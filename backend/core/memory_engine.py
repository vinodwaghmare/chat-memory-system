"""Abstract interface for the memory system lifecycle.

CONTRACT (Design by Contract):
  Precondition:  user_id is always a non-empty string.
  Postcondition: returned memories ALWAYS belong to the requesting user_id.
  Invariant:     deleted memories are never returned by any method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.models.memory import MemoryRecord, ScoredMemory


class MemoryEngine(ABC):
    """Top-level abstraction that ties capture, store, and retrieve."""

    @abstractmethod
    async def capture(
        self,
        user_id: str,
        conversation_turn: dict[str, Any],
    ) -> list[MemoryRecord]:
        """Extract and store memories from a conversation turn.

        Args:
            user_id: Owner of the memories.
            conversation_turn: Dict with keys 'message', 'conversation_id',
                               'turn_number'.

        Returns:
            List of MemoryRecord objects that were actually stored
            (candidates that failed evaluation are excluded).
        """
        ...

    @abstractmethod
    async def retrieve(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[ScoredMemory]:
        """Retrieve the most relevant memories for a query.

        Args:
            user_id: Only this user's memories are searched.
            query: The natural-language query to match against.
            top_k: Maximum number of memories to return.

        Returns:
            List of ScoredMemory objects, sorted by final_score descending.
            Empty list if retrieval fails (Invariant 3).
        """
        ...

    @abstractmethod
    async def delete(self, user_id: str, memory_id: str) -> None:
        """Soft-delete a memory. It will never appear in retrieval again.

        Raises:
            MemoryNotFoundError: if the memory does not exist.
            MemoryAccessDeniedError: if user_id does not own it.
        """
        ...

    @abstractmethod
    async def update(
        self,
        user_id: str,
        memory_id: str,
        updates: dict[str, Any],
    ) -> MemoryRecord:
        """Update fields on an existing memory.

        Raises:
            MemoryNotFoundError: if the memory does not exist.
            MemoryAccessDeniedError: if user_id does not own it.
        """
        ...
