"""One evolutionary generation tick."""

from dataclasses import dataclass

from mtes.core.generation_pipeline import GenerationPipeline, GenerationPipelineResult
from mtes.ga.population_service import PopulationService
from mtes.shared.types import Genome


@dataclass(frozen=True, slots=True)
class EvolutionCycleResult:
    generation_number: int
    pipeline_results: tuple[GenerationPipelineResult, ...]


class EvolutionCycle:
    """Run one evolutionary generation for the current population sample."""

    def __init__(
        self,
        generation_pipeline: GenerationPipeline,
        population_service: PopulationService,
    ) -> None:
        self._generation_pipeline = generation_pipeline
        self._population_service = population_service

    async def run_generation(
        self,
        *,
        sample_size: int = 1,
    ) -> EvolutionCycleResult:
        if not self._population_service.members:
            raise ValueError("population is empty")
        generation_number = self._population_service.advance_generation()
        sample = self._population_service.members[:sample_size]
        results: list[GenerationPipelineResult] = []
        for genome in sample:
            results.append(await self._generation_pipeline.run(genome))
        return EvolutionCycleResult(
            generation_number=generation_number,
            pipeline_results=tuple(results),
        )
