import { useState, useEffect } from "react";
import { Target, ListTodo, MessageCircle, User, TrendingUp, Sparkles, ArrowRight, Search, Plus, Calendar, Clock } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { NewTaskDialog } from "@/components/dashboard/NewTaskDialog";
import { getTasks, addTaskReview, getGoals, type Task, type Review, type Goal } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

type FilterTab = 'all' | 'pending' | 'in-progress' | 'completed';

export default function Tasks() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('all');
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);

  // Redirect to landing page if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  async function loadData() {
    setLoadingTasks(true);
    Promise.all([getTasks(), getGoals()])
      .then(([tasksData, goalsData]) => {
        setTasks(tasksData);
        setGoals(goalsData);
        setLoadingTasks(false);
      })
      .catch(err => {
        console.error('Failed to load data:', err);
        setTasks([]);
        setGoal.error('Failed to load tasks:', err);
        setTasks([]);
        setLoadingTasks(false);
      });
  }

  const handleToggleTask = async (task: Task) => {
    if (task.review) {
      // Task is already completed, don't allow uncompleting for now
      return;
    }

    // Mark task as completed
    const review: Review = {
      notes: "Completed via task list",
      focus_rate: 7,
      artifact: task.artifact,
      done_on_time: 'yes'
    };

    try {
      await addTaskReview(task.id, review);
      // Reload tasks to get updated state
      loadData();
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  };

  // Calculate task counts
  const pendingTasks = tasks.filter(t => !t.review);
  const completedTasks = tasks.filter(t => t.review);

  // Filter tasks based on search and filters
  const filteredTasks = tasks.filter(task => {
    // Search filter
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !task.goal.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Status filter
    if (filterTab === 'pending' && task.review) {
      return false;
    }
    if (filterTab === 'completed' && !task.review) {
      return false;
    }
    // 'in-progress' not implemented yet
    if (filterTab === 'in-progress') {
      return false;
    }

    return true;
  });

  // Helper function to get goal by task
  const getGoalForTask = (task: Task): Goal | undefined => {
    if (task.goal_id) {
      return goals.find(g => g.id === task.goal_id);
    }
    return undefined;
  };

  // Sort tasks: pending first (by priority), then completed
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    // Completed tasks go to bottom
    if (a.review && !b.review) return 1;
    if (!a.review && b.review) return -1;
    
    // Among pending tasks, sort by priority
    if (!a.review && !b.review) {
      if (a.priority !== b.priority) {
        return (b.priority || 5) - (a.priority || 5);
      }
      // Then by due date
      if (a.due_date && b.due_date) {
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      }
    }
    
    return 0;
  });

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
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Home
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
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 text-purple-600 font-medium"
          >
            <ListTodo className="w-5 h-5" />
            Tasks
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
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
            Get personalized guidance to achieve your goals faster
          </p>
          <button 
            onClick={() => navigate('/coach')}
            className="w-full bg-white text-purple-600 rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
          >
            Start Session
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <ListTodo className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">All Tasks</h1>
            </div>
            <p className="text-gray-500">
              {pendingTasks.length} pending • {completedTasks.length} completed
            </p>
          </div>
          <Button
            onClick={() => setTaskDialogOpen(true)}
            className="bg-gray-900 hover:bg-gray-800 gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Task
          </Button>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-white border-gray-200"
            />
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setFilterTab('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === 'all'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterTab('pending')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === 'pending'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pending
          </button>
          <button
            onClick={() => setFilterTab('in-progress')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === 'in-progress'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            In Progress
          </button>
          <button
            onClick={() => setFilterTab('completed')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === 'completed'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Completed
          </button>
        </div>

        {/* Tasks List */}
        <div className="space-y-3">
          {loadingTasks ? (
            <div className="bg-white rounded-xl p-12 border border-gray-200 text-center">
              <p className="text-gray-500">Loading tasks...</p>
            </div>
          ) : sortedTasks.length > 0 ? (
            sortedTasks.map((task, idx) => {
              const isCompleted = !!task.review;
              const borderColors = ['border-l-red-400', 'border-l-blue-400', 'border-l-purple-400', 'border-l-teal-400', 'border-l-orange-400'];
              const borderColor = isCompleted ? 'border-l-gray-300' : borderColors[idx % borderColors.length];
              
              return (
                <div
                  key={task.id}
                  className={`bg-white rounded-xl p-4 border-l-4 ${borderColor} border-t border-r border-b border-gray-200 hover:shadow-md transition-shadow`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      <Checkbox
                        checked={isCompleted}
                        onCheckedChange={() => handleToggleTask(task)}
                        className={`w-5 h-5 rounded-full ${
                          isCompleted 
                            ? 'bg-gray-400 border-gray-400 data-[state=checked]:bg-gray-400' 
                            : 'border-2 border-gray-300'
                        }`}
                        disabled={isCompleted}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className={`font-medium mb-1 ${
                        isCompleted ? 'text-gray-400 line-through' : 'text-gray-900'
                      }`}>
                        {task.title}
                      </h4>
                      {(() => {
                        const linkedGoal = getGoalForTask(task);
                        if (linkedGoal) {
                          return (
                            <Link 
                              to={`/goals/${linkedGoal.id}`}
                              className={`text-sm mb-2 inline-block hover:underline ${
                                isCompleted ? 'text-gray-400' : 'text-purple-600 hover:text-purple-700'
                              }`}
                            >
                              🎯 {linkedGoal.goal}
                            </Link>
                          );
                        }
                        return (
                          <p className={`text-sm mb-2 ${
                            isCompleted ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            {task.goal}
                          </p>
                        );
                      })()}
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        {task.due_date && (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            {new Date(task.due_date).toLocaleDateString('en-US', { 
                              month: 'short', 
                              day: 'numeric' 
                            })}
                          </div>
                        )}
                        {task.calendar_scheduling?.scheduled && task.calendar_scheduling.scheduled.length > 0 && (
                          <div className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" />
                            {new Date(task.calendar_scheduling.scheduled[0].start_time).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                              hour12: false
                            })}
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <span>{task.time_hours * 60} min</span>
                        </div>
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded font-medium ml-auto flex items-center gap-1">
                          <Sparkles className="w-3 h-3" /> AI
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="bg-white rounded-xl p-12 border border-gray-200 text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ListTodo className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2 text-xl">No Tasks Found</h3>
              <p className="text-gray-500 mb-6">
                {searchQuery || filterTab !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Create your first task to get started'}
              </p>
              {!searchQuery && filterTab === 'all' && (
                <Button
                  onClick={() => setTaskDialogOpen(true)}
                  className="bg-gray-900 hover:bg-gray-800"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Create Your First Task
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Task Dialog */}
      <NewTaskDialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen} onTaskCreated={loadData} />
    </div>
  );
}
