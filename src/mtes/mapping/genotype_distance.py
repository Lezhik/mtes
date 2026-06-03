"""Genotype distance functions per GA Specification §7."""

from mtes.shared.types import NumericGenes, SemanticGene

SEMANTIC_DISTANCE_DIVISOR = 35.0
SEMANTIC_WEIGHT = 0.70
NUMERIC_WEIGHT = 0.30


def semantic_coordinate_distance(
    coordinate_a: tuple[int, int, int, int, int],
    coordinate_b: tuple[int, int, int, int, int],
) -> float:
    """GA §7.1: sum(abs differences) / 35."""
    axis_delta = sum(abs(a - b) for a, b in zip(coordinate_a, coordinate_b, strict=True))
    return axis_delta / SEMANTIC_DISTANCE_DIVISOR


def semantic_genome_distance(genes_a: tuple[SemanticGene, ...], genes_b: tuple[SemanticGene, ...]) -> float:
    """Mean semantic distance across paired genes by gene_id."""
    genes_by_id_b = {gene.gene_id: gene for gene in genes_b}
    distances: list[float] = []
    for gene_a in genes_a:
        gene_b = genes_by_id_b.get(gene_a.gene_id)
        if gene_b is None:
            continue
        distances.append(semantic_coordinate_distance(gene_a.coordinate, gene_b.coordinate))
    if not distances:
        return 0.0
    return sum(distances) / len(distances)


def numeric_genome_distance(numeric_a: NumericGenes, numeric_b: NumericGenes) -> float:
    """GA §7.2: mean absolute difference across six numeric genes."""
    deltas = [
        abs(numeric_a.fragmentation_bias - numeric_b.fragmentation_bias),
        abs(numeric_a.ambiguity_bias - numeric_b.ambiguity_bias),
        abs(numeric_a.sentiment_contrast - numeric_b.sentiment_contrast),
        abs(numeric_a.semantic_jump_radius - numeric_b.semantic_jump_radius),
        abs(numeric_a.compression_target - numeric_b.compression_target),
        abs(numeric_a.anchor_rigidity - numeric_b.anchor_rigidity),
    ]
    return sum(deltas) / len(deltas)


def genome_distance(
    genes_a: tuple[SemanticGene, ...],
    genes_b: tuple[SemanticGene, ...],
    numeric_a: NumericGenes,
    numeric_b: NumericGenes,
) -> float:
    """GA §7.3: 0.70 * d_semantic + 0.30 * d_numeric."""
    d_semantic = semantic_genome_distance(genes_a, genes_b)
    d_numeric = numeric_genome_distance(numeric_a, numeric_b)
    return SEMANTIC_WEIGHT * d_semantic + NUMERIC_WEIGHT * d_numeric
