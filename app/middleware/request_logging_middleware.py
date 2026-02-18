"""Request logging middleware - structured JSON with request_id, latency, status."""
import time
import uuid
import logging
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def _get_request_id(request: Request) -> str:
    """Use X-Request-ID header or generate new."""
    return request.headers.get("x-request-id") or str(uuid.uuid4())


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with request_id, path, method, status, duration."""

    async def dispatch(self, request: Request, call_next):
        request_id = _get_request_id(request)
        request.state.request_id = request_id
        request_id_ctx.set(request_id)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        path = request.scope.get("path", "")
        method = request.scope.get("method", "")
        status = response.status_code
        log_level = logging.WARNING if status >= 400 else logging.INFO
        logger = logging.getLogger("app.request")
        msg = f"{method} {path} {status} {duration_ms:.0f}ms"
        logger.log(
            log_level,
            msg,
            extra={
                "request_id": request_id,
                "path": path,
                "method": method,
                "status_code": status,
                "duration_ms": round(duration_ms, 2),
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
