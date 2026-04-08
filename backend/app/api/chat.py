import time
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runner import run_agent
from app.agent.state import Citation
from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.db.audit import log_interaction
from app.db.engine import get_db
from app.db.models import Message, Session

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    session_id: str | None = None


class CitationResponse(BaseModel):
    doc_name: str
    section: str
    url: str
    chunk_text: str
    last_updated: str = ""


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    citations: list[CitationResponse] = []
    requires_confirmation: bool = False
    pending_ticket: dict | None = None
    latency_ms: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatResponse:
    start = time.monotonic()

    # Load or create session
    session_id = request.session_id or str(uuid.uuid4())
    session = await _get_or_create_session(db, session_id, current_user.user_id, request.message)

    # Load message history for this session
    history = await _load_message_history(db, session_id)

    # Persist the user message
    user_msg = Message(
        session_id=uuid.UUID(session_id),
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    # Invoke the agent
    result = await run_agent(
        session_id=session_id,
        user_message=request.message,
        user_context=current_user,
        message_history=history,
    )

    # Persist the assistant message
    assistant_msg = Message(
        session_id=uuid.UUID(session_id),
        role="assistant",
        content=result["content"],
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    # Dispatch audit log as background task
    background_tasks.add_task(
        log_interaction,
        db=db,
        user_id=current_user.user_id,
        query_text=request.message,
        session_id=uuid.UUID(session_id),
        tools_invoked=result.get("tool_calls"),
        response_summary=result["content"],
        latency_ms=result["latency_ms"],
    )

    citations = [
        CitationResponse(
            doc_name=c.doc_name if isinstance(c, Citation) else c.get("doc_name", ""),
            section=c.section if isinstance(c, Citation) else c.get("section", ""),
            url=c.url if isinstance(c, Citation) else c.get("url", ""),
            chunk_text=c.chunk_text if isinstance(c, Citation) else c.get("chunk_text", ""),
            last_updated=c.last_updated if isinstance(c, Citation) else c.get("last_updated", ""),
        )
        for c in result.get("citations", [])
    ]

    return ChatResponse(
        session_id=session_id,
        message_id=str(assistant_msg.id),
        content=result["content"],
        citations=citations,
        requires_confirmation=result.get("awaiting_confirmation", False),
        pending_ticket=result.get("pending_jira_ticket"),
        latency_ms=result["latency_ms"],
    )


async def _get_or_create_session(
    db: AsyncSession, session_id: str, user_id: str, first_message: str
) -> Session:
    from sqlalchemy import select
    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
    session = result.scalar_one_or_none()
    if session is None:
        title = first_message[:80]
        session = Session(id=uuid.UUID(session_id), user_id=user_id, title=title)
        db.add(session)
        await db.flush()
    return session


async def _load_message_history(db: AsyncSession, session_id: str) -> list[dict]:
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.session_id == uuid.UUID(session_id))
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages if m.role in ("user", "assistant")]
