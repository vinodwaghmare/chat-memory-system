from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.memory import MemoryRecord


class MemoryListResponse(BaseModel):
    memories: list[MemoryRecord]
    total: int
    offset: int
    limit: int


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str = ""
    services: dict[str, str] = Field(default_factory=dict)
