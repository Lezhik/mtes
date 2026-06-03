"""Tests for P3 constraint expansion."""

import json

import pytest

from mtes.llm.constraint_expansion_service import ConstraintExpansionService
from mtes.llm.constraint_schema import validate_constraint_expansion_payload
from mtes.llm.decoding_profiles import decoding_profile_for_phase
from mtes.llm.llm_adapter import MockLlmProviderAdapter
from mtes.llm.provider_chain import LlmAdapterService, LlmProviderChain
from mtes.llm.types import LlmRequest
from mtes.shared.exceptions import ConstraintViolationError
from mtes.shared.types import Genome, NumericGenes, SemanticGene

SAMPLE_GENOME = Genome(
    genome_id="genome_001",
    generation=1,
    semantic_genes=(
        SemanticGene(gene_id=1, coordinate=(3, 5, 4, 2, 3), anchor="winter"),
    ),
    numeric_genes=NumericGenes(0.5, 0.45, 0.4, 0.35, 0.55, 0.7),
)


def test_validate_constraint_expansion_payload_accepts_valid() -> None:
    payload = {
        "generation_constraints": [
            {"type": "required", "dimension": "anchor", "value": "winter"},
            {"type": "target", "dimension": "fragmentation", "value": 0.8},
        ]
    }
    assert validate_constraint_expansion_payload(payload)["generation_constraints"]


def test_validate_constraint_expansion_payload_rejects_invalid_type() -> None:
    with pytest.raises(ConstraintViolationError):
        validate_constraint_expansion_payload(
            {"generation_constraints": [{"type": "maybe", "dimension": "x", "value": 1}]}
        )


@pytest.mark.asyncio
async def test_expand_constraints_with_mock_llm() -> None:
    valid_response = json.dumps(
        {
            "generation_constraints": [
                {"type": "required", "dimension": "anchor", "value": "winter"},
            ]
        }
    )
    service = ConstraintExpansionService(
        LlmAdapterService(
            LlmProviderChain(
                primary=MockLlmProviderAdapter(
                    provider_name="mock",
                    model_name="mock-model",
                    response_content=valid_response,
                )
            )
        )
    )
    result = await service.expand_constraints(SAMPLE_GENOME)
    assert result["generation_constraints"][0]["value"] == "winter"


@pytest.mark.asyncio
async def test_expand_constraints_rejects_invalid_json() -> None:
    service = ConstraintExpansionService(
        LlmAdapterService(
            LlmProviderChain(
                primary=MockLlmProviderAdapter(
                    provider_name="mock",
                    model_name="mock-model",
                    response_content="not-json",
                )
            )
        )
    )
    with pytest.raises(ConstraintViolationError):
        await service.expand_constraints(SAMPLE_GENOME)
