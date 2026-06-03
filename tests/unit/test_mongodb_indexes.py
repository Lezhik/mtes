"""Unit tests for standard MongoDB index bootstrap."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mtes.persistence.mongodb_indexes import ensure_mongodb_indexes


@pytest.mark.asyncio
async def test_ensure_mongodb_indexes_creates_standard_indexes() -> None:
    database = MagicMock()
    collection = AsyncMock()
    database.__getitem__.return_value = collection

    ensured = await ensure_mongodb_indexes(database)

    assert any("dictionary_terms" in name for name in ensured)
    assert collection.create_index.await_count >= 1
