"""Crossover operators per GA Specification §11."""

import random

from mtes.shared.types import NumericGenes, SemanticGene

Coordinate = tuple[int, int, int, int, int]


def canonicalize_parent_ids(parent_a_id: str, parent_b_id: str) -> tuple[str, str]:
    if parent_a_id < parent_b_id:
        return parent_a_id, parent_b_id
    return parent_b_id, parent_a_id


class CrossoverService:
    """Adaptive blend crossover for semantic genes."""

    def __init__(self, *, random_source: random.Random | None = None) -> None:
        self._random = random_source or random.Random()

    def blend_axis(self, value_a: int, value_b: int) -> int:
        mode = self._random.choice(["interval", "midpoint", "inject"])
        if mode == "interval":
            low, high = sorted((value_a, value_b))
            return self._random.randint(low, high)
        if mode == "midpoint":
            return int(round((value_a + value_b) / 2))
        return value_a if self._random.random() < 0.5 else value_b

    def crossover_semantic_genes(
        self,
        genes_a: tuple[SemanticGene, ...],
        genes_b: tuple[SemanticGene, ...],
    ) -> tuple[SemanticGene, ...]:
        by_id_b = {gene.gene_id: gene for gene in genes_b}
        offspring: list[SemanticGene] = []
        for gene_a in genes_a:
            gene_b = by_id_b.get(gene_a.gene_id)
            if gene_b is None:
                offspring.append(gene_a)
                continue
            blended_coordinate: Coordinate = tuple(
                self.blend_axis(gene_a.coordinate[index], gene_b.coordinate[index])
                for index in range(5)
            )
            anchor = gene_a.anchor if self._random.random() < 0.5 else gene_b.anchor
            offspring.append(
                SemanticGene(
                    gene_id=gene_a.gene_id,
                    coordinate=blended_coordinate,
                    anchor=anchor,
                )
            )
        return tuple(offspring)

    def crossover_numeric_genes(self, numeric_a: NumericGenes, numeric_b: NumericGenes) -> NumericGenes:
        field_names = list(NumericGenes.__dataclass_fields__.keys())
        values: dict[str, float] = {}
        for name in field_names:
            values[name] = (
                getattr(numeric_a, name) if self._random.random() < 0.5 else getattr(numeric_b, name)
            )
        return NumericGenes(**values)
