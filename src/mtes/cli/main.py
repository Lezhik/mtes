"""MTES CLI application per SRS §4–9."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from mtes.cli import exit_codes
from mtes.cli.context import CliContext
from mtes.core.bootstrap_pipeline import BootstrapPipeline, InMemoryBootstrapStageStore
from mtes.core.bootstrap_stages import BOOTSTRAP_STAGE_ORDER
from mtes.core.daemon_service import DaemonService
from mtes.shared.exceptions import MtesError

app = typer.Typer(
    name="mtes",
    help="Mutation-Traceable Evolutionary Synthesis operator CLI.",
    no_args_is_help=True,
)


def _get_context(ctx: typer.Context) -> CliContext:
    context = ctx.obj
    if not isinstance(context, CliContext):
        return CliContext()
    return context


def _emit(context: CliContext, payload: dict[str, object]) -> None:
    if context.json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
    elif context.verbose or context.verbose_sanitized:
        typer.echo(str(payload))


def _run_async(coro: object) -> None:
    asyncio.run(coro)  # type: ignore[arg-type]


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: Annotated[
        Path | None,
        typer.Option("--config", help="Path to MTES YAML configuration."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose operator output.")] = False,
    verbose_sanitized: Annotated[
        bool,
        typer.Option("--verbose-sanitized", help="Verbose output with secrets redacted."),
    ] = False,
) -> None:
    ctx.obj = CliContext(
        config_path=config,
        json_output=json_output,
        verbose=verbose,
        verbose_sanitized=verbose_sanitized,
    )


@app.command("bootstrap")
def bootstrap_command(
    ctx: typer.Context,
    force: Annotated[bool, typer.Option("--force", help="Re-run all bootstrap stages.")] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print bootstrap stage order without executing handlers."),
    ] = False,
) -> None:
    """Run bootstrap pipeline stages."""
    context = _get_context(ctx)
    if dry_run:
        stages = [stage.value for stage in BOOTSTRAP_STAGE_ORDER]
        _emit(context, {"dry_run": True, "stages": stages})
        return
    raise typer.Exit(exit_codes.BOOTSTRAP_FAILED)


@app.command("generate")
def generate_command(ctx: typer.Context) -> None:
    """Generate a single candidate (wired in later phases)."""
    _get_context(ctx)
    raise typer.Exit(exit_codes.GENERAL_ERROR)


@app.command("evolution")
def evolution_command(
    ctx: typer.Context,
    action: Annotated[str, typer.Argument(help="pause | resume | stop | reset")],
    operator_id: Annotated[str, typer.Option("--operator-id", help="Operator identity.")] = "",
    operator_token: Annotated[
        str | None,
        typer.Option("--operator-token", help="Operator authentication token."),
    ] = None,
) -> None:
    """Control evolution lifecycle."""
    context = _get_context(ctx)
    from mtes.core.operator_auth import OperatorAuthService

    auth = OperatorAuthService.from_environment()
    try:
        auth.authenticate(operator_id=operator_id, presented_token=operator_token)
        auth.audit_admin_command(operator_id=operator_id, command=f"evolution {action}")
    except MtesError:
        raise typer.Exit(exit_codes.GENERAL_ERROR) from None
    _emit(context, {"evolution_action": action, "status": "accepted"})


@app.command("telegram")
def telegram_command(ctx: typer.Context) -> None:
    """Telegram integration commands (Phase 11)."""
    _get_context(ctx)
    raise typer.Exit(exit_codes.TELEGRAM_CONNECTION_FAILED)


@app.command("report")
def report_command(ctx: typer.Context) -> None:
    """Generate operational reports (Phase 12)."""
    _get_context(ctx)
    raise typer.Exit(exit_codes.GENERAL_ERROR)


@app.command("daemon")
def daemon_command(
    ctx: typer.Context,
    action: Annotated[str, typer.Argument(help="start | stop")],
) -> None:
    """Start or stop background daemon."""
    context = _get_context(ctx)

    async def _start_daemon() -> None:
        daemon = DaemonService()
        daemon.register_signal_handlers()
        await daemon.start([(1.0, _noop_job)])

    async def _noop_job() -> None:
        if context.verbose:
            _emit(context, {"daemon": "heartbeat"})

    if action == "start":
        try:
            _run_async(_start_daemon())
        except KeyboardInterrupt:
            raise typer.Exit(exit_codes.SUCCESS) from None
    raise typer.Exit(exit_codes.GENERAL_ERROR)


if __name__ == "__main__":
    app()
