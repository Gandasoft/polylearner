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
  const response = await fetch(`${API_BASE_URL}/tasks`, {
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
