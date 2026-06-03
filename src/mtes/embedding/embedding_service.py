"""Embedding service with bootstrap cache policy."""

from dataclasses import dataclass, field
from typing import Any

from mtes.embedding.embedding_adapter import EmbeddingAdapter
from mtes.persistence.repositories.base_repository import CollectionRepository


@dataclass
class EmbeddingCache:
    """In-memory cache keyed by text for calibration reuse."""

    _vectors: dict[str, tuple[float, ...]] = field(default_factory=dict)

    def get(self, text: str) -> tuple[float, ...] | None:
        return self._vectors.get(text)

    def put(self, text: str, vector: tuple[float, ...]) -> None:
        self._vectors[text] = vector

    def invalidate(self) -> None:
        self._vectors.clear()


class EmbeddingService:
    """Generate embeddings with optional cache and model metadata persistence."""

    def __init__(
        self,
        adapter: EmbeddingAdapter,
        *,
        embedding_models_repository: CollectionRepository | None = None,
        cache: EmbeddingCache | None = None,
    ) -> None:
        self._adapter = adapter
        self._embedding_models_repository = embedding_models_repository
        self._cache = cache or EmbeddingCache()

    @property
    def model_id(self) -> str:
        return self._adapter.model_id

    @property
    def dimension(self) -> int:
        return self._adapter.dimension

    async def ensure_model_metadata_persisted(self) -> None:
        if self._embedding_models_repository is None:
            return
        existing = await self._embedding_models_repository.find_by_id(self._adapter.model_id)
        if existing is not None:
            return
        document: dict[str, Any] = {
            "_id": self._adapter.model_id,
            "version": "1.0",
            "dimension": self._adapter.dimension,
            "distance_metric": "cosine",
        }
        await self._embedding_models_repository.insert_one(document)

    async def embed_texts(
        self,
        texts: list[str],
        *,
        use_cache: bool = True,
    ) -> list[tuple[float, ...]]:
        """Embed texts, reusing cached vectors when enabled."""
        if not texts:
            return []

        results: list[tuple[float, ...] | None] = [None] * len(texts)
        pending_texts: list[str] = []
        pending_indexes: list[int] = []

        for index, text in enumerate(texts):
            if use_cache:
                cached = self._cache.get(text)
                if cached is not None:
                    results[index] = cached
                    continue
            pending_indexes.append(index)
            pending_texts.append(text)

        if pending_texts:
            generated = await self._adapter.embed_texts(pending_texts)
            for index, vector in zip(pending_indexes, generated, strict=True):
                results[index] = vector
                if use_cache:
                    self._cache.put(texts[index], vector)

        return [vector for vector in results if vector is not None]

    async def find_top_neighbors_in_memory(
        self,
        query_text: str,
        corpus_texts: list[str],
        *,
        k: int = 20,
        use_cache: bool = True,
    ) -> tuple[str, ...]:
        """Bootstrap §8.2: rank corpus texts by in-memory cosine similarity."""
        from mtes.persistence.in_memory_cosine_retrieval import InMemoryCosineRetrieval

        if not corpus_texts:
            return ()
        vectors = await self.embed_texts(corpus_texts, use_cache=use_cache)
        query_vectors = await self.embed_texts([query_text], use_cache=use_cache)
        query_vector = query_vectors[0]
        corpus = [
            (text, text, vector)
            for text, vector in zip(corpus_texts, vectors, strict=True)
        ]
        matches = InMemoryCosineRetrieval().top_k_neighbors(query_vector, corpus, k=k)
        return tuple(match.label for match in matches)

    async def measure_retrieval_consistency(
        self,
        query_text: str,
        corpus_texts: list[str],
        *,
        k: int = 20,
        run_count: int = 3,
    ) -> float:
        """Bootstrap §8.2 retrieval consistency using in-memory cosine ranking."""
        from mtes.persistence.in_memory_cosine_retrieval import InMemoryCosineRetrieval

        vectors = await self.embed_texts(corpus_texts, use_cache=False)
        query_vectors = await self.embed_texts([query_text], use_cache=False)
        query_vector = query_vectors[0]
        corpus = [
            (text, text, vector)
            for text, vector in zip(corpus_texts, vectors, strict=True)
        ]
        return InMemoryCosineRetrieval().retrieval_consistency(
            query_vector,
            corpus,
            k=k,
            run_count=run_count,
        )
