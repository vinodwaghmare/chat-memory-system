from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime | None = None


class ConversationTurn(BaseModel):
    user_message: str
    assistant_response: str | None = None
    conversation_id: str = ""
    turn_number: int = 0


class ConversationRequest(BaseModel):
    message: str
    conversation_id: str = ""


class ConversationResponse(BaseModel):
    response: str
    conversation_id: str
    memories_used: list[dict] = Field(default_factory=list)
    memories_stored: int = 0
