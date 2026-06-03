"""Tests for genotype and phenotype distance calculators."""

import pytest

from mtes.mapping.genotype_distance import (
    genome_distance,
    numeric_genome_distance,
    semantic_coordinate_distance,
)
from mtes.mapping.phenotype_distance import PhenotypeDistanceCalculator, PhenotypeFeatures
from mtes.mapping.translation_service import MVP_NUMERIC_DEFAULTS, translate_numeric_genes
from mtes.shared.types import NumericGenes, SemanticGene


def test_semantic_coordinate_distance_max_axes() -> None:
    distance = semantic_coordinate_distance((0, 0, 0, 0, 0), (7, 7, 7, 7, 7))
    assert distance == pytest.approx(35 / 35)


def test_numeric_genome_distance_identical() -> None:
    assert numeric_genome_distance(MVP_NUMERIC_DEFAULTS, MVP_NUMERIC_DEFAULTS) == 0.0


def test_genome_distance_hand_calculated() -> None:
    genes_a = (SemanticGene(gene_id=1, coordinate=(0, 0, 0, 0, 0), anchor="a"),)
    genes_b = (SemanticGene(gene_id=1, coordinate=(1, 0, 0, 0, 0), anchor="b"),)
    numeric_a = NumericGenes(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    numeric_b = NumericGenes(0.6, 0.5, 0.5, 0.5, 0.5, 0.5)
    expected = 0.70 * (1 / 35) + 0.30 * ((0.1) / 6)
    assert genome_distance(genes_a, genes_b, numeric_a, numeric_b) == pytest.approx(expected)


def test_phenotype_distance_identical_embeddings() -> None:
    calculator = PhenotypeDistanceCalculator()
    constraints = translate_numeric_genes(MVP_NUMERIC_DEFAULTS)
    features = PhenotypeFeatures(
        text="winter silence",
        embedding=(1.0, 0.0),
        punctuation_density_value=0.0,
        short_clause_ratio_value=1.0,
        sentiment_shift_value=0.0,
    )
    distance = calculator.phenotype_distance(features, features, constraints_a=constraints, constraints_b=constraints)
    assert distance == pytest.approx(0.0, abs=0.01)
