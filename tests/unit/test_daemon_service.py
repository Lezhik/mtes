"""Daemon graceful shutdown tests."""

import asyncio
from pathlib import Path

import pytest

from mtes.core.daemon_service import DaemonService


@pytest.mark.asyncio
async def test_daemon_starts_schedules_and_stops(tmp_path: Path) -> None:
    pid_file = tmp_path / "mtes.pid"
    daemon = DaemonService(pid_file=pid_file)
    heartbeats = 0

    async def heartbeat_job() -> None:
        nonlocal heartbeats
        heartbeats += 1
        if heartbeats >= 1:
            daemon.request_shutdown()

    task = asyncio.create_task(daemon.start([(0.05, heartbeat_job)]))
    await asyncio.wait_for(task, timeout=2.0)
    assert heartbeats >= 1
    assert not pid_file.exists()
