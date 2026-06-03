"""Locality calibration per Bootstrap Specification §11."""

from dataclasses import dataclass
from math import sqrt
from typing import Sequence

from mtes.core.golden_loaders import GoldenDatasetRecord
from mtes.mapping.genotype_distance import genome_distance
from mtes.mapping.phenotype_distance import PhenotypeDistanceCalculator
from mtes.mapping.translation_service import translate_numeric_genes

LOCALITY_STABILITY_STD_MAX = 0.05
LOCALITY_MANDATORY_MIN = 0.45
LOCALITY_BORDERLINE_MAX = 0.50
MIN_CALIBRATION_RUNS = 3


class CalibrationFailedError(Exception):
    """Raised when locality stability or acceptance criteria fail."""


def spearman_rank_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman rank correlation without external dependencies."""
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) < 2:
        return 0.0
    rank_x = _average_ranks(x)
    rank_y = _average_ranks(y)
    mean_x = sum(rank_x) / len(rank_x)
    mean_y = sum(rank_y) / len(rank_y)
    covariance = sum((rank_x[i] - mean_x) * (rank_y[i] - mean_y) for i in range(len(rank_x)))
    variance_x = sum((value - mean_x) ** 2 for value in rank_x)
    variance_y = sum((value - mean_y) ** 2 for value in rank_y)
    if variance_x == 0.0 or variance_y == 0.0:
        return 0.0
    return covariance / sqrt(variance_x * variance_y)


def _average_ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        tie_end = index
        while tie_end + 1 < len(indexed) and indexed[tie_end + 1][1] == indexed[index][1]:
            tie_end += 1
        average_rank = (index + tie_end) / 2.0 + 1.0
        for position in range(index, tie_end + 1):
            original_index = indexed[position][0]
            ranks[original_index] = average_rank
        index = tie_end + 1
    return ranks


def expected_pair_count(genome_count: int) -> int:
    """Bootstrap §11.4: n genomes produce n*(n-1)/2 pairs."""
    return genome_count * (genome_count - 1) // 2


@dataclass(frozen=True, slots=True)
class LocalityCalibrationResult:
    locality_correlation: float
    pair_count: int
    genotype_distances: tuple[float, ...]
    phenotype_distances: tuple[float, ...]


@dataclass
class LocalityCalibrationService:
    """Compute genotype–phenotype Spearman correlation on the full golden dataset."""

    phenotype_distance_calculator: PhenotypeDistanceCalculator | None = None

    def __post_init__(self) -> None:
        if self.phenotype_distance_calculator is None:
            self.phenotype_distance_calculator = PhenotypeDistanceCalculator()

    def calibrate_once(self, records: Sequence[GoldenDatasetRecord]) -> LocalityCalibrationResult:
        """
        Bootstrap §11.4: all genome pairs, no subsampling.

        Embeddings are taken from records (computed once upstream per run).
        """
        genotype_distances: list[float] = []
        phenotype_distances: list[float] = []
        calculator = self.phenotype_distance_calculator
        assert calculator is not None

        for left_index in range(len(records)):
            left = records[left_index]
            left_features = calculator.extract_features(left.phenotype_text, left.embedding)
            left_constraints = translate_numeric_genes(left.genome.numeric_genes)
            for right_index in range(left_index + 1, len(records)):
                right = records[right_index]
                genotype_distances.append(
                    genome_distance(
                        left.genome.semantic_genes,
                        right.genome.semantic_genes,
                        left.genome.numeric_genes,
                        right.genome.numeric_genes,
                    )
                )
                right_features = calculator.extract_features(right.phenotype_text, right.embedding)
                right_constraints = translate_numeric_genes(right.genome.numeric_genes)
                phenotype_distances.append(
                    calculator.phenotype_distance(
                        left_features,
                        right_features,
                        constraints_a=left_constraints,
                        constraints_b=right_constraints,
                    )
                )

        correlation = spearman_rank_correlation(genotype_distances, phenotype_distances)
        return LocalityCalibrationResult(
            locality_correlation=correlation,
            pair_count=len(genotype_distances),
            genotype_distances=tuple(genotype_distances),
            phenotype_distances=tuple(phenotype_distances),
        )

    def calibrate_with_stability(
        self,
        records: Sequence[GoldenDatasetRecord],
        *,
        run_count: int = MIN_CALIBRATION_RUNS,
    ) -> tuple[float, float]:
        """
        Bootstrap §11.5–11.6: mean correlation across runs; std must be ≤ 0.05.
        """
        if run_count < MIN_CALIBRATION_RUNS:
            raise ValueError(f"run_count must be at least {MIN_CALIBRATION_RUNS}")
        correlations = [self.calibrate_once(records).locality_correlation for _ in range(run_count)]
        mean_value = sum(correlations) / len(correlations)
        if len(correlations) < 2:
            std_value = 0.0
        else:
            variance = sum((value - mean_value) ** 2 for value in correlations) / len(correlations)
            std_value = sqrt(variance)
        if std_value > LOCALITY_STABILITY_STD_MAX:
            raise CalibrationFailedError(
                f"locality stability std {std_value:.4f} exceeds {LOCALITY_STABILITY_STD_MAX}"
            )
        return mean_value, std_value
