"""Maintenance worker unit tests."""

from datetime import UTC, datetime, timedelta

import pytest

from mtes.core.maintenance_worker import MaintenanceWorker


class InMemoryTemporaryRepository:
    def __init__(self, name: str) -> None:
        self.name = name
        self.documents: list[dict[str, object]] = []

    async def delete_many(self, query: dict[str, object]) -> int:
        cutoff = query.get("created_at", {}).get("$lt")
        remaining: list[dict[str, object]] = []
        deleted = 0
        for document in self.documents:
            if cutoff is not None and str(document.get("created_at", "")) < str(cutoff):
                deleted += 1
            else:
                remaining.append(document)
        self.documents = remaining
        return deleted

    async def find_many(
        self,
        query: dict[str, object],
        *,
        limit: int = 100,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict[str, object]]:
        del query, limit, sort
        return list(self.documents)


@pytest.mark.asyncio
async def test_purge_phenotype_candidates_removes_expired_documents() -> None:
    old_timestamp = (datetime.now(UTC) - timedelta(days=120)).isoformat()
    recent_timestamp = datetime.now(UTC).isoformat()
    phenotype_repo = InMemoryTemporaryRepository("phenotype_candidates")
    phenotype_repo.documents = [
        {"_id": "old", "created_at": old_timestamp},
        {"_id": "new", "created_at": recent_timestamp},
    ]
    constraint_repo = InMemoryTemporaryRepository("constraint_records")
    worker = MaintenanceWorker(
        phenotype_candidates=phenotype_repo,
        constraint_records=constraint_repo,
    )
    deleted = await worker.purge_phenotype_candidates_ttl()
    assert deleted == 1
    assert len(phenotype_repo.documents) == 1
    assert phenotype_repo.documents[0]["_id"] == "new"
