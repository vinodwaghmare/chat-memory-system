from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.config.settings import get_settings

router = APIRouter(tags=["ops"])

try:
    APP_VERSION = version("chat-memory-system")
except PackageNotFoundError:
    APP_VERSION = "dev"


@router.get("/health/live")
async def liveness() -> dict:
    return {"status": "ok", "version": APP_VERSION}


@router.get("/health")
async def health_check() -> JSONResponse:
    cfg = get_settings()

    postgres_status = await _check_postgres()
    redis_status = await _check_redis()

    hard_ok = postgres_status == "ok" and redis_status == "ok"
    overall = "ok" if hard_ok else "degraded"

    body = {
        "status": overall,
        "version": APP_VERSION,
        "env": cfg.app_env,
        "services": {
            "postgres": postgres_status,
            "redis": redis_status,
        },
    }

    http_status = 200 if overall == "ok" else 503
    return JSONResponse(content=body, status_code=http_status)


async def _check_postgres() -> str:
    try:
        from sqlalchemy import text

        from backend.database.postgres import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"


async def _check_redis() -> str:
    try:
        import redis.asyncio as aioredis

        from backend.config.settings import get_settings

        cfg = get_settings()
        r = aioredis.from_url(cfg.redis_url)
        await r.ping()
        await r.aclose()
        return "ok"
    except Exception:
        return "unavailable"
