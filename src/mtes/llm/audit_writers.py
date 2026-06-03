"""Persistence-backed audit and system event writers for LLM operations."""

from typing import Any

from mtes.persistence.repositories.base_repository import CollectionRepository


class MongoAuditLogWriter:
    def __init__(self, audit_log_repository: CollectionRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def write_llm_audit_event(
        self,
        *,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        await self._audit_log_repository.insert_one(
            {
                "_id": f"audit_{event_type.lower()}_{details.get('request_id', 'unknown')}",
                "event_type": event_type,
                "details": details,
            }
        )


class MongoSystemEventWriter:
    def __init__(self, system_events_repository: CollectionRepository) -> None:
        self._system_events_repository = system_events_repository

    async def write_provider_failover(
        self,
        *,
        message: str,
        details: dict[str, Any],
    ) -> None:
        await self._system_events_repository.insert_one(
            {
                "_id": f"event_failover_{details.get('from_provider')}_{details.get('to_provider')}",
                "event_type": "PROVIDER_FAILOVER",
                "severity": "WARNING",
                "message": message,
                "details": details,
            }
        )
