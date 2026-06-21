# ADR-003: Orchestration Engine

## Status
Accepted

## Date
2026-06-21

## Context
The memory system has two workflows: a write path (extract → evaluate → store) and a read path (retrieve → rank → compose → respond). These need orchestration with error handling, retries, and state tracking. Options: LangGraph (lightweight, runs in-process), Temporal (durable, distributed), or plain async Python functions.

## Decision
Start with LangGraph for Phases 0-9. Defer Temporal until scale demands it. Define an abstract `WorkflowEngine` interface to enable swapping later.

## Consequences

**Positive:**
- Zero extra infrastructure in Phases 0-9 (LangGraph runs inside the Python process).
- State graphs are easy to visualize and test.
- The `WorkflowEngine` ABC in `backend/core/workflow_engine.py` decouples business logic from the orchestration engine.

**Negative:**
- LangGraph has no built-in durable execution (workflow state lost on process crash).
- No cross-service coordination capabilities.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Temporal | Requires a Temporal server cluster — premature infrastructure cost for Phases 0-9. |
| Plain async functions | No built-in state tracking, retry logic, or checkpointing. |

## Exit Hatch
Write a `TemporalWorkflowEngine` implementation of the same `WorkflowEngine` interface and swap it in. Nothing else in the codebase changes. Revisit when concurrent workflow count exceeds 50/min or cross-service coordination is needed.
