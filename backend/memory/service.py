"""High-level memory service — ties write + read paths.

Handles write path failure gracefully (log, continue to read path).
Handles read path failure with fallback (respond without memory — Invariant 3).
"""

from __future__ import annotations

import logging
import uuid

from backend.core.llm_client import LLMClient
from backend.core.storage_backend import StorageBackend
from backend.models.conversation import ConversationResponse
from backend.models.enums import WorkflowStatus
from backend.orchestrator.engine import SequentialWorkflowEngine
from backend.retrieve.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class MemoryService:

    def __init__(
        self,
        llm_client: LLMClient,
        store: StorageBackend,
        retriever: HybridRetriever,
    ):
        self._engine = SequentialWorkflowEngine(llm_client, store, retriever)

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: str = "",
    ) -> ConversationResponse:
        conversation_id = conversation_id or str(uuid.uuid4())
        workflow_id = f"{user_id}:{conversation_id}:{uuid.uuid4().hex[:8]}"

        # --- Write path (extract + evaluate + store) ---
        memories_stored = 0
        try:
            write_result = await self._engine.run_write_path(
                workflow_id=f"write:{workflow_id}",
                input_data={
                    "user_id": user_id,
                    "message": message,
                    "conversation_id": conversation_id,
                },
            )
            memories_stored = len(write_result.stored_memory_ids)
            if write_result.status == WorkflowStatus.FAILED:
                logger.warning("Write path failed: %s", write_result.error_message)
        except Exception as exc:
            logger.warning("Write path exception (continuing to read): %s", exc)

        # --- Read path (retrieve + rank + compose + respond) ---
        try:
            read_result = await self._engine.run_read_path(
                workflow_id=f"read:{workflow_id}",
                input_data={
                    "user_id": user_id,
                    "query": message,
                },
            )
            return ConversationResponse(
                response=read_result.response_text,
                conversation_id=conversation_id,
                memories_used=read_result.memories_used,
                memories_stored=memories_stored,
            )
        except Exception as exc:
            logger.error("Read path exception (fallback response): %s", exc)
            return ConversationResponse(
                response="I'm here to help, but I'm having trouble accessing my memory right now.",
                conversation_id=conversation_id,
                memories_used=[],
                memories_stored=memories_stored,
            )
