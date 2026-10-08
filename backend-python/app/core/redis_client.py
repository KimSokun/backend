import redis.asyncio as aioredis
from typing import Optional
from app.core.config import settings

class RedisService:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._connected: bool = False

    async def get_client(self) -> Optional[aioredis.Redis]:
        if not settings.REDIS_ENABLED:
            return None
            
        if self._client is None:
            try:
                self._client = aioredis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD or None,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=1.5
                )
                await self._client.ping()
                self._connected = True
            except Exception:
                self._client = None
                self._connected = False
                
        return self._client

    async def get(self, key: str) -> Optional[str]:
        try:
            client = await self.get_client()
            if client:
                return await client.get(key)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        try:
            client = await self.get_client()
            if client:
                await client.set(key, value, ex=expire_seconds)
                return True
        except Exception:
            pass
        return False

    async def incr(self, key: str, expire_seconds: Optional[int] = None) -> int:
        try:
            client = await self.get_client()
            if client:
                val = await client.incr(key)
                if val == 1 and expire_seconds:
                    await client.expire(key, expire_seconds)
                return val
        except Exception:
            pass
        return 0

    @property
    def is_connected(self) -> bool:
        return self._connected

redis_service = RedisService()
