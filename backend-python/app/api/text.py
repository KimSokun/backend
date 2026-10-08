from fastapi import APIRouter, Body, Request
from app.services.text_service import TextService
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/text", tags=["Text Tools"])

@router.post("/word-count")
async def word_count(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = TextService.word_count(text)
    return {"success": True, "data": res}

@router.post("/case-convert")
async def case_convert(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    target_case = payload.get("case", "upper")
    res = TextService.case_convert(text, target_case)
    return {"success": True, "result": res}

@router.post("/clean")
async def clean_text(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    remove_duplicates = payload.get("removeDuplicates", True)
    trim_lines = payload.get("trimLines", True)
    remove_empty = payload.get("removeEmpty", True)
    res = TextService.clean_text(text, remove_duplicates, trim_lines, remove_empty)
    return {"success": True, "result": res}

@router.post("/base64-encode")
async def base64_encode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = TextService.base64_encode(text)
    return {"success": True, "result": res}

@router.post("/base64-decode")
async def base64_decode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = TextService.base64_decode(text)
    return {"success": True, "result": res}

@router.post("/url-encode")
async def url_encode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = TextService.url_encode(text)
    return {"success": True, "result": res}

@router.post("/url-decode")
async def url_decode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = TextService.url_decode(text)
    return {"success": True, "result": res}
