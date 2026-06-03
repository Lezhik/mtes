"""Anchor selection per Mapping Specification §6."""

import math
from dataclasses import dataclass

from mtes.mapping.vector_math import cosine_similarity


@dataclass(frozen=True, slots=True)
class AnchorCandidate:
    token: str
    position: int
    tfidf_score: float = 0.0
    embedding_centrality: float = 0.0
    is_explicit_anchor: bool = False


class AnchorSelectionService:
    """Select anchors using priority chain and deterministic tie-breaks."""

    def select_anchors(
        self,
        candidates: list[AnchorCandidate],
        *,
        max_anchors: int = 1,
    ) -> tuple[str, ...]:
        if not candidates:
            return ()

        ranked = sorted(
            candidates,
            key=lambda candidate: (
                0 if candidate.is_explicit_anchor else 1,
                -candidate.tfidf_score,
                -candidate.embedding_centrality,
                candidate.position,
                candidate.token,
            ),
        )
        return tuple(candidate.token for candidate in ranked[:max_anchors])

    def compute_tfidf_scores(
        self,
        tokens: list[str],
        *,
        corpus_documents: list[list[str]],
    ) -> dict[str, float]:
        """Compute simplified TF-IDF centrality scores for tokens in a document."""
        if not tokens:
            return {}

        document_frequency: dict[str, int] = {}
        for document in corpus_documents:
            unique_tokens = set(document)
            for token in unique_tokens:
                document_frequency[token] = document_frequency.get(token, 0) + 1

        document_count = max(len(corpus_documents), 1)
        scores: dict[str, float] = {}
        token_counts: dict[str, int] = {}
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1

        for token, term_frequency in token_counts.items():
            doc_freq = document_frequency.get(token, 0)
            idf = math.log((1 + document_count) / (1 + doc_freq)) + 1.0
            scores[token] = term_frequency * idf
        return scores

    def compute_embedding_centrality(
        self,
        token: str,
        *,
        token_embeddings: dict[str, tuple[float, ...]],
    ) -> float:
        """Mean cosine similarity to all other tokens in the pool."""
        target = token_embeddings.get(token)
        if target is None:
            return 0.0
        similarities = [
            cosine_similarity(target, other)
            for other_token, other in token_embeddings.items()
            if other_token != token
        ]
        if not similarities:
            return 0.0
        return sum(similarities) / len(similarities)
