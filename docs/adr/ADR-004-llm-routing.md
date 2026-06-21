# ADR-004: LLM Provider Routing

## Status
Accepted

## Date
2026-06-21

## Context
The memory system uses LLMs for three tasks: memory extraction (reading conversation turns), memory evaluation (judging utility), and response generation (answering with memory context). Different tasks have different cost, latency, and quality requirements. We have access to both OpenAI and Anthropic APIs.

## Decision
Use a model router that maps task types to providers. OpenAI primary, Anthropic secondary.

| Task | Model | Why |
|------|-------|-----|
| Extraction | gpt-4o-mini | Cheap, fast, structured output reliable |
| Evaluation | gpt-4o-mini | Same — simple keep/drop judgment |
| Embedding | text-embedding-3-small | 1536 dims, good quality/cost ratio |
| Response | gpt-4o or claude-sonnet-4-20250514 | Higher quality for user-facing output |

## Consequences

**Positive:**
- Cost-optimized: cheap model for high-volume extraction, expensive model only for response.
- Provider redundancy: if OpenAI is down, Claude can handle response generation.
- Per-task override via environment variables (EXTRACTION_MODEL, etc.).

**Negative:**
- Two provider SDKs to maintain.
- Prompt templates may need provider-specific tuning.

## Exit Hatch
The `LLMClient` ABC in `backend/core/llm_client.py` and the model router abstract provider selection. Adding a new provider requires one new client class and a routing table entry.
