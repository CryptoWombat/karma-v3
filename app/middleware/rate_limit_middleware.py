"""Rate limiting middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings
from app.core.rate_limit import check_rate_limit


def _get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_limit_for_path(path: str) -> tuple[str, int]:
    """Return (key_prefix, limit) for path."""
    s = get_settings()
    if path.startswith("/v1/admin"):
        return "admin", s.rate_limit_admin
    if path.startswith("/v1/validator"):
        return "validator", s.rate_limit_validator
    if path in ("/v1/stats", "/health", "/"):
        return "public", s.rate_limit_public
    return "user", s.rate_limit_user


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting by client IP and path tier."""

    async def dispatch(self, request: Request, call_next):
        if get_settings().rate_limit_disabled:
            return await call_next(request)
        path = request.scope.get("path", "")
        tier, limit = _get_limit_for_path(path)
        ip = _get_client_ip(request)
        key = f"{tier}:{ip}"
        if not check_rate_limit(key, limit):
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit_exceeded", "retry_after": 60},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
