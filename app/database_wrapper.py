"""
Database wrapper to provide MongoDB-like interface for all database adapters.
This wrapper simplifies the migration from Motor to our abstraction layer.
"""

from typing import Dict, Any, Optional, List
from database_interface import DatabaseInterface


class DatabaseWrapper:
    """
    Wrapper that provides a MongoDB-like interface (db.collection.operation)
    for any database adapter implementing DatabaseInterface.
    """

    def __init__(self, db_adapter: DatabaseInterface):
        self.adapter = db_adapter

    def __getattr__(self, collection_name: str):
        """Return a collection wrapper for the given collection name"""
        return CollectionWrapper(self.adapter, collection_name)


class CollectionWrapper:
    """
    Wrapper for collection operations, providing MongoDB-like syntax.
    """

    def __init__(self, adapter: DatabaseInterface, collection_name: str):
        self.adapter = adapter
        self.collection_name = collection_name

    async def find_one(
        self, filter: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        if filter is None:
            filter = {}

        # Handle MongoDB sort parameter
        sort = kwargs.get("sort")

        if sort:
            # MongoDB sort with limit 1
            results = await self.adapter.find(
                self.collection_name, filter, sort=sort, limit=1
            )
            return results[0] if results else None

        return await self.adapter.find_one(self.collection_name, filter)

    def find(self, filter: Optional[Dict[str, Any]] = None, **kwargs):
        """Find multiple documents - returns a cursor-like object"""
        if filter is None:
            filter = {}
        return CursorWrapper(self.adapter, self.collection_name, filter, kwargs)

    async def insert_one(self, document: Dict[str, Any]) -> None:
        """Insert a single document"""
        await self.adapter.insert_one(self.collection_name, document)

    async def update_one(
        self, filter: Dict[str, Any], update: Dict[str, Any], **kwargs
    ) -> None:
        """Update a single document"""
        await self.adapter.update_one(self.collection_name, filter, update)

    async def delete_one(self, filter: Dict[str, Any]) -> None:
        """Delete a single document"""
        await self.adapter.delete_one(self.collection_name, filter)

    async def delete_many(self, filter: Dict[str, Any]):
        """Delete multiple documents"""
        deleted_count = await self.adapter.delete_many(self.collection_name, filter)

        # Return an object with deleted_count attribute for compatibility
        class DeleteResult:
            def __init__(self, count):
                self.deleted_count = count

        return DeleteResult(deleted_count)

    async def count_documents(self, filter: Dict[str, Any]) -> int:
        """Count documents"""
        return await self.adapter.count_documents(self.collection_name, filter)

    def aggregate(self, pipeline: List[Dict[str, Any]]):
        """Perform aggregation"""
        return AggregateCursor(self.adapter, self.collection_name, pipeline)


class CursorWrapper:
    """
    Wrapper to provide MongoDB-like cursor interface for async iteration.
    """

    def __init__(
        self,
        adapter: DatabaseInterface,
        collection: str,
        filter: Dict[str, Any],
        options: Dict[str, Any],
    ):
        self.adapter = adapter
        self.collection = collection
        self.filter = filter
        self.options = options
        self._sort = None
        self._limit = None
        self._results = None
        self._index = 0

    def sort(self, *args, **kwargs):
        """Set sort order"""
        # Handle both sort([("field", 1)]) and sort("field", 1) formats
        if args and isinstance(args[0], list):
            self._sort = args[0]
        elif args and isinstance(args[0], str):
            direction = args[1] if len(args) > 1 else 1
            self._sort = [(args[0], direction)]
        return self

    def limit(self, limit: int):
        """Set limit"""
        self._limit = limit
        return self

    async def to_list(self, length: Optional[int] = None):
        """Convert cursor to list"""
        limit = length if length is not None else self._limit
        results = await self.adapter.find(
            self.collection, self.filter, sort=self._sort, limit=limit
        )
        return results

    def __aiter__(self):
        """Support async iteration"""
        return self

    async def __anext__(self):
        """Get next item in async iteration"""
        if self._results is None:
            self._results = await self.to_list()
            self._index = 0

        if self._index >= len(self._results):
            raise StopAsyncIteration

        result = self._results[self._index]
        self._index += 1
        return result


class AggregateCursor:
    """Wrapper for aggregation pipeline cursor"""

    def __init__(
        self,
        adapter: DatabaseInterface,
        collection: str,
        pipeline: List[Dict[str, Any]],
    ):
        self.adapter = adapter
        self.collection = collection
        self.pipeline = pipeline
        self._results = None
        self._index = 0

    async def to_list(self, length: Optional[int] = None):
        """Convert cursor to list"""
        results = await self.adapter.aggregate(self.collection, self.pipeline)
        if length:
            return results[:length]
        return results

    def __aiter__(self):
        """Support async iteration"""
        return self

    async def __anext__(self):
        """Get next item in async iteration"""
        if self._results is None:
            self._results = await self.to_list()
            self._index = 0

        if self._index >= len(self._results):
            raise StopAsyncIteration

        result = self._results[self._index]
        self._index += 1
        return result
