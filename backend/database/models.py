"""SQLAlchemy ORM models for the memory system.

Tables: memories, memory_edges, audit_log.
Enum values stored as VARCHAR for operational flexibility (no ALTER TYPE needed).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class MemoryORM(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=5)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    source: Mapped[dict] = mapped_column(JSON, default=dict)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    reinforcement_count: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("idx_memories_user_type", "user_id", "type"),
    )


class MemoryEdgeORM(Base):
    __tablename__ = "memory_edges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_new_uuid)
    from_memory_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    to_memory_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    relation: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditLogORM(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
