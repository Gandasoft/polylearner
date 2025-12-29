# Goal-Based Onboarding Workflow

## Overview

The PolyLearner application now includes an **intelligent goal-based onboarding workflow** powered by LLM. This workflow ensures users set SMART goals and receive AI-generated task suggestions based on proven productivity principles.

## Productivity Guidelines Integration

The system follows these core principles from productivity science:

### 1. **Proactive Mindset**
- Goals reflect ownership and intentionality
- View challenges as opportunities
- Create conditions rather than wait for them

### 2. **Clear Intentions (SMART Goals)**
- **Specific**: Clearly defined, not ambiguous
- **Measurable**: Quantifiable metrics or clear qualitative indicators
- **Achievable**: Realistic given constraints
- **Relevant**: Aligned with bigger picture
- **Time-bound**: Has deadline or timeframe

### 3. **Prioritization (Eisenhower Matrix)**
- Focus on important tasks over urgent ones
- Apply 80/20 rule: 20% of tasks drive 80% of results

### 4. **Energy Management**
- Circadian rhythm: 24-hour cycle of alertness
- Ultradian rhythm: 90-120 min high focus, 20-30 min rest
- High-energy tasks for complex/creative work
- Low-energy tasks for routine/administrative work
- **Mandatory rest: 12am-6am (6 hours)**

### 5. **Task Batching**
- Group similar tasks to minimize cognitive switching cost
- Batch by mental effort and task type

### 6. **Time Blocking**
- Allocate specific time slots to tasks
- Leave buffer time for unforeseen events
- Balance work, rest, and personal activities

## Onboarding Flow

### Step 1: User Submits Goal

**Endpoint**: `POST /onboarding/validate-goal`

```json
{
  "goal": "Master Python web development and build 3 production applications",
  "timeframe": "next 3 months",
  "available_hours_per_week": 20,
  "peak_energy_time": "morning"
}
```

### Step 2: LLM Analyzes and Refines Goal

The system analyzes the goal and **always provides refinement suggestions** - it never outright rejects:

#### 📊 **Analysis with Refinements**
```json
{
  "goal": "Learn programming",
  "analysis": {
    "is_valid": false,
    "validation_details": {
      "specific": false,
      "measurable": false,
      "achievable": true,
      "relevant": true,
      "time_bound": false
    },
    "feedback": "Your goal shows interest in programming, but could be more specific. Here are refined versions that add measurability and clarity.",
    "suggestions": [
      "Specify which programming language",
      "Define measurable outcomes (complete a course, build projects)",
      "Set a clear deadline"
    ],
    "refined_versions": [
      {
        "goal": "Complete Python fundamentals course (30 hours) by end of February",
        "improvement": "Added specific language, measurable hours, and deadline",
        "why_better": "Clear outcome with quantifiable progress"
      },
      {
        "goal": "Learn Python basics and build 3 beginner projects (calculator, to-do app, web scraper) within 8 weeks",
        "improvement": "Includes concrete deliverables and realistic timeframe",
        "why_better": "Measurable through completed projects, shows practical application"
      },
      {
        "goal": "Master Python fundamentals through 40-hour online course, complete 20 practice exercises, and build portfolio project by March 15th",
        "improvement": "Most structured with multiple measurable milestones",
        "why_better": "Combines learning, practice, and application with clear metrics"
      }
    ]
  }
}
```

**Key Point**: Users can:
- Proceed with their original goal
- Choose any of the 3 refined versions
- Edit any version before proceeding
- Always move forward - never blocked

### Step 3: Generate Task Suggestions

**Endpoint**: `POST /onboarding/suggest-tasks`

Once goal is validated, the LLM generates task suggestions following productivity principles:

```json
{
  "suggested_tasks": [
    {
      "title": "Complete Python basics modules 1-5",
      "category": "research",
      "time_hours": 8.0,
      "goal": "Build foundation in Python syntax and concepts",
      "artifact": "notes",
      "priority": 9,
      "energy_level": "high",
      "batch_group": "Learning",
      "dependencies": []
    },
    {
      "title": "Build calculator CLI application",
      "category": "coding",
      "time_hours": 4.0,
      "goal": "Apply basic Python concepts in real project",
      "artifact": "code",
      "priority": 8,
      "energy_level": "high",
      "batch_group": "Hands-on Practice",
      "dependencies": ["Complete Python basics modules 1-5"]
    },
    {
      "title": "Study Flask web framework documentation",
      "category": "research",
      "time_hours": 3.0,
      "goal": "Understand web development basics with Flask",
      "artifact": "notes",
      "priority": 7,
      "energy_level": "medium",
      "batch_group": "Learning",
      "dependencies": ["Complete Python basics modules 1-5"]
    }
  ],
  "scheduling_strategy": "Front-load learning tasks in morning high-energy blocks. Batch coding practice sessions together. Schedule research/reading in medium-energy afternoon slots.",
  "estimated_total_hours": 15.0,
  "energy_allocation": {
    "high_energy_hours": 12.0,
    "medium_energy_hours": 3.0,
    "low_energy_hours": 0.0
  },
  "batching_recommendations": "Batch all learning modules together (8 hours). Separate coding practice into 2-hour focused blocks. Group documentation reading with note-taking.",
  "weekly_breakdown": "Week 1: Complete modules 1-5 (8h). Week 2: Build calculator (4h) + Flask docs (3h)."
}
```

### Step 4: User Accepts/Modifies Tasks

**Endpoint**: `POST /onboarding/create-tasks-from-suggestions`

User can:
- Accept all suggested tasks
- Select specific tasks
- Modify tasks before creation

```json
{
  "suggested_tasks": [/* selected tasks */],
  "goal_id": 1
}
```

**Response**:
```json
{
  "created_task_ids": [1, 2, 3],
  "count": 3,
  "message": "Successfully created 3 tasks"
}
```

### Step 5: View Onboarding Goals

**Endpoint**: `GET /onboarding/goals`

Returns all onboarding goals for the user:

```json
[
  {
    "id": 1,
    "user_id": 123,
    "goal": "Complete Python fundamentals course and build 3 projects by end of February",
    "timeframe": "next 3 months",
    "is_validated": true,
    "validation_feedback": "Excellent SMART goal!",
    "created_at": "2025-12-28T10:30:00",
    "tasks_generated": true
  }
]
```

## LLM Validation Rules

The LLM analyzes goals and **always provides helpful refinements** (never blocks progress):

### 🎯 How Analysis Works:

1. **Evaluate against SMART criteria**: Checks specificity, measurability, achievability, relevance, time-bound
2. **Provide constructive feedback**: Explains what's good and what could be improved
3. **Generate 3 refined versions**: Progressively better alternatives
4. **Allow user choice**: User can proceed with original or choose refined version

### 📋 Refinement Levels:

**Version 1**: Basic improvements (add deadline, specify outcome)
**Version 2**: Moderate refinement (add milestones, concrete deliverables)
**Version 3**: Comprehensive (multiple metrics, structured approach)

### Examples of Refinements:

| User Input | Refined Versions |
|------------|------------------|
| "Learn React" | 1. "Complete React fundamentals course (20 hours) by Feb 15"<br>2. "Learn React and build 2 projects (todo app, weather app) in 6 weeks"<br>3. "Master React through 30-hour course, 10 exercises, and 3 portfolio projects by March 1" |
| "Get better at coding" | 1. "Complete 50 coding challenges on LeetCode by end of January"<br>2. "Improve coding skills by solving 3 problems daily and building 1 project per week for 8 weeks"<br>3. "Master algorithmic thinking through 100 LeetCode problems (easy/medium), 5 system design exercises, and 2 full-stack projects by Feb 28" |
| "Study machine learning" | 1. "Complete introductory ML course (30 hours) by March 1"<br>2. "Learn ML fundamentals and implement 5 classic algorithms (linear regression, decision trees, etc.) in 10 weeks"<br>3. "Master ML basics through Andrew Ng's course, complete 20 exercises, build 3 projects (classification, regression, clustering) by March 15" |

### ✨ Key Benefits:

- **No Rejection**: Users never get blocked - they always have options
- **Learning Tool**: Shows users what SMART goals look like
- **Flexibility**: Can proceed with original or refined version
- **Progressive Improvement**: Three levels of refinement to choose from

## Task Generation Principles

The LLM applies these principles when generating tasks:

### 1. **80/20 Rule**
- Identify the 20% of tasks that will drive 80% of results
- Prioritize high-impact activities

### 2. **Task Batching**
- Group similar tasks together
- Minimize context switching cost
- Examples: "Learning" batch, "Coding Practice" batch, "Admin" batch

### 3. **Energy Allocation**
- **High energy**: Complex problem-solving, creative work, learning new concepts
- **Medium energy**: Practice exercises, code reviews, documentation reading
- **Low energy**: Administrative tasks, organizing notes, routine activities

### 4. **Realistic Time Estimates**
- Consider ultradian rhythms (90-120 min focus blocks)
- Include breaks and buffer time
- Don't overcommit (respect available_hours_per_week)

### 5. **Dependencies**
- Identify prerequisite tasks
- Sequence tasks logically
- Ensure foundational knowledge before advanced topics

## ExAnalysis**: ✓ Shows what's good, what could be better
   - Feedback: "Good start! You've mentioned React and a deliverable (portfolio website). To make it stronger, let's add specific learning milestones and quantifiable outcomes."
   - SMART breakdown with visual indicators

2. **Refined Versions Presented**:
   - **Version 1**: "Complete React fundamentals course and build portfolio website by March 1st"
   - **Version 2**: "Learn React basics, build 3 portfolio projects (todo app, weather app, blog), and deploy portfolio website within 8 weeks"  
   - **Version 3**: "Complete React fundamentals course (24 hours), build 3 portfolio projects with specific features (todo app with localStorage, weather app with API, blog with routing), and deploy responsive portfolio website by March 1st"

3. **User selects** Version 2 → Proceeds to task generation

1. **Validation**: ❌ REJECTED
   - Feedback: "Goal needs more specificity. What specific React concepts? How many portfolio projects? What features?"
   - Suggested improvement: "Complete React fundamentals course, build 3 portfolio projects (todo app, weather app, blog), and deploy portfolio website by March 1st"

2. **User revises**: "Complete React fundamentals course, build 3 portfolio projects (todo app, weather app, blog), and deploy portfolio website by March 1st"

3. **Validation**: ✅ APPROVED
   - Specific: React fundamentals + 3 defined projects
   - Measurable: 3 projects, deployed website
   - Achievable: 8 weeks with 15 hours/week = 120 hours (realistic)
   - Time-bound: March 1st deadline

4. **Task Suggestions** (15 tasks generated):
   - Week 1-2: React fundamentals (24 hours)
   - Week 3-4: Todo app project (18 hours)
   - Week 5-6: Weather app project (18 hours)
   - Week 7: Blog project (15 hours)
   - Week 8: Portfolio deployment (10 hours)

5. **Scheduling Strategy**:
   - High-energy evening blocks for coding
   - Medium-energy for tutorials/documentation
   - Low-energy for planning and admin
   - Task batching: Group all tutorial modules together

6. **User accepts** tasks → System creates 15 tasks in database → Ready for scheduling

## Benefits

1. **Prevents vague goals**: Forces users to think clearly about outcomes
2. **Never blocked**: Users always have path forward with refinement suggestions
2. **Educational**: Shows what SMART goals look like through examples
3. **Flexible**: Can proceed with original or choose refined version
4. **Realistic planning**: LLM considers time constraints and energy levels
5. **Optimized for productivity**: Applies proven principles (80/20, batching, energy management)
6. **Reduces decision fatigue**: AI suggests optimal task breakdown
7. **Built-in accountability**: Refined goals are measurable by design
8. **Personalized**: Considers user's peak energy times and availability
9. **Progressive refinement**: Three levels of suggestions to choose from
## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/onboarding/validate-goal` | POST | Validate goal against SMART criteria |
| `/onboarding/suggest-tasks` | POST | Generate AI task suggestions |
| `/onboarding/create-tasks-from-suggestions` | POST | Create tasks from suggestions |
| `/onboarding/goals` | GET | List user's onboarding goals |

## Notes

- All endpoints require authentication (JWT token)
- LLM validation is strict to ensure quality goals
- Task suggestions follow productivity science principles
- Users can modify suggested tasks before creation
- System stores validation history for learning
