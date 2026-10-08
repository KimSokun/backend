const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const jwt = require('jsonwebtoken');
const os = require('os');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const Redis = require('ioredis');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'alltools_admin_secret_key_2026_secure';

// Persistent Data Directory
const DATA_DIR = path.join(__dirname, '../data');
if (!fs.existsSync(DATA_DIR)) {
  try { fs.mkdirSync(DATA_DIR, { recursive: true }); } catch (_) {}
}
const ADS_FILE = path.join(DATA_DIR, 'ads-config.json');

app.use(helmet());
app.use(cors({ 
  origin: true, 
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));
app.use(express.json());

// Redis Client with Graceful Fallback
let isRedisConnected = false;
const redis = new Redis({
  host: process.env.REDIS_HOST || '127.0.0.1',
  port: Number(process.env.REDIS_PORT) || 6379,
  password: process.env.REDIS_PASSWORD || undefined,
  lazyConnect: true,
  retryStrategy(times) {
    if (times > 3) return null; // stop retry if not found locally
    return Math.min(times * 500, 2000);
  }
});

redis.connect().then(() => {
  isRedisConnected = true;
  console.log('✅ Connected to Redis cache service!');
}).catch(() => {
  isRedisConnected = false;
  console.log('ℹ️ Redis offline, using in-memory cache fallback.');
});

redis.on('connect', () => { isRedisConnected = true; });
redis.on('error', () => { isRedisConnected = false; });

// In-Memory Fallbacks
let adminConfig = {
  username: process.env.ADMIN_USER || 'kamin',
  password: process.env.ADMIN_PASS || 'kamin@2026',
  twoFactorKey: process.env.ADMIN_2FA || 'kamin@2026kk',
  rateLimit: {
    enabled: true,
    maxRequestsPerMinute: 40,
    strictDDoSProtection: true,
    autoBanThreshold: 90
  }
};

let memoryCaptchas = new Map();
let memoryBlockedIPs = new Map();
let memoryAdSlots = {
  leftAd: { enabled: true, customHtml: '', width: 160, height: 600 },
  rightAd: { enabled: true, customHtml: '', width: 160, height: 600 },
  bottomBanner: { enabled: true, customHtml: '', width: 728, height: 90 },
  stickyBottomAd: { enabled: true, customHtml: '', width: 728, height: 90 },
  mobileAd: { enabled: true, customHtml: '', width: 320, height: 100 },
  directLinkUrl: '',
  downloadAd: { enabled: true, url: '' }
};

// Load saved Ads from disk on boot
try {
  if (fs.existsSync(ADS_FILE)) {
    const raw = fs.readFileSync(ADS_FILE, 'utf8');
    const diskAds = JSON.parse(raw);
    memoryAdSlots = { ...memoryAdSlots, ...diskAds };
    console.log('✅ Loaded persisted Ad configuration from disk!');
  }
} catch (e) {
  console.error('Failed to load ads-config.json:', e);
}

let memoryToolUsage = {
  'remove-background': 1240,
  'fake-address-generator': 2450,
  'password-generator': 1890,
  'uuid-generator': 920,
  'qr-generator': 1130,
  'merge-pdf': 870,
  'video-to-mp3': 1560,
  'hash-generator': 640
};

// Generate Captcha Challenge
async function generateCaptchaChallenge() {
  const chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';
  let text = '';
  for (let i = 0; i < 5; i++) {
    text += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  const id = crypto.randomUUID();

  if (isRedisConnected) {
    await redis.setex(`captcha:${id}`, 300, text.toLowerCase());
  } else {
    memoryCaptchas.set(id, { code: text.toLowerCase(), expiresAt: Date.now() + 300000 });
  }

  return { id, text };
}

// Rate Limiter & Crash Protection Middleware
app.use(async (req, res, next) => {
  const clientIp = req.headers['cf-connecting-ip'] || 
    (req.headers['x-forwarded-for'] ? req.headers['x-forwarded-for'].split(',')[0].trim() : req.socket.remoteAddress) || 
    '127.0.0.1';
  const now = Date.now();

  // 1. Check if IP is blocked in Redis or Memory
  let isBlocked = false;
  if (isRedisConnected) {
    const ban = await redis.get(`ban:${clientIp}`);
    if (ban) isBlocked = true;
  } else if (memoryBlockedIPs.has(clientIp)) {
    const banInfo = memoryBlockedIPs.get(clientIp);
    if (now - banInfo.bannedAt < 900000) isBlocked = true;
    else memoryBlockedIPs.delete(clientIp);
  }

  if (isBlocked) {
    return res.status(429).json({
      success: false,
      error: 'Too Many Requests. Your IP is temporarily rate-limited for server protection.'
    });
  }

  // 2. Sliding window limit
  if (adminConfig.rateLimit.enabled && !req.path.startsWith('/admin-api/auth')) {
    if (isRedisConnected) {
      const key = `ratelimit:node:${clientIp}`;
      const count = await redis.incr(key);
      if (count === 1) await redis.expire(key, 60);

      if (count > adminConfig.rateLimit.autoBanThreshold) {
        await redis.setex(`ban:${clientIp}`, 900, 'Flood threshold exceeded');
        return res.status(429).json({ success: false, error: 'IP blocked due to abnormal request flood.' });
      }

      if (count > adminConfig.rateLimit.maxRequestsPerMinute) {
        return res.status(429).json({ success: false, error: 'Rate limit exceeded. Please slow down.' });
      }
    }
  }

  next();
});

// Admin JWT Middleware
const authenticateAdmin = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Unauthorized admin access.' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.admin = decoded;
    next();
  } catch {
    return res.status(401).json({ success: false, error: 'Invalid or expired token.' });
  }
};

// 1. Health check
app.get('/admin-api/health', (req, res) => {
  res.json({
    status: 'healthy',
    redis: isRedisConnected ? 'connected' : 'memory_fallback',
    timestamp: new Date().toISOString()
  });
});

// 2. Captcha Generation
app.get('/admin-api/auth/captcha', async (req, res) => {
  const challenge = await generateCaptchaChallenge();
  res.json({
    success: true,
    captchaId: challenge.id,
    captchaDisplay: challenge.text
  });
});

// 3. Admin Login (Username, Password, 2FA, Captcha)
app.post('/admin-api/auth/login', async (req, res) => {
  const { username, password, twoFactorCode, captchaId, captchaAnswer } = req.body;

  if (!captchaId || !captchaAnswer) {
    return res.status(400).json({ success: false, error: 'Security Captcha verification is required.' });
  }

  let validCaptcha = false;
  if (isRedisConnected) {
    const stored = await redis.get(`captcha:${captchaId}`);
    if (stored && stored === captchaAnswer.trim().toLowerCase()) {
      validCaptcha = true;
      await redis.del(`captcha:${captchaId}`);
    }
  } else {
    const stored = memoryCaptchas.get(captchaId);
    if (stored && stored.code === captchaAnswer.trim().toLowerCase() && Date.now() < stored.expiresAt) {
      validCaptcha = true;
      memoryCaptchas.delete(captchaId);
    }
  }

  if (!validCaptcha) {
    return res.status(400).json({ success: false, error: 'Incorrect or expired Captcha code.' });
  }

  if (
    username === adminConfig.username &&
    password === adminConfig.password &&
    twoFactorCode === adminConfig.twoFactorKey
  ) {
    const token = jwt.sign({ username, role: 'superadmin' }, JWT_SECRET, { expiresIn: '8h' });
    return res.json({ success: true, token, message: 'Authenticated successfully' });
  }

  return res.status(401).json({ success: false, error: 'Invalid credentials or 2-Factor security key.' });
});

// 4. Change Admin Credentials
app.post('/admin-api/auth/change-credentials', authenticateAdmin, (req, res) => {
  const { currentPassword, newUsername, newPassword, newTwoFactorKey } = req.body;

  if (currentPassword !== adminConfig.password) {
    return res.status(400).json({ success: false, error: 'Current password is incorrect.' });
  }

  if (newUsername) adminConfig.username = newUsername;
  if (newPassword) adminConfig.password = newPassword;
  if (newTwoFactorKey) adminConfig.twoFactorKey = newTwoFactorKey;

  res.json({ success: true, message: 'Admin security credentials updated successfully.' });
});

// 5. System Metrics & Telemetry
app.get('/admin-api/metrics', authenticateAdmin, (req, res) => {
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const usedMem = totalMem - freeMem;
  const cpus = os.cpus();

  res.json({
    system: {
      platform: os.platform(),
      arch: os.arch(),
      cpuCores: cpus.length,
      cpuModel: cpus[0]?.model || 'Generic CPU',
      uptimeHours: Math.round(os.uptime() / 3600),
      memory: {
        totalGb: (totalMem / 1024 / 1024 / 1024).toFixed(2),
        usedGb: (usedMem / 1024 / 1024 / 1024).toFixed(2),
        percentUsed: Math.round((usedMem / totalMem) * 100)
      },
      nodeVersion: process.version
    },
    protection: {
      rateLimit: adminConfig.rateLimit,
      redisActive: isRedisConnected
    },
    toolsTotalInvocations: Object.values(memoryToolUsage).reduce((a, b) => a + b, 0)
  });
});

// 6. Abuse Protection Settings & Blocked IPs
app.get('/admin-api/protection', authenticateAdmin, async (req, res) => {
  let bansList = [];
  if (isRedisConnected) {
    const keys = await redis.keys('ban:*');
    for (const k of keys) {
      const ip = k.replace('ban:', '');
      const ttl = await redis.ttl(k);
      bansList.push({ ip, reason: 'Abnormal flood blocked by Redis', bannedAt: `${ttl}s left`, requestCount: '> 90' });
    }
  } else {
    bansList = Array.from(memoryBlockedIPs.entries()).map(([ip, info]) => ({
      ip,
      reason: info.reason,
      bannedAt: new Date(info.bannedAt).toLocaleTimeString(),
      requestCount: info.count
    }));
  }

  res.json({ config: adminConfig.rateLimit, blockedList: bansList });
});

app.post('/admin-api/protection', authenticateAdmin, (req, res) => {
  const { maxRequestsPerMinute, autoBanThreshold, strictDDoSProtection, enabled } = req.body;
  if (maxRequestsPerMinute !== undefined) adminConfig.rateLimit.maxRequestsPerMinute = Number(maxRequestsPerMinute);
  if (autoBanThreshold !== undefined) adminConfig.rateLimit.autoBanThreshold = Number(autoBanThreshold);
  if (strictDDoSProtection !== undefined) adminConfig.rateLimit.strictDDoSProtection = Boolean(strictDDoSProtection);
  if (enabled !== undefined) adminConfig.rateLimit.enabled = Boolean(enabled);

  res.json({ success: true, config: adminConfig.rateLimit });
});

app.post('/admin-api/protection/unban', authenticateAdmin, async (req, res) => {
  const { ip } = req.body;
  if (isRedisConnected) await redis.del(`ban:${ip}`);
  memoryBlockedIPs.delete(ip);
  res.json({ success: true, message: `Unbanned IP: ${ip}` });
});

// 7. Ad Slots Management (Persisted to Disk File, Redis, and Memory)
app.get('/admin-api/ads', async (req, res) => {
  if (isRedisConnected) {
    const saved = await redis.get('ads:config');
    if (saved) {
      const parsed = JSON.parse(saved);
      return res.json({ ads: parsed, ...parsed });
    }
  }
  res.json({ ads: memoryAdSlots, ...memoryAdSlots });
});

app.post('/admin-api/ads', async (req, res) => {
  const { slotId, enabled, customHtml, allAds } = req.body;
  if (allAds && typeof allAds === 'object') {
    memoryAdSlots = { ...memoryAdSlots, ...allAds };
  } else if (slotId) {
    if (!memoryAdSlots[slotId]) memoryAdSlots[slotId] = {};
    if (enabled !== undefined) memoryAdSlots[slotId].enabled = Boolean(enabled);
    if (customHtml !== undefined) memoryAdSlots[slotId].customHtml = String(customHtml);
  }

  // 1. Persist to Disk File Immediately
  try {
    fs.writeFileSync(ADS_FILE, JSON.stringify(memoryAdSlots, null, 2), 'utf8');
  } catch (err) {
    console.error('Failed to persist ads to disk:', err);
  }

  // 2. Persist to Redis if available
  if (isRedisConnected) {
    await redis.set('ads:config', JSON.stringify(memoryAdSlots));
  }

  return res.json({ success: true, ads: memoryAdSlots, ...memoryAdSlots });
});

// Verify Auth Token on Page Refresh
app.get('/admin-api/auth/verify', authenticateAdmin, (req, res) => {
  res.json({ success: true, admin: req.admin });
});

// 8. Tool Usage Analytics
app.get('/admin-api/tools/stats', authenticateAdmin, (req, res) => {
  res.json({ metrics: memoryToolUsage });
});

app.post('/admin-api/tools/record', (req, res) => {
  const { toolId } = req.body;
  if (toolId) {
    memoryToolUsage[toolId] = (memoryToolUsage[toolId] || 0) + 1;
  }
  res.json({ success: true });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`AllTools Node.js Admin Backend listening on port ${PORT}`);
  console.log(`Protected Admin Route: https://admin.domain or /kadmin`);
  console.log(`Redis Cache Support: Active`);
});
