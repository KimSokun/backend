import time
import asyncio
from collections import defaultdict
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.redis_client import redis_service

# Global Concurrency Limiter: Caps heavy CPU tasks to 4 simultaneous workers
HEAVY_TASK_SEMAPHORE = asyncio.Semaphore(4)

class MemoryRateLimiter:
    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: dict[str, list[float]] = defaultdict(list)
        self.blocked_ips: dict[str, float] = {}

    def is_rate_limited(self, ip: str) -> bool:
        now = time.time()
        
        # Check active ban
        if ip in self.blocked_ips:
            if now < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]

        self.history[ip] = [t for t in self.history[ip] if now - t < self.window_seconds]
        
        # Auto-Ban if flooding > 3x limit (abusive bot)
        if len(self.history[ip]) > (self.requests_limit * 3):
            self.blocked_ips[ip] = now + 900 # 15 min ban
            return True

        if len(self.history[ip]) >= self.requests_limit:
            return True
            
        self.history[ip].append(now)
        return False

# Local in-memory fallback limiters
standard_memory_limiter = MemoryRateLimiter(requests_limit=settings.RATE_LIMIT_PER_MINUTE)
heavy_memory_limiter = MemoryRateLimiter(requests_limit=settings.HEAVY_RATE_LIMIT_PER_MINUTE)
upload_memory_limiter = MemoryRateLimiter(requests_limit=6) # Max 6 uploads/min per IP

def get_client_ip(request: Request) -> str:
    # 1. Cloudflare Proxied Client IP (Primary)
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
        
    # 2. Standard X-Forwarded-For header
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
        
    # 3. Direct socket host
    return request.client.host if request.client else "127.0.0.1"

async def check_rate_limit(request: Request):
    ip = get_client_ip(request)
    
    redis_key = f"ratelimit:std:{ip}"
    count = await redis_service.incr(redis_key, expire_seconds=60)
    
    if count > 0:
        if count > settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please wait a minute."}
            )
    else:
        if standard_memory_limiter.is_rate_limited(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please wait a minute."}
            )

async def check_heavy_rate_limit(request: Request):
    """Protects AI Background Removal & Video conversions"""
    ip = get_client_ip(request)
    
    redis_key = f"ratelimit:heavy:{ip}"
    count = await redis_service.incr(redis_key, expire_seconds=60)
    
    if count > 0:
        if count > settings.HEAVY_RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "HEAVY_RATE_LIMIT_EXCEEDED", "message": "Processing limit reached. Please wait before submitting another job."}
            )
    else:
        if heavy_memory_limiter.is_rate_limited(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "HEAVY_RATE_LIMIT_EXCEEDED", "message": "Processing limit reached. Please wait before submitting another job."}
            )

async def check_upload_limit(request: Request):
    """Strict Upload Guard: Limits max file uploads to 6 per minute per IP"""
    ip = get_client_ip(request)
    
    redis_key = f"ratelimit:upload:{ip}"
    count = await redis_service.incr(redis_key, expire_seconds=60)
    
    if count > 0:
        if count > 6:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "UPLOAD_LIMIT_EXCEEDED", "message": "Upload frequency limit reached (Max 6 uploads/min). Please wait 30 seconds."}
            )
    else:
        if upload_memory_limiter.is_rate_limited(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "UPLOAD_LIMIT_EXCEEDED", "message": "Upload frequency limit reached (Max 6 uploads/min). Please wait 30 seconds."}
            )

class RateLimiterCompat:
    def check_rate_limit(self, request: Request, limit_per_minute: int = 60):
        ip = get_client_ip(request)
        if standard_memory_limiter.is_rate_limited(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please wait a minute."}
            )

rate_limiter = RateLimiterCompat()
