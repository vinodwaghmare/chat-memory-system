"""Session-tier memory in Redis with TTL and promotion to long-term."""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.models.memory import MemoryRecord

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 7 * 24 * 3600  # 7 days


class RedisSessionStore:

    def __init__(self, redis_client: Any):
        self._redis = redis_client

    def _key(self, user_id: str) -> str:
        return f"session_memories:{user_id}"

    async def store(self, user_id: str, memory: MemoryRecord, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        key = self._key(user_id)
        data = memory.model_dump_json()
        try:
            await self._redis.hset(key, memory.id, data)
            await self._redis.expire(key, ttl)
        except Exception as exc:
            logger.warning("Redis session store failed: %s", exc)

    async def get_all(self, user_id: str) -> list[MemoryRecord]:
        key = self._key(user_id)
        try:
            data = await self._redis.hgetall(key)
            return [MemoryRecord.model_validate_json(v) for v in data.values()]
        except Exception as exc:
            logger.warning("Redis session read failed: %s", exc)
            return []

    async def remove(self, user_id: str, memory_id: str) -> None:
        try:
            await self._redis.hdel(self._key(user_id), memory_id)
        except Exception as exc:
            logger.warning("Redis session remove failed: %s", exc)
