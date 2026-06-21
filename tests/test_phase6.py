"""Sprint 4 gate tests — Memory Architecture (Phase 6).

Validates: pgvector store, keyword search, ranking, hybrid retriever,
graph retriever, context composer, session store, invariants 1-3.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest

from backend.context.composer import ContextComposer
from backend.models.enums import MemoryType
from backend.models.memory import MemoryRecord, ScoredMemory
from backend.retrieve.ranking import RankingService, RawCandidate
from backend.store.pgvector_store import PgVectorStore

from tests.conftest import TEST_USER_A, TEST_USER_B


def _make_record(
    user_id: str = TEST_USER_A,
    content: str = "Test memory",
    mem_type: MemoryType = MemoryType.SEMANTIC,
    importance: int = 5,
    reinforcement_count: int = 0,
    updated_at: datetime | None = None,
) -> MemoryRecord:
    return MemoryRecord(
        user_id=user_id,
        type=mem_type,
        content=content,
        importance=importance,
        confidence=0.8,
        reinforcement_count=reinforcement_count,
        updated_at=updated_at or datetime.now(timezone.utc),
    )


# -------------------------------------------------------------------------
# PgVectorStore tests (using SQLite for keyword search)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_store_and_retrieve(db_session):
    store = PgVectorStore(db_session)
    record = _make_record(content="Uses PostgreSQL")
    memory_id = await store.store(record)
    await db_session.commit()

    fetched = await store.get(memory_id, TEST_USER_A)
    assert fetched is not None
    assert fetched.content == "Uses PostgreSQL"


@pytest.mark.asyncio
async def test_keyword_search_returns_match(db_session):
    store = PgVectorStore(db_session)
    await store.store(_make_record(content="Uses PostgreSQL for all projects"))
    await store.store(_make_record(content="Prefers short answers"))
    await db_session.commit()

    results = await store.search_keyword(TEST_USER_A, "PostgreSQL")
    assert len(results) == 1
    assert results[0][0].content == "Uses PostgreSQL for all projects"


@pytest.mark.asyncio
async def test_user_isolation_in_store(db_session):
    """Invariant 1: user B cannot see user A's memories."""
    store = PgVectorStore(db_session)
    await store.store(_make_record(user_id=TEST_USER_A, content="Secret A"))
    await store.store(_make_record(user_id=TEST_USER_B, content="Secret B"))
    await db_session.commit()

    results_a = await store.search_keyword(TEST_USER_A, "Secret")
    results_b = await store.search_keyword(TEST_USER_B, "Secret")

    assert len(results_a) == 1
    assert results_a[0][0].content == "Secret A"
    assert len(results_b) == 1
    assert results_b[0][0].content == "Secret B"


@pytest.mark.asyncio
async def test_deleted_excluded_from_search(db_session):
    """Invariant 2: deleted memories never appear in search."""
    store = PgVectorStore(db_session)
    mid = await store.store(_make_record(content="Will be deleted"))
    await db_session.commit()

    await store.soft_delete(mid, TEST_USER_A)
    await db_session.commit()

    results = await store.search_keyword(TEST_USER_A, "deleted")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_archive_below_threshold(db_session):
    store = PgVectorStore(db_session)
    await store.store(_make_record(content="Low weight memory"))
    await db_session.commit()

    # Update weight to below threshold
    mems = await store.list_memories(TEST_USER_A)
    await store.update_weight(mems[0].id, 0.05)
    await db_session.commit()

    archived = await store.archive_below_threshold(TEST_USER_A, 0.1)
    await db_session.commit()
    assert archived == 1

    remaining = await store.list_memories(TEST_USER_A, include_archived=False)
    assert len(remaining) == 0


# -------------------------------------------------------------------------
# Ranking tests
# -------------------------------------------------------------------------
def test_ranking_high_importance_recent_wins():
    ranker = RankingService()
    now = datetime.now(timezone.utc)

    candidates = [
        RawCandidate(
            memory=_make_record(content="Low importance old", importance=2, updated_at=now - timedelta(days=30)),
            semantic_score=0.5,
        ),
        RawCandidate(
            memory=_make_record(content="High importance recent", importance=9, updated_at=now, reinforcement_count=5),
            semantic_score=0.8,
        ),
    ]

    scored = ranker.rank(candidates, top_k=2)
    assert scored[0].memory.content == "High importance recent"
    assert scored[0].final_score > scored[1].final_score


def test_ranking_respects_weights():
    ranker = RankingService()
    now = datetime.now(timezone.utc)

    c1 = RawCandidate(
        memory=_make_record(content="Semantic winner", importance=3, updated_at=now),
        semantic_score=1.0,
    )
    c2 = RawCandidate(
        memory=_make_record(content="Importance winner", importance=10, updated_at=now),
        semantic_score=0.0,
    )

    scored = ranker.rank([c1, c2], top_k=2)
    # semantic_weight=0.4, importance_weight=0.2 → semantic winner should lead
    assert scored[0].memory.content == "Semantic winner"


def test_ranking_score_breakdown():
    ranker = RankingService()
    now = datetime.now(timezone.utc)

    candidates = [RawCandidate(
        memory=_make_record(content="Test", importance=8, updated_at=now, reinforcement_count=3),
        semantic_score=0.7,
        source="vector",
    )]

    scored = ranker.rank(candidates)
    assert "semantic" in scored[0].score_breakdown
    assert "recency" in scored[0].score_breakdown
    assert "frequency" in scored[0].score_breakdown
    assert "importance" in scored[0].score_breakdown
    assert scored[0].score_breakdown["source"] == "vector"


# -------------------------------------------------------------------------
# Hybrid retriever tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_hybrid_merges_without_duplicates(db_session):
    from backend.retrieve.hybrid_retriever import HybridRetriever

    store = PgVectorStore(db_session)
    await store.store(_make_record(content="PostgreSQL database user"))
    await store.store(_make_record(content="Prefers functional programming"))
    await db_session.commit()

    retriever = HybridRetriever(store=store)
    results = await retriever.retrieve(TEST_USER_A, "PostgreSQL")

    assert len(results) >= 1
    ids = [r.memory.id for r in results]
    assert len(ids) == len(set(ids)), "No duplicates"


@pytest.mark.asyncio
async def test_retrieval_failure_returns_empty(db_session):
    """Invariant 3: retrieval failure never blocks, returns empty."""
    from backend.retrieve.hybrid_retriever import HybridRetriever

    failing_store = AsyncMock()
    failing_store.search_keyword.side_effect = Exception("DB down")
    failing_store.search_vector.side_effect = Exception("Embedding down")

    retriever = HybridRetriever(store=failing_store)
    results = await retriever.retrieve(TEST_USER_A, "anything")

    assert results == []


# -------------------------------------------------------------------------
# Graph retriever tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_graph_retriever_follows_edges(db_session):
    from backend.database.models import MemoryEdgeORM
    from backend.retrieve.graph_retriever import GraphRetriever

    store = PgVectorStore(db_session)
    mid1 = await store.store(_make_record(content="SecondBrainLabs startup"))
    mid2 = await store.store(_make_record(content="ML course project"))
    await db_session.commit()

    import uuid as uuid_mod
    edge = MemoryEdgeORM(
        from_memory_id=uuid_mod.UUID(mid1),
        to_memory_id=uuid_mod.UUID(mid2),
        relation="related_project",
        user_id=uuid_mod.UUID(TEST_USER_A),
    )
    db_session.add(edge)
    await db_session.commit()

    graph = GraphRetriever(db_session)
    related = await graph.get_related(TEST_USER_A, [mid1])

    assert len(related) == 1
    assert related[0][0].content == "ML course project"
    assert related[0][1] == "related_project"


# -------------------------------------------------------------------------
# Context composer tests
# -------------------------------------------------------------------------
def test_composer_formats_by_type():
    composer = ContextComposer()
    memories = [
        ScoredMemory(
            memory=_make_record(content="Prefers short answers", mem_type=MemoryType.PROCEDURAL),
            final_score=0.9,
        ),
        ScoredMemory(
            memory=_make_record(content="Uses PostgreSQL", mem_type=MemoryType.SEMANTIC),
            final_score=0.8,
        ),
        ScoredMemory(
            memory=_make_record(content="Visited Kashmir", mem_type=MemoryType.EPISODIC),
            final_score=0.5,
        ),
    ]

    text = composer.compose(memories)
    assert "Preferences:" in text
    assert "Facts:" in text
    assert "Experiences:" in text
    pref_pos = text.index("Preferences:")
    facts_pos = text.index("Facts:")
    assert pref_pos < facts_pos


def test_composer_respects_token_budget():
    composer = ContextComposer()
    memories = [
        ScoredMemory(
            memory=_make_record(content="A" * 5000, mem_type=MemoryType.SEMANTIC),
            final_score=0.9,
        ),
    ]

    text = composer.compose(memories, token_budget=100)
    assert len(text) <= 100 * 4 + 50  # budget + truncation marker
    assert "[truncated]" in text


def test_composer_empty_returns_empty():
    composer = ContextComposer()
    assert composer.compose([]) == ""


# -------------------------------------------------------------------------
# Vector search fallback (Invariant 3)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vector_failure_returns_keyword_only(db_session):
    """If vector search fails, keyword results still returned."""
    from backend.retrieve.hybrid_retriever import HybridRetriever

    store = PgVectorStore(db_session)
    await store.store(_make_record(content="PostgreSQL expertise"))
    await db_session.commit()

    failing_llm = AsyncMock()
    failing_llm.embed.side_effect = Exception("Embedding service down")

    retriever = HybridRetriever(store=store, llm_client=failing_llm)
    results = await retriever.retrieve(TEST_USER_A, "PostgreSQL")

    assert len(results) >= 1
    assert results[0].memory.content == "PostgreSQL expertise"
