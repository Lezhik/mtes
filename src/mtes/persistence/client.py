"""Async MongoDB client lifecycle."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from mtes.persistence.retry_policy import with_infrastructure_retry
from mtes.shared.exceptions import MongoDbUnavailableError


class MongoPersistenceClient:
    """Motor-based persistence client with connect, ping, and close."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string
        self._client: AsyncIOMotorClient[Any] | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def get_database(self, database_name: str | None = None) -> AsyncIOMotorDatabase[Any]:
        if self._client is None:
            raise MongoDbUnavailableError("MongoDB client is not connected")
        if database_name is not None:
            return self._client[database_name]
        default_database = self._client.get_default_database()
        if default_database is None:
            raise MongoDbUnavailableError("Connection string does not include a database name")
        return default_database

    async def connect(self) -> None:
        """Open the Motor client and verify connectivity with retry."""

        async def _connect_and_ping() -> None:
            client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(self._connection_string)
            await client.admin.command("ping")
            if self._client is not None:
                self._client.close()
            self._client = client

        await with_infrastructure_retry(
            _connect_and_ping,
            error_factory=lambda exc: MongoDbUnavailableError(
                f"MongoDB connection failed after {3} attempts: {exc}"
            ),
        )

    async def ping(self) -> bool:
        """Return True when the database responds to a ping command."""

        async def _ping() -> bool:
            if self._client is None:
                raise MongoDbUnavailableError("MongoDB client is not connected")
            await self._client.admin.command("ping")
            return True

        return await with_infrastructure_retry(
            _ping,
            error_factory=lambda exc: MongoDbUnavailableError(
                f"MongoDB ping failed: {exc}"
            ),
        )

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
