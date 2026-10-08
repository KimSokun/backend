import time
import asyncio
import logging
import shutil
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger("alltools_cleanup")

def get_folder_size_mb(path: Path) -> float:
    """Calculates total folder size in MB"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception:
        pass
    return total / (1024 * 1024)

def cleanup_expired_files(max_age_seconds: int = 1200):
    """
    Cleans temporary and generated result files older than max_age_seconds (default 20 mins).
    Also performs emergency purging if storage exceeds 2GB or disk is > 85% full.
    """
    now = time.time()
    deleted_count = 0
    deleted_bytes = 0

    # 1. Check if emergency purge is needed
    emergency_mode = False
    try:
        temp_size_mb = get_folder_size_mb(settings.TEMP_DIR)
        results_size_mb = get_folder_size_mb(settings.RESULTS_DIR)
        total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
        disk_used_percent = (used / total) * 100

        # If storage > 2GB or disk > 85% full, aggressively purge files older than 3 minutes
        if (temp_size_mb + results_size_mb > 2048) or disk_used_percent > 85:
            emergency_mode = True
            max_age_seconds = 180 # 3 minutes
            logger.warning(f"🚨 Emergency Storage Purge activated (Disk: {disk_used_percent:.1f}%)")
    except Exception:
        pass

    target_dirs = [settings.TEMP_DIR, settings.RESULTS_DIR]
    
    for directory in target_dirs:
        if not directory.exists():
            continue
            
        for file_path in directory.glob("*"):
            if file_path.is_file():
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        deleted_bytes += file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"Error removing {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"🧹 Automated Cleanup: Removed {deleted_count} files ({deleted_bytes / (1024*1024):.2f} MB). Emergency Mode: {emergency_mode}")

async def cleanup_worker_loop():
    """Background worker running every 3 minutes continuously"""
    while True:
        try:
            cleanup_expired_files()
        except Exception as e:
            logger.error(f"Cleanup worker error: {e}")
        await asyncio.sleep(180) # Run every 3 minutes
