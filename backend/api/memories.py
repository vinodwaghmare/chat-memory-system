"""Memory CRUD endpoints.

All endpoints enforce Invariant 1 (user isolation) via get_current_user_id dependency.
All queries enforce Invariant 2 (deleted exclusion) via repository filters.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user_id
from backend.database.postgres import get_db
from backend.database.repository import MemoryRepository
from backend.models.enums import MemoryType
from backend.models.memory import MemoryCreate, MemoryRecord, MemoryUpdate

router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


def _get_repo(session: AsyncSession = Depends(get_db)) -> MemoryRepository:
    return MemoryRepository(session)


@router.post("", status_code=201, response_model=MemoryRecord)
async def create_memory(
    body: MemoryCreate,
    user_id: str = Depends(get_current_user_id),
    repo: MemoryRepository = Depends(_get_repo),
    session: AsyncSession = Depends(get_db),
) -> MemoryRecord:
    record = await repo.create_memory(
        user_id=user_id,
        memory_type=body.type,
        content=body.content,
        importance=body.importance,
        confidence=body.confidence,
        source=body.source,
    )
    await repo.write_audit_log(user_id, "create", record.id, {"content": body.content})
    await session.commit()
    return record


@router.get("", response_model=list[MemoryRecord])
async def list_memories(
    type: MemoryType | None = None,
    offset: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    repo: MemoryRepository = Depends(_get_repo),
) -> list[MemoryRecord]:
    return await repo.list_memories(
        user_id=user_id,
        memory_type=type,
        offset=offset,
        limit=limit,
    )


@router.get("/{memory_id}", response_model=MemoryRecord)
async def get_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    repo: MemoryRepository = Depends(_get_repo),
) -> MemoryRecord:
    record = await repo.get_memory(memory_id, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return record


@router.put("/{memory_id}", response_model=MemoryRecord)
async def update_memory(
    memory_id: str,
    body: MemoryUpdate,
    user_id: str = Depends(get_current_user_id),
    repo: MemoryRepository = Depends(_get_repo),
    session: AsyncSession = Depends(get_db),
) -> MemoryRecord:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    record = await repo.update_memory(memory_id, user_id, updates)
    if record is None:
        raise HTTPException(status_code=404, detail="Memory not found")

    await repo.write_audit_log(user_id, "update", memory_id, updates)
    await session.commit()
    return record


@router.delete("/{memory_id}", status_code=200)
async def delete_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    repo: MemoryRepository = Depends(_get_repo),
    session: AsyncSession = Depends(get_db),
) -> dict:
    deleted = await repo.soft_delete(memory_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")

    await repo.write_audit_log(user_id, "delete", memory_id)
    await session.commit()
    return {"status": "deleted", "memory_id": memory_id}
