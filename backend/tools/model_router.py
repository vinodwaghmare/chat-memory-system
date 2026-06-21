"""Routes task types to model configurations.

Each task (extraction, evaluation, embedding, response) maps to a provider,
model name, and token budget. Environment variables override defaults.
See ADR-004.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    EXTRACTION = "extraction"
    EVALUATION = "evaluation"
    EMBEDDING = "embedding"
    RESPONSE = "response"


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_name: str
    max_input_tokens: int = 4096
    max_output_tokens: int = 1024
    temperature: float = 0.0


_DEFAULT_ROUTES: dict[TaskType, ModelConfig] = {
    TaskType.EXTRACTION: ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        max_input_tokens=4096,
        max_output_tokens=1024,
        temperature=0.0,
    ),
    TaskType.EVALUATION: ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        max_input_tokens=2048,
        max_output_tokens=512,
        temperature=0.0,
    ),
    TaskType.EMBEDDING: ModelConfig(
        provider="openai",
        model_name="text-embedding-3-small",
        max_input_tokens=8191,
        max_output_tokens=0,
    ),
    TaskType.RESPONSE: ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        max_input_tokens=8192,
        max_output_tokens=2048,
        temperature=0.7,
    ),
}

_ENV_OVERRIDES: dict[TaskType, str] = {
    TaskType.EXTRACTION: "EXTRACTION_MODEL",
    TaskType.EVALUATION: "EVALUATION_MODEL",
    TaskType.EMBEDDING: "EMBEDDING_MODEL",
    TaskType.RESPONSE: "RESPONSE_MODEL",
}


def get_model_config(task: TaskType) -> ModelConfig:
    default = _DEFAULT_ROUTES[task]
    env_key = _ENV_OVERRIDES.get(task, "")
    override = os.environ.get(env_key, "")
    if override:
        parts = override.split("/", 1)
        provider = parts[0] if len(parts) == 2 else default.provider
        model = parts[1] if len(parts) == 2 else parts[0]
        return ModelConfig(
            provider=provider,
            model_name=model,
            max_input_tokens=default.max_input_tokens,
            max_output_tokens=default.max_output_tokens,
            temperature=default.temperature,
        )
    return default
