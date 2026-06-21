# ADR-002: Architecture Style

## Status
Accepted

## Date
2026-06-21

## Context
The memory system is built by a small team (1-2 engineers). We need clear module boundaries for maintainability but cannot afford microservices operational overhead. The question is whether to build a monolith, a modular monolith, or microservices from the start.

## Decision
Modular monolith with 15 disciplined modules and strict inward-only dependency hierarchy.

## The 15 Modules

```
Layer 0:  core/          — ABCs, exceptions
Layer 1:  models/        — Pydantic schemas, enums
Layer 2:  config/        — Settings
Layer 3:  database/      — ORM, repository
Layer 4:  tools/         — LLM client, model router, PII
Layer 5:  store/         — pgvector, Redis session
Layer 5:  retrieve/      — Hybrid retrieval, ranking
Layer 5:  capture/       — Extractor, evaluator
Layer 5:  context/       — Composer
Layer 6:  agents/        — Contracts, base agent
Layer 6:  jobs/          — Decay, reflection
Layer 7:  orchestrator/  — LangGraph workflows
Layer 7:  memory/        — MemoryService
Layer 8:  evaluation/    — Golden dataset, judge
Layer 9:  api/           — FastAPI routers
```

## Dependency Direction Rule
Dependencies flow INWARD only. A module at Layer N may import from Layer 0..N-1 but NEVER from Layer N+1 or higher.

## Consequences

**Positive:**
- Single deployment, single process — simple to run and debug.
- Module boundaries enforce separation of concerns without network overhead.
- Clean extraction path: any module can become a service later by putting an API in front of it.

**Negative:**
- Discipline required: no tooling enforces the dependency rule (code review only).
- All modules share one process; a memory leak in one affects all.

## When to Revisit
When the team grows beyond 3 engineers or when two modules need to scale independently (e.g., retrieval needs more compute than the rest).
