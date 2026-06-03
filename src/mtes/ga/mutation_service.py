"""Semantic and numeric mutation per GA Specification §8."""

import random

from mtes.mapping.genotype_distance import genome_distance
from mtes.mapping.numeric_lut import byte_to_gene_value, gene_value_to_byte
from mtes.shared.types import NumericGenes, SemanticGene

Coordinate = tuple[int, int, int, int, int]
LOCALITY_REPAIR_THRESHOLD = 0.35
LOCALITY_REPAIR_MAX_ITERATIONS = 3


def reflect_axis_value(value: int, delta: int) -> int:
    """Reflect axis mutations at boundaries 0 and 7."""
    result = value + delta
    while result < 0 or result > 7:
        if result < 0:
            result = -result
        if result > 7:
            result = 14 - result
    return result


class MutationService:
    """Apply semantic and numeric mutations."""

    def __init__(self, *, random_source: random.Random | None = None) -> None:
        self._random = random_source or random.Random()

    def mutate_semantic_coordinate(
        self,
        coordinate: Coordinate,
        *,
        gene_index: int | None = None,
        axis_index: int | None = None,
    ) -> Coordinate:
        gene_idx = gene_index if gene_index is not None else self._random.randint(0, 4)
        axis_idx = axis_index if axis_index is not None else self._random.randint(0, 4)
        coordinate_list = list(coordinate)
        delta = self._random.choice([-1, 1])
        coordinate_list[axis_idx] = reflect_axis_value(coordinate_list[axis_idx], delta)
        return tuple(coordinate_list)

    def mutate_semantic_gene(self, gene: SemanticGene) -> SemanticGene:
        new_coordinate = self.mutate_semantic_coordinate(gene.coordinate)
        return SemanticGene(
            gene_id=gene.gene_id,
            coordinate=new_coordinate,
            anchor=gene.anchor,
        )

    def mutate_numeric_genes(self, numeric: NumericGenes) -> NumericGenes:
        field_names = list(NumericGenes.__dataclass_fields__.keys())
        chosen = self._random.choice(field_names)
        current = getattr(numeric, chosen)
        mutated_byte = gene_value_to_byte(current)
        delta = self._random.choice([-1, 1])
        new_byte = max(0, min(255, mutated_byte + delta))
        new_value = byte_to_gene_value(new_byte)
        updated = {name: getattr(numeric, name) for name in field_names}
        updated[chosen] = new_value
        return NumericGenes(**updated)

    def locality_repair_semantic_genes(
        self,
        offspring_genes: tuple[SemanticGene, ...],
        parent_genes_a: tuple[SemanticGene, ...],
        parent_genes_b: tuple[SemanticGene, ...],
        numeric_offspring: NumericGenes,
        numeric_a: NumericGenes,
        numeric_b: NumericGenes,
    ) -> tuple[SemanticGene, ...]:
        """Repair semantic genes when offspring distance exceeds threshold."""
        genes = list(offspring_genes)
        for _ in range(LOCALITY_REPAIR_MAX_ITERATIONS):
            distance = genome_distance(genes, parent_genes_a, numeric_offspring, numeric_a)
            if distance <= LOCALITY_REPAIR_THRESHOLD:
                break
            index = self._random.randrange(len(genes))
            genes[index] = self.mutate_semantic_gene(genes[index])
        return tuple(genes)
