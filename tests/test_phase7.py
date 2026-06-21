"""Sprint 6 gate tests — Tooling & PII (Phase 7).

Validates: PII filter detection, user memory tools.
"""

from __future__ import annotations

import pytest

from backend.tools.pii_filter import PIIFilter
from backend.tools.tool_registry import ToolRegistry

from tests.conftest import TEST_USER_A


# -------------------------------------------------------------------------
# PII Filter
# -------------------------------------------------------------------------
def test_pii_catches_credit_card():
    f = PIIFilter()
    result = f.detect("My card is 4111-1111-1111-1111")
    assert result.has_pii is True
    assert "credit_card" in result.detected_types
    assert "CREDIT_CARD_REDACTED" in result.redacted_text


def test_pii_catches_api_key_openai():
    f = PIIFilter()
    result = f.detect("My key is sk-abcdefghijklmnopqrstuvwxyz1234567890")
    assert result.has_pii is True
    assert "api_key" in result.detected_types


def test_pii_catches_github_token():
    f = PIIFilter()
    result = f.detect("Use this token ghp_abcdefghijklmnopqrstuvwxyz1234567890")
    assert result.has_pii is True
    assert "api_key" in result.detected_types


def test_pii_catches_password():
    f = PIIFilter()
    result = f.detect("password: mysecretpass123")
    assert result.has_pii is True
    assert "password" in result.detected_types


def test_pii_catches_ssn():
    f = PIIFilter()
    result = f.detect("SSN is 123-45-6789")
    assert result.has_pii is True
    assert "ssn" in result.detected_types


def test_pii_allows_normal_text():
    f = PIIFilter()
    result = f.detect("I use PostgreSQL and prefer short answers")
    assert result.has_pii is False
    assert result.detected_types == ()


def test_pii_detects_multiple_types():
    f = PIIFilter()
    result = f.detect("Card 4111 1111 1111 1111, password=secret123")
    assert result.has_pii is True
    assert "credit_card" in result.detected_types
    assert "password" in result.detected_types


# -------------------------------------------------------------------------
# Tool Registry
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_remember_this(db_session):
    tools = ToolRegistry(db_session)
    result = await tools.remember_this(TEST_USER_A, "I love Python")
    await db_session.commit()

    assert result["status"] == "remembered"
    assert result["memory_id"]

    show = await tools.show_memories(TEST_USER_A)
    assert show["count"] == 1
    assert show["memories"][0]["content"] == "I love Python"


@pytest.mark.asyncio
async def test_forget_this(db_session):
    tools = ToolRegistry(db_session)
    await tools.remember_this(TEST_USER_A, "Uses PostgreSQL")
    await tools.remember_this(TEST_USER_A, "Likes Python")
    await db_session.commit()

    result = await tools.forget_this(TEST_USER_A, "PostgreSQL")
    await db_session.commit()

    assert result["status"] == "forgotten"
    assert result["deleted_count"] == 1

    show = await tools.show_memories(TEST_USER_A)
    assert show["count"] == 1
    assert show["memories"][0]["content"] == "Likes Python"


@pytest.mark.asyncio
async def test_show_memories(db_session):
    tools = ToolRegistry(db_session)
    await tools.remember_this(TEST_USER_A, "Fact 1")
    await tools.remember_this(TEST_USER_A, "Fact 2", "procedural")
    await db_session.commit()

    result = await tools.show_memories(TEST_USER_A)
    assert result["count"] == 2

    filtered = await tools.show_memories(TEST_USER_A, "procedural")
    assert filtered["count"] == 1


@pytest.mark.asyncio
async def test_correct_memory(db_session):
    tools = ToolRegistry(db_session)
    r = await tools.remember_this(TEST_USER_A, "Uses MySQL")
    await db_session.commit()

    result = await tools.correct_memory(TEST_USER_A, r["memory_id"], "Uses PostgreSQL")
    await db_session.commit()

    assert result["status"] == "corrected"
    assert result["new_content"] == "Uses PostgreSQL"

    show = await tools.show_memories(TEST_USER_A)
    assert show["memories"][0]["content"] == "Uses PostgreSQL"


@pytest.mark.asyncio
async def test_correct_nonexistent_memory(db_session):
    import uuid
    tools = ToolRegistry(db_session)
    result = await tools.correct_memory(TEST_USER_A, str(uuid.uuid4()), "new content")
    assert result["status"] == "not_found"
