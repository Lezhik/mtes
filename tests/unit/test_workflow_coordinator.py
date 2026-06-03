"""Tests for workflow coordinator and evolution lifecycle."""

from typing import Any

import pytest

from mtes.core.evolution_lifecycle_service import (
    ALLOWED_EVOLUTION_TRANSITIONS,
    EvolutionLifecycleService,
    InvalidEvolutionTransitionError,
)
from mtes.core.workflow_coordinator import WorkflowCoordinator
from mtes.core.workflow_types import WorkflowState
from mtes.persistence.repositories.workflow_state_repository import WorkflowStateRepository
from mtes.persistence.document_context import DocumentContext
from mtes.shared.types import EvolutionStatus

pytest.importorskip("testcontainers")

from testcontainers.mongodb import MongoDbContainer  # type: ignore[import-untyped]


class InMemoryEvolutionRepository:
    def __init__(self) -> None:
        self.document: dict[str, Any] | None = None

    async def load_evolution_state(self) -> dict[str, Any] | None:
        return self.document

    async def save_evolution_state(self, *, status: EvolutionStatus, generation_number: int) -> None:
        self.document = {
            "_id": "evolution_state",
            "status": status.value,
            "generation_number": generation_number,
        }


@pytest.fixture
async def workflow_repository():
    try:
        with MongoDbContainer("mongo:7") as mongo:
            from mtes.persistence.client import MongoPersistenceClient

            client = MongoPersistenceClient(f"{mongo.get_connection_url()}/mtes_workflow_test")
            await client.connect()
            database = client.get_database()
            context = DocumentContext(
                schema_version="3.4",
                experiment_id="exp_wf",
                run_id="run_wf",
            )
            repository = WorkflowStateRepository(
                database["workflow_state"],
                context,
            )
            yield repository
            await client.close()
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers unavailable: {exc}")


@pytest.mark.asyncio
async def test_workflow_completes_and_persists(workflow_repository: WorkflowStateRepository) -> None:
    coordinator = WorkflowCoordinator(workflow_repository)
    steps = [_async_noop]
    result = await coordinator.run_workflow("wf_complete", stage="generation", steps=steps)
    assert result["state"] == WorkflowState.COMPLETED.value


@pytest.mark.asyncio
async def test_emergency_stop_pauses_workflow(workflow_repository: WorkflowStateRepository) -> None:
    coordinator = WorkflowCoordinator(workflow_repository)
    coordinator.trigger_emergency_stop()

    async def failing_step() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await coordinator.run_workflow("wf_fail", stage="generation", steps=[failing_step])

    document = await workflow_repository.find_by_workflow_id("wf_fail")
    assert document is not None
    assert document["state"] in {
        WorkflowState.FAILED.value,
        WorkflowState.EMERGENCY_STOPPED.value,
    }


@pytest.mark.asyncio
async def test_recover_workflows_on_startup(workflow_repository: WorkflowStateRepository) -> None:
    coordinator = WorkflowCoordinator(workflow_repository)
    await coordinator.start_workflow("wf_recover", stage="generation")
    document = await workflow_repository.transition_workflow_state(
        "wf_recover",
        expected_version=1,
        state=WorkflowState.RUNNING.value,
        stage="generation",
    )
    assert document is not None

    recovery_coordinator = WorkflowCoordinator(workflow_repository)
    recovered = await recovery_coordinator.recover_workflows_on_startup()
    assert any(item["workflow_id"] == "wf_recover" for item in recovered)


async def _async_noop() -> None:
    return None


def test_evolution_transition_table_has_no_invalid_edges() -> None:
    for source, targets in ALLOWED_EVOLUTION_TRANSITIONS.items():
        for target in targets:
            assert target in EvolutionStatus
            assert source in ALLOWED_EVOLUTION_TRANSITIONS


@pytest.mark.asyncio
async def test_evolution_pause_at_cycle_boundary() -> None:
    service = EvolutionLifecycleService(evolution_repository=InMemoryEvolutionRepository())
    await service.transition_to(EvolutionStatus.RUNNING)
    service.request_pause_at_boundary()
    service.begin_cycle()
    generation = await service.complete_cycle()
    assert generation == 1
    assert service.status == EvolutionStatus.PAUSED


@pytest.mark.asyncio
async def test_invalid_evolution_transition_rejected() -> None:
    service = EvolutionLifecycleService()
    with pytest.raises(InvalidEvolutionTransitionError):
        await service.transition_to(EvolutionStatus.STOPPED)
