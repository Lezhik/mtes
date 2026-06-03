"""Tests for bootstrap pipeline, provider validation, and locality calibration."""

from pathlib import Path

import pytest

from mtes.core.bootstrap_pipeline import BootstrapPipeline, InMemoryBootstrapStageStore
from mtes.core.bootstrap_report_service import (
    BootstrapNotReadyError,
    BootstrapReadiness,
    BootstrapValidationSnapshot,
    assert_production_evolution_allowed,
    evaluate_bootstrap_readiness,
)
from mtes.core.bootstrap_stages import BOOTSTRAP_STAGE_ORDER, BootstrapStage
from mtes.core.golden_loaders import load_golden_dataset, load_golden_prompts
from mtes.core.locality_calibration import (
    LocalityCalibrationService,
    expected_pair_count,
    spearman_rank_correlation,
)
from mtes.core.provider_validation import (
    ProviderValidationMetrics,
    calculate_final_provider_score,
    calculate_preliminary_provider_score,
    passes_mandatory_provider_thresholds,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "config" / "fixtures"


def test_bootstrap_stage_order_matches_spec() -> None:
    assert [stage.value for stage in BOOTSTRAP_STAGE_ORDER][0] == "infrastructure_validation"
    assert BOOTSTRAP_STAGE_ORDER[-1] == BootstrapStage.BOOTSTRAP_REPORT


@pytest.mark.asyncio
async def test_bootstrap_pipeline_idempotent_skip() -> None:
    store = InMemoryBootstrapStageStore()
    calls: list[str] = []

    async def handler() -> None:
        calls.append("ran")

    pipeline = BootstrapPipeline(
        stage_store=store,
        handlers={BootstrapStage.INFRASTRUCTURE_VALIDATION: handler},
    )
    for stage in BOOTSTRAP_STAGE_ORDER[1:]:
        await store.mark_completed(stage)
    await pipeline.run()
    await pipeline.run()
    assert calls == ["ran"]


def test_preliminary_and_final_provider_scores() -> None:
    metrics = ProviderValidationMetrics(
        provider_id="p1",
        provider_success_rate=0.96,
        schema_compliance=0.99,
        anchor_integrity=0.90,
        repair_rate=0.05,
        latency_mean_seconds=2.0,
        locality_correlation=0.48,
    )
    preliminary = calculate_preliminary_provider_score(metrics, latency_reference_seconds=10.0)
    final_score = calculate_final_provider_score(metrics, latency_reference_seconds=10.0)
    assert preliminary > 0.8
    assert final_score > preliminary * 0.5
    assert passes_mandatory_provider_thresholds(metrics)


def test_locality_calibration_on_fixture_dataset() -> None:
    records = load_golden_dataset(FIXTURES_DIR / "golden_dataset.jsonl")
    service = LocalityCalibrationService()
    result = service.calibrate_once(records)
    assert result.pair_count == expected_pair_count(len(records))
    assert result.locality_correlation >= 0.45


def test_subsampling_forbidden_pair_count_documented() -> None:
    """Bootstrap §11.4 forbids subsampling; full pair set is required."""
    genome_count = 4
    assert expected_pair_count(genome_count) == 6


def test_spearman_perfect_monotonic_ranks() -> None:
    x = [1.0, 2.0, 3.0, 4.0]
    y = [10.0, 20.0, 30.0, 40.0]
    assert spearman_rank_correlation(x, y) == pytest.approx(1.0)


def test_readiness_borderline_and_not_ready() -> None:
    ready_snapshot = BootstrapValidationSnapshot(
        all_stages_passed=True,
        provider_success_rate=0.96,
        schema_compliance=0.99,
        anchor_integrity=0.90,
        repair_rate=0.05,
        locality_correlation=0.55,
    )
    assert evaluate_bootstrap_readiness(ready_snapshot) == BootstrapReadiness.READY

    warning_snapshot = BootstrapValidationSnapshot(
        all_stages_passed=True,
        provider_success_rate=0.96,
        schema_compliance=0.99,
        anchor_integrity=0.90,
        repair_rate=0.05,
        locality_correlation=0.47,
    )
    assert evaluate_bootstrap_readiness(warning_snapshot) == BootstrapReadiness.READY_WITH_WARNINGS

    blocked_snapshot = BootstrapValidationSnapshot(
        all_stages_passed=True,
        provider_success_rate=0.96,
        schema_compliance=0.99,
        anchor_integrity=0.90,
        repair_rate=0.05,
        locality_correlation=0.40,
    )
    assert evaluate_bootstrap_readiness(blocked_snapshot) == BootstrapReadiness.NOT_READY


def test_not_ready_blocks_production_evolution() -> None:
    with pytest.raises(BootstrapNotReadyError):
        assert_production_evolution_allowed({"readiness_status": "NOT_READY"})


def test_golden_prompt_loader() -> None:
    prompts = load_golden_prompts(FIXTURES_DIR / "golden_prompts.jsonl")
    assert len(prompts) == 1
    assert prompts[0].routing_family == "P1-A"
