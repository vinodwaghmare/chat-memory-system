"""Decay job — reduces memory weights over time, archives below threshold.

Runs off the request path on a configurable schedule.
Reinforcement: when a memory is retrieved and used, its weight is boosted.
"""

from __future__ import annotations

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import get_settings
from backend.database.models import MemoryORM

logger = logging.getLogger(__name__)


class DecayJob:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def run(self) -> dict:
        cfg = get_settings()
        decay_factor = cfg.decay_factor
        threshold = cfg.archive_threshold

        stmt = select(MemoryORM).where(
            MemoryORM.deleted == False,  # noqa: E712
            MemoryORM.archived == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        decayed = 0
        archived = 0
        for row in rows:
            row.weight = round(row.weight * decay_factor, 6)
            decayed += 1
            if row.weight < threshold:
                row.archived = True
                archived += 1

        await self._session.flush()

        logger.info("Decay job: decayed=%d archived=%d", decayed, archived)
        return {"decayed": decayed, "archived": archived}
