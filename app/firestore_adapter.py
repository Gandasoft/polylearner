"""
Google Firestore adapter for the database abstraction layer.
"""

from typing import List, Dict, Any, Optional
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from database_interface import DatabaseInterface
import logging
import os

logger = logging.getLogger(__name__)


class FirestoreAdapter(DatabaseInterface):
    """Google Firestore implementation of the database interface"""

    def __init__(
        self, project_id: Optional[str] = None, credentials_path: Optional[str] = None
    ):
        """
        Initialize Firestore adapter

        Args:
            project_id: Google Cloud project ID (optional, can be inferred from credentials)
            credentials_path: Path to service account JSON file (optional, uses GOOGLE_APPLICATION_CREDENTIALS env var if not provided)
        """
        # Set credentials path if provided
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # Initialize Firestore client
        if project_id:
            self.client = firestore.AsyncClient(project=project_id)
        else:
            self.client = firestore.AsyncClient()

        logger.info(
            f"Firestore adapter initialized for project: {project_id or 'default'}"
        )

    def _convert_filter_to_firestore(self, filter: Dict[str, Any]) -> List[FieldFilter]:
        """Convert MongoDB-style filter to Firestore field filters"""
        filters = []

        for key, value in filter.items():
            if isinstance(value, dict):
                # Handle operators like $in, $gt, $gte, $lt, $lte
                for operator, operand in value.items():
                    if operator == "$in":
                        # Firestore doesn't have direct $in, need to use 'in' operator
                        filters.append(FieldFilter(key, "in", operand))
                    elif operator == "$gt":
                        filters.append(FieldFilter(key, ">", operand))
                    elif operator == "$gte":
                        filters.append(FieldFilter(key, ">=", operand))
                    elif operator == "$lt":
                        filters.append(FieldFilter(key, "<", operand))
                    elif operator == "$lte":
                        filters.append(FieldFilter(key, "<=", operand))
                    elif operator == "$ne":
                        filters.append(FieldFilter(key, "!=", operand))
                    elif operator == "$set":
                        # This is for updates, not filters
                        pass
                    elif operator == "$inc":
                        # This is for updates, not filters
                        pass
                    elif operator == "$addToSet":
                        # This is for updates, not filters
                        pass
                    else:
                        logger.warning(f"Unsupported operator: {operator}")
            else:
                # Simple equality filter
                filters.append(FieldFilter(key, "==", value))

        return filters

    def _convert_sort_to_firestore(self, sort: List[tuple]) -> List[tuple]:
        """Convert MongoDB-style sort to Firestore order_by format"""
        firestore_sort = []
        for field, direction in sort:
            # MongoDB uses 1 for ascending, -1 for descending
            # Firestore uses ASCENDING and DESCENDING
            if direction == 1 or direction == "asc":
                firestore_sort.append((field, firestore.Query.ASCENDING))
            else:
                firestore_sort.append((field, firestore.Query.DESCENDING))
        return firestore_sort

    async def find_one(
        self, collection: str, filter: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        col_ref = self.client.collection(collection)
        query = col_ref

        # Apply filters
        filters = self._convert_filter_to_firestore(filter)
        for f in filters:
            query = query.where(filter=f)

        # Limit to 1
        query = query.limit(1)

        docs = [doc async for doc in query.stream()]

        if docs:
            doc = docs[0]
            data = doc.to_dict()
            # Firestore uses document ID, we might need to include it
            data["_firestore_id"] = doc.id
            return data

        return None

    async def find(
        self,
        collection: str,
        filter: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        col_ref = self.client.collection(collection)
        query = col_ref

        # Apply filters
        filters = self._convert_filter_to_firestore(filter)
        for f in filters:
            query = query.where(filter=f)

        # Apply sort
        if sort:
            firestore_sort = self._convert_sort_to_firestore(sort)
            for field, direction in firestore_sort:
                query = query.order_by(field, direction=direction)

        # Apply limit
        if limit:
            query = query.limit(limit)

        results = []
        async for doc in query.stream():
            data = doc.to_dict()
            data["_firestore_id"] = doc.id
            results.append(data)

        return results

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> None:
        """Insert a single document"""
        col_ref = self.client.collection(collection)

        # Remove MongoDB-specific _id if present
        doc_copy = document.copy()
        doc_copy.pop("_id", None)

        # Use 'id' field as document ID if present
        if "id" in doc_copy:
            doc_id = str(doc_copy["id"])
            await col_ref.document(doc_id).set(doc_copy)
        else:
            # Let Firestore generate ID
            await col_ref.add(doc_copy)

    async def update_one(
        self, collection: str, filter: Dict[str, Any], update: Dict[str, Any]
    ) -> None:
        """Update a single document"""
        # First find the document
        doc = await self.find_one(collection, filter)

        if not doc:
            logger.warning(
                f"Document not found for update in collection {collection} with filter {filter}"
            )
            return

        # Get the Firestore document ID
        doc_id = doc.get("_firestore_id")
        if not doc_id and "id" in doc:
            doc_id = str(doc["id"])

        if not doc_id:
            logger.error(f"Could not determine document ID for update")
            return

        # Parse the update operations
        update_data = {}

        if "$set" in update:
            update_data.update(update["$set"])

        if "$inc" in update:
            # For increment operations, we need to read current value and increment
            for field, value in update["$inc"].items():
                current_value = doc.get(field, 0)
                update_data[field] = current_value + value

        if "$addToSet" in update:
            # For array operations
            for field, value in update["$addToSet"].items():
                current_array = doc.get(field, [])
                if isinstance(value, dict) and "$each" in value:
                    # Add multiple items
                    for item in value["$each"]:
                        if item not in current_array:
                            current_array.append(item)
                else:
                    # Add single item
                    if value not in current_array:
                        current_array.append(value)
                update_data[field] = current_array

        # Apply the update
        doc_ref = self.client.collection(collection).document(doc_id)
        await doc_ref.update(update_data)

    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> None:
        """Delete a single document"""
        doc = await self.find_one(collection, filter)

        if not doc:
            logger.warning(
                f"Document not found for deletion in collection {collection}"
            )
            return

        doc_id = doc.get("_firestore_id")
        if not doc_id and "id" in doc:
            doc_id = str(doc["id"])

        if doc_id:
            doc_ref = self.client.collection(collection).document(doc_id)
            await doc_ref.delete()

    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents"""
        docs = await self.find(collection, filter)

        deleted_count = 0
        for doc in docs:
            doc_id = doc.get("_firestore_id")
            if not doc_id and "id" in doc:
                doc_id = str(doc["id"])

            if doc_id:
                doc_ref = self.client.collection(collection).document(doc_id)
                await doc_ref.delete()
                deleted_count += 1

        return deleted_count

    async def count_documents(self, collection: str, filter: Dict[str, Any]) -> int:
        """Count documents matching filter"""
        docs = await self.find(collection, filter)
        return len(docs)

    async def aggregate(
        self, collection: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Perform aggregation pipeline
        Note: Firestore has limited aggregation capabilities compared to MongoDB.
        This is a basic implementation that may need enhancement for complex pipelines.
        """
        logger.warning(
            "Firestore has limited aggregation support. This may not work for all MongoDB aggregation pipelines."
        )

        # For now, just return all documents
        # Complex aggregations should be handled in application code
        results = await self.find(collection, {})

        return results

    async def close(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Firestore connection closed")
