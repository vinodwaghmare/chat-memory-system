"""Orchestrates the write path: embed, store, audit.

Handles embedding failure gracefully — stores without embedding.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.capture.extractor import CandidateMemory
from backend.core.storage_backend import StorageBackend
from backend.models.memory import MemoryRecord
from backend.tools.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class WriteService:

    def __init__(
        self,
        store: StorageBackend,
        embedding_service: EmbeddingService | None = None,
    ):
        self._store = store
        self._embedding = embedding_service

    async def write_memory(
        self,
        user_id: str,
        candidate: CandidateMemory,
        importance: int,
        confidence: float,
        source: dict[str, Any] | None = None,
    ) -> str:
        record = MemoryRecord(
            user_id=user_id,
            type=candidate.type,
            content=candidate.content,
            importance=importance,
            confidence=confidence,
            source=source or {},
        )

        memory_id = await self._store.store(record)
        logger.info("Stored memory %s for user %s: %s", memory_id, user_id, candidate.content[:50])
        return memory_id
