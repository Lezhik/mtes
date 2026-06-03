"""Semantic expansion per Mapping Specification §5."""

from dataclasses import dataclass
from typing import Protocol

from mtes.mapping.vector_math import cosine_distance


@dataclass(frozen=True, slots=True)
class EmbeddedTerm:
    token: str
    embedding: tuple[float, ...]


class EmbeddingProvider(Protocol):
    """Embedding generation abstraction (implemented in Phase 4)."""

    async def embed_texts(self, texts: list[str]) -> list[tuple[float, ...]]:
        ...


class SemanticExpansionService:
    """Deterministic nearest-neighbor expansion with cosine distance filter."""

    def expand_terms(
        self,
        *,
        source_terms: list[EmbeddedTerm],
        candidate_pool: list[EmbeddedTerm],
        semantic_expansion_radius: float,
    ) -> tuple[str, ...]:
        """Return candidate tokens with cosine_distance <= radius, sorted deterministically."""
        expanded: list[tuple[str, float]] = []
        for candidate in candidate_pool:
            best_distance = min(
                cosine_distance(source.embedding, candidate.embedding) for source in source_terms
            )
            if best_distance <= semantic_expansion_radius:
                expanded.append((candidate.token, best_distance))
        expanded.sort(key=lambda item: (item[1], item[0]))
        return tuple(token for token, _ in expanded)
