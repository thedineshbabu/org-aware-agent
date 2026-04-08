"""
Audit logging — Phase 1 stub.
Phase 5 completes PII masking via core.pii_masker.
"""
import uuid
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentAuditLog

logger = structlog.get_logger(__name__)


async def log_interaction(
    db: AsyncSession,
    user_id: str,
    query_text: str,
    session_id: uuid.UUID | None = None,
    tools_invoked: list[dict] | None = None,
    response_summary: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """
    Persist one agent interaction to the audit log.
    Called as a BackgroundTask — failures are logged but do not affect the response.
    """
    try:
        # Phase 1: minimal masking — replace email-like strings
        masked_query = _mask_emails(query_text)

        entry = AgentAuditLog(
            session_id=session_id,
            user_id=user_id,
            query_text=masked_query,
            tools_invoked=tools_invoked,
            response_summary=response_summary[:500] if response_summary else None,
            latency_ms=latency_ms,
        )
        db.add(entry)
        await db.commit()
    except Exception:
        logger.exception("audit_log_failed", user_id=user_id)


def _mask_emails(text: str) -> str:
    """Simple regex email masker — replaced by pii_masker.py in Phase 5."""
    import re
    return re.sub(r"[\w.+-]+@[\w.-]+\.\w+", "[email]", text)
