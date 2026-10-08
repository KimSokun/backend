# aaPanel Multi-Subdomain Deployment Guide (2 Separate Paths)

This guide organizes your VPS into **2 clean directories**:
1. **Frontend Path**: `/www/wwwroot/frontend/` ➔ Hosts `www.yourdomain.com` and `yourdomain.com`
2. **Backend Path**: `/www/wwwroot/backend/` ➔ Hosts `api.yourdomain.com` (Port 8000) and `admin.yourdomain.com` (Port 5000)

---

## 📁 1. Upload & Unzip into 2 Paths on aaPanel

In aaPanel ➔ **Files**:
1. Go to `/www/wwwroot/` ➔ Create folder **`frontend`** ➔ Upload **`frontend.zip`** ➔ Click **Unzip**.
2. Go to `/www/wwwroot/` ➔ Create folder **`backend`** ➔ Upload **`backend.zip`** ➔ Click **Unzip**.

Directory structure on server:
```text
/www/wwwroot/
├── frontend/                     <── from frontend.zip
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
└── backend/                      <── from backend.zip
    ├── backend-python/
    └── backend-node/
```

---

## 🐍 2. Start Python FastAPI Backend (api.yourdomain.com)

In aaPanel Terminal:
```bash
cd /www/wwwroot/backend/backend-python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
In **Supervisor Manager** ➔ **Add Daemon**:
- **Name**: `alltools-fastapi`
- **Directory**: `/www/wwwroot/backend/backend-python`
- **Command**: `/www/wwwroot/backend/backend-python/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4`
- **User**: `www`

---

## 🟢 3. Start Node.js Admin Backend (admin.yourdomain.com)

In aaPanel Terminal:
```bash
cd /www/wwwroot/backend/backend-node
npm install --production
```
In **PM2 Project Manager** ➔ **Add Project**:
- **Path**: `/www/wwwroot/backend/backend-node`
- **File**: `src/server.js`
- **Name**: `alltools-admin-node`
- **User**: `www`

---

## ⚛️ 4. Build React Frontend (www.yourdomain.com)

In aaPanel Terminal:
```bash
cd /www/wwwroot/frontend
npm install
npm run build
```
*(Build files will be generated into `/www/wwwroot/frontend/dist`)*

---

## 🌐 5. Configure 3 Websites in aaPanel

### Site 1: Frontend (`www.yourdomain.com` & `yourdomain.com`)
- **Document Root**: `/www/wwwroot/frontend/dist`
- **PHP Version**: `Pure Static`
- **URL Rewrite tab**:
  ```nginx
  location / {
      try_files $uri $uri/ /index.html;
  }
  ```
- **SSL tab**: Apply for Let's Encrypt SSL.

### Site 2: API Backend (`api.yourdomain.com`)
- **Document Root**: `/www/wwwroot/backend/backend-python`
- **Reverse Proxy tab**: Add target `http://127.0.0.1:8000`
- **Config tab (nginx)**:
  ```nginx
  client_max_body_size 500M;
  proxy_read_timeout 300s;
  proxy_connect_timeout 300s;
  ```
- **SSL tab**: Apply for Let's Encrypt SSL.

### Site 3: Admin Portal (`admin.yourdomain.com`)
- **Document Root**: `/www/wwwroot/frontend/dist`
- **Config tab (nginx)**:
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
- **SSL tab**: Apply for Let's Encrypt SSL.
