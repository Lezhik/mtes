"""Periodic housekeeping per Architecture §7.13 and Data Model §10."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

PHENOTYPE_CANDIDATE_TTL_DAYS = 90
CONSTRAINT_RECORD_TTL_DAYS = 90


class TemporaryCollectionRepository(Protocol):
    name: str

    async def delete_many(self, query: dict[str, Any]) -> int:
        ...

    async def find_many(
        self,
        query: dict[str, Any],
        *,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict[str, Any]]:
        ...


class IndexHealthProbe(Protocol):
    async def list_index_names(self, collection_name: str) -> list[str]:
        ...


@dataclass(frozen=True, slots=True)
class MaintenanceResult:
    phenotype_candidates_deleted: int
    constraint_records_deleted: int
    index_health: dict[str, list[str]]
    engagement_records_synced: int


@dataclass
class MaintenanceWorker:
    """Run TTL purge, index health checks, and engagement sync hooks."""

    phenotype_candidates: TemporaryCollectionRepository
    constraint_records: TemporaryCollectionRepository
    index_probe: IndexHealthProbe | None = None
    engagement_sync_enabled: bool = False

    async def run_scheduled_tasks(self) -> MaintenanceResult:
        phenotype_deleted = await self.purge_phenotype_candidates_ttl()
        constraint_deleted = await self.purge_constraint_records_ttl()
        index_health = await self.verify_index_health()
        engagement_synced = await self.synchronize_engagement_metrics()
        return MaintenanceResult(
            phenotype_candidates_deleted=phenotype_deleted,
            constraint_records_deleted=constraint_deleted,
            index_health=index_health,
            engagement_records_synced=engagement_synced,
        )

    async def purge_phenotype_candidates_ttl(
        self,
        *,
        max_age_days: int = PHENOTYPE_CANDIDATE_TTL_DAYS,
    ) -> int:
        cutoff = (datetime.now(UTC) - timedelta(days=max_age_days)).isoformat()
        return await self.phenotype_candidates.delete_many({"created_at": {"$lt": cutoff}})

    async def purge_constraint_records_ttl(
        self,
        *,
        max_age_days: int = CONSTRAINT_RECORD_TTL_DAYS,
    ) -> int:
        cutoff = (datetime.now(UTC) - timedelta(days=max_age_days)).isoformat()
        return await self.constraint_records.delete_many({"created_at": {"$lt": cutoff}})

    async def verify_index_health(self) -> dict[str, list[str]]:
        if self.index_probe is None:
            return {}
        collections = ("phenotype_candidates", "constraint_records", "genomes")
        health: dict[str, list[str]] = {}
        for collection_name in collections:
            health[collection_name] = await self.index_probe.list_index_names(collection_name)
        return health

    async def synchronize_engagement_metrics(self) -> int:
        if not self.engagement_sync_enabled:
            return 0
        raise NotImplementedError("Engagement synchronization is not implemented")
