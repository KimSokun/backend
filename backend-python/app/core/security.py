import re
import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException, status, Request
from app.core.config import settings

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}

# Hack & Exploit Probe Signatures
HACK_PROBE_PATTERNS = [
    r"\.\./",              # Path traversal
    r"\.env",              # Environment probes
    r"wp-admin",           # WordPress brute force
    r"xmlrpc\.php",        # WordPress XML-RPC attack
    r"\.git",              # Git leak probe
    r"phpmyadmin",         # Database panel scanner
    r"cgi-bin",            # CGI exploit
    r"<script",            # XSS injection
    r"union.*select",      # SQL injection
    r"eval\(",             # Code execution
]

def check_malicious_probe(request: Request, filename: str = ""):
    """Detects and instantly rejects hacker scanning probes"""
    path_to_check = f"{request.url.path} {filename}"
    for pattern in HACK_PROBE_PATTERNS:
        if re.search(pattern, path_to_check, re.IGNORECASE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PROBE_REJECTED", "message": "Access denied by Server Security Guard."}
            )

def sanitize_filename(filename: str) -> str:
    """Strips dangerous characters from uploaded filenames"""
    name = Path(filename).name
    # Keep only safe alphanumeric, dashes, dots, and underscores
    clean = re.sub(r"[^\w\s\.-]", "", name)
    clean = re.sub(r"\s+", "_", clean).strip()
    return clean[:50] or "safe_file"

def validate_extension(filename: str, allowed: set[str]):
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": f"Unsupported file type. Allowed: {', '.join(allowed)}"
            }
        )

def check_disk_safety():
    """Emergency Disk Guard: Rejects new uploads if server disk space is dangerously full"""
    try:
        total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
        used_percent = (used / total) * 100
        # If disk > 90% full or free space < 1GB, reject to protect VPS from crashing
        if used_percent > 90 or (free / (1024 * 1024 * 1024)) < 1.0:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "SERVER_STORAGE_FULL",
                    "message": "Server is currently running automated maintenance. Please try again in 2 minutes."
                }
            )
    except HTTPException:
        raise
    except Exception:
        pass
