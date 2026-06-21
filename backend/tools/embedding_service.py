"""Embedding service — wraps LLMClient.embed() with batching."""

from __future__ import annotations

from backend.core.llm_client import LLMClient
from backend.config.settings import get_settings


class EmbeddingService:

    def __init__(self, llm_client: LLMClient):
        self._client = llm_client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        cfg = get_settings()
        return await self._client.embed(
            texts,
            model=cfg.openai_embedding_model,
            dimensions=cfg.openai_embedding_dimensions,
        )

    async def embed_single(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
