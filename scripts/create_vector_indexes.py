"""Create MongoDB Atlas Vector Search indexes from embedding_models.dimension.

Hardcoded embedding dimensions are prohibited (Data Model Specification §2.3).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from mtes.persistence.client import MongoPersistenceClient
from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories import create_repository_registry
from mtes.persistence.vector_indexes import create_vector_indexes, resolve_embedding_dimension
from mtes.shared.config import load_config
from mtes.shared.exceptions import ConfigurationError, MongoDbUnavailableError


async def run_create_vector_indexes(
    *,
    config_path: Path,
    model_id: str | None,
    dry_run: bool,
) -> int:
    config = load_config(config_path)
    context = DocumentContext(
        schema_version="3.4",
        experiment_id="system",
        run_id="vector_index_bootstrap",
    )

    client = MongoPersistenceClient(config.database.connection_string)
    await client.connect()
    try:
        database = client.get_database()
        registry = create_repository_registry(database, context)
        resolved_model_id, dimension = await resolve_embedding_dimension(
            registry.embedding_models,
            model_id,
        )

        if dry_run:
            print(
                f"Dry run: would create vector indexes with model={resolved_model_id} "
                f"dimension={dimension}"
            )
            return 0

        created = await create_vector_indexes(database, dimension=dimension)
        await registry.audit_log.insert_one(
            {
                "_id": f"audit_vector_index_{resolved_model_id}",
                "event_type": "VECTOR_INDEX_REBUILD",
                "details": {
                    "model_id": resolved_model_id,
                    "dimension": dimension,
                    "indexes": created,
                },
            }
        )
        print(f"Created vector indexes: {', '.join(created)}")
        return 0
    finally:
        await client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create MTES vector search indexes")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.example.yaml"),
        help="Path to MTES YAML configuration",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="embedding_models document id (default: first model in collection)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve dimension only; do not create indexes",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(
            run_create_vector_indexes(
                config_path=args.config,
                model_id=args.model_id,
                dry_run=args.dry_run,
            )
        )
    except (ConfigurationError, MongoDbUnavailableError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
