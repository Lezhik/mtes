"""Fitness evaluation per Mapping Specification v5.0 §7."""

from dataclasses import dataclass
from typing import Protocol

from mtes.mapping.metrics import compression_score, indirect_reference_ratio
from mtes.mapping.translation_service import TranslatedConstraints

PROXY_WEIGHT_CAP = 0.30

FITNESS_WEIGHTS = {
    "anchor_integrity": 0.35,
    "compression_score": 0.20,
    "local_novelty": 0.20,
    "readability_floor": 0.10,
    "human_style_score": 0.03,
    "ambiguity_score": 0.05,
    "sentiment_contrast_score": 0.05,
    "fragmentation_alignment": 0.02,
}


def fragmentation_alignment_stub(
    candidate_text: str,
    constraints: TranslatedConstraints,
) -> float:
    """Lightweight fragmentation proxy until full stylometric pipeline is wired."""
    from mtes.mapping.metrics import punctuation_density, short_clause_ratio

    observed = (
        punctuation_density(candidate_text),
        short_clause_ratio(candidate_text),
    )
    target = (
        constraints.punctuation_density,
        constraints.short_clause_ratio,
    )
    errors = [abs(observed[index] - target[index]) for index in range(2)]
    return max(0.0, 1.0 - (sum(errors) / len(errors)))


@dataclass(frozen=True, slots=True)
class FitnessInputs:
    candidate_text: str
    anchor_integrity: float
    local_novelty: float
    readability_floor: float = 0.80
    human_style_score: float = 0.50
    ambiguity_score: float | None = None
    sentiment_contrast_score: float = 0.0
    repair_cost_penalty: float = 0.0


@dataclass(frozen=True, slots=True)
class FitnessResult:
    fitness: float
    pre_repair_fitness: float
    components: dict[str, float]
    formula_version: str = "5.0"


class FitnessRecordRepository(Protocol):
    async def save_fitness_record(
        self,
        *,
        candidate_id: str,
        genome_id: str,
        result: FitnessResult,
    ) -> str:
        ...


class FitnessEvaluator:
    """Compute post-repair fitness for selection and pre-repair for diagnostics."""

    def calculate_fitness(
        self,
        inputs: FitnessInputs,
        constraints: TranslatedConstraints,
    ) -> FitnessResult:
        ambiguity = (
            inputs.ambiguity_score
            if inputs.ambiguity_score is not None
            else indirect_reference_ratio(inputs.candidate_text)
        )
        components = {
            "anchor_integrity": inputs.anchor_integrity,
            "compression_score": compression_score(inputs.candidate_text),
            "local_novelty": inputs.local_novelty,
            "readability_floor": inputs.readability_floor,
            "human_style_score": inputs.human_style_score,
            "ambiguity_score": ambiguity,
            "sentiment_contrast_score": inputs.sentiment_contrast_score,
            "fragmentation_alignment": fragmentation_alignment_stub(
                inputs.candidate_text,
                constraints,
            ),
        }
        proxy_total = (
            components["human_style_score"] * FITNESS_WEIGHTS["human_style_score"]
            + components["ambiguity_score"] * FITNESS_WEIGHTS["ambiguity_score"]
            + components["sentiment_contrast_score"] * FITNESS_WEIGHTS["sentiment_contrast_score"]
        )
        if proxy_total > PROXY_WEIGHT_CAP:
            raise ValueError("proxy metric weight contribution exceeds cap")

        weighted = sum(
            components[key] * FITNESS_WEIGHTS[key]
            for key in FITNESS_WEIGHTS
            if key in components
        )
        fitness = max(0.0, weighted - inputs.repair_cost_penalty)
        return FitnessResult(
            fitness=fitness,
            pre_repair_fitness=fitness,
            components=components,
        )

    def apply_repair_penalty(
        self,
        result: FitnessResult,
        *,
        repair_cost_penalty: float,
    ) -> FitnessResult:
        post_repair = max(0.0, result.pre_repair_fitness - repair_cost_penalty)
        return FitnessResult(
            fitness=post_repair,
            pre_repair_fitness=result.pre_repair_fitness,
            components=result.components,
        )
