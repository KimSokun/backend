from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from app.services.video_service import VideoService
from app.utils.files import save_upload_file_tmp
from app.core.security import validate_extension, ALLOWED_VIDEO_EXTENSIONS
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/video", tags=["Video Tools"])

# Strict 2C2G Resource Protection Limits
VIDEO_5MB_LIMIT = 5 * 1024 * 1024
AUDIO_10MB_LIMIT = 10 * 1024 * 1024

@router.post("/convert")
async def convert_video(
    request: Request,
    file: UploadFile = File(...),
    output_format: str = Form("mp4")
):
    rate_limiter.check_rate_limit(request, limit_per_minute=10)
    validate_extension(file.filename or "", ALLOWED_VIDEO_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file, max_bytes=VIDEO_5MB_LIMIT)
    res_path = VideoService.convert_video(tmp_path, output_format)
    
    return FileResponse(path=res_path, filename=res_path.name)

@router.post("/compress")
async def compress_video(
    request: Request,
    file: UploadFile = File(...),
    crf: int = Form(28)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=10)
    validate_extension(file.filename or "", ALLOWED_VIDEO_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file, max_bytes=VIDEO_5MB_LIMIT)
    res = VideoService.compress_video(tmp_path, crf)
    
    return FileResponse(
        path=res["file_path"],
        filename=res["file_path"].name,
        headers={
            "X-Original-Size": str(res["original_size"]),
            "X-Compressed-Size": str(res["compressed_size"]),
            "X-Saved-Percent": str(res["saved_percent"])
        }
    )

@router.post("/to-mp3")
async def video_to_mp3(
    request: Request,
    file: UploadFile = File(...),
    bitrate: str = Form("192k")
):
    rate_limiter.check_rate_limit(request, limit_per_minute=15)
    validate_extension(file.filename or "", ALLOWED_VIDEO_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file, max_bytes=AUDIO_10MB_LIMIT)
    res_path = VideoService.video_to_mp3(tmp_path, bitrate)
    
    return FileResponse(path=res_path, media_type="audio/mpeg", filename=res_path.name)

@router.post("/to-gif")
async def video_to_gif(
    request: Request,
    file: UploadFile = File(...),
    fps: int = Form(12),
    width: int = Form(480)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=10)
    validate_extension(file.filename or "", ALLOWED_VIDEO_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file, max_bytes=VIDEO_5MB_LIMIT)
    res_path = VideoService.video_to_gif(tmp_path, fps, width)
    
    return FileResponse(path=res_path, media_type="image/gif", filename=res_path.name)

@router.post("/resize")
async def resize_video(
    request: Request,
    file: UploadFile = File(...),
    width: int = Form(1280),
    height: int = Form(720)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=10)
    validate_extension(file.filename or "", ALLOWED_VIDEO_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file, max_bytes=VIDEO_5MB_LIMIT)
    res_path = VideoService.resize_video(tmp_path, width, height)
    
    return FileResponse(path=res_path, filename=res_path.name)
