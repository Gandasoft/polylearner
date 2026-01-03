#!/usr/bin/env python3
"""
Example script demonstrating how to use the database abstraction layer directly.
This can be used for data migration, testing, or administrative tasks.
"""

import asyncio
import os
from database_factory import create_database
from datetime import datetime


async def example_mongodb():
    """Example using MongoDB adapter"""
    print("=== MongoDB Example ===\n")

    # Create MongoDB adapter
    db = create_database(
        db_type="mongodb",
        mongo_uri="mongodb://localhost:27017",
        mongo_db_name="polylearner_test",
    )

    # Insert a document
    print("Inserting a test user...")
    await db.insert_one(
        "users",
        {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "created_at": datetime.now(),
        },
    )

    # Find the document
    print("Finding the user...")
    user = await db.find_one("users", {"id": 1})
    print(f"Found: {user['name']} ({user['email']})")

    # Update the document
    print("Updating the user...")
    await db.update_one("users", {"id": 1}, {"$set": {"name": "Updated User"}})

    # Find all documents
    print("Finding all users...")
    users = await db.find("users", {})
    print(f"Total users: {len(users)}")

    # Count documents
    count = await db.count_documents("users", {"id": 1})
    print(f"Users with id=1: {count}")

    # Delete the document
    print("Deleting the user...")
    await db.delete_one("users", {"id": 1})

    # Close connection
    await db.close()
    print("\nMongoDB example completed!")


async def example_firestore():
    """Example using Firestore adapter"""
    print("\n=== Firestore Example ===\n")

    # Create Firestore adapter
    # Make sure FIRESTORE_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS are set
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not project_id:
        print("Skipping Firestore example (FIRESTORE_PROJECT_ID not set)")
        return

    db = create_database(db_type="firestore", firestore_project_id=project_id)

    # Insert a document
    print("Inserting a test task...")
    await db.insert_one(
        "tasks",
        {
            "id": 1,
            "title": "Test Task",
            "category": "research",
            "time_hours": 2.0,
            "created_at": datetime.now(),
        },
    )

    # Find the document
    print("Finding the task...")
    task = await db.find_one("tasks", {"id": 1})
    print(f"Found: {task['title']} ({task['category']})")

    # Update with $set
    print("Updating the task...")
    await db.update_one("tasks", {"id": 1}, {"$set": {"title": "Updated Task"}})

    # Update with $inc
    print("Incrementing time_hours...")
    await db.update_one("tasks", {"id": 1}, {"$inc": {"time_hours": 1.0}})

    # Find with filter
    print("Finding tasks with time > 2 hours...")
    tasks = await db.find("tasks", {"time_hours": {"$gt": 2.0}})
    print(f"Found {len(tasks)} tasks")

    # Delete the document
    print("Deleting the task...")
    await db.delete_one("tasks", {"id": 1})

    # Close connection
    await db.close()
    print("\nFirestore example completed!")


async def example_wrapper():
    """Example using DatabaseWrapper for MongoDB-like syntax"""
    print("\n=== DatabaseWrapper Example ===\n")

    from database_wrapper import DatabaseWrapper

    # Create adapter
    db_adapter = create_database(
        db_type="mongodb",
        mongo_uri="mongodb://localhost:27017",
        mongo_db_name="polylearner_test",
    )

    # Wrap it for MongoDB-like syntax
    db = DatabaseWrapper(db_adapter)

    # Use MongoDB-like syntax
    print("Inserting users using wrapper...")
    await db.users.insert_one({"id": 1, "name": "Alice"})
    await db.users.insert_one({"id": 2, "name": "Bob"})
    await db.users.insert_one({"id": 3, "name": "Charlie"})

    # Find with sorting
    print("Finding users sorted by id...")
    cursor = db.users.find({}).sort("id", -1)
    users = await cursor.to_list(length=10)
    print(f"Found {len(users)} users")
    for user in users:
        print(f"  - {user['name']} (id: {user['id']})")

    # Async iteration
    print("\nIterating over users...")
    async for user in db.users.find({}):
        print(f"  - {user['name']}")

    # Update one
    print("\nUpdating Alice...")
    await db.users.update_one({"id": 1}, {"$set": {"name": "Alice Updated"}})

    # Delete many
    print("Deleting all users...")
    result = await db.users.delete_many({})
    print(f"Deleted {result.deleted_count} users")

    # Close connection
    await db_adapter.close()
    print("\nWrapper example completed!")


async def example_migration():
    """Example of data migration from MongoDB to Firestore"""
    print("\n=== Migration Example ===\n")

    # Check if Firestore is configured
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not project_id:
        print("Skipping migration example (FIRESTORE_PROJECT_ID not set)")
        return

    # Create both adapters
    mongo_db = create_database(
        db_type="mongodb",
        mongo_uri="mongodb://localhost:27017",
        mongo_db_name="polylearner_test",
    )

    firestore_db = create_database(db_type="firestore", firestore_project_id=project_id)

    # Insert test data in MongoDB
    print("Creating test data in MongoDB...")
    await mongo_db.insert_one(
        "tasks", {"id": 1, "title": "MongoDB Task", "category": "coding"}
    )

    # Migrate to Firestore
    print("Migrating data to Firestore...")
    tasks = await mongo_db.find("tasks", {})
    for task in tasks:
        task.pop("_id", None)  # Remove MongoDB ObjectId
        await firestore_db.insert_one("tasks", task)
    print(f"Migrated {len(tasks)} tasks")

    # Verify in Firestore
    print("Verifying in Firestore...")
    firestore_tasks = await firestore_db.find("tasks", {})
    print(f"Found {len(firestore_tasks)} tasks in Firestore")

    # Cleanup
    print("Cleaning up...")
    await mongo_db.delete_many("tasks", {})
    await firestore_db.delete_many("tasks", {})

    # Close connections
    await mongo_db.close()
    await firestore_db.close()
    print("\nMigration example completed!")


async def main():
    """Run all examples"""
    try:
        # MongoDB example
        await example_mongodb()

        # Firestore example (if configured)
        await example_firestore()

        # Wrapper example
        await example_wrapper()

        # Migration example (if Firestore configured)
        await example_migration()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Database Abstraction Layer Examples")
    print("=" * 50)
    asyncio.run(main())
