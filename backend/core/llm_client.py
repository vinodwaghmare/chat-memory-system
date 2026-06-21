"""Abstract interface for LLM interactions.

Enables routing between OpenAI and Anthropic (and future providers)
without changing call sites. See ADR-004.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: Any
    input_tokens: int = 0
    output_tokens: int = 0
    model_used: str = ""
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0


class LLMClient(ABC):

    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        response_format: dict[str, str] | None = None,
    ) -> LLMResponse:
        """Send a completion request. Returns structured LLMResponse."""
        ...

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model: str = "",
        dimensions: int = 1536,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...
