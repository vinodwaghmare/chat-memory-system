"""Reflection job — periodically consolidates old memories.

For each user with many active memories, runs the reflection agent
to produce cleaner summaries and archives the originals.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.contracts import ReflectionTask
from backend.agents.reflection_agent import ReflectionAgent
from backend.core.llm_client import LLMClient
from backend.database.models import MemoryORM
from backend.database.repository import MemoryRepository
from backend.models.enums import MemoryType

logger = logging.getLogger(__name__)

MIN_MEMORIES_FOR_REFLECTION = 10
BATCH_SIZE = 10


class ReflectionJob:

    def __init__(self, session: AsyncSession, llm_client: LLMClient):
        self._session = session
        self._agent = ReflectionAgent(llm_client)
        self._repo = MemoryRepository(session)

    async def run(self, user_id: str) -> dict:
        stmt = (
            select(MemoryORM)
            .where(
                MemoryORM.user_id == user_id,
                MemoryORM.deleted == False,  # noqa: E712
                MemoryORM.archived == False,  # noqa: E712
            )
            .order_by(MemoryORM.created_at.asc())
            .limit(BATCH_SIZE)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        if len(rows) < MIN_MEMORIES_FOR_REFLECTION:
            return {"status": "skipped", "reason": "not enough memories"}

        task = ReflectionTask(
            user_id=user_id,
            memory_ids=tuple(str(r.id) for r in rows),
            memory_contents=tuple(r.content for r in rows),
            memory_types=tuple(r.type for r in rows),
        )

        consolidated = await self._agent.reflect(task)

        stored_ids: list[str] = []
        for cm in consolidated:
            record = await self._repo.create_memory(
                user_id=user_id,
                memory_type=cm.type,
                content=cm.content,
                importance=cm.importance,
                confidence=0.9,
                source={"origin": "reflection", "source_ids": list(cm.source_memory_ids)},
            )
            stored_ids.append(record.id)

        # Archive originals (not delete — preserves provenance, Invariant 4)
        for row in rows:
            row.archived = True

        await self._session.flush()

        logger.info("Reflection: consolidated %d → %d for user %s", len(rows), len(stored_ids), user_id)
        return {
            "status": "completed",
            "originals_archived": len(rows),
            "consolidated_created": len(stored_ids),
        }
