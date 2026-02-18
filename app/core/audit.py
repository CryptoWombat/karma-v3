"""Audit logging for admin actions."""
import logging

from app.middleware.request_logging_middleware import request_id_ctx


def log_admin_action(action: str, detail: dict) -> None:
    """Log admin action as structured audit event."""
    logger = logging.getLogger("app.audit")
    extra = {
        "audit": True,
        "audit_action": action,
        "audit_detail": detail,
    }
    try:
        extra["request_id"] = request_id_ctx.get()
    except LookupError:
        pass
    logger.info(f"admin_action:{action}", extra=extra)
