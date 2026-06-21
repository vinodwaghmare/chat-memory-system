# Chat Memory System

A production-grade ChatGPT-style memory system that selectively retains information across conversations to improve future interactions.

## What It Does

- **Extracts** memories from conversations (preferences, facts, goals, experiences)
- **Evaluates** each candidate's future utility before storing (write gate)
- **Retrieves** relevant memories via hybrid search (vector + keyword + graph)
- **Ranks** by a weighted formula: 0.4 semantic + 0.2 recency + 0.2 frequency + 0.2 importance
- **Decays** unused memories over time; reinforces useful ones
- **Respects** four invariants: user isolation, deletion, graceful degradation, provenance

## Architecture

```
WRITE PATH                    READ PATH
Message                       New Query
    ↓                             ↓
Extractor (LLM)               Retriever (vector+keyword+graph)
    ↓                             ↓
Evaluator (utility+PII)       Ranking Service
    ↓                             ↓
Write Service                 Context Composer
    ↓                             ↓
Memory Store ───────────────→ Response LLM

BACKGROUND: Decay Job, Reflection Agent
PLANES:     Observability, Security, Governance
```

## Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI |
| Database | PostgreSQL + pgvector |
| Session cache | Redis |
| Orchestration | LangGraph (Temporal deferred) |
| LLM (primary) | OpenAI (GPT-4o-mini, text-embedding-3-small) |
| LLM (secondary) | Anthropic Claude |
| Frontend | Next.js 14 + Tailwind |

## Quick Start

```bash
# Clone and setup
cp .env.example .env
# Fill in OPENAI_API_KEY and ANTHROPIC_API_KEY

# Start infrastructure
docker compose -f docker-compose.dev.yml up --build

# Or run locally
pip install -e ".[dev]"
uvicorn backend.main:app --reload
```

## 20-Phase Build Roadmap

| # | Phase | Status |
|---|-------|--------|
| 0 | Cognitive Design — mission, classification, 10-question framework | Done |
| 1 | System Architecture — module graph, ADRs, dependency hierarchy | Done |
| 2 | Frontend — Next.js dashboard, memory browser, HITL corrections | Sprint 9 |
| 3 | Backend & API — CRUD endpoints, database repository | Sprint 2 |
| 4 | Workflow Orchestration — LangGraph write/read paths | Sprint 5 |
| 5 | LLM & Reasoning — extractor, evaluator, model router | Sprint 3 |
| 6 | Memory Architecture — pgvector, hybrid retrieval, ranking | Sprint 4 |
| 7 | Tooling & Sandboxing — PII filter, user memory tools | Sprint 6 |
| 8 | Multi-Agent — contracts, reflection agent, decay job | Sprint 7 |
| 9 | Evaluation — golden dataset, precision/recall, regression gate | Sprint 8 |
| 10-20 | Production hardening | Deferred (see docs/FUTURE_WORK.md) |

## Project Structure

```
backend/
├── core/           ABCs: MemoryEngine, WorkflowEngine, StorageBackend, LLMClient
├── models/         Pydantic schemas, enums
├── config/         pydantic-settings
├── database/       SQLAlchemy ORM, async pool
├── capture/        Extractor + Evaluator (write gate)
├── store/          pgvector store, Redis session
├── retrieve/       Hybrid retriever, ranking
├── context/        Context composer
├── agents/         Typed contracts, base agent
├── orchestrator/   LangGraph state, nodes, graph
├── memory/         MemoryService (high-level)
├── tools/          LLM client, model router, PII filter
├── jobs/           Decay, reflection (background)
├── evaluation/     Golden dataset, metrics, judge
├── api/            REST routers
├── auth/           User ID extraction
├── prompts/        Versioned prompt templates
└── main.py         FastAPI entry point
```

## Key Design Decisions

See `docs/adr/` for full rationale:

- **ADR-001:** Postgres + pgvector (not Pinecone) — single database, simpler ops
- **ADR-002:** Modular monolith — 15 modules, inward-only dependencies
- **ADR-003:** LangGraph now, Temporal later — abstract WorkflowEngine interface
- **ADR-004:** OpenAI primary + Claude secondary — model router per task type

## Four Invariants

1. User A's memory is never returned to user B (row-level security + query filters)
2. Deleted memories are never retrieved (soft-delete + exclusion filter)
3. Retrieval failure never blocks a response (fallback to memoryless response)
4. Every memory carries provenance (source field + append-only audit log)
