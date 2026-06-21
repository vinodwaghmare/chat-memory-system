# ADR-001: Storage Engine

## Status
Accepted

## Date
2026-06-21

## Context
The memory system needs durable storage for typed memory records (episodic, semantic, procedural) with both structured queries (filter by user, type, importance) and semantic search (vector similarity on embeddings). The options are: a single Postgres database with the pgvector extension, or a dedicated vector database (Pinecone, Weaviate, Qdrant) alongside Postgres for structured data.

## Decision
Use PostgreSQL with pgvector as the single storage engine for both structured and vector data.

## Consequences

**Positive:**
- One database to operate, back up, and monitor.
- Structured queries (user isolation, type filters, full-text search) and vector queries live in one transaction boundary.
- Row-level security enforces Invariant 1 (user isolation) at the database level.
- The team already knows Postgres.

**Negative:**
- pgvector's ivfflat index is less optimized than purpose-built vector databases at very large scale (100M+ vectors).
- No built-in auto-scaling of vector search independent of structured queries.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Pinecone | Adds a second data store, doubles operational complexity, vendor lock-in. |
| Weaviate | Same operational overhead; pgvector is sufficient at our scale. |
| Qdrant | Good performance but separate system to manage; premature at <1M vectors. |

## Exit Hatch
The `StorageBackend` abstract interface (`backend/core/storage_backend.py`) allows swapping pgvector for a dedicated vector cluster without touching retrieval or capture logic. Revisit when retrieval QPS exceeds single-node Postgres capacity or vector count exceeds 10M.
