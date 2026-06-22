"""Hybrid retriever — fans out vector + keyword + graph in parallel.

Merges results, deduplicates by memory_id, passes to ranking.
If any retrieval leg fails, continues with remaining (Invariant 3).
"""

from __future__ import annotations

import asyncio
import logging

from backend.core.llm_client import LLMClient
from backend.core.storage_backend import StorageBackend
from backend.models.memory import ScoredMemory
from backend.retrieve.graph_retriever import GraphRetriever
from backend.retrieve.ranking import RankingService, RawCandidate

logger = logging.getLogger(__name__)


class HybridRetriever:

    def __init__(
        self,
        store: StorageBackend,
        llm_client: LLMClient | None = None,
        graph_retriever: GraphRetriever | None = None,
        ranking_service: RankingService | None = None,
    ):
        self._store = store
        self._llm = llm_client
        self._graph = graph_retriever
        self._ranker = ranking_service or RankingService()

    async def retrieve(
        self,
        user_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[ScoredMemory]:
        vector_task = self._vector_search(user_id, query, top_k)
        keyword_task = self._keyword_search(user_id, query, top_k)

        results = await asyncio.gather(vector_task, keyword_task, return_exceptions=True)

        candidates: dict[str, RawCandidate] = {}

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Retrieval leg failed: %s", result)
                continue
            if isinstance(result, list):
                for candidate in result:
                    mid = candidate.memory.id
                    if mid not in candidates or candidate.semantic_score > candidates[mid].semantic_score:
                        candidates[mid] = candidate

        # Graph search (depends on initial results)
        if self._graph and candidates:
            try:
                memory_ids = list(candidates.keys())[:5]
                related = await self._graph.get_related(user_id, memory_ids)
                for mem, relation in related:
                    if mem.id not in candidates:
                        candidates[mem.id] = RawCandidate(
                            memory=mem,
                            semantic_score=0.3,
                            source="graph",
                        )
            except Exception as exc:
                logger.warning("Graph retrieval failed: %s", exc)

        # Fallback: if vector + keyword both returned empty, load recent memories
        if not candidates:
            try:
                recent = await self._store.list_memories(user_id, limit=top_k)
                for mem in recent:
                    candidates[mem.id] = RawCandidate(
                        memory=mem,
                        semantic_score=0.3,
                        source="fallback",
                    )
                if candidates:
                    logger.info("Fallback retrieval: loaded %d recent memories", len(candidates))
            except Exception as exc:
                logger.warning("Fallback retrieval failed: %s", exc)

        return self._ranker.rank(list(candidates.values()), top_k)

    async def _vector_search(self, user_id: str, query: str, top_k: int) -> list[RawCandidate]:
        if not self._llm:
            return []
        try:
            embeddings = await self._llm.embed([query])
            results = await self._store.search_vector(user_id, embeddings[0], top_k)
            return [
                RawCandidate(memory=mem, semantic_score=score, source="vector")
                for mem, score in results
            ]
        except Exception as exc:
            logger.warning("Vector search failed: %s", exc)
            return []

    async def _keyword_search(self, user_id: str, query: str, top_k: int) -> list[RawCandidate]:
        try:
            results = await self._store.search_keyword(user_id, query, top_k)
            return [
                RawCandidate(memory=mem, semantic_score=score * 0.8, source="keyword")
                for mem, score in results
            ]
        except Exception as exc:
            logger.warning("Keyword search failed: %s", exc)
            return []
