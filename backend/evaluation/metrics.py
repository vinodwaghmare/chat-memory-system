"""Retrieval quality metrics: precision, recall, F1, MRR."""

from __future__ import annotations


class RetrievalMetrics:

    @staticmethod
    def precision(retrieved: list[str], expected: list[str]) -> float:
        if not retrieved:
            return 0.0
        relevant = set(expected)
        hits = sum(1 for r in retrieved if r in relevant)
        return hits / len(retrieved)

    @staticmethod
    def recall(retrieved: list[str], expected: list[str]) -> float:
        if not expected:
            return 1.0
        relevant = set(expected)
        hits = sum(1 for r in retrieved if r in relevant)
        return hits / len(expected)

    @staticmethod
    def f1(precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)

    @staticmethod
    def mean_reciprocal_rank(retrieved: list[str], expected: list[str]) -> float:
        relevant = set(expected)
        for i, r in enumerate(retrieved, start=1):
            if r in relevant:
                return 1.0 / i
        return 0.0
