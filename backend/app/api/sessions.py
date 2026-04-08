import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.core.errors import ForbiddenError, NotFoundError
from app.db.engine import get_db
from app.db.models import Session

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["sessions"])


class SessionSummary(BaseModel):
    id: str
    title: str | None
    created_at: str
    updated_at: str


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SessionSummary]:
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.user_id)
        .order_by(Session.updated_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return [
        SessionSummary(
            id=str(s.id),
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
    session = result.scalar_one_or_none()

    if session is None:
        raise NotFoundError("Session not found")
    if session.user_id != current_user.user_id:
        raise ForbiddenError("Cannot delete another user's session")

    await db.delete(session)
    await db.commit()
