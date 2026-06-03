"""Tests for P5 candidate expansion and ranking."""

import json

import pytest

from mtes.llm.candidate_expansion_service import (
    P5_CANDIDATE_COUNT,
    CandidateExpansionService,
    apply_outlier_policy,
    overall_score,
)
from mtes.llm.candidate_expansion_service import RankedCandidate
from mtes.llm.llm_adapter import MockLlmProviderAdapter
from mtes.llm.provider_chain import LlmAdapterService, LlmProviderChain


def test_overall_score_formula() -> None:
    score = overall_score(0.8, 0.6, 0.75)
    assert score == pytest.approx(0.50 * 0.8 + 0.30 * 0.6 + 0.20 * 0.75)


def test_apply_outlier_policy_keeps_at_least_one() -> None:
    candidates = [
        RankedCandidate("a", 0.9, 0.5, 0.8, 0.95),
        RankedCandidate("b", 0.8, 0.5, 0.8, 0.50),
        RankedCandidate("c", 0.7, 0.5, 0.8, 0.48),
        RankedCandidate("d", 0.6, 0.5, 0.8, 0.47),
    ]
    filtered = apply_outlier_policy(candidates)
    assert len(filtered) >= 1


@pytest.mark.asyncio
async def test_expand_exactly_five_candidates_with_provided_responses() -> None:
    service = CandidateExpansionService(
        LlmAdapterService(
            LlmProviderChain(
                primary=MockLlmProviderAdapter(
                    provider_name="mock",
                    model_name="m",
                    response_content="{}",
                )
            )
        )
    )
    texts = [f"winter variant {index}" for index in range(P5_CANDIDATE_COUNT)]
    constraint_set = {
        "generation_constraints": [
            {"type": "required", "dimension": "anchor", "value": "winter"},
        ]
    }
    ranked = await service.expand_candidates(
        genome_id="genome_001",
        base_candidate_text="winter calm night",
        constraint_set=constraint_set,
        routing_family="P4-A",
        base_embedding=(1.0, 0.0, 0.0, 0.0),
        candidate_embeddings=[(1.0, 0.0, 0.0, 0.0)] * P5_CANDIDATE_COUNT,
        llm_responses=texts,
    )
    assert len(ranked) == P5_CANDIDATE_COUNT
    assert sum(1 for item in ranked if item.selected) == 1


@pytest.mark.asyncio
async def test_expand_via_mock_llm_list_response() -> None:
    response = json.dumps(
        {"candidates": [{"candidate_text": f"text {i}"} for i in range(P5_CANDIDATE_COUNT)]}
    )
    service = CandidateExpansionService(
        LlmAdapterService(
            LlmProviderChain(
                primary=MockLlmProviderAdapter(
                    provider_name="mock",
                    model_name="m",
                    response_content=response,
                )
            )
        )
    )
    ranked = await service.expand_candidates(
        genome_id="genome_001",
        base_candidate_text="winter calm night",
        constraint_set={
            "generation_constraints": [
                {"type": "required", "dimension": "anchor", "value": "winter"},
            ]
        },
        routing_family="P4-A",
        base_embedding=(1.0, 0.0, 0.0, 0.0),
        candidate_embeddings=[(1.0, 0.0, 0.0, 0.0)] * P5_CANDIDATE_COUNT,
    )
    assert len(ranked) == P5_CANDIDATE_COUNT
