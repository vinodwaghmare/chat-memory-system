"""Ranking service — scores and orders candidate memories.

Final Score = semantic_weight * semantic
            + recency_weight  * recency
            + frequency_weight * frequency
            + importance_weight * importance

Weights configurable via Settings.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from dataclasses import dataclass

from backend.config.settings import get_settings
from backend.models.memory import MemoryRecord, ScoredMemory


@dataclass
class RawCandidate:
    memory: MemoryRecord
    semantic_score: float = 0.0
    source: str = "unknown"


class RankingService:

    def rank(self, candidates: list[RawCandidate], top_k: int | None = None) -> list[ScoredMemory]:
        cfg = get_settings()
        top_k = top_k or cfg.retrieval_top_k
        now = datetime.now(timezone.utc)

        scored = []
        for c in candidates:
            recency = self._recency_score(c.memory, now)
            frequency = self._frequency_score(c.memory)
            importance = self._importance_score(c.memory)

            final = (
                cfg.semantic_weight * c.semantic_score
                + cfg.recency_weight * recency
                + cfg.frequency_weight * frequency
                + cfg.importance_weight * importance
            )

            scored.append(ScoredMemory(
                memory=c.memory,
                final_score=round(final, 4),
                score_breakdown={
                    "semantic": round(c.semantic_score, 4),
                    "recency": round(recency, 4),
                    "frequency": round(frequency, 4),
                    "importance": round(importance, 4),
                    "source": c.source,
                },
            ))

        scored.sort(key=lambda s: s.final_score, reverse=True)
        return scored[:top_k]

    def _recency_score(self, memory: MemoryRecord, now: datetime) -> float:
        if not memory.updated_at:
            return 0.5
        updated = memory.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        days_ago = (now - updated).total_seconds() / 86400
        return math.exp(-0.05 * days_ago)

    def _frequency_score(self, memory: MemoryRecord) -> float:
        count = memory.reinforcement_count
        return min(count / 10.0, 1.0)

    def _importance_score(self, memory: MemoryRecord) -> float:
        return memory.importance / 10.0
