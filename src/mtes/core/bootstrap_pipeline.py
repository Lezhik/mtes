"""Sequential bootstrap pipeline per Bootstrap Specification §4."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Protocol

from mtes.core.bootstrap_stages import BOOTSTRAP_STAGE_ORDER, BootstrapStage

BootstrapStageHandler = Callable[[], Awaitable[None]]


class BootstrapStageStore(Protocol):
    async def is_completed(self, stage: BootstrapStage) -> bool:
        ...

    async def mark_completed(self, stage: BootstrapStage) -> None:
        ...

    async def clear_all(self) -> None:
        ...


@dataclass
class InMemoryBootstrapStageStore:
    completed: set[BootstrapStage] = field(default_factory=set)

    async def is_completed(self, stage: BootstrapStage) -> bool:
        return stage in self.completed

    async def mark_completed(self, stage: BootstrapStage) -> None:
        self.completed.add(stage)

    async def clear_all(self) -> None:
        self.completed.clear()


@dataclass(frozen=True, slots=True)
class BootstrapPipelineResult:
    completed_stages: tuple[BootstrapStage, ...]
    failed_stage: BootstrapStage | None = None


class BootstrapPipeline:
    """Run bootstrap stages sequentially with idempotent skip."""

    def __init__(
        self,
        *,
        stage_store: BootstrapStageStore,
        handlers: dict[BootstrapStage, BootstrapStageHandler],
    ) -> None:
        self._stage_store = stage_store
        self._handlers = handlers

    async def run(self, *, force: bool = False) -> BootstrapPipelineResult:
        if force:
            await self._stage_store.clear_all()

        completed: list[BootstrapStage] = []
        for stage in BOOTSTRAP_STAGE_ORDER:
            if not force and await self._stage_store.is_completed(stage):
                completed.append(stage)
                continue
            handler = self._handlers.get(stage)
            if handler is None:
                raise NotImplementedError(f"Bootstrap handler not implemented: {stage.value}")
            try:
                await handler()
            except Exception:
                return BootstrapPipelineResult(
                    completed_stages=tuple(completed),
                    failed_stage=stage,
                )
            await self._stage_store.mark_completed(stage)
            completed.append(stage)
        return BootstrapPipelineResult(completed_stages=tuple(completed))
