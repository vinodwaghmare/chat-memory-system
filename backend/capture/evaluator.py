"""Memory evaluator — the write gate.

Judges whether a candidate memory is worth storing. Sets importance
and confidence scores. Checks for duplicates against existing memories.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from backend.capture.extractor import CandidateMemory
from backend.core.llm_client import LLMClient
from backend.models.memory import MemoryRecord
from backend.prompts.registry import load_prompt
from backend.tools.model_router import TaskType, get_model_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationResult:
    """Internal contract — decision + scores."""
    keep: bool
    importance: int
    confidence: float
    reason: str


class MemoryEvaluator:

    def __init__(self, llm_client: LLMClient):
        self._client = llm_client

    async def evaluate(
        self,
        candidate: CandidateMemory,
        existing_memories: list[MemoryRecord] | None = None,
    ) -> EvaluationResult:
        config = get_model_config(TaskType.EVALUATION)

        existing_summary = "None"
        if existing_memories:
            lines = [f"- [{m.type.value}] {m.content}" for m in existing_memories[:20]]
            existing_summary = "\n".join(lines)

        prompt_template = load_prompt("evaluation")
        system_prompt = prompt_template.replace("{existing_memories}", existing_summary)

        candidate_text = f"[{candidate.type.value}] {candidate.content} (importance hint: {candidate.importance_hint})"

        response = await self._client.complete(
            model=config.model_name,
            messages=[{"role": "user", "content": candidate_text}],
            system_prompt=system_prompt,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
            response_format={"type": "json_object"},
        )

        return self._parse_result(response.content, candidate)

    def _parse_result(self, content: Any, candidate: CandidateMemory) -> EvaluationResult:
        if isinstance(content, dict):
            keep = bool(content.get("keep", False))
            importance = int(content.get("importance", candidate.importance_hint))
            importance = max(1, min(10, importance))
            confidence = float(content.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            reason = str(content.get("reason", ""))
            return EvaluationResult(
                keep=keep,
                importance=importance,
                confidence=confidence,
                reason=reason,
            )

        logger.warning("Evaluator returned non-dict, defaulting to keep with candidate hints")
        return EvaluationResult(
            keep=True,
            importance=candidate.importance_hint,
            confidence=0.5,
            reason="Evaluator response was not parseable; defaulting to keep.",
        )
