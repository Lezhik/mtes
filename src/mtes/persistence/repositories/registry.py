"""Repository registry for all Data Model collections."""

from dataclasses import dataclass
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories.base_repository import CollectionRepository, collection_repository

IMMUTABLE_COLLECTION_NAMES: frozenset[str] = frozenset(
    {
        "genomes",
        "mutation_history",
        "candidate_archive",
        "validation_records",
        "fitness_records",
        "tweet_archive",
        "audit_log",
    }
)


@dataclass(frozen=True, slots=True)
class RepositoryRegistry:
    """Named repositories for the MTES data model."""

    dictionary_terms: CollectionRepository
    dictionary_buckets: CollectionRepository
    pair_memory_state: CollectionRepository
    constraint_records: CollectionRepository
    genomes: CollectionRepository
    mutation_history: CollectionRepository
    phenotype_candidates: CollectionRepository
    candidate_archive: CollectionRepository
    validation_records: CollectionRepository
    fitness_records: CollectionRepository
    tweet_archive: CollectionRepository
    embedding_models: CollectionRepository
    audit_log: CollectionRepository
    system_events: CollectionRepository


def create_repository_registry(
    database: AsyncIOMotorDatabase[Any],
    context: DocumentContext,
) -> RepositoryRegistry:
    """Create repositories for all specification-defined collections."""

    def repo(name: str) -> CollectionRepository:
        return collection_repository(
            database,
            name,
            context,
            append_only=name in IMMUTABLE_COLLECTION_NAMES,
        )

    return RepositoryRegistry(
        dictionary_terms=repo("dictionary_terms"),
        dictionary_buckets=repo("dictionary_buckets"),
        pair_memory_state=repo("pair_memory_state"),
        constraint_records=repo("constraint_records"),
        genomes=repo("genomes"),
        mutation_history=repo("mutation_history"),
        phenotype_candidates=repo("phenotype_candidates"),
        candidate_archive=repo("candidate_archive"),
        validation_records=repo("validation_records"),
        fitness_records=repo("fitness_records"),
        tweet_archive=repo("tweet_archive"),
        embedding_models=repo("embedding_models"),
        audit_log=repo("audit_log"),
        system_events=repo("system_events"),
    )
