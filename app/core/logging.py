"""Structured (JSON) logging configuration.

Production services should emit machine-parseable logs so they can be
shipped to a log aggregator (CloudWatch, Datadog, ELK, ...) and queried by
field instead of grepped by hand. This module configures the stdlib root
logger with a JSON formatter; call ``configure_logging()`` once at process
startup (API and worker both do this).
"""

import json
import logging
import sys
from datetime import UTC, datetime

from app.core.config import get_settings

# Attributes present on every stdlib LogRecord. Anything else attached via
# `extra={...}` is application-specific context and gets surfaced as-is.
_RESERVED_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime", "taskName",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())

    # Uvicorn's own access logger duplicates what our request-logging
    # middleware already emits (with richer, structured fields), so quiet it.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
