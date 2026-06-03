"""Integration tests for MongoDB persistence client."""

import pytest

pytest.importorskip("testcontainers")

from testcontainers.mongodb import MongoDbContainer  # type: ignore[import-untyped]

from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.health import check_database_health
from mtes.shared.exceptions import MongoDbUnavailableError

pytestmark = pytest.mark.integration


@pytest.fixture
def mongo_connection_string() -> str:
    try:
        with MongoDbContainer("mongo:7") as mongo:
            yield mongo.get_connection_url()
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers unavailable: {exc}")


@pytest.mark.asyncio
async def test_connect_and_ping(mongo_connection_string: str) -> None:
    client = MongoPersistenceClient(mongo_connection_string)
    await client.connect()
    assert await client.ping() is True
    await client.close()
    assert client.is_connected is False


@pytest.mark.asyncio
async def test_health_check_healthy(mongo_connection_string: str) -> None:
    client = MongoPersistenceClient(mongo_connection_string)
    await client.connect()
    result = await check_database_health(client)
    assert result.status == "healthy"
    await client.close()


@pytest.mark.asyncio
async def test_ping_without_connect_raises() -> None:
    client = MongoPersistenceClient("mongodb://localhost:27017/mtes_test")
    with pytest.raises(MongoDbUnavailableError):
        await client.ping()
