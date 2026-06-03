"""Integration tests for core collection repositories."""

import pytest

pytest.importorskip("testcontainers")

from testcontainers.mongodb import MongoDbContainer  # type: ignore[import-untyped]

from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories import AppendOnlyViolationError, create_repository_registry

pytestmark = pytest.mark.integration

SAMPLE_GENOME: dict[str, object] = {
    "_id": "genome_test_001",
    "generation": 1,
    "semantic_genes": [
        {
            "gene_id": 1,
            "coordinate": [3, 5, 4, 2, 3],
            "anchor": "winter",
        }
    ],
    "numeric_genes": {"anchor_rigidity": 0.81},
    "parent_ids": [],
    "seed": 123456789,
    "dictionary_version": "4.2",
    "mapping_version": "4.9",
}

SAMPLE_CANDIDATE: dict[str, object] = {
    "_id": "candidate_test_001",
    "genome_id": "genome_test_001",
    "text": "winter silence drifts slowly",
    "constraint_score": 0.82,
    "quality_score": 0.75,
    "diversity_score": 0.61,
    "overall_score": 0.74,
    "selected": True,
    "routing_family": "P4-C",
    "prompt_version": "3.1",
    "embedding": [],
    "embedding_model_id": "e5-large",
}


@pytest.fixture
async def repository_registry():
    try:
        with MongoDbContainer("mongo:7") as mongo:
            connection_string = mongo.get_connection_url()
            client = MongoPersistenceClient(f"{connection_string}/mtes_test")
            await client.connect()
            database = client.get_database()
            context = DocumentContext(
                schema_version="3.4",
                experiment_id="exp_test",
                run_id="run_test",
            )
            registry = create_repository_registry(database, context)
            yield registry
            await client.close()
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers unavailable: {exc}")


@pytest.mark.asyncio
async def test_genome_round_trip(repository_registry) -> None:
    await repository_registry.genomes.insert_one(SAMPLE_GENOME)
    loaded = await repository_registry.genomes.find_by_id("genome_test_001")
    assert loaded is not None
    assert loaded["generation"] == 1
    assert loaded["schema_version"] == "3.4"
    assert loaded["experiment_id"] == "exp_test"
    assert "created_at" in loaded


@pytest.mark.asyncio
async def test_candidate_archive_round_trip(repository_registry) -> None:
    await repository_registry.candidate_archive.insert_one(SAMPLE_CANDIDATE)
    loaded = await repository_registry.candidate_archive.find_by_id("candidate_test_001")
    assert loaded is not None
    assert loaded["text"] == "winter silence drifts slowly"


@pytest.mark.asyncio
async def test_append_only_genomes_rejects_delete(repository_registry) -> None:
    await repository_registry.genomes.insert_one(
        {**SAMPLE_GENOME, "_id": "genome_append_only"}
    )
    with pytest.raises(AppendOnlyViolationError):
        await repository_registry.genomes.delete_one({"_id": "genome_append_only"})


@pytest.mark.asyncio
async def test_mutable_system_events_allows_delete(repository_registry) -> None:
    await repository_registry.system_events.insert_one(
        {
            "_id": "event_test_001",
            "event_type": "SERVICE_START",
            "severity": "INFO",
            "message": "test",
        }
    )
    await repository_registry.system_events.delete_one({"_id": "event_test_001"})
    assert await repository_registry.system_events.find_by_id("event_test_001") is None
