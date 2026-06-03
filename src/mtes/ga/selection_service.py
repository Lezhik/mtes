"""Parent selection per GA Specification §9."""

import random
from dataclasses import dataclass

POOL_EXPLOITATION = 0.70
POOL_NOVELTY = 0.20
POOL_EXPLORATION = 0.10
INTER_POOL_CROSSOVER_PROBABILITY = 0.20


@dataclass(frozen=True, slots=True)
class ParentCandidate:
    genome_id: str
    fitness_rank: float
    compatibility: float
    novelty: float
    diversity_bonus: float
    pool: str


class SelectionService:
    """Select parents using weighted parent score."""

    def __init__(self, *, random_source: random.Random | None = None) -> None:
        self._random = random_source or random.Random()

    def parent_score(self, candidate: ParentCandidate) -> float:
        return (
            0.50 * candidate.fitness_rank
            + 0.25 * candidate.compatibility
            + 0.15 * candidate.novelty
            + 0.10 * candidate.diversity_bonus
        )

    def assign_pool(self, candidate: ParentCandidate, *, rank_percentile: float) -> str:
        if rank_percentile <= POOL_EXPLOITATION:
            return "exploitation"
        if rank_percentile <= POOL_EXPLOITATION + POOL_NOVELTY:
            return "novelty"
        return "exploration"

    def select_parents(
        self,
        candidates: list[ParentCandidate],
        *,
        count: int = 2,
    ) -> tuple[ParentCandidate, ...]:
        ranked = sorted(candidates, key=self.parent_score, reverse=True)
        if len(ranked) < count:
            raise ValueError("insufficient candidates for parent selection")
        if self._random.random() < INTER_POOL_CROSSOVER_PROBABILITY and len(ranked) >= count:
            pools = {candidate.pool for candidate in ranked}
            if len(pools) >= 2:
                first = self._random.choice(ranked)
                different_pool = [item for item in ranked if item.pool != first.pool]
                second = self._random.choice(different_pool)
                return first, second
        return tuple(ranked[:count])
