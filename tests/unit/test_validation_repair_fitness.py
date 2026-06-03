"""Tests for validation, repair, and fitness evaluation."""

import pytest

from mtes.llm.llm_adapter import MockLlmProviderAdapter
from mtes.llm.provider_chain import LlmAdapterService, LlmProviderChain
from mtes.llm.repair_service import (
    LEAKAGE_PENALTY_THRESHOLD,
    RepairLeakageMonitor,
    RepairService,
)
from mtes.mapping.fitness_evaluator import FitnessEvaluator, FitnessInputs, FITNESS_WEIGHTS
from mtes.mapping.translation_service import MVP_NUMERIC_DEFAULTS, translate_numeric_genes
from mtes.mapping.validation_service import (
    ANCHOR_HARD_REJECT_THRESHOLD,
    ValidationResult,
    ValidationService,
)
from mtes.shared.exceptions import ConstraintViolationError


def test_anchor_integrity_exact_match() -> None:
    service = ValidationService()
    score = service.anchor_integrity("winter silence drifts", ("winter",))
    assert score == 1.0


def test_validation_rejects_low_anchor_integrity() -> None:
    service = ValidationService()
    constraints = translate_numeric_genes(MVP_NUMERIC_DEFAULTS)
    result = service.validate_candidate(
        candidate_text="silence only",
        required_anchors=("winter",),
        constraints=constraints,
    )
    assert result.anchor_integrity < ANCHOR_HARD_REJECT_THRESHOLD
    assert not result.passed
    assert "anchor_hard_reject" in result.failed_checks


@pytest.mark.asyncio
async def test_validate_and_persist_raises_on_failure() -> None:
    service = ValidationService()
    constraints = translate_numeric_genes(MVP_NUMERIC_DEFAULTS)
    with pytest.raises(ConstraintViolationError):
        await service.validate_and_persist(
            candidate_id="c1",
            candidate_text="no anchors here",
            required_anchors=("winter",),
            constraints=constraints,
        )


@pytest.mark.asyncio
async def test_repair_respects_token_delta_cap() -> None:
    repair_service = RepairService(
        LlmAdapterService(
            LlmProviderChain(
                primary=MockLlmProviderAdapter(
                    provider_name="mock",
                    model_name="m",
                    response_content="x" * 500,
                )
            )
        )
    )
    validation = ValidationResult(
        schema_pass=False,
        constraint_pass=False,
        semantic_pass=False,
        integration_pass=False,
        anchor_integrity=0.5,
        failed_checks=("anchor_preservation",),
    )
    with pytest.raises(ConstraintViolationError, match="repair_token_delta"):
        await repair_service.repair_candidate(
            candidate_text="short",
            violation="anchor",
            validation_result=validation,
        )


def test_repair_leakage_triggers_diagnostic_action() -> None:
    monitor = RepairLeakageMonitor()
    for _ in range(3):
        monitor.record_window([LEAKAGE_PENALTY_THRESHOLD + 0.01])
    assert monitor.leakage_detected()
    assert monitor.diagnostic_action() == "reduce_semantic_expansion_radius"


def test_fitness_formula_matches_weights() -> None:
    evaluator = FitnessEvaluator()
    constraints = translate_numeric_genes(MVP_NUMERIC_DEFAULTS)
    inputs = FitnessInputs(
        candidate_text="winter silence drifts slowly",
        anchor_integrity=0.92,
        local_novelty=0.63,
        ambiguity_score=0.05,
        sentiment_contrast_score=0.05,
        human_style_score=0.03,
    )
    result = evaluator.calculate_fitness(inputs, constraints)
    expected = (
        FITNESS_WEIGHTS["anchor_integrity"] * 0.92
        + FITNESS_WEIGHTS["compression_score"] * result.components["compression_score"]
        + FITNESS_WEIGHTS["local_novelty"] * 0.63
        + FITNESS_WEIGHTS["readability_floor"] * 0.80
        + FITNESS_WEIGHTS["human_style_score"] * 0.03
        + FITNESS_WEIGHTS["ambiguity_score"] * 0.05
        + FITNESS_WEIGHTS["sentiment_contrast_score"] * 0.05
        + FITNESS_WEIGHTS["fragmentation_alignment"] * result.components["fragmentation_alignment"]
    )
    assert result.fitness == pytest.approx(expected, abs=0.01)
