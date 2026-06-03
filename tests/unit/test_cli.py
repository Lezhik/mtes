"""CLI integration tests with Typer CliRunner."""

import pytest
from typer.testing import CliRunner

from mtes.cli import exit_codes
from mtes.cli.main import app

runner = CliRunner()


def test_bootstrap_dry_run_lists_stages() -> None:
    result = runner.invoke(app, ["--json", "bootstrap", "--dry-run"])
    assert result.exit_code == exit_codes.SUCCESS
    assert "infrastructure_validation" in result.stdout


def test_bootstrap_without_handlers_exits_bootstrap_failed() -> None:
    result = runner.invoke(app, ["bootstrap"])
    assert result.exit_code == exit_codes.BOOTSTRAP_FAILED


def test_evolution_unauthenticated_exits_error() -> None:
    result = runner.invoke(app, ["evolution", "pause"])
    assert result.exit_code == exit_codes.GENERAL_ERROR


def test_evolution_authenticated_accepts_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MTES_OPERATOR_TOKEN", "secret-token")
    monkeypatch.setenv("MTES_OPERATOR_ALLOW_LIST", "operator-1")
    result = runner.invoke(
        app,
        [
            "--json",
            "evolution",
            "pause",
            "--operator-id",
            "operator-1",
            "--operator-token",
            "secret-token",
        ],
    )
    assert result.exit_code == exit_codes.SUCCESS
    assert "accepted" in result.stdout


def test_report_command_generates_artifacts(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--json", "report"])
    assert result.exit_code == exit_codes.SUCCESS
    assert "json_path" in result.stdout
    reports_dir = tmp_path / "reports"
    assert reports_dir.exists()
    assert any(reports_dir.glob("mtes_report_*.json"))
    assert any(reports_dir.glob("mtes_report_*.html"))


def test_invalid_evolution_action_still_requires_auth() -> None:
    result = runner.invoke(app, ["evolution", "invalid-action"])
    assert result.exit_code == exit_codes.GENERAL_ERROR
