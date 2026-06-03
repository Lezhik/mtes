"""Diversity management per GA Specification §12."""

from mtes.mapping.genotype_distance import genome_distance
from mtes.shared.types import Genome

COLLAPSE_DISTANCE_THRESHOLD = 0.15
SPARSE_OCCUPANCY_THRESHOLD = 3
SPARSE_WINDOW_GENERATIONS = 20


class DiversityService:
    """Detect population collapse and sparse coordinate regions."""

    def mean_genome_distance(self, population: list[Genome]) -> float:
        if len(population) < 2:
            return 0.0
        distances: list[float] = []
        for index, genome_a in enumerate(population):
            for genome_b in population[index + 1 :]:
                distances.append(
                    genome_distance(
                        genome_a.semantic_genes,
                        genome_b.semantic_genes,
                        genome_a.numeric_genes,
                        genome_b.numeric_genes,
                    )
                )
        return sum(distances) / len(distances)

    def collapse_detected(self, population: list[Genome]) -> bool:
        return self.mean_genome_distance(population) < COLLAPSE_DISTANCE_THRESHOLD

    def sparse_coordinates(
        self,
        population: list[Genome],
        *,
        occupancy_threshold: int = SPARSE_OCCUPANCY_THRESHOLD,
    ) -> tuple[tuple[int, int, int, int, int], ...]:
        occupancy: dict[tuple[int, int, int, int, int], int] = {}
        for genome in population:
            for gene in genome.semantic_genes:
                occupancy[gene.coordinate] = occupancy.get(gene.coordinate, 0) + 1
        return tuple(
            coordinate
            for coordinate, count in occupancy.items()
            if count < occupancy_threshold
        )
