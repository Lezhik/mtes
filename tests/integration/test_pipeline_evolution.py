"""Cross-module integration tests with mock LLM (no real providers)."""

import json

import pytest

from mtes.core.evolution_cycle import EvolutionCycle
from mtes.core.evolution_lifecycle_service import EvolutionLifecycleService
from mtes.core.generation_pipeline import GenerationPipeline
from mtes.ga.population_service import PopulationService
from mtes.llm.decoding_profiles import LlmPhase
from mtes.llm.llm_adapter import normalize_response_content
from mtes.llm.provider_chain import LlmAdapterService, LlmProviderChain
from mtes.llm.types import LlmRequest, LlmResponse
from mtes.shared.types import EvolutionStatus, Genome, NumericGenes, SemanticGene

SAMPLE_GENOME = Genome(
    genome_id="genome_integration_001",
    generation=1,
    semantic_genes=(
        SemanticGene(gene_id=1, coordinate=(3, 5, 4, 2, 3), anchor="winter"),
    ),
    numeric_genes=NumericGenes(0.5, 0.45, 0.4, 0.35, 0.55, 0.7),
)

CONSTRAINT_JSON = json.dumps(
    {"generation_constraints": [{"type": "required", "dimension": "anchor", "value": "winter"}]}
)
COMPILE_JSON = json.dumps({"candidate_text": "winter silence drifts"})


class PhaseAwareMockLlmProvider:
    provider_name = "mock"
    model_name = "mock-model"

    async def complete(self, request: LlmRequest, *, timeout_seconds: float) -> LlmResponse:
        del timeout_seconds
        if request.phase == LlmPhase.P3:
            content = CONSTRAINT_JSON
        elif request.phase == LlmPhase.P4:
            content = COMPILE_JSON
        else:
            content = json.dumps(
                {
                    "candidates": [
                        {"candidate_text": "winter silence drifts"},
                        {"candidate_text": "winter silence drifts variant a"},
                        {"candidate_text": "winter silence drifts variant b"},
                        {"candidate_text": "winter silence drifts variant c"},
                        {"candidate_text": "winter silence drifts variant d"},
                    ]
                }
            )
        return LlmResponse(
            content=normalize_response_content(content),
            provider_name=self.provider_name,
            model_name=self.model_name,
            phase=request.phase,
        )


@pytest.fixture
def pipeline() -> GenerationPipeline:
    return GenerationPipeline(
        LlmAdapterService(LlmProviderChain(primary=PhaseAwareMockLlmProvider()))
    )


@pytest.mark.asyncio
async def test_full_pipeline_genome_to_fitness(pipeline: GenerationPipeline) -> None:
    result = await pipeline.run(SAMPLE_GENOME)
    assert result.fitness.fitness > 0.0
    assert result.validation_anchor_integrity >= 0.0
    assert "winter" in result.selected_candidate.candidate_text


@pytest.mark.asyncio
async def test_evolution_cycle_pause_at_boundary(pipeline: GenerationPipeline) -> None:
    population = PopulationService(target_size=10)
    population.add_member(SAMPLE_GENOME)
    cycle = EvolutionCycle(pipeline, population)
    lifecycle = EvolutionLifecycleService()
    await lifecycle.transition_to(EvolutionStatus.RUNNING)
    lifecycle.request_pause_at_boundary()
    lifecycle.begin_cycle()
    await cycle.run_generation()
    generation_number = await lifecycle.complete_cycle()
    assert generation_number == 1
    assert lifecycle.status == EvolutionStatus.PAUSED
