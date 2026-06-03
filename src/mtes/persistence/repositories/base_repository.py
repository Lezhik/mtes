"""Base MongoDB repository with append-only enforcement."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from mtes.persistence.document_context import DocumentContext


class AppendOnlyViolationError(Exception):
    """Raised when a mutation is attempted on an append-only collection."""


class CollectionRepository:
    """CRUD helper for a single MongoDB collection."""

    def __init__(
        self,
        collection: AsyncIOMotorCollection[Any],
        context: DocumentContext,
        *,
        append_only: bool = False,
    ) -> None:
        self._collection = collection
        self._context = context
        self._append_only = append_only

    @property
    def name(self) -> str:
        return self._collection.name

    @property
    def is_append_only(self) -> bool:
        return self._append_only

    def _guard_mutation(self, operation: str) -> None:
        if self._append_only:
            raise AppendOnlyViolationError(
                f"{operation} is forbidden on append-only collection {self.name}"
            )

    async def insert_one(self, document: dict[str, Any]) -> str:
        """Insert a document with common metadata fields."""
        stamped = self._context.stamp(document)
        result = await self._collection.insert_one(stamped)
        inserted_id = result.inserted_id
        return str(inserted_id)

    async def find_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Load a document by string _id or custom id field."""
        by_custom_id = await self._collection.find_one({"_id": document_id})
        if by_custom_id is not None:
            return by_custom_id
        return await self._collection.find_one({"_id": document_id})

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        return await self._collection.find_one(query)

    async def replace_one(self, document_id: str, document: dict[str, Any]) -> None:
        """Replace a document (disallowed for append-only collections)."""
        self._guard_mutation("replace_one")
        stamped = self._context.stamp(document)
        await self._collection.replace_one({"_id": document_id}, stamped, upsert=True)

    async def delete_one(self, query: dict[str, Any]) -> None:
        """Delete a document (disallowed for append-only collections)."""
        self._guard_mutation("delete_one")
        await self._collection.delete_one(query)

    async def insert_correction(self, document: dict[str, Any]) -> str:
        """Insert a new document as correction (append-only collections)."""
        if not self._append_only:
            raise AppendOnlyViolationError(
                f"insert_correction applies only to append-only collections, not {self.name}"
            )
        return await self.insert_one(document)


def collection_repository(
    database: AsyncIOMotorDatabase[Any],
    collection_name: str,
    context: DocumentContext,
    *,
    append_only: bool = False,
) -> CollectionRepository:
    return CollectionRepository(database[collection_name], context, append_only=append_only)
