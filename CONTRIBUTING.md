# Contributing

Thanks for your interest in contributing to Chat Memory System.

## Development Setup

```bash
git clone https://github.com/vinodwaghmare/chat-memory-system.git
cd chat-memory-system
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory (no PostgreSQL required). The test suite covers 9 phases from foundation through concurrent workflows.

### Running Locally

```bash
cp .env.example .env
# Fill in your API keys

# Option A: Docker
docker compose -f docker-compose.dev.yml up --build

# Option B: Manual
# Start PostgreSQL (with pgvector) and Redis separately
uvicorn backend.main:app --reload --port 8001
```

## Code Standards

- **Formatter/Linter**: [Ruff](https://docs.astral.sh/ruff/) with line length 88
- **Type hints**: Required on all function signatures
- **Async**: All database and LLM operations must be async
- **Imports**: Absolute imports only (`from backend.core.exceptions import ...`)

## Architecture Rules

1. Dependencies flow inward: `api` -> `memory` -> `orchestrator` -> `capture/store/retrieve` -> `core`
2. No circular imports between modules
3. Every database query must filter by `user_id` (Invariant 1)
4. Every retrieval query must exclude `deleted = true` (Invariant 2)
5. Retrieval failure must never block a response (Invariant 3)
6. Every memory must carry source metadata (Invariant 4)

## Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Write tests for new functionality
4. Run `ruff check .` and `pytest tests/` before pushing
5. Open a PR with a clear description of what changed and why

## Adding a New Module

1. Create the module directory under `backend/`
2. Add `__init__.py`
3. Define interfaces in `backend/core/` if the module introduces a new abstraction
4. Write tests in `tests/`
5. Update the dependency graph in the README if module boundaries change

## Reporting Issues

Open a GitHub issue with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (Python version, OS, database version)
