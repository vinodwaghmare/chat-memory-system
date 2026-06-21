"""Context composer — formats top-k memories into a text block for the LLM.

Groups by memory type. Respects a token budget.
"""

from __future__ import annotations

from backend.models.enums import MemoryType
from backend.models.memory import ScoredMemory

CHARS_PER_TOKEN = 4
DEFAULT_TOKEN_BUDGET = 2000

TYPE_ORDER = [MemoryType.PROCEDURAL, MemoryType.SEMANTIC, MemoryType.EPISODIC]
TYPE_LABELS = {
    MemoryType.PROCEDURAL: "Preferences",
    MemoryType.SEMANTIC: "Facts",
    MemoryType.EPISODIC: "Experiences",
}


class ContextComposer:

    def compose(
        self,
        memories: list[ScoredMemory],
        query: str = "",
        token_budget: int = DEFAULT_TOKEN_BUDGET,
    ) -> str:
        if not memories:
            return ""

        grouped: dict[MemoryType, list[str]] = {t: [] for t in TYPE_ORDER}
        for sm in memories:
            mt = sm.memory.type
            if mt in grouped:
                grouped[mt].append(sm.memory.content)

        lines: list[str] = []
        for mt in TYPE_ORDER:
            items = grouped.get(mt, [])
            if not items:
                continue
            label = TYPE_LABELS.get(mt, mt.value)
            lines.append(f"{label}:")
            for item in items:
                lines.append(f"  - {item}")

        text = "\n".join(lines)

        max_chars = token_budget * CHARS_PER_TOKEN
        if len(text) > max_chars:
            text = text[:max_chars] + "\n  [truncated]"

        return text
