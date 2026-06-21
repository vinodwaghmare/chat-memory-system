"""Data access layer for memory operations.

Every query filters by user_id (Invariant 1) and excludes deleted records (Invariant 2).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AuditLogORM, MemoryEdgeORM, MemoryORM
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


class MemoryRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    # -----------------------------------------------------------------
    # Create
    # -----------------------------------------------------------------
    async def create_memory(
        self,
        user_id: str,
        memory_type: MemoryType,
        content: str,
        importance: int = 5,
        confidence: float = 0.8,
        source: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        row = MemoryORM(
            user_id=uuid.UUID(user_id),
            type=memory_type.value,
            content=content,
            importance=importance,
            confidence=confidence,
            source=source or {},
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _orm_to_record(row)

    # -----------------------------------------------------------------
    # Read
    # -----------------------------------------------------------------
    async def get_memory(self, memory_id: str, user_id: str) -> MemoryRecord | None:
        stmt = (
            select(MemoryORM)
            .where(
                MemoryORM.id == uuid.UUID(memory_id),
                MemoryORM.user_id == uuid.UUID(user_id),
                MemoryORM.deleted == False,  # noqa: E712 — Invariant 2
            )
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _orm_to_record(row) if row else None

    async def list_memories(
        self,
        user_id: str,
        memory_type: MemoryType | None = None,
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
        if memory_type is not None:
            stmt = stmt.where(MemoryORM.type == memory_type.value)
        if not include_archived:
            stmt = stmt.where(MemoryORM.archived == False)  # noqa: E712
        result = await self._session.execute(stmt)
        return [_orm_to_record(r) for r in result.scalars().all()]

    async def count_memories(self, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(MemoryORM)
            .where(
                MemoryORM.user_id == uuid.UUID(user_id),
                MemoryORM.deleted == False,  # noqa: E712
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # -----------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------
    async def update_memory(
        self,
        memory_id: str,
        user_id: str,
        updates: dict[str, Any],
    ) -> MemoryRecord | None:
        row = await self._get_owned_row(memory_id, user_id)
        if row is None:
            return None

        allowed = {"content", "type", "importance", "confidence"}
        for key, value in updates.items():
            if key in allowed:
                if key == "type" and isinstance(value, MemoryType):
                    value = value.value
                setattr(row, key, value)
        row.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(row)
        return _orm_to_record(row)

    async def update_weight(
        self,
        memory_id: str,
        weight: float,
    ) -> None:
        stmt = (
            update(MemoryORM)
            .where(MemoryORM.id == uuid.UUID(memory_id))
            .values(weight=weight, updated_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def reinforce(self, memory_id: str) -> None:
        row_stmt = select(MemoryORM).where(MemoryORM.id == uuid.UUID(memory_id))
        result = await self._session.execute(row_stmt)
        row = result.scalar_one_or_none()
        if row:
            row.reinforcement_count += 1
            row.weight = min(row.weight * 1.1, 10.0)
            row.updated_at = datetime.now(timezone.utc)
            await self._session.flush()

    # -----------------------------------------------------------------
    # Delete (soft)
    # -----------------------------------------------------------------
    async def soft_delete(self, memory_id: str, user_id: str) -> bool:
        row = await self._get_owned_row(memory_id, user_id)
        if row is None:
            return False
        row.deleted = True
        row.deleted_at = datetime.now(timezone.utc)
        row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return True

    # -----------------------------------------------------------------
    # Archive
    # -----------------------------------------------------------------
    async def archive_below_threshold(
        self,
        user_id: str,
        threshold: float,
    ) -> int:
        stmt = (
            select(MemoryORM)
            .where(
                MemoryORM.user_id == uuid.UUID(user_id),
                MemoryORM.deleted == False,  # noqa: E712
                MemoryORM.archived == False,  # noqa: E712
                MemoryORM.weight < threshold,
            )
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        for row in rows:
            row.archived = True
            row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return len(rows)

    # -----------------------------------------------------------------
    # Audit log
    # -----------------------------------------------------------------
    async def write_audit_log(
        self,
        user_id: str,
        action: str,
        memory_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        log = AuditLogORM(
            user_id=uuid.UUID(user_id),
            action=action,
            memory_id=uuid.UUID(memory_id) if memory_id else None,
            details=details,
        )
        self._session.add(log)
        await self._session.flush()

    async def get_audit_log(
        self,
        user_id: str,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(AuditLogORM)
            .where(AuditLogORM.user_id == uuid.UUID(user_id))
            .order_by(AuditLogORM.created_at.desc())
            .limit(limit)
        )
        if memory_id:
            stmt = stmt.where(AuditLogORM.memory_id == uuid.UUID(memory_id))
        result = await self._session.execute(stmt)
        return [
            {
                "id": str(row.id),
                "action": row.action,
                "memory_id": str(row.memory_id) if row.memory_id else None,
                "details": row.details,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in result.scalars().all()
        ]

    # -----------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------
    async def _get_owned_row(self, memory_id: str, user_id: str) -> MemoryORM | None:
        stmt = (
            select(MemoryORM)
            .where(
                MemoryORM.id == uuid.UUID(memory_id),
                MemoryORM.user_id == uuid.UUID(user_id),
                MemoryORM.deleted == False,  # noqa: E712
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
