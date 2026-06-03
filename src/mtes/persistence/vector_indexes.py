"""Vector search index creation helpers."""

from typing import Any

from mtes.persistence.repositories.base_repository import CollectionRepository
from mtes.shared.exceptions import ConfigurationError, MongoDbUnavailableError

VECTOR_INDEXED_COLLECTIONS: tuple[tuple[str, str], ...] = (
    ("dictionary_terms", "embedding"),
    ("candidate_archive", "embedding"),
    ("tweet_archive", "embedding"),
)


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
            "embedding_models must contain at least one model before index creation"
        )

    dimension = model_document.get("dimension")
    if not isinstance(dimension, int) or dimension <= 0:
        raise ConfigurationError("embedding_models.dimension must be a positive integer")

    resolved_id = str(model_document.get("_id", model_id or "unknown"))
    return resolved_id, dimension


async def create_vector_indexes(
    database: Any,
    *,
    dimension: int,
) -> list[str]:
    """Create vector search indexes for all embedding-backed collections."""
    created_indexes: list[str] = []
    for collection_name, vector_field in VECTOR_INDEXED_COLLECTIONS:
        index_name = f"{collection_name}_{vector_field}_vector"
        await database[collection_name].create_search_index(
            {
                "name": index_name,
                "type": "vectorSearch",
                "definition": {
                    "fields": [
                        {
                            "type": "vector",
                            "path": vector_field,
                            "numDimensions": dimension,
                            "similarity": "cosine",
                        }
                    ]
                },
            }
        )
        created_indexes.append(index_name)
    return created_indexes
