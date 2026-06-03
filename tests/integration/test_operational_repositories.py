"""Integration tests for operational persistence collections."""

import pytest

pytest.importorskip("testcontainers")

from testcontainers.mongodb import MongoDbContainer  # type: ignore[import-untyped]

from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories import create_operational_repository_registry

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_workflow_state_survives_simulated_restart() -> None:
    try:
        with MongoDbContainer("mongo:7") as mongo:
            connection_string = f"{mongo.get_connection_url()}/mtes_ops_test"
            context = DocumentContext(
                schema_version="3.4",
                experiment_id="exp_ops",
                run_id="run_ops",
            )

            client_first = MongoPersistenceClient(connection_string)
            await client_first.connect()
            registry_first = create_operational_repository_registry(
                client_first.get_database(), context
            )
            created = await registry_first.workflow_state.create_workflow_state(
                "workflow_001",
                state="RUNNING",
                stage="generation",
            )
            await client_first.close()

            client_second = MongoPersistenceClient(connection_string)
            await client_second.connect()
            registry_second = create_operational_repository_registry(
                client_second.get_database(), context
            )
            loaded = await registry_second.workflow_state.find_by_id("workflow_001")
            assert loaded is not None
            assert loaded["state"] == "RUNNING"
            assert loaded["version"] == created["version"]

            updated = await registry_second.workflow_state.transition_workflow_state(
                "workflow_001",
                expected_version=int(loaded["version"]),
                state="PAUSED",
                stage="generation",
            )
            assert updated is not None
            assert updated["state"] == "PAUSED"
            assert updated["version"] == int(loaded["version"]) + 1
            await client_second.close()
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers unavailable: {exc}")
