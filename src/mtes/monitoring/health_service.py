"""Health endpoint assembly per SRS §11."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.health import check_database_health
from mtes.shared.types import EvolutionStatus

HealthStatus = Literal["healthy", "degraded", "unhealthy"]


class EvolutionSnapshotProvider(Protocol):
    """Provides evolution runtime fields for health responses."""

    async def get_evolution_snapshot(self) -> dict[str, object]:
        ...


@dataclass(frozen=True, slots=True)
class StaticEvolutionSnapshotProvider:
    """Default snapshot until evolution module is implemented."""

    evolution_status: EvolutionStatus = EvolutionStatus.CREATED
    queue_depth: int = 0
    active_workers: int = 0
    last_generation_at: str | None = None
    last_publication_at: str | None = None

    async def get_evolution_snapshot(self) -> dict[str, object]:
        return {
            "evolution_status": self.evolution_status.value,
            "queue_depth": self.queue_depth,
            "active_workers": self.active_workers,
            "last_generation_at": self.last_generation_at,
            "last_publication_at": self.last_publication_at,
        }


@dataclass(frozen=True, slots=True)
class HealthService:
    """Build health check payloads."""

    mongo_client: MongoPersistenceClient
    evolution_provider: EvolutionSnapshotProvider

    async def build_health_response(self) -> dict[str, object]:
        database_result = await check_database_health(self.mongo_client)
        evolution_snapshot = await self.evolution_provider.get_evolution_snapshot()

        if database_result.status == "unhealthy":
            overall: HealthStatus = "unhealthy"
        elif evolution_snapshot.get("evolution_status") == EvolutionStatus.FAILED.value:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "evolution_status": evolution_snapshot.get("evolution_status"),
            "queue_depth": evolution_snapshot.get("queue_depth"),
            "active_workers": evolution_snapshot.get("active_workers"),
            "last_generation_at": evolution_snapshot.get("last_generation_at"),
            "last_publication_at": evolution_snapshot.get("last_publication_at"),
            "checked_at": datetime.now().isoformat(),
            "database": database_result.status,
        }
