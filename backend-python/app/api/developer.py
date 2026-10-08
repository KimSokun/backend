from fastapi import APIRouter, Body, Query, Request
from app.services.dev_service import DevService
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/dev", tags=["Developer Tools"])

@router.post("/json-format")
async def json_format(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    raw = payload.get("json", "")
    indent = int(payload.get("indent", 2))
    res = DevService.format_json(raw, indent)
    return {"success": True, "data": res}

@router.post("/json-validate")
async def json_validate(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    raw = payload.get("json", "")
    res = DevService.format_json(raw)
    return {"success": True, "data": res}

@router.get("/timestamp")
async def timestamp_convert(
    request: Request,
    timestamp: float = Query(...)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    res = DevService.convert_timestamp(timestamp)
    return {"success": True, "data": res}

@router.post("/hash")
async def generate_hash(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = DevService.generate_hashes(text)
    return {"success": True, "hashes": res}

@router.post("/regex-test")
async def regex_test(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    pattern = payload.get("pattern", "")
    text = payload.get("text", "")
    flags = payload.get("flags", "")
    res = DevService.test_regex(pattern, text, flags)
    return {"success": True, "data": res}

@router.post("/jwt-decode")
async def jwt_decode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    token = payload.get("token", "")
    res = DevService.decode_jwt(token)
    return {"success": True, "data": res}

@router.post("/html-encode")
async def html_encode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = DevService.html_encode(text)
    return {"success": True, "result": res}

@router.post("/html-decode")
async def html_decode(request: Request, payload: dict = Body(...)):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    text = payload.get("text", "")
    res = DevService.html_decode(text)
    return {"success": True, "result": res}
