import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.utils.cleanup import cleanup_worker_loop
from app.api.image import router as image_router
from app.api.pdf import router as pdf_router
from app.api.video import router as video_router
from app.api.generators import router as generator_router
from app.api.test_data import router as test_data_router
from app.api.text import router as text_router
from app.api.developer import router as dev_router
from app.api.health import router as health_router
from app.api.doc import router as doc_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("alltools_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AllTools FastAPI Engine...")
    cleanup_task = asyncio.create_task(cleanup_worker_loop())
    yield
    logger.info("Shutting down AllTools FastAPI Engine...")
    cleanup_task.cancel()

# Initialize FastAPI with Swagger/OpenAPI docs COMPLETELY HIDDEN & DISABLED for security
app = FastAPI(
    title="AllTools Backend API",
    description="High-performance, anonymous, privacy-focused online utilities engine.",
    version="1.0.0",
    docs_url=None,       # Hide Swagger UI (/docs)
    redoc_url=None,      # Hide Redoc UI (/redoc)
    openapi_url=None,    # Hide OpenAPI JSON schema (/openapi.json)
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uniform error handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": detail}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": "HTTP_ERROR", "message": str(detail)}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters.",
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An internal server error occurred while processing your request."
            }
        }
    )

# Include all modular API routers
app.include_router(image_router)
app.include_router(pdf_router)
app.include_router(video_router)
app.include_router(generator_router)
app.include_router(test_data_router)
app.include_router(text_router)
app.include_router(dev_router)
app.include_router(health_router)
app.include_router(doc_router)

# Public Ads Configuration Endpoint for Frontend (Serves all new visitors & new tabs)
@app.get("/api/ads")
async def get_public_ads():
    import json
    from pathlib import Path
    
    search_paths = [
        Path("/www/wwwroot/backend/backend-node/data/ads-config.json"),
        Path(__file__).resolve().parent.parent.parent / "backend-node" / "data" / "ads-config.json",
        Path.cwd() / "data" / "ads-config.json"
    ]
    
    for p in search_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    ads_data = json.load(f)
                    return JSONResponse(content={"success": True, "ads": ads_data, **ads_data})
            except Exception:
                pass
                
    fallback_ads = {
        "leftAd": {"enabled": True, "customHtml": "", "width": 160, "height": 600},
        "rightAd": {"enabled": True, "customHtml": "", "width": 160, "height": 600},
        "bottomBanner": {"enabled": True, "customHtml": "", "width": 728, "height": 90},
        "stickyBottomAd": {"enabled": True, "customHtml": "", "width": 728, "height": 90},
        "mobileAd": {"enabled": True, "customHtml": "", "width": 320, "height": 100},
        "directLinkUrl": "",
        "downloadAd": {"enabled": True, "url": ""}
    }
    return JSONResponse(content={"success": True, "ads": fallback_ads, **fallback_ads})

@app.post("/api/ads")
async def save_public_ads(request: Request):
    import json
    from pathlib import Path
    try:
        body = await request.json()
        slot_id = body.get("slotId")
        enabled = body.get("enabled", True)
        custom_html = body.get("customHtml", "")
        all_ads = body.get("allAds")
        
        target_file = Path("/www/wwwroot/backend/backend-node/data/ads-config.json")
        if not target_file.parent.exists():
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                target_file = Path.cwd() / "data" / "ads-config.json"
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
        current_ads = {
            "leftAd": {"enabled": True, "customHtml": "", "width": 160, "height": 600},
            "rightAd": {"enabled": True, "customHtml": "", "width": 160, "height": 600},
            "bottomBanner": {"enabled": True, "customHtml": "", "width": 728, "height": 90},
            "stickyBottomAd": {"enabled": True, "customHtml": "", "width": 728, "height": 90},
            "mobileAd": {"enabled": True, "customHtml": "", "width": 320, "height": 100},
            "directLinkUrl": "",
            "downloadAd": {"enabled": True, "url": ""}
        }
        if target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    disk_loaded = json.load(f)
                    if isinstance(disk_loaded, dict):
                        current_ads.update(disk_loaded)
            except Exception:
                pass
                
        if all_ads and isinstance(all_ads, dict):
            current_ads.update(all_ads)
        elif slot_id:
            if slot_id not in current_ads:
                current_ads[slot_id] = {}
            current_ads[slot_id]["enabled"] = bool(enabled)
            current_ads[slot_id]["customHtml"] = str(custom_html)
            
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(current_ads, f, indent=2)
                
        return JSONResponse(content={"success": True, "ads": current_ads, **current_ads})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

# Modern, Secure "UI RUNNING ONLY" Status Page (Hides all internal API routes from public)
STATUS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AllTools API Engine - Running</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body {
            background-color: #0B0F19;
            color: #F3F4F6;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            background: #111827;
            border: 1px solid #1F2937;
            border-radius: 24px;
            padding: 40px;
            max-width: 460px;
            width: 100%;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .badge-pulse {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.1);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin-bottom: 24px;
            text-transform: uppercase;
        }
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10B981;
            box-shadow: 0 0 10px #10B981;
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: .4; transform: scale(1.3); }
        }
        h1 {
            font-size: 22px;
            font-weight: 800;
            margin-bottom: 8px;
            color: #FFFFFF;
        }
        p {
            font-size: 13px;
            color: #9CA3AF;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 24px;
            text-align: left;
        }
        .item {
            background: #1F2937;
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid #374151;
        }
        .item-label {
            font-size: 11px;
            color: #9CA3AF;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .item-val {
            font-size: 13px;
            color: #F9FAFB;
            font-weight: 700;
        }
        .footer-note {
            font-size: 11px;
            color: #6B7280;
            border-top: 1px solid #1F2937;
            padding-top: 16px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge-pulse">
            <span class="dot"></span>
            <span>All Systems Operational</span>
        </div>
        <h1>AllTools API Engine</h1>
        <p>High-performance backend processing engine is running securely in production mode.</p>
        
        <div class="grid">
            <div class="item">
                <div class="item-label">Status</div>
                <div class="item-val" style="color: #10B981;">Online (200 OK)</div>
            </div>
            <div class="item">
                <div class="item-label">Protection</div>
                <div class="item-val" style="color: #3B82F6;">Shield Active</div>
            </div>
            <div class="item">
                <div class="item-label">Rate Limiting</div>
                <div class="item-val">Enabled (Redis)</div>
            </div>
            <div class="item">
                <div class="item-label">API Endpoints</div>
                <div class="item-val" style="color: #F59E0B;">Protected</div>
            </div>
        </div>

        <div class="footer-note">
            AllTools Platform &bull; Anonymous & Encrypted API Gateway
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=STATUS_HTML)

@app.get("/docs", response_class=HTMLResponse)
async def docs_hidden():
    return HTMLResponse(content=STATUS_HTML)

@app.get("/redoc", response_class=HTMLResponse)
async def redoc_hidden():
    return HTMLResponse(content=STATUS_HTML)
