"""Unit tests for in-memory cosine retrieval."""

import pytest

from mtes.persistence.in_memory_cosine_retrieval import (
    BOOTSTRAP_RETRIEVAL_CONSISTENCY_MIN,
    InMemoryCosineRetrieval,
    build_embedding_corpus,
)


def test_top_k_neighbors_orders_by_cosine_similarity() -> None:
    retrieval = InMemoryCosineRetrieval()
    corpus = [
        ("a", "token-a", (1.0, 0.0)),
        ("b", "token-b", (0.9, 0.1)),
        ("c", "token-c", (0.0, 1.0)),
    ]
    matches = retrieval.top_k_neighbors((1.0, 0.0), corpus, k=2)
    assert [match.document_id for match in matches] == ["a", "b"]


def test_retrieval_consistency_is_perfect_for_static_corpus() -> None:
    retrieval = InMemoryCosineRetrieval()
    corpus = [
        ("1", "winter", (1.0, 0.0, 0.0)),
        ("2", "silence", (0.8, 0.2, 0.0)),
        ("3", "night", (0.0, 1.0, 0.0)),
    ]
    consistency = retrieval.retrieval_consistency((1.0, 0.0, 0.0), corpus, k=2, run_count=5)
    assert consistency == pytest.approx(1.0)
    assert consistency >= BOOTSTRAP_RETRIEVAL_CONSISTENCY_MIN


def test_build_embedding_corpus_skips_invalid_vectors() -> None:
    corpus = build_embedding_corpus(
        [
            {"_id": "ok", "token": "winter", "embedding": [1.0, 0.0]},
            {"_id": "bad", "token": "broken", "embedding": []},
        ]
    )
    assert len(corpus) == 1
    assert corpus[0][1] == "winter"
