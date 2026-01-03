import { useState, useEffect } from "react";
import { Target, ListTodo, MessageCircle, User, TrendingUp, Sparkles, ArrowRight, MessageSquare } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { NewTaskDialog } from "@/components/dashboard/NewTaskDialog";
import { WeeklyGoalDialog } from "@/components/dashboard/WeeklyGoalDialog";
import { getTasks, getRecommendations, getGoals, Task, AIRecommendation, Goal } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

export default function Dashboard() {
  const { user, logout, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [goalDialogOpen, setGoalDialogOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [loadingGoals, setLoadingGoals] = useState(true);

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
      setLoadingTasks(false);
      setLoadingGoals(false);
    }
  }, [isAuthenticated, isLoading]);

  async function loadData() {
    setLoadingTasks(true);
    setLoadingGoals(true);
    
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

    getGoals()
      .then(goalsData => {
        setGoals(goalsData);
        setLoadingGoals(false);
      })
      .catch(err => {
        console.error('Failed to load goals:', err);
        setGoals([]);
        setLoadingGoals(false);
      });
  }

  // Calculate stats
  const activeGoals = goals.filter(g => !g.tasks_generated || tasks.some(t => t.goal === g.goal)).length;
  const completedTasks = tasks.filter(task => task.review).length;
  const totalTasks = tasks.length;
  const avgProgress = activeGoals > 0 ? Math.round((completedTasks / Math.max(totalTasks, 1)) * 100) : 0;
  
  // Get upcoming tasks (no review, sorted by priority and due date)
  const upcomingTasks = tasks
    .filter(task => !task.review)
    .sort((a, b) => {
      if (a.priority !== b.priority) return (b.priority || 5) - (a.priority || 5);
      if (a.due_date && b.due_date) return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      return 0;
    })
    .slice(0, 3);

  // Helper function to get goal for task
  const getGoalForTask = (task: Task): Goal | undefined => {
    if (task.goal_id) {
      return goals.find(g => g.id === task.goal_id);
    }
    return undefined;
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
    <div className="flex min-h-screen bg-[#F8F9FB]">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-border p-6 flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg">GoalFlow</h1>
            <p className="text-xs text-muted-foreground">AI-Powered Goals</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 text-purple-600 font-medium"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Home
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
          
          <Link
            to="/goals"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <Target className="w-5 h-5" />
            Goals
          </Link>
          
          <Link
            to="/tasks"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <ListTodo className="w-5 h-5" />
            Tasks
          </Link>
          
          <Link
            to="/coach"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <MessageCircle className="w-5 h-5" />
            Coach
          </Link>
          
          <Link
            to="/profile"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <User className="w-5 h-5" />
            Profile
          </Link>
          
          <Link
            to="/leaderboard"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <TrendingUp className="w-5 h-5" />
            Leaderboard
          </Link>
        </nav>

        {/* AI Goal Coach Card */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 text-white">
          <Sparkles className="w-8 h-8 mb-4" />
          <h3 className="font-semibold mb-2">AI Goal Coach</h3>
          <p className="text-sm text-purple-100 mb-4">
            Get personalized guidance, break down goals, and stay motivated
          </p>
          <button 
            onClick={() => navigate('/coach')}
            className="w-full bg-white text-purple-600 rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
          >
            Start a session
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">Track your goals and stay on course</p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              className="gap-2"
            >
              <MessageSquare className="w-5 h-5" />
              Talk to Coach
            </Button>
            <Button
              onClick={() => setGoalDialogOpen(true)}
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Goal
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          {/* Active Goals */}
          <Link 
            to="/goals"
            className="bg-purple-50 rounded-2xl p-6 border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all cursor-pointer"
          >
            <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center mb-4">
              <Target className="w-6 h-6 text-white" />
            </div>
            <div className="text-4xl font-bold text-gray-900 mb-1">
              {loadingGoals ? "..." : activeGoals}
            </div>
            <div className="text-gray-600">Active Goals</div>
          </Link>

          {/* Tasks Completed */}
          <Link
            to="/tasks"
            className="bg-teal-50 rounded-2xl p-6 border border-teal-100 hover:border-teal-300 hover:shadow-md transition-all cursor-pointer"
          >
            <div className="w-12 h-12 bg-teal-500 rounded-xl flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-4xl font-bold text-gray-900 mb-1">
              {loadingTasks ? "..." : `${completedTasks}/${Math.max(totalTasks, 5)}`}
            </div>
            <div className="text-gray-600">Tasks Completed</div>
          </Link>

          {/* Avg Progress */}
          <div className="bg-blue-50 rounded-2xl p-6 border border-blue-100">
            <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="text-4xl font-bold text-gray-900 mb-1">
              {loadingTasks ? "..." : `${avgProgress}%`}
            </div>
            <div className="text-gray-600">Avg Progress</div>
          </div>

          {/* Upcoming */}
          <div className="bg-orange-50 rounded-2xl p-6 border border-orange-100">
            <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="text-4xl font-bold text-gray-900 mb-1">
              {loadingTasks ? "..." : upcomingTasks.length}
            </div>
            <div className="text-gray-600">Upcoming</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Goals Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-purple-600" />
                <h2 className="text-xl font-bold text-gray-900">Active Goals</h2>
              </div>
              <Link 
                to="/goals"
                className="text-purple-600 hover:text-purple-700 flex items-center gap-1 text-sm font-medium"
              >
                View All
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="space-y-4">
              {loadingGoals ? (
                <div className="bg-white rounded-2xl p-6 border border-gray-200">
                  <p className="text-gray-500">Loading goals...</p>
                </div>
              ) : goals.length > 0 ? (
                goals.slice(0, 2).map((goal, idx) => {
                  const goalTasks = tasks.filter(t => t.goal === goal.goal);
                  const completedGoalTasks = goalTasks.filter(t => t.review).length;
                  const progress = goalTasks.length > 0 ? (completedGoalTasks / goalTasks.length) * 100 : 0;
                  
                  return (
                    <Link 
                      key={goal.id} 
                      to={`/goals/${goal.id}`}
                      className="block bg-white rounded-2xl p-6 border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all cursor-pointer"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
                          <Target className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <h3 className="font-semibold text-gray-900 text-lg">
                              {goal.goal.length > 50 ? goal.goal.substring(0, 50) + '...' : goal.goal}
                            </h3>
                            <div className="text-gray-400 hover:text-gray-600">
                              <ArrowRight className="w-5 h-5" />
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2 mb-3">
                            <span className="px-3 py-1 bg-teal-100 text-teal-700 rounded-full text-xs font-medium">
                              health
                            </span>
                            <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                              high
                            </span>
                          </div>
                          
                          <p className="text-gray-600 text-sm mb-4">
                            {goal.goal}
                          </p>
                          
                          <div className="mb-2">
                            <div className="flex items-center justify-between text-sm mb-2">
                              <span className="text-gray-600">Progress</span>
                              <span className="font-semibold text-gray-900">{Math.round(progress)}%</span>
                            </div>
                            <Progress value={progress} className="h-2" />
                          </div>
                          
                          <div className="flex items-center justify-between text-sm text-gray-500">
                            <div className="flex items-center gap-1">
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {new Date(goal.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                            </div>
                            <div className="flex items-center gap-1 text-purple-600">
                              <Sparkles className="w-4 h-4" />
                              AI Analyzed
                            </div>
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })
              ) : (
                <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Target className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">No Active Goals</h3>
                  <p className="text-gray-500 mb-4">Create your first goal to get started</p>
                  <Button
                    onClick={() => navigate('/onboarding')}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    Create Goal
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Upcoming Tasks Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Upcoming Tasks</h2>
              <button className="text-purple-600 hover:text-purple-700 flex items-center gap-1 text-sm font-medium">
                View All
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              {loadingTasks ? (
                <div className="bg-white rounded-xl p-4 border border-gray-200">
                  <p className="text-gray-500 text-sm">Loading tasks...</p>
                </div>
              ) : upcomingTasks.length > 0 ? (
                upcomingTasks.map((task, idx) => (
                  <div
                    key={task.id}
                    className={`bg-white rounded-xl p-4 border-l-4 ${
                      idx === 0 ? 'border-l-red-400' : idx === 1 ? 'border-l-blue-400' : 'border-l-gray-300'
                    } border-t border-r border-b border-gray-200 hover:shadow-md transition-shadow cursor-pointer`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 mb-1">{task.title}</h4>
                        {(() => {
                          const linkedGoal = getGoalForTask(task);
                          if (linkedGoal) {
                            return (
                              <Link 
                                to={`/goals/${linkedGoal.id}`}
                                className="text-sm text-purple-600 hover:text-purple-700 hover:underline mb-2 inline-block"
                              >
                                🎯 {linkedGoal.goal}
                              </Link>
                            );
                          }
                          return <p className="text-sm text-gray-500 mb-2">{task.goal}</p>;
                        })()}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <div className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {task.calendar_scheduling?.scheduled?.[0]?.start_time ? (
                              new Date(task.calendar_scheduling.scheduled[0].start_time).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })
                            ) : task.due_date ? (
                              new Date(task.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                            ) : (
                              'No date'
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {task.time_hours}h
                          </div>
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded font-medium ml-auto">
                            <Sparkles className="w-3 h-3 inline" /> AI
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bg-white rounded-xl p-6 border border-gray-200 text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <ListTodo className="w-6 h-6 text-gray-400" />
                  </div>
                  <p className="text-gray-500 text-sm mb-3">No upcoming tasks</p>
                  <Button
                    onClick={() => setTaskDialogOpen(true)}
                    size="sm"
                    variant="outline"
                  >
                    Create Task
                  </Button>
                </div>
              )}
            </div>

            {/* AI Goal Coach (Right Side) */}
            <div className="mt-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 text-white">
              <Sparkles className="w-8 h-8 mb-3" />
              <h3 className="font-semibold mb-2">AI Goal Coach</h3>
              <p className="text-sm text-purple-100 mb-4">
                Get personalized guidance, break down goals, and stay motivated
              </p>
              <button 
                onClick={() => navigate('/coach')}
                className="w-full bg-white text-purple-600 rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
              >
                Start a session
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <NewTaskDialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen} onTaskCreated={loadData} />
      <WeeklyGoalDialog open={goalDialogOpen} onOpenChange={setGoalDialogOpen} onGoalCreated={loadData} />
    </div>
  );
}
