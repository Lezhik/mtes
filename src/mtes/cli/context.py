"""Shared CLI runtime context."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CliContext:
    config_path: Path | None = None
    json_output: bool = False
    verbose: bool = False
    verbose_sanitized: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
