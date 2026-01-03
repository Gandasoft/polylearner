import { useState, useEffect } from "react";
import { Target, ListTodo, MessageCircle, User, TrendingUp, Sparkles, ArrowRight, Trophy, Users, Zap } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

type TimeRange = 'all-time' | 'this-month' | 'this-week';

interface LeaderboardUser {
  id: number;
  name: string;
  email: string;
  avatar?: string;
  points: number;
  rank: number;
  streak: number;
  tasksCompleted: number;
}

interface LeaderboardStats {
  activeUsers: number;
  totalPoints: number;
  topStreak: number;
}

export default function Leaderboard() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState<TimeRange>('all-time');
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardUser[]>([]);
  const [stats, setStats] = useState<LeaderboardStats>({
    activeUsers: 0,
    totalPoints: 0,
    topStreak: 0
  });
  const [loadingData, setLoadingData] = useState(true);

  // Redirect to landing page if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      loadLeaderboardData();
    }
  }, [isAuthenticated, timeRange]);

  async function loadLeaderboardData() {
    setLoadingData(true);
    
    try {
      // In a real implementation, this would fetch from the backend
      // For now, we'll use empty data
      setLeaderboardData([]);
      setStats({
        activeUsers: 0,
        totalPoints: 0,
        topStreak: 0
      });
    } catch (error) {
      console.error('Failed to load leaderboard data:', error);
    } finally {
      setLoadingData(false);
    }
  }

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
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <User className="w-5 h-5" />
            Profile
          </Link>
          
          <Link
            to="/leaderboard"
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 text-purple-600 font-medium"
          >
            <TrendingUp className="w-5 h-5" />
            Leaderboard
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
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
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-500 to-purple-600 rounded-3xl mb-4">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Leaderboard</h1>
          <p className="text-gray-500">See how you rank among goal achievers</p>
        </div>

        {/* Rankings Section */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-white rounded-2xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Rankings</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setTimeRange('all-time')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    timeRange === 'all-time'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  All Time
                </button>
                <button
                  onClick={() => setTimeRange('this-month')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    timeRange === 'this-month'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  This Month
                </button>
                <button
                  onClick={() => setTimeRange('this-week')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    timeRange === 'this-week'
                      ? 'bg-gray-900 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  This Week
                </button>
              </div>
            </div>

            {/* Leaderboard List */}
            {loadingData ? (
              <div className="text-center py-20">
                <p className="text-gray-500">Loading leaderboard...</p>
              </div>
            ) : leaderboardData.length > 0 ? (
              <div className="space-y-3">
                {leaderboardData.map((leaderUser, index) => (
                  <div
                    key={leaderUser.id}
                    className={`flex items-center gap-4 p-4 rounded-xl transition-colors ${
                      leaderUser.id === user?.id
                        ? 'bg-purple-50 border-2 border-purple-200'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold ${
                      index === 0 ? 'bg-yellow-400 text-yellow-900' :
                      index === 1 ? 'bg-gray-300 text-gray-700' :
                      index === 2 ? 'bg-orange-400 text-orange-900' :
                      'bg-gray-200 text-gray-600'
                    }`}>
                      {leaderUser.rank}
                    </div>
                    
                    <div className="flex-1 flex items-center gap-3">
                      {leaderUser.avatar ? (
                        <img src={leaderUser.avatar} alt={leaderUser.name} className="w-10 h-10 rounded-full" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center text-white font-semibold">
                          {leaderUser.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div>
                        <p className="font-semibold text-gray-900">{leaderUser.name}</p>
                        <p className="text-sm text-gray-500">{leaderUser.tasksCompleted} tasks completed</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-2xl font-bold text-purple-600">{leaderUser.points}</p>
                      <p className="text-xs text-gray-500">points</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Trophy className="w-10 h-10 text-gray-300" />
                </div>
                <p className="text-gray-500">No users on the leaderboard yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Active Users */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 border border-blue-200">
            <div className="flex items-center justify-center w-12 h-12 bg-blue-500 rounded-full mb-4 mx-auto">
              <Users className="w-6 h-6 text-white" />
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 mb-2">{stats.activeUsers}</p>
              <p className="text-gray-600">Active Users</p>
            </div>
          </div>

          {/* Total Points */}
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6 border border-green-200">
            <div className="flex items-center justify-center w-12 h-12 bg-green-500 rounded-full mb-4 mx-auto">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 mb-2">{stats.totalPoints}</p>
              <p className="text-gray-600">Total Points</p>
            </div>
          </div>

          {/* Top Streak */}
          <div className="bg-gradient-to-br from-orange-50 to-yellow-100 rounded-2xl p-6 border border-orange-200">
            <div className="flex items-center justify-center w-12 h-12 bg-orange-500 rounded-full mb-4 mx-auto">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 mb-2">{stats.topStreak}</p>
              <p className="text-gray-600">Top Streak</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
