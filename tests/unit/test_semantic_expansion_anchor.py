"""Tests for semantic expansion and anchor selection."""

from mtes.mapping.anchor_selection_service import AnchorCandidate, AnchorSelectionService
from mtes.mapping.semantic_expansion_service import EmbeddedTerm, SemanticExpansionService


def test_semantic_expansion_is_deterministic() -> None:
    service = SemanticExpansionService()
    source = [EmbeddedTerm("winter", (1.0, 0.0, 0.0, 0.0))]
    pool = [
        EmbeddedTerm("winter", (1.0, 0.0, 0.0, 0.0)),
        EmbeddedTerm("silence", (0.9, 0.1, 0.0, 0.0)),
        EmbeddedTerm("automation", (0.0, 1.0, 0.0, 0.0)),
    ]
    first = service.expand_terms(
        source_terms=source,
        candidate_pool=pool,
        semantic_expansion_radius=0.2,
    )
    second = service.expand_terms(
        source_terms=source,
        candidate_pool=pool,
        semantic_expansion_radius=0.2,
    )
    assert first == second
    assert "silence" in first
    assert "automation" not in first


def test_anchor_selection_prefers_explicit_anchor() -> None:
    service = AnchorSelectionService()
    anchors = service.select_anchors(
        [
            AnchorCandidate("alpha", position=0, tfidf_score=0.9),
            AnchorCandidate("beta", position=1, tfidf_score=0.1, is_explicit_anchor=True),
        ]
    )
    assert anchors == ("beta",)


def test_anchor_selection_tie_break_by_tfidf() -> None:
    service = AnchorSelectionService()
    anchors = service.select_anchors(
        [
            AnchorCandidate("alpha", position=1, tfidf_score=0.2),
            AnchorCandidate("beta", position=0, tfidf_score=0.8),
        ]
    )
    assert anchors == ("beta",)
