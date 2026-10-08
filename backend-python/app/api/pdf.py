from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from fastapi.responses import FileResponse, JSONResponse
from app.services.pdf_service import PdfService
from app.utils.files import save_uploaded_file, cleanup_temp_file
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/pdf", tags=["PDF Tools"])

@router.post("/jpg-to-pdf")
async def images_to_pdf(request: Request, files: list[UploadFile] = File(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    saved_paths = []
    try:
        for file in files:
            p = await save_uploaded_file(file)
            saved_paths.append(p)
            
        result_pdf = PdfService.images_to_pdf(saved_paths)
        return FileResponse(
            path=str(result_pdf),
            filename=result_pdf.name,
            media_type="application/pdf"
        )
    finally:
        for p in saved_paths:
            cleanup_temp_file(p)

@router.post("/pdf-to-word")
async def pdf_to_word(request: Request, file: UploadFile = File(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=15)
    temp_path = await save_uploaded_file(file)
    try:
        docx_path = PdfService.pdf_to_docx(temp_path)
        return FileResponse(
            path=str(docx_path),
            filename=f"{Path(file.filename or 'document').stem}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    finally:
        cleanup_temp_file(temp_path)

@router.post("/word-to-pdf")
async def word_to_pdf_pdf_router(request: Request, file: UploadFile = File(...)):
    from app.services.doc_service import DocService
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    temp_path = await save_uploaded_file(file)
    try:
        pdf_path = DocService.word_to_pdf(temp_path)
        return FileResponse(
            path=str(pdf_path),
            filename=f"{Path(file.filename or 'document').stem}.pdf",
            media_type="application/pdf"
        )
    finally:
        cleanup_temp_file(temp_path)

@router.post("/pdf-to-jpg")
async def pdf_to_jpg(request: Request, file: UploadFile = File(...), dpi: int = Form(150)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    temp_path = await save_uploaded_file(file)
    try:
        result_images = PdfService.pdf_to_images(temp_path, format_type='jpg', dpi=dpi)
        if not result_images:
            raise HTTPException(status_code=400, detail="Could not extract pages from PDF.")
        first_img = result_images[0]
        return FileResponse(
            path=str(first_img),
            filename=first_img.name,
            media_type="image/jpeg"
        )
    finally:
        cleanup_temp_file(temp_path)

@router.post("/pdf-to-png")
async def pdf_to_png(request: Request, file: UploadFile = File(...), dpi: int = Form(150)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    temp_path = await save_uploaded_file(file)
    try:
        result_images = PdfService.pdf_to_images(temp_path, format_type='png', dpi=dpi)
        if not result_images:
            raise HTTPException(status_code=400, detail="Could not extract pages from PDF.")
        first_img = result_images[0]
        return FileResponse(
            path=str(first_img),
            filename=first_img.name,
            media_type="image/png"
        )
    finally:
        cleanup_temp_file(temp_path)

@router.post("/pdf-to-webp")
async def pdf_to_webp(request: Request, file: UploadFile = File(...), dpi: int = Form(150)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    temp_path = await save_uploaded_file(file)
    try:
        result_images = PdfService.pdf_to_images(temp_path, format_type='webp', dpi=dpi)
        if not result_images:
            raise HTTPException(status_code=400, detail="Could not extract pages from PDF.")
        first_img = result_images[0]
        return FileResponse(
            path=str(first_img),
            filename=first_img.name,
            media_type="image/webp"
        )
    finally:
        cleanup_temp_file(temp_path)

@router.post("/pdf-to-text")
async def pdf_to_text(request: Request, file: UploadFile = File(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=30)
    temp_path = await save_uploaded_file(file)
    try:
        extracted = PdfService.pdf_to_text(temp_path)
        return {
            "success": True,
            "filename": file.filename,
            "text": extracted
        }
    finally:
        cleanup_temp_file(temp_path)

@router.post("/merge")
async def merge_pdfs(request: Request, files: list[UploadFile] = File(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    saved_paths = []
    try:
        for file in files:
            p = await save_uploaded_file(file)
            saved_paths.append(p)
            
        merged_pdf = PdfService.merge_pdfs(saved_paths)
        return FileResponse(
            path=str(merged_pdf),
            filename="merged.pdf",
            media_type="application/pdf"
        )
    finally:
        for p in saved_paths:
            cleanup_temp_file(p)

@router.post("/split")
async def split_pdf(request: Request, file: UploadFile = File(...), page_ranges: str = Form("1-1")):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    temp_path = await save_uploaded_file(file)
    try:
        split_pdf_path = PdfService.split_pdf(temp_path, page_ranges)
        return FileResponse(
            path=str(split_pdf_path),
            filename=split_pdf_path.name,
            media_type="application/pdf"
        )
    finally:
        cleanup_temp_file(temp_path)

@router.post("/compress")
async def compress_pdf(request: Request, file: UploadFile = File(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    temp_path = await save_uploaded_file(file)
    try:
        info = PdfService.compress_pdf(temp_path)
        return FileResponse(
            path=str(info["file_path"]),
            filename=info["file_path"].name,
            media_type="application/pdf",
            headers={
                "X-Original-Size": str(info["original_size"]),
                "X-Compressed-Size": str(info["compressed_size"]),
                "X-Saved-Percent": str(info["saved_percent"])
            }
        )
    finally:
        cleanup_temp_file(temp_path)
