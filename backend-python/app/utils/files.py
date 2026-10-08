import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.core.security import sanitize_filename, check_disk_safety

MAX_FILE_BYTES = 50 * 1024 * 1024 # 50 MB Global Upload Ceiling

def get_unique_filename(original_filename: str, prefix: str = "") -> str:
    ext = Path(original_filename).suffix.lower()
    random_id = uuid.uuid4().hex[:12]
    clean_name = sanitize_filename(Path(original_filename).stem)[:30]
    if prefix:
        return f"{prefix}_{random_id}_{clean_name}{ext}"
    return f"{random_id}_{clean_name}{ext}"

async def save_upload_file_tmp(upload_file: UploadFile, max_bytes: int = MAX_FILE_BYTES) -> Path:
    # 1. Emergency Disk Safety Check
    check_disk_safety()

    filename = get_unique_filename(upload_file.filename or "file")
    temp_path = settings.TEMP_DIR / filename
    
    total_bytes = 0
    chunk_size = 512 * 1024 # 512KB chunks

    try:
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                
                # Enforce tool-specific upload ceiling to protect 2C2G VPS
                if total_bytes > max_bytes:
                    buffer.close()
                    if temp_path.exists():
                        temp_path.unlink()
                    limit_mb = max_bytes // (1024 * 1024)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "code": "FILE_TOO_LARGE",
                            "message": f"File size exceeds the {limit_mb}MB limit for this tool."
                        }
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "UPLOAD_FAILED", "message": f"Failed to save uploaded file: {str(e)}"}
        )
    finally:
        upload_file.file.close()
        
    return temp_path

save_uploaded_file = save_upload_file_tmp

def cleanup_temp_file(file_path: Path):
    try:
        if file_path and file_path.exists():
            file_path.unlink()
    except Exception:
        pass

def get_result_filepath(filename: str) -> Path:
    return settings.RESULTS_DIR / filename
