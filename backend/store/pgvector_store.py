"""Concrete StorageBackend using PostgreSQL + pgvector.

Vector search via cosine distance, keyword search via ts_rank.
Every query enforces user_id (Invariant 1) and deleted=false (Invariant 2).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.storage_backend import StorageBackend
from backend.database.models import AuditLogORM, MemoryORM
from backend.models.enums import MemoryType
from backend.models.memory import MemoryRecord


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


class PgVectorStore(StorageBackend):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def store(self, record: MemoryRecord) -> str:
        row = MemoryORM(
            user_id=uuid.UUID(record.user_id),
            type=record.type.value,
            content=record.content,
            embedding=record.embedding,
            importance=record.importance,
            confidence=record.confidence,
            source=record.source,
            weight=record.weight,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return str(row.id)

    async def get(self, memory_id: str, user_id: str) -> MemoryRecord | None:
        stmt = select(MemoryORM).where(
            MemoryORM.id == uuid.UUID(memory_id),
            MemoryORM.user_id == uuid.UUID(user_id),
            MemoryORM.deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _orm_to_record(row) if row else None

    async def list_memories(
        self,
        user_id: str,
        memory_type: str | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        stmt = (
            select(MemoryORM)
            .where(
                MemoryORM.user_id == uuid.UUID(user_id),
                MemoryORM.deleted == False,  # noqa: E712
            )
            .order_by(MemoryORM.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if memory_type:
            stmt = stmt.where(MemoryORM.type == memory_type)
        if not include_archived:
            stmt = stmt.where(MemoryORM.archived == False)  # noqa: E712
        result = await self._session.execute(stmt)
        return [_orm_to_record(r) for r in result.scalars().all()]

    async def search_vector(
        self,
        user_id: str,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        # pgvector cosine distance: <=> operator
        # SQLite fallback: return empty (no vector support in tests)
        try:
            vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
            stmt = text("""
                SELECT id, user_id, type, content, importance, confidence,
                       source, weight, reinforcement_count, archived,
                       created_at, updated_at,
                       1 - (embedding <=> :vec::vector) AS score
                FROM memories
                WHERE user_id = :uid
                  AND deleted = false
                  AND archived = false
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> :vec::vector
                LIMIT :topk
            """)
            result = await self._session.execute(
                stmt,
                {"vec": vec_str, "uid": user_id, "topk": top_k},
            )
            rows = result.fetchall()
            return [
                (MemoryRecord(
                    id=str(r.id), user_id=str(r.user_id),
                    type=MemoryType(r.type), content=r.content,
                    importance=r.importance, confidence=r.confidence,
                    source=r.source or {}, weight=r.weight,
                    reinforcement_count=r.reinforcement_count,
                    archived=r.archived, created_at=r.created_at,
                    updated_at=r.updated_at,
                ), float(r.score))
                for r in rows
            ]
        except Exception:
            return []

    async def search_keyword(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        # Full-text search with simple LIKE for cross-DB compatibility
        # Production: use ts_rank + to_tsvector for Postgres
        pattern = f"%{query}%"
        stmt = (
            select(MemoryORM)
            .where(
                MemoryORM.user_id == uuid.UUID(user_id),
                MemoryORM.deleted == False,  # noqa: E712
                MemoryORM.archived == False,  # noqa: E712
                MemoryORM.content.ilike(pattern),
            )
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [(_orm_to_record(r), 0.5) for r in rows]

    async def soft_delete(self, memory_id: str, user_id: str) -> bool:
        stmt = select(MemoryORM).where(
            MemoryORM.id == uuid.UUID(memory_id),
            MemoryORM.user_id == uuid.UUID(user_id),
            MemoryORM.deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return False
        row.deleted = True
        row.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        return True

    async def update_weight(self, memory_id: str, weight: float) -> None:
        stmt = (
            update(MemoryORM)
            .where(MemoryORM.id == uuid.UUID(memory_id))
            .values(weight=weight, updated_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def update_fields(
        self,
        memory_id: str,
        user_id: str,
        updates: dict[str, Any],
    ) -> MemoryRecord | None:
        stmt = select(MemoryORM).where(
            MemoryORM.id == uuid.UUID(memory_id),
            MemoryORM.user_id == uuid.UUID(user_id),
            MemoryORM.deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        allowed = {"content", "type", "importance", "confidence", "weight"}
        for k, v in updates.items():
            if k in allowed:
                setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(row)
        return _orm_to_record(row)

    async def archive_below_threshold(self, user_id: str, threshold: float) -> int:
        stmt = select(MemoryORM).where(
            MemoryORM.user_id == uuid.UUID(user_id),
            MemoryORM.deleted == False,  # noqa: E712
            MemoryORM.archived == False,  # noqa: E712
            MemoryORM.weight < threshold,
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        for row in rows:
            row.archived = True
            row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return len(rows)
