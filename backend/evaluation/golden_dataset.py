"""Golden dataset for retrieval quality evaluation.

Loads test cases from fixtures/golden_retrieval.json.
Each case: query + user_id + expected memory contents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


@dataclass(frozen=True)
class GoldenCase:
    query: str
    user_id: str
    expected_contents: tuple[str, ...]
    expected_types: tuple[str, ...] = ()


class GoldenDataset:

    def __init__(self, path: Path | None = None):
        self._path = path or _FIXTURES_DIR / "golden_retrieval.json"

    def load(self) -> list[GoldenCase]:
        if not self._path.exists():
            return []
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        return [
            GoldenCase(
                query=item["query"],
                user_id=item.get("user_id", "test-user"),
                expected_contents=tuple(item.get("expected_contents", [])),
                expected_types=tuple(item.get("expected_types", [])),
            )
            for item in data
        ]
