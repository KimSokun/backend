#!/bin/bash
# ==============================================================================
# AllTools Platform - 1-Click Automated Setup & 2C2G VPS Resource Optimizer
# ==============================================================================

set -e

echo ""
echo "=================================================================="
echo "🚀 Starting AllTools Auto-Setup (Optimized for 2C2G VPS)..."
echo "=================================================================="
echo ""

# 1. Free Virtual Memory (SWAP) Setup for 2GB RAM VPS
echo "🧠 [1/7] Optimizing Memory & Creating 2GB SWAP (Virtual RAM)..."
if [ $(free -m | grep -i swap | awk '{print $2}') -lt 1000 ]; then
    echo "Creating 2GB Swapfile to ensure VPS NEVER runs out of memory..."
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    (grep -v "/swapfile" /etc/fstab; echo "/swapfile none swap sw 0 0") > /tmp/fstab && mv /tmp/fstab /etc/fstab
    echo "✅ 2GB SWAP created! Your VPS now has 2GB RAM + 2GB Virtual Memory ($0 Cost)!"
else
    echo "✅ SWAP Memory is already active."
fi

# 2. Detect OS & Install FFmpeg + System Tools for Ubuntu 22.04 / Debian
echo ""
echo "📦 [2/7] Installing system dependencies (FFmpeg, Python, Redis, Cron)..."
if [ -f /etc/debian_version ]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y ffmpeg python3-venv python3-pip python3-dev libgl1 libglib2.0-0 libsm6 libxext6 redis-server curl cron git libreoffice-writer-nogui fonts-khmeros fonts-khmeros-core fonts-dejavu-core
    systemctl enable redis-server 2>/dev/null || true
    systemctl start redis-server 2>/dev/null || true
elif [ -f /etc/redhat-release ]; then
    yum install -y epel-release || true
    yum install -y ffmpeg python3-pip redis curl crontabs git || true
    systemctl enable redis 2>/dev/null || true
    systemctl start redis 2>/dev/null || true
fi

# 3. Setup Python FastAPI Backend
echo ""
echo "🐍 [3/7] Setting up Python FastAPI Engine (Port 8000)..."
cd /www/wwwroot/backend/backend-python

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Pre-warm rembg AI model to ~/.u2net so first user request is instant
python3 -c "import rembg; print('Pre-warming AI model...'); rembg.new_session('u2net')" 2>/dev/null || true

# Ensure storage directories
mkdir -p storage/temp storage/results
chmod -R 775 storage

# 4. Setup Node.js Admin Backend
echo ""
echo "🟢 [4/7] Setting up Node.js Admin Backend (Port 5000)..."
cd /www/wwwroot/backend/backend-node
npm install --production

# 5. Setup and Build React Frontend
echo ""
echo "⚛️ [5/7] Installing dependencies and building React Frontend..."
cd /www/wwwroot/frontend
chattr -i /www/wwwroot/frontend/dist/.user.ini 2>/dev/null || true
rm -rf /www/wwwroot/frontend/dist/.user.ini 2>/dev/null || true
chattr -i /www/wwwroot/frontend/.user.ini 2>/dev/null || true
npm install
npm run build

# 6. Configure 24/7 Automated OS Storage Cleanup Cron
echo ""
echo "🛡️ [6/7] Configuring 24/7 Automatic Disk Space Protection Cron..."
CRON_JOB="*/15 * * * * find /www/wwwroot/backend/backend-python/storage/temp /www/wwwroot/backend/backend-python/storage/results -type f -mmin +20 -delete 2>/dev/null"
(crontab -l 2>/dev/null | grep -v "alltools" ; echo "$CRON_JOB # alltools-auto-cleanup") | crontab -

# 7. Start Services with PM2 (2 Workers tuned for 2C2G)
echo ""
echo "⚡ [7/7] Auto-starting backend services tuned for 2 Cores..."

if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
fi

pm2 delete alltools-fastapi 2>/dev/null || true
pm2 delete alltools-admin 2>/dev/null || true

# Start Python FastAPI (2 workers perfectly matched to 2 CPU cores)
cd /www/wwwroot/backend/backend-python
pm2 start "/www/wwwroot/backend/backend-python/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2" --name "alltools-fastapi"

# Start Node.js Admin on Port 5000
cd /www/wwwroot/backend/backend-node
pm2 start src/server.js --name "alltools-admin"

# Save PM2 state
pm2 save

echo ""
echo "=================================================================="
echo "🎉 ALL SERVICES SUCCESSFULLY RUNNING ON 2C2G VPS!"
echo "=================================================================="
pm2 status
free -h

echo ""
echo "📡 Endpoints Ready:"
echo " - Python FastAPI: http://127.0.0.1:8000/api/health"
echo " - Node Admin API: http://127.0.0.1:5000/admin-api/health"
echo " - Frontend Dist:  /www/wwwroot/frontend/dist"
echo "=================================================================="
