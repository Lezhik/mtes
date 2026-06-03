"""Tests for configuration loading."""

from pathlib import Path

import pytest

from mtes.shared.config import load_config
from mtes.shared.exceptions import ConfigurationError

EXAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "config" / "config.example.yaml"


def test_load_example_config() -> None:
    config = load_config(EXAMPLE_CONFIG)
    assert config.database.connection_string.startswith("mongodb://")
    assert config.daemon.worker_count == 1
    assert config.monitoring.health_port == 8080
    assert config.metrics.locality_measurement_interval == 100
    assert config.security.operator_auth_source == "environment"


def test_missing_file_raises_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(tmp_path / "missing.yaml")


def test_invalid_root_raises_configuration_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.yaml"
    invalid_path.write_text("not a mapping\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="YAML mapping"):
        load_config(invalid_path)


def test_missing_section_raises_configuration_error(tmp_path: Path) -> None:
    partial_path = tmp_path / "partial.yaml"
    partial_path.write_text("database:\n  connection_string: mongodb://localhost\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="daemon"):
        load_config(partial_path)
