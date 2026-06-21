"""Node functions for the LangGraph write and read paths.

Each node takes state, performs one step, returns partial state update.
Errors are caught and recorded in state — never crash the workflow.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.capture.evaluator import MemoryEvaluator
from backend.capture.extractor import MemoryExtractor
from backend.context.composer import ContextComposer
from backend.core.llm_client import LLMClient
from backend.core.storage_backend import StorageBackend
from backend.models.memory import MemoryRecord, ScoredMemory
from backend.prompts.registry import load_prompt
from backend.retrieve.hybrid_retriever import HybridRetriever
from backend.store.write_service import WriteService
from backend.tools.model_router import TaskType, get_model_config

logger = logging.getLogger(__name__)


class WriteNodes:
    """Nodes for the write path: extract → evaluate → store."""

    def __init__(
        self,
        extractor: MemoryExtractor,
        evaluator: MemoryEvaluator,
        write_service: WriteService,
    ):
        self._extractor = extractor
        self._evaluator = evaluator
        self._writer = write_service

    async def extract(self, state: dict) -> dict:
        try:
            candidates = await self._extractor.extract(state["user_message"])
            return {
                "candidate_memories": [
                    {"type": c.type.value, "content": c.content, "importance_hint": c.importance_hint}
                    for c in candidates
                ],
                "status": "evaluating",
            }
        except Exception as exc:
            logger.warning("Extraction failed: %s", exc)
            return {
                "candidate_memories": [],
                "extraction_error": str(exc),
                "status": "failed",
            }

    async def evaluate(self, state: dict) -> dict:
        candidates_raw = state.get("candidate_memories", [])
        if not candidates_raw:
            return {"approved_candidates": [], "rejected_count": 0, "status": "storing"}

        from backend.capture.extractor import CandidateMemory
        from backend.models.enums import MemoryType

        approved = []
        rejected = 0
        for c in candidates_raw:
            try:
                candidate = CandidateMemory(
                    type=MemoryType(c["type"]),
                    content=c["content"],
                    importance_hint=c.get("importance_hint", 5),
                )
                result = await self._evaluator.evaluate(candidate)
                if result.keep:
                    approved.append({
                        "type": c["type"],
                        "content": c["content"],
                        "importance": result.importance,
                        "confidence": result.confidence,
                    })
                else:
                    rejected += 1
            except Exception as exc:
                logger.warning("Evaluation failed for candidate: %s", exc)
                rejected += 1

        return {"approved_candidates": approved, "rejected_count": rejected, "status": "storing"}

    async def store(self, state: dict) -> dict:
        approved = state.get("approved_candidates", [])
        user_id = state["user_id"]
        conversation_id = state.get("conversation_id", "")
        stored_ids: list[str] = []

        from backend.capture.extractor import CandidateMemory
        from backend.models.enums import MemoryType

        for a in approved:
            try:
                candidate = CandidateMemory(
                    type=MemoryType(a["type"]),
                    content=a["content"],
                    importance_hint=a.get("importance", 5),
                )
                mid = await self._writer.write_memory(
                    user_id=user_id,
                    candidate=candidate,
                    importance=a.get("importance", 5),
                    confidence=a.get("confidence", 0.8),
                    source={"conversation_id": conversation_id},
                )
                stored_ids.append(mid)
            except Exception as exc:
                logger.warning("Store failed for memory: %s", exc)

        return {"stored_memory_ids": stored_ids, "status": "completed"}


class ReadNodes:
    """Nodes for the read path: retrieve → compose → respond."""

    def __init__(
        self,
        retriever: HybridRetriever,
        composer: ContextComposer,
        llm_client: LLMClient,
    ):
        self._retriever = retriever
        self._composer = composer
        self._llm = llm_client

    async def retrieve(self, state: dict) -> dict:
        try:
            scored = await self._retriever.retrieve(
                user_id=state["user_id"],
                query=state["user_query"],
            )
            return {
                "retrieved_memories": [
                    {"content": s.memory.content, "type": s.memory.type.value,
                     "score": s.final_score, "id": s.memory.id}
                    for s in scored
                ],
                "retrieval_count": len(scored),
                "status": "composing",
            }
        except Exception as exc:
            logger.warning("Retrieval failed: %s", exc)
            return {"retrieved_memories": [], "retrieval_count": 0, "status": "composing"}

    async def compose(self, state: dict) -> dict:
        raw = state.get("retrieved_memories", [])
        if not raw:
            return {"memory_context": "", "status": "responding"}

        from backend.models.enums import MemoryType

        scored_list = []
        for r in raw:
            scored_list.append(ScoredMemory(
                memory=MemoryRecord(
                    id=r.get("id", ""),
                    user_id=state["user_id"],
                    type=MemoryType(r["type"]),
                    content=r["content"],
                ),
                final_score=r.get("score", 0.5),
            ))

        context = self._composer.compose(scored_list, query=state.get("user_query", ""))
        return {"memory_context": context, "status": "responding"}

    async def respond(self, state: dict) -> dict:
        config = get_model_config(TaskType.RESPONSE)
        memory_context = state.get("memory_context", "")

        prompt_template = load_prompt("response")
        system_prompt = prompt_template.replace("{memory_context}", memory_context or "No memories available.")

        try:
            response = await self._llm.complete(
                model=config.model_name,
                messages=[{"role": "user", "content": state["user_query"]}],
                system_prompt=system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_output_tokens,
            )
            text = response.content if isinstance(response.content, str) else str(response.content)
            return {"response_text": text, "status": "completed"}
        except Exception as exc:
            logger.warning("Response generation failed: %s", exc)
            return {
                "response_text": "I'm sorry, I couldn't generate a response right now. Please try again.",
                "status": "completed",
                "error_message": str(exc),
            }
