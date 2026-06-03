"""Workflow coordination with persistence and recovery per Architecture §7.1."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from mtes.core.workflow_types import WorkflowState
from mtes.persistence.repositories.workflow_state_repository import WorkflowStateRepository
from mtes.persistence.retry_policy import (
    INFRASTRUCTURE_MAX_ATTEMPTS,
    INFRASTRUCTURE_RETRY_DELAYS_SECONDS,
)

WorkflowStep = Callable[[], Awaitable[None]]
MAX_WORKFLOW_STEP_RETRIES = INFRASTRUCTURE_MAX_ATTEMPTS


@dataclass
class WorkflowCoordinator:
    """Coordinate long-running workflows with persisted state."""

    workflow_repository: WorkflowStateRepository
    emergency_stop: bool = False
    _paused_workflows: set[str] = field(default_factory=set)

    def trigger_emergency_stop(self) -> None:
        self.emergency_stop = True

    def clear_emergency_stop(self) -> None:
        self.emergency_stop = False

    def pause_workflow(self, workflow_id: str) -> None:
        self._paused_workflows.add(workflow_id)

    def resume_workflow(self, workflow_id: str) -> None:
        self._paused_workflows.discard(workflow_id)

    async def start_workflow(
        self,
        workflow_id: str,
        *,
        stage: str,
    ) -> dict[str, Any]:
        existing = await self.workflow_repository.find_by_workflow_id(workflow_id)
        if existing is not None:
            return existing
        return await self.workflow_repository.create_workflow_state(
            workflow_id,
            state=WorkflowState.PENDING.value,
            stage=stage,
        )

    async def recover_workflows_on_startup(self) -> list[dict[str, Any]]:
        """Restore recoverable workflows after process restart."""
        active = await self.workflow_repository.find_active_workflows()
        recovered: list[dict[str, Any]] = []
        for document in active:
            workflow_id = str(document["workflow_id"])
            if self.emergency_stop:
                updated = await self._transition(
                    document,
                    state=WorkflowState.EMERGENCY_STOPPED.value,
                    stage=str(document["stage"]),
                )
                if updated is not None:
                    recovered.append(updated)
                continue
            updated = await self._transition(
                document,
                state=WorkflowState.RUNNING.value,
                stage=str(document["stage"]),
            )
            if updated is not None:
                recovered.append(updated)
        return recovered

    async def run_workflow(
        self,
        workflow_id: str,
        *,
        stage: str,
        steps: list[WorkflowStep],
    ) -> dict[str, Any]:
        document = await self.start_workflow(workflow_id, stage=stage)
        document = await self._transition(
            document,
            state=WorkflowState.RUNNING.value,
            stage=stage,
        )
        if document is None:
            raise RuntimeError(f"Failed to start workflow {workflow_id}")

        try:
            for step_index, step in enumerate(steps):
                if self.emergency_stop:
                    document = await self._transition(
                        document,
                        state=WorkflowState.EMERGENCY_STOPPED.value,
                        stage=stage,
                    )
                    return document or {}
                if workflow_id in self._paused_workflows:
                    document = await self._transition(
                        document,
                        state=WorkflowState.PAUSED.value,
                        stage=stage,
                    )
                    return document or {}

                await self._run_step_with_retry(
                    workflow_id=workflow_id,
                    step=step,
                    step_index=step_index,
                    document=document,
                )
                refreshed = await self.workflow_repository.find_by_workflow_id(workflow_id)
                if refreshed is not None:
                    document = refreshed

            completed = await self._transition(
                document,
                state=WorkflowState.COMPLETED.value,
                stage=stage,
            )
            return completed or document
        except Exception as exc:
            await self._transition(
                document,
                state=WorkflowState.FAILED.value,
                stage=stage,
            )
            raise RuntimeError(f"Workflow {workflow_id} failed") from exc

    async def resume_paused_workflow(
        self,
        workflow_id: str,
        *,
        steps: list[WorkflowStep],
    ) -> dict[str, Any]:
        self.resume_workflow(workflow_id)
        document = await self.workflow_repository.find_by_workflow_id(workflow_id)
        if document is None:
            raise KeyError(f"Unknown workflow: {workflow_id}")
        if str(document.get("state")) != WorkflowState.PAUSED.value:
            return document
        return await self.run_workflow(
            workflow_id,
            stage=str(document["stage"]),
            steps=steps,
        )

    async def _run_step_with_retry(
        self,
        *,
        workflow_id: str,
        step: WorkflowStep,
        step_index: int,
        document: dict[str, Any],
    ) -> None:
        last_error: Exception | None = None
        retry_count = int(document.get("retry_count", 0))
        for attempt_index in range(MAX_WORKFLOW_STEP_RETRIES):
            try:
                await step()
                return
            except Exception as exc:  # noqa: BLE001 — workflow boundary
                last_error = exc
                retry_count += 1
                refreshed = await self.workflow_repository.find_by_workflow_id(workflow_id)
                if refreshed is None:
                    break
                await self._transition(
                    refreshed,
                    state=str(refreshed.get("state", WorkflowState.RUNNING.value)),
                    stage=str(refreshed["stage"]),
                    retry_count=retry_count,
                )
                if attempt_index >= MAX_WORKFLOW_STEP_RETRIES - 1:
                    break
                await asyncio.sleep(INFRASTRUCTURE_RETRY_DELAYS_SECONDS[attempt_index])
        raise RuntimeError(
            f"Workflow step {step_index} failed for {workflow_id}: {last_error}"
        ) from last_error

    async def _transition(
        self,
        document: dict[str, Any],
        *,
        state: str,
        stage: str,
        retry_count: int | None = None,
    ) -> dict[str, Any] | None:
        return await self.workflow_repository.transition_workflow_state(
            str(document["workflow_id"]),
            expected_version=int(document["version"]),
            state=state,
            stage=stage,
            retry_count=retry_count,
        )
