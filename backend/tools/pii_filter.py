"""PII detection filter — blocks sensitive data from being stored.

Regex-based for Phase 0-9. Swap to Microsoft Presidio in Phase 11.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PIIDetectionResult:
    has_pii: bool
    detected_types: tuple[str, ...] = ()
    redacted_text: str = ""


_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("credit_card", re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("api_key", re.compile(
        r"(?:sk-[a-zA-Z0-9]{20,})"
        r"|(?:AKIA[0-9A-Z]{16})"
        r"|(?:ghp_[a-zA-Z0-9]{36})"
        r"|(?:glpat-[a-zA-Z0-9\-_]{20,})"
        r"|(?:xox[baprs]-[a-zA-Z0-9\-]{10,})"
    )),
    ("password", re.compile(
        r"(?:password|passwd|pwd|secret|token)\s*[:=]\s*\S+",
        re.IGNORECASE,
    )),
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b")),
]


class PIIFilter:

    def detect(self, text: str) -> PIIDetectionResult:
        detected: list[str] = []
        redacted = text

        for pii_type, pattern in _PATTERNS:
            if pattern.search(text):
                detected.append(pii_type)
                redacted = pattern.sub(f"[{pii_type.upper()}_REDACTED]", redacted)

        return PIIDetectionResult(
            has_pii=len(detected) > 0,
            detected_types=tuple(detected),
            redacted_text=redacted,
        )
