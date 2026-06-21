"""Sprint 2 gate tests — Backend & API (Phase 3).

Validates: CRUD endpoints, user isolation (Invariant 1),
deleted exclusion (Invariant 2), audit logging, conversation placeholder.
"""

from __future__ import annotations

import pytest

from tests.conftest import TEST_USER_A, TEST_USER_B

HEADERS_A = {"X-User-ID": TEST_USER_A}
HEADERS_B = {"X-User-ID": TEST_USER_B}


# -------------------------------------------------------------------------
# 1. POST /memories — create a memory
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_memory(client):
    resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Uses PostgreSQL", "importance": 8},
        headers=HEADERS_A,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["content"] == "Uses PostgreSQL"
    assert body["type"] == "semantic"
    assert body["importance"] == 8
    assert body["id"]  # UUID assigned


# -------------------------------------------------------------------------
# 2. GET /memories — empty DB returns empty list
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_memories_empty(client):
    resp = await client.get("/api/v1/memories", headers=HEADERS_A)
    assert resp.status_code == 200
    assert resp.json() == []


# -------------------------------------------------------------------------
# 3. GET /memories — with seeded data returns list
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_memories_with_data(client):
    await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Knows Python"},
        headers=HEADERS_A,
    )
    await client.post(
        "/api/v1/memories",
        json={"type": "procedural", "content": "Prefers short answers"},
        headers=HEADERS_A,
    )
    resp = await client.get("/api/v1/memories", headers=HEADERS_A)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# -------------------------------------------------------------------------
# 4. GET /memories?type=semantic — filter by type
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_memories_filter_type(client):
    await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Knows Python"},
        headers=HEADERS_A,
    )
    await client.post(
        "/api/v1/memories",
        json={"type": "procedural", "content": "Prefers short answers"},
        headers=HEADERS_A,
    )
    resp = await client.get("/api/v1/memories?type=semantic", headers=HEADERS_A)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["type"] == "semantic"


# -------------------------------------------------------------------------
# 5. GET /memories/{id} — existing record returns 200
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_memory_exists(client):
    create_resp = await client.post(
        "/api/v1/memories",
        json={"type": "episodic", "content": "Visited Kashmir"},
        headers=HEADERS_A,
    )
    memory_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/memories/{memory_id}", headers=HEADERS_A)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Visited Kashmir"


# -------------------------------------------------------------------------
# 6. GET /memories/{id} — non-existent returns 404
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_memory_not_found(client):
    import uuid

    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/memories/{fake_id}", headers=HEADERS_A)
    assert resp.status_code == 404


# -------------------------------------------------------------------------
# 7. PUT /memories/{id} — update content
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_memory(client):
    create_resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Uses MySQL"},
        headers=HEADERS_A,
    )
    memory_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/memories/{memory_id}",
        json={"content": "Uses PostgreSQL"},
        headers=HEADERS_A,
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "Uses PostgreSQL"


# -------------------------------------------------------------------------
# 8. DELETE /memories/{id} — soft-delete
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_memory(client):
    create_resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Temporary fact"},
        headers=HEADERS_A,
    )
    memory_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/memories/{memory_id}", headers=HEADERS_A)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


# -------------------------------------------------------------------------
# 9. GET after DELETE — returns 404 (Invariant 2)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_after_delete_returns_404(client):
    create_resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Will be deleted"},
        headers=HEADERS_A,
    )
    memory_id = create_resp.json()["id"]

    await client.delete(f"/api/v1/memories/{memory_id}", headers=HEADERS_A)

    resp = await client.get(f"/api/v1/memories/{memory_id}", headers=HEADERS_A)
    assert resp.status_code == 404, "Invariant 2: deleted memories must not be retrieved"


# -------------------------------------------------------------------------
# 10. User isolation — user B cannot see user A's memory (Invariant 1)
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_user_isolation(client):
    create_resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Secret of user A"},
        headers=HEADERS_A,
    )
    memory_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/memories/{memory_id}", headers=HEADERS_B)
    assert resp.status_code == 404, "Invariant 1: user B must not see user A's memory"

    resp_list = await client.get("/api/v1/memories", headers=HEADERS_B)
    assert len(resp_list.json()) == 0, "Invariant 1: user B's list must be empty"


# -------------------------------------------------------------------------
# 11. Audit log — create, update, delete all logged
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_log_written(client, db_session):
    from backend.database.repository import MemoryRepository

    create_resp = await client.post(
        "/api/v1/memories",
        json={"type": "semantic", "content": "Auditable fact"},
        headers=HEADERS_A,
    )
    memory_id = create_resp.json()["id"]

    await client.put(
        f"/api/v1/memories/{memory_id}",
        json={"content": "Updated auditable fact"},
        headers=HEADERS_A,
    )
    await client.delete(f"/api/v1/memories/{memory_id}", headers=HEADERS_A)

    repo = MemoryRepository(db_session)
    logs = await repo.get_audit_log(TEST_USER_A)
    actions = [log["action"] for log in logs]
    assert "create" in actions
    assert "update" in actions
    assert "delete" in actions


# -------------------------------------------------------------------------
# 12. POST /conversations/message — placeholder returns 200
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_conversation_placeholder(client):
    resp = await client.post(
        "/api/v1/conversations/message",
        json={"message": "What database do I use?"},
        headers=HEADERS_A,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "response" in body
    assert body["conversation_id"]


# -------------------------------------------------------------------------
# 13. Missing X-User-ID header returns 401
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_user_id_returns_401(client):
    resp = await client.get("/api/v1/memories")
    assert resp.status_code == 401
