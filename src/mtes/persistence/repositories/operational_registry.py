"""Operational collections defined in detailed_design §2.3.3."""

from dataclasses import dataclass
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories.base_repository import CollectionRepository, collection_repository
from mtes.persistence.repositories.workflow_state_repository import WorkflowStateRepository


@dataclass(frozen=True, slots=True)
class OperationalRepositoryRegistry:
    bootstrap_reports: CollectionRepository
    workflow_state: WorkflowStateRepository
    evolution_state: CollectionRepository
    population_members: CollectionRepository
    publication_queue: CollectionRepository
    daemon_state: CollectionRepository


def create_operational_repository_registry(
    database: AsyncIOMotorDatabase[Any],
    context: DocumentContext,
) -> OperationalRepositoryRegistry:
    workflow_collection = database["workflow_state"]
    return OperationalRepositoryRegistry(
        bootstrap_reports=collection_repository(
            database, "bootstrap_reports", context, append_only=True
        ),
        workflow_state=WorkflowStateRepository(workflow_collection, context, append_only=False),
        evolution_state=collection_repository(database, "evolution_state", context),
        population_members=collection_repository(database, "population_members", context),
        publication_queue=collection_repository(database, "publication_queue", context),
        daemon_state=collection_repository(database, "daemon_state", context),
    )
