"""Relation graph construction per Mapping Specification §7 and v5.0 §3."""

from dataclasses import dataclass
from enum import StrEnum

from mtes.mapping.vector_math import cosine_similarity

RARITY_CORPUS_HASH = "mtes-twitter-corpus-v1-sha256:8d13c9e4a1"


class RelationType(StrEnum):
    REINFORCEMENT = "reinforcement"
    CONTRAST = "contrast"
    TENSION = "tension"
    ASSOCIATIVE = "associative"
    DISTANT = "distant"


@dataclass(frozen=True, slots=True)
class RelationEdge:
    source_token: str
    target_token: str
    relation_type: RelationType
    edge_score: float
    cosine_similarity: float
    polarity_alignment: float
    rarity_score: float


class RelationGraphService:
    """Build relation edges and assign types using ordered v5.0 rules."""

    def edge_score(
        self,
        *,
        cosine_similarity_value: float,
        polarity_alignment: float,
        rarity_score: float,
    ) -> float:
        # Mapping Specification §7.1
        return (
            0.50 * cosine_similarity_value
            + 0.30 * polarity_alignment
            + 0.20 * rarity_score
        )

    def polarity_alignment(self, sentiment_a: float, sentiment_b: float) -> float:
        # Mapping Specification v5.0 §5
        return 1.0 - abs(sentiment_a - sentiment_b)

    def assign_relation_type(
        self,
        *,
        cosine_similarity_value: float,
        polarity_alignment: float,
        rarity_score: float,
    ) -> RelationType:
        """Ordered evaluation per Mapping Specification v5.0 §3."""
        if cosine_similarity_value >= 0.80 and polarity_alignment >= 0.70:
            return RelationType.REINFORCEMENT
        if cosine_similarity_value >= 0.60 and polarity_alignment <= 0.40:
            return RelationType.CONTRAST
        if cosine_similarity_value <= 0.35 and rarity_score >= 0.70:
            return RelationType.TENSION
        if cosine_similarity_value >= 0.50:
            return RelationType.ASSOCIATIVE
        return RelationType.DISTANT

    def build_edge(
        self,
        *,
        source_token: str,
        target_token: str,
        embedding_a: tuple[float, ...],
        embedding_b: tuple[float, ...],
        sentiment_a: float,
        sentiment_b: float,
        rarity_score: float,
    ) -> RelationEdge:
        cosine_value = cosine_similarity(embedding_a, embedding_b)
        polarity = self.polarity_alignment(sentiment_a, sentiment_b)
        score = self.edge_score(
            cosine_similarity_value=cosine_value,
            polarity_alignment=polarity,
            rarity_score=rarity_score,
        )
        relation_type = self.assign_relation_type(
            cosine_similarity_value=cosine_value,
            polarity_alignment=polarity,
            rarity_score=rarity_score,
        )
        return RelationEdge(
            source_token=source_token,
            target_token=target_token,
            relation_type=relation_type,
            edge_score=score,
            cosine_similarity=cosine_value,
            polarity_alignment=polarity,
            rarity_score=rarity_score,
        )
