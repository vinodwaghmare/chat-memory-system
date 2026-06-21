"""Shared test fixtures.

Uses SQLite in-memory with aiosqlite and StaticPool — no real Postgres needed.
StaticPool ensures all connections share the same in-memory database.
Creates a separate FastAPI app for testing (no lifespan side effects).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import backend.database.models  # noqa: F401 — registers ORM classes with Base.metadata
from backend.database.postgres import Base


TEST_USER_A = str(uuid.uuid4())
TEST_USER_B = str(uuid.uuid4())


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


def _build_test_app() -> FastAPI:
    """Build a minimal FastAPI app with the same routers but no lifespan."""
    from backend.api.conversations import router as conversations_router
    from backend.api.health import router as health_router
    from backend.api.memories import router as memories_router

    test_app = FastAPI(title="Test App")
    test_app.include_router(health_router)
    test_app.include_router(memories_router)
    test_app.include_router(conversations_router)
    return test_app


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    from backend.database.postgres import get_db

    test_app = _build_test_app()
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
