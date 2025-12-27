from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import os
import sys
import jwt
from openai import OpenAI
from ics import Calendar, Event as ICSEvent
from ics.grammar.parse import ContentLine
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
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
    WeeklyGoalBase,
    WeeklyGoalCreate,
    WeeklyGoal,
    WeeklyReviewCreate,
    WeeklyReviewResponse,
    ReviewCreate,
    TaskReviewResponse,
    AIRecommendation,
    ScheduleBlock,
    WeekScheduleResponse,
    UserCreate,
    User,
    GoogleAuthRequest,
    AuthResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PolyLearner API",
    description="This is an API that uses the roles for polymath learning",
    version="1.0.0",
    docs_url="/",
    redoc_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment-specific config from .env file
APP_ENV = os.getenv("APP_ENV", "dev")
env_file = f"../.env.{APP_ENV}"
load_dotenv(env_file)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "polylearner")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

mongo_client: AsyncIOMotorClient | None = None
openai_client: OpenAI | None = None
security = HTTPBearer()


def get_db():
    if mongo_client is None:
        raise RuntimeError("Mongo client is not initialized")
    return mongo_client[MONGO_DB_NAME]


@app.on_event("startup")
async def startup_event():
    global mongo_client, openai_client
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("Application starting up and connected to MongoDB...")


@app.on_event("shutdown")
async def shutdown_event():
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()
    logger.info("Application shutting down and MongoDB client closed...")


def create_jwt_token(user_id: int, email: str) -> str:
    """Create JWT token for user"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify JWT token and validate Google session"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        db = get_db()
        user_doc = await db.users.find_one({"id": user_id})
        
        if user_doc is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if Google token is still valid
        if user_doc.get("google_token_expiry"):
            token_expiry = user_doc["google_token_expiry"]
            if datetime.now() > token_expiry:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google session has expired. Please sign in again."
                )
        
        user_doc.pop("_id", None)
        return User(**user_doc)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@app.get("/info")
async def root():
    logger.info("Info endpoint accessed")
    return {
        "message": "PolyLearner API - Basic FastAPI Application",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/auth/google", response_model=AuthResponse)
async def google_auth(auth_request: GoogleAuthRequest):
    """Authenticate user with Google OAuth"""
    try:
        # Get user info from Google using access token
        import httpx
        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {auth_request.access_token}'}
            )
        
        if user_info_response.status_code != 200:
            raise ValueError("Invalid access token")
        
        user_info = user_info_response.json()
        
        # Extract user info
        google_id = user_info['id']
        email = user_info['email']
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        db = get_db()
        
        # Calculate token expiry
        token_expiry = datetime.now() + timedelta(seconds=auth_request.expires_in)
        
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
                "created_at": datetime.now(),
                "tokens_used": 0,
                "tokens_limit": 100000,
                "google_access_token": auth_request.access_token,
                "google_token_expiry": token_expiry
            }
            
            await db.users.insert_one(user_doc)
            logger.info(f"Created new user with email {email}")
        else:
            # Update existing user's token and expiry
            await db.users.update_one(
                {"google_id": google_id},
                {"$set": {
                    "google_access_token": auth_request.access_token,
                    "google_token_expiry": token_expiry,
                    "name": name,
                    "picture": picture
                }}
            )
            user_doc = await db.users.find_one({"google_id": google_id})
        
        user_doc.pop("_id", None)
        user = User(**user_doc)
        
        # Create JWT token
        access_token = create_jwt_token(user.id, user.email)
        
        return AuthResponse(
            access_token=access_token,
            user=user
        )
    
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google credentials: {str(e)}"
        )


@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user


@app.patch("/users/tokens")
async def update_token_usage(tokens_used: int, current_user: User = Depends(get_current_user)):
    """Update user's token usage"""
    db = get_db()
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"tokens_used": tokens_used}}
    )
    
    logger.info(f"Updated token usage for user {current_user.id}: +{tokens_used}")
    return {"success": True, "tokens_used": current_user.tokens_used + tokens_used}


@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task with title, category, time in hours, goal, artifact, and optional review."""
    db = get_db()

    # Validate weekly_goal_id if provided
    if task.weekly_goal_id is not None:
        weekly_goal = await db.weekly_goals.find_one({"id": task.weekly_goal_id})
        if weekly_goal is None:
            raise HTTPException(status_code=404, detail="Weekly goal not found")

    # Generate next task id
    last_task = await db.tasks.find_one(sort=[("id", -1)])
    next_id = (last_task["id"] + 1) if last_task else 1

    task_doc = {"id": next_id, **task.model_dump()}
    await db.tasks.insert_one(task_doc)

    # If linked to a weekly goal, register this task under that goal
    if task.weekly_goal_id is not None:
        await db.weekly_goals.update_one(
            {"id": task.weekly_goal_id},
            {"$addToSet": {"task_ids": next_id}},
        )

    logger.info(f"Created task with ID {next_id} and title '{task.title}'")
    return Task(**task_doc)


@app.get("/tasks", response_model=List[Task])
async def list_tasks():
    """List all tasks."""
    logger.info("Listing all tasks")
    db = get_db()
    cursor = db.tasks.find()
    tasks: List[Task] = []
    async for doc in cursor:
        doc.pop("_id", None)
        tasks.append(Task(**doc))
    return tasks


@app.post("/weekly-goals", response_model=WeeklyGoal, status_code=201)
async def create_weekly_goal(goal: WeeklyGoalCreate):
    """Create a weekly goal for a given week number."""
    db = get_db()

    # Generate next weekly goal id
    last_goal = await db.weekly_goals.find_one(sort=[("id", -1)])
    next_id = (last_goal["id"] + 1) if last_goal else 1

    goal_doc = {
        "id": next_id,
        "week_number": goal.week_number,
        "goal": goal.goal,
        "task_ids": [],
        "weekly_review": None,
    }
    await db.weekly_goals.insert_one(goal_doc)

    logger.info(f"Created weekly goal id={next_id} for week {goal.week_number}")
    return WeeklyGoal(**goal_doc)


@app.get("/weekly-goals", response_model=List[WeeklyGoal])
async def list_weekly_goals():
    """List all weekly goals with their associated task ids and weekly review (if any)."""
    logger.info("Listing all weekly goals")
    db = get_db()
    cursor = db.weekly_goals.find()
    goals: List[WeeklyGoal] = []
    async for doc in cursor:
        doc.pop("_id", None)
        # Backward-compat: older documents may not have a goal text yet
        if "goal" not in doc:
            doc["goal"] = ""
        goals.append(WeeklyGoal(**doc))
    return goals


@app.post("/weekly-goals/review", response_model=WeeklyReviewResponse, status_code=201)
async def add_weekly_review(review: WeeklyReviewCreate):
    """Attach a weekly review to an existing weekly goal."""
    db = get_db()

    weekly_goal = await db.weekly_goals.find_one({"id": review.weekly_goal_id})
    if weekly_goal is None:
        raise HTTPException(status_code=404, detail="Weekly goal not found")

    review_data = Review(
        notes=review.notes,
        focus_rate=review.focus_rate,
        artifact=review.artifact,
        done_on_time=review.done_on_time,
    )

    await db.weekly_goals.update_one(
        {"id": review.weekly_goal_id},
        {"$set": {"weekly_review": review_data.model_dump()}},
    )

    # Also persist this weekly review as its own document
    await db.weekly_reviews.insert_one(
        {"weekly_goal_id": review.weekly_goal_id, **review_data.model_dump()}
    )

    logger.info(f"Added weekly review for weekly_goal_id={review.weekly_goal_id}")
    return WeeklyReviewResponse(weekly_goal_id=review.weekly_goal_id, **review_data.model_dump())


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
        if schedule[i]["category"] != schedule[i-1]["category"]:
            switches += 1
    
    # Lower score is better
    return switches / len(schedule) if len(schedule) > 0 else 0.0


def optimize_schedule(tasks: List[Task], week_start: datetime, daily_start: int = 9, daily_end: int = 17) -> List[dict]:
    """Optimize task scheduling to minimize cognitive tax"""
    if not tasks:
        return []
    
    # Sort by category (to group similar tasks), then priority, then duration
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            t.category,
            -(t.priority if hasattr(t, 'priority') and t.priority else 5),
            -t.time_hours
        )
    )
    
    schedule = []
    cursor = week_start.replace(hour=daily_start, minute=0, second=0, microsecond=0)
    
    for task in sorted_tasks:
        remaining = task.time_hours
        
        while remaining > 0:
            current_hour = cursor.hour + cursor.minute / 60
            
            # Move to next day if past working hours
            if current_hour >= daily_end:
                cursor = cursor.replace(hour=daily_start, minute=0, second=0, microsecond=0)
                cursor += timedelta(days=1)
                continue
            
            # Calculate available time today
            available = daily_end - current_hour
            block_duration = min(available, remaining)
            
            block_end = cursor + timedelta(hours=block_duration)
            
            schedule.append({
                "task_id": task.id,
                "task_title": task.title,
                "category": task.category,
                "start_time": cursor.isoformat(),
                "end_time": block_end.isoformat(),
                "duration_hours": block_duration,
            })
            
            cursor = block_end
            remaining -= block_duration
    
    return schedule


async def generate_ai_recommendations(tasks: List[Task]) -> List[AIRecommendation]:
    """Generate AI-powered recommendations for task scheduling"""
    if not openai_client or not tasks:
        return [
            AIRecommendation(
                suggestion="Group similar tasks together",
                reason="Minimize context switching to reduce cognitive load",
                priority=8
            ),
            AIRecommendation(
                suggestion="Schedule deep work in your peak hours",
                reason="High-priority coding and research tasks need focused attention",
                priority=9
            ),
            AIRecommendation(
                suggestion="Leave buffer time between task blocks",
                reason="Allow for breaks and unexpected delays",
                priority=7
            )
        ]
    
    try:
        # Prepare task summary for AI
        task_summary = []
        for t in tasks:
            task_summary.append(f"- {t.title} ({t.category}, {t.time_hours}h, priority: {getattr(t, 'priority', 5)})")
        
        prompt = f"""You are an AI productivity assistant. Analyze these tasks and provide 3 specific, actionable recommendations to optimize the weekly schedule and reduce cognitive tax:

Tasks:
{chr(10).join(task_summary)}

Provide recommendations in JSON format:
[{{"suggestion": "...", "reason": "...", "priority": 1-10}}]

Focus on:
1. Minimizing context switching between different task types
2. Optimal time blocks for deep work
3. Energy management throughout the week"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        # Try to parse JSON from response
        import json
        import re
        
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        recommendations_data = json.loads(content)
        recommendations = [AIRecommendation(**r) for r in recommendations_data[:3]]
        
        return recommendations
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {e}")
        return [
            AIRecommendation(
                suggestion="Group similar tasks together",
                reason="Minimize context switching to reduce cognitive load",
                priority=8
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
    week_start: Optional[str] = None,
    daily_start: int = 9,
    daily_end: int = 17
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
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
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
        cognitive_tax_score=cognitive_tax
    )


@app.get("/schedule/ics")
async def export_schedule_ics(
    week_start: Optional[str] = None,
    daily_start: int = 9,
    daily_end: int = 17
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
        week_start_dt = (now - timedelta(days=days_to_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Generate schedule
    schedule = optimize_schedule(tasks, week_start_dt, daily_start, daily_end)
    
    # Create ICS calendar
    cal = Calendar()
    
    for block in schedule:
        event = ICSEvent()
        event.name = block["task_title"]
        event.begin = datetime.fromisoformat(block["start_time"])
        event.end = datetime.fromisoformat(block["end_time"])
        event.description = f"Category: {block['category']}\nDuration: {block['duration_hours']:.1f}h"
        cal.events.add(event)
    
    from fastapi.responses import Response
    return Response(
        content=str(cal),
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=polylearner-schedule.ics"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
