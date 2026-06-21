"""Abstract interface for workflow orchestration.

Enables swapping LangGraph for Temporal (or another engine) without
touching business logic. See ADR-003.

CONTRACT (Design by Contract):
  Precondition for run_write_path():
      workflow_id is a non-empty string.
      input_data contains keys: user_id, message, conversation_id.
  Postcondition for run_write_path():
      Returns WritePathResult with status COMPLETED or FAILED.
      On COMPLETED, stored_memory_ids lists every memory written.
  Precondition for run_read_path():
      input_data contains keys: user_id, query.
  Postcondition for run_read_path():
      Returns ReadPathResult with response_text set.
      On retrieval failure, response_text is still set (Invariant 3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.models.enums import WorkflowStatus


class WritePathResult(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    stored_memory_ids: list[str] = Field(default_factory=list)
    candidates_extracted: int = 0
    candidates_approved: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str = ""


class ReadPathResult(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    response_text: str = ""
    memories_used: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_scores: dict[str, float] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str = ""


class WorkflowEngine(ABC):

    @abstractmethod
    async def run_write_path(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
    ) -> WritePathResult:
        ...

    @abstractmethod
    async def run_read_path(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
    ) -> ReadPathResult:
        ...

    @abstractmethod
    async def get_state(self, workflow_id: str) -> dict[str, Any] | None:
        ...
