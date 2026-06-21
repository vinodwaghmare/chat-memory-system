"""Sprint 1 gate tests — Foundation (Phase 0 + 1).

Validates: imports, dependency direction, settings, health endpoints,
abstract interfaces, models, and enums.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


# -------------------------------------------------------------------------
# 1. All modules import without circular dependencies
# -------------------------------------------------------------------------
def test_import_core():
    from backend.core import exceptions, llm_client, memory_engine, storage_backend, workflow_engine
    assert exceptions.MemorySystemError
    assert memory_engine.MemoryEngine
    assert workflow_engine.WorkflowEngine
    assert storage_backend.StorageBackend
    assert llm_client.LLMClient


def test_import_models():
    from backend.models import api_schemas, conversation, enums, memory
    assert enums.MemoryType.SEMANTIC == "semantic"
    assert memory.MemoryRecord
    assert conversation.ConversationTurn
    assert api_schemas.HealthResponse


def test_import_config():
    from backend.config.settings import Settings
    assert Settings


def test_import_database():
    from backend.database import models, postgres
    assert postgres.Base
    assert models.MemoryORM
    assert models.MemoryEdgeORM
    assert models.AuditLogORM


def test_import_api():
    from backend.api import conversations, health, memories
    assert health.router
    assert memories.router
    assert conversations.router


# -------------------------------------------------------------------------
# 2. Dependency direction: core/ imports NOTHING from the project
# -------------------------------------------------------------------------
def test_core_has_no_project_imports():
    import importlib
    import inspect

    core_modules = [
        "backend.core.exceptions",
        "backend.core.llm_client",
    ]
    for mod_name in core_modules:
        mod = importlib.import_module(mod_name)
        source = inspect.getsource(mod)
        for forbidden in ["backend.api", "backend.orchestrator", "backend.database"]:
            assert forbidden not in source, f"{mod_name} imports {forbidden}"


# -------------------------------------------------------------------------
# 3. Settings loads with defaults
# -------------------------------------------------------------------------
def test_settings_defaults():
    from backend.config.settings import Settings

    s = Settings(
        openai_api_key="test-key",
        anthropic_api_key="test-key",
    )
    assert s.database_url.startswith("postgresql")
    assert s.redis_url.startswith("redis")
    assert s.semantic_weight == 0.4
    assert s.recency_weight == 0.2
    assert s.frequency_weight == 0.2
    assert s.importance_weight == 0.2
    assert s.is_development is True
    assert s.is_production is False


# -------------------------------------------------------------------------
# 4. Health endpoints
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_live_returns_200():
    from backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# -------------------------------------------------------------------------
# 5. Abstract interfaces cannot be instantiated
# -------------------------------------------------------------------------
def test_memory_engine_is_abstract():
    from backend.core.memory_engine import MemoryEngine

    with pytest.raises(TypeError):
        MemoryEngine()


def test_workflow_engine_is_abstract():
    from backend.core.workflow_engine import WorkflowEngine

    with pytest.raises(TypeError):
        WorkflowEngine()


def test_storage_backend_is_abstract():
    from backend.core.storage_backend import StorageBackend

    with pytest.raises(TypeError):
        StorageBackend()


def test_llm_client_is_abstract():
    from backend.core.llm_client import LLMClient

    with pytest.raises(TypeError):
        LLMClient()


# -------------------------------------------------------------------------
# 6. Models validate correctly
# -------------------------------------------------------------------------
def test_memory_record_validates():
    from backend.models.memory import MemoryRecord

    m = MemoryRecord(
        user_id="user-123",
        type="semantic",
        content="Uses PostgreSQL",
        importance=8,
        confidence=0.9,
    )
    assert m.type == "semantic"
    assert m.importance == 8


def test_memory_record_rejects_invalid_type():
    from backend.models.memory import MemoryRecord

    with pytest.raises(ValueError):
        MemoryRecord(
            user_id="user-123",
            type="invalid_type",
            content="test",
        )


# -------------------------------------------------------------------------
# 7. Enums serialize to strings
# -------------------------------------------------------------------------
def test_enums_serialize_to_strings():
    from backend.models.enums import MemoryType, WorkflowStatus

    assert MemoryType.EPISODIC == "episodic"
    assert str(MemoryType.EPISODIC) == "MemoryType.EPISODIC"
    assert MemoryType.EPISODIC.value == "episodic"
    assert WorkflowStatus.COMPLETED.value == "completed"


# -------------------------------------------------------------------------
# 8. Exceptions carry context
# -------------------------------------------------------------------------
def test_memory_not_found_carries_id():
    from backend.core.exceptions import MemoryNotFoundError

    exc = MemoryNotFoundError("mem-123", "user-456")
    assert exc.memory_id == "mem-123"
    assert exc.user_id == "user-456"
    assert "mem-123" in str(exc)


def test_workflow_error_carries_id():
    from backend.core.exceptions import WorkflowError

    exc = WorkflowError("wf-789", "extraction failed")
    assert exc.workflow_id == "wf-789"
    assert "extraction failed" in str(exc)


def test_pii_detected_carries_types():
    from backend.core.exceptions import PIIDetectedError

    exc = PIIDetectedError(["credit_card", "api_key"])
    assert exc.detected_types == ["credit_card", "api_key"]
