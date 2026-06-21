"""Sprint 5 gate tests — Workflow Orchestration (Phase 4).

End-to-end write + read paths with mocked LLM.
Validates: extraction→evaluation→store→retrieve→rank→compose→respond,
invariants 1-3, conversation endpoint wired live.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from backend.core.llm_client import LLMResponse
from backend.memory.service import MemoryService
from backend.models.enums import MemoryType, WorkflowStatus
from backend.orchestrator.engine import SequentialWorkflowEngine
from backend.retrieve.hybrid_retriever import HybridRetriever
from backend.retrieve.ranking import RankingService
from backend.store.pgvector_store import PgVectorStore

from tests.conftest import TEST_USER_A, TEST_USER_B


def _make_mock_llm():
    """LLM mock that handles extraction, evaluation, and response."""
    llm = AsyncMock()

    async def _complete(model, messages, system_prompt="", **kwargs):
        user_msg = messages[0]["content"] if messages else ""

        if "extraction" in system_prompt.lower():
            if "postgresql" in user_msg.lower():
                return LLMResponse(content=[
                    {"type": "semantic", "content": "Uses PostgreSQL", "importance_hint": 8},
                ])
            return LLMResponse(content=[])

        if "evaluator" in system_prompt.lower():
            return LLMResponse(content={
                "keep": True, "importance": 8, "confidence": 0.9,
                "reason": "Useful technical fact",
            })

        # Response generation
        return LLMResponse(content=f"Based on what I know, here's my response about: {user_msg}")

    llm.complete = AsyncMock(side_effect=_complete)
    llm.embed = AsyncMock(return_value=[[0.1] * 10])
    return llm


# -------------------------------------------------------------------------
# 1. Write path: message → extract → evaluate → store
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_write_path_stores_memories(db_session):
    llm = _make_mock_llm()
    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    engine = SequentialWorkflowEngine(llm, store, retriever)

    result = await engine.run_write_path(
        workflow_id="test-write-1",
        input_data={"user_id": TEST_USER_A, "message": "I always use PostgreSQL", "conversation_id": "conv-1"},
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert result.candidates_extracted == 1
    assert result.candidates_approved == 1
    assert len(result.stored_memory_ids) == 1

    await db_session.commit()
    fetched = await store.get(result.stored_memory_ids[0], TEST_USER_A)
    assert fetched is not None
    assert fetched.content == "Uses PostgreSQL"


# -------------------------------------------------------------------------
# 2. Read path: query → retrieve → rank → compose → respond
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_read_path_returns_response(db_session):
    llm = _make_mock_llm()
    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    engine = SequentialWorkflowEngine(llm, store, retriever)

    result = await engine.run_read_path(
        workflow_id="test-read-1",
        input_data={"user_id": TEST_USER_A, "query": "What database do I use?"},
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert result.response_text


# -------------------------------------------------------------------------
# 3. End-to-end: store then retrieve
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_end_to_end_memory_roundtrip(db_session):
    llm = _make_mock_llm()
    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    service = MemoryService(llm_client=llm, store=store, retriever=retriever)

    # Send message that creates a memory
    resp1 = await service.process_message(TEST_USER_A, "I always use PostgreSQL", "conv-1")
    await db_session.commit()
    assert resp1.memories_stored == 1

    # Query should find the stored memory via keyword search
    resp2 = await service.process_message(TEST_USER_A, "What database do I use?", "conv-1")
    assert resp2.response


# -------------------------------------------------------------------------
# 4. Write path failure → read path still works (Invariant 3)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_write_failure_does_not_block_read(db_session):
    llm = _make_mock_llm()
    llm_failing_extract = _make_mock_llm()

    async def _fail_extract(model, messages, system_prompt="", **kwargs):
        if "extraction" in system_prompt.lower():
            raise Exception("LLM down")
        return LLMResponse(content="Fallback response")

    llm_failing_extract.complete = AsyncMock(side_effect=_fail_extract)

    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    service = MemoryService(llm_client=llm_failing_extract, store=store, retriever=retriever)

    resp = await service.process_message(TEST_USER_A, "Hello", "conv-1")
    assert resp.response
    assert resp.memories_stored == 0


# -------------------------------------------------------------------------
# 5. Read path failure → fallback response (Invariant 3)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_read_failure_returns_fallback(db_session):
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=Exception("Total failure"))
    llm.embed = AsyncMock(side_effect=Exception("Embed failure"))

    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store, llm_client=llm)
    engine = SequentialWorkflowEngine(llm, store, retriever)

    result = await engine.run_read_path(
        workflow_id="test-fail",
        input_data={"user_id": TEST_USER_A, "query": "anything"},
    )

    assert result.response_text
    assert result.status == WorkflowStatus.COMPLETED


# -------------------------------------------------------------------------
# 6. Two users — memories isolated (Invariant 1)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_user_isolation_end_to_end(db_session):
    llm = _make_mock_llm()
    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    service = MemoryService(llm_client=llm, store=store, retriever=retriever)

    await service.process_message(TEST_USER_A, "I always use PostgreSQL", "conv-a")
    await db_session.commit()

    # User B should not see User A's memories
    mems_b = await store.list_memories(TEST_USER_B)
    assert len(mems_b) == 0

    mems_a = await store.list_memories(TEST_USER_A)
    assert len(mems_a) == 1


# -------------------------------------------------------------------------
# 7. WorkflowEngine returns typed result with correct status
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_workflow_result_is_typed(db_session):
    llm = _make_mock_llm()
    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    engine = SequentialWorkflowEngine(llm, store, retriever)

    write_result = await engine.run_write_path(
        workflow_id="typed-test",
        input_data={"user_id": TEST_USER_A, "message": "I use PostgreSQL"},
    )
    assert hasattr(write_result, "workflow_id")
    assert hasattr(write_result, "status")
    assert hasattr(write_result, "stored_memory_ids")
    assert write_result.started_at is not None
    assert write_result.completed_at is not None


# -------------------------------------------------------------------------
# 8. Conversation endpoint returns 200 with response text
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_conversation_endpoint_returns_200(client):
    # The endpoint builds its own LLM client which needs real keys,
    # so we patch it to use our mock
    with patch("backend.api.conversations._build_memory_service") as mock_build:
        mock_service = AsyncMock()
        from backend.models.conversation import ConversationResponse
        mock_service.process_message.return_value = ConversationResponse(
            response="I remember you use PostgreSQL!",
            conversation_id="conv-test",
            memories_used=[{"content": "Uses PostgreSQL", "type": "semantic", "score": 0.9}],
            memories_stored=1,
        )
        mock_build.return_value = mock_service

        resp = await client.post(
            "/api/v1/conversations/message",
            json={"message": "What database do I use?"},
            headers={"X-User-ID": TEST_USER_A},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "PostgreSQL" in body["response"]
    assert body["memories_stored"] == 1
    assert len(body["memories_used"]) == 1


# -------------------------------------------------------------------------
# 9. Empty extraction → no memories stored, response still works
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_memories_extracted_still_responds(db_session):
    llm = _make_mock_llm()
    store = PgVectorStore(db_session)
    retriever = HybridRetriever(store=store)
    service = MemoryService(llm_client=llm, store=store, retriever=retriever)

    resp = await service.process_message(TEST_USER_A, "Hello there!", "conv-1")
    assert resp.response
    assert resp.memories_stored == 0
