"""
Redis cache service for storing generated captions.
Cache key = SHA256 hash of image bytes.
"""

import hashlib
import json
from typing import Optional

import redis.asyncio as aioredis
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CacheService:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        try:
            self._client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._client.ping()
            logger.info("Redis connected", url=settings.redis_url)
        except Exception as e:
            logger.warning("Redis unavailable — caching disabled", error=str(e))
            self._client = None

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @staticmethod
    def _make_key(image_bytes: bytes, beam_size: int) -> str:
        digest = hashlib.sha256(image_bytes).hexdigest()
        return f"caption:{digest}:beam{beam_size}"

    async def get(self, image_bytes: bytes, beam_size: int) -> Optional[dict]:
        if not self._client:
            return None
        key = self._make_key(image_bytes, beam_size)
        try:
            value = await self._client.get(key)
            if value:
                logger.debug("Cache hit", key=key[:20])
                return json.loads(value)
        except Exception as e:
            logger.warning("Cache get error", error=str(e))
        return None

    async def set(self, image_bytes: bytes, beam_size: int,
                  result: dict) -> None:
        if not self._client:
            return
        key = self._make_key(image_bytes, beam_size)
        try:
            await self._client.setex(
                key, settings.cache_ttl_seconds, json.dumps(result))
            logger.debug("Cache set", key=key[:20])
        except Exception as e:
            logger.warning("Cache set error", error=str(e))


# Singleton
cache_service = CacheService()
