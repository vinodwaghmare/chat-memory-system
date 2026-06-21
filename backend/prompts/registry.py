"""Loads versioned prompt templates from disk."""

from __future__ import annotations

from pathlib import Path

from backend.core.exceptions import ConfigurationError

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_prompt(task_type: str, version: str = "v1") -> str:
    path = _TEMPLATES_DIR / task_type / f"{version}.txt"
    if not path.exists():
        raise ConfigurationError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8").strip()
