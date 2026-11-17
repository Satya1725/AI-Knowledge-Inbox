"""JSON logging with a per-request id.

Usage:  logger.info("item ingested", extra={"item_id": item_id, "chunks": 4})
Every key passed in `extra` ends up as a top-level field in the log line.
"""

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Attributes every LogRecord has; anything else came from `extra=`.
_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id:
            entry["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                entry[key] = value

        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # We log requests ourselves (see main.py), so silence uvicorn's access log.
    logging.getLogger("uvicorn.access").disabled = True
    # The HTTP clients used by the AI SDKs are very chatty at INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)
