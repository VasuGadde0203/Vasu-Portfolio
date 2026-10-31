from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.security import enforce_rate_limit
from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    dependencies=[Depends(enforce_rate_limit)],
)
async def chat(
    body: ChatRequest,
    session: Session = Depends(get_session),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    # The service is synchronous (SQLAlchemy + OpenAI SDK); run it off the event loop.
    return await run_in_threadpool(service.answer, session, body)
