"""Deterministic structural plan per Mapping Specification §8."""

from dataclasses import dataclass
from enum import StrEnum

from mtes.mapping.relation_graph_service import RelationType


class RhetoricalMode(StrEnum):
    FRAGMENTED = "fragmented"
    DECLARATIVE = "declarative"
    JUXTAPOSED = "juxtaposed"
    EMPHATIC = "emphatic"
    REFLECTIVE = "reflective"
    OBSERVATIONAL = "observational"


class SentimentPattern(StrEnum):
    FLAT = "flat"
    NEGATIVE_TO_NEUTRAL = "negative_to_neutral"
    NEGATIVE_TO_POSITIVE = "negative_to_positive"


RELATION_PRIORITY: tuple[RelationType, ...] = (
    RelationType.REINFORCEMENT,
    RelationType.CONTRAST,
    RelationType.TENSION,
    RelationType.ASSOCIATIVE,
    RelationType.DISTANT,
)


@dataclass(frozen=True, slots=True)
class StructuralPlan:
    anchors: tuple[str, ...]
    relation_focus: RelationType
    rhetorical_mode: RhetoricalMode
    sentiment_pattern: SentimentPattern


class StructuralPlanService:
    """Generate structural plan from anchors, relation graph, and gene constraints."""

    def lookup_rhetorical_mode(
        self,
        relation: RelationType,
        *,
        short_clause_ratio: float,
    ) -> RhetoricalMode:
        is_short = short_clause_ratio >= 0.50
        if relation == RelationType.TENSION:
            return RhetoricalMode.FRAGMENTED if is_short else RhetoricalMode.DECLARATIVE
        if relation == RelationType.CONTRAST:
            return RhetoricalMode.JUXTAPOSED
        if relation == RelationType.REINFORCEMENT:
            return RhetoricalMode.EMPHATIC if is_short else RhetoricalMode.REFLECTIVE
        return RhetoricalMode.OBSERVATIONAL

    def lookup_sentiment_pattern(self, required_sentiment_shift: float) -> SentimentPattern:
        if required_sentiment_shift < 0.20:
            return SentimentPattern.FLAT
        if required_sentiment_shift <= 0.50:
            return SentimentPattern.NEGATIVE_TO_NEUTRAL
        return SentimentPattern.NEGATIVE_TO_POSITIVE

    def dominant_relation_type(
        self,
        relation_counts: dict[RelationType, int],
    ) -> RelationType:
        if not relation_counts:
            return RelationType.ASSOCIATIVE
        max_count = max(relation_counts.values())
        candidates = [
            relation for relation, count in relation_counts.items() if count == max_count
        ]
        for relation in RELATION_PRIORITY:
            if relation in candidates:
                return relation
        return candidates[0]

    def build_plan(
        self,
        *,
        anchors: tuple[str, ...],
        relation_counts: dict[RelationType, int],
        short_clause_ratio: float,
        required_sentiment_shift: float,
    ) -> StructuralPlan:
        relation_focus = self.dominant_relation_type(relation_counts)
        return StructuralPlan(
            anchors=anchors,
            relation_focus=relation_focus,
            rhetorical_mode=self.lookup_rhetorical_mode(
                relation_focus,
                short_clause_ratio=short_clause_ratio,
            ),
            sentiment_pattern=self.lookup_sentiment_pattern(required_sentiment_shift),
        )
