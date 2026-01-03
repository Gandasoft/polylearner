"""
MongoDB adapter for the database abstraction layer.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)


class MongoDBAdapter(DatabaseInterface):
    """MongoDB implementation of the database interface"""

    def __init__(self, uri: str, database_name: str):
        """
        Initialize MongoDB adapter

        Args:
            uri: MongoDB connection URI
            database_name: Name of the database to use
        """
        self.client = AsyncIOMotorClient(uri)
        self.db: AsyncIOMotorDatabase = self.client[database_name]
        logger.info(f"MongoDB adapter initialized with database: {database_name}")

    async def find_one(
        self, collection: str, filter: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        result = await self.db[collection].find_one(filter)
        return result

    async def find(
        self,
        collection: str,
        filter: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        cursor = self.db[collection].find(filter)

        if sort:
            cursor = cursor.sort(sort)

        if limit:
            cursor = cursor.limit(limit)

        results = await cursor.to_list(length=limit if limit else None)
        return results

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> None:
        """Insert a single document"""
        await self.db[collection].insert_one(document)

    async def update_one(
        self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]
    ) -> None:
        """Update a single document"""
        await self.db[collection].update_one(filter, update)

    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> None:
        """Delete a single document"""
        await self.db[collection].delete_one(filter)

    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents"""
        result = await self.db[collection].delete_many(filter)
        return result.deleted_count

    async def count_documents(self, collection: str, filter: Dict[str, Any]) -> int:
        """Count documents matching filter"""
        count = await self.db[collection].count_documents(filter)
        return count

    async def aggregate(
        self, collection: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform aggregation pipeline"""
        cursor = self.db[collection].aggregate(pipeline)
        results = await cursor.to_list(length=None)
        return results

    async def close(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_native_db(self) -> AsyncIOMotorDatabase:
        """
        Get the native MongoDB database object for services that need direct access.
        This is a temporary compatibility method.
        """
        return self.db
