from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
import logging.handlers
import json
import os
import sys
import jwt
from ics import Calendar, Event as ICSEvent
from ics.grammar.parse import ContentLine
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from dotenv import load_dotenv
from logger import JsonFormatter
from database_factory import create_database, get_database_type
from database_interface import DatabaseInterface
from database_wrapper import DatabaseWrapper


# Configure logging with JSON format
json_formatter = JsonFormatter()

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(json_formatter)

# File handler
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(json_formatter)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

logger = logging.getLogger(__name__)

# Import modules after logging is configured
from analytics_service import TaskAnalyticsService
from calendar_service import CalendarService
from llm_provider import get_default_provider, LLMProvider
from goal_validation_service import GoalValidationService
from coach_service import (
    generate_coach_response,
    get_user_task_context,
    get_task_vector_insights,
    create_session_summary,
    CoachRequest,
    CoachResponse,
    CoachingSession,
)
from models import (
    MessageRequest,
    MessageResponse,
    TaskCategory,
    TaskArtifact,
    DoneOnTime,
    Review,
    TaskCreate,
    Task,
    GoalReviewCreate,
    GoalReviewResponse,
    ReviewCreate,
    TaskReviewResponse,
    AIRecommendation,
    ScheduleBlock,
    WeekScheduleResponse,
    UserCreate,
    User,
    GoogleAuthRequest,
    AuthResponse,
    GoalSubmission,
    GoalValidationResponse,
    SuggestedTask,
    TaskSuggestionResponse,
    CreateTasksFromSuggestionsRequest,
    GoalCreate,
    Goal,
)

app = FastAPI(
    title="PolyLearner API",
    description="This is an API that uses the roles for polymath learning",
    version="1.0.0",
    docs_url="/",
    redoc_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
# In Docker, environment variables are passed directly from docker-compose.yml
# For local development, load from .env file if it exists
APP_ENV = os.getenv("APP_ENV", "dev")
if APP_ENV == "dev" and os.path.exists("../.env"):
    load_dotenv("../.env")
    logger.info("Loaded environment from ../.env file")
else:
    logger.info(f"Using environment variables from system (APP_ENV={APP_ENV})")

# Database setup
DB_TYPE = os.getenv("DB_TYPE", "mongodb")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "polylearner")
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")
FIRESTORE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

# Log configuration status (without exposing sensitive data)
logger.info(f"DB_TYPE: {DB_TYPE}")
logger.info(f"MONGO_URI: {MONGO_URI}")
logger.info(f"MONGO_DB: {MONGO_DB_NAME}")
logger.info(f"OPENAI_API_KEY configured: {'Yes' if OPENAI_API_KEY else 'No'}")
logger.info(f"GOOGLE_CLIENT_ID configured: {'Yes' if GOOGLE_CLIENT_ID else 'No'}")
logger.info(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'openai')}")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

db_adapter: DatabaseInterface | None = None
db: DatabaseWrapper | None = None
llm_provider: LLMProvider | None = None
analytics_service: TaskAnalyticsService | None = None
goal_validation_service: GoalValidationService | None = None
security = HTTPBearer()


def get_db() -> DatabaseWrapper:
    if db is None:
        raise RuntimeError("Database is not initialized")
    return db


@app.on_event("startup")
async def startup_event():
    global db_adapter, db, llm_provider, analytics_service, goal_validation_service

    # Initialize database adapter
    db_adapter = create_database(
        db_type=DB_TYPE,
        mongo_uri=MONGO_URI,
        mongo_db_name=MONGO_DB_NAME,
        firestore_project_id=FIRESTORE_PROJECT_ID,
        firestore_credentials_path=FIRESTORE_CREDENTIALS_PATH,
    )

    # Wrap the adapter to provide MongoDB-like interface
    db = DatabaseWrapper(db_adapter)

    # Initialize LLM provider (will try configured provider or fallback)
    llm_provider = get_default_provider()

    # For services that need the native MongoDB database object, we provide it if using MongoDB
    # This is a temporary compatibility layer
    if get_database_type() == "mongodb":
        from mongodb_adapter import MongoDBAdapter

        native_db = (
            db_adapter.get_native_db()
            if isinstance(db_adapter, MongoDBAdapter)
            else None
        )
    else:
        native_db = None

    if llm_provider and llm_provider.is_available():
        analytics_service = TaskAnalyticsService(llm_provider, native_db)
        goal_validation_service = GoalValidationService(llm_provider, native_db)
        logger.info(
            "Analytics and Goal Validation services initialized with LLM provider"
        )
    else:
        analytics_service = TaskAnalyticsService(db=native_db)
        goal_validation_service = GoalValidationService(db=native_db)
        logger.warning("Services initialized without LLM (limited functionality)")

    logger.info(f"Application starting up with {DB_TYPE} database...")


@app.on_event("shutdown")
async def shutdown_event():
    global db_adapter
    if db_adapter is not None:
        await db_adapter.close()
    logger.info(
        f"Application shutting down and {DB_TYPE} database connection closed..."
    )


def create_jwt_token(user_id: int, email: str) -> str:
    """Create JWT token for user"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Verify JWT token and validate Google session"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        db = get_db()
        user_doc = await db.users.find_one({"id": user_id})

        if user_doc is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Check if Google token is still valid
        if user_doc.get("google_token_expiry"):
            token_expiry = user_doc["google_token_expiry"]
            # Normalize both datetimes to naive UTC for comparison
            now = datetime.utcnow()
            # If token_expiry is timezone-aware, convert to naive UTC
            if hasattr(token_expiry, "tzinfo") and token_expiry.tzinfo is not None:
                token_expiry = token_expiry.replace(tzinfo=None)

            if now > token_expiry:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google session has expired. Please sign in again.",
                )

        user_doc.pop("_id", None)
        return User(**user_doc)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@app.get("/info")
async def root():
    logger.info("Info endpoint accessed")
    return {
        "message": "PolyLearner API - Basic FastAPI Application",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/auth/google", response_model=AuthResponse, include_in_schema=False)
async def google_auth(auth_request: GoogleAuthRequest):
    """Authenticate user with Google OAuth"""
    try:
        # Get user info from Google using access token
        import httpx

        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {auth_request.access_token}"},
            )

        if user_info_response.status_code != 200:
            raise ValueError("Invalid access token")

        user_info = user_info_response.json()

        # Extract user info
        google_id = user_info["id"]
        email = user_info["email"]
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")

        db = get_db()

        # Calculate token expiry (use UTC for consistency)
        token_expiry = datetime.utcnow() + timedelta(seconds=auth_request.expires_in)

        # Check if user exists
        user_doc = await db.users.find_one({"google_id": google_id})

        if user_doc is None:
            # Create new user
            last_user = await db.users.find_one(sort=[("id", -1)])
            next_id = (last_user["id"] + 1) if last_user else 1

            user_doc = {
                "id": next_id,
                "email": email,
                "name": name,
                "google_id": google_id,
                "picture": picture,
                "created_at": datetime.utcnow(),
                "tokens_used": 0,
                "tokens_limit": 100000,
                "google_access_token": auth_request.access_token,
                "google_token_expiry": token_expiry,
            }

            await db.users.insert_one(user_doc)
            logger.info(f"Created new user with email {email}")
        else:
            # Update existing user's token and expiry
            await db.users.update_one(
                {"google_id": google_id},
                {
                    "$set": {
                        "google_access_token": auth_request.access_token,
                        "google_token_expiry": token_expiry,
                        "name": name,
                        "picture": picture,
                    }
                },
            )
            user_doc = await db.users.find_one({"google_id": google_id})

        user_doc.pop("_id", None)
        user = User(**user_doc)

        # Create JWT token
        access_token = create_jwt_token(user.id, user.email)

        return AuthResponse(access_token=access_token, user=user)

    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google credentials: {str(e)}",
        )


@app.get("/auth/me", response_model=User, include_in_schema=False)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user


@app.patch("/users/tokens")
async def update_token_usage(
    tokens_used: int, current_user: User = Depends(get_current_user)
):
    """Update user's token usage"""
    db = get_db()

    await db.users.update_one(
        {"id": current_user.id}, {"$inc": {"tokens_used": tokens_used}}
    )

    logger.info(f"Updated token usage for user {current_user.id}: +{tokens_used}")
    return {"success": True, "tokens_used": current_user.tokens_used + tokens_used}


# ==================== GOAL VALIDATION & ONBOARDING ENDPOINTS ====================


@app.post("/onboarding/validate-goal", response_model=GoalValidationResponse)
async def validate_onboarding_goal(
    goal_submission: GoalSubmission, current_user: User = Depends(get_current_user)
):
    """
    Validate a user's goal during onboarding using SMART criteria and productivity guidelines.

    The goal must be:
    - Specific: Clearly defined, not vague
    - Measurable: Has quantifiable or clear qualitative success criteria
    - Achievable: Realistic given constraints
    - Relevant: Aligned with user's intentions
    - Time-bound: Has a deadline or timeframe

    Returns validation result with feedback and suggestions for improvement if rejected.
    """
    if not goal_validation_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Goal validation service not available",
        )

    validation_result = await goal_validation_service.validate_goal(
        goal=goal_submission.goal
    )

    db = get_db()

    # If goal_id provided, update existing goal; otherwise create new one
    if goal_submission.goal_id:
        # Update existing goal
        existing_goal = await db.goals.find_one(
            {"id": goal_submission.goal_id, "user_id": current_user.id}
        )
        if not existing_goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal {goal_submission.goal_id} not found",
            )

        await db.goals.update_one(
            {"id": goal_submission.goal_id, "user_id": current_user.id},
            {
                "$set": {
                    "goal": goal_submission.goal,
                    "is_validated": validation_result["is_valid"],
                    "validation_feedback": validation_result["feedback"],
                }
            },
        )
        next_id = goal_submission.goal_id
        logger.info(
            f"Updated goal {next_id} for user {current_user.id}: '{goal_submission.goal}' -> "
            f"{'APPROVED' if validation_result['is_valid'] else 'REJECTED'}"
        )
    else:
        # Create new goal
        last_goal = await db.goals.find_one(sort=[("id", -1)])
        next_id = (last_goal["id"] + 1) if last_goal else 1

        goal_doc = {
            "id": next_id,
            "user_id": current_user.id,
            "goal": goal_submission.goal,
            "timeframe": "inferred from goal and feedback",
            "category": None,
            "is_validated": validation_result["is_valid"],
            "validation_feedback": validation_result["feedback"],
            "created_at": datetime.utcnow(),
            "tasks_generated": False,
            "task_ids": [],
        }

        await db.goals.insert_one(goal_doc)

        logger.info(
            f"Created goal {next_id} for user {current_user.id}: '{goal_submission.goal}' -> "
            f"{'APPROVED' if validation_result['is_valid'] else 'REJECTED'}"
        )

    # Add goal_id to response
    validation_result["goal_id"] = next_id

    # Normalize refined_versions to ensure correct format
    # Some LLMs might return nested structures, so we normalize to Dict[str, str]
    if "refined_versions" in validation_result:
        normalized_versions = []
        for version in validation_result["refined_versions"]:
            if isinstance(version, dict):
                # Extract the goal string - handle various possible formats
                goal_str = version.get("goal")
                if isinstance(goal_str, dict):
                    # If goal is a nested dict, try to extract the actual goal string
                    goal_str = (
                        goal_str.get("refined_goal")
                        or goal_str.get("goal")
                        or str(goal_str)
                    )

                normalized_versions.append(
                    {
                        "goal": str(goal_str)
                        if goal_str
                        else version.get("refined_goal", ""),
                        "improvement": str(version.get("improvement", "")),
                        "why_better": str(version.get("why_better", "")),
                    }
                )
        validation_result["refined_versions"] = normalized_versions

    return GoalValidationResponse(**validation_result)


@app.post("/onboarding/suggest-tasks", response_model=TaskSuggestionResponse)
async def suggest_tasks_for_goal(
    goal_submission: GoalSubmission, current_user: User = Depends(get_current_user)
):
    """
    Generate task suggestions for a goal following productivity guidelines.

    The LLM will:
    1. Apply 80/20 rule (identify high-impact tasks)
    2. Batch similar tasks to minimize context switching
    3. Categorize by type (research, coding, admin, networking)
    4. Assign appropriate energy levels
    5. Estimate realistic time blocks
    6. Prioritize using Eisenhower Matrix
    7. Consider dependencies and optimal sequencing

    Works with any goal - validation is done separately to provide refinement suggestions.

    Also saves the goal to the unified goals collection and returns the goal_id.
    """
    if not goal_validation_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Goal validation service not available",
        )

    db = get_db()

    # If goal_id is provided, update existing goal; otherwise create new one
    if goal_submission.goal_id:
        # Update existing goal
        existing_goal = await db.goals.find_one(
            {"id": goal_submission.goal_id, "user_id": current_user.id}
        )
        if not existing_goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal {goal_submission.goal_id} not found for user {current_user.id}",
            )

        # Update the goal text and mark as validated
        await db.goals.update_one(
            {"id": goal_submission.goal_id, "user_id": current_user.id},
            {
                "$set": {
                    "goal": goal_submission.goal,
                    "is_validated": True,
                    "validation_feedback": None,
                }
            },
        )
        next_goal_id = goal_submission.goal_id
        logger.info(f"Updated goal {next_goal_id} for user {current_user.id}")
    else:
        # Create new goal
        last_goal = await db.goals.find_one(sort=[("id", -1)])
        next_goal_id = (last_goal["id"] + 1) if last_goal else 1

        goal_doc = {
            "id": next_goal_id,
            "user_id": current_user.id,
            "goal": goal_submission.goal,
            "timeframe": "inferred from goal",
            "category": None,
            "is_validated": True,
            "validation_feedback": None,
            "created_at": datetime.utcnow(),
            "tasks_generated": False,
            "task_ids": [],
        }

        await db.goals.insert_one(goal_doc)
        logger.info(f"Created new goal {next_goal_id} for user {current_user.id}")

    # Generate task suggestions (no validation check - user can proceed with any goal)
    suggestions = await goal_validation_service.suggest_tasks_for_goal(
        goal=goal_submission.goal
    )

    if "error" in suggestions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate task suggestions: {suggestions['error']}",
        )

    # Convert weekly_breakdown to string if it's a dict
    if isinstance(suggestions.get("weekly_breakdown"), dict):
        breakdown_dict = suggestions["weekly_breakdown"]
        breakdown_str = ", ".join(
            [f"{day}: {hours}h" for day, hours in breakdown_dict.items()]
        )
        suggestions["weekly_breakdown"] = breakdown_str

    logger.info(
        f"Generated {len(suggestions['suggested_tasks'])} tasks for user {current_user.id} "
        f"goal: '{goal_submission.goal}' with goal_id: {next_goal_id}"
    )

    # Add goal_id to response
    suggestions["goal_id"] = next_goal_id

    return TaskSuggestionResponse(**suggestions)


@app.post("/onboarding/create-tasks-from-suggestions")
async def create_tasks_from_suggestions(
    request: CreateTasksFromSuggestionsRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create actual tasks in the database from LLM suggestions.

    This allows users to:
    1. Accept all suggested tasks
    2. Accept selected tasks
    3. Modify tasks before creation

    Also creates Google Calendar events if the user has a valid access token.

    Returns created task IDs and calendar event creation status.
    """
    db = get_db()
    created_tasks = []
    calendar_events = []
    calendar_errors = []

    # Validate goal exists and get goal text
    if not request.goal_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="goal_id is required to create tasks",
        )

    goal = await db.goals.find_one({"id": request.goal_id, "user_id": current_user.id})
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal {request.goal_id} not found",
        )

    goal_text = goal.get("goal", "")

    # Get last task ID
    last_task = await db.tasks.find_one(sort=[("id", -1)])
    next_id = (last_task["id"] + 1) if last_task else 1

    # Create tasks in database - all belong to the same goal
    for idx, suggested_task in enumerate(request.suggested_tasks):
        task_doc = {
            "id": next_id + idx,
            "title": suggested_task.title,
            "category": suggested_task.category,
            "time_hours": suggested_task.time_hours,
            "goal": goal_text,  # Denormalized from parent goal
            "artifact": suggested_task.artifact,
            "priority": suggested_task.priority,
            "goal_id": request.goal_id,  # Foreign key to parent goal
            "review": None,
            "due_date": None,
        }

        await db.tasks.insert_one(task_doc)
        created_tasks.append(task_doc["id"])

    # Update the unified goals collection with task_ids
    if request.goal_id:
        # Update unified goals collection
        goal_update_result = await db.goals.update_one(
            {"id": request.goal_id},
            {
                "$addToSet": {"task_ids": {"$each": created_tasks}},
                "$set": {"tasks_generated": True},
            },
        )

        logger.info(
            f"Updated goal {request.goal_id} with {len(created_tasks)} task IDs"
        )

    logger.info(
        f"Created {len(created_tasks)} tasks from suggestions for user {current_user.id}"
    )

    # Use AI-powered auto-scheduling instead of simple sequential scheduling
    if current_user.google_access_token:
        logger.info("Using AI-powered auto-scheduling for created tasks")
        schedule_result = await auto_schedule_tasks_to_calendar(
            created_tasks, current_user, db
        )

        if schedule_result.get("scheduled"):
            calendar_events = schedule_result.get("events", [])
            logger.info(f"AI-scheduled {len(calendar_events)} tasks to Google Calendar")
        else:
            logger.warning(f"Auto-scheduling failed: {schedule_result.get('reason')}")
            calendar_errors.append(
                {"error": f"Auto-scheduling failed: {schedule_result.get('reason')}"}
            )
    else:
        logger.warning(
            f"User {current_user.id} does not have Google Calendar access token - skipping calendar event creation"
        )

    response = {
        "created_task_ids": created_tasks,
        "count": len(created_tasks),
        "message": f"Successfully created {len(created_tasks)} tasks",
    }

    # Add calendar info if events were created
    if calendar_events:
        response["calendar_events_created"] = len(calendar_events)
        response["calendar_events"] = calendar_events

    if calendar_errors:
        response["calendar_errors"] = calendar_errors

    return response


@app.get("/onboarding/goals", response_model=List[Goal])
async def list_onboarding_goals(current_user: User = Depends(get_current_user)):
    """List all goals for the current user (for backwards compatibility with frontend)"""
    db = get_db()
    cursor = db.goals.find({"user_id": current_user.id}).sort("created_at", -1)

    goals = []
    async for doc in cursor:
        doc.pop("_id", None)
        goals.append(Goal(**doc))

    return goals


# Unified Goals Endpoints
@app.post("/goals", response_model=Goal, status_code=201)
async def create_goal(goal: GoalCreate, current_user: User = Depends(get_current_user)):
    """Create a unified goal"""
    db = get_db()

    # Generate next goal id
    last_goal = await db.goals.find_one(sort=[("id", -1)])
    next_id = (last_goal["id"] + 1) if last_goal else 1

    goal_doc = {
        "id": next_id,
        "user_id": current_user.id,
        "goal": goal.goal,
        "timeframe": goal.timeframe,
        "category": goal.category,
        "is_validated": False,
        "validation_feedback": None,
        "created_at": datetime.utcnow(),
        "tasks_generated": False,
        "task_ids": [],
    }
    await db.goals.insert_one(goal_doc)

    logger.info(f"Created unified goal id={next_id} for user_id={current_user.id}")
    return Goal(**goal_doc)


@app.get("/goals", response_model=List[Goal])
async def list_goals(current_user: User = Depends(get_current_user)):
    """List all goals for the current user"""
    db = get_db()

    # Get goals from the unified goals collection
    goals = []
    cursor = db.goals.find({"user_id": current_user.id}).sort("created_at", -1)
    async for doc in cursor:
        doc.pop("_id", None)
        goals.append(Goal(**doc))

    return goals


@app.get("/goals/{goal_id}", response_model=Goal)
async def get_goal(goal_id: int, current_user: User = Depends(get_current_user)):
    """Get a specific goal by ID"""
    db = get_db()

    # Get from unified goals collection
    goal_doc = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})

    if not goal_doc:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal_doc.pop("_id", None)
    return Goal(**goal_doc)


@app.delete("/goals/{goal_id}")
async def delete_goal(goal_id: int, current_user: User = Depends(get_current_user)):
    """
    Delete a goal and all its associated tasks.
    Also removes calendar events for all tasks.
    """
    db = get_db()

    # Verify goal exists and belongs to user
    goal_doc = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
    if not goal_doc:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Find all tasks associated with this goal
    tasks_cursor = db.tasks.find({"goal_id": goal_id})
    tasks_to_delete = []
    async for task in tasks_cursor:
        tasks_to_delete.append(task)

    # Delete calendar events for each task (if user has calendar access)
    if current_user.google_access_token:
        try:
            calendar_service = CalendarService(current_user.google_access_token)
            for task in tasks_to_delete:
                if task.get("calendar_event_id"):
                    try:
                        await calendar_service.delete_event(task["calendar_event_id"])
                        logger.info(
                            f"Deleted calendar event {task['calendar_event_id']} for task {task['id']}"
                        )
                    except Exception as e:
                        # Log but don't fail if calendar deletion fails
                        logger.warning(
                            f"Failed to delete calendar event {task['calendar_event_id']}: {str(e)}"
                        )
        except Exception as e:
            logger.warning(f"Calendar service error during task deletion: {str(e)}")

    # Delete all tasks associated with this goal
    delete_result = await db.tasks.delete_many({"goal_id": goal_id})
    logger.info(f"Deleted {delete_result.deleted_count} tasks for goal {goal_id}")

    # Delete the goal
    await db.goals.delete_one({"id": goal_id, "user_id": current_user.id})
    logger.info(f"Deleted goal {goal_id} for user {current_user.id}")

    return {
        "message": f"Goal and {delete_result.deleted_count} associated tasks deleted successfully"
    }


@app.get("/calendar/events")
async def get_calendar_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Fetch events from user's Google Calendar.

    Args:
        time_min: Optional ISO timestamp for earliest event (defaults to start of current week)
        time_max: Optional ISO timestamp for latest event (defaults to end of current week)

    Returns:
        List of calendar events with task information
    """
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=401,
            detail="Google Calendar access required. Please sign in with Google.",
        )

    try:
        calendar_service = CalendarService(current_user.google_access_token)

        # Default to current week if not specified
        if not time_min:
            now = datetime.now()
            days_to_monday = (now.weekday()) % 7
            week_start = (now - timedelta(days=days_to_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            time_min_dt = week_start
        else:
            time_min_dt = datetime.fromisoformat(time_min)

        if not time_max:
            time_max_dt = time_min_dt + timedelta(days=7)
        else:
            time_max_dt = datetime.fromisoformat(time_max)

        # Fetch events from Google Calendar
        events = await calendar_service.list_events(
            calendar_id="primary",
            time_min=time_min_dt,
            time_max=time_max_dt,
            max_results=100,
        )

        logger.info(f"Fetched {len(events)} calendar events for user {current_user.id}")

        # Transform events to match our schedule format
        schedule_blocks = []
        for event in events:
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")

            if start and end:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                duration = (end_dt - start_dt).total_seconds() / 3600

                # Try to extract category from description
                description = event.get("description", "")
                category = "admin"  # default
                if "Category: " in description:
                    category_line = [
                        line for line in description.split("\n") if "Category: " in line
                    ]
                    if category_line:
                        category = (
                            category_line[0].split("Category: ")[1].strip().lower()
                        )

                schedule_blocks.append(
                    {
                        "event_id": event.get("id"),
                        "task_title": event.get("summary", "Untitled Event"),
                        "category": category,
                        "start_time": start,
                        "end_time": end,
                        "duration_hours": round(duration, 2),
                        "description": description,
                    }
                )

        return {
            "events": schedule_blocks,
            "count": len(schedule_blocks),
            "time_min": time_min_dt.isoformat(),
            "time_max": time_max_dt.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to fetch calendar events: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch calendar events: {str(e)}"
        )


# ==================== TASK ENDPOINTS ====================


async def auto_schedule_tasks_to_calendar(task_ids: List[int], user: User, db):
    """
    Automatically schedule tasks to Google Calendar using AI-optimized time slots.

    Args:
        task_ids: List of task IDs to schedule
        user: Current user with Google access token
        db: Database connection

    Returns:
        Dictionary with scheduling results
    """
    if not user.google_access_token:
        logger.warning(
            f"User {user.id} doesn't have Google Calendar access - skipping auto-scheduling"
        )
        return {"scheduled": False, "reason": "No Google Calendar access"}

    try:
        # Fetch tasks from database
        tasks_to_schedule = []
        for task_id in task_ids:
            task_doc = await db.tasks.find_one({"id": task_id})
            if task_doc:
                task_doc.pop("_id", None)
                tasks_to_schedule.append(Task(**task_doc))

        if not tasks_to_schedule:
            return {"scheduled": False, "reason": "No tasks found"}

        # Use AI to generate optimal schedule
        calendar_service = CalendarService(user.google_access_token)

        # Get existing calendar events to avoid conflicts
        from datetime import timezone

        now = datetime.now(timezone.utc)
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        try:
            existing_events = await calendar_service.list_events(
                calendar_id="primary",
                time_min=week_start,
                time_max=week_end,
                max_results=100,
            )
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                logger.error(
                    f"Calendar permission denied for user {user.id}. User needs to grant calendar access."
                )
                return {
                    "scheduled": False,
                    "reason": "Calendar permission denied. Please re-authenticate with calendar access.",
                    "error_code": "calendar_permission_denied",
                }
            existing_events = []  # Continue without checking conflicts

        # Find available time slots (9 AM - 5 PM on weekdays)
        scheduled_events = []

        # Build busy time slots from existing events
        busy_slots = []
        for event in existing_events:
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")
            if start and end:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                busy_slots.append((start_dt, end_dt))

        logger.info(f"Found {len(busy_slots)} existing calendar events to avoid")

        # Track daily cognitive load to distribute tasks evenly across the week
        daily_hours = {}  # Track hours scheduled per day
        daily_task_count = {}  # Track number of tasks per day
        MAX_DAILY_HOURS = 6  # Max 6 hours of focused work per day
        MAX_TASKS_PER_DAY = 4  # Max 4 tasks per day to avoid context switching

        # Helper function to check if a time slot is free
        def is_slot_free(start: datetime, end: datetime) -> bool:
            """Check if a time slot doesn't conflict with existing events"""
            for busy_start, busy_end in busy_slots:
                # Check for overlap
                if start < busy_end and end > busy_start:
                    return False
            return True

        # Helper function to get cognitive load for a day
        def get_daily_load(day_key: str) -> tuple:
            """Returns (hours_used, task_count) for a given day"""
            return (daily_hours.get(day_key, 0), daily_task_count.get(day_key, 0))

        # Helper function to check if day has capacity
        def has_daily_capacity(day_key: str, duration_hours: float) -> bool:
            """Check if a day can accommodate more work without cognitive overload"""
            hours, count = get_daily_load(day_key)
            return (
                hours + duration_hours <= MAX_DAILY_HOURS and count < MAX_TASKS_PER_DAY
            )

        # Helper function to find next free slot with cognitive load distribution
        def find_next_free_slot(
            start: datetime, duration_hours: float, prefer_new_day: bool = False
        ) -> tuple:
            """Find the next available time slot that respects cognitive load limits

            Args:
                start: Starting datetime to search from
                duration_hours: Task duration in hours
                prefer_new_day: If True, prefer scheduling on a different day for better distribution
            """
            current = start
            max_attempts = 60  # Search up to 60 half-hour slots
            attempts = 0

            # If prefer_new_day, skip to next day
            if prefer_new_day:
                current = (current + timedelta(days=1)).replace(hour=9, minute=0)

            while attempts < max_attempts:
                # Skip weekends
                while current.weekday() >= 5:
                    current = (current + timedelta(days=1)).replace(hour=9, minute=0)

                day_key = current.strftime("%Y-%m-%d")

                # Check if day has capacity for this task
                if not has_daily_capacity(day_key, duration_hours):
                    # Move to next day if this day is at capacity
                    current = (current + timedelta(days=1)).replace(hour=9, minute=0)
                    continue

                # Skip if past work hours
                if current.hour >= 17:
                    current = (current + timedelta(days=1)).replace(hour=9, minute=0)
                    continue

                # Calculate potential end time
                end = current + timedelta(hours=duration_hours)

                # If extends past 5 PM, cap at 5 PM
                if end.hour >= 17 or (end.hour == 17 and end.minute > 0):
                    end = current.replace(hour=17, minute=0)
                    actual_duration = (end - current).total_seconds() / 3600

                    # If slot is too small, move to next day
                    if actual_duration < 0.5:  # At least 30 minutes
                        current = (current + timedelta(days=1)).replace(
                            hour=9, minute=0
                        )
                        continue

                # Check if this slot is free
                if is_slot_free(current, end):
                    return current, end

                # Slot is busy, try next 30-minute increment
                current += timedelta(minutes=30)
                attempts += 1

            return None, None

        current_slot = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if current_slot < now:
            current_slot += timedelta(days=1)

        # Group tasks by category for better distribution
        tasks_by_category = {}
        for task in tasks_to_schedule:
            cat = task.category
            if cat not in tasks_by_category:
                tasks_by_category[cat] = []
            tasks_by_category[cat].append(task)

        # Sort tasks by priority (high priority first)
        sorted_tasks = sorted(
            tasks_to_schedule,
            key=lambda t: -(t.priority if hasattr(t, "priority") and t.priority else 5),
        )

        # Schedule tasks with cognitive load distribution
        scheduled_count = 0
        for i, task in enumerate(sorted_tasks):
            # For better distribution, prefer scheduling on a new day if:
            # 1. Not the first task
            # 2. Task is from a different category than previous
            # 3. We've already scheduled 2+ tasks today
            prefer_new_day = False
            if i > 0:
                current_day_key = current_slot.strftime("%Y-%m-%d")
                _, task_count_today = get_daily_load(current_day_key)

                # Prefer new day if we've scheduled 2+ tasks today, for better distribution
                if task_count_today >= 2:
                    prefer_new_day = True

            # Find next free slot for this task
            start_time, end_time = find_next_free_slot(
                current_slot, task.time_hours, prefer_new_day
            )

            if start_time is None:
                logger.warning(
                    f"Could not find free slot for task {task.id} '{task.title}' within search window"
                )
                continue

            # Create calendar event
            try:
                event = await calendar_service.create_event(
                    summary=task.title,
                    start_time=start_time,
                    end_time=end_time,
                    description=f"Category: {task.category}\\nGoal: {task.goal}\\nArtifact: {task.artifact}\\nPriority: {task.priority if hasattr(task, 'priority') and task.priority else 5}",
                    calendar_id="primary",
                )

                scheduled_events.append(
                    {
                        "task_id": task.id,
                        "task_title": task.title,
                        "event_id": event.get("id"),
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                    }
                )

                # Update daily tracking
                day_key = start_time.strftime("%Y-%m-%d")
                daily_hours[day_key] = daily_hours.get(day_key, 0) + task.time_hours
                daily_task_count[day_key] = daily_task_count.get(day_key, 0) + 1

                # Add this event to busy slots to avoid conflicts with subsequent tasks
                busy_slots.append((start_time, end_time))

                scheduled_count += 1
                logger.info(
                    f"Scheduled task {task.id} '{task.title}' on {day_key}: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')} (Day load: {daily_hours[day_key]:.1f}h, {daily_task_count[day_key]} tasks)"
                )

                # Move search window forward by 30 minutes after this event for next task
                # This creates natural spacing between tasks
                current_slot = end_time + timedelta(minutes=30)

            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "Forbidden" in error_msg:
                    logger.error(
                        f"Calendar permission denied while scheduling task {task.id}"
                    )
                    return {
                        "scheduled": False,
                        "reason": "Calendar write permission denied. Please sign out and sign in again, making sure to grant calendar access.",
                        "error_code": "calendar_permission_denied",
                    }
                logger.error(f"Failed to schedule task {task.id}: {error_msg}")

        return {
            "scheduled": True,
            "events_created": len(scheduled_events),
            "events": scheduled_events,
        }

    except Exception as e:
        logger.error(f"Auto-scheduling failed: {str(e)}", exc_info=True)
        return {"scheduled": False, "reason": str(e)}


@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    auto_schedule: bool = True,
):
    """
    Create a new task with title, category, time in hours, goal, artifact, and optional review.

    Args:
        task: Task data
        current_user: Authenticated user
        auto_schedule: Whether to automatically schedule the task on Google Calendar (default: True)
    """
    db = get_db()

    # Validate goal_id - task must belong to a goal
    goal = await db.goals.find_one({"id": task.goal_id, "user_id": current_user.id})
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Generate next task id
    last_task = await db.tasks.find_one(sort=[("id", -1)])
    next_id = (last_task["id"] + 1) if last_task else 1

    # Create task with denormalized goal text
    task_doc = {
        "id": next_id,
        **task.model_dump(),
        "goal": goal.get("goal"),  # Denormalize goal text for display
    }
    await db.tasks.insert_one(task_doc)

    # Register this task under the goal
    await db.goals.update_one(
        {"id": task.goal_id},
        {"$addToSet": {"task_ids": next_id}},
    )

    logger.info(f"Created task with ID {next_id} and title '{task.title}'")

    # Auto-schedule to Google Calendar if enabled
    calendar_info = None
    if auto_schedule:
        schedule_result = await auto_schedule_tasks_to_calendar(
            [next_id], current_user, db
        )
        if schedule_result.get("scheduled"):
            logger.info(f"Task {next_id} auto-scheduled to Google Calendar")
            calendar_info = schedule_result

            # Store calendar scheduling info in the database
            await db.tasks.update_one(
                {"id": next_id}, {"$set": {"calendar_scheduling": calendar_info}}
            )
        elif schedule_result.get("error_code") == "calendar_permission_denied":
            logger.warning(f"Calendar permission denied for user {current_user.id}")
            calendar_info = {"error": schedule_result.get("reason")}

            # Store error info in database
            await db.tasks.update_one(
                {"id": next_id}, {"$set": {"calendar_scheduling": calendar_info}}
            )

    created_task = Task(**task_doc)

    # Add calendar scheduling info to response if available
    if calendar_info:
        response_dict = created_task.model_dump()
        response_dict["calendar_scheduling"] = calendar_info
        return response_dict

    return created_task


@app.get("/tasks", response_model=List[Task])
async def list_tasks(
    goal_id: Optional[int] = None, current_user: User = Depends(get_current_user)
):
    """
    List all tasks for the current user.
    Optionally filter by goal_id to get tasks for a specific goal.
    """
    logger.info(f"Listing tasks for user {current_user.id}, goal_id filter: {goal_id}")
    db = get_db()

    # Build query - always filter by user's goals
    user_goals = await db.goals.find({"user_id": current_user.id}).to_list(length=None)
    user_goal_ids = [g["id"] for g in user_goals]

    query = {"goal_id": {"$in": user_goal_ids}}
    if goal_id is not None:
        # Further filter by specific goal
        query["goal_id"] = goal_id

    cursor = db.tasks.find(query)
    tasks: List[Task] = []
    async for doc in cursor:
        doc.pop("_id", None)
        # Extract calendar_scheduling before creating Task object
        calendar_scheduling = doc.pop("calendar_scheduling", None)
        task = Task(**doc)

        # Add calendar_scheduling to response if it exists
        if calendar_scheduling:
            task_dict = task.model_dump()
            task_dict["calendar_scheduling"] = calendar_scheduling
            tasks.append(task_dict)
        else:
            tasks.append(task)
    return tasks


@app.post("/weekly-goals", response_model=Goal, status_code=201)
async def create_weekly_goal(
    goal: GoalCreate, current_user: User = Depends(get_current_user)
):
    """Create a weekly goal - saved to unified goals collection."""
    db = get_db()

    # Generate next goal id from unified collection
    last_goal = await db.goals.find_one(sort=[("id", -1)])
    next_id = (last_goal["id"] + 1) if last_goal else 1

    goal_doc = {
        "id": next_id,
        "user_id": current_user.id,
        "goal": goal.goal,
        "timeframe": goal.timeframe or "ongoing",
        "category": goal.category or "weekly",
        "is_validated": True,
        "validation_feedback": None,
        "created_at": datetime.utcnow(),
        "tasks_generated": False,
        "task_ids": [],
    }
    await db.goals.insert_one(goal_doc)

    logger.info(f"Created weekly goal id={next_id} for user {current_user.id}")
    return Goal(**goal_doc)


@app.get("/weekly-goals", response_model=List[Goal])
async def list_weekly_goals(current_user: User = Depends(get_current_user)):
    """List all weekly goals (filtered from unified goals collection)"""
    logger.info("Listing all weekly goals")
    db = get_db()
    # Filter goals with category="weekly"
    cursor = db.goals.find({"user_id": current_user.id, "category": "weekly"})
    goals: List[Goal] = []
    async for doc in cursor:
        doc.pop("_id", None)
        goals.append(Goal(**doc))
    return goals


@app.post("/weekly-goals/review", response_model=GoalReviewResponse, status_code=201)
async def add_weekly_review(review: GoalReviewCreate):
    """Attach a review to an existing goal."""
    db = get_db()

    goal = await db.goals.find_one({"id": review.goal_id})
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")

    review_data = Review(
        notes=review.notes,
        focus_rate=review.focus_rate,
        artifact=review.artifact,
        done_on_time=review.done_on_time,
    )

    # Store review in goal_reviews collection
    await db.goal_reviews.insert_one(
        {"goal_id": review.goal_id, **review_data.model_dump()}
    )

    logger.info(f"Added review for goal_id={review.goal_id}")
    return GoalReviewResponse(goal_id=review.goal_id, **review_data.model_dump())


@app.post("/tasks/reviews", response_model=TaskReviewResponse, status_code=201)
async def add_review(review: ReviewCreate):
    """Add a review linked to an existing task by task_id."""
    db = get_db()

    # Find the task in MongoDB
    task_doc = await db.tasks.find_one({"id": review.task_id})
    if task_doc is None:
        logger.warning(f"Attempt to review non-existent task id={review.task_id}")
        raise HTTPException(status_code=404, detail="Task not found")

    review_data = Review(
        notes=review.notes,
        focus_rate=review.focus_rate,
        artifact=review.artifact,
        done_on_time=review.done_on_time,
    )

    # Attach review to task document
    await db.tasks.update_one(
        {"id": review.task_id},
        {"$set": {"review": review_data.model_dump()}},
    )

    logger.info(f"Added review for task id={review.task_id}")
    return TaskReviewResponse(task_id=review.task_id, **review_data.model_dump())


def calculate_cognitive_tax(schedule: List[dict]) -> float:
    """Calculate cognitive tax based on context switching"""
    if not schedule:
        return 0.0

    switches = 0
    for i in range(1, len(schedule)):
        if schedule[i]["category"] != schedule[i - 1]["category"]:
            switches += 1

    # Lower score is better
    return switches / len(schedule) if len(schedule) > 0 else 0.0


def optimize_schedule(
    tasks: List[Task], week_start: datetime, daily_start: int = 9, daily_end: int = 17
) -> List[dict]:
    """Optimize task scheduling to minimize cognitive tax"""
    if not tasks:
        return []

    # Sort by category (to group similar tasks), then priority, then duration
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            t.category,
            -(t.priority if hasattr(t, "priority") and t.priority else 5),
            -t.time_hours,
        ),
    )

    schedule = []
    cursor = week_start.replace(hour=daily_start, minute=0, second=0, microsecond=0)

    for task in sorted_tasks:
        remaining = task.time_hours

        while remaining > 0:
            current_hour = cursor.hour + cursor.minute / 60

            # Move to next day if past working hours
            if current_hour >= daily_end:
                cursor = cursor.replace(
                    hour=daily_start, minute=0, second=0, microsecond=0
                )
                cursor += timedelta(days=1)
                continue

            # Calculate available time today
            available = daily_end - current_hour
            block_duration = min(available, remaining)

            block_end = cursor + timedelta(hours=block_duration)

            schedule.append(
                {
                    "task_id": task.id,
                    "task_title": task.title,
                    "category": task.category,
                    "start_time": cursor.isoformat(),
                    "end_time": block_end.isoformat(),
                    "duration_hours": block_duration,
                }
            )

            cursor = block_end
            remaining -= block_duration

    return schedule


async def generate_ai_recommendations(tasks: List[Task]) -> List[AIRecommendation]:
    """Generate AI-powered recommendations for task scheduling"""
    if not llm_provider or not llm_provider.is_available() or not tasks:
        return [
            AIRecommendation(
                suggestion="Group similar tasks together",
                reason="Minimize context switching to reduce cognitive load",
                priority=8,
            ),
            AIRecommendation(
                suggestion="Schedule deep work in your peak hours",
                reason="High-priority coding and research tasks need focused attention",
                priority=9,
            ),
            AIRecommendation(
                suggestion="Leave buffer time between task blocks",
                reason="Allow for breaks and unexpected delays",
                priority=7,
            ),
        ]

    try:
        # Prepare task summary for AI
        task_summary = []
        for t in tasks:
            task_summary.append(
                f"- {t.title} ({t.category}, {t.time_hours}h, priority: {getattr(t, 'priority', 5)})"
            )

        prompt = f"""You are an AI productivity assistant. Analyze these tasks and provide 3 specific, actionable recommendations to optimize the weekly schedule and reduce cognitive tax:

Tasks:
{chr(10).join(task_summary)}

You MUST respond with ONLY a valid JSON array, nothing else. No explanation, no markdown, just the JSON array.

Format:
[
  {{"suggestion": "specific actionable recommendation", "reason": "why this helps", "priority": 8}},
  {{"suggestion": "another recommendation", "reason": "explanation", "priority": 9}},
  {{"suggestion": "third recommendation", "reason": "benefit", "priority": 7}}
]

Focus on:
1. Minimizing context switching between different task types
2. Optimal time blocks for deep work
3. Energy management throughout the week

Remember: Output ONLY the JSON array, nothing else."""

        content = await llm_provider.generate(
            prompt=prompt, temperature=0.7, max_tokens=500, json_mode=True
        )

        # Try to parse JSON from response
        import json
        import re

        logger.info(f"LLM response for recommendations: {content[:200]}...")

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        # Try to find JSON array in the content
        if not content.strip().startswith("["):
            array_match = re.search(r"\[.*?\]", content, re.DOTALL)
            if array_match:
                content = array_match.group(0)

        if not content or not content.strip():
            raise ValueError("Empty response from LLM")

        recommendations_data = json.loads(content.strip())

        # If LLM returned a single dict instead of a list, wrap it
        if isinstance(recommendations_data, dict):
            logger.warning(
                "LLM returned single recommendation dict instead of list, wrapping it"
            )
            recommendations_data = [recommendations_data]

        if not isinstance(recommendations_data, list):
            raise ValueError(f"Expected list, got {type(recommendations_data)}")

        recommendations = [AIRecommendation(**r) for r in recommendations_data[:3]]

        return recommendations
    except Exception as e:
        logger.error(
            f"Error generating AI recommendations: {e}, Content: {content[:500] if 'content' in locals() else 'No content'}"
        )
        return [
            AIRecommendation(
                suggestion="Group similar tasks together",
                reason="Minimize context switching to reduce cognitive load",
                priority=8,
            )
        ]


@app.get("/recommendations", response_model=List[AIRecommendation])
async def get_recommendations():
    """Get AI-powered task recommendations"""
    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    recommendations = await generate_ai_recommendations(tasks)
    return recommendations


@app.get("/schedule", response_model=WeekScheduleResponse)
async def get_optimized_schedule(
    week_start: Optional[str] = None, daily_start: int = 9, daily_end: int = 17
):
    """Get optimized weekly schedule with AI recommendations"""
    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    # Parse week start or use current Monday
    if week_start:
        week_start_dt = datetime.fromisoformat(week_start)
    else:
        now = datetime.now()
        days_to_monday = (now.weekday()) % 7
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Generate optimized schedule
    schedule = optimize_schedule(tasks, week_start_dt, daily_start, daily_end)

    # Calculate metrics
    total_hours = sum(t.time_hours for t in tasks)
    cognitive_tax = calculate_cognitive_tax(schedule)

    # Get AI recommendations
    recommendations = await generate_ai_recommendations(tasks)

    # Convert to response format
    schedule_blocks = [ScheduleBlock(**block) for block in schedule]

    return WeekScheduleResponse(
        week_start=week_start_dt.isoformat(),
        schedule=schedule_blocks,
        recommendations=recommendations,
        total_hours=total_hours,
        cognitive_tax_score=cognitive_tax,
    )


@app.get("/schedule/ics")
async def export_schedule_ics(
    week_start: Optional[str] = None, daily_start: int = 9, daily_end: int = 17
):
    """Export schedule as ICS file"""
    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    # Parse week start
    if week_start:
        week_start_dt = datetime.fromisoformat(week_start)
    else:
        now = datetime.now()
        days_to_monday = (now.weekday()) % 7
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Generate schedule
    schedule = optimize_schedule(tasks, week_start_dt, daily_start, daily_end)

    # Create ICS calendar
    cal = Calendar()

    for block in schedule:
        event = ICSEvent()
        event.name = block["task_title"]
        event.begin = datetime.fromisoformat(block["start_time"])
        event.end = datetime.fromisoformat(block["end_time"])
        event.description = (
            f"Category: {block['category']}\nDuration: {block['duration_hours']:.1f}h"
        )
        cal.events.add(event)

    from fastapi.responses import Response

    return Response(
        content=str(cal),
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=polylearner-schedule.ics"
        },
    )


# ============================================================================
# Analytics Service Endpoints
# ============================================================================


@app.get("/analytics/groups", include_in_schema=False)
async def get_task_groups():
    """Group tasks by similarity using LLM analysis"""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    grouped = await analytics_service.group_tasks_by_similarity(tasks)

    # Convert to response format
    result = []
    for group_name, group_tasks in grouped.items():
        result.append(
            {
                "group_name": group_name,
                "task_count": len(group_tasks),
                "total_hours": sum(t.time_hours for t in group_tasks),
                "tasks": [
                    {"id": t.id, "title": t.title, "category": t.category}
                    for t in group_tasks
                ],
            }
        )

    logger.info(f"Generated {len(result)} task groups")
    return {"groups": result, "total_groups": len(result)}


@app.get("/analytics/schedule/intelligent", include_in_schema=False)
async def get_intelligent_schedule(
    week_start: Optional[str] = None,
    daily_start: int = 9,
    daily_end: int = 17,
    peak_hours: str = "9-12",
    include_embeddings: bool = True,
):
    """Get AI-optimized schedule that groups similar tasks and minimizes cognitive load"""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    # Parse week start
    if week_start:
        week_start_dt = datetime.fromisoformat(week_start)
    else:
        now = datetime.now()
        days_to_monday = (now.weekday()) % 7
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Generate embeddings if requested
    embeddings = {}
    if include_embeddings:
        logger.info("Generating task embeddings...")
        embeddings = await analytics_service.generate_task_embeddings(tasks)

    preferences = {
        "peak_hours": peak_hours,
        "break_duration_minutes": 15,
        "max_continuous_hours": 2,
    }

    # Generate intelligent schedule
    schedule = await analytics_service.generate_intelligent_schedule(
        tasks, week_start_dt, daily_start, daily_end, preferences
    )

    # Add embedding samples to schedule blocks
    if embeddings:
        for block in schedule:
            task_id = block["task_id"]
            if task_id in embeddings:
                block["embedding_sample"] = embeddings[task_id][
                    :5
                ]  # First 5 dimensions

    # Calculate metrics
    cognitive_metrics = analytics_service.calculate_cognitive_tax(schedule)
    total_hours = sum(s["duration_hours"] for s in schedule)

    # Get AI recommendations
    recommendations = await generate_ai_recommendations(tasks)

    logger.info(
        f"Generated intelligent schedule with {len(schedule)} blocks, cognitive tax: {cognitive_metrics['cognitive_tax_score']}"
    )

    return {
        "week_start": week_start_dt.isoformat(),
        "schedule": schedule,
        "total_blocks": len(schedule),
        "total_hours": round(total_hours, 2),
        "cognitive_metrics": cognitive_metrics,
        "recommendations": recommendations,
        "embeddings_generated": len(embeddings) if embeddings else 0,
        "embedding_dimension": len(list(embeddings.values())[0]) if embeddings else 0,
    }


@app.get("/analytics/patterns", include_in_schema=False)
async def analyze_task_patterns():
    """Analyze patterns and trends in tasks with AI insights"""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    analysis = await analytics_service.analyze_task_patterns(tasks)

    logger.info(f"Analyzed {len(tasks)} tasks")
    return analysis


@app.get("/analytics/cognitive-tax", include_in_schema=False)
async def get_cognitive_tax_analysis(
    week_start: Optional[str] = None, daily_start: int = 9, daily_end: int = 17
):
    """Analyze cognitive tax of current schedule"""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    # Parse week start
    if week_start:
        week_start_dt = datetime.fromisoformat(week_start)
    else:
        now = datetime.now()
        days_to_monday = (now.weekday()) % 7
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Generate two schedules for comparison
    basic_schedule = optimize_schedule(tasks, week_start_dt, daily_start, daily_end)
    intelligent_schedule = await analytics_service.generate_intelligent_schedule(
        tasks, week_start_dt, daily_start, daily_end
    )

    basic_metrics = analytics_service.calculate_cognitive_tax(basic_schedule)
    intelligent_metrics = analytics_service.calculate_cognitive_tax(
        intelligent_schedule
    )

    improvement = (
        basic_metrics["cognitive_tax_score"]
        - intelligent_metrics["cognitive_tax_score"]
    )
    improvement_pct = (
        (improvement / basic_metrics["cognitive_tax_score"] * 100)
        if basic_metrics["cognitive_tax_score"] > 0
        else 0
    )

    return {
        "basic_schedule": {"metrics": basic_metrics, "blocks": len(basic_schedule)},
        "intelligent_schedule": {
            "metrics": intelligent_metrics,
            "blocks": len(intelligent_schedule),
        },
        "improvement": {
            "absolute": round(improvement, 3),
            "percentage": round(improvement_pct, 1),
            "recommendation": "Use intelligent scheduling"
            if improvement > 0
            else "Schedules are similar",
        },
    }


@app.post("/analytics/query", include_in_schema=False)
async def natural_language_query(request: MessageRequest):
    """
    Ask questions about your tasks in natural language.

    Examples:
    - "How many coding tasks do I have?"
    - "What's the average time for research tasks?"
    - "Show me high priority tasks"
    - "Which category has the most hours allocated?"
    - "How many tasks have been reviewed?"
    """
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    result = await analytics_service.natural_language_query(request.message)
    logger.info(f"NL Query: {request.message}")
    return result


@app.get("/analytics/insights/database", include_in_schema=False)
async def get_database_insights():
    """
    Get comprehensive insights from the MongoDB database.
    Provides real-time statistics and patterns from your actual task data.
    """
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    insights = await analytics_service.get_database_insights()
    return insights


@app.get("/analytics/embeddings", include_in_schema=False)
async def get_task_embeddings():
    """
    Generate vector embeddings for all tasks.
    Returns semantic vector representations of each task.
    """
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    embeddings = await analytics_service.generate_task_embeddings(tasks)

    return {
        "total_tasks": len(tasks),
        "embedding_dimension": len(list(embeddings.values())[0]) if embeddings else 0,
        "embeddings": {
            str(task_id): {"vector": vector, "dimension": len(vector)}
            for task_id, vector in embeddings.items()
        },
    }


@app.post("/analytics/schedule/intelligent/create-events", include_in_schema=False)
async def create_calendar_events_from_intelligent_schedule(
    week_start: Optional[str] = None,
    daily_start: int = 9,
    daily_end: int = 17,
    peak_hours: str = "9-12",
    calendar_id: str = "primary",
    current_user: User = Depends(get_current_user),
):
    """
    Generate intelligent schedule with vector embeddings and create actual Google Calendar events.

    This endpoint:
    1. Generates vector embeddings for all tasks
    2. Creates an AI-optimized schedule
    3. Creates the scheduled tasks as events in Google Calendar

    Requires Google Calendar access (user must be authenticated)
    """
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not available")

    # Check if user has Google access token
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=401,
            detail="Google Calendar access required. Please sign in with Google.",
        )

    db = get_db()
    cursor = db.tasks.find()
    tasks = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found to schedule")

    # Step 1: Generate vector embeddings
    logger.info("Generating task embeddings...")
    embeddings = await analytics_service.generate_task_embeddings(tasks)

    # Step 2: Parse week start
    if week_start:
        week_start_dt = datetime.fromisoformat(week_start)
    else:
        now = datetime.now()
        days_to_monday = (now.weekday()) % 7
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Step 3: Generate intelligent schedule
    preferences = {
        "peak_hours": peak_hours,
        "break_duration_minutes": 15,
        "max_continuous_hours": 2,
    }

    logger.info("Generating intelligent schedule...")
    schedule = await analytics_service.generate_intelligent_schedule(
        tasks, week_start_dt, daily_start, daily_end, preferences
    )

    # Step 4: Calculate cognitive metrics
    cognitive_metrics = analytics_service.calculate_cognitive_tax(schedule)

    # Step 5: Create calendar events
    logger.info("Creating calendar events...")
    calendar_service = CalendarService(current_user.google_access_token)

    try:
        created_events = await analytics_service.create_calendar_events_from_schedule(
            schedule, calendar_service, calendar_id
        )

        # Count successful and failed events
        successful = [e for e in created_events if "event_id" in e]
        failed = [e for e in created_events if "error" in e]

        logger.info(f"Created {len(successful)} calendar events, {len(failed)} failed")

        return {
            "status": "success",
            "week_start": week_start_dt.isoformat(),
            "embeddings_generated": len(embeddings),
            "schedule": {
                "total_blocks": len(schedule),
                "total_hours": sum(s["duration_hours"] for s in schedule),
                "cognitive_metrics": cognitive_metrics,
            },
            "calendar_events": {
                "created": len(successful),
                "failed": len(failed),
                "events": created_events,
            },
            "task_embeddings": {
                task_id: {
                    "dimension": len(vector),
                    "sample": vector[:5],  # First 5 dimensions as sample
                }
                for task_id, vector in embeddings.items()
            },
        }

    except Exception as e:
        logger.error(f"Error creating calendar events: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create calendar events: {str(e)}"
        )


# ===== COACH ENDPOINTS =====


@app.get("/coach/sessions", include_in_schema=False)
async def get_coaching_sessions(current_user: User = Depends(get_current_user)):
    """Get all coaching sessions for the current user."""
    db = get_db()

    # Query sessions from MongoDB
    cursor = db.coaching_sessions.find({"user_id": current_user.id}).sort(
        "timestamp", -1
    )
    sessions = []

    async for doc in cursor:
        doc.pop("_id", None)
        sessions.append(doc)

    return sessions


@app.post("/coach/sessions", include_in_schema=False)
async def create_coaching_session(
    title: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    """Create a new coaching session."""
    db = get_db()

    session_id = f"session_{current_user.id}_{datetime.now().timestamp()}"

    session = {
        "id": session_id,
        "user_id": current_user.id,
        "title": title
        or f"Goal Coaching Session - {datetime.now().strftime('%b %d, %Y')}",
        "timestamp": datetime.now().isoformat(),
        "messages": [],
    }

    await db.coaching_sessions.insert_one(session)
    session.pop("_id", None)

    return session


@app.post("/coach/chat", response_model=CoachResponse, include_in_schema=False)
async def chat_with_coach(
    request: CoachRequest, current_user: User = Depends(get_current_user)
):
    """
    Send a message to the AI coach and get a response.
    The coach has access to user's tasks and can provide insights.
    """
    db = get_db()

    # Verify session exists
    session = await db.coaching_sessions.find_one(
        {"id": request.session_id, "user_id": current_user.id}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create a simple database wrapper for compatibility with coach_service
    class SimpleDB:
        def __init__(self, async_db, user_id):
            self.async_db = async_db
            self.user_id = user_id
            self._cache = None

        async def get_tasks(self):
            if self._cache is None:
                cursor = self.async_db.tasks.find({"user_id": self.user_id})
                tasks = []
                async for doc in cursor:
                    doc.pop("_id", None)
                    tasks.append(Task(**doc))
                self._cache = tasks
            return self._cache

        def query(self, model):
            # Return a query object that filters by user_id
            return SimpleQuery(self, model)

    class SimpleQuery:
        def __init__(self, db, model):
            self.db = db
            self.model = model
            self.filters = {}

        def filter(self, **kwargs):
            self.filters.update(kwargs)
            return self

        async def all(self):
            return await self.db.get_tasks()

    simple_db = SimpleDB(db, current_user.id)
    tasks = await simple_db.get_tasks()

    # Get task context
    task_context = _get_user_task_context_from_tasks(tasks)
    task_insights = _get_task_vector_insights_from_tasks(tasks)

    # Generate coach response
    system_prompt = f"""You are an AI Goal Coach helping users achieve their learning and personal development goals. 
You have access to the user's current tasks, progress, and productivity metrics.

Your role is to:
1. Provide motivational and actionable advice
2. Help break down goals into manageable tasks
3. Identify patterns in their work and suggest improvements
4. Keep them accountable and on track
5. Celebrate their wins and help them learn from setbacks

Current user context:
{task_context}

Task insights:
- Total tasks: {task_insights["total_tasks"]}
- Category distribution: {task_insights["category_distribution"]}
- Time allocation: {task_insights["time_allocation"]["total_hours"]}h total

Be conversational, supportive, and specific. Reference their actual tasks and progress when relevant.
Keep responses concise but helpful (2-4 paragraphs max).
"""

    try:
        llm_provider = get_default_provider()
        response_text = llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=request.message,
            temperature=0.7,
            max_tokens=500,
        )
    except Exception as e:
        logger.error(f"Error generating coach response: {e}")
        response_text = """I'm here to help you with your goals! Based on your current tasks, 
I can see you're working on several important objectives. 

Let me know what specific aspect you'd like to discuss - whether it's staying motivated, 
prioritizing tasks, or overcoming challenges. I'm here to support you!"""

    # Save messages to session
    user_message = {
        "id": f"msg_{datetime.now().timestamp()}",
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat(),
    }

    assistant_message = {
        "id": f"msg_{datetime.now().timestamp() + 0.001}",
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now().isoformat(),
    }

    await db.coaching_sessions.update_one(
        {"id": request.session_id},
        {"$push": {"messages": {"$each": [user_message, assistant_message]}}},
    )

    return CoachResponse(response=response_text, task_insights=task_insights)


def _get_user_task_context_from_tasks(tasks: List[Task]) -> str:
    """Helper to get task context from task list."""
    if not tasks:
        return "The user has no tasks yet."

    completed_tasks = [t for t in tasks if t.review is not None]
    pending_tasks = [t for t in tasks if t.review is None]

    context_parts = [
        "USER TASK OVERVIEW:",
        f"- Total tasks: {len(tasks)}",
        f"- Completed: {len(completed_tasks)}",
        f"- Pending: {len(pending_tasks)}",
    ]

    if pending_tasks:
        context_parts.append("\nPENDING TASKS:")
        for task in pending_tasks[:10]:
            task_info = [
                f"  • {task.title}",
                f"    Goal: {task.goal}",
                f"    Category: {task.category}",
                f"    Time estimate: {task.time_hours}h",
                f"    Priority: {task.priority or 5}/10",
            ]
            if task.due_date:
                task_info.append(f"    Due: {task.due_date}")
            context_parts.append("\n".join(task_info))

    if completed_tasks:
        context_parts.append("\nRECENTLY COMPLETED TASKS:")
        for task in completed_tasks[-5:]:
            focus_rate = task.review.get("focus_rate", "N/A") if task.review else "N/A"
            context_parts.append(f"  • {task.title} (Focus: {focus_rate}/10)")

    if tasks:
        completed = [t for t in tasks if t.review]
        if completed:
            avg_focus = sum([t.review.get("focus_rate", 0) for t in completed]) / len(
                completed
            )
            completion_rate = len(completed) / len(tasks) * 100

            context_parts.append("\nPRODUCTIVITY METRICS:")
            context_parts.append(f"- Completion rate: {completion_rate:.1f}%")
            context_parts.append(f"- Average focus rate: {avg_focus:.1f}/10")

    return "\n".join(context_parts)


def _get_task_vector_insights_from_tasks(tasks: List[Task]) -> dict:
    """Helper to get task insights from task list."""
    insights = {
        "total_tasks": len(tasks),
        "category_distribution": {},
        "priority_distribution": {},
        "time_allocation": {},
    }

    for task in tasks:
        category = (
            task.category.value
            if hasattr(task.category, "value")
            else str(task.category)
        )
        insights["category_distribution"][category] = (
            insights["category_distribution"].get(category, 0) + 1
        )

    for task in tasks:
        priority = task.priority or 5
        priority_level = (
            "high" if priority >= 8 else "medium" if priority >= 5 else "low"
        )
        insights["priority_distribution"][priority_level] = (
            insights["priority_distribution"].get(priority_level, 0) + 1
        )

    total_hours = sum(task.time_hours for task in tasks)
    insights["time_allocation"]["total_hours"] = total_hours
    insights["time_allocation"]["average_per_task"] = total_hours / max(len(tasks), 1)

    return insights


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
