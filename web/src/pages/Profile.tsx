import { useState, useEffect } from "react";
import { Target, ListTodo, MessageCircle, User, TrendingUp, Sparkles, ArrowRight, Star, Award, Trophy, Flame, Settings as SettingsIcon } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getTasks, getGoals, type Task, type Goal } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

interface UserStats {
  level: number;
  points: number;
  pointsToNextLevel: number;
  totalPoints: number;
  currentStreak: number;
  bestStreak: number;
  tasksCompleted: number;
  goalsAchieved: number;
  badgesEarned: number;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  earned: boolean;
  earnedDate?: Date;
}

export default function Profile() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [activeTab, setActiveTab] = useState('achievements');

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
    setLoadingData(true);
    
    try {
      const [tasksData, goalsData] = await Promise.all([
        getTasks().catch(() => []),
        getGoals().catch(() => [])
      ]);
      
      setTasks(tasksData);
      setGoals(goalsData);
    } catch (error) {
      console.error('Failed to load profile data:', error);
    } finally {
      setLoadingData(false);
    }
  }

  // Calculate user stats
  const calculateStats = (): UserStats => {
    const completedTasks = tasks.filter(t => t.review).length;
    const totalTasks = tasks.length;
    
    // Points calculation: 10 points per completed task
    const totalPoints = completedTasks * 10;
    
    // Level calculation: 150 points per level
    const pointsPerLevel = 150;
    const level = Math.floor(totalPoints / pointsPerLevel) + 1;
    const pointsInCurrentLevel = totalPoints % pointsPerLevel;
    const pointsToNextLevel = pointsPerLevel - pointsInCurrentLevel;
    
    // Streak calculation (simplified - would need date tracking in real implementation)
    const currentStreak = 0; // Would calculate from task completion dates
    const bestStreak = 0;
    
    // Goals achieved calculation
    const goalsAchieved = goals.filter(g => {
      const goalTasks = tasks.filter(t => t.goal === g.goal);
      const completedGoalTasks = goalTasks.filter(t => t.review).length;
      return goalTasks.length > 0 && completedGoalTasks === goalTasks.length;
    }).length;
    
    return {
      level,
      points: pointsInCurrentLevel,
      pointsToNextLevel,
      totalPoints,
      currentStreak,
      bestStreak,
      tasksCompleted: completedTasks,
      goalsAchieved,
      badgesEarned: 0 // Would calculate from achievements
    };
  };

  const stats = calculateStats();
  
  // Get level title
  const getLevelTitle = (level: number): string => {
    if (level === 1) return "Beginner";
    if (level <= 3) return "Learner";
    if (level <= 5) return "Practitioner";
    if (level <= 10) return "Expert";
    return "Master";
  };

  // Get next milestone for streak
  const getNextMilestone = (currentStreak: number): number => {
    const milestones = [3, 7, 14, 30, 60, 90, 180, 365];
    return milestones.find(m => m > currentStreak) || milestones[milestones.length - 1];
  };

  const achievements: Achievement[] = [
    {
      id: "first-task",
      title: "First Steps",
      description: "Complete your first task",
      icon: "✓",
      earned: stats.tasksCompleted >= 1,
      earnedDate: stats.tasksCompleted >= 1 ? new Date() : undefined
    },
    {
      id: "five-tasks",
      title: "Getting Started",
      description: "Complete 5 tasks",
      icon: "🎯",
      earned: stats.tasksCompleted >= 5,
      earnedDate: stats.tasksCompleted >= 5 ? new Date() : undefined
    },
    {
      id: "first-goal",
      title: "Goal Setter",
      description: "Create your first goal",
      icon: "🎪",
      earned: goals.length >= 1,
      earnedDate: goals.length >= 1 ? new Date() : undefined
    }
  ];

  const earnedAchievements = achievements.filter(a => a.earned);

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
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 text-purple-600 font-medium"
          >
            <User className="w-5 h-5" />
            Profile
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
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
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <User className="w-8 h-8 text-purple-600" />
            <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
          </div>
          <p className="text-gray-500">Track your progress and achievements</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Level Card */}
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-6 border border-purple-200">
            <div className="flex items-center gap-2 mb-3">
              <Star className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-700">Level {stats.level}</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">{getLevelTitle(stats.level)}</h3>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Progress to Level {stats.level + 1}</span>
                <span className="font-semibold text-gray-900">{stats.points} / 150</span>
              </div>
              <div className="w-full h-2 bg-purple-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-purple-600 rounded-full transition-all"
                  style={{ width: `${(stats.points / 150) * 100}%` }}
                />
              </div>
              <p className="text-xs text-purple-700 flex items-center gap-1 mt-3">
                <ArrowRight className="w-3 h-3" />
                {stats.pointsToNextLevel} points to next level
              </p>
            </div>
            
            <div className="mt-4 pt-4 border-t border-purple-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Points</span>
                <span className="text-2xl font-bold text-purple-600">{stats.totalPoints}</span>
              </div>
            </div>
          </div>

          {/* Streak Card */}
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 text-white">
            <div className="flex items-center gap-2 mb-3">
              <Flame className="w-5 h-5 text-orange-400" />
              <span className="text-sm font-medium text-gray-300">Current Streak</span>
            </div>
            <div className="flex items-baseline gap-2 mb-4">
              <h3 className="text-4xl font-bold">{stats.currentStreak}</h3>
              <span className="text-lg text-gray-400">days</span>
            </div>
            
            <div className="inline-block px-3 py-1 bg-gray-700 rounded-full text-sm text-gray-300 mb-6">
              {stats.currentStreak === 0 ? 'Starting' : 'On Fire! 🔥'}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                  <Trophy className="w-3 h-3 text-yellow-500" />
                  Best Streak
                </div>
                <p className="text-lg font-semibold">{stats.bestStreak} days</p>
              </div>
              <div>
                <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                  <Target className="w-3 h-3 text-green-400" />
                  Next Milestone
                </div>
                <p className="text-lg font-semibold">{getNextMilestone(stats.currentStreak)} days</p>
              </div>
            </div>
          </div>

          {/* Statistics Overview Card */}
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-6 border border-blue-200">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">Statistics</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Overview</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Tasks Completed</span>
                <span className="text-2xl font-bold text-gray-900">{stats.tasksCompleted}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Goals Achieved</span>
                <span className="text-2xl font-bold text-gray-900">{stats.goalsAchieved}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Badges Earned</span>
                <span className="text-2xl font-bold text-gray-900">{stats.badgesEarned}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs Section */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="bg-transparent border-b border-gray-200 rounded-none p-0 h-auto space-x-6 mb-6">
            <TabsTrigger 
              value="achievements"
              className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-gray-900 rounded-none px-0 pb-3"
            >
              <Trophy className="w-4 h-4 mr-2" />
              Achievements
            </TabsTrigger>
            <TabsTrigger 
              value="badges"
              className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-gray-900 rounded-none px-0 pb-3"
            >
              <Award className="w-4 h-4 mr-2" />
              Badges
            </TabsTrigger>
            <TabsTrigger 
              value="settings"
              className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-gray-900 rounded-none px-0 pb-3"
            >
              <SettingsIcon className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="achievements" className="mt-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-6">
                <Trophy className="w-5 h-5 text-yellow-600" />
                <h3 className="font-semibold text-gray-900">Recent Achievements</h3>
              </div>
              
              {loadingData ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">Loading achievements...</p>
                </div>
              ) : earnedAchievements.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {earnedAchievements.map(achievement => (
                    <div key={achievement.id} className="bg-gradient-to-br from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-4">
                      <div className="text-4xl mb-2">{achievement.icon}</div>
                      <h4 className="font-semibold text-gray-900 mb-1">{achievement.title}</h4>
                      <p className="text-sm text-gray-600 mb-2">{achievement.description}</p>
                      {achievement.earnedDate && (
                        <p className="text-xs text-gray-500">
                          Earned {achievement.earnedDate.toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trophy className="w-10 h-10 text-gray-300" />
                  </div>
                  <p className="text-gray-500">
                    No achievements yet. Complete tasks to earn badges!
                  </p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="badges" className="mt-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-6">
                <Award className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Your Badges</h3>
              </div>
              
              <div className="text-center py-12">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Award className="w-10 h-10 text-gray-300" />
                </div>
                <p className="text-gray-500">
                  No badges earned yet. Keep completing tasks to unlock badges!
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="mt-6">
            <div className="bg-white rounded-2xl p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-6">
                <SettingsIcon className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold text-gray-900">Profile Settings</h3>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={user?.name || ''}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  />
                </div>
                
                <p className="text-sm text-gray-500">
                  Profile settings are managed through your Google account.
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
