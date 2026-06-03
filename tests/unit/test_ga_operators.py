"""Tests for GA operators."""

import random

from mtes.ga.crossover_service import CrossoverService, canonicalize_parent_ids
from mtes.ga.diversity_service import DiversityService
from mtes.ga.mutation_service import MutationService, reflect_axis_value
from mtes.ga.pair_memory_service import PairMemoryService
from mtes.ga.population_service import PopulationService
from mtes.ga.selection_service import ParentCandidate, SelectionService
from mtes.shared.types import Genome, NumericGenes, SemanticGene

GENE = SemanticGene(gene_id=1, coordinate=(3, 3, 3, 3, 3), anchor="winter")
NUMERIC = NumericGenes(0.5, 0.45, 0.4, 0.35, 0.55, 0.7)


def test_reflect_axis_value_boundaries() -> None:
    assert reflect_axis_value(0, -1) == 1
    assert reflect_axis_value(7, 1) == 6


def test_mutation_changes_coordinate_with_fixed_seed() -> None:
    service = MutationService(random_source=random.Random(42))
    mutated = service.mutate_semantic_coordinate((3, 3, 3, 3, 3), gene_index=0, axis_index=0)
    assert mutated != (3, 3, 3, 3, 3)


def test_crossover_canonicalize_parent_ids() -> None:
    assert canonicalize_parent_ids("b", "a") == ("a", "b")


def test_pair_memory_penalty_decays() -> None:
    service = PairMemoryService()
    service.record_use("genome_a", "genome_z", current_generation=10)
    penalty_early = service.get_penalty("genome_a", "genome_z", current_generation=11)
    penalty_late = service.get_penalty("genome_a", "genome_z", current_generation=40)
    assert penalty_late < penalty_early


def test_selection_parent_score_weights() -> None:
    service = SelectionService()
    candidate = ParentCandidate(
        genome_id="g1",
        fitness_rank=1.0,
        compatibility=1.0,
        novelty=1.0,
        diversity_bonus=1.0,
        pool="exploitation",
    )
    assert service.parent_score(candidate) == 1.0


def test_population_service_trims_to_target_size() -> None:
    population = PopulationService(target_size=2)
    for index in range(4):
        population.add_member(
            Genome(
                genome_id=f"g{index}",
                generation=index,
                semantic_genes=(GENE,),
                numeric_genes=NUMERIC,
            )
        )
    assert population.population_size == 2


def test_diversity_collapse_detected_for_identical_genomes() -> None:
    service = DiversityService()
    genome = Genome(
        genome_id="g1",
        generation=1,
        semantic_genes=(GENE,),
        numeric_genes=NUMERIC,
    )
    assert service.collapse_detected([genome, genome])
