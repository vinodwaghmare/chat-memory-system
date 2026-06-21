# Future Work

The core memory system (Phases 0-9) is the current build scope. The following phases are intentionally deferred, with rationale and half-built hooks documented.

---

## Phase 10 — Observability

**What it is:** Prometheus metrics, Grafana dashboards, OpenTelemetry traces for every extraction, retrieval, and LLM call.

**Half-built:**
- `backend/api/health.py` — service health checks already report Postgres and Redis status.
- Logging is structured with `%(name)s` logger names per module.

**Missing:**
- Prometheus metrics endpoint (`/metrics`)
- OpenTelemetry span instrumentation on write and read paths
- Grafana dashboard definitions
- Token cost attribution per workflow

---

## Phase 11 — Security Architecture

**What it is:** JWT authentication, encryption at rest (AES-256 via KMS), production PII detection (Microsoft Presidio), threat model.

**Half-built:**
- `backend/auth/dependencies.py` — user_id extraction (swap to JWT later)
- `backend/tools/pii_filter.py` — regex-based PII detection (Phase 7)
- Row-level security enabled in DDL (`001-init.sql`)

**Missing:**
- JWT validation middleware
- Encryption at rest for sensitive memory content
- Microsoft Presidio integration (replaces regex PII filter)
- Formal threat model document

---

## Phase 12 — Reliability Engineering

**What it is:** Circuit breakers on LLM calls, retry with backoff, idempotency keys, graceful degradation.

**Half-built:**
- Invariant 3 (retrieval failure never blocks response) is enforced in MemoryService.
- LLM client has basic retry logic.

**Missing:**
- Circuit breaker pattern for LLM providers
- Idempotency keys for memory writes
- Dead letter queue for failed extractions

---

## Phases 13-20

Deferred entirely. Infrastructure scaling (Phase 13), data engineering (14), governance (15), economics (16), developer experience (17), CI/CD (18), HITL workflows (19), continuous learning (20) will be picked up after the core proves value.
