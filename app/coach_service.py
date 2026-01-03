"""
AI Goal Coach Service
Provides personalized coaching by reading user tasks, analyzing vector embeddings,
and offering insights based on task metadata and progress.
"""

from typing import List, Dict, Optional
from datetime import datetime
import json
from pydantic import BaseModel

class CoachMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime

class CoachingSession(BaseModel):
    id: str
    user_id: int
    title: str
    timestamp: datetime
    messages: List[Dict]

class CoachRequest(BaseModel):
    session_id: str
    message: str

class CoachResponse(BaseModel):
    response: str
    task_insights: Optional[Dict] = None

def get_user_task_context(user_id: int, db) -> str:
    """
    Retrieve user's tasks and create context for the coach.
    """
    from models import Task
    
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    
    if not tasks:
        return "The user has no tasks yet."
    
    # Separate completed and pending tasks
    completed_tasks = [t for t in tasks if t.review is not None]
    pending_tasks = [t for t in tasks if t.review is None]
    
    context_parts = []
    
    # Add overview
    context_parts.append(f"USER TASK OVERVIEW:")
    context_parts.append(f"- Total tasks: {len(tasks)}")
    context_parts.append(f"- Completed: {len(completed_tasks)}")
    context_parts.append(f"- Pending: {len(pending_tasks)}")
    
    # Add pending tasks details
    if pending_tasks:
        context_parts.append(f"\nPENDING TASKS:")
        for task in pending_tasks[:10]:  # Limit to 10 most recent
            task_info = [
                f"  • {task.title}",
                f"    Goal: {task.goal}",
                f"    Category: {task.category}",
                f"    Time estimate: {task.time_hours}h",
                f"    Priority: {task.priority or 5}/10"
            ]
            if task.due_date:
                task_info.append(f"    Due: {task.due_date}")
            context_parts.append("\n".join(task_info))
    
    # Add completed tasks summary
    if completed_tasks:
        context_parts.append(f"\nRECENTLY COMPLETED TASKS:")
        for task in completed_tasks[-5:]:  # Last 5 completed
            focus_rate = task.review.get('focus_rate', 'N/A') if task.review else 'N/A'
            context_parts.append(f"  • {task.title} (Focus: {focus_rate}/10)")
    
    # Calculate productivity metrics
    if tasks:
        avg_focus = sum([t.review.get('focus_rate', 0) for t in completed_tasks if t.review]) / max(len(completed_tasks), 1)
        completion_rate = len(completed_tasks) / len(tasks) * 100
        
        context_parts.append(f"\nPRODUCTIVITY METRICS:")
        context_parts.append(f"- Completion rate: {completion_rate:.1f}%")
        context_parts.append(f"- Average focus rate: {avg_focus:.1f}/10")
    
    return "\n".join(context_parts)

def get_task_vector_insights(user_id: int, db) -> Dict:
    """
    Analyze task embeddings and patterns to provide insights.
    This would integrate with your vector database for semantic analysis.
    """
    from models import Task
    
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    
    insights = {
        "total_tasks": len(tasks),
        "category_distribution": {},
        "priority_distribution": {},
        "time_allocation": {},
        "energy_patterns": []
    }
    
    # Analyze category distribution
    for task in tasks:
        category = task.category
        insights["category_distribution"][category] = insights["category_distribution"].get(category, 0) + 1
    
    # Analyze priority distribution
    for task in tasks:
        priority = task.priority or 5
        priority_level = "high" if priority >= 8 else "medium" if priority >= 5 else "low"
        insights["priority_distribution"][priority_level] = insights["priority_distribution"].get(priority_level, 0) + 1
    
    # Calculate total time allocation
    total_hours = sum(task.time_hours for task in tasks)
    insights["time_allocation"]["total_hours"] = total_hours
    insights["time_allocation"]["average_per_task"] = total_hours / max(len(tasks), 1)
    
    # Analyze patterns
    if tasks:
        # Find most common category
        most_common_category = max(insights["category_distribution"].items(), key=lambda x: x[1])[0]
        insights["patterns"] = {
            "dominant_category": most_common_category,
            "workload": "heavy" if total_hours > 40 else "moderate" if total_hours > 20 else "light"
        }
    
    return insights

def generate_coach_response(user_message: str, user_id: int, db, llm_provider) -> CoachResponse:
    """
    Generate AI coach response based on user message and task context.
    """
    # Get user's task context
    task_context = get_user_task_context(user_id, db)
    task_insights = get_task_vector_insights(user_id, db)
    
    # Create coaching prompt
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
- Total tasks: {task_insights['total_tasks']}
- Category distribution: {json.dumps(task_insights['category_distribution'])}
- Time allocation: {task_insights['time_allocation']['total_hours']}h total
- Workload: {task_insights.get('patterns', {}).get('workload', 'unknown')}

Be conversational, supportive, and specific. Reference their actual tasks and progress when relevant.
Keep responses concise but helpful (2-4 paragraphs max).
"""
    
    # Generate response using LLM
    try:
        response = llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_message,
            temperature=0.7,
            max_tokens=500
        )
        
        return CoachResponse(
            response=response,
            task_insights=task_insights
        )
    except Exception as e:
        # Fallback response if LLM fails
        fallback_response = """I'm here to help you with your goals! Based on your current tasks, 
I can see you're working on several important objectives. 

Let me know what specific aspect you'd like to discuss - whether it's staying motivated, 
prioritizing tasks, or overcoming challenges. I'm here to support you!"""
        
        return CoachResponse(
            response=fallback_response,
            task_insights=task_insights
        )

def create_session_summary(messages: List[Dict]) -> str:
    """
    Create a brief summary of the session for the session title.
    """
    if not messages:
        return "New Coaching Session"
    
    # Use the first user message or a generic title
    first_message = next((msg for msg in messages if msg['role'] == 'user'), None)
    if first_message:
        content = first_message['content'][:50]
        return f"Goal Coaching: {content}..." if len(first_message['content']) > 50 else f"Goal Coaching: {content}"
    
    return "Goal Coaching Session"
