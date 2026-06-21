"""Sprint 9 gate tests — Frontend (Phase 2).

Validates: API client functions construct correct URLs,
frontend build succeeds (verified externally), API contract compatibility.
"""

from __future__ import annotations

import pytest

from tests.conftest import TEST_USER_A


HEADERS_A = {"X-User-ID": TEST_USER_A}


# -------------------------------------------------------------------------
# API contract tests — ensure frontend-expected shapes match backend
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_memories_list_returns_array(client):
    resp = await client.get("/api/v1/memories", headers=HEADERS_A)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_memory_create_returns_expected_fields(client):
    resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Test from frontend"},
        headers=HEADERS_A,
    )
    body = resp.json()
    assert resp.status_code == 201
    required_fields = {"id", "user_id", "type", "content", "importance", "confidence", "weight"}
    assert required_fields.issubset(body.keys())


@pytest.mark.asyncio
async def test_memory_detail_returns_expected_fields(client):
    create = await client.post(
        "/api/v1/memories",
        json={"type": "procedural", "content": "Prefers dark mode"},
        headers=HEADERS_A,
    )
    mid = create.json()["id"]

    resp = await client.get(f"/api/v1/memories/{mid}", headers=HEADERS_A)
    body = resp.json()
    assert resp.status_code == 200
    assert body["type"] == "procedural"
    assert body["content"] == "Prefers dark mode"
    assert "source" in body
    assert "weight" in body
    assert "reinforcement_count" in body


@pytest.mark.asyncio
async def test_memory_update_returns_updated_record(client):
    create = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Old content"},
        headers=HEADERS_A,
    )
    mid = create.json()["id"]

    resp = await client.put(
        f"/api/v1/memories/{mid}",
        json={"content": "New content", "importance": 9},
        headers=HEADERS_A,
    )
    body = resp.json()
    assert resp.status_code == 200
    assert body["content"] == "New content"
    assert body["importance"] == 9


@pytest.mark.asyncio
async def test_memory_delete_returns_status(client):
    create = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Delete me"},
        headers=HEADERS_A,
    )
    mid = create.json()["id"]

    resp = await client.delete(f"/api/v1/memories/{mid}", headers=HEADERS_A)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_conversation_returns_expected_fields(client):
    from unittest.mock import AsyncMock, patch
    from backend.models.conversation import ConversationResponse

    with patch("backend.api.conversations._build_memory_service") as mock_build:
        mock_svc = AsyncMock()
        mock_svc.process_message.return_value = ConversationResponse(
            response="Hello!",
            conversation_id="test-conv",
            memories_used=[],
            memories_stored=0,
        )
        mock_build.return_value = mock_svc

        resp = await client.post(
            "/api/v1/conversations/message",
            json={"message": "Hi there"},
            headers=HEADERS_A,
        )

    body = resp.json()
    assert resp.status_code == 200
    required = {"response", "conversation_id", "memories_used", "memories_stored"}
    assert required.issubset(body.keys())


@pytest.mark.asyncio
async def test_health_live_returns_expected_shape(client):
    resp = await client.get("/health/live")
    body = resp.json()
    assert resp.status_code == 200
    assert "status" in body
    assert "version" in body
