"""Abstract interface for memory storage.

Exit hatch: swap pgvector for a dedicated vector cluster without
touching retrieval or capture logic. See ADR-001.

CONTRACT (Design by Contract):
  Invariant: every query method filters by user_id (Invariant 1)
             and excludes deleted records (Invariant 2).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.models.memory import MemoryRecord


class StorageBackend(ABC):

    @abstractmethod
    async def store(self, record: MemoryRecord) -> str:
        """Persist a memory record. Returns the assigned memory id."""
        ...

    @abstractmethod
    async def get(self, memory_id: str, user_id: str) -> MemoryRecord | None:
        """Fetch a single memory. Returns None if not found or not owned."""
        ...

    @abstractmethod
    async def list_memories(
        self,
        user_id: str,
        memory_type: str | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[MemoryRecord]:
        ...

    @abstractmethod
    async def search_vector(
        self,
        user_id: str,
        embedding: list[float],
        top_k: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """Cosine-similarity search. Returns (record, score) pairs."""
        ...

    @abstractmethod
    async def search_keyword(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[MemoryRecord, float]]:
        """Full-text search. Returns (record, rank) pairs."""
        ...

    @abstractmethod
    async def soft_delete(self, memory_id: str, user_id: str) -> bool:
        """Mark as deleted. Returns True if found and deleted."""
        ...

    @abstractmethod
    async def update_weight(self, memory_id: str, weight: float) -> None:
        ...

    @abstractmethod
    async def update_fields(
        self,
        memory_id: str,
        user_id: str,
        updates: dict[str, Any],
    ) -> MemoryRecord | None:
        ...

    @abstractmethod
    async def archive_below_threshold(
        self,
        user_id: str,
        threshold: float,
    ) -> int:
        """Archive memories with weight below threshold. Returns count."""
        ...
