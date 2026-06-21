"""Sprint 7 gate tests — Agent Contracts & Background Jobs (Phase 8).

Validates: frozen contracts, reflection agent, decay job, reinforcement.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from backend.agents.contracts import (
    ConsolidatedMemory,
    EvaluationTask,
    ExtractionTask,
    ReflectionTask,
)
from backend.agents.reflection_agent import ReflectionAgent
from backend.core.llm_client import LLMResponse
from backend.database.repository import MemoryRepository
from backend.jobs.decay_job import DecayJob
from backend.models.enums import MemoryType

from tests.conftest import TEST_USER_A


# -------------------------------------------------------------------------
# Contract immutability
# -------------------------------------------------------------------------
def test_extraction_task_is_frozen():
    t = ExtractionTask(user_message="hello", user_id="u1")
    with pytest.raises(AttributeError):
        t.user_message = "changed"


def test_evaluation_task_is_frozen():
    t = EvaluationTask(
        candidate_type=MemoryType.SEMANTIC,
        candidate_content="test",
        importance_hint=5,
        user_id="u1",
    )
    with pytest.raises(AttributeError):
        t.candidate_content = "changed"


def test_reflection_task_is_frozen():
    t = ReflectionTask(
        user_id="u1",
        memory_ids=("id1",),
        memory_contents=("content1",),
        memory_types=("semantic",),
    )
    with pytest.raises(AttributeError):
        t.user_id = "changed"


def test_consolidated_memory_is_frozen():
    c = ConsolidatedMemory(
        type=MemoryType.SEMANTIC,
        content="summary",
        importance=8,
        source_memory_ids=("id1", "id2"),
    )
    with pytest.raises(AttributeError):
        c.content = "changed"


# -------------------------------------------------------------------------
# Reflection agent
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reflection_consolidates_memories():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content=[
        {"type": "semantic", "content": "User is a Python developer who uses PostgreSQL", "importance": 8},
    ])

    agent = ReflectionAgent(llm)
    task = ReflectionTask(
        user_id="u1",
        memory_ids=("id1", "id2", "id3"),
        memory_contents=("Knows Python", "Uses PostgreSQL", "Codes daily"),
        memory_types=("semantic", "semantic", "procedural"),
    )

    results = await agent.reflect(task)

    assert len(results) == 1
    assert "Python" in results[0].content
    assert results[0].importance == 8
    assert results[0].source_memory_ids == ("id1", "id2", "id3")


@pytest.mark.asyncio
async def test_reflection_handles_malformed_response():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content="not json at all")

    agent = ReflectionAgent(llm)
    task = ReflectionTask(
        user_id="u1",
        memory_ids=("id1",),
        memory_contents=("test",),
        memory_types=("semantic",),
    )

    results = await agent.reflect(task)
    assert results == []


@pytest.mark.asyncio
async def test_consolidated_has_higher_importance():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content=[
        {"type": "semantic", "content": "Expert Python developer", "importance": 9},
    ])

    agent = ReflectionAgent(llm)
    task = ReflectionTask(
        user_id="u1",
        memory_ids=("id1", "id2"),
        memory_contents=("Knows Python", "Writes Python daily"),
        memory_types=("semantic", "procedural"),
    )

    results = await agent.reflect(task)
    assert results[0].importance >= 8


# -------------------------------------------------------------------------
# Decay job
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_decay_reduces_weights(db_session):
    repo = MemoryRepository(db_session)
    await repo.create_memory(TEST_USER_A, MemoryType.SEMANTIC, "Fact 1", importance=5)
    await repo.create_memory(TEST_USER_A, MemoryType.SEMANTIC, "Fact 2", importance=5)
    await db_session.commit()

    job = DecayJob(db_session)
    result = await job.run()
    await db_session.commit()

    assert result["decayed"] == 2

    memories = await repo.list_memories(TEST_USER_A)
    for m in memories:
        assert m.weight < 1.0


@pytest.mark.asyncio
async def test_decay_archives_below_threshold(db_session):
    repo = MemoryRepository(db_session)
    await repo.create_memory(TEST_USER_A, MemoryType.SEMANTIC, "Will decay away", importance=1)
    await db_session.commit()

    # Set weight very low
    mems = await repo.list_memories(TEST_USER_A)
    await repo.update_weight(mems[0].id, 0.05)
    await db_session.commit()

    job = DecayJob(db_session)
    result = await job.run()
    await db_session.commit()

    assert result["archived"] >= 1

    remaining = await repo.list_memories(TEST_USER_A, include_archived=False)
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_reinforcement_increases_weight(db_session):
    repo = MemoryRepository(db_session)
    record = await repo.create_memory(TEST_USER_A, MemoryType.SEMANTIC, "Important fact", importance=8)
    await db_session.commit()

    original_weight = record.weight

    await repo.reinforce(record.id)
    await db_session.commit()

    mems = await repo.list_memories(TEST_USER_A)
    assert mems[0].weight > original_weight
    assert mems[0].reinforcement_count == 1
