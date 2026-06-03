"""Standard MongoDB B-tree index creation (no Atlas Search / Vector Search)."""

from typing import Any

IndexSpec = tuple[tuple[str, int], dict[str, Any]]


STANDARD_COLLECTION_INDEXES: dict[str, list[IndexSpec]] = {
    "dictionary_terms": [
        (("token", 1), {"unique": True, "name": "dictionary_terms_token_unique"}),
        (("coordinate", 1), {"name": "dictionary_terms_coordinate"}),
        (("bucket_id", 1), {"name": "dictionary_terms_bucket_id"}),
        (("dictionary_version", 1), {"name": "dictionary_terms_dictionary_version"}),
    ],
    "dictionary_buckets": [
        (("coordinate", 1), {"unique": True, "name": "dictionary_buckets_coordinate_unique"}),
    ],
    "genomes": [
        (("generation", 1), {"name": "genomes_generation"}),
    ],
    "phenotype_candidates": [
        (("genome_id", 1), {"name": "phenotype_candidates_genome_id"}),
        (("created_at", 1), {"name": "phenotype_candidates_created_at"}),
    ],
    "candidate_archive": [
        (("genome_id", 1), {"name": "candidate_archive_genome_id"}),
        (("selected", 1), {"name": "candidate_archive_selected"}),
    ],
    "tweet_archive": [
        (("genome_id", 1), {"name": "tweet_archive_genome_id"}),
    ],
    "audit_log": [
        (("event_type", 1), {"name": "audit_log_event_type"}),
        (("created_at", 1), {"name": "audit_log_created_at"}),
    ],
    "system_events": [
        (("event_type", 1), {"name": "system_events_event_type"}),
        (("severity", 1), {"name": "system_events_severity"}),
        (("created_at", 1), {"name": "system_events_created_at"}),
    ],
}


async def ensure_mongodb_indexes(database: Any) -> list[str]:
    """Create or verify standard MongoDB indexes for MTES collections."""
    ensured: list[str] = []
    for collection_name, index_specs in STANDARD_COLLECTION_INDEXES.items():
        collection = database[collection_name]
        for keys, options in index_specs:
            index_name = str(options["name"])
            await collection.create_index([keys], **options)
            ensured.append(f"{collection_name}.{index_name}")
    return ensured
