"""Tests for embedding service."""

import hashlib
import math

import pytest

from mtes.embedding.embedding_service import EmbeddingCache, EmbeddingService


class FakeEmbeddingAdapter:
    model_id = "fake-model"
    dimension = 4

    async def embed_texts(self, texts: list[str]) -> list[tuple[float, ...]]:
        vectors: list[tuple[float, ...]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vectors.append(
                tuple(digest[index] / 255.0 for index in range(self.dimension))
            )
        return vectors


@pytest.mark.asyncio
async def test_embed_texts_uses_cache() -> None:
    adapter = FakeEmbeddingAdapter()
    cache = EmbeddingCache()
    service = EmbeddingService(adapter, cache=cache)

    first = await service.embed_texts(["winter", "silence"])
    second = await service.embed_texts(["winter", "silence"])

    assert first == second
    assert len(cache._vectors) == 2


@pytest.mark.asyncio
async def test_retrieval_consistency_on_repeated_runs() -> None:
    """Bootstrap §8.2: stable neighbor rankings across repeated retrieval runs."""
    adapter = FakeEmbeddingAdapter()
    service = EmbeddingService(adapter)

    corpus = ["winter", "silence", "automation", "night"]
    query = "winter"

    def top_tokens(vectors: dict[str, tuple[float, ...]]) -> tuple[str, ...]:
        query_vector = vectors[query]

        def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
            dot = sum(x * y for x, y in zip(a, b, strict=True))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

        ranked = sorted(
            ((token, cosine(query_vector, vector)) for token, vector in vectors.items() if token != query),
            key=lambda item: (-item[1], item[0]),
        )
        return tuple(token for token, _ in ranked[:3])

    rankings: list[tuple[str, ...]] = []
    for _ in range(3):
        vectors_list = await service.embed_texts(corpus, use_cache=False)
        vectors = dict(zip(corpus, vectors_list, strict=True))
        rankings.append(top_tokens(vectors))

    assert rankings[0] == rankings[1] == rankings[2]
