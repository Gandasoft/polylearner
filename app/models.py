from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict

from pydantic import BaseModel, Field, EmailStr


# User models
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    google_id: str
    picture: Optional[str] = None


class User(UserCreate):
    id: int
    created_at: datetime = Field(default_factory=datetime.now)
    tokens_used: int = 0
    tokens_limit: int = 100000
    google_access_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None


class GoogleAuthRequest(BaseModel):
    access_token: str  # Google access token
    expires_in: int  # Token expiry in seconds


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    message: str
    timestamp: datetime


class TaskCategory(str, Enum):
    research = "research"
    coding = "coding"
    admin = "admin"
    networking = "networking"


class TaskArtifact(str, Enum):
    article = "article"
    notes = "notes"
    code = "code"


class DoneOnTime(str, Enum):
    yes = "yes"
    no = "no"


class Review(BaseModel):
    notes: str
    focus_rate: int = Field(..., ge=1, le=10)
    artifact: str 
    done_on_time: DoneOnTime


class TaskCreate(BaseModel):
    title: str
    category: TaskCategory
    time_hours: float
    goal_id: int  # Required - tasks must belong to a goal
    artifact: TaskArtifact
    review: Optional[Review] = None
    priority: Optional[int] = Field(default=5, ge=1, le=10)
    due_date: Optional[str] = None


class Task(TaskCreate):
    id: int
    goal: Optional[str] = None  # Denormalized for display, derived from goal_id


# Unified Goal Models
class GoalBase(BaseModel):
    goal: str
    timeframe: Optional[str] = None
    category: Optional[str] = None


class GoalCreate(GoalBase):
    pass


class Goal(GoalBase):
    id: int
    user_id: int
    is_validated: bool = False
    validation_feedback: Optional[str] = None
    created_at: datetime
    tasks_generated: bool = False
    task_ids: List[int] = []


class GoalReviewCreate(Review):
    goal_id: int


class GoalReviewResponse(Review):
    goal_id: int


class ReviewCreate(Review):
    task_id: int


class TaskReviewResponse(Review):
    task_id: int


class AIRecommendation(BaseModel):
    suggestion: str
    reason: str
    priority: int = Field(..., ge=1, le=10)


class ScheduleBlock(BaseModel):
    task_id: int
    task_title: str
    category: str
    start_time: str
    end_time: str
    duration_hours: float
    scheduling_reason: Optional[str] = None
    embedding_sample: Optional[List[float]] = None


class WeekScheduleResponse(BaseModel):
    week_start: str
    schedule: List[ScheduleBlock]
    recommendations: List[AIRecommendation]
    total_hours: float
    cognitive_tax_score: float
    embeddings_generated: Optional[int] = None


# Goal Validation Models
class GoalSubmission(BaseModel):
    goal: str
    goal_id: Optional[int] = None  # If provided, updates existing goal instead of creating new one
    # Note: timeframe, hours, and energy preferences are inferred from weekly feedback analysis


class GoalValidationResponse(BaseModel):
    goal_id: int  # ID of the created/updated goal
    is_valid: bool
    validation_details: Dict[str, bool]
    feedback: str
    suggestions: List[str]
    refined_versions: List[Dict[str, str]]  # List of refined goal options


class SuggestedTask(BaseModel):
    title: str
    category: TaskCategory
    time_hours: float
    goal: str
    artifact: TaskArtifact
    priority: int = Field(..., ge=1, le=10)
    energy_level: str  # "high", "medium", "low"
    batch_group: str
    dependencies: List[str] = []


class TaskSuggestionResponse(BaseModel):
    goal_id: int  # ID of the saved goal
    suggested_tasks: List[SuggestedTask]
    scheduling_strategy: str
    estimated_total_hours: Optional[float] = 0.0
    energy_allocation: Optional[Dict[str, float]] = None
    batching_recommendations: Optional[str] = None
    weekly_breakdown: Optional[str] = None


class CreateTasksFromSuggestionsRequest(BaseModel):
    suggested_tasks: List[SuggestedTask]
    goal_id: Optional[int] = None



