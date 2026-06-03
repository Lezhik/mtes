"""Tests for P4 prompt router."""

from mtes.llm.prompt_router import PromptFamily, PromptRouter
from mtes.shared.types import NumericGenes


def test_default_family_when_no_activation() -> None:
    router = PromptRouter()
    genes = NumericGenes(0.5, 0.4, 0.4, 0.3, 0.5, 0.5)
    decision = router.select_family(genes)
    assert decision.selected_family == PromptFamily.P4_A


def test_anchor_family_activates_at_threshold() -> None:
    router = PromptRouter()
    genes = NumericGenes(0.5, 0.4, 0.4, 0.3, 0.5, 0.75)
    decision = router.select_family(genes)
    assert decision.selected_family == PromptFamily.P4_B


def test_combined_mode_when_two_families_active() -> None:
    router = PromptRouter()
    genes = NumericGenes(0.75, 0.4, 0.4, 0.3, 0.5, 0.75)
    decision = router.select_family(genes)
    assert decision.selected_family == PromptFamily.P4_F
    assert len(decision.activated_families) >= 2


def test_hysteresis_keeps_current_family() -> None:
    router = PromptRouter()
    genes = NumericGenes(0.5, 0.4, 0.4, 0.3, 0.5, 0.72)
    decision = router.select_family(
        genes,
        current_family=PromptFamily.P4_B,
        current_family_score=0.75,
    )
    assert decision.selected_family == PromptFamily.P4_B
