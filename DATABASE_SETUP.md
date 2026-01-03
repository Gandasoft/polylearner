# Database Configuration Guide

PolyLearner supports two database backends: **MongoDB** and **Google Firestore**. You can easily switch between them using environment variables.

## Table of Contents
- [MongoDB Setup (Default)](#mongodb-setup-default)
- [Google Firestore Setup](#google-firestore-setup)
- [Switching Between Databases](#switching-between-databases)
- [Architecture Overview](#architecture-overview)
- [Limitations](#limitations)

## MongoDB Setup (Default)

MongoDB is the default database backend and requires no additional configuration beyond what's already in place.

### Local Development

1. Make sure MongoDB is running locally or via Docker:
   ```bash
   docker-compose up mongo
   ```

2. Set environment variables in `.env`:
   ```env
   DB_TYPE=mongodb
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB=polylearner
   ```

3. Run the application:
   ```bash
   cd app && uvicorn app:app --reload
   ```

### Docker Deployment

The default `docker-compose.yml` already includes MongoDB:
```bash
docker-compose up --build
```

## Google Firestore Setup

Google Firestore is a fully-managed NoSQL document database from Google Cloud Platform.

### Prerequisites

1. **Google Cloud Project**: You need a Google Cloud Platform (GCP) project with Firestore enabled.
2. **Service Account**: Create a service account with Firestore permissions.

### Step-by-Step Setup

#### 1. Create a GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID (e.g., `my-polylearner-project`)

#### 2. Enable Firestore API

1. In the GCP Console, navigate to **Firestore**
2. Click **Select Native Mode** (recommended for PolyLearner)
3. Choose a location (e.g., `us-central1`)
4. Click **Create Database**

#### 3. Create a Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Name it (e.g., `polylearner-db`)
4. Grant the following roles:
   - **Cloud Datastore User** (for read/write access)
   - Or **Cloud Datastore Owner** (for full access including admin operations)
5. Click **Done**

#### 4. Generate Service Account Key

1. Click on your newly created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Choose **JSON** format
5. Download the key file (e.g., `polylearner-firestore-key.json`)
6. **IMPORTANT**: Keep this file secure and never commit it to version control

#### 5. Configure PolyLearner

##### Local Development

1. Place your service account key file in a secure location (e.g., `~/secrets/polylearner-firestore-key.json`)

2. Update your `.env` file:
   ```env
   DB_TYPE=firestore
   FIRESTORE_PROJECT_ID=my-polylearner-project
   GOOGLE_APPLICATION_CREDENTIALS=/home/user/secrets/polylearner-firestore-key.json
   ```

3. Run the application:
   ```bash
   cd app && uvicorn app:app --reload
   ```

##### Docker Deployment

1. Place your service account key file in the project root (gitignored)

2. Update `docker-compose.yml` to mount the credentials:
   ```yaml
   services:
     app:
       volumes:
         - ./polylearner-firestore-key.json:/secrets/firestore-key.json:ro
       environment:
         - DB_TYPE=firestore
         - FIRESTORE_PROJECT_ID=my-polylearner-project
         - GOOGLE_APPLICATION_CREDENTIALS=/secrets/firestore-key.json
   ```

3. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

#### 6. Verify Setup

1. Start the application
2. Check the logs for: `Firestore adapter initialized for project: my-polylearner-project`
3. Create a test task or goal through the API
4. Verify data appears in the Firestore console

## Switching Between Databases

You can switch between MongoDB and Firestore by changing the `DB_TYPE` environment variable.

### From MongoDB to Firestore

1. Export your MongoDB data (optional, for migration):
   ```bash
   mongoexport --db=polylearner --collection=tasks --out=tasks.json
   mongoexport --db=polylearner --collection=goals --out=goals.json
   mongoexport --db=polylearner --collection=users --out=users.json
   ```

2. Update `.env`:
   ```env
   DB_TYPE=firestore
   FIRESTORE_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

3. Restart the application

**Note**: Data is NOT automatically migrated. You'll start with an empty database.

### From Firestore to MongoDB

1. Update `.env`:
   ```env
   DB_TYPE=mongodb
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB=polylearner
   ```

2. Restart the application

## Architecture Overview

### Database Abstraction Layer

PolyLearner uses a database abstraction layer to support multiple backends:

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Database Wrapper│  ← Provides MongoDB-like API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Database Interface│  ← Abstract interface
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│MongoDB │ │Firestore │
│Adapter │ │ Adapter  │
└────────┘ └──────────┘
```

### Key Components

1. **DatabaseInterface** (`database_interface.py`): Abstract base class defining standard operations
2. **MongoDBAdapter** (`mongodb_adapter.py`): MongoDB implementation using Motor
3. **FirestoreAdapter** (`firestore_adapter.py`): Firestore implementation using Google Cloud SDK
4. **DatabaseWrapper** (`database_wrapper.py`): Provides MongoDB-like syntax for both adapters
5. **DatabaseFactory** (`database_factory.py`): Factory for creating the appropriate adapter

### Collections

Both databases use the same collection/document structure:

- `users`: User accounts and authentication
- `tasks`: Individual tasks
- `goals`: User goals
- `coaching_sessions`: AI coaching conversations
- `goal_reviews`: Reviews of completed goals

## Limitations

### Firestore Limitations

While Firestore is a powerful database, it has some differences from MongoDB:

1. **Aggregation Pipelines**: Firestore has limited aggregation capabilities compared to MongoDB. Complex aggregations are handled in application code.

2. **Transactions**: Firestore transactions work differently. The current implementation doesn't use transactions, but they can be added if needed.

3. **Query Operators**: Some MongoDB query operators don't have direct Firestore equivalents:
   - `$regex`: Not supported (use client-side filtering)
   - Complex `$or` queries: Limited support
   - Computed fields: Not supported

4. **Atomic Operations**: MongoDB's `$inc` and `$addToSet` are emulated in Firestore with read-modify-write operations.

5. **Cost**: Firestore charges per read/write operation. Monitor usage to avoid unexpected costs.

### MongoDB Limitations

1. **Scalability**: Self-hosted MongoDB requires more management for scaling compared to Firestore.

2. **Managed Features**: Firestore provides built-in backups, replication, and global distribution.

## Best Practices

### Security

1. **Never commit credentials**: Add `*.json` key files to `.gitignore`
2. **Use IAM roles**: In production, use GCP workload identity instead of service account keys
3. **Rotate keys**: Regularly rotate service account keys
4. **Least privilege**: Grant minimal required permissions to service accounts

### Performance

1. **Index Strategy**: 
   - MongoDB: Create indexes on frequently queried fields
   - Firestore: Composite indexes are auto-created based on query patterns

2. **Batch Operations**: Both databases support batch operations for better performance

3. **Connection Pooling**: 
   - MongoDB: Handled by Motor driver
   - Firestore: Managed by Google Cloud SDK

### Cost Optimization (Firestore)

1. **Read Operations**: Cache frequently accessed data
2. **Write Operations**: Batch updates when possible
3. **Storage**: Delete old documents (implement TTL policies)
4. **Monitoring**: Use GCP billing alerts

## Troubleshooting

### Common Issues

#### "Firestore adapter initialization failed"

- Check that `FIRESTORE_PROJECT_ID` is correct
- Verify service account key path is accessible
- Ensure Firestore API is enabled in GCP

#### "Permission denied" errors

- Verify service account has correct IAM roles
- Check if Firestore is in Native mode (not Datastore mode)

#### "Module not found: google.cloud.firestore"

- Install dependencies: `pip install -r requirements.txt`
- Check that `google-cloud-firestore==2.14.0` is in requirements.txt

#### Data not appearing in Firestore Console

- Check collection names are correct
- Verify document IDs (Firestore uses string IDs)
- Look for errors in application logs

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger('google.cloud.firestore').setLevel(logging.DEBUG)
```

## Migration Tools

We don't provide automatic migration tools yet, but you can export/import data using:

### Export from MongoDB
```bash
mongoexport --db=polylearner --collection=tasks --out=tasks.json --jsonArray
```

### Import to Firestore (Python script)
```python
from google.cloud import firestore
import json

db = firestore.Client(project='your-project-id')
with open('tasks.json') as f:
    tasks = json.load(f)
    for task in tasks:
        task.pop('_id', None)  # Remove MongoDB ID
        doc_id = str(task.get('id', ''))
        db.collection('tasks').document(doc_id).set(task)
```

## Support

For issues or questions:
1. Check application logs for detailed error messages
2. Review Firestore console for data structure
3. Verify environment variables are set correctly
4. Check IAM permissions in GCP Console

## Future Enhancements

Planned improvements:
- [ ] Automatic data migration tool
- [ ] Support for PostgreSQL with SQLAlchemy
- [ ] Multi-database replication
- [ ] Database-agnostic backup/restore utilities
- [ ] Performance benchmarking tools
