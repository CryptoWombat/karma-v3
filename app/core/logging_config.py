"""Structured JSON logging configuration."""
import json
import logging
import sys
import uuid
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "request_id"):
            data["request_id"] = record.request_id
        if hasattr(record, "path"):
            data["path"] = record.path
        if hasattr(record, "method"):
            data["method"] = record.method
        if hasattr(record, "status_code"):
            data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            data["duration_ms"] = record.duration_ms
        if hasattr(record, "audit"):
            data["audit"] = record.audit
        if hasattr(record, "audit_action"):
            data["audit_action"] = record.audit_action
        if hasattr(record, "audit_detail"):
            data["audit_detail"] = record.audit_detail
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with JSON formatter."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    for h in root.handlers[:]:
        root.removeHandler(h)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JSONFormatter())
    root.addHandler(h)


def get_logger(name: str) -> logging.Logger:
    """Get logger for module."""
    return logging.getLogger(name)
