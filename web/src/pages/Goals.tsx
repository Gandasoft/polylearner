import { useState, useEffect } from "react";
import { Target, ListTodo, MessageCircle, User, TrendingUp, Sparkles, ArrowRight, Search, Plus, Filter } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getGoals, getTasks, type Goal, type Task } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

type FilterTab = 'all' | 'active' | 'completed' | 'paused';

export default function Goals() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadingGoals, setLoadingGoals] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTab, setFilterTab] = useState<FilterTab>('all');
  const [categoryFilter, setCategoryFilter] = useState('all');

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
    setLoadingGoals(true);
    setLoadingTasks(true);
    
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
  }

  // Filter goals based on search and filters
  const filteredGoals = goals.filter(goal => {
    // Search filter
    if (searchQuery && !goal.goal.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Status filter
    const goalTasks = tasks.filter(t => t.goal === goal.goal);
    const completedCount = goalTasks.filter(t => t.review).length;
    const progress = goalTasks.length > 0 ? (completedCount / goalTasks.length) * 100 : 0;
    
    if (filterTab === 'active' && (progress >= 100 || goalTasks.length === 0)) {
      return false;
    }
    if (filterTab === 'completed' && progress < 100) {
      return false;
    }
    // Note: 'paused' status not yet implemented in backend
    if (filterTab === 'paused') {
      return false;
    }

    return true;
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
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 text-purple-600 font-medium"
          >
            <Target className="w-5 h-5" />
            Goals
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
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
              <Target className="w-8 h-8 text-purple-600" />
              <h1 className="text-3xl font-bold text-gray-900">My Goals</h1>
            </div>
            <p className="text-gray-500">{goals.length} goals total</p>
          </div>
          <Button
            onClick={() => navigate('/onboarding')}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 gap-2"
          >
            <Plus className="w-5 h-5" />
            New Goal
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              placeholder="Search goals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-white border-gray-200"
            />
          </div>

          {/* Filter Tabs and Category Filter */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
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
                onClick={() => setFilterTab('active')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filterTab === 'active'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Active
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
              <button
                onClick={() => setFilterTab('paused')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filterTab === 'paused'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Paused
              </button>
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[180px] bg-white border-gray-200">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="learning">Learning</SelectItem>
                  <SelectItem value="health">Health</SelectItem>
                  <SelectItem value="career">Career</SelectItem>
                  <SelectItem value="personal">Personal</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Goals Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {loadingGoals ? (
            <div className="col-span-2 bg-white rounded-2xl p-12 border border-gray-200 text-center">
              <p className="text-gray-500">Loading goals...</p>
            </div>
          ) : filteredGoals.length > 0 ? (
            filteredGoals.map((goal) => {
              const goalTasks = tasks.filter(t => t.goal === goal.goal);
              const completedGoalTasks = goalTasks.filter(t => t.review).length;
              const progress = goalTasks.length > 0 ? (completedGoalTasks / goalTasks.length) * 100 : 0;
              
              // Determine category and priority based on goal content (simplified)
              const category = goal.goal.toLowerCase().includes('spanish') || goal.goal.toLowerCase().includes('learn') 
                ? 'learning' 
                : 'health';
              const priority = goal.goal.toLowerCase().includes('marathon') || goal.goal.toLowerCase().includes('urgent')
                ? 'high'
                : 'medium';
              
              return (
                <div
                  key={goal.id}
                  className="bg-white rounded-2xl p-6 border border-gray-200 hover:border-purple-300 transition-all cursor-pointer hover:shadow-md"
                  onClick={() => navigate(`/goals/${goal.id}`)}
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Target className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="font-semibold text-gray-900 text-lg">
                          {goal.goal.length > 50 ? goal.goal.substring(0, 50) + '...' : goal.goal}
                        </h3>
                        <button className="text-gray-400 hover:text-gray-600">
                          <ArrowRight className="w-5 h-5" />
                        </button>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          category === 'learning' 
                            ? 'bg-purple-100 text-purple-700' 
                            : 'bg-teal-100 text-teal-700'
                        }`}>
                          {category}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          priority === 'high'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          {priority}
                        </span>
                      </div>
                      
                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                        {goal.goal}
                      </p>
                      
                      <div className="mb-3">
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
                </div>
              );
            })
          ) : (
            <div className="col-span-2 bg-white rounded-2xl p-12 border border-gray-200 text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2 text-xl">No Goals Found</h3>
              <p className="text-gray-500 mb-6">
                {searchQuery || filterTab !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Create your first goal to get started on your learning journey'}
              </p>
              {!searchQuery && filterTab === 'all' && (
                <Button
                  onClick={() => navigate('/onboarding')}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Create Your First Goal
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
