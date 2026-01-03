# PolyLearner API

A comprehensive task and learning management system designed to help you organize your work with weekly goals, track task reviews, and measure progress through structured reviews. Built with FastAPI and supports both **MongoDB** and **Google Firestore** as database backends.

## 🎯 Overview

PolyLearner is a RESTful API that enables you to:

- **Create and manage tasks** with categories, time estimates, and goals
- **Organize work into weekly goals** with associated task groups and reviews
- **Track task reviews** with focus rate, artifact links, and completion status
- **Capture weekly reviews** to measure progress and improve planning

## ✨ Key Features

### Task Management
- Create tasks with:
  - Title, category (research, coding, admin, networking)
  - Time estimates in hours
  - Goal description
  - Artifact type (article, notes, code)
  - Link to a weekly goal (optional)
  - Task review (embedded in task document)

### Weekly Goals
- Create weekly goals with:
  - Week number (1–53)
  - Goal description text
  - Associated task IDs (auto-tracked)
  - Weekly review (separate collection)

### Reviews
- **Task Reviews**: Embedded in task documents
  - Notes, focus rate (1–10), artifact URL, completion status (yes/no)
- **Weekly Reviews**: Separate collection
  - Weekly goal reviews with goal linkage
  - Full review metadata stored separately for querying

### REST API
- Swagger UI at `/` for interactive API exploration
- Full CRUD operations for tasks, weekly goals, and reviews
- MongoDB persistence with async Motor driver

## 🏗️ Tech Stack

- **FastAPI** (v0.109.0): Modern Python web framework
- **Motor** (v3.6.0): Async MongoDB driver
- **Database Options**: 
  - **MongoDB** (default): Document-based NoSQL database
  - **Google Firestore**: Fully-managed NoSQL document database
- **Docker & Docker Compose**: Containerization and orchestration
- **Python 3.11**: Runtime

### Database Configuration

PolyLearner supports two database backends. See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed configuration instructions.

**Quick Configuration:**
- **MongoDB** (default): Set `DB_TYPE=mongodb` in `.env`
- **Firestore**: Set `DB_TYPE=firestore` and configure GCP credentials

## 📋 Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Git (optional, for version control)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/loki/polylearner
   ```

2. **Set environment (optional):**
   ```bash
   export APP_ENV=dev  # or 'prod'
   ```

3. **Build and run:**
   ```bash
   docker compose up --build
   ```

4. **Access the API:**
   - Swagger UI: [http://localhost:8000/](http://localhost:8000/)
   - Health check: [http://localhost:8000/health](http://localhost:8000/health)
   - Info endpoint: [http://localhost:8000/info](http://localhost:8000/info)

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r app/requirements.txt
   ```

2. **Ensure MongoDB is running** (either locally or via Docker):
   ```bash
   docker run -d -p 27017:27017 mongo:7
   ```

3. **Set environment variables:**
   ```bash
   export APP_ENV=dev
   export MONGO_URI=mongodb://localhost:27017
   export MONGO_DB=polylearner
   ```

4. **Run the app:**
   ```bash
   cd app
   python app.py
   ```

   Or with auto-reload:
   ```bash
   uvicorn app:app --reload
   ```

## 📚 API Endpoints

### Tasks

- **POST /tasks** — Create a new task
  ```json
  {
    "title": "Read RL paper",
    "category": "research",
    "time_hours": 2.5,
    "goal": "Understand key algorithms",
    "artifact": "notes",
    "weekly_goal_id": 1,
    "review": null
  }
  ```

- **GET /tasks** — List all tasks

### Weekly Goals

- **POST /weekly-goals** — Create a new weekly goal
  ```json
  {
    "week_number": 1,
    "goal": "Complete 3 research tasks and 2 coding projects"
  }
  ```

- **GET /weekly-goals** — List all weekly goals

- **POST /weekly-goals/review** — Add a review to a weekly goal
  ```json
  {
    "weekly_goal_id": 1,
    "notes": "Completed all tasks on time with good focus",
    "focus_rate": 9,
    "artifact": "https://example.com/weekly-review",
    "done_on_time": "yes"
  }
  ```

### Task Reviews

- **POST /reviews** — Add a review to an existing task
  ```json
  {
    "task_id": 1,
    "notes": "Deep work, minimal distractions",
    "focus_rate": 9,
    "artifact": "https://example.com/my-notes",
    "done_on_time": "yes"
  }
  ```

### System Endpoints

- **GET /info** — API information
- **GET /health** — Health check

## 🗄️ MongoDB Collections

### `tasks`
Stores all tasks with embedded reviews:
```javascript
{
  "_id": ObjectId,
  "id": 1,
  "title": "Read RL paper",
  "category": "research",
  "time_hours": 2.5,
  "goal": "Understand key algorithms",
  "artifact": "notes",
  "weekly_goal_id": 1,
  "review": {
    "notes": "Deep work, minimal distractions",
    "focus_rate": 9,
    "artifact": "https://example.com/my-notes",
    "done_on_time": "yes"
  }
}
```

### `weekly_goals`
Stores weekly goals with embedded reviews:
```javascript
{
  "_id": ObjectId,
  "id": 1,
  "week_number": 1,
  "goal": "Complete 3 research tasks and 2 coding projects",
  "task_ids": [1, 2, 3],
  "weekly_review": {
    "notes": "Completed all tasks on time with good focus",
    "focus_rate": 9,
    "artifact": "https://example.com/weekly-review",
    "done_on_time": "yes"
  }
}
```

### `weekly_reviews`
Separate collection for weekly reviews (for querying):
```javascript
{
  "_id": ObjectId,
  "weekly_goal_id": 1,
  "notes": "Completed all tasks on time with good focus",
  "focus_rate": 9,
  "artifact": "https://example.com/weekly-review",
  "done_on_time": "yes"
}
```


## 📖 Data Models

### Task Category
- `research`
- `coding`
- `admin`
- `networking`

### Artifact Types
- `article`
- `notes`
- `code`

### Completion Status
- `yes`
- `no`

### Review Fields
- `notes` (string): Detailed notes on the task/week
- `focus_rate` (integer, 1–10): Concentration level
- `artifact` (URL string): Link to deliverable/notes
- `done_on_time` (enum: yes/no): Completion status

## 🐳 Docker Compose Services

### `app` Service
- **Image**: Built from `./app/Dockerfile`
- **Port**: 8000 (maps to localhost:8000)
- **Environment**: `MONGO_URI`, `MONGO_DB`, `APP_ENV`
- **Depends on**: `mongo` service

### `mongo` Service
- **Image**: `mongo:7`
- **Port**: 27017 (maps to localhost:27017)
- **Volume**: Named volume `mongo_data` for persistence

## 🛠️ Development

### Running Tests
Currently, no automated tests are configured. To add:
```bash
pip install pytest pytest-asyncio
pytest tests/
```

### Code Organization
```
polylearner/
├── app/
│   ├── app.py           # Main FastAPI application
│   ├── models.py        # Pydantic models and enums
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile       # Container image
├── docker-compose.yml   # x
└── README.md           # This file
```

## 📝 Logging

- **Log level**: INFO (adjustable in `app.py`)
- **Handlers**:
  - Console output (stdout)
  - File output (`app.log`)
- **Format**: `timestamp - logger_name - level - message`

## 🔐 Security Notes

- CORS is currently open (`allow_origins=["*"]`)
- For production, restrict CORS to specific domains
- MongoDB runs without authentication (configure in production)
- Validate all inputs before persisting to database

### Google Calendar Integration

**Required OAuth Scopes:**
When setting up Google OAuth, make sure to include these scopes for calendar integration:
- `https://www.googleapis.com/auth/userinfo.profile`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/calendar` (for calendar read/write access)
- `https://www.googleapis.com/auth/calendar.events` (for event creation)

**Auto-Scheduling:**
Tasks are automatically scheduled to your Google Calendar when created or during onboarding:
- Checks existing calendar events to avoid conflicts
- Finds free time slots in 30-minute increments
- Respects work hours (9 AM - 5 PM)
- Schedules weekdays only
- Prioritizes high-priority tasks first
- Adds 1-hour buffer between tasks

**Handling Calendar Permission Errors:**
If you see "Calendar Access Required" notifications:
1. **Sign out** of the application
2. **Sign back in** with Google
3. **Grant calendar permissions** when prompted by Google OAuth
4. If you previously denied permissions, you may need to:
   - Go to [Google Account Permissions](https://myaccount.google.com/permissions)
   - Remove PolyLearner access
   - Sign in again and grant all requested permissions

**Common Issues:**
- **403 Forbidden Error**: The user hasn't granted calendar access. Follow the steps above to re-authenticate.
- **Token Expiry**: Access tokens expire after a certain time. Implement token refresh flow for production use.
- **No Free Slots Found**: If the system can't find a free slot within 30 days, it will notify you. Consider clearing some calendar events or manually scheduling the task.

**Testing Calendar Integration:**
1. Ensure your Google OAuth app is configured with calendar scopes
2. User must grant calendar permissions during sign-in
3. Tasks will be automatically scheduled to Google Calendar when created
4. Check logs for detailed error messages if scheduling fails
5. Use the Calendar view to see all scheduled events

## 🐛 Troubleshooting

### MongoDB Connection Fails
- Ensure `mongo` service is running: `docker compose ps`
- Check `MONGO_URI` matches your setup
- Verify network connectivity between app and mongo containers

### Port Already in Use
- Change port bindings in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # App on 8001
    - "27018:27017"  # Mongo on 27018
  ```

### Module Not Found Error
- Ensure dependencies are installed:
  ```bash
  pip install -r app/requirements.txt
  ```

## 📚 Future Enhancements

Based on the requirements, consider adding:
- Energy/focus analytics per task
- Task grouping by mental expenditure
- Distraction tracking and backlog
- Cross-domain skill graphs
- Habit tracking and behavior analytics
- Integration with external tools (Obsidian, etc.)


## 👤 Author

PolyLearner — A structured task and learning management system.
# polylearner
