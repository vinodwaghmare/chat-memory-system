"""Memory extractor — reads a conversation turn and emits candidate memories.

Uses the extraction prompt template and the configured LLM.
Output guardrail: validates JSON, skips malformed candidates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.core.llm_client import LLMClient
from backend.models.enums import MemoryType
from backend.prompts.registry import load_prompt
from backend.tools.model_router import TaskType, get_model_config

logger = logging.getLogger(__name__)

_VALID_TYPES = {t.value for t in MemoryType}


@dataclass(frozen=True)
class CandidateMemory:
    """Internal contract — never leaves the process."""
    type: MemoryType
    content: str
    importance_hint: int = 5


class MemoryExtractor:

    def __init__(self, llm_client: LLMClient):
        self._client = llm_client

    async def extract(self, user_message: str) -> list[CandidateMemory]:
        config = get_model_config(TaskType.EXTRACTION)
        system_prompt = load_prompt("extraction")

        response = await self._client.complete(
            model=config.model_name,
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
            response_format={"type": "json_object"},
        )

        logger.info("Extraction raw content type=%s value=%s", type(response.content).__name__, str(response.content)[:500])
        candidates = self._parse_candidates(response.content)
        logger.info("Extraction produced %d candidates", len(candidates))
        return candidates

    def _parse_candidates(self, content: Any) -> list[CandidateMemory]:
        if content is None:
            return []

        items: list[dict] = []
        if isinstance(content, list):
            items = content
        elif isinstance(content, dict):
            if "memories" in content:
                items = content["memories"]
            elif "candidates" in content:
                items = content["candidates"]
            elif "type" in content and "content" in content:
                items = [content]
            else:
                items = [content]
            if not isinstance(items, list):
                items = [items]
        elif isinstance(content, str):
            return []
        else:
            return []

        candidates = []
        for item in items:
            try:
                if not isinstance(item, dict):
                    continue
                mem_type = item.get("type", "")
                if mem_type not in _VALID_TYPES:
                    logger.warning("Skipping candidate with invalid type: %s", mem_type)
                    continue
                content_text = item.get("content", "").strip()
                if not content_text:
                    continue
                importance = int(item.get("importance_hint", 5))
                importance = max(1, min(10, importance))
                candidates.append(CandidateMemory(
                    type=MemoryType(mem_type),
                    content=content_text,
                    importance_hint=importance,
                ))
            except (ValueError, TypeError) as exc:
                logger.warning("Skipping malformed candidate: %s", exc)
                continue

        return candidates
