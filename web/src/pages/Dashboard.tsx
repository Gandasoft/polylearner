import { useState, useEffect } from "react";
import { Bell, Play, Sparkles, Mail, Flame, Info, Users, Video, Calendar, MessageSquare, Settings, Home, Plus, LogOut, Target } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { NewTaskDialog } from "@/components/dashboard/NewTaskDialog";
import { WeeklyGoalDialog } from "@/components/dashboard/WeeklyGoalDialog";
import { getTasks, getRecommendations, getSchedule, Task, AIRecommendation, WeekScheduleResponse } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export default function Dashboard() {
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [goalDialogOpen, setGoalDialogOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [scheduleData, setScheduleData] = useState<WeekScheduleResponse | null>(null);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [loadingRecommendations, setLoadingRecommendations] = useState(true);
  const [loadingSchedule, setLoadingSchedule] = useState(true);

  // Redirect to landing page if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    } else if (!isLoading) {
      // Set loading to false if not authenticated
      setLoadingTasks(false);
      setLoadingRecommendations(false);
      setLoadingSchedule(false);
    }
  }, [isAuthenticated, isLoading]);

  async function loadData() {
    // Load tasks first (most critical)
    setLoadingTasks(true);
    getTasks()
      .then(tasksData => {
        setTasks(tasksData);
        setLoadingTasks(false);
      })
      .catch(err => {
        console.error('Failed to load tasks:', err);
        setTasks([]);
        setLoadingTasks(false);
      });

    // Load recommendations in background
    setLoadingRecommendations(true);
    getRecommendations()
      .then(recommendationsData => {
        setRecommendations(recommendationsData);
        setLoadingRecommendations(false);
      })
      .catch(err => {
        console.error('Failed to load recommendations:', err);
        setRecommendations([]);
        setLoadingRecommendations(false);
      });

    // Load schedule in background
    setLoadingSchedule(true);
    getSchedule()
      .then(schedule => {
        setScheduleData(schedule);
        setLoadingSchedule(false);
      })
      .catch(err => {
        console.error('Failed to load schedule:', err);
        setScheduleData(null);
        setLoadingSchedule(false);
      });
  }

  // Get high priority tasks for "Up Next" section
  const upNextTasks = tasks
    .filter(task => !task.review) // Only show incomplete tasks
    .sort((a, b) => (b.priority || 5) - (a.priority || 5))
    .slice(0, 3)
    .map(task => ({
      id: task.id.toString(),
      title: task.title,
      time: task.due_date || 'Today',
      location: task.category,
      tag: task.category.toUpperCase(),
    }));

  // Get current focus task (highest priority incomplete task)
  const currentTask = tasks
    .filter(task => !task.review)
    .sort((a, b) => (b.priority || 5) - (a.priority || 5))[0];

  // Calculate productivity metrics
  const completedTasks = tasks.filter(task => task.review).length;
  const totalTasks = tasks.length;
  const productivity = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Calculate average focus rate
  const tasksWithReviews = tasks.filter(task => task.review);
  const avgFocusRate = tasksWithReviews.length > 0
    ? tasksWithReviews.reduce((sum, task) => sum + (task.review?.focus_rate || 0), 0) / tasksWithReviews.length
    : 5;

  const cognitiveLoad = avgFocusRate <= 3 ? 'Low' : avgFocusRate <= 7 ? 'Moderate' : 'High';
  const cognitiveLoadEmoji = avgFocusRate <= 3 ? '😊' : avgFocusRate <= 7 ? '😐' : '😰';

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Main Content */}
      <div className="w-full p-6 pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-7 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {user?.picture ? (
                  <img 
                    src={user.picture} 
                    alt={user.name}
                    className="w-12 h-12 rounded-full"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-primary-foreground font-semibold text-lg">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                )}
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Good Afternoon</p>
                  <p className="font-semibold text-foreground text-lg">{user?.name || 'User'}</p>
                </div>
              </div>
            </div>

            {/* Current Focus Card */}
            <div className="bg-card rounded-2xl p-6 border border-border">
              <div className="flex items-center justify-between mb-4">
                <span className="flex items-center gap-2 text-sm font-medium text-primary">
                  <Sparkles className="w-4 h-4" />
                  CURRENT FOCUS
                </span>
                <span className="text-sm text-muted-foreground">{currentTask?.due_date || 'Due Today'}</span>
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {loadingTasks ? 'Loading...' : currentTask ? currentTask.title : 'No tasks yet'}
              </h2>
              <p className="text-muted-foreground mb-6">
                {loadingTasks ? 'Fetching tasks...' : currentTask ? currentTask.goal : 'Create your first task to get started.'}
              </p>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Est. Time</p>
                  <p className="text-2xl font-bold text-foreground">
                    {currentTask ? `${currentTask.time_hours}h` : '--'}
                  </p>
                </div>
                <Button 
                  className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2 rounded-xl px-8 py-6 text-base"
                  disabled={!currentTask}
                >
                  <Play className="w-5 h-5" />
                  Start Timer
                </Button>
              </div>
            </div>

            {/* AI Insights */}
            <div className="bg-card rounded-2xl p-5 border border-border">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-primary" />
                <span className="font-semibold text-foreground">AI Insights</span>
              </div>
              <div className="flex flex-wrap gap-3">
                {loadingRecommendations ? (
                  <p className="text-sm text-muted-foreground">Loading recommendations...</p>
                ) : recommendations.length > 0 ? (
                  recommendations.map((rec, idx) => (
                    <button
                      key={idx}
                      className="flex items-center gap-2 bg-secondary hover:bg-secondary/80 rounded-xl px-4 py-3 text-foreground transition-colors"
                      title={rec.reason}
                    >
                      <Sparkles className="w-5 h-5 text-primary" />
                      {rec.suggestion}
                    </button>
                  ))
                ) : tasks.length === 0 ? (
                  <>
                    <button 
                      onClick={() => navigate('/onboarding')}
                      className="flex items-center gap-2 bg-primary hover:bg-primary/90 rounded-xl px-4 py-3 text-primary-foreground transition-colors"
                    >
                      <Target className="w-5 h-5" />
                      Set Your First Goal
                    </button>
                    <button 
                      onClick={() => setTaskDialogOpen(true)}
                      className="flex items-center gap-2 bg-secondary hover:bg-secondary/80 rounded-xl px-4 py-3 text-foreground transition-colors"
                    >
                      <Mail className="w-5 h-5 text-primary" />
                      Or Create a Task Manually
                    </button>
                  </>
                ) : (
                  <>
                    <button 
                      onClick={() => setTaskDialogOpen(true)}
                      className="flex items-center gap-2 bg-secondary hover:bg-secondary/80 rounded-xl px-4 py-3 text-foreground transition-colors"
                    >
                      <Mail className="w-5 h-5 text-primary" />
                      Create your first task
                    </button>
                    <button 
                      onClick={() => setGoalDialogOpen(true)}
                      className="flex items-center gap-2 bg-secondary hover:bg-secondary/80 rounded-xl px-4 py-3 text-foreground transition-colors"
                    >
                      <Flame className="w-5 h-5 text-warning" />
                      Set your goals
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Productivity */}
              <div className="bg-card rounded-2xl p-5 border border-border">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-muted-foreground uppercase">Productivity</span>
                  <span className="text-sm text-success font-medium">
                    {loadingTasks ? '...' : `${completedTasks}/${totalTasks}`}
                  </span>
                </div>
                <p className="text-3xl font-bold text-foreground mb-3">
                  {loadingTasks ? '--' : productivity}<span className="text-xl">%</span>
                </p>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div 
                      key={i} 
                      className={`w-8 h-8 rounded ${i <= Math.round(productivity / 20) ? 'bg-primary' : 'bg-muted'}`}
                    />
                  ))}
                </div>
              </div>

              {/* Cognitive Load */}
              <div className="bg-card rounded-2xl p-5 border border-border">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-muted-foreground uppercase">Cog. Load</span>
                  <Info className="w-4 h-4 text-muted-foreground" />
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <p className="text-2xl font-bold text-foreground">
                    {loadingTasks ? 'Loading...' : cognitiveLoad}
                  </p>
                  <span className="text-2xl">{cognitiveLoadEmoji}</span>
                </div>
                <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-success via-warning to-destructive rounded-full" 
                    style={{ width: `${(avgFocusRate / 10) * 100}%` }}
                  />
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  {avgFocusRate <= 7 ? 'Optimal range for deep work' : 'Consider taking a break'}
                </p>
              </div>
            </div>
          </div>

          {/* Right Column - Calendar & Up Next */}
          <div className="lg:col-span-5 space-y-6">
            {/* Top Right Actions */}
            <div className="flex items-center justify-end gap-2">
              <div className="relative cursor-pointer">
                <Bell className="w-6 h-6 text-muted-foreground hover:text-foreground transition-colors" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-destructive rounded-full" />
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Logout">
                <LogOut className="h-5 w-5" />
              </Button>
            </div>

            {/* Calendar View */}
            <div className="bg-card rounded-2xl p-5 border border-border">
              <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-foreground text-lg">Schedule</h3>
              <button 
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  setLoadingSchedule(true);
                  getSchedule()
                    .then(schedule => {
                      setScheduleData(schedule);
                      setLoadingSchedule(false);
                    })
                    .catch(err => {
                      console.error('Failed to load schedule:', err);
                      setLoadingSchedule(false);
                    });
                }}
                disabled={loadingSchedule}
                className="text-sm text-primary hover:underline disabled:opacity-50"
              >
                {loadingSchedule ? 'Refreshing...' : 'Refresh'}
              </button>
              </div>

              {/* Week Days Selector */}
              <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
              {(() => {
                const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
                const today = new Date();
                return Array.from({ length: 7 }, (_, i) => {
                const date = new Date(today);
                date.setDate(today.getDate() - today.getDay() + i);
                const isToday = date.toDateString() === today.toDateString();
                return (
                  <button
                  key={i}
                  className={`flex flex-col items-center min-w-[48px] py-2 px-3 rounded-xl transition-colors ${
                    isToday 
                    ? 'bg-primary text-primary-foreground' 
                    : 'text-muted-foreground hover:bg-secondary'
                  }`}
                  >
                  <span className="text-xs font-medium">{days[i]}</span>
                  <span className={`text-lg font-bold ${isToday ? '' : 'text-foreground'}`}>{date.getDate()}</span>
                  </button>
                );
                });
              })()}
              </div>

              {/* Today's Schedule */}
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {loadingSchedule ? (
                <p className="text-sm text-muted-foreground text-center py-4">Loading schedule...</p>
              ) : scheduleData && scheduleData.schedule.length > 0 ? (
                (() => {
                const today = new Date();
                const todaySchedule = scheduleData.schedule.filter(block => {
                  const blockDate = new Date(block.start_time);
                  return blockDate.toDateString() === today.toDateString();
                });

                if (todaySchedule.length === 0) {
                  return (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No tasks scheduled for today
                  </p>
                  );
                }

                return todaySchedule.map((block, idx) => {
                  const startTime = new Date(block.start_time);
                  const endTime = new Date(block.end_time);
                  const timeStr = `${startTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })} - ${endTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}`;
                  
                  return (
                  <div key={idx} className="bg-secondary/50 rounded-xl p-3">
                    <div className="flex items-start justify-between mb-1">
                    <span className="text-xs font-medium text-primary uppercase">{block.category}</span>
                    <span className="text-xs text-muted-foreground">{block.duration_hours}h</span>
                    </div>
                    <h4 className="font-medium text-foreground text-sm mb-1">{block.task_title}</h4>
                    <p className="text-xs text-muted-foreground">{timeStr}</p>
                  </div>
                  );
                });
                })()
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                No schedule available. Create tasks to get started!
                </p>
              )}
              </div>

              {/* Cognitive Tax Score */}
              {scheduleData && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="flex items-center justify-between text-sm">
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Cognitive Tax</p>
                  <p className="text-lg font-bold text-foreground">
                  {(scheduleData.cognitive_tax_score * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground uppercase">Total Hours</p>
                  <p className="text-lg font-bold text-foreground">
                  {scheduleData.total_hours.toFixed(1)}h
                  </p>
                </div>
                </div>
              </div>
              )}
            </div>

            {/* Up Next Section */}
            <div className="bg-card rounded-2xl p-5 border border-border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-foreground text-lg">Up Next</h3>
              </div>
              <div className="space-y-3">
                {loadingTasks ? (
                  <p className="text-sm text-muted-foreground">Loading tasks...</p>
                ) : upNextTasks.length > 0 ? (
                  upNextTasks.map((task) => (
                    <div key={task.id} className="bg-secondary/50 rounded-xl p-4 flex items-center gap-3">
                      <Checkbox className="rounded-full" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground">{task.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {task.time}{task.location && ` • ${task.location}`}
                        </p>
                      </div>
                      {task.tag && (
                        <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded font-medium">
                          {task.tag}
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No upcoming tasks. Create one to get started!
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Floating Add Button */}
        <button 
          onClick={() => setTaskDialogOpen(true)}
          className="fixed bottom-24 right-6 w-16 h-16 bg-primary hover:bg-primary/90 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105"
        >
          <Plus className="w-7 h-7 text-primary-foreground" />
        </button>
      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
        <div className="flex items-center justify-around py-4 max-w-2xl mx-auto">
          <Link to="/dashboard" className="flex flex-col items-center gap-1 text-primary">
            <Home className="w-6 h-6" />
            <span className="text-xs">Home</span>
          </Link>
          <Link to="/onboarding" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground">
            <Target className="w-6 h-6" />
            <span className="text-xs">Goals</span>
          </Link>
          <button className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground">
            <Calendar className="w-6 h-6" />
            <span className="text-xs">Calendar</span>
          </button>
          <button className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground">
            <Settings className="w-6 h-6" />
            <span className="text-xs">Settings</span>
          </button>
        </div>
      </nav>

      <NewTaskDialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen} onTaskCreated={loadData} />
      <WeeklyGoalDialog open={goalDialogOpen} onOpenChange={setGoalDialogOpen} onGoalCreated={loadData} />
    </div>
  );
}
