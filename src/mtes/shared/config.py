"""YAML configuration loading and validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mtes.shared.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    connection_string: str


@dataclass(frozen=True, slots=True)
class DaemonConfig:
    worker_count: int
    generation_queue_size: int
    publication_queue_size: int
    resume_threshold: int


@dataclass(frozen=True, slots=True)
class MonitoringConfig:
    health_port: int
    metrics_port: int


@dataclass(frozen=True, slots=True)
class MetricsConfig:
    locality_measurement_interval: int


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    evolution_confirmation_required: bool
    reset_requires_confirmation: bool
    operator_auth_source: str


@dataclass(frozen=True, slots=True)
class MtesConfig:
    """Root application configuration per SRS §12."""

    database: DatabaseConfig
    daemon: DaemonConfig
    monitoring: MonitoringConfig
    metrics: MetricsConfig
    security: SecurityConfig


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigurationError(f"Missing or invalid config section: {key}")
    return value


def _require_str(section: dict[str, Any], key: str, path: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"Missing or invalid {path}.{key}")
    return value


def _require_int(section: dict[str, Any], key: str, path: str) -> int:
    value = section.get(key)
    if not isinstance(value, int):
        raise ConfigurationError(f"Missing or invalid {path}.{key}")
    return value


def _require_bool(section: dict[str, Any], key: str, path: str) -> bool:
    value = section.get(key)
    if not isinstance(value, bool):
        raise ConfigurationError(f"Missing or invalid {path}.{key}")
    return value


def parse_config(data: dict[str, Any]) -> MtesConfig:
    """Parse a raw YAML mapping into a validated MtesConfig."""
    database_section = _require_mapping(data, "database")
    daemon_section = _require_mapping(data, "daemon")
    monitoring_section = _require_mapping(data, "monitoring")
    metrics_section = _require_mapping(data, "metrics")
    security_section = _require_mapping(data, "security")

    return MtesConfig(
        database=DatabaseConfig(
            connection_string=_require_str(database_section, "connection_string", "database"),
        ),
        daemon=DaemonConfig(
            worker_count=_require_int(daemon_section, "worker_count", "daemon"),
            generation_queue_size=_require_int(
                daemon_section, "generation_queue_size", "daemon"
            ),
            publication_queue_size=_require_int(
                daemon_section, "publication_queue_size", "daemon"
            ),
            resume_threshold=_require_int(daemon_section, "resume_threshold", "daemon"),
        ),
        monitoring=MonitoringConfig(
            health_port=_require_int(monitoring_section, "health_port", "monitoring"),
            metrics_port=_require_int(monitoring_section, "metrics_port", "monitoring"),
        ),
        metrics=MetricsConfig(
            locality_measurement_interval=_require_int(
                metrics_section, "locality_measurement_interval", "metrics"
            ),
        ),
        security=SecurityConfig(
            evolution_confirmation_required=_require_bool(
                security_section, "evolution_confirmation_required", "security"
            ),
            reset_requires_confirmation=_require_bool(
                security_section, "reset_requires_confirmation", "security"
            ),
            operator_auth_source=_require_str(
                security_section, "operator_auth_source", "security"
            ),
        ),
    )


def load_config(path: Path | str) -> MtesConfig:
    """Load and validate configuration from a YAML file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigurationError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file)

    if not isinstance(raw, dict):
        raise ConfigurationError("Config root must be a YAML mapping")

    return parse_config(raw)
