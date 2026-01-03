"""
Database factory for creating database adapters based on configuration.
"""

import os
import logging
from typing import Optional
from database_interface import DatabaseInterface
from mongodb_adapter import MongoDBAdapter
from firestore_adapter import FirestoreAdapter

logger = logging.getLogger(__name__)


def create_database(
    db_type: Optional[str] = None,
    mongo_uri: Optional[str] = None,
    mongo_db_name: Optional[str] = None,
    firestore_project_id: Optional[str] = None,
    firestore_credentials_path: Optional[str] = None,
) -> DatabaseInterface:
    """
    Factory function to create appropriate database adapter based on configuration.

    Args:
        db_type: Database type ('mongodb' or 'firestore'). If not provided, reads from DB_TYPE env var.
        mongo_uri: MongoDB connection URI (for MongoDB)
        mongo_db_name: MongoDB database name (for MongoDB)
        firestore_project_id: Google Cloud project ID (for Firestore)
        firestore_credentials_path: Path to Firestore credentials JSON (for Firestore)

    Returns:
        DatabaseInterface: Configured database adapter

    Raises:
        ValueError: If database type is invalid or required configuration is missing
    """
    # Determine database type
    if db_type is None:
        db_type = os.getenv("DB_TYPE", "mongodb").lower()

    logger.info(f"Initializing database with type: {db_type}")

    if db_type == "mongodb":
        # MongoDB configuration
        if mongo_uri is None:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

        if mongo_db_name is None:
            mongo_db_name = os.getenv("MONGO_DB", "polylearner")

        logger.info(
            f"Creating MongoDB adapter with URI: {mongo_uri}, Database: {mongo_db_name}"
        )
        return MongoDBAdapter(uri=mongo_uri, database_name=mongo_db_name)

    elif db_type == "firestore":
        # Firestore configuration
        if firestore_project_id is None:
            firestore_project_id = os.getenv("FIRESTORE_PROJECT_ID")

        if firestore_credentials_path is None:
            firestore_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        logger.info(
            f"Creating Firestore adapter with project: {firestore_project_id or 'default'}"
        )
        return FirestoreAdapter(
            project_id=firestore_project_id, credentials_path=firestore_credentials_path
        )

    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. Must be 'mongodb' or 'firestore'"
        )


def get_database_type() -> str:
    """
    Get the configured database type from environment.

    Returns:
        str: Database type ('mongodb' or 'firestore')
    """
    return os.getenv("DB_TYPE", "mongodb").lower()
