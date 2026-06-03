"""MongoDB index health probe for maintenance worker."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class MongoIndexHealthProbe:
    def __init__(self, database: AsyncIOMotorDatabase[Any]) -> None:
        self._database = database

    async def list_index_names(self, collection_name: str) -> list[str]:
        collection = self._database[collection_name]
        indexes = await collection.index_information()
        return sorted(indexes.keys())
