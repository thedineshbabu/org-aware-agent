import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "AUTH_ERROR", status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, "NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ToolError(Exception):
    """Raised inside LangGraph tools — caught by the agent graph, not the HTTP layer."""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"[{tool_name}] {message}")


class ToolPermissionError(ToolError):
    """Raised when a user invokes a tool they do not have RBAC permission for."""
    pass


def _error_body(message: str, code: str, request_id: str) -> dict[str, Any]:
    return {"error": message, "code": code, "request_id": request_id}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.warning("app_error", code=exc.code, message=exc.message, request_id=request_id)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.message, exc.code, request_id),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.exception("unhandled_error", request_id=request_id)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("Internal server error", "INTERNAL_ERROR", request_id),
        )
