"""Typed contracts for memory system agents.

All frozen dataclasses — immutable, in-process only.
Each field documents its source and consumer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from backend.models.enums import MemoryType


@dataclass(frozen=True)
class ExtractionTask:
    """Input contract for the extraction agent.
    Source: conversation endpoint. Consumer: MemoryExtractor.
    """
    user_message: str
    user_id: str
    existing_memory_count: int = 0


@dataclass(frozen=True)
class EvaluationTask:
    """Input contract for the evaluation agent.
    Source: MemoryExtractor output. Consumer: MemoryEvaluator.
    """
    candidate_type: MemoryType
    candidate_content: str
    importance_hint: int
    user_id: str
    existing_summaries: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReflectionTask:
    """Input contract for the reflection agent.
    Source: reflection job. Consumer: ReflectionAgent.
    """
    user_id: str
    memory_ids: tuple[str, ...]
    memory_contents: tuple[str, ...]
    memory_types: tuple[str, ...]


@dataclass(frozen=True)
class ConsolidatedMemory:
    """Output of the reflection agent — a cleaner, merged memory."""
    type: MemoryType
    content: str
    importance: int
    source_memory_ids: tuple[str, ...]
