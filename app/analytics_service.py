"""
Analytics Service
-----------------
A service responsible for data analytics using LLM models to:
1. Group tasks by likeness/similarity
2. Generate optimal schedules
3. Allocate time slots for the week
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re
from motor.motor_asyncio import AsyncIOMotorDatabase

from models import Task, AIRecommendation, ScheduleBlock
from llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class TaskAnalyticsService:
    """Service for analyzing tasks and generating intelligent schedules using LLM"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None, db: Optional[AsyncIOMotorDatabase] = None):
        self.llm_provider = llm_provider
        self.db = db
    
    async def generate_task_embeddings(self, tasks: List[Task]) -> Dict[int, List[float]]:
        """
        Generate vector embeddings for tasks to represent their semantic meaning.
        Uses LLM provider's embedding capabilities or creates simple embeddings.
        
        Returns:
            Dictionary mapping task_id to embedding vector
        """
        embeddings = {}
        
        if not tasks:
            return embeddings
        
        # Try to use OpenAI embeddings if available
        if self.llm_provider and hasattr(self.llm_provider, 'client'):
            try:
                # Check if it's OpenAI provider
                if hasattr(self.llm_provider.client, 'embeddings'):
                    for task in tasks:
                        text = f"{task.title} {task.goal} {task.category}"
                        response = await self.llm_provider.client.embeddings.create(
                            model="text-embedding-3-small",
                            input=text
                        )
                        embeddings[task.id] = response.data[0].embedding
                        logger.info(f"Generated embedding for task {task.id}")
                    return embeddings
            except Exception as e:
                logger.warning(f"Could not generate LLM embeddings: {e}")
        
        # Fallback: simple TF-IDF-like embeddings
        logger.info("Using simple embedding fallback")
        for task in tasks:
            # Create a simple feature vector based on task attributes
            embedding = self._create_simple_embedding(task)
            embeddings[task.id] = embedding
        
        return embeddings
    
    def _create_simple_embedding(self, task: Task) -> List[float]:
        """
        Create a simple embedding vector for a task based on its attributes.
        Returns a 384-dimensional vector (mimicking sentence transformers).
        """
        import hashlib
        
        # Combine task information
        text = f"{task.title} {task.goal} {task.category}".lower()
        
        # Create deterministic hash-based embedding
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to float vector (normalize between -1 and 1)
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if i + 1 < len(hash_bytes):
                val = (hash_bytes[i] * 256 + hash_bytes[i+1]) / 65535.0 * 2 - 1
                embedding.append(val)
        
        # Pad or truncate to 384 dimensions
        while len(embedding) < 384:
            embedding.extend(embedding[:min(384 - len(embedding), len(embedding))])
        embedding = embedding[:384]
        
        # Add categorical features
        category_features = {
            'research': [1.0, 0.0, 0.0, 0.0],
            'coding': [0.0, 1.0, 0.0, 0.0],
            'admin': [0.0, 0.0, 1.0, 0.0],
            'networking': [0.0, 0.0, 0.0, 1.0]
        }
        
        cat_vector = category_features.get(task.category, [0.25, 0.25, 0.25, 0.25])
        
        # Priority and time features (normalized)
        priority = getattr(task, 'priority', 5) / 10.0
        time_norm = min(task.time_hours / 10.0, 1.0)
        
        # Combine all features
        full_embedding = embedding[:378] + cat_vector + [priority, time_norm]
        
        return full_embedding
    
    async def group_tasks_by_similarity(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """
        Use LLM to group tasks by similarity based on title, category, and goal.
        Returns a dictionary where keys are group names and values are lists of tasks.
        """
        if not tasks:
            return {}
        
        if not self.llm_provider or not self.llm_provider.is_available():
            # Fallback: group by category only
            logger.warning("LLM provider not available, falling back to category-based grouping")
            return self._group_by_category(tasks)
        
        try:
            # Prepare task data for LLM
            task_data = []
            for task in tasks:
                task_data.append({
                    "id": task.id,
                    "title": task.title,
                    "category": task.category,
                    "goal": task.goal,
                    "time_hours": task.time_hours,
                    "priority": getattr(task, 'priority', 5)
                })
            
            prompt = f"""You are an expert task organizer. Analyze these tasks and group them by similarity based on their content, purpose, and context.

Tasks:
{json.dumps(task_data, indent=2)}

Group these tasks into logical clusters. Consider:
- Similar subject matter or domain
- Related skills or tools needed
- Sequential or dependent work
- Complementary activities that benefit from being done together

Return ONLY a valid JSON object in this exact format:
{{
  "groups": [
    {{
      "name": "Group Name",
      "description": "Why these tasks belong together",
      "task_ids": [1, 2, 3]
    }}
  ]
}}

Rules:
- Each task must appear in exactly one group
- Aim for 2-5 meaningful groups
- Group names should be clear and descriptive
- Every task_id in the input must appear in the output"""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt="You are a task organization expert. Always return valid JSON.",
                temperature=0.3,
                max_tokens=1500,
                json_mode=True
            )
            
            # Extract JSON from potential markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            result = json.loads(content)
            
            # Convert to our format
            grouped_tasks = {}
            task_dict = {task.id: task for task in tasks}
            
            for group in result.get("groups", []):
                group_name = group["name"]
                group_tasks = []
                
                for task_id in group.get("task_ids", []):
                    if task_id in task_dict:
                        group_tasks.append(task_dict[task_id])
                
                if group_tasks:
                    grouped_tasks[group_name] = group_tasks
                    logger.info(f"Created group '{group_name}' with {len(group_tasks)} tasks")
            
            # Ensure all tasks are included
            all_grouped_ids = set()
            for group_tasks in grouped_tasks.values():
                all_grouped_ids.update(t.id for t in group_tasks)
            
            missing_tasks = [t for t in tasks if t.id not in all_grouped_ids]
            if missing_tasks:
                grouped_tasks["Other"] = missing_tasks
                logger.warning(f"Added {len(missing_tasks)} ungrouped tasks to 'Other' group")
            
            return grouped_tasks
            
        except Exception as e:
            logger.error(f"Error grouping tasks with LLM: {e}")
            return self._group_by_category(tasks)
    
    def _group_by_category(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Fallback method to group tasks by category"""
        grouped = {}
        for task in tasks:
            category_name = task.category.capitalize()
            if category_name not in grouped:
                grouped[category_name] = []
            grouped[category_name].append(task)
        return grouped
    
    async def generate_intelligent_schedule(
        self,
        tasks: List[Task],
        week_start: datetime,
        daily_start: int = 9,
        daily_end: int = 17,
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate an intelligent schedule using LLM that considers:
        - Task grouping and similarity
        - Cognitive load and context switching
        - Energy levels throughout the day/week
        - Priority and deadlines
        - User preferences
        """
        if not tasks:
            return []
        
        if not self.llm_provider or not self.llm_provider.is_available():
            logger.warning("LLM provider not available, using rule-based scheduling")
            return self._rule_based_schedule(tasks, week_start, daily_start, daily_end)
        
        try:
            # First, group tasks by similarity
            grouped_tasks = await self.group_tasks_by_similarity(tasks)
            
            # Prepare scheduling context
            task_data = []
            for task in tasks:
                task_data.append({
                    "id": task.id,
                    "title": task.title,
                    "category": task.category,
                    "time_hours": task.time_hours,
                    "priority": getattr(task, 'priority', 5),
                    "due_date": getattr(task, 'due_date', None),
                    "goal": task.goal
                })
            
            group_info = []
            for group_name, group_tasks in grouped_tasks.items():
                group_info.append({
                    "name": group_name,
                    "task_ids": [t.id for t in group_tasks],
                    "total_hours": sum(t.time_hours for t in group_tasks)
                })
            
            prefs = preferences or {}
            peak_hours = prefs.get("peak_hours", "9-12")
            break_duration = prefs.get("break_duration_minutes", 15)
            max_continuous_hours = prefs.get("max_continuous_hours", 2)
            
            prompt = f"""You are an expert productivity coach and scheduler. Create an optimal weekly schedule for these tasks.

TASKS:
{json.dumps(task_data, indent=2)}

TASK GROUPS (similar tasks):
{json.dumps(group_info, indent=2)}

CONSTRAINTS:
- Week starts: {week_start.strftime('%Y-%m-%d %A')}
- Daily work hours: {daily_start}:00 to {daily_end}:00
- REST PERIOD: 12:00 AM (midnight) to 6:00 AM - NO TASKS ALLOWED (mandatory rest)
- Peak productivity hours: {peak_hours}
- Take {break_duration} min breaks every {max_continuous_hours} hours
- Total available hours per day: {daily_end - daily_start}

SCHEDULING PRINCIPLES:
1. NEVER schedule tasks between 12:00 AM (midnight) and 6:00 AM - this is mandatory rest time
2. Group similar tasks together to minimize context switching
3. Schedule high-priority and cognitively demanding tasks during peak hours
4. Schedule similar tasks in consecutive blocks
5. Leave buffer time for unexpected delays
6. Consider task dependencies and deadlines
7. Balance workload across the week
8. Respect natural energy patterns (harder tasks early, lighter tasks later)

Return ONLY valid JSON in this format:
{{
  "schedule": [
    {{
      "task_id": 1,
      "day_of_week": "Monday",
      "start_hour": 9,
      "start_minute": 0,
      "duration_hours": 2.0,
      "reason": "Why this time slot"
    }}
  ],
  "scheduling_notes": "Brief explanation of the scheduling strategy"
}}

Requirements:
- All tasks must be scheduled
- Respect daily work hours
- Schedule similar tasks together
- No overlapping time slots"""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt="You are an expert scheduler. Always return valid JSON.",
                temperature=0.5,
                max_tokens=2500,
                json_mode=True
            )
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            result = json.loads(content)
            
            # Convert to detailed schedule format
            schedule = []
            task_dict = {task.id: task for task in tasks}
            
            for slot in result.get("schedule", []):
                task_id = slot["task_id"]
                if task_id not in task_dict:
                    continue
                
                task = task_dict[task_id]
                
                # Calculate actual datetime
                day_name = slot["day_of_week"]
                days_offset = self._get_day_offset(day_name, week_start)
                slot_date = week_start + timedelta(days=days_offset)
                
                start_time = slot_date.replace(
                    hour=slot["start_hour"],
                    minute=slot.get("start_minute", 0),
                    second=0,
                    microsecond=0
                )
                end_time = start_time + timedelta(hours=slot["duration_hours"])
                
                # Validate: skip tasks scheduled during rest period (12am-6am)
                start_hour = start_time.hour + start_time.minute / 60
                end_hour = end_time.hour + end_time.minute / 60
                if (start_hour < 6 and start_hour >= 0) or (end_hour > 0 and end_hour <= 6):
                    logger.warning(f"Skipping task {task_id} scheduled during rest period (12am-6am)")
                    continue
                
                schedule.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "category": task.category,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_hours": slot["duration_hours"],
                    "scheduling_reason": slot.get("reason", "")
                })
            
            logger.info(f"Generated AI-powered schedule with {len(schedule)} blocks")
            logger.info(f"Scheduling notes: {result.get('scheduling_notes', '')}")
            
            # Validate schedule and fill gaps if needed
            schedule = self._validate_and_complete_schedule(
                schedule, tasks, week_start, daily_start, daily_end
            )
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error generating AI schedule: {e}")
            return self._rule_based_schedule(tasks, week_start, daily_start, daily_end)
    
    def _get_day_offset(self, day_name: str, week_start: datetime) -> int:
        """Get day offset from week start"""
        days = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        return days.get(day_name.lower(), 0)
    
    def _validate_and_complete_schedule(
        self,
        schedule: List[Dict],
        all_tasks: List[Task],
        week_start: datetime,
        daily_start: int,
        daily_end: int
    ) -> List[Dict]:
        """Ensure all tasks are scheduled and no overlaps exist"""
        scheduled_ids = {s["task_id"] for s in schedule}
        missing_tasks = [t for t in all_tasks if t.id not in scheduled_ids]
        
        if missing_tasks:
            logger.warning(f"Scheduling {len(missing_tasks)} missing tasks")
            # Use rule-based scheduling for missing tasks
            additional = self._rule_based_schedule(
                missing_tasks, week_start, daily_start, daily_end
            )
            schedule.extend(additional)
        
        return schedule
    
    def _rule_based_schedule(
        self,
        tasks: List[Task],
        week_start: datetime,
        daily_start: int = 9,
        daily_end: int = 17
    ) -> List[Dict[str, Any]]:
        """Rule-based scheduling algorithm (fallback)"""
        if not tasks:
            return []
        
        # Sort by category, priority, duration
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                t.category,
                -(getattr(t, 'priority', 5)),
                -t.time_hours
            )
        )
        
        schedule = []
        cursor = week_start.replace(hour=daily_start, minute=0, second=0, microsecond=0)
        
        for task in sorted_tasks:
            remaining = task.time_hours
            
            while remaining > 0:
                current_hour = cursor.hour + cursor.minute / 60
                
                # Skip rest period (12am-6am)
                if 0 <= current_hour < 6:
                    cursor = cursor.replace(hour=6, minute=0, second=0, microsecond=0)
                    continue
                
                # Skip weekends
                if cursor.weekday() >= 5:
                    cursor = cursor.replace(hour=daily_start, minute=0, second=0, microsecond=0)
                    cursor += timedelta(days=1)
                    continue
                
                # Move to next day if past working hours
                if current_hour >= daily_end:
                    # Move to next day at 6am (after rest period)
                    cursor = cursor.replace(hour=6, minute=0, second=0, microsecond=0)
                    cursor += timedelta(days=1)
                    continue
                
                # Calculate available time (but not into rest period if we're in evening)
                available = daily_end - current_hour
                
                # If scheduling in evening, ensure we don't go past midnight into rest period
                if current_hour >= 18:  # After 6pm
                    time_until_midnight = 24 - current_hour
                    available = min(available, time_until_midnight)
                
                block_duration = min(available, remaining, 2.0)  # Max 2-hour blocks
                
                block_end = cursor + timedelta(hours=block_duration)
                
                # Double-check we're not extending into rest period
                if block_end.hour < 6 and cursor.hour >= 18:
                    # Adjust to end at midnight
                    block_duration = (24 - current_hour)
                    block_end = cursor.replace(hour=23, minute=59, second=59, microsecond=0)
                
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
    
    async def analyze_task_patterns(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Analyze patterns in tasks to provide insights:
        - Most common categories
        - Average task duration
        - Priority distribution
        - Workload trends
        """
        if not tasks:
            return {
                "total_tasks": 0,
                "total_hours": 0,
                "analysis": "No tasks to analyze"
            }
        
        # Basic statistics
        total_hours = sum(t.time_hours for t in tasks)
        avg_hours = total_hours / len(tasks)
        
        # Category distribution
        category_counts = {}
        category_hours = {}
        for task in tasks:
            cat = task.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
            category_hours[cat] = category_hours.get(cat, 0) + task.time_hours
        
        # Priority distribution
        priorities = [getattr(t, 'priority', 5) for t in tasks]
        avg_priority = sum(priorities) / len(priorities) if priorities else 5
        
        analysis = {
            "total_tasks": len(tasks),
            "total_hours": round(total_hours, 2),
            "average_task_duration": round(avg_hours, 2),
            "average_priority": round(avg_priority, 2),
            "category_distribution": {
                cat: {
                    "count": category_counts.get(cat, 0),
                    "total_hours": round(category_hours.get(cat, 0), 2)
                }
                for cat in category_counts.keys()
            },
            "most_common_category": max(category_counts, key=category_counts.get) if category_counts else None,
        }
        
        # Use LLM for deeper insights if available
        if self.llm_provider and self.llm_provider.is_available():
            try:
                insights = await self._generate_insights(tasks, analysis)
                analysis["ai_insights"] = insights
            except Exception as e:
                logger.error(f"Error generating AI insights: {e}")
        
        return analysis
    
    async def _generate_insights(self, tasks: List[Task], basic_stats: Dict) -> str:
        """Generate AI-powered insights about task patterns"""
        try:
            task_summary = [
                f"{t.title} ({t.category}, {t.time_hours}h, priority {getattr(t, 'priority', 5)})"
                for t in tasks[:20]  # Limit to first 20 for context
            ]
            
            prompt = f"""Analyze these productivity patterns and provide 3-5 key insights and recommendations:

STATISTICS:
{json.dumps(basic_stats, indent=2)}

SAMPLE TASKS:
{chr(10).join(task_summary)}

Provide insights about:
- Workload balance and distribution
- Potential scheduling optimizations
- Risk areas (overcommitment, context switching, etc.)
- Productivity patterns
- Actionable recommendations

Keep insights concise and actionable (2-3 sentences each)."""

            return await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=600
            )
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return "Unable to generate AI insights at this time."
    
    def calculate_cognitive_tax(self, schedule: List[Dict]) -> Dict[str, Any]:
        """
        Calculate cognitive tax metrics for a schedule:
        - Context switches (category changes)
        - Average block duration
        - Fragmentation score
        """
        if not schedule:
            return {
                "cognitive_tax_score": 0.0,
                "context_switches": 0,
                "average_block_duration": 0.0,
                "fragmentation_score": 0.0
            }
        
        # Count context switches
        switches = 0
        for i in range(1, len(schedule)):
            if schedule[i]["category"] != schedule[i-1]["category"]:
                switches += 1
        
        # Calculate average block duration
        durations = [s["duration_hours"] for s in schedule]
        avg_duration = sum(durations) / len(durations)
        
        # Fragmentation score (lower is better)
        # Based on number of small blocks (< 1 hour)
        small_blocks = sum(1 for d in durations if d < 1.0)
        fragmentation = small_blocks / len(schedule)
        
        # Overall cognitive tax (normalized 0-1, lower is better)
        switch_penalty = switches / len(schedule)
        duration_bonus = max(0, 1 - (avg_duration / 2.0))  # Longer blocks are better
        cognitive_tax = (switch_penalty * 0.6 + fragmentation * 0.2 + duration_bonus * 0.2)
        
        return {
            "cognitive_tax_score": round(cognitive_tax, 3),
            "context_switches": switches,
            "average_block_duration": round(avg_duration, 2),
            "fragmentation_score": round(fragmentation, 3),
            "interpretation": self._interpret_cognitive_tax(cognitive_tax)
        }
    
    def _interpret_cognitive_tax(self, score: float) -> str:
        """Provide human-readable interpretation of cognitive tax score"""
        if score < 0.3:
            return "Excellent - Very low context switching and good focus blocks"
        elif score < 0.5:
            return "Good - Moderate context switching with decent focus time"
        elif score < 0.7:
            return "Fair - Significant context switching, consider regrouping tasks"
        else:
            return "Poor - High context switching and fragmentation, needs optimization"
    
    async def create_calendar_events_from_schedule(
        self,
        schedule: List[Dict[str, Any]],
        calendar_service,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """
        Create actual Google Calendar events from a schedule.
        
        Args:
            schedule: List of schedule blocks
            calendar_service: CalendarService instance with user's access token
            calendar_id: Target calendar ID
            
        Returns:
            List of created calendar events with their IDs
        """
        created_events = []
        
        for block in schedule:
            try:
                # Parse datetime
                start_time = datetime.fromisoformat(block['start_time'])
                end_time = datetime.fromisoformat(block['end_time'])
                
                # Create event description
                description = f"""Task: {block['task_title']}
Category: {block['category']}
Duration: {block['duration_hours']:.1f} hours

Scheduled by PolyLearner AI"""
                
                if 'scheduling_reason' in block and block['scheduling_reason']:
                    description += f"\n\nScheduling Reason: {block['scheduling_reason']}"
                
                # Create the calendar event
                event = await calendar_service.create_event(
                    summary=f"📚 {block['task_title']}",
                    start_time=start_time,
                    end_time=end_time,
                    description=description,
                    calendar_id=calendar_id
                )
                
                created_events.append({
                    'task_id': block['task_id'],
                    'event_id': event['id'],
                    'event_link': event.get('htmlLink', ''),
                    'start_time': block['start_time'],
                    'end_time': block['end_time']
                })
                
                logger.info(f"Created calendar event for task {block['task_id']}: {event['id']}")
                
            except Exception as e:
                logger.error(f"Failed to create calendar event for task {block.get('task_id')}: {e}")
                created_events.append({
                    'task_id': block.get('task_id'),
                    'error': str(e)
                })
        
        return created_events
    
    async def natural_language_query(self, question: str) -> Dict[str, Any]:
        """
        Convert natural language questions to MongoDB queries and execute them.
        Returns insights based on actual database data.
        
        Examples:
        - "How many coding tasks do I have?"
        - "What's the average time spent on research tasks?"
        - "Show me high priority tasks this week"
        - "Which category takes the most time?"
        """
        if not self.db:
            return {
                "error": "Database connection not available",
                "question": question
            }
        
        if not self.llm_provider or not self.llm_provider.is_available():
            logger.warning("LLM provider not available for NL query")
            return await self._basic_query_handler(question)
        
        try:
            # Use LLM to convert natural language to MongoDB query
            schema_info = """
Database Schema:
- Collection: tasks
  Fields:
    - id (int): Unique task identifier
    - title (string): Task name
    - category (string): Task category (research, coding, admin, networking)
    - time_hours (float): Estimated time in hours
    - goal (string): Task objective
    - artifact (string): Expected output (article, notes, code)
    - priority (int): 1-10, higher is more important
    - due_date (string): Optional deadline
    - weekly_goal_id (int): Optional link to weekly goal
    - review (object): Optional review data with focus_rate, notes, done_on_time

- Collection: weekly_goals
  Fields:
    - id (int): Unique goal identifier
    - week_number (int): Week of the year (1-53)
    - goal (string): Weekly objective
    - task_ids (array): List of task IDs
    - weekly_review (object): Optional review data

- Collection: users
  Fields:
    - id (int): User identifier
    - email (string): User email
    - name (string): User name
    - tokens_used (int): API tokens consumed
    - tokens_limit (int): Token usage limit
"""
            
            prompt = f"""You are a MongoDB query expert. Convert the natural language question to a MongoDB aggregation pipeline or find query.

Schema:
{schema_info}

Question: {question}

Return a JSON object with:
{{
  "collection": "collection_name",
  "operation": "find" | "aggregate" | "count",
  "query": {{...}},
  "pipeline": [...],  // only if operation is aggregate
  "explanation": "Brief explanation of what the query does"
}}

Important:
- Use proper MongoDB operators ($match, $group, $project, $sort, etc.)
- For aggregations, provide the full pipeline array
- For simple queries, use find operation
- Return ONLY valid JSON, no markdown"""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt="You are a MongoDB query expert. Always return valid JSON.",
                temperature=0.1,
                max_tokens=800,
                json_mode=True
            )
            
            # Extract JSON from markdown if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            query_info = json.loads(content)
            
            # Execute the MongoDB query
            collection_name = query_info.get("collection", "tasks")
            operation = query_info.get("operation", "find")
            collection = self.db[collection_name]
            
            result_data = None
            
            if operation == "aggregate":
                pipeline = query_info.get("pipeline", [])
                cursor = collection.aggregate(pipeline)
                result_data = await cursor.to_list(length=100)
            elif operation == "count":
                query = query_info.get("query", {})
                result_data = await collection.count_documents(query)
            else:  # find
                query = query_info.get("query", {})
                cursor = collection.find(query)
                result_data = await cursor.to_list(length=100)
                # Remove MongoDB _id field
                for doc in result_data:
                    doc.pop("_id", None)
            
            # Generate natural language answer from results
            answer = await self._generate_nl_answer(question, query_info, result_data)
            
            logger.info(f"Executed NL query: {question} -> {operation} on {collection_name}")
            
            return {
                "question": question,
                "answer": answer,
                "query_explanation": query_info.get("explanation", ""),
                "collection": collection_name,
                "operation": operation,
                "result_count": len(result_data) if isinstance(result_data, list) else result_data,
                "data": result_data if isinstance(result_data, list) and len(result_data) <= 20 else None
            }
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {e}")
            return {
                "error": str(e),
                "question": question,
                "fallback": await self._basic_query_handler(question)
            }
    
    async def _generate_nl_answer(self, question: str, query_info: Dict, result_data: Any) -> str:
        """Generate natural language answer from query results using LLM"""
        try:
            if not self.llm_provider or not self.llm_provider.is_available():
                return f"Query executed successfully. Found {len(result_data) if isinstance(result_data, list) else result_data} results."
            
            # Prepare result summary
            if isinstance(result_data, list):
                if len(result_data) == 0:
                    data_summary = "No results found."
                elif len(result_data) <= 10:
                    data_summary = json.dumps(result_data, indent=2, default=str)
                else:
                    data_summary = f"Found {len(result_data)} results. First 5: {json.dumps(result_data[:5], indent=2, default=str)}"
            else:
                data_summary = str(result_data)
            
            prompt = f"""Question: {question}

Query executed: {query_info.get('explanation', '')}

Results:
{data_summary}

Provide a clear, concise answer to the question based on these results. Be specific with numbers and details.
If the data is empty, explain that no matching records were found.
Keep the answer to 2-3 sentences."""

            return await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200
            )
            
        except Exception as e:
            logger.error(f"Error generating NL answer: {e}")
            return f"Query executed. Found {len(result_data) if isinstance(result_data, list) else result_data} results."
    
    async def _basic_query_handler(self, question: str) -> Dict[str, Any]:
        """Fallback query handler without LLM"""
        if not self.db:
            return {"error": "Database not available"}
        
        question_lower = question.lower()
        
        try:
            # Simple keyword-based query routing
            if "how many" in question_lower and "task" in question_lower:
                count = await self.db.tasks.count_documents({})
                return {"answer": f"You have {count} tasks in total.", "count": count}
            
            elif "coding" in question_lower:
                cursor = self.db.tasks.find({"category": "coding"})
                tasks = await cursor.to_list(length=100)
                return {
                    "answer": f"Found {len(tasks)} coding tasks.",
                    "count": len(tasks),
                    "tasks": [t.get("title") for t in tasks[:10]]
                }
            
            elif "research" in question_lower:
                cursor = self.db.tasks.find({"category": "research"})
                tasks = await cursor.to_list(length=100)
                return {
                    "answer": f"Found {len(tasks)} research tasks.",
                    "count": len(tasks),
                    "tasks": [t.get("title") for t in tasks[:10]]
                }
            
            elif "priority" in question_lower or "important" in question_lower:
                cursor = self.db.tasks.find({"priority": {"$gte": 7}}).sort("priority", -1)
                tasks = await cursor.to_list(length=20)
                return {
                    "answer": f"Found {len(tasks)} high-priority tasks (priority >= 7).",
                    "count": len(tasks),
                    "tasks": [{"title": t.get("title"), "priority": t.get("priority")} for t in tasks[:10]]
                }
            
            else:
                # Default: return task summary
                total = await self.db.tasks.count_documents({})
                pipeline = [
                    {"$group": {
                        "_id": "$category",
                        "count": {"$sum": 1},
                        "total_hours": {"$sum": "$time_hours"}
                    }}
                ]
                cursor = self.db.tasks.aggregate(pipeline)
                categories = await cursor.to_list(length=10)
                
                return {
                    "answer": f"You have {total} tasks across {len(categories)} categories.",
                    "total_tasks": total,
                    "categories": categories
                }
        
        except Exception as e:
            logger.error(f"Error in basic query handler: {e}")
            return {"error": str(e)}
    
    async def get_database_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive insights from the MongoDB database.
        Provides statistics and patterns from actual data.
        """
        if not self.db:
            return {"error": "Database connection not available"}
        
        try:
            insights = {}
            
            # Task statistics
            total_tasks = await self.db.tasks.count_documents({})
            insights["total_tasks"] = total_tasks
            
            # Tasks by category
            category_pipeline = [
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "total_hours": {"$sum": "$time_hours"},
                    "avg_priority": {"$avg": "$priority"}
                }},
                {"$sort": {"count": -1}}
            ]
            categories = await self.db.tasks.aggregate(category_pipeline).to_list(length=10)
            insights["categories"] = categories
            
            # Priority distribution
            priority_pipeline = [
                {"$group": {
                    "_id": "$priority",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]
            priorities = await self.db.tasks.aggregate(priority_pipeline).to_list(length=10)
            insights["priority_distribution"] = priorities
            
            # Tasks with reviews
            reviewed_tasks = await self.db.tasks.count_documents({"review": {"$exists": True}})
            insights["reviewed_tasks"] = reviewed_tasks
            insights["review_rate"] = round(reviewed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
            
            # Average focus rate from reviews
            focus_pipeline = [
                {"$match": {"review.focus_rate": {"$exists": True}}},
                {"$group": {
                    "_id": None,
                    "avg_focus_rate": {"$avg": "$review.focus_rate"},
                    "count": {"$sum": 1}
                }}
            ]
            focus_results = await self.db.tasks.aggregate(focus_pipeline).to_list(length=1)
            if focus_results:
                insights["average_focus_rate"] = round(focus_results[0]["avg_focus_rate"], 1)
            
            # Weekly goals
            total_goals = await self.db.weekly_goals.count_documents({})
            insights["total_weekly_goals"] = total_goals
            
            # Recent activity (tasks created in last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            # Note: This assumes tasks have a created_at field, adjust if needed
            
            # Time allocation by category
            time_pipeline = [
                {"$group": {
                    "_id": "$category",
                    "total_hours": {"$sum": "$time_hours"}
                }},
                {"$sort": {"total_hours": -1}}
            ]
            time_by_category = await self.db.tasks.aggregate(time_pipeline).to_list(length=10)
            insights["time_allocation"] = time_by_category
            
            # Generate AI insights if available
            if self.llm_provider and self.llm_provider.is_available():
                ai_summary = await self._generate_database_insights_summary(insights)
                insights["ai_summary"] = ai_summary
            
            logger.info("Generated database insights from MongoDB")
            return insights
            
        except Exception as e:
            logger.error(f"Error getting database insights: {e}")
            return {"error": str(e)}
    
    async def _generate_database_insights_summary(self, insights: Dict) -> str:
        """Generate AI-powered summary of database insights"""
        try:
            prompt = f"""Analyze this productivity data and provide 3-4 key insights and actionable recommendations:

Data Summary:
{json.dumps(insights, indent=2, default=str)}

Provide insights about:
- Workload balance across categories
- Productivity patterns (focus rates, review completion)
- Time allocation efficiency
- Potential improvements or risks

Keep each insight to 1-2 sentences. Be specific and actionable."""

            return await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=400
            )
            
        except Exception as e:
            logger.error(f"Error generating insights summary: {e}")
            return "Unable to generate AI summary at this time."
