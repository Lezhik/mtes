#!/usr/bin/env python3
"""Run maintenance worker tasks (TTL purge, index health)."""

from __future__ import annotations

import asyncio
import os

from mtes.core.maintenance_worker import MaintenanceWorker
from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.document_context import DocumentContext
from mtes.persistence.mongo_index_probe import MongoIndexHealthProbe
from mtes.persistence.repositories import create_repository_registry


async def main() -> None:
    connection_string = os.environ.get("MTES_MONGODB_URI", "mongodb://localhost:27017/mtes")
    client = MongoPersistenceClient(connection_string)
    await client.connect()
    database = client.get_database()
    context = DocumentContext(
        schema_version=os.environ.get("MTES_SCHEMA_VERSION", "3.4"),
        experiment_id=os.environ.get("MTES_EXPERIMENT_ID", "default"),
        run_id=os.environ.get("MTES_RUN_ID", "maintenance"),
    )
    registry = create_repository_registry(database, context)
    worker = MaintenanceWorker(
        phenotype_candidates=registry.phenotype_candidates,
        constraint_records=registry.constraint_records,
        index_probe=MongoIndexHealthProbe(database),
    )
    result = await worker.run_scheduled_tasks()
    print(
        "maintenance_complete",
        f"phenotype_deleted={result.phenotype_candidates_deleted}",
        f"constraint_deleted={result.constraint_records_deleted}",
        f"index_collections={list(result.index_health.keys())}",
    )
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
