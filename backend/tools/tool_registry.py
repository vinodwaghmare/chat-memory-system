"""User-facing memory tools: remember, forget, inspect, correct.

Each tool is a callable that takes (user_id, args, store, session) and
returns a dict result.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AuditLogORM
from backend.database.repository import MemoryRepository
from backend.models.enums import MemoryType

logger = logging.getLogger(__name__)


class ToolRegistry:

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = MemoryRepository(session)

    async def remember_this(self, user_id: str, content: str, memory_type: str = "semantic") -> dict:
        """Force-store a memory with high importance."""
        try:
            mt = MemoryType(memory_type)
        except ValueError:
            mt = MemoryType.SEMANTIC

        record = await self._repo.create_memory(
            user_id=user_id,
            memory_type=mt,
            content=content,
            importance=9,
            confidence=1.0,
            source={"origin": "user_explicit"},
        )
        await self._repo.write_audit_log(user_id, "remember_this", record.id, {"content": content})
        return {"status": "remembered", "memory_id": record.id, "content": content}

    async def forget_this(self, user_id: str, query: str) -> dict:
        """Soft-delete memories matching the query."""
        memories = await self._repo.list_memories(user_id)
        deleted_ids: list[str] = []

        for mem in memories:
            if query.lower() in mem.content.lower():
                await self._repo.soft_delete(mem.id, user_id)
                await self._repo.write_audit_log(user_id, "forget_this", mem.id, {"query": query})
                deleted_ids.append(mem.id)

        return {"status": "forgotten", "deleted_count": len(deleted_ids), "deleted_ids": deleted_ids}

    async def show_memories(self, user_id: str, memory_type: str | None = None) -> dict:
        """List what the system knows about the user."""
        mt = MemoryType(memory_type) if memory_type else None
        memories = await self._repo.list_memories(user_id, memory_type=mt, limit=100)
        return {
            "status": "ok",
            "count": len(memories),
            "memories": [
                {"id": m.id, "type": m.type.value, "content": m.content,
                 "importance": m.importance, "confidence": m.confidence}
                for m in memories
            ],
        }

    async def correct_memory(self, user_id: str, memory_id: str, new_content: str) -> dict:
        """Update a memory's content."""
        record = await self._repo.update_memory(memory_id, user_id, {"content": new_content})
        if record is None:
            return {"status": "not_found", "memory_id": memory_id}

        await self._repo.write_audit_log(
            user_id, "correct_memory", memory_id,
            {"old_content": "unknown", "new_content": new_content},
        )
        return {"status": "corrected", "memory_id": memory_id, "new_content": new_content}
