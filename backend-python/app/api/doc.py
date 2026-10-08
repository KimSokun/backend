from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
from fastapi.responses import FileResponse
from app.services.doc_service import DocService
from app.utils.files import save_uploaded_file, cleanup_temp_file
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/doc", tags=["Document Tools"])

ALLOWED_DOC_EXTS = {".docx", ".doc"}
ALLOWED_PDF_EXTS = {".pdf"}

@router.post("/word-to-pdf")
async def word_to_pdf(request: Request, file: UploadFile = File(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=20)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_DOC_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FORMAT", "message": "Only .docx / .doc Word files are supported."}
        )

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

@router.post("/pdf-to-word")
async def pdf_to_word_doc_router(request: Request, file: UploadFile = File(...)):
    from app.services.pdf_service import PdfService
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
