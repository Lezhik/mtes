"""Unit tests for embedding model metadata resolution."""

from unittest.mock import AsyncMock

import pytest

from mtes.persistence.embedding_model_metadata import resolve_embedding_dimension
from mtes.shared.exceptions import ConfigurationError, MongoDbUnavailableError


@pytest.mark.asyncio
async def test_resolve_embedding_dimension_from_model_id() -> None:
    repository = AsyncMock()
    repository.find_one.return_value = {
        "_id": "e5-large",
        "dimension": 1024,
    }
    model_id, dimension = await resolve_embedding_dimension(repository, "e5-large")
    assert model_id == "e5-large"
    assert dimension == 1024


@pytest.mark.asyncio
async def test_resolve_embedding_dimension_requires_model() -> None:
    repository = AsyncMock()
    repository.find_one.return_value = None
    with pytest.raises(MongoDbUnavailableError):
        await resolve_embedding_dimension(repository, None)


@pytest.mark.asyncio
async def test_resolve_embedding_dimension_validates_dimension() -> None:
    repository = AsyncMock()
    repository.find_one.return_value = {"_id": "bad", "dimension": 0}
    with pytest.raises(ConfigurationError):
        await resolve_embedding_dimension(repository, "bad")
