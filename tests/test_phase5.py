"""Sprint 3 gate tests — LLM & Reasoning (Phase 5).

All LLM calls mocked with pre-recorded responses. No real API calls.
Validates: extractor, evaluator, model router, prompt registry.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest

from backend.capture.extractor import CandidateMemory, MemoryExtractor
from backend.capture.evaluator import EvaluationResult, MemoryEvaluator
from backend.core.llm_client import LLMResponse
from backend.models.enums import MemoryType
from backend.models.memory import MemoryRecord


def _mock_llm(content):
    """Create a mock LLMClient whose complete() returns the given content."""
    client = AsyncMock()
    client.complete.return_value = LLMResponse(
        content=content,
        input_tokens=100,
        output_tokens=50,
        model_used="gpt-4o-mini",
        estimated_cost_usd=0.0001,
    )
    return client


# -------------------------------------------------------------------------
# Extractor tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_extractor_produces_candidates():
    llm = _mock_llm([
        {"type": "semantic", "content": "Uses PostgreSQL", "importance_hint": 8},
        {"type": "procedural", "content": "Prefers short answers", "importance_hint": 9},
    ])
    extractor = MemoryExtractor(llm)
    candidates = await extractor.extract("I always use PostgreSQL and prefer short answers.")

    assert len(candidates) == 2
    assert candidates[0].type == MemoryType.SEMANTIC
    assert candidates[0].content == "Uses PostgreSQL"
    assert candidates[0].importance_hint == 8
    assert candidates[1].type == MemoryType.PROCEDURAL


@pytest.mark.asyncio
async def test_extractor_handles_dict_wrapper():
    llm = _mock_llm({"memories": [
        {"type": "semantic", "content": "Knows Python", "importance_hint": 7},
    ]})
    extractor = MemoryExtractor(llm)
    candidates = await extractor.extract("I've been writing Python for years.")

    assert len(candidates) == 1
    assert candidates[0].content == "Knows Python"


@pytest.mark.asyncio
async def test_extractor_handles_malformed_response():
    llm = _mock_llm("This is not JSON at all")
    extractor = MemoryExtractor(llm)
    candidates = await extractor.extract("Some random chat")

    assert candidates == []


@pytest.mark.asyncio
async def test_extractor_skips_invalid_type():
    llm = _mock_llm([
        {"type": "semantic", "content": "Valid fact", "importance_hint": 5},
        {"type": "invalid_type", "content": "Bad type", "importance_hint": 5},
    ])
    extractor = MemoryExtractor(llm)
    candidates = await extractor.extract("test")

    assert len(candidates) == 1
    assert candidates[0].content == "Valid fact"


@pytest.mark.asyncio
async def test_extractor_clamps_importance():
    llm = _mock_llm([
        {"type": "semantic", "content": "Test", "importance_hint": 15},
    ])
    extractor = MemoryExtractor(llm)
    candidates = await extractor.extract("test")

    assert candidates[0].importance_hint == 10


# -------------------------------------------------------------------------
# Evaluator tests
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_evaluator_keeps_high_utility():
    llm = _mock_llm({"keep": True, "importance": 8, "confidence": 0.9, "reason": "Stable technical fact"})
    evaluator = MemoryEvaluator(llm)
    candidate = CandidateMemory(type=MemoryType.SEMANTIC, content="Uses PostgreSQL", importance_hint=8)

    result = await evaluator.evaluate(candidate)

    assert result.keep is True
    assert result.importance == 8
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_evaluator_drops_low_utility():
    llm = _mock_llm({"keep": False, "importance": 1, "confidence": 0.3, "reason": "Ephemeral statement"})
    evaluator = MemoryEvaluator(llm)
    candidate = CandidateMemory(type=MemoryType.EPISODIC, content="Had coffee today", importance_hint=2)

    result = await evaluator.evaluate(candidate)

    assert result.keep is False


@pytest.mark.asyncio
async def test_evaluator_with_existing_memories():
    llm = _mock_llm({"keep": False, "importance": 5, "confidence": 0.8, "reason": "Duplicate"})
    evaluator = MemoryEvaluator(llm)
    candidate = CandidateMemory(type=MemoryType.SEMANTIC, content="Uses PostgreSQL", importance_hint=8)
    existing = [MemoryRecord(user_id="u1", type=MemoryType.SEMANTIC, content="Uses PostgreSQL")]

    result = await evaluator.evaluate(candidate, existing)

    assert result.keep is False
    llm.complete.assert_called_once()
    call_kwargs = llm.complete.call_args
    assert "PostgreSQL" in call_kwargs.kwargs.get("system_prompt", "") or \
           "PostgreSQL" in str(call_kwargs)


@pytest.mark.asyncio
async def test_evaluator_handles_malformed_response():
    llm = _mock_llm("not a dict")
    evaluator = MemoryEvaluator(llm)
    candidate = CandidateMemory(type=MemoryType.SEMANTIC, content="Test", importance_hint=7)

    result = await evaluator.evaluate(candidate)

    assert result.keep is True
    assert result.importance == 7
    assert result.confidence == 0.5


# -------------------------------------------------------------------------
# Model router tests
# -------------------------------------------------------------------------
def test_model_router_returns_correct_config():
    from backend.tools.model_router import TaskType, get_model_config

    extraction = get_model_config(TaskType.EXTRACTION)
    assert extraction.provider == "openai"
    assert extraction.model_name == "gpt-4o-mini"

    response = get_model_config(TaskType.RESPONSE)
    assert response.model_name == "gpt-4o"

    embedding = get_model_config(TaskType.EMBEDDING)
    assert embedding.model_name == "text-embedding-3-small"


def test_model_router_env_override(monkeypatch):
    from backend.tools.model_router import TaskType, get_model_config

    monkeypatch.setenv("EXTRACTION_MODEL", "anthropic/claude-sonnet-4-20250514")
    config = get_model_config(TaskType.EXTRACTION)
    assert config.provider == "anthropic"
    assert config.model_name == "claude-sonnet-4-20250514"


# -------------------------------------------------------------------------
# Prompt registry tests
# -------------------------------------------------------------------------
def test_prompt_registry_loads_templates():
    from backend.prompts.registry import load_prompt

    extraction = load_prompt("extraction")
    assert "memory extraction agent" in extraction.lower()

    evaluation = load_prompt("evaluation")
    assert "memory evaluator" in evaluation.lower()

    response = load_prompt("response")
    assert "memory" in response.lower()


def test_prompt_registry_raises_on_missing():
    from backend.core.exceptions import ConfigurationError
    from backend.prompts.registry import load_prompt

    with pytest.raises(ConfigurationError):
        load_prompt("nonexistent_task")


# -------------------------------------------------------------------------
# CandidateMemory is frozen
# -------------------------------------------------------------------------
def test_candidate_memory_is_frozen():
    c = CandidateMemory(type=MemoryType.SEMANTIC, content="test", importance_hint=5)
    with pytest.raises(AttributeError):
        c.content = "changed"
