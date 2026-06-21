# Chat Memory System

A memory layer for conversational AI that selectively retains information across conversations to improve future interactions.

Instead of treating every conversation as stateless, this system extracts facts, preferences, and experiences from messages, evaluates whether they are worth remembering, and retrieves relevant memories to personalize responses. It is a complete implementation of the write-evaluate-store-retrieve-rank-compose loop, deployed on Google Cloud with PostgreSQL + pgvector.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-0.3+-4169E1.svg)](https://github.com/pgvector/pgvector)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg)](https://nextjs.org)

## Screenshots

| Dashboard | Memory Browser |
|-----------|---------------|
| ![Dashboard](docs/images/dashboard.png) | ![Memories](docs/images/memories.png) |

## Why This Exists

Most LLM applications are stateless. Each conversation starts from zero. Users repeat themselves, preferences are forgotten, and context from previous sessions is lost.

Commercial products like ChatGPT have added memory features, but the implementation details are opaque. This project is an open implementation of a production memory system that:

- Decides what is worth remembering (not everything is)
- Stores memories with vector embeddings for semantic search
- Retrieves relevant memories using multiple strategies
- Manages memory lifecycle through decay and consolidation
- Enforces user isolation at the database level

## Key Features

- **Selective extraction**: LLM-powered extraction of facts, preferences, and experiences from conversation turns
- **Write gate**: Each candidate memory is evaluated for utility and deduplicated before storage
- **Hybrid retrieval**: Vector similarity search + keyword search, merged and deduplicated
- **Weighted ranking**: `0.4 * semantic + 0.2 * recency + 0.2 * frequency + 0.2 * importance` (all weights configurable)
- **Memory decay**: Unused memories lose weight over time (factor: 0.95 per cycle). Memories below threshold are archived
- **Reflection agent**: Consolidates old memories into summaries, archives originals while preserving provenance
- **User isolation**: Row-level security on PostgreSQL. Every query filters by `user_id`
- **Soft delete**: Deleted memories are never returned but remain in the database for audit
- **Audit logging**: Append-only log of all memory operations with timestamps
- **PII detection**: Regex-based filtering for credit cards, SSNs, API keys (Presidio integration planned)
- **LLM fallback**: Automatic failover from OpenAI to OpenRouter when quota is exhausted
- **Model routing**: Different models for different tasks (extraction: gpt-4o-mini, response: gpt-4o)

## Architecture

```
WRITE PATH                          READ PATH
Message                             New Query
    |                                   |
    v                                   v
Extractor (LLM)                     Embed Query
    |                                   |
    v                                   v
Evaluator (LLM)                     Hybrid Retriever
  keep/drop                         vector + keyword
    |                                   |
    v                                   v
Embed + Store                       Ranking Service
    |                             (4-factor scoring)
    v                                   |
PostgreSQL + pgvector                   v
    |                             Context Composer
    v                            (token-budgeted)
Audit Log                              |
                                       v
                                  Response LLM
                                (with memory context)

BACKGROUND JOBS
  Decay Job       - reduces memory weights on schedule
  Reflection Job  - consolidates old memories into summaries
```

### Write Path

1. **Extract**: The LLM reads the user message and produces candidate memories as structured JSON (type, content, importance)
2. **Evaluate**: Each candidate is checked for utility and duplication against existing memories. Low-value candidates are dropped
3. **Embed**: Approved memories are embedded using `text-embedding-3-small` (1536 dimensions)
4. **Store**: Memories are persisted to PostgreSQL with their embeddings, importance scores, and source metadata
5. **Audit**: Every write operation is logged to an append-only audit table

### Read Path

1. **Retrieve**: The query is embedded and searched against stored memories using cosine similarity. A parallel keyword search runs simultaneously
2. **Rank**: Results from both searches are merged, deduplicated, and scored using the 4-factor formula
3. **Compose**: Top memories are grouped by type (facts, preferences, experiences) and formatted into a context block within a token budget
4. **Respond**: The LLM generates a response with the memory context injected into the system prompt

## Design Principles

The system enforces four invariants at all times:

| # | Invariant | Enforcement |
|---|-----------|-------------|
| 1 | User A's memories are never returned to User B | Row-level security + `user_id` filter on every query |
| 2 | Deleted memories are never retrieved | `deleted = false` filter on every retrieval query |
| 3 | Retrieval failure never blocks a response | Try-catch with fallback to memoryless response |
| 4 | Every memory carries provenance | `source` JSONB field + append-only audit log |

## Why Not Just Vector Search?

| Approach | Store Everything + Vector Search | This System |
|----------|--------------------------------|-------------|
| Write gate | None. Everything is stored | LLM evaluates utility before storing |
| Deduplication | None. Duplicates accumulate | Evaluator checks against existing memories |
| Retrieval | Vector similarity only | Hybrid: vector + keyword, merged and ranked |
| Ranking | Raw similarity score | 4-factor weighted score (semantic, recency, frequency, importance) |
| Lifecycle | Memories persist forever | Decay reduces weight over time. Reflection consolidates old memories |
| Provenance | No tracking | Source metadata + audit log on every operation |

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI | Async REST API with dependency injection |
| Database | PostgreSQL 15 + pgvector | Structured data + vector similarity search |
| ORM | SQLAlchemy (async) + asyncpg | Async database access with connection pooling |
| Cache | Redis | Session memory and caching (optional, graceful degradation) |
| LLM (primary) | OpenAI (gpt-4o-mini, gpt-4o) | Extraction, evaluation, response generation |
| LLM (fallback) | OpenRouter (free models) | Automatic failover when primary quota exhausted |
| Embeddings | text-embedding-3-small (1536d) | Vector representation for semantic search |
| Frontend | Next.js 14 + Tailwind CSS | Dashboard, memory browser, chat interface |
| Icons | Lucide React | UI iconography |
| Containerization | Docker + Docker Compose | Local development stack |
| Cloud | Google Cloud (Cloud Run, Cloud SQL) | Production deployment |

## Repository Structure

```
backend/
  core/           # Abstract interfaces: MemoryEngine, WorkflowEngine, StorageBackend, LLMClient
  models/         # Pydantic schemas and enums (MemoryRecord, ConversationRequest/Response)
  config/         # Application settings via pydantic-settings (all env-driven)
  database/       # SQLAlchemy ORM models, async connection pool, repository layer
  capture/        # Write gate: Extractor (LLM) + Evaluator (LLM)
  store/          # PgVectorStore (implements StorageBackend), WriteService, Redis session store
  retrieve/       # HybridRetriever (vector + keyword), RankingService, GraphRetriever
  context/        # ContextComposer (token-budgeted memory formatting)
  orchestrator/   # SequentialWorkflowEngine, state management, node functions
  memory/         # MemoryService (high-level write + read path orchestration)
  agents/         # ReflectionAgent, BaseAgent, typed contracts
  tools/          # ConcreteLLMClient, ModelRouter, EmbeddingService, PIIFilter
  jobs/           # DecayJob, ReflectionJob (background)
  evaluation/     # GoldenDataset, RetrievalMetrics, MemoryJudge, RegressionGate
  api/            # REST routers: /health, /api/v1/memories, /api/v1/conversations
  auth/           # User ID extraction (header-based, JWT planned)
  prompts/        # Versioned prompt templates (extraction, evaluation, response)
  main.py         # FastAPI entry point with lifespan management

frontend/
  src/app/        # Next.js 14 pages (dashboard, memories, conversations, health)
  src/components/ # React components (ChatInterface, MemoryCard, MemoryEditor)
  src/lib/        # API client and TypeScript types

tests/            # 9-phase test suite covering foundation through concurrent workflows
fixtures/         # Golden retrieval dataset (5 test cases)
scripts/          # Database migrations (001-init.sql)
docs/             # ADRs, future work documentation, screenshots
```

## Engineering Decisions

### ADR-001: PostgreSQL + pgvector over dedicated vector databases

A single PostgreSQL instance handles both structured queries (user isolation, type filtering, full-text search) and vector search (cosine similarity on embeddings). This eliminates the operational overhead of a second data store. Row-level security enforces user isolation at the database level. The `StorageBackend` abstract interface allows swapping to Pinecone or Weaviate if vector query volume exceeds single-node Postgres capacity.

### ADR-002: Modular monolith architecture

15 modules with inward-only dependencies. No circular imports. Each module has a clear responsibility and communicates through typed interfaces. This avoids microservice overhead while maintaining clean boundaries that can be split later.

### ADR-003: Sequential workflow engine (LangGraph deferred)

The write and read paths are linear pipelines (extract -> evaluate -> store, retrieve -> rank -> compose -> respond). A sequential async engine is functionally equivalent to a graph engine for linear flows. The `WorkflowEngine` abstract interface allows swapping to LangGraph or Temporal when the pipeline becomes non-linear.

### ADR-004: Model routing by task type

Different tasks have different requirements. Extraction and evaluation use gpt-4o-mini (cheap, reliable structured output). Response generation uses gpt-4o (higher quality). Embedding uses text-embedding-3-small. All model assignments are overridable via environment variables.

## Evaluation and Quality

### Test Suite

9 test phases covering progressive validation:

| Phase | Focus | Coverage |
|-------|-------|----------|
| 1 | Foundation | Imports, dependency direction, abstract interfaces, models |
| 2 | Frontend contract | Memory CRUD shapes, health endpoint format |
| 3 | Backend CRUD | User isolation (Invariant 1), deleted exclusion (Invariant 2), audit logging |
| 4 | Orchestration | Write + read paths, extraction -> evaluation -> store |
| 5 | Retrieval quality | Hybrid retrieval, ranking formula, deduplication |
| 6 | Advanced features | Decay job, reflection agent, PII filter, conversation endpoint |
| 7 | Golden dataset | Regression gate with baseline precision/recall/latency |
| 8 | Graph retrieval | 1-hop memory edges, related memories |
| 9 | Concurrent workflows | Multi-user isolation, state management, error recovery |

### Golden Dataset

5 retrieval test cases in `fixtures/golden_retrieval.json` with expected contents and types. Used by the regression gate to prevent quality degradation across deployments.

### Metrics

- Precision, recall, F1 for retrieval quality
- Mean reciprocal rank (MRR)
- LLM-as-judge for extraction correctness (hallucination detection, missed facts)

## Quick Start

### With Docker (local development)

```bash
git clone https://github.com/vinodwaghmare/chat-memory-system.git
cd chat-memory-system
cp .env.example .env
# Add your OPENAI_API_KEY to .env

docker compose -f docker-compose.dev.yml up --build
```

The API will be available at `http://localhost:8001`. Interactive docs at `http://localhost:8001/docs`.

### Without Docker

```bash
pip install -e ".[dev]"

# Start PostgreSQL with pgvector and Redis separately, then:
uvicorn backend.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard at `http://localhost:3000`.

### Test the API

```bash
# Send a message
curl -X POST http://localhost:8001/api/v1/conversations/message \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"message": "I prefer Python and I build AI systems.", "conversation_id": "test-001"}'

# List stored memories
curl http://localhost:8001/api/v1/memories \
  -H "X-User-ID: 550e8400-e29b-41d4-a716-446655440000"
```

## Roadmap

### Implemented (Phases 0-9)

- [x] Cognitive design: classification taxonomy, 10-question framework
- [x] System architecture: module graph, ADRs, dependency hierarchy
- [x] Backend API: CRUD endpoints, database repository
- [x] LLM integration: extractor, evaluator, model router
- [x] Memory architecture: pgvector store, hybrid retrieval, weighted ranking
- [x] Workflow orchestration: sequential write/read paths
- [x] Tooling: PII filter, user memory tools
- [x] Multi-agent: reflection agent, decay job, typed contracts
- [x] Evaluation: golden dataset, regression gate, LLM judge
- [x] Frontend: Next.js dashboard, memory browser, chat interface
- [x] Production deployment: Cloud Run, Cloud SQL, OpenRouter fallback

### Planned (Phases 10-20)

- [ ] Observability: Prometheus metrics, OpenTelemetry traces, Grafana dashboards
- [ ] Security: JWT authentication, encryption at rest, Microsoft Presidio PII detection
- [ ] Reliability: Circuit breakers, idempotency keys, dead letter queues
- [ ] Infrastructure: Auto-scaling, multi-region deployment
- [ ] Data engineering: ETL pipelines, data lake integration
- [ ] Governance: Memory retention policies, compliance framework
- [ ] CI/CD: Automated testing pipeline, deployment gates
- [ ] HITL workflows: Human-in-the-loop memory correction
- [ ] Continuous learning: Feedback loops, model fine-tuning

Half-built hooks for Phases 10-12 are documented in [docs/FUTURE_WORK.md](docs/FUTURE_WORK.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and pull request guidelines.

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
