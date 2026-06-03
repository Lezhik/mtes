"""Structured logging setup."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonLineFormatter(logging.Formatter):
    """Emit one JSON object per log line per AGENTS.md logging schema."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        for field_name in ("operation", "genome_id", "workflow_stage", "generation_id"):
            value = getattr(record, field_name, None)
            if value is not None:
                payload[field_name] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    *,
    level: int = logging.INFO,
    json_lines: bool = True,
) -> None:
    """Configure root logger for CLI and daemon processes."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    if json_lines:
        handler.setFormatter(JsonLineFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
