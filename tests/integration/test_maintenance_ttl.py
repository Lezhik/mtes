"""Integration test: TTL purge on phenotype_candidates."""

from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("testcontainers")

from testcontainers.mongodb import MongoDbContainer  # type: ignore[import-untyped]

from mtes.core.maintenance_worker import MaintenanceWorker
from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories import create_repository_registry

pytestmark = pytest.mark.integration


@pytest.fixture
async def maintenance_worker():
    try:
        with MongoDbContainer("mongo:7") as mongo:
            connection_string = mongo.get_connection_url()
            client = MongoPersistenceClient(f"{connection_string}/mtes_maintenance_test")
            await client.connect()
            database = client.get_database()
            context = DocumentContext(
                schema_version="3.4",
                experiment_id="exp_maint",
                run_id="run_maint",
            )
            registry = create_repository_registry(database, context)
            worker = MaintenanceWorker(
                phenotype_candidates=registry.phenotype_candidates,
                constraint_records=registry.constraint_records,
            )
            yield worker, registry
            await client.close()
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers unavailable: {exc}")


@pytest.mark.asyncio
async def test_ttl_job_removes_aged_phenotype_candidates(maintenance_worker) -> None:
    worker, registry = maintenance_worker
    old_timestamp = (datetime.now(UTC) - timedelta(days=120)).isoformat()
    recent_timestamp = datetime.now(UTC).isoformat()
    await registry.phenotype_candidates.insert_one(
        {
            "_id": "candidate_old",
            "genome_id": "g1",
            "text": "old",
            "created_at": old_timestamp,
        }
    )
    await registry.phenotype_candidates.insert_one(
        {
            "_id": "candidate_new",
            "genome_id": "g2",
            "text": "new",
            "created_at": recent_timestamp,
        }
    )
    deleted = await worker.purge_phenotype_candidates_ttl()
    assert deleted == 1
    remaining = await registry.phenotype_candidates.find_by_id("candidate_new")
    assert remaining is not None
    removed = await registry.phenotype_candidates.find_by_id("candidate_old")
    assert removed is None
