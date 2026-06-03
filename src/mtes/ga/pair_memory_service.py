"""Pair memory penalty tracking per GA Specification §9.3."""

from dataclasses import dataclass

PAIR_MEMORY_HALF_LIFE_GENERATIONS = 20


@dataclass
class PairMemoryEntry:
    genome_id_a: str
    genome_id_b: str
    use_count: int
    last_used_generation: int
    current_penalty: float


class PairMemoryService:
    """Exponential decay penalties for repeated parent pairs."""

    def __init__(self, *, half_life_generations: int = PAIR_MEMORY_HALF_LIFE_GENERATIONS) -> None:
        self._half_life = half_life_generations
        self._entries: dict[tuple[str, str], PairMemoryEntry] = {}

    @staticmethod
    def canonical_pair(genome_id_a: str, genome_id_b: str) -> tuple[str, str]:
        if genome_id_a < genome_id_b:
            return genome_id_a, genome_id_b
        return genome_id_b, genome_id_a

    def decay_factor(self, generations_elapsed: int) -> float:
        if generations_elapsed <= 0:
            return 1.0
        return 0.5 ** (generations_elapsed / self._half_life)

    def get_penalty(self, genome_id_a: str, genome_id_b: str, *, current_generation: int) -> float:
        key = self.canonical_pair(genome_id_a, genome_id_b)
        entry = self._entries.get(key)
        if entry is None:
            return 0.0
        elapsed = current_generation - entry.last_used_generation
        return entry.current_penalty * self.decay_factor(elapsed)

    def record_use(
        self,
        genome_id_a: str,
        genome_id_b: str,
        *,
        current_generation: int,
        base_penalty: float = 0.34,
    ) -> PairMemoryEntry:
        key = self.canonical_pair(genome_id_a, genome_id_b)
        existing = self._entries.get(key)
        if existing is None:
            entry = PairMemoryEntry(
                genome_id_a=key[0],
                genome_id_b=key[1],
                use_count=1,
                last_used_generation=current_generation,
                current_penalty=base_penalty,
            )
        else:
            entry = PairMemoryEntry(
                genome_id_a=key[0],
                genome_id_b=key[1],
                use_count=existing.use_count + 1,
                last_used_generation=current_generation,
                current_penalty=min(1.0, existing.current_penalty + 0.05),
            )
        self._entries[key] = entry
        return entry
