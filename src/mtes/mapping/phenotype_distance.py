"""Phenotype distance per Mapping Specification §12."""

from dataclasses import dataclass
from typing import Protocol

from mtes.mapping.metrics import punctuation_density, short_clause_ratio
from mtes.mapping.translation_service import TranslatedConstraints
from mtes.mapping.vector_math import cosine_distance

EMBEDDING_WEIGHT = 0.60
STYLOMETRIC_WEIGHT = 0.25
CONSTRAINT_WEIGHT = 0.15


@dataclass(frozen=True, slots=True)
class PhenotypeFeatures:
    text: str
    embedding: tuple[float, ...]
    punctuation_density_value: float
    short_clause_ratio_value: float
    sentiment_shift_value: float


class EmbeddingDistanceProvider(Protocol):
    """Embedding distance abstraction (Phase 4 implementation)."""

    def distance(self, embedding_a: tuple[float, ...], embedding_b: tuple[float, ...]) -> float:
        ...


class CosineEmbeddingDistanceProvider:
    def distance(self, embedding_a: tuple[float, ...], embedding_b: tuple[float, ...]) -> float:
        return cosine_distance(embedding_a, embedding_b)


class PhenotypeDistanceCalculator:
    """Compute phenotype distance from embeddings, stylometrics, and constraints."""

    def __init__(self, embedding_provider: EmbeddingDistanceProvider | None = None) -> None:
        self._embedding_provider = embedding_provider or CosineEmbeddingDistanceProvider()

    def extract_features(self, text: str, embedding: tuple[float, ...]) -> PhenotypeFeatures:
        return PhenotypeFeatures(
            text=text,
            embedding=embedding,
            punctuation_density_value=punctuation_density(text),
            short_clause_ratio_value=short_clause_ratio(text),
            sentiment_shift_value=0.0,
        )

    def stylometric_delta(
        self,
        features_a: PhenotypeFeatures,
        features_b: PhenotypeFeatures,
    ) -> float:
        """Mapping Spec §12.2 mean absolute delta of stylometric components."""
        deltas = [
            abs(features_a.punctuation_density_value - features_b.punctuation_density_value),
            abs(features_a.short_clause_ratio_value - features_b.short_clause_ratio_value),
            abs(features_a.sentiment_shift_value - features_b.sentiment_shift_value),
        ]
        return sum(deltas) / len(deltas)

    def constraint_deviation(
        self,
        features: PhenotypeFeatures,
        constraints: TranslatedConstraints,
    ) -> float:
        """Mapping Spec §12.3 mean absolute error against normalized targets."""
        deltas = [
            abs(features.punctuation_density_value - constraints.punctuation_density),
            abs(features.short_clause_ratio_value - constraints.short_clause_ratio),
            abs(features.sentiment_shift_value - constraints.required_sentiment_shift),
        ]
        return sum(deltas) / len(deltas)

    def phenotype_distance(
        self,
        features_a: PhenotypeFeatures,
        features_b: PhenotypeFeatures,
        *,
        constraints_a: TranslatedConstraints | None = None,
        constraints_b: TranslatedConstraints | None = None,
    ) -> float:
        embedding_distance = self._embedding_provider.distance(
            features_a.embedding,
            features_b.embedding,
        )
        stylometric = self.stylometric_delta(features_a, features_b)
        constraint_component = 0.0
        if constraints_a is not None and constraints_b is not None:
            constraint_component = (
                self.constraint_deviation(features_a, constraints_a)
                + self.constraint_deviation(features_b, constraints_b)
            ) / 2.0
        distance = (
            EMBEDDING_WEIGHT * embedding_distance
            + STYLOMETRIC_WEIGHT * stylometric
            + CONSTRAINT_WEIGHT * constraint_component
        )
        return max(0.0, min(1.0, distance))
