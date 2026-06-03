"""Workflow state repository with atomic transitions."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from mtes.persistence.document_context import DocumentContext
from mtes.persistence.repositories.base_repository import CollectionRepository


class WorkflowStateRepository(CollectionRepository):
    """Persist workflow state with optimistic concurrency control."""

    async def create_workflow_state(
        self,
        workflow_id: str,
        *,
        state: str,
        stage: str,
        retry_count: int = 0,
    ) -> dict[str, Any]:
        document: dict[str, Any] = {
            "_id": workflow_id,
            "workflow_id": workflow_id,
            "state": state,
            "stage": stage,
            "retry_count": retry_count,
            "version": 1,
        }
        await self.insert_one(document)
        loaded = await self.find_by_id(workflow_id)
        if loaded is None:
            raise RuntimeError(f"Workflow state not found after insert: {workflow_id}")
        return loaded

    async def transition_workflow_state(
        self,
        workflow_id: str,
        *,
        expected_version: int,
        state: str,
        stage: str,
        retry_count: int | None = None,
    ) -> dict[str, Any] | None:
        """Atomically update workflow state when version matches."""
        update_fields: dict[str, Any] = {
            "state": state,
            "stage": stage,
        }
        if retry_count is not None:
            update_fields["retry_count"] = retry_count

        collection: AsyncIOMotorCollection[Any] = self._collection
        return await collection.find_one_and_update(
            {"workflow_id": workflow_id, "version": expected_version},
            {"$set": update_fields, "$inc": {"version": 1}},
            return_document=ReturnDocument.AFTER,
        )

    async def find_active_workflows(self) -> list[dict[str, Any]]:
        cursor = self._collection.find(
            {"state": {"$in": ["RUNNING", "PAUSED", "PENDING"]}},
        )
        return await cursor.to_list(length=1000)

    async def find_by_workflow_id(self, workflow_id: str) -> dict[str, Any] | None:
        document = await self._collection.find_one({"workflow_id": workflow_id})
        return document
