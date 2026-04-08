import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.engine import get_session_factory

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    """Liveness + readiness check. Verifies DB connectivity."""
    status = {"status": "ok", "checks": {}}

    # Database check
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        status["checks"]["database"] = "ok"
    except Exception as exc:
        logger.warning("health_check_db_failed", error=str(exc))
        status["checks"]["database"] = "error"
        status["status"] = "degraded"

    http_status = 200 if status["status"] == "ok" else 503
    return JSONResponse(content=status, status_code=http_status)
