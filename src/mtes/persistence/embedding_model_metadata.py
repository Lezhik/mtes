"""Embedding model metadata helpers (no Atlas-specific features)."""

from mtes.persistence.repositories.base_repository import CollectionRepository
from mtes.shared.exceptions import ConfigurationError, MongoDbUnavailableError


async def resolve_embedding_dimension(
    embedding_models: CollectionRepository,
    model_id: str | None,
) -> tuple[str, int]:
    """Load embedding dimension from embedding_models collection."""
    if model_id is not None:
        model_document = await embedding_models.find_one({"_id": model_id})
    else:
        model_document = await embedding_models.find_one({})

    if model_document is None:
        raise MongoDbUnavailableError(
            "embedding_models must contain at least one model before retrieval setup"
        )

    dimension = model_document.get("dimension")
    if not isinstance(dimension, int) or dimension <= 0:
        raise ConfigurationError("embedding_models.dimension must be a positive integer")

    resolved_id = str(model_document.get("_id", model_id or "unknown"))
    return resolved_id, dimension
