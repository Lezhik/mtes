"""Evolution lifecycle FSM per SRS §7.2."""

from dataclasses import dataclass
from typing import Any, Protocol

from mtes.core.bootstrap_report_service import BootstrapReportService
from mtes.shared.exceptions import MtesError
from mtes.shared.types import EvolutionStatus


class InvalidEvolutionTransitionError(MtesError):
    """Raised when an evolution lifecycle transition is not allowed."""


ALLOWED_EVOLUTION_TRANSITIONS: dict[EvolutionStatus, frozenset[EvolutionStatus]] = {
    EvolutionStatus.CREATED: frozenset({EvolutionStatus.RUNNING}),
    EvolutionStatus.RUNNING: frozenset(
        {EvolutionStatus.PAUSED, EvolutionStatus.STOPPING, EvolutionStatus.FAILED}
    ),
    EvolutionStatus.PAUSED: frozenset({EvolutionStatus.RUNNING, EvolutionStatus.STOPPING}),
    EvolutionStatus.STOPPING: frozenset({EvolutionStatus.STOPPED}),
    EvolutionStatus.STOPPED: frozenset({EvolutionStatus.RUNNING, EvolutionStatus.RESETTING}),
    EvolutionStatus.RESETTING: frozenset({EvolutionStatus.CREATED}),
    EvolutionStatus.FAILED: frozenset(),
}


class EvolutionStateRepository(Protocol):
    async def load_evolution_state(self) -> dict[str, Any] | None:
        ...

    async def save_evolution_state(self, *, status: EvolutionStatus, generation_number: int) -> None:
        ...


@dataclass
class EvolutionLifecycleService:
    """Manage evolution lifecycle transitions with optional persistence."""

    evolution_repository: EvolutionStateRepository | None = None
    bootstrap_report_service: BootstrapReportService | None = None
    _status: EvolutionStatus = EvolutionStatus.CREATED
    _generation_number: int = 0
    _pause_requested: bool = False
    _cycle_in_progress: bool = False

    @property
    def status(self) -> EvolutionStatus:
        return self._status

    @property
    def generation_number(self) -> int:
        return self._generation_number

    def can_transition(self, target: EvolutionStatus) -> bool:
        allowed = ALLOWED_EVOLUTION_TRANSITIONS.get(self._status, frozenset())
        return target in allowed

    async def transition_to(self, target: EvolutionStatus) -> EvolutionStatus:
        if not self.can_transition(target):
            raise InvalidEvolutionTransitionError(
                f"Transition {self._status.value} -> {target.value} is not allowed"
            )
        if target == EvolutionStatus.RUNNING and self.bootstrap_report_service is not None:
            await self.bootstrap_report_service.assert_latest_allows_evolution()
        self._status = target
        await self._persist_state()
        return self._status

    def request_pause_at_boundary(self) -> None:
        self._pause_requested = True

    def clear_pause_request(self) -> None:
        self._pause_requested = False

    def begin_cycle(self) -> None:
        if self._status not in {EvolutionStatus.RUNNING, EvolutionStatus.CREATED}:
            raise InvalidEvolutionTransitionError(
                f"Cannot begin cycle while evolution is {self._status.value}"
            )
        self._cycle_in_progress = True

    async def complete_cycle(self) -> int:
        if not self._cycle_in_progress:
            raise InvalidEvolutionTransitionError("No evolutionary cycle is in progress")
        self._cycle_in_progress = False
        self._generation_number += 1
        if self._pause_requested and self._status == EvolutionStatus.RUNNING:
            await self.transition_to(EvolutionStatus.PAUSED)
            self._pause_requested = False
        await self._persist_state()
        return self._generation_number

    async def load_persisted_state(self) -> None:
        if self.evolution_repository is None:
            return
        document = await self.evolution_repository.load_evolution_state()
        if document is None:
            return
        self._status = EvolutionStatus(str(document.get("status", EvolutionStatus.CREATED.value)))
        self._generation_number = int(document.get("generation_number", 0))

    async def _persist_state(self) -> None:
        if self.evolution_repository is None:
            return
        await self.evolution_repository.save_evolution_state(
            status=self._status,
            generation_number=self._generation_number,
        )
