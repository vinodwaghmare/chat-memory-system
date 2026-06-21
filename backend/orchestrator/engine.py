"""Concrete WorkflowEngine implementation using sequential async calls.

LangGraph graph construction deferred — this engine runs nodes in sequence,
which is functionally identical for a linear pipeline and avoids the
LangGraph dependency in tests. The abstract interface allows swapping later.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.capture.evaluator import MemoryEvaluator
from backend.capture.extractor import MemoryExtractor
from backend.context.composer import ContextComposer
from backend.core.llm_client import LLMClient
from backend.core.storage_backend import StorageBackend
from backend.core.workflow_engine import (
    ReadPathResult,
    WorkflowEngine,
    WritePathResult,
)
from backend.models.enums import WorkflowStatus
from backend.orchestrator.nodes import ReadNodes, WriteNodes
from backend.retrieve.hybrid_retriever import HybridRetriever
from backend.store.write_service import WriteService
from backend.tools.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SequentialWorkflowEngine(WorkflowEngine):

    def __init__(
        self,
        llm_client: LLMClient,
        store: StorageBackend,
        retriever: HybridRetriever,
    ):
        self._write_nodes = WriteNodes(
            extractor=MemoryExtractor(llm_client),
            evaluator=MemoryEvaluator(llm_client),
            write_service=WriteService(store, EmbeddingService(llm_client)),
        )
        self._read_nodes = ReadNodes(
            retriever=retriever,
            composer=ContextComposer(),
            llm_client=llm_client,
        )

    async def run_write_path(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
    ) -> WritePathResult:
        started = datetime.now(timezone.utc)
        state: dict[str, Any] = {
            "workflow_id": workflow_id,
            "user_id": input_data["user_id"],
            "user_message": input_data["message"],
            "conversation_id": input_data.get("conversation_id", ""),
        }

        try:
            state.update(await self._write_nodes.extract(state))
            state.update(await self._write_nodes.evaluate(state))
            state.update(await self._write_nodes.store(state))

            return WritePathResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                stored_memory_ids=state.get("stored_memory_ids", []),
                candidates_extracted=len(state.get("candidate_memories", [])),
                candidates_approved=len(state.get("approved_candidates", [])),
                started_at=started,
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.error("Write path failed: %s", exc)
            return WritePathResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error_message=str(exc),
                started_at=started,
                completed_at=datetime.now(timezone.utc),
            )

    async def run_read_path(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
    ) -> ReadPathResult:
        started = datetime.now(timezone.utc)
        state: dict[str, Any] = {
            "workflow_id": workflow_id,
            "user_id": input_data["user_id"],
            "user_query": input_data["query"],
        }

        try:
            state.update(await self._read_nodes.retrieve(state))
            state.update(await self._read_nodes.compose(state))
            state.update(await self._read_nodes.respond(state))

            return ReadPathResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                response_text=state.get("response_text", ""),
                memories_used=state.get("retrieved_memories", []),
                started_at=started,
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.error("Read path failed: %s", exc)
            return ReadPathResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                response_text="I couldn't process your request right now.",
                error_message=str(exc),
                started_at=started,
                completed_at=datetime.now(timezone.utc),
            )

    async def get_state(self, workflow_id: str) -> dict[str, Any] | None:
        return None
