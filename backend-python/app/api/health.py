import os
import shutil
import time
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["Health & System"])

@router.get("/health")
async def health_check():
    temp_files_count = len(list(settings.TEMP_DIR.glob("*"))) if settings.TEMP_DIR.exists() else 0
    results_files_count = len(list(settings.RESULTS_DIR.glob("*"))) if settings.RESULTS_DIR.exists() else 0
    
    total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
    
    return {
        "status": "healthy",
        "service": "AllTools Python FastAPI Engine",
        "version": "1.0.0",
        "timestamp": int(time.time()),
        "storage": {
            "tempFiles": temp_files_count,
            "resultFiles": results_files_count,
            "diskFreeGb": round(free / (1024**3), 2)
        }
    }
