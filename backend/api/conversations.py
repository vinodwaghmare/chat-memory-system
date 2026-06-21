"""Conversation endpoint — sends a message, triggers write + read paths."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user_id
from backend.database.postgres import get_db
from backend.memory.service import MemoryService
from backend.models.conversation import ConversationRequest, ConversationResponse
from backend.retrieve.hybrid_retriever import HybridRetriever
from backend.retrieve.ranking import RankingService
from backend.store.pgvector_store import PgVectorStore
from backend.tools.llm_client import ConcreteLLMClient

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _build_memory_service(session: AsyncSession) -> MemoryService:
    llm = ConcreteLLMClient()
    store = PgVectorStore(session)
    retriever = HybridRetriever(
        store=store,
        llm_client=llm,
        ranking_service=RankingService(),
    )
    return MemoryService(llm_client=llm, store=store, retriever=retriever)


@router.post("/message", response_model=ConversationResponse)
async def send_message(
    body: ConversationRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    service = _build_memory_service(session)
    response = await service.process_message(
        user_id=user_id,
        message=body.message,
        conversation_id=body.conversation_id,
    )
    await session.commit()
    return response
