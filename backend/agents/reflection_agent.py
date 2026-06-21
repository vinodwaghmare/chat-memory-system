"""Reflection agent — consolidates old memories into cleaner summaries.

Runs off the request path (background job).
Archives originals after consolidation (preserves provenance — Invariant 4).
"""

from __future__ import annotations

import logging
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.agents.contracts import ConsolidatedMemory, ReflectionTask
from backend.models.enums import MemoryType
from backend.tools.model_router import TaskType

logger = logging.getLogger(__name__)

_REFLECTION_PROMPT = """You are a memory reflection agent. You consolidate multiple related raw memories
into fewer, cleaner summary memories.

Rules:
- Merge related facts into concise summaries.
- Preserve all important information — do not drop facts.
- Each consolidated memory should be self-contained.
- Output a JSON array of objects: {"type": "semantic|episodic|procedural", "content": "...", "importance": 1-10}

Raw memories to consolidate:"""


class ReflectionAgent(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "reflection"

    def _system_prompt(self, **kwargs: Any) -> str:
        return _REFLECTION_PROMPT

    def _task_type(self) -> TaskType:
        return TaskType.EVALUATION

    async def reflect(self, task: ReflectionTask) -> list[ConsolidatedMemory]:
        lines = []
        for i, (mid, content, mtype) in enumerate(
            zip(task.memory_ids, task.memory_contents, task.memory_types)
        ):
            lines.append(f"{i+1}. [{mtype}] {content}")

        user_content = "\n".join(lines)
        response = await self._call_llm(user_content)
        parsed = self._parse_json_output(response.content)

        if not parsed:
            return []

        items = parsed if isinstance(parsed, list) else parsed.get("memories", [])
        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                mem_type = item.get("type", "semantic")
                if mem_type not in {"semantic", "episodic", "procedural"}:
                    mem_type = "semantic"
                results.append(ConsolidatedMemory(
                    type=MemoryType(mem_type),
                    content=item["content"],
                    importance=max(1, min(10, int(item.get("importance", 7)))),
                    source_memory_ids=task.memory_ids,
                ))
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping malformed consolidation: %s", exc)

        return results
