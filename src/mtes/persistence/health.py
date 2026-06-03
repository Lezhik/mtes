"""Database health checks for monitoring integration."""

from dataclasses import dataclass
from typing import Literal

from mtes.persistence.client import MongoPersistenceClient
from mtes.shared.exceptions import MongoDbUnavailableError

DatabaseHealthStatus = Literal["healthy", "unhealthy"]


@dataclass(frozen=True, slots=True)
class DatabaseHealthResult:
    status: DatabaseHealthStatus
    message: str


async def check_database_health(client: MongoPersistenceClient) -> DatabaseHealthResult:
    """Perform a read-only database ping for health endpoints."""
    try:
        await client.ping()
    except MongoDbUnavailableError as exc:
        return DatabaseHealthResult(status="unhealthy", message=str(exc))
    return DatabaseHealthResult(status="healthy", message="MongoDB ping succeeded")
