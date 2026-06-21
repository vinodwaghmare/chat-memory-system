"""Sprint 8 gate tests — Evaluation Systems (Phase 9).

Validates: golden dataset, precision/recall metrics, LLM judge,
regression gate.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.core.llm_client import LLMResponse
from backend.evaluation.golden_dataset import GoldenDataset
from backend.evaluation.judge import MemoryJudge
from backend.evaluation.metrics import RetrievalMetrics
from backend.evaluation.regression_gate import RegressionGate


# -------------------------------------------------------------------------
# Golden dataset
# -------------------------------------------------------------------------
def test_golden_dataset_loads():
    ds = GoldenDataset()
    cases = ds.load()
    assert len(cases) == 5
    assert cases[0].query == "What database do I use?"
    assert "Uses PostgreSQL" in cases[0].expected_contents


def test_golden_case_is_frozen():
    ds = GoldenDataset()
    cases = ds.load()
    with pytest.raises(AttributeError):
        cases[0].query = "changed"


# -------------------------------------------------------------------------
# Metrics
# -------------------------------------------------------------------------
def test_precision_perfect():
    p = RetrievalMetrics.precision(["a", "b"], ["a", "b"])
    assert p == 1.0


def test_precision_partial():
    p = RetrievalMetrics.precision(["a", "b", "c"], ["a", "b"])
    assert abs(p - 2 / 3) < 0.01


def test_precision_empty_retrieved():
    p = RetrievalMetrics.precision([], ["a"])
    assert p == 0.0


def test_recall_perfect():
    r = RetrievalMetrics.recall(["a", "b"], ["a", "b"])
    assert r == 1.0


def test_recall_partial():
    r = RetrievalMetrics.recall(["a"], ["a", "b"])
    assert r == 0.5


def test_recall_empty_expected():
    r = RetrievalMetrics.recall(["a"], [])
    assert r == 1.0


def test_f1_balanced():
    f = RetrievalMetrics.f1(0.8, 0.8)
    assert abs(f - 0.8) < 0.01


def test_f1_zero():
    f = RetrievalMetrics.f1(0.0, 0.0)
    assert f == 0.0


def test_mrr_first_hit():
    mrr = RetrievalMetrics.mean_reciprocal_rank(["a", "b"], ["a"])
    assert mrr == 1.0


def test_mrr_second_hit():
    mrr = RetrievalMetrics.mean_reciprocal_rank(["x", "a"], ["a"])
    assert mrr == 0.5


def test_mrr_no_hit():
    mrr = RetrievalMetrics.mean_reciprocal_rank(["x", "y"], ["a"])
    assert mrr == 0.0


# -------------------------------------------------------------------------
# LLM Judge
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_judge_detects_hallucination():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content={
        "correctness_score": 0.5,
        "missed_facts": [],
        "hallucinated": ["User works at Google"],
        "notes": "One hallucinated memory detected",
    })

    judge = MemoryJudge(llm)
    result = await judge.judge_extraction(
        conversation="I use PostgreSQL for my projects.",
        extracted_memories=["Uses PostgreSQL", "User works at Google"],
    )

    assert result.correctness_score == 0.5
    assert "Google" in result.hallucinated[0]


@pytest.mark.asyncio
async def test_judge_confirms_correct_extraction():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content={
        "correctness_score": 1.0,
        "missed_facts": [],
        "hallucinated": [],
        "notes": "All memories are correct",
    })

    judge = MemoryJudge(llm)
    result = await judge.judge_extraction(
        conversation="I use PostgreSQL and prefer short answers.",
        extracted_memories=["Uses PostgreSQL", "Prefers short answers"],
    )

    assert result.correctness_score == 1.0
    assert len(result.hallucinated) == 0
    assert len(result.missed_facts) == 0


@pytest.mark.asyncio
async def test_judge_handles_malformed():
    llm = AsyncMock()
    llm.complete.return_value = LLMResponse(content="not json")

    judge = MemoryJudge(llm)
    result = await judge.judge_extraction("test", ["test"])

    assert result.correctness_score == 0.5
    assert "Unparseable" in result.notes


# -------------------------------------------------------------------------
# Regression gate
# -------------------------------------------------------------------------
def test_gate_passes_when_metrics_improve():
    gate = RegressionGate()
    result = gate.check(
        baseline={"precision": 0.85, "recall": 0.80, "latency_p99": 80.0},
        current={"precision": 0.90, "recall": 0.85, "latency_p99": 75.0},
    )
    assert result.passed is True
    assert len(result.regressions) == 0


def test_gate_fails_on_precision_drop():
    gate = RegressionGate()
    result = gate.check(
        baseline={"precision": 0.90, "recall": 0.80, "latency_p99": 80.0},
        current={"precision": 0.75, "recall": 0.80, "latency_p99": 80.0},
    )
    assert result.passed is False
    assert any("Precision" in r for r in result.regressions)


def test_gate_fails_on_latency_spike():
    gate = RegressionGate()
    result = gate.check(
        baseline={"precision": 0.85, "recall": 0.80, "latency_p99": 80.0},
        current={"precision": 0.85, "recall": 0.80, "latency_p99": 200.0},
    )
    assert result.passed is False
    assert any("Latency" in r for r in result.regressions)


def test_gate_result_is_frozen():
    result = RegressionGate().check(
        baseline={"precision": 0.9},
        current={"precision": 0.9},
    )
    with pytest.raises(AttributeError):
        result.passed = False
