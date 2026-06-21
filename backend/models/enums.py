from __future__ import annotations

from enum import Enum


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryTier(str, Enum):
    WORKING = "working"
    SESSION = "session"
    LONG_TERM = "long_term"
    KNOWLEDGE = "knowledge"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class WorkflowStatus(str, Enum):
    RECEIVED = "received"
    EXTRACTING = "extracting"
    EVALUATING = "evaluating"
    STORING = "storing"
    RETRIEVING = "retrieving"
    COMPOSING = "composing"
    COMPLETED = "completed"
    FAILED = "failed"


class RetrievalStrategy(str, Enum):
    VECTOR = "vector"
    KEYWORD = "keyword"
    GRAPH = "graph"
    HYBRID = "hybrid"
