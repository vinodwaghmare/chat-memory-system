"""Concrete LLM client supporting OpenAI and Anthropic.

Retry logic with exponential backoff. Cost estimation per call.
Output guardrail: validates JSON responses, handles malformed output.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from backend.config.settings import get_settings
from backend.core.exceptions import LLMClientError
from backend.core.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

COST_PER_1K_INPUT: dict[str, float] = {
    "gpt-4o": 0.0025,
    "gpt-4o-mini": 0.00015,
    "claude-sonnet-4-20250514": 0.003,
}
COST_PER_1K_OUTPUT: dict[str, float] = {
    "gpt-4o": 0.01,
    "gpt-4o-mini": 0.0006,
    "claude-sonnet-4-20250514": 0.015,
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    inp = COST_PER_1K_INPUT.get(model, 0.001) * input_tokens / 1000
    out = COST_PER_1K_OUTPUT.get(model, 0.002) * output_tokens / 1000
    return round(inp + out, 6)


def try_parse_json(text: str) -> Any | None:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


class ConcreteLLMClient(LLMClient):

    async def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        response_format: dict[str, str] | None = None,
    ) -> LLMResponse:
        cfg = get_settings()
        provider = "anthropic" if "claude" in model else "openai"

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                start = time.monotonic()
                if provider == "openai":
                    result = await self._call_openai(
                        cfg.openai_api_key, model, messages,
                        system_prompt, temperature, max_tokens, response_format,
                    )
                else:
                    result = await self._call_anthropic(
                        cfg.anthropic_api_key, model, messages,
                        system_prompt, temperature, max_tokens,
                    )
                elapsed_ms = (time.monotonic() - start) * 1000
                result.latency_ms = round(elapsed_ms, 1)
                return result
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning("LLM call failed (attempt %d), retrying in %ds: %s", attempt + 1, wait, exc)
                    await asyncio.sleep(wait)

        raise LLMClientError(provider, str(last_error))

    async def embed(
        self,
        texts: list[str],
        model: str = "",
        dimensions: int = 1536,
    ) -> list[list[float]]:
        cfg = get_settings()
        model = model or cfg.openai_embedding_model
        dimensions = dimensions or cfg.openai_embedding_dimensions

        try:
            from openai import AsyncOpenAI

            client_kwargs: dict[str, Any] = {"api_key": cfg.openai_api_key}
            if cfg.openai_base_url:
                client_kwargs["base_url"] = cfg.openai_base_url
            client = AsyncOpenAI(**client_kwargs)
            all_embeddings: list[list[float]] = []

            embed_kwargs: dict[str, Any] = {"model": model, "input": None}
            if not cfg.openai_base_url:
                embed_kwargs["dimensions"] = dimensions

            for i in range(0, len(texts), 100):
                batch = texts[i:i + 100]
                embed_kwargs["input"] = batch
                resp = await client.embeddings.create(**embed_kwargs)
                all_embeddings.extend([d.embedding for d in resp.data])

            return all_embeddings
        except Exception as exc:
            raise LLMClientError("openai", f"Embedding failed: {exc}") from exc

    async def _call_openai(
        self,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: dict[str, str] | None,
    ) -> LLMResponse:
        from openai import AsyncOpenAI

        cfg = get_settings()
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if cfg.openai_base_url:
            client_kwargs["base_url"] = cfg.openai_base_url
        client = AsyncOpenAI(**client_kwargs)
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format and not cfg.openai_base_url:
            kwargs["response_format"] = response_format

        resp = await client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        content = choice.message.content or ""
        input_tokens = resp.usage.prompt_tokens if resp.usage else 0
        output_tokens = resp.usage.completion_tokens if resp.usage else 0

        parsed = try_parse_json(content)

        return LLMResponse(
            content=parsed if parsed is not None else content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=model,
            estimated_cost_usd=_estimate_cost(model, input_tokens, output_tokens),
        )

    async def _call_anthropic(
        self,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=model,
            system=system_prompt or "You are a helpful assistant.",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.content[0].text if resp.content else ""
        input_tokens = resp.usage.input_tokens
        output_tokens = resp.usage.output_tokens

        parsed = try_parse_json(content)

        return LLMResponse(
            content=parsed if parsed is not None else content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=model,
            estimated_cost_usd=_estimate_cost(model, input_tokens, output_tokens),
        )
