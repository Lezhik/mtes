"""Tests for relation graph and structural plan services."""

import pytest

from mtes.mapping.relation_graph_service import RelationGraphService, RelationType
from mtes.mapping.structural_plan_service import (
    RhetoricalMode,
    SentimentPattern,
    StructuralPlanService,
)


@pytest.fixture
def relation_service() -> RelationGraphService:
    return RelationGraphService()


def test_assign_relation_type_reinforcement(relation_service: RelationGraphService) -> None:
    relation = relation_service.assign_relation_type(
        cosine_similarity_value=0.85,
        polarity_alignment=0.80,
        rarity_score=0.10,
    )
    assert relation == RelationType.REINFORCEMENT


def test_assign_relation_type_contrast(relation_service: RelationGraphService) -> None:
    relation = relation_service.assign_relation_type(
        cosine_similarity_value=0.70,
        polarity_alignment=0.30,
        rarity_score=0.10,
    )
    assert relation == RelationType.CONTRAST


def test_assign_relation_type_tension(relation_service: RelationGraphService) -> None:
    relation = relation_service.assign_relation_type(
        cosine_similarity_value=0.30,
        polarity_alignment=0.50,
        rarity_score=0.80,
    )
    assert relation == RelationType.TENSION


def test_assign_relation_type_distant(relation_service: RelationGraphService) -> None:
    relation = relation_service.assign_relation_type(
        cosine_similarity_value=0.10,
        polarity_alignment=0.50,
        rarity_score=0.10,
    )
    assert relation == RelationType.DISTANT


def test_edge_score_formula(relation_service: RelationGraphService) -> None:
    score = relation_service.edge_score(
        cosine_similarity_value=0.8,
        polarity_alignment=0.7,
        rarity_score=0.6,
    )
    assert score == pytest.approx(0.50 * 0.8 + 0.30 * 0.7 + 0.20 * 0.6)


def test_structural_plan_sentiment_pattern() -> None:
    service = StructuralPlanService()
    assert service.lookup_sentiment_pattern(0.10) == SentimentPattern.FLAT
    assert service.lookup_sentiment_pattern(0.40) == SentimentPattern.NEGATIVE_TO_NEUTRAL
    assert service.lookup_sentiment_pattern(0.60) == SentimentPattern.NEGATIVE_TO_POSITIVE


def test_structural_plan_rhetorical_mode_tension_short() -> None:
    service = StructuralPlanService()
    mode = service.lookup_rhetorical_mode(RelationType.TENSION, short_clause_ratio=0.80)
    assert mode == RhetoricalMode.FRAGMENTED


def test_build_plan_prefers_reinforcement_on_tie() -> None:
    service = StructuralPlanService()
    plan = service.build_plan(
        anchors=("winter",),
        relation_counts={
            RelationType.CONTRAST: 2,
            RelationType.REINFORCEMENT: 2,
        },
        short_clause_ratio=0.4,
        required_sentiment_shift=0.55,
    )
    assert plan.relation_focus == RelationType.REINFORCEMENT
    assert plan.rhetorical_mode == RhetoricalMode.REFLECTIVE
