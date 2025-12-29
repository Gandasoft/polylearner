// API client for PolyLearner backend

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

export interface Task {
  id: number;
  title: string;
  category: 'research' | 'coding' | 'admin' | 'networking';
  time_hours: number;
  goal: string;
  artifact: 'article' | 'notes' | 'code';
  weekly_goal_id?: number;
  review?: Review;
  priority?: number;
  due_date?: string;
  calendar_scheduling?: {
    scheduled?: Array<{
      event_id: string;
      start_time: string;
      end_time: string;
    }>;
    error?: string;
  };
}

export interface Review {
  notes: string;
  focus_rate: number;
  artifact: string;
  done_on_time: 'yes' | 'no';
}

export interface TaskCreate {
  title: string;
  category: 'research' | 'coding' | 'admin' | 'networking';
  time_hours: number;
  goal: string;
  artifact: 'article' | 'notes' | 'code';
  weekly_goal_id?: number;
  review?: Review;
  priority?: number;
  due_date?: string;
}

export interface AIRecommendation {
  suggestion: string;
  reason: string;
  priority: number;
}

export interface ScheduleBlock {
  task_id: number;
  task_title: string;
  category: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
}

export interface WeekScheduleResponse {
  week_start: string;
  schedule: ScheduleBlock[];
  recommendations: AIRecommendation[];
  total_hours: number;
  cognitive_tax_score: number;
}

export interface WeeklyGoal {
  id: number;
  week_number: number;
  goal: string;
  task_ids: number[];
  weekly_review?: Review;
}

export interface WeeklyGoalCreate {
  week_number: number;
  goal: string;
}

// Goal Onboarding interfaces
export interface GoalSubmission {
  goal: string;
  // Note: timeframe, hours, and energy preferences inferred from weekly feedback analysis
}

export interface GoalValidationResponse {
  is_valid: boolean;
  validation_details: {
    specific: boolean;
    measurable: boolean;
    achievable: boolean;
    relevant: boolean;
    time_bound: boolean;
  };
  feedback: string;
  suggestions: string[];
  refined_versions: Array<{
    goal: string;
    improvement: string;
    why_better: string;
  }>;
}

export interface SuggestedTask {
  title: string;
  category: 'research' | 'coding' | 'admin' | 'networking';
  time_hours: number;
  goal: string;
  artifact: 'article' | 'notes' | 'code';
  priority: number;
  energy_level: string;
  batch_group: string;
  dependencies: string[];
}

export interface TaskSuggestionResponse {
  goal_id: number;  // ID of the saved goal
  suggested_tasks: SuggestedTask[];
  scheduling_strategy: string;
  estimated_total_hours: number;
  energy_allocation: {
    high_energy_hours: number;
    medium_energy_hours: number;
    low_energy_hours: number;
  };
  batching_recommendations?: string;
  weekly_breakdown?: string;
}

export interface OnboardingGoal {
  id: number;
  user_id: number;
  goal: string;
  timeframe: string;
  is_validated: boolean;
  validation_feedback?: string;
  created_at: string;
  tasks_generated: boolean;
}

// API functions
export async function getTasks(): Promise<Task[]> {
  const response = await fetch(`${API_BASE_URL}/tasks`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch tasks');
  }
  return response.json();
}

export async function createTask(task: TaskCreate): Promise<Task> {
  const response = await fetch(`${API_BASE_URL}/tasks?auto_schedule=true`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(task),
  });
  if (!response.ok) {
    throw new Error('Failed to create task');
  }
  return response.json();
}

export async function getRecommendations(): Promise<AIRecommendation[]> {
  const response = await fetch(`${API_BASE_URL}/recommendations`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch recommendations');
  }
  return response.json();
}

export async function getSchedule(
  weekStart?: string,
  dailyStart: number = 9,
  dailyEnd: number = 17
): Promise<WeekScheduleResponse> {
  const params = new URLSearchParams();
  if (weekStart) params.append('week_start', weekStart);
  params.append('daily_start', dailyStart.toString());
  params.append('daily_end', dailyEnd.toString());

  const response = await fetch(`${API_BASE_URL}/schedule?${params}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch schedule');
  }
  return response.json();
}

export async function getWeeklyGoals(): Promise<WeeklyGoal[]> {
  const response = await fetch(`${API_BASE_URL}/weekly-goals`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch weekly goals');
  }
  return response.json();
}

export async function createWeeklyGoal(goal: WeeklyGoalCreate): Promise<WeeklyGoal> {
  const response = await fetch(`${API_BASE_URL}/weekly-goals`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(goal),
  });
  if (!response.ok) {
    throw new Error('Failed to create weekly goal');
  }
  return response.json();
}

export async function addTaskReview(taskId: number, review: Review): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/tasks/reviews`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ task_id: taskId, ...review }),
  });
  if (!response.ok) {
    throw new Error('Failed to add review');
  }
}

export async function addWeeklyReview(weeklyGoalId: number, review: Review): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/weekly-goals/review`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ weekly_goal_id: weeklyGoalId, ...review }),
  });
  if (!response.ok) {
    throw new Error('Failed to add weekly review');
  }
}

// Goal Onboarding API functions
export async function validateGoal(goalSubmission: GoalSubmission): Promise<GoalValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/onboarding/validate-goal`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(goalSubmission),
  });
  if (!response.ok) {
    throw new Error('Failed to validate goal');
  }
  return response.json();
}

export async function suggestTasks(goalSubmission: GoalSubmission): Promise<TaskSuggestionResponse> {
  const response = await fetch(`${API_BASE_URL}/onboarding/suggest-tasks`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(goalSubmission),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate task suggestions');
  }
  return response.json();
}

export async function createTasksFromSuggestions(
  suggestedTasks: SuggestedTask[],
  goalId?: number
): Promise<{ created_task_ids: number[]; count: number; message: string }> {
  const response = await fetch(`${API_BASE_URL}/onboarding/create-tasks-from-suggestions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ suggested_tasks: suggestedTasks, goal_id: goalId }),
  });
  if (!response.ok) {
    throw new Error('Failed to create tasks from suggestions');
  }
  return response.json();
}

export async function getOnboardingGoals(): Promise<OnboardingGoal[]> {
  const response = await fetch(`${API_BASE_URL}/onboarding/goals`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch onboarding goals');
  }
  return response.json();
}

export interface CalendarEvent {
  event_id: string;
  task_title: string;
  category: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  description: string;
}

export interface CalendarEventsResponse {
  events: CalendarEvent[];
  count: number;
  time_min: string;
  time_max: string;
}

export async function getCalendarEvents(
  timeMin?: string,
  timeMax?: string
): Promise<CalendarEventsResponse> {
  const params = new URLSearchParams();
  if (timeMin) params.append('time_min', timeMin);
  if (timeMax) params.append('time_max', timeMax);

  const response = await fetch(`${API_BASE_URL}/calendar/events?${params}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch calendar events');
  }
  return response.json();
}
