from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from fastapi.responses import FileResponse
from app.services.image_service import ImageService
from app.utils.files import save_upload_file_tmp
from app.core.security import validate_extension, ALLOWED_IMAGE_EXTENSIONS
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/image", tags=["Image Tools"])

EXTENDED_IMAGE_EXTS = ALLOWED_IMAGE_EXTENSIONS | {".ico", ".svg", ".bmp", ".gif"}

@router.post("/remove-background")
@router.post("/remove-bg")
async def remove_background(
    request: Request,
    file: UploadFile = File(...)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    validate_extension(file.filename or "", ALLOWED_IMAGE_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file)
    result_path = ImageService.remove_background(tmp_path)
    
    return FileResponse(
        path=result_path,
        media_type="image/png",
        filename=f"nobg_{file.filename}.png"
    )

@router.post("/remove-logo-bg")
async def remove_logo_background(
    request: Request,
    file: UploadFile = File(...),
    smoothness: int = Form(2),
    tolerance: int = Form(20),
    protect_inner: bool = Form(True)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    validate_extension(file.filename or "", ALLOWED_IMAGE_EXTENSIONS)

    tmp_path = await save_upload_file_tmp(file)
    result_path = ImageService.remove_logo_background(tmp_path, smoothness, tolerance, protect_inner)

    return FileResponse(
        path=result_path,
        media_type="image/png",
        filename=f"clean_logo_{file.filename}.png"
    )

@router.post("/convert")
async def convert_image(
    request: Request,
    file: UploadFile = File(...),
    target_format: str = Form("png"),
    quality: int = Form(90)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=30)
    validate_extension(file.filename or "", EXTENDED_IMAGE_EXTS)
    
    tmp_path = await save_upload_file_tmp(file)
    result_path = ImageService.convert_image(tmp_path, target_format, quality)
    
    media_map = {
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "bmp": "image/bmp"
    }
    media_type = media_map.get(target_format.lower(), "application/octet-stream")

    return FileResponse(
        path=result_path,
        media_type=media_type,
        filename=result_path.name
    )

@router.post("/to-ico")
async def convert_to_ico(
    request: Request,
    file: UploadFile = File(...)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=30)
    validate_extension(file.filename or "", ALLOWED_IMAGE_EXTENSIONS)

    tmp_path = await save_upload_file_tmp(file)
    result_path = ImageService.convert_to_ico(tmp_path)

    return FileResponse(
        path=result_path,
        media_type="image/x-icon",
        filename=f"favicon_{file.filename}.ico"
    )

@router.post("/to-svg")
async def convert_to_svg(
    request: Request,
    file: UploadFile = File(...)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=30)
    validate_extension(file.filename or "", ALLOWED_IMAGE_EXTENSIONS)

    tmp_path = await save_upload_file_tmp(file)
    result_path = ImageService.convert_to_svg(tmp_path)

    return FileResponse(
        path=result_path,
        media_type="image/svg+xml",
        filename=f"vector_{file.filename}.svg"
    )

@router.post("/compress")
async def compress_image(
    request: Request,
    file: UploadFile = File(...),
    quality: int = Form(75)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=30)
    validate_extension(file.filename or "", ALLOWED_IMAGE_EXTENSIONS)
    
    tmp_path = await save_upload_file_tmp(file)
    res = ImageService.compress_image(tmp_path, quality)
    
    return FileResponse(
        path=res["file_path"],
        media_type="image/jpeg",
        filename=res["file_path"].name,
        headers={
            "X-Original-Size": str(res["original_size"]),
            "X-Compressed-Size": str(res["compressed_size"]),
            "X-Saved-Percent": str(res["saved_percent"])
        }
    )
