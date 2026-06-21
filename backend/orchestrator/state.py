"""Typed state definitions for LangGraph workflows.

Every field documents who READS and who WRITES it.
"""

from __future__ import annotations

from typing import Any, TypedDict

from backend.models.enums import WorkflowStatus


class WritePathState(TypedDict, total=False):
    # Identity — set at workflow start, never changes
    workflow_id: str                      # write: caller | read: all nodes
    user_id: str                          # write: caller | read: all nodes
    conversation_id: str                  # write: caller | read: store node

    # Input — set at workflow start
    user_message: str                     # write: caller | read: extract node

    # Extraction — written by extract node
    candidate_memories: list[dict]        # write: extract | read: evaluate
    extraction_error: str                 # write: extract | read: caller

    # Evaluation — written by evaluate node
    approved_candidates: list[dict]       # write: evaluate | read: store
    rejected_count: int                   # write: evaluate | read: caller

    # Storage — written by store node
    stored_memory_ids: list[str]          # write: store | read: caller

    # Metadata
    status: str                           # write: all nodes | read: caller
    error_message: str                    # write: any failing node


class ReadPathState(TypedDict, total=False):
    # Identity
    workflow_id: str                      # write: caller | read: all nodes
    user_id: str                          # write: caller | read: all nodes

    # Input
    user_query: str                       # write: caller | read: retrieve, respond

    # Retrieval — written by retrieve node
    retrieved_memories: list[dict]        # write: retrieve | read: compose
    retrieval_count: int                  # write: retrieve | read: caller

    # Composition — written by compose node
    memory_context: str                   # write: compose | read: respond

    # Response — written by respond node
    response_text: str                    # write: respond | read: caller

    # Metadata
    status: str
    error_message: str
