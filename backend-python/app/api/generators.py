from fastapi import APIRouter, Query, Body, Request
from app.services.generator_service import GeneratorService
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/generator", tags=["Generators"])

@router.get("/password")
async def generate_password(
    request: Request,
    length: int = Query(16, ge=4, le=128),
    uppercase: bool = Query(True),
    lowercase: bool = Query(True),
    numbers: bool = Query(True),
    symbols: bool = Query(True)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    password = GeneratorService.generate_password(
        length=length,
        include_uppercase=uppercase,
        include_lowercase=lowercase,
        include_numbers=numbers,
        include_symbols=symbols
    )
    return {"success": True, "password": password}

@router.get("/uuid")
async def generate_uuid(
    request: Request,
    count: int = Query(1, ge=1, le=100),
    version: str = Query("v4")
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    uuids = GeneratorService.generate_uuids(count=count, version=version)
    return {"success": True, "uuids": uuids}

@router.post("/qr")
async def generate_qr(
    request: Request,
    payload: dict = Body(...)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=50)
    data = payload.get("data", "https://alltools.online")
    size = int(payload.get("size", 10))
    error_correction = payload.get("errorCorrection", "M")
    fmt = payload.get("format", "png")
    
    qr_data_uri = GeneratorService.generate_qr_code(
        data=data,
        size=size,
        error_correction=error_correction,
        format=fmt
    )
    return {"success": True, "qrDataUri": qr_data_uri, "format": fmt}

@router.get("/username")
async def generate_username(
    request: Request,
    category: str = Query("all")
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    from faker import Faker
    f = Faker()
    usernames = [f.user_name() for _ in range(10)]
    return {"success": True, "usernames": usernames}

@router.get("/random-string")
async def generate_random_string(
    request: Request,
    length: int = Query(16, ge=1, le=500),
    charset: str = Query("alphanumeric")
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    res = GeneratorService.generate_random_string(length, charset)
    return {"success": True, "result": res}

@router.get("/color")
async def generate_color_palette(
    request: Request,
    count: int = Query(5, ge=1, le=20)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    colors = GeneratorService.generate_color_palette(count)
    return {"success": True, "palette": colors}
