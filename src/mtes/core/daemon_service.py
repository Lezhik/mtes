"""Background daemon with graceful shutdown per SRS §5 and §14."""

import asyncio
import os
import signal
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class DaemonStateRepository(Protocol):
    async def save_daemon_state(self, *, running: bool, pid: int) -> None:
        ...

    async def load_daemon_state(self) -> dict[str, object] | None:
        ...


ScheduledJob = Callable[[], Awaitable[None]]


@dataclass
class DaemonService:
    """Run scheduled async jobs with PID file and signal-aware shutdown."""

    pid_file: Path = Path("runtime/mtes.pid")
    state_repository: DaemonStateRepository | None = None
    _running: bool = False
    _shutdown_requested: bool = False
    _tasks: list[asyncio.Task[None]] = field(default_factory=list)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    def register_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self.request_shutdown)
            except NotImplementedError:
                # Windows may not support all signals in add_signal_handler.
                signal.signal(sig, lambda _signum, _frame: self.request_shutdown())

    def request_shutdown(self) -> None:
        self._shutdown_requested = True

    async def start(self, jobs: list[tuple[float, ScheduledJob]]) -> None:
        """Start daemon, schedule interval jobs (seconds), and persist PID."""
        if self._running:
            return
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(os.getpid()), encoding="utf-8")
        self._running = True
        self._shutdown_requested = False
        if self.state_repository is not None:
            await self.state_repository.save_daemon_state(running=True, pid=0)
        for interval_seconds, job in jobs:
            self._tasks.append(asyncio.create_task(self._run_interval(interval_seconds, job)))
        await self._wait_for_shutdown()
        await self.stop()

    async def _run_interval(self, interval_seconds: float, job: ScheduledJob) -> None:
        while not self._shutdown_requested:
            await job()
            await asyncio.sleep(interval_seconds)

    async def _wait_for_shutdown(self) -> None:
        while not self._shutdown_requested:
            await asyncio.sleep(0.2)

    async def stop(self) -> None:
        """Graceful shutdown: cancel tasks and remove PID file."""
        self._shutdown_requested = True
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._running = False
        if self.pid_file.exists():
            self.pid_file.unlink()
        if self.state_repository is not None:
            await self.state_repository.save_daemon_state(running=False, pid=0)
