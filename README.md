# AllTools - All-in-One Online Tools Platform

> A modern, lightning-fast, anonymous, 100% free online tools website with **zero registration required**, an optimized **three-column ad layout**, **Python FastAPI** tool processing engine, and **Node.js** Admin & Telemetry Dashboard.

---

## 🌟 Key Highlights

- **Anonymous & Zero Friction**: No login, no signup, no account creation, no password needed.
- **Three-Column Desktop Layout**:
  - **Left Ad**: `160 × 600` Sticky Sidebar container.
  - **Middle Workspace**: Left Category Sidebar Menu + Main Tool Canvas & Options + Results + Actions.
  - **Right Ad**: `160 × 600` Sticky Sidebar container.
  - **Footer Banner**: `728 × 90` Responsive Bottom Banner container.
- **Ephemeral & Secure**:
  - Uploaded temporary files automatically deleted after 30 minutes via background worker.
  - IP-based rate limiting.
  - Parameterized FFmpeg (strictly no `shell=True` or `os.system`).
  - No database required in V1 (stateless and horizontally scalable).
- **Dual Backend Architecture**:
  - **Python FastAPI (Port 8000)**: Image processing, PDF tools, Video conversion, Cryptographic password/UUID/QR generators, Mock data with Faker, Text & Developer utilities.
  - **Node.js Express (Port 5000)**: Admin dashboard, system telemetry (CPU, RAM, storage), and dynamic Ad slot management.

---

## 📁 Project Structure

```text
fullstack/
├── frontend/                     # React + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/layout/   # Header, Footer, MainLayout, LeftAd, RightAd, BottomBanner
│   │   ├── components/tools/    # ToolHeader, FileUploader, ComparisonSlider, ResultPanel, ToolMenu
│   │   ├── config/tools.ts      # Central Plugin-like Tool Registry
│   │   ├── pages/               # Tool pages (Image, PDF, Video, Generators, Test Data, Text, Dev, Admin)
│   │   └── services/api.ts      # Axios client configuration
│   └── package.json
│
├── backend-python/               # Python FastAPI Tool Processing Engine
│   ├── app/
│   │   ├── api/                 # image.py, pdf.py, video.py, generators.py, test_data.py, text.py, developer.py, health.py
│   │   ├── services/            # Pillow/OpenCV/Rembg, PyMuPDF, FFmpeg, secrets, Faker, Text/Dev utilities
│   │   ├── core/                # config.py, security.py, rate_limiter.py
│   │   ├── utils/               # files.py, cleanup.py, ffmpeg_runner.py
│   │   └── main.py              # FastAPI entrypoint with Lifespan auto-cleanup
│   ├── storage/                 # temp/ and results/ ephemeral directories
│   ├── tests/                   # Pytest automated test suite
│   └── requirements.txt
│
├── backend-node/                 # Node.js Express Admin & Telemetry Engine
│   ├── src/
│   │   └── server.js            # Express server (Port 5000), system metrics & ad slot management
│   └── package.json
│
├── nginx/
│   └── nginx.conf               # Production reverse proxy (Gzip, 500M upload, SSL/Proxy)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start Guide (Local Development)

### 1. Start Python FastAPI Backend
```bash
cd backend-python
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API is live at `http://localhost:8000`
- Interactive OpenAPI Docs at `http://localhost:8000/docs`

### 2. Start Node.js Admin Backend
```bash
cd backend-node
npm install
npm run dev
```
- Admin API is live at `http://localhost:5000`

### 3. Start React Frontend
```bash
cd frontend
npm install
npm run dev
```
- Web Application is live at `http://localhost:5173`

---

## 🐳 Docker Deployment

To launch all services (Frontend, FastAPI Backend, Node Admin, Nginx Gateway) in one command:

```bash
docker-compose up --build -d
```
Access the application at `http://localhost`.

---

## 🧪 Running Automated Tests

```bash
cd backend-python
.\.venv\Scripts\pytest
```

---

## 🔐 Admin Console
Navigate to `http://localhost:5173/admin`
- Default Username: `admin`
- Default Password: `admin123`
- Features: Live CPU/RAM/Disk metrics, Active temporary files count, Tool usage statistics, and dynamic Ad slot toggles/HTML injection.
