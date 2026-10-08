# Complete Cloudflare (Proxy Enabled ☁️) + aaPanel Deployment Guide

This guide details the exact production setup when using **Cloudflare with Proxy Enabled (Orange Cloud ☁️🧡)** and **aaPanel**.

---

## 🌐 1. Cloudflare DNS Settings (Proxy Enabled ☁️)

In your **Cloudflare Dashboard** -> **DNS** -> **Records**, add:

| Type | Name | Content (Target) | Proxy status | TTL |
| :--- | :--- | :--- | :--- | :--- |
| **A** | `@` | `YOUR_SERVER_IP` | ☁️ **Proxied** (Orange) | Auto |
| **A** | `www` | `YOUR_SERVER_IP` | ☁️ **Proxied** (Orange) | Auto |
| **A** | `api` | `YOUR_SERVER_IP` | ☁️ **Proxied** (Orange) | Auto |
| **A** | `admin` | `YOUR_SERVER_IP` | ☁️ **Proxied** (Orange) | Auto |

---

## 🔒 2. Critical Cloudflare SSL/TLS Settings

1. In Cloudflare Dashboard -> **SSL/TLS** -> **Overview**:
   - Set encryption mode to **Full** or **Full (strict)**.
   - ⚠️ **DO NOT USE "Flexible"** (Flexible causes an infinite redirect loop with Nginx).
2. In **SSL/TLS** -> **Edge Certificates**:
   - Enable **Always Use HTTPS** (On).
   - Enable **Automatic HTTPS Rewrites** (On).
   - Minimum TLS Version: **TLS 1.2**.
3. In **Network**:
   - Enable **HTTP/2** & **HTTP/3 (QUIC)** for maximum conversion download speeds.
   - Enable **WebSockets** (On).

---

## 🛡️ 3. Restore Real Visitor IP in aaPanel Nginx

Because Cloudflare acts as a reverse proxy, Nginx would see Cloudflare's IP instead of the visitor's real IP unless configured. 

In **aaPanel** -> **App Store** -> **Nginx (Settings)** -> **Configuration (nginx.conf)**:
Add this inside the `http { ... }` block:

```nginx
# Restore Real Visitor IP from Cloudflare
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 104.16.0.0/13;
set_real_ip_from 104.24.0.0/14;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 131.0.72.0/22;
set_real_ip_from 2400:cb00::/32;
set_real_ip_from 2606:4700::/32;
set_real_ip_from 2803:f800::/32;
set_real_ip_from 2405:b500::/32;
set_real_ip_from 2405:8100::/32;
set_real_ip_from 2a06:98c0::/29;
set_real_ip_from 2c0f:f248::/32;

real_ip_header CF-Connecting-IP;
```
Click **Save** and **Reload Nginx**. Now our backend rate limiter and anti-DDoS blocker automatically see the real visitor IP!

---

## 🚀 4. Setting up the 3 Sites in aaPanel

### Site 1: Frontend (`www.yourdomain.com` & `yourdomain.com`)
1. In aaPanel -> **Website** -> **Add Site**:
   - **Domain**: `yourdomain.com` and `www.yourdomain.com`
   - **Document Root**: `/www/wwwroot/alltools/frontend/dist`
   - **PHP Version**: `Pure Static`
2. In Website settings -> **URL rewrite**:
   ```nginx
   location / {
       try_files $uri $uri/ /index.html;
   }
   ```
3. In Website settings -> **SSL** tab: Apply for a free **Let's Encrypt** SSL certificate (or paste a Cloudflare Origin Certificate).

---

### Site 2: API Engine (`api.yourdomain.com`)
1. In aaPanel -> **Website** -> **Add Site**:
   - **Domain**: `api.yourdomain.com`
   - **Document Root**: `/www/wwwroot/alltools/backend-python`
   - **PHP Version**: `Pure Static`
2. In Website settings -> **Reverse Proxy** tab -> **Add reverse proxy**:
   - **Name**: `fastapi`
   - **Target URL**: `http://127.0.0.1:8000`
   - **Sent Domain**: `$host`
3. In Website settings -> **Config** tab, add inside `server { ... }`:
   ```nginx
   client_max_body_size 500M;
   proxy_read_timeout 300s;
   proxy_connect_timeout 300s;
   proxy_send_timeout 300s;
   ```
4. In **SSL** tab: Apply for SSL.

---

### Site 3: Admin Portal (`admin.yourdomain.com`)
1. In aaPanel -> **Website** -> **Add Site**:
   - **Domain**: `admin.yourdomain.com`
   - **Document Root**: `/www/wwwroot/alltools/frontend/dist`
   - **PHP Version**: `Pure Static`
2. In Website settings -> **Config** tab, paste inside `server { ... }`:
   ```nginx
   location /admin-api/ {
       proxy_pass http://127.0.0.1:5000/admin-api/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header CF-Connecting-IP $http_cf_connecting_ip;
       proxy_set_header X-Forwarded-Proto $scheme;
   }

   location / {
       try_files $uri $uri/ /index.html;
   }
   ```
3. In **SSL** tab: Apply for SSL.

---

## ⚡ 5. Cloudflare Upload Optimization (Large Media Files)

Cloudflare Free plan buffers uploads up to **100MB**. Since our platform supports up to **200MB–500MB** video/image files:

1. In Cloudflare Dashboard -> **Rules** -> **Configuration Rules** -> **Create Rule**:
   - **Rule name**: `Allow High Upload Limits`
   - **Matching Criteria**: `Hostname equals api.yourdomain.com`
   - **Settings**: Set **Maximum Request Body Size** to **100MB** (or custom).
2. For very large files (>100MB on Cloudflare free tier), you can simply toggle the proxy on `api.yourdomain.com` to **DNS only (Grey Cloud ☁️)** if users upload massive 500MB raw 4K videos, while keeping `www` and `admin` on full Orange Cloud protection!

---

## 🔐 6. Admin Portal Login via Cloudflare

Open: **`https://admin.yourdomain.com/kadmin`**
- **Username**: `kamin`
- **Password**: `kamin@2026`
- **2FA Key**: `kamin@2026kk`
- **Captcha**: Interactive 5-character verification challenge.
