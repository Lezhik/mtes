"""P4 prompt family routing per LLM Interaction Specification §6."""

from dataclasses import dataclass
from enum import StrEnum

from mtes.shared.types import NumericGenes

ACTIVATION_THRESHOLD = 0.70
HYSTERESIS_DELTA = 0.10

FAMILY_PRIORITY = (
    "P4-B",
    "P4-D",
    "P4-C",
    "P4-E",
    "P4-A",
)


class PromptFamily(StrEnum):
    P4_A = "P4-A"
    P4_B = "P4-B"
    P4_C = "P4-C"
    P4_D = "P4-D"
    P4_E = "P4-E"
    P4_F = "P4-F"


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    selected_family: PromptFamily
    activated_families: tuple[str, ...]
    activation_scores: dict[str, float]


class PromptRouter:
    """Select P4 prompt family from numeric gene activation scores."""

    def activation_scores(self, numeric_genes: NumericGenes) -> dict[str, float]:
        return {
            "P4-B": numeric_genes.anchor_rigidity,
            "P4-C": numeric_genes.fragmentation_bias,
            "P4-D": numeric_genes.compression_target,
            "P4-E": numeric_genes.ambiguity_bias,
        }

    def activated_families(self, numeric_genes: NumericGenes) -> tuple[str, ...]:
        scores = self.activation_scores(numeric_genes)
        activated = [
            family
            for family, score in scores.items()
            if score >= ACTIVATION_THRESHOLD
        ]
        return tuple(sorted(activated, key=lambda family: FAMILY_PRIORITY.index(family)))

    def select_family(
        self,
        numeric_genes: NumericGenes,
        *,
        current_family: PromptFamily | None = None,
        current_family_score: float | None = None,
    ) -> RoutingDecision:
        scores = self.activation_scores(numeric_genes)
        activated = self.activated_families(numeric_genes)

        if len(activated) >= 2:
            return RoutingDecision(
                selected_family=PromptFamily.P4_F,
                activated_families=activated,
                activation_scores=scores,
            )

        if not activated:
            return RoutingDecision(
                selected_family=PromptFamily.P4_A,
                activated_families=(),
                activation_scores=scores,
            )

        candidate_family = activated[0]
        candidate_score = scores[candidate_family]

        if current_family is not None and current_family_score is not None:
            switch_threshold = current_family_score + HYSTERESIS_DELTA
            current_name = current_family.value
            if current_name in scores and candidate_family != current_name:
                if candidate_score <= switch_threshold:
                    return RoutingDecision(
                        selected_family=current_family,
                        activated_families=(current_name,),
                        activation_scores=scores,
                    )

        return RoutingDecision(
            selected_family=PromptFamily(candidate_family),
            activated_families=(candidate_family,),
            activation_scores=scores,
        )
