"""Bootstrap report persistence and readiness gating per Bootstrap §16–17."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from mtes.core.locality_calibration import (
    LOCALITY_BORDERLINE_MAX,
    LOCALITY_MANDATORY_MIN,
)
from mtes.core.provider_validation import (
    MANDATORY_ANCHOR_INTEGRITY,
    MANDATORY_PROVIDER_SUCCESS_RATE,
    MANDATORY_REPAIR_RATE_MAX,
    MANDATORY_SCHEMA_COMPLIANCE,
)
from mtes.shared.exceptions import MtesError


class BootstrapReadiness(StrEnum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"


class BootstrapNotReadyError(MtesError):
    """Raised when production evolution is blocked by bootstrap readiness."""


class BootstrapApprovalRequiredError(MtesError):
    """Raised when READY_WITH_WARNINGS lacks operator approval."""


@dataclass(frozen=True, slots=True)
class BootstrapValidationSnapshot:
    """Inputs for readiness evaluation (Bootstrap §16)."""

    all_stages_passed: bool
    provider_success_rate: float
    schema_compliance: float
    anchor_integrity: float
    repair_rate: float
    locality_correlation: float
    calibration_stability_std: float | None = None


@dataclass(frozen=True, slots=True)
class ReproducibilityRecord:
    bootstrap_version: str
    dataset_version: str
    prompt_set_version: str
    dictionary_version: str
    provider: str
    model: str
    embedding_model: str
    seed_policy: str
    timestamp: str

    def to_document(self) -> dict[str, str]:
        return {
            "bootstrap_version": self.bootstrap_version,
            "dataset_version": self.dataset_version,
            "prompt_set_version": self.prompt_set_version,
            "dictionary_version": self.dictionary_version,
            "provider": self.provider,
            "model": self.model,
            "embedding_model": self.embedding_model,
            "seed_policy": self.seed_policy,
            "timestamp": self.timestamp,
        }


class BootstrapReportRepository(Protocol):
    async def insert_report(self, document: dict[str, Any]) -> None:
        ...

    async def find_latest_report(self) -> dict[str, Any] | None:
        ...


def evaluate_bootstrap_readiness(snapshot: BootstrapValidationSnapshot) -> BootstrapReadiness:
    """Bootstrap §16: readiness from mandatory metrics and borderline locality."""
    if not snapshot.all_stages_passed:
        return BootstrapReadiness.NOT_READY
    if snapshot.provider_success_rate < MANDATORY_PROVIDER_SUCCESS_RATE:
        return BootstrapReadiness.NOT_READY
    if snapshot.schema_compliance < MANDATORY_SCHEMA_COMPLIANCE:
        return BootstrapReadiness.NOT_READY
    if snapshot.anchor_integrity < MANDATORY_ANCHOR_INTEGRITY:
        return BootstrapReadiness.NOT_READY
    if snapshot.repair_rate > MANDATORY_REPAIR_RATE_MAX:
        return BootstrapReadiness.NOT_READY
    if snapshot.locality_correlation < LOCALITY_MANDATORY_MIN:
        return BootstrapReadiness.NOT_READY
    if LOCALITY_MANDATORY_MIN <= snapshot.locality_correlation < LOCALITY_BORDERLINE_MAX:
        return BootstrapReadiness.READY_WITH_WARNINGS
    return BootstrapReadiness.READY


def assert_production_evolution_allowed(report: dict[str, Any]) -> None:
    """Bootstrap §19 / FR-bootstrap.03–04."""
    readiness = BootstrapReadiness(str(report.get("readiness_status", BootstrapReadiness.NOT_READY)))
    if readiness == BootstrapReadiness.NOT_READY:
        raise BootstrapNotReadyError("Bootstrap readiness is NOT_READY; evolution start blocked")
    if readiness == BootstrapReadiness.READY_WITH_WARNINGS and not bool(
        report.get("operator_approval", False)
    ):
        raise BootstrapApprovalRequiredError(
            "READY_WITH_WARNINGS requires operator_approval before production evolution"
        )


@dataclass
class BootstrapReportService:
    """Persist bootstrap reports and expose readiness checks."""

    report_repository: BootstrapReportRepository

    async def save_bootstrap_report(
        self,
        *,
        readiness_status: BootstrapReadiness,
        reproducibility_record: ReproducibilityRecord,
        operator_approval: bool = False,
        operator_notes: str = "",
    ) -> dict[str, Any]:
        document: dict[str, Any] = {
            "bootstrap_version": reproducibility_record.bootstrap_version,
            "dataset_version": reproducibility_record.dataset_version,
            "prompt_set_version": reproducibility_record.prompt_set_version,
            "readiness_status": readiness_status.value,
            "operator_approval": operator_approval,
            "reproducibility_record": reproducibility_record.to_document(),
        }
        if operator_approval:
            document["operator_approval_timestamp"] = datetime.now(UTC).isoformat()
        if operator_notes:
            document["operator_notes"] = operator_notes
        await self.report_repository.insert_report(document)
        return document

    async def load_latest_readiness(self) -> BootstrapReadiness:
        report = await self.report_repository.find_latest_report()
        if report is None:
            return BootstrapReadiness.NOT_READY
        return BootstrapReadiness(str(report.get("readiness_status", BootstrapReadiness.NOT_READY)))

    async def assert_latest_allows_evolution(self) -> None:
        report = await self.report_repository.find_latest_report()
        if report is None:
            raise BootstrapNotReadyError("No bootstrap report found")
        assert_production_evolution_allowed(report)
