"""Base agent class with context truncation, prompt assembly, output guardrail."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from backend.core.llm_client import LLMClient, LLMResponse
from backend.tools.model_router import TaskType, get_model_config

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 4


class BaseAgent(ABC):

    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client

    @property
    @abstractmethod
    def agent_type(self) -> str:
        ...

    @abstractmethod
    def _system_prompt(self, **kwargs: Any) -> str:
        ...

    @abstractmethod
    def _task_type(self) -> TaskType:
        ...

    async def _call_llm(self, user_content: str, **prompt_kwargs: Any) -> LLMResponse:
        config = get_model_config(self._task_type())
        system = self._system_prompt(**prompt_kwargs)

        max_input_chars = config.max_input_tokens * CHARS_PER_TOKEN
        if len(user_content) > max_input_chars:
            user_content = user_content[:max_input_chars] + "\n[truncated]"

        return await self._llm.complete(
            model=config.model_name,
            messages=[{"role": "user", "content": user_content}],
            system_prompt=system,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
            response_format={"type": "json_object"},
        )

    def _parse_json_output(self, content: Any) -> Any:
        if isinstance(content, (dict, list)):
            return content
        if isinstance(content, str):
            try:
                return json.loads(content)
            except (json.JSONDecodeError, ValueError):
                pass
        return None
