"""Embedding provider abstraction."""

from typing import Protocol


class EmbeddingAdapter(Protocol):
    """Provider-independent embedding generation."""

    @property
    def model_id(self) -> str:
        ...

    @property
    def dimension(self) -> int:
        ...

    async def embed_texts(self, texts: list[str]) -> list[tuple[float, ...]]:
        ...
