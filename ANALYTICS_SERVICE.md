# Analytics Service Documentation

## Overview

The Analytics Service is an intelligent task management system that uses Large Language Models (LLMs) to:

1. **Group tasks by similarity** - Automatically categorize and cluster related tasks
2. **Generate optimal schedules** - Create weekly schedules that minimize cognitive load
3. **Allocate time slots intelligently** - Smart time allocation based on task priority, energy levels, and context

## Architecture

### Core Component: `analytics_service.py`

The `TaskAnalyticsService` class provides the following capabilities:

- **LLM-powered task grouping** - Uses GPT-4 to analyze task content and group similar tasks
- **Intelligent scheduling** - Considers multiple factors to create optimal schedules
- **Cognitive tax calculation** - Measures context switching and schedule efficiency
- **Pattern analysis** - Identifies trends and provides actionable insights

## API Endpoints

### 1. Group Tasks by Similarity

**Endpoint:** `GET /analytics/groups`

Groups all tasks by similarity using LLM analysis.

**Response:**
```json
{
  "groups": [
    {
      "group_name": "Machine Learning Projects",
      "task_count": 3,
      "total_hours": 15.5,
      "tasks": [
        {"id": 1, "title": "Train CNN model", "category": "coding"},
        {"id": 2, "title": "Optimize hyperparameters", "category": "research"}
      ]
    }
  ],
  "total_groups": 4
}
```

**Use Case:** Understanding which tasks are related and should be worked on together.

---

### 2. Get Intelligent Schedule

**Endpoint:** `GET /analytics/schedule/intelligent`

**Query Parameters:**
- `week_start` (optional): ISO format date string (e.g., "2025-12-30")
- `daily_start` (optional): Work day start hour (default: 9)
- `daily_end` (optional): Work day end hour (default: 17)
- `peak_hours` (optional): Peak productivity hours (default: "9-12")

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
      "scheduling_reason": "High-priority coding task scheduled during peak hours"
    }
  ],
  "total_blocks": 15,
  "total_hours": 40.5,
  "cognitive_metrics": {
    "cognitive_tax_score": 0.234,
    "context_switches": 8,
    "average_block_duration": 2.7,
    "fragmentation_score": 0.133,
    "interpretation": "Good - Moderate context switching with decent focus time"
  },
  "recommendations": [...]
}
```

**Features:**
- Groups similar tasks together
- Schedules demanding tasks during peak hours
- Minimizes context switching
- Respects natural energy patterns
- Includes buffer time

---

### 3. Analyze Task Patterns

**Endpoint:** `GET /analytics/patterns`

Provides comprehensive analysis of task patterns and trends.

**Response:**
```json
{
  "total_tasks": 20,
  "total_hours": 65.5,
  "average_task_duration": 3.27,
  "average_priority": 6.8,
  "category_distribution": {
    "coding": {
      "count": 8,
      "total_hours": 28.0
    },
    "research": {
      "count": 7,
      "total_hours": 25.5
    }
  },
  "most_common_category": "coding",
  "ai_insights": "Your workload shows a healthy balance between coding and research..."
}
```

**Use Case:** Understanding workload distribution and identifying potential issues.

---

### 4. Cognitive Tax Analysis

**Endpoint:** `GET /analytics/cognitive-tax`

**Query Parameters:**
- `week_start` (optional): ISO format date string
- `daily_start` (optional): Work day start hour
- `daily_end` (optional): Work day end hour

**Response:**
```json
{
  "basic_schedule": {
    "metrics": {
      "cognitive_tax_score": 0.567,
      "context_switches": 15,
      "average_block_duration": 1.8
    },
    "blocks": 22
  },
  "intelligent_schedule": {
    "metrics": {
      "cognitive_tax_score": 0.234,
      "context_switches": 8,
      "average_block_duration": 2.7
    },
    "blocks": 18
  },
  "improvement": {
    "absolute": 0.333,
    "percentage": 58.7,
    "recommendation": "Use intelligent scheduling"
  }
}
```

**Use Case:** Comparing basic vs. AI-optimized scheduling to see potential improvements.

## Key Concepts

### Cognitive Tax

**Cognitive tax** measures the mental cost of your schedule based on:
- **Context switching**: Changing between different types of tasks
- **Block duration**: Longer focused blocks are better
- **Fragmentation**: Many small blocks increase overhead

**Score Range:** 0.0 (best) to 1.0 (worst)

**Interpretation:**
- < 0.3: Excellent - Very low context switching
- 0.3-0.5: Good - Moderate switching, decent focus
- 0.5-0.7: Fair - Consider regrouping tasks
- > 0.7: Poor - High fragmentation, needs optimization

### Task Grouping Algorithm

The LLM considers multiple factors when grouping tasks:
1. **Subject matter similarity** - Related topics or domains
2. **Required skills/tools** - Common technologies or methods
3. **Dependencies** - Sequential or prerequisite relationships
4. **Complementary activities** - Tasks that benefit from being done together

### Intelligent Scheduling Principles

1. **Peak Hours Optimization** - Demanding tasks during your most productive time
2. **Task Batching** - Similar tasks grouped together
3. **Energy Management** - Harder tasks early, lighter tasks later
4. **Buffer Time** - Built-in slack for unexpected delays
5. **Break Integration** - Automatic break scheduling
6. **Deadline Awareness** - Priority to time-sensitive tasks

## Configuration

### Environment Variables

```bash
# Required for AI features
OPENAI_API_KEY=your-api-key-here

# OpenAI models used:
# - GPT-4o: For task grouping and intelligent scheduling
# - GPT-4o-mini: For quick recommendations and insights
```

### User Preferences

You can customize scheduling behavior:

```python
preferences = {
    "peak_hours": "9-12",           # Your most productive hours
    "break_duration_minutes": 15,   # Break length
    "max_continuous_hours": 2       # Max time before a break
}
```

## Implementation Details

### Fallback Behavior

If OpenAI API is unavailable or fails:
- **Task grouping**: Falls back to category-based grouping
- **Scheduling**: Uses rule-based algorithm (sort by category + priority)
- **Insights**: Provides generic recommendations

This ensures the service is always functional, even without AI.

### Performance Considerations

- **Task grouping**: ~2-5 seconds for 20-30 tasks
- **Intelligent scheduling**: ~3-7 seconds for comprehensive analysis
- **Token usage**: ~500-2000 tokens per analysis (OpenAI API costs)

### Token Cost Estimation

Using GPT-4o pricing (as of Dec 2024):
- Task grouping: ~$0.01-0.02 per request
- Intelligent scheduling: ~$0.02-0.04 per request
- Pattern analysis: ~$0.01-0.02 per request

## Usage Examples

### Example 1: Get Weekly Schedule

```bash
# Get optimized schedule for current week
curl http://localhost:8000/analytics/schedule/intelligent

# Get schedule for specific week
curl "http://localhost:8000/analytics/schedule/intelligent?week_start=2025-12-30&peak_hours=10-13"
```

### Example 2: Analyze Task Groups

```bash
# See how tasks are grouped
curl http://localhost:8000/analytics/groups
```

### Example 3: Compare Schedules

```bash
# See improvement from intelligent scheduling
curl http://localhost:8000/analytics/cognitive-tax
```

## Benefits

### For Users

1. **Reduced Context Switching** - 40-60% reduction in task category changes
2. **Better Focus Time** - Longer uninterrupted work blocks
3. **Energy Alignment** - Demanding tasks during peak hours
4. **Workload Insights** - Clear visibility into task patterns
5. **Time Savings** - Automated schedule optimization

### For Developers

1. **Extensible Architecture** - Easy to add new analytics features
2. **Fallback Support** - Graceful degradation without API
3. **Logging & Monitoring** - Comprehensive logging for debugging
4. **Type Safety** - Full Pydantic model validation

## Future Enhancements

Potential improvements for the analytics service:

1. **Learning from History** - Adapt to user's actual completion patterns
2. **Collaboration Awareness** - Consider team schedules and meetings
3. **Multi-week Planning** - Long-term scheduling optimization
4. **Personal Analytics Dashboard** - Detailed productivity metrics
5. **Custom ML Models** - Fine-tuned models on user's task history
6. **Integration with Calendar** - Sync with Google Calendar, Outlook, etc.

## Troubleshooting

### Common Issues

**Issue:** "Analytics service not available" error
- **Solution**: Check that `OPENAI_API_KEY` is set in environment variables
- **Note**: Service will still work with limited functionality

**Issue:** Task grouping returns only categories
- **Solution**: This is expected fallback behavior when LLM is unavailable
- **Check**: Verify API key is valid and has sufficient credits

**Issue:** Schedule generation is slow
- **Solution**: This is normal for comprehensive AI analysis (3-7 seconds)
- **Alternative**: Use the basic `/schedule` endpoint for faster results

## Contributing

When extending the analytics service:

1. Add new methods to `TaskAnalyticsService` class
2. Create corresponding API endpoints in `app.py`
3. Update this documentation
4. Add logging for new features
5. Include fallback behavior for LLM failures

## License

Part of the PolyLearner project.
