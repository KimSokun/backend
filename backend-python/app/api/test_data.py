from fastapi import APIRouter, Query, Body, Request
from app.services.test_data_service import TestDataService, DISCLAIMER
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/api/test-data", tags=["Test Data Tools"])

@router.get("/name")
async def get_mock_names(
    request: Request,
    count: int = Query(10, ge=1, le=100),
    gender: str = Query("all")
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    data = TestDataService.generate_names(count, gender)
    return {"success": True, "disclaimer": DISCLAIMER, "data": data}

@router.get("/address")
async def get_mock_addresses(
    request: Request,
    count: int = Query(5, ge=1, le=50)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    data = TestDataService.generate_addresses(count)
    return {"success": True, "disclaimer": DISCLAIMER, "data": data}

@router.get("/phone")
async def get_mock_phones(
    request: Request,
    count: int = Query(10, ge=1, le=100)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    data = TestDataService.generate_phones(count)
    return {"success": True, "disclaimer": DISCLAIMER, "data": data}

@router.get("/email")
async def get_mock_emails(
    request: Request,
    count: int = Query(10, ge=1, le=100)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    data = TestDataService.generate_emails(count)
    return {"success": True, "disclaimer": DISCLAIMER, "data": data}

@router.get("/company")
async def get_mock_companies(
    request: Request,
    count: int = Query(5, ge=1, le=50)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=100)
    data = TestDataService.generate_companies(count)
    return {"success": True, "disclaimer": DISCLAIMER, "data": data}

@router.post("/json")
async def get_mock_json(
    request: Request,
    payload: dict = Body(...)
):
    rate_limiter.check_rate_limit(request, limit_per_minute=50)
    fields = payload.get("fields", ["id", "name", "email", "phone", "company", "city"])
    count = int(payload.get("count", 10))
    data = TestDataService.generate_custom_json(fields, count)
    return {"success": True, "disclaimer": DISCLAIMER, "data": data}
