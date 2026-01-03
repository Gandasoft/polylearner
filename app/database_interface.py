"""
Database abstraction layer for PolyLearner.

Provides a unified interface for MongoDB and Google Firestore,
allowing seamless switching between database providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class DatabaseInterface(ABC):
    """Abstract base class for database operations"""

    @abstractmethod
    async def find_one(
        self, collection: str, filter: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        pass

    @abstractmethod
    async def find(
        self,
        collection: str,
        filter: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        pass

    @abstractmethod
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> None:
        """Insert a single document"""
        pass

    @abstractmethod
    async def update_one(
        self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]
    ) -> None:
        """Update a single document"""
        pass

    @abstractmethod
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> None:
        """Delete a single document"""
        pass

    @abstractmethod
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents, returns count of deleted documents"""
        pass

    @abstractmethod
    async def count_documents(self, collection: str, filter: Dict[str, Any]) -> int:
        """Count documents matching filter"""
        pass

    @abstractmethod
    async def aggregate(
        self, collection: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform aggregation pipeline"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass
