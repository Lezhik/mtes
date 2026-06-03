"""Evolution start blocked when bootstrap is NOT_READY."""

import pytest

from mtes.core.bootstrap_report_service import (
    BootstrapNotReadyError,
    BootstrapReadiness,
    BootstrapReportService,
)
from mtes.core.evolution_lifecycle_service import EvolutionLifecycleService
from mtes.shared.types import EvolutionStatus


class InMemoryBootstrapReportRepository:
    def __init__(self) -> None:
        self._documents: list[dict[str, object]] = []

    async def insert_report(self, document: dict[str, object]) -> None:
        self._documents.append(document)

    async def find_latest_report(self) -> dict[str, object] | None:
        if not self._documents:
            return None
        return self._documents[-1]


@pytest.mark.asyncio
async def test_running_transition_blocked_without_ready_report() -> None:
    repository = InMemoryBootstrapReportRepository()
    report_service = BootstrapReportService(report_repository=repository)
    lifecycle = EvolutionLifecycleService(bootstrap_report_service=report_service)
    with pytest.raises(BootstrapNotReadyError):
        await lifecycle.transition_to(EvolutionStatus.RUNNING)


@pytest.mark.asyncio
async def test_running_transition_allowed_with_ready_report() -> None:
    repository = InMemoryBootstrapReportRepository()
    report_service = BootstrapReportService(report_repository=repository)
    from mtes.core.bootstrap_report_service import ReproducibilityRecord

    await report_service.save_bootstrap_report(
        readiness_status=BootstrapReadiness.READY,
        reproducibility_record=ReproducibilityRecord(
            bootstrap_version="2.4",
            dataset_version="1.0",
            prompt_set_version="1.0",
            dictionary_version="1.0",
            provider="provider-x",
            model="model-y",
            embedding_model="embedding-z",
            seed_policy="hash(genome_id)",
            timestamp="2026-01-01T00:00:00Z",
        ),
    )
    lifecycle = EvolutionLifecycleService(bootstrap_report_service=report_service)
    await lifecycle.transition_to(EvolutionStatus.RUNNING)
    assert lifecycle.status == EvolutionStatus.RUNNING


@pytest.mark.asyncio
async def test_not_ready_report_blocks_running() -> None:
    repository = InMemoryBootstrapReportRepository()
    await repository.insert_report({"readiness_status": "NOT_READY"})
    report_service = BootstrapReportService(report_repository=repository)
    lifecycle = EvolutionLifecycleService(bootstrap_report_service=report_service)
    with pytest.raises(BootstrapNotReadyError):
        await lifecycle.transition_to(EvolutionStatus.RUNNING)
