"""FastAPI entry point with lifespan context manager.

Startup connects dependencies best-effort (warn, never crash).
Shutdown disconnects cleanly.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings

try:
    APP_VERSION = version("chat-memory-system")
except PackageNotFoundError:
    APP_VERSION = "dev"

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    logger.info(
        "Chat Memory System starting | version=%s env=%s",
        APP_VERSION,
        cfg.app_env,
    )

    # --- Postgres (best-effort) ---
    try:
        from backend.database.postgres import init_db

        await init_db()
        logger.info("Postgres tables verified/created.")
    except Exception as exc:
        logger.warning("Postgres unavailable at startup: %s", exc)

    # --- Redis (best-effort) ---
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(cfg.redis_url)
        await r.ping()
        await r.aclose()
        logger.info("Redis connection verified.")
    except Exception as exc:
        logger.warning("Redis unavailable at startup: %s", exc)

    yield

    logger.info("Chat Memory System shutting down.")


app = FastAPI(
    title="Chat Memory System",
    description="Production-grade ChatGPT-style memory system",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# --- CORS ---
cors_origins = ["*"] if settings.is_development else [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Routers ---
from backend.api.auth import router as auth_router  # noqa: E402
from backend.api.conversations import router as conversations_router  # noqa: E402
from backend.api.health import router as health_router  # noqa: E402
from backend.api.memories import router as memories_router  # noqa: E402

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(memories_router)
app.include_router(conversations_router)
