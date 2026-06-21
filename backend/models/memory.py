from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.models.enums import MemoryType


class MemoryRecord(BaseModel):
    id: str = ""
    user_id: str
    type: MemoryType
    content: str
    embedding: list[float] | None = None
    importance: int = 5
    confidence: float = 0.8
    source: dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0
    reinforcement_count: int = 0
    archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MemoryCreate(BaseModel):
    type: MemoryType
    content: str
    importance: int = 5
    confidence: float = 0.8
    source: dict[str, Any] = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    content: str | None = None
    type: MemoryType | None = None
    importance: int | None = None
    confidence: float | None = None


class ScoredMemory(BaseModel):
    memory: MemoryRecord
    final_score: float
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
