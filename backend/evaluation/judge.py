"""LLM-as-judge for memory extraction correctness.

Checks: are extracted memories factually present in the conversation?
Are important facts missed? Is there hallucination?
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.core.llm_client import LLMClient
from backend.tools.model_router import TaskType, get_model_config

logger = logging.getLogger(__name__)

_JUDGE_PROMPT = """You are a memory extraction quality judge. Given a conversation and the memories
that were extracted from it, evaluate the extraction quality.

Check:
1. Are all extracted memories factually present in the conversation? (correctness)
2. Were any important facts missed? (completeness)
3. Were any facts hallucinated (not in the conversation)? (hallucination)

Output a JSON object:
{
  "correctness_score": 0.0-1.0,
  "missed_facts": ["fact1", ...],
  "hallucinated": ["memory1", ...],
  "notes": "brief assessment"
}

Conversation:
{conversation}

Extracted memories:
{memories}"""


@dataclass(frozen=True)
class JudgeResult:
    correctness_score: float
    missed_facts: tuple[str, ...]
    hallucinated: tuple[str, ...]
    notes: str = ""


class MemoryJudge:

    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    async def judge_extraction(
        self,
        conversation: str,
        extracted_memories: list[str],
    ) -> JudgeResult:
        config = get_model_config(TaskType.EVALUATION)
        prompt = _JUDGE_PROMPT.replace("{conversation}", conversation)
        prompt = prompt.replace("{memories}", "\n".join(f"- {m}" for m in extracted_memories))

        response = await self._llm.complete(
            model=config.model_name,
            messages=[{"role": "user", "content": "Evaluate the extraction quality."}],
            system_prompt=prompt,
            temperature=0.0,
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        return self._parse(response.content)

    def _parse(self, content: Any) -> JudgeResult:
        if isinstance(content, dict):
            return JudgeResult(
                correctness_score=float(content.get("correctness_score", 0.5)),
                missed_facts=tuple(content.get("missed_facts", [])),
                hallucinated=tuple(content.get("hallucinated", [])),
                notes=str(content.get("notes", "")),
            )
        return JudgeResult(correctness_score=0.5, missed_facts=(), hallucinated=(), notes="Unparseable response")
