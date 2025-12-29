# Vector Embeddings & Calendar Integration

## Overview

The analytics service now includes advanced features for:
1. **Vector Embeddings** - Semantic representation of tasks as numerical vectors
2. **Calendar Integration** - Automatic creation of Google Calendar events from intelligent schedules

## Vector Embeddings

### What are Vector Embeddings?

Vector embeddings are numerical representations of tasks that capture their semantic meaning. Similar tasks will have similar vectors, enabling:
- Intelligent task grouping
- Similarity-based scheduling
- Semantic search and recommendations

### How It Works

The service generates **384-dimensional vectors** for each task using:

1. **LLM-based embeddings** (when OpenAI is available):
   - Uses `text-embedding-3-small` model
   - Combines task title, goal, and category
   - Produces high-quality semantic vectors

2. **Fallback embeddings** (when LLM is unavailable):
   - Hash-based deterministic vectors
   - Includes categorical features (task type)
   - Normalized priority and time features

### API Endpoints

#### Get Task Embeddings

```bash
GET /analytics/embeddings
```

**Response:**
```json
{
  "total_tasks": 10,
  "embedding_dimension": 384,
  "embeddings": {
    "1": {
      "vector": [0.234, -0.567, 0.891, ...],
      "dimension": 384
    },
    "2": {
      "vector": [-0.123, 0.456, -0.789, ...],
      "dimension": 384
    }
  }
}
```

**Use Cases:**
- Visualize task relationships (use dimensionality reduction: t-SNE, UMAP)
- Find similar tasks
- Cluster tasks automatically
- Train custom ML models

---

## Calendar Integration

### Overview

The intelligent scheduling system can now automatically create events in your Google Calendar, turning AI-generated schedules into actionable calendar blocks.

### Features

✅ **Automatic Event Creation** - Schedule blocks become calendar events  
✅ **Smart Descriptions** - Each event includes task details and scheduling rationale  
✅ **Batch Creation** - All schedule blocks created at once  
✅ **Error Handling** - Graceful handling of calendar API errors  
✅ **Event Tracking** - Returns calendar event IDs for reference

### API Endpoints

#### 1. Get Intelligent Schedule with Embeddings

```bash
GET /analytics/schedule/intelligent?include_embeddings=true
```

**Query Parameters:**
- `week_start` (optional): ISO date (e.g., "2025-12-30")
- `daily_start` (optional): Work day start hour (default: 9)
- `daily_end` (optional): Work day end hour (default: 17)
- `peak_hours` (optional): Peak productivity hours (default: "9-12")
- `include_embeddings` (optional): Generate embeddings (default: true)

**Response:**
```json
{
  "week_start": "2025-12-30T00:00:00",
  "schedule": [
    {
      "task_id": 1,
      "task_title": "Train CNN model",
      "category": "coding",
      "start_time": "2025-12-30T09:00:00",
      "end_time": "2025-12-30T11:00:00",
      "duration_hours": 2.0,
      "scheduling_reason": "High-priority coding during peak hours",
      "embedding_sample": [0.234, -0.567, 0.891, 0.123, -0.456]
    }
  ],
  "total_blocks": 15,
  "total_hours": 40.5,
  "cognitive_metrics": {
    "cognitive_tax_score": 0.234,
    "context_switches": 8,
    "average_block_duration": 2.7,
    "fragmentation_score": 0.133
  },
  "recommendations": [...],
  "embeddings_generated": 10,
  "embedding_dimension": 384
}
```

#### 2. Create Calendar Events from Schedule

```bash
POST /analytics/schedule/intelligent/create-events
```

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Query Parameters:**
- `week_start` (optional): ISO date
- `daily_start` (optional): Work day start hour
- `daily_end` (optional): Work day end hour
- `peak_hours` (optional): Peak productivity hours
- `calendar_id` (optional): Target calendar (default: "primary")

**Response:**
```json
{
  "status": "success",
  "week_start": "2025-12-30T00:00:00",
  "embeddings_generated": 10,
  "schedule": {
    "total_blocks": 15,
    "total_hours": 40.5,
    "cognitive_metrics": {
      "cognitive_tax_score": 0.234,
      "context_switches": 8,
      "average_block_duration": 2.7
    }
  },
  "calendar_events": {
    "created": 15,
    "failed": 0,
    "events": [
      {
        "task_id": 1,
        "event_id": "abc123xyz",
        "event_link": "https://calendar.google.com/event?eid=...",
        "start_time": "2025-12-30T09:00:00",
        "end_time": "2025-12-30T11:00:00"
      }
    ]
  },
  "task_embeddings": {
    "1": {
      "dimension": 384,
      "sample": [0.234, -0.567, 0.891, 0.123, -0.456]
    }
  }
}
```

---

## Complete Workflow Example

### Step 1: Create Tasks

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Train ML model",
    "category": "coding",
    "time_hours": 3,
    "goal": "Train CNN on image dataset",
    "artifact": "code",
    "priority": 9
  }'
```

### Step 2: Generate Embeddings

```bash
curl http://localhost:8000/analytics/embeddings
```

This returns vector representations of all tasks.

### Step 3: Get Intelligent Schedule

```bash
curl "http://localhost:8000/analytics/schedule/intelligent?include_embeddings=true&peak_hours=9-13"
```

### Step 4: Create Calendar Events

```bash
curl -X POST "http://localhost:8000/analytics/schedule/intelligent/create-events?peak_hours=9-13" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Your Google Calendar now has all tasks scheduled optimally!

---

## Understanding the Output

### Vector Embeddings

Each task gets a 384-dimensional vector. Example:

```json
{
  "task_id": 1,
  "title": "Train CNN model",
  "embedding": [0.234, -0.567, 0.891, ...]
}
```

**Interpreting Embeddings:**
- Similar tasks have similar vectors (measured by cosine similarity)
- First 378 dimensions: semantic features from task content
- Next 4 dimensions: category one-hot encoding
- Last 2 dimensions: priority (normalized) and time (normalized)

**Cosine Similarity Example:**
```python
import numpy as np

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Similarity between two tasks
sim = cosine_similarity(embedding1, embedding2)
# sim > 0.8: Very similar tasks
# sim > 0.5: Somewhat similar
# sim < 0.3: Different tasks
```

### Schedule Blocks

Each block in the schedule includes:

```json
{
  "task_id": 1,
  "task_title": "Train CNN model",
  "category": "coding",
  "start_time": "2025-12-30T09:00:00",
  "end_time": "2025-12-30T11:00:00",
  "duration_hours": 2.0,
  "scheduling_reason": "High-priority task during peak hours",
  "embedding_sample": [0.234, -0.567, 0.891, 0.123, -0.456]
}
```

- **scheduling_reason**: AI explanation for why this time slot was chosen
- **embedding_sample**: First 5 dimensions of the task vector (for reference)

### Cognitive Metrics

```json
{
  "cognitive_tax_score": 0.234,
  "context_switches": 8,
  "average_block_duration": 2.7,
  "fragmentation_score": 0.133,
  "interpretation": "Excellent - Very low context switching"
}
```

- **cognitive_tax_score**: 0-1 scale (lower is better)
- **context_switches**: Number of category changes
- **average_block_duration**: Hours per block (longer is better)
- **fragmentation_score**: Ratio of small blocks (lower is better)

### Calendar Events

```json
{
  "task_id": 1,
  "event_id": "abc123xyz",
  "event_link": "https://calendar.google.com/event?eid=...",
  "start_time": "2025-12-30T09:00:00",
  "end_time": "2025-12-30T11:00:00"
}
```

- **event_id**: Google Calendar event ID (use for updates/deletion)
- **event_link**: Direct link to view/edit in Google Calendar
- Click the link to see the event details

---

## Advanced Use Cases

### 1. Visualizing Task Embeddings

Use dimensionality reduction to visualize task relationships:

```python
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# Get embeddings from API
response = requests.get('http://localhost:8000/analytics/embeddings')
embeddings_data = response.json()

# Extract vectors and task IDs
task_ids = list(embeddings_data['embeddings'].keys())
vectors = [embeddings_data['embeddings'][tid]['vector'] for tid in task_ids]

# Reduce to 2D
tsne = TSNE(n_components=2, random_state=42)
vectors_2d = tsne.fit_transform(vectors)

# Plot
plt.figure(figsize=(10, 8))
plt.scatter(vectors_2d[:, 0], vectors_2d[:, 1])
for i, tid in enumerate(task_ids):
    plt.annotate(f"Task {tid}", (vectors_2d[i, 0], vectors_2d[i, 1]))
plt.title("Task Similarity Map")
plt.show()
```

### 2. Finding Similar Tasks

```python
def find_similar_tasks(target_task_id, embeddings, top_k=5):
    target_vec = np.array(embeddings[str(target_task_id)]['vector'])
    
    similarities = []
    for task_id, data in embeddings.items():
        if task_id == str(target_task_id):
            continue
        vec = np.array(data['vector'])
        sim = cosine_similarity(target_vec, vec)
        similarities.append((task_id, sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

# Find tasks similar to task 1
similar = find_similar_tasks(1, embeddings_data['embeddings'])
print(f"Tasks similar to Task 1: {similar}")
```

### 3. Automated Weekly Planning

```python
import requests
from datetime import datetime, timedelta

# Get next Monday
today = datetime.now()
days_to_monday = (7 - today.weekday()) % 7
next_monday = (today + timedelta(days=days_to_monday)).replace(hour=0, minute=0, second=0)

# Create schedule and calendar events
response = requests.post(
    'http://localhost:8000/analytics/schedule/intelligent/create-events',
    headers={'Authorization': f'Bearer {jwt_token}'},
    params={
        'week_start': next_monday.isoformat(),
        'daily_start': 9,
        'daily_end': 17,
        'peak_hours': '9-12'
    }
)

result = response.json()
print(f"Created {result['calendar_events']['created']} events for next week!")
```

### 4. Comparing Task Clusters

```python
# Group tasks by embedding similarity
from sklearn.cluster import KMeans

vectors = [embeddings_data['embeddings'][tid]['vector'] for tid in task_ids]
kmeans = KMeans(n_clusters=3, random_state=42)
clusters = kmeans.fit_predict(vectors)

# Analyze clusters
for i in range(3):
    cluster_tasks = [task_ids[j] for j in range(len(task_ids)) if clusters[j] == i]
    print(f"Cluster {i}: Tasks {cluster_tasks}")
```

---

## Requirements

### Google Calendar Access

To use calendar integration, users must:

1. **Sign in with Google** using the `/auth/google` endpoint
2. **Grant calendar permissions** during OAuth flow
3. **Have a valid access token** in their user profile

### Environment Variables

```bash
# For OpenAI embeddings (recommended)
OPENAI_API_KEY=your-key-here

# For Google Calendar
GOOGLE_CLIENT_ID=your-google-client-id

# Alternative: Use Anthropic or Ollama
LLM_PROVIDER=openai  # or anthropic, ollama
```

---

## Error Handling

### Common Issues

**Issue:** "Google Calendar access required"
- **Solution**: Sign in with Google and grant calendar permissions

**Issue:** Embeddings generation fails
- **Solution**: Service falls back to simple embeddings automatically

**Issue:** Calendar event creation fails
- **Solution**: Check Google token validity, calendar permissions

### Error Response Format

```json
{
  "status": "error",
  "message": "Failed to create calendar events",
  "calendar_events": {
    "created": 10,
    "failed": 5,
    "events": [
      {
        "task_id": 3,
        "error": "Calendar API rate limit exceeded"
      }
    ]
  }
}
```

---

## Performance Considerations

### Embedding Generation

- **OpenAI embeddings**: ~0.5-1 second per task
- **Simple embeddings**: <0.01 seconds per task
- **Batch processing**: Automatically handled

### Calendar Event Creation

- **Rate limits**: Google Calendar API has rate limits
- **Batch size**: Create 20-50 events at a time recommended
- **Timeout**: 60 seconds for full schedule creation

### Optimization Tips

1. **Cache embeddings**: Store in database for reuse
2. **Incremental updates**: Only create events for new/changed tasks
3. **Background processing**: Use task queue for large schedules

---

## Future Enhancements

Planned improvements:

1. **Vector Search** - Find tasks by semantic similarity
2. **Embedding-based Recommendations** - Suggest related tasks
3. **Calendar Sync** - Two-way sync with Google Calendar
4. **Custom Embeddings** - Fine-tune on user's task history
5. **Conflict Detection** - Check for existing calendar events
6. **Multi-calendar Support** - Distribute across multiple calendars

---

## API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analytics/embeddings` | GET | Get vector embeddings for all tasks |
| `/analytics/schedule/intelligent` | GET | Get AI-optimized schedule with embeddings |
| `/analytics/schedule/intelligent/create-events` | POST | Create calendar events from schedule |

All endpoints require authentication except `/analytics/embeddings`.

Calendar creation requires Google OAuth token with calendar scope.
