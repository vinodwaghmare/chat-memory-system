"""Async PostgreSQL connection pool and session management.

Lazy initialization: the engine is built on first use, not at import time.
This prevents import-time env var requirements and allows tests to override.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config.settings import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    pass


def _build_engine(url: str | None = None) -> AsyncEngine:
    db_url = url or get_settings().database_url
    return create_async_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
    )


def get_engine(url: str | None = None) -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _build_engine(url)
    return _engine


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=engine or get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def init_db(engine: AsyncEngine | None = None) -> None:
    eng = engine or get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")


def reset_engine() -> None:
    """For testing: clear the cached engine and session factory."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
