"""
app/routers/chat.py — Chat endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatHistoryItem, ChatRequest, ChatResponse
from app.schemas.common import PaginatedResponse
from app.services.chat_service import ChatService

router = APIRouter()
_svc   = ChatService()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    req:     ChatRequest,
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    return await _svc.process(req.message, req.session_id, current["id"], db)


@router.get("/history", response_model=PaginatedResponse[ChatHistoryItem])
async def chat_history(
    session_id: str = Query("default"),
    page:       int = Query(1, ge=1),
    page_size:  int = Query(20, ge=1, le=100),
    current:    dict = Depends(get_current_user),
    db:         AsyncSession = Depends(get_db),
):
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current["id"], ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    all_m  = result.scalars().all()
    total  = len(all_m)
    start  = (page - 1) * page_size
    items  = list(all_m[start : start + page_size])
    return PaginatedResponse.build(
        [ChatHistoryItem.model_validate(m) for m in items],
        total, page, page_size
    )


@router.delete("/history", status_code=204)
async def clear_history(
    session_id: str = Query("default"),
    current:    dict = Depends(get_current_user),
    db:         AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(ChatMessage).where(
            ChatMessage.user_id == current["id"],
            ChatMessage.session_id == session_id
        )
    )
