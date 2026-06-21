"""Graph retriever — walks memory_edges for related memories (1-hop)."""

from __future__ import annotations

import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import MemoryEdgeORM, MemoryORM
from backend.models.enums import MemoryType
from backend.models.memory import MemoryRecord

logger = logging.getLogger(__name__)


def _orm_to_record(row: MemoryORM) -> MemoryRecord:
    return MemoryRecord(
        id=str(row.id),
        user_id=str(row.user_id),
        type=MemoryType(row.type),
        content=row.content,
        importance=row.importance,
        confidence=row.confidence,
        source=row.source or {},
        weight=row.weight,
        reinforcement_count=row.reinforcement_count,
        archived=row.archived,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class GraphRetriever:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_related(
        self,
        user_id: str,
        memory_ids: list[str],
        max_results: int = 5,
    ) -> list[tuple[MemoryRecord, str]]:
        """Returns (related_memory, relation_type) pairs from 1-hop edges."""
        if not memory_ids:
            return []

        try:
            source_uuids = [uuid.UUID(mid) for mid in memory_ids]
            stmt = (
                select(MemoryEdgeORM)
                .where(
                    MemoryEdgeORM.user_id == uuid.UUID(user_id),
                    MemoryEdgeORM.from_memory_id.in_(source_uuids),
                )
                .limit(max_results)
            )
            result = await self._session.execute(stmt)
            edges = result.scalars().all()

            if not edges:
                return []

            target_ids = [e.to_memory_id for e in edges]
            mem_stmt = (
                select(MemoryORM)
                .where(
                    MemoryORM.id.in_(target_ids),
                    MemoryORM.user_id == uuid.UUID(user_id),
                    MemoryORM.deleted == False,  # noqa: E712
                )
            )
            mem_result = await self._session.execute(mem_stmt)
            mem_map = {row.id: row for row in mem_result.scalars().all()}

            results = []
            for edge in edges:
                mem_row = mem_map.get(edge.to_memory_id)
                if mem_row:
                    results.append((_orm_to_record(mem_row), edge.relation))

            return results
        except Exception as exc:
            logger.warning("Graph retrieval failed: %s", exc)
            return []
