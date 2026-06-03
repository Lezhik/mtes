"""Tests for embedding service."""

import hashlib

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
    consistency = await service.measure_retrieval_consistency("winter", corpus, k=3, run_count=3)
    assert consistency == 1.0
