import { useState, useEffect, useRef } from "react";
import { Target, ListTodo, MessageCircle, User, TrendingUp, Sparkles, ArrowRight, ArrowLeft, Plus, Send } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuth } from "@/contexts/AuthContext";

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface CoachingSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

export default function Coach() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<CoachingSession[]>([]);
  const [currentSession, setCurrentSession] = useState<CoachingSession | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Redirect to landing page if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  async function loadSessions() {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/coach/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        const formattedSessions = data.map((session: any) => ({
          ...session,
          timestamp: new Date(session.timestamp),
          messages: session.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }));
        setSessions(formattedSessions);
        
        // Load the most recent session if available
        if (formattedSessions.length > 0) {
          setCurrentSession(formattedSessions[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load coaching sessions:', error);
    }
  }

  async function createNewSession() {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/coach/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: `Goal Coaching Session - ${new Date().toLocaleDateString()}`
        })
      });
      
      if (response.ok) {
        const newSession = await response.json();
        const formattedSession = {
          ...newSession,
          timestamp: new Date(newSession.timestamp),
          messages: []
        };
        setSessions([formattedSession, ...sessions]);
        setCurrentSession(formattedSession);
      }
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  }

  async function sendMessage() {
    if (!inputMessage.trim() || !currentSession || sendingMessage) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    // Update UI immediately with user message
    setCurrentSession({
      ...currentSession,
      messages: [...currentSession.messages, userMessage]
    });
    setInputMessage('');
    setSendingMessage(true);

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/coach/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: currentSession.id,
          message: userMessage.content
        })
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        };

        setCurrentSession({
          ...currentSession,
          messages: [...currentSession.messages, userMessage, assistantMessage]
        });

        // Update the session in the list
        setSessions(sessions.map(s => 
          s.id === currentSession.id 
            ? { ...s, messages: [...currentSession.messages, userMessage, assistantMessage] }
            : s
        ));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSendingMessage(false);
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
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
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-purple-50 text-purple-600 font-medium"
          >
            <MessageCircle className="w-5 h-5" />
            Coach
            <svg className="w-4 h-4 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
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
            onClick={createNewSession}
            className="w-full bg-white text-purple-600 rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-purple-50 transition-colors flex items-center justify-center gap-2"
          >
            Start Session
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Sessions Sidebar */}
      <div className="w-64 bg-white border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Sessions</h2>
            <button 
              onClick={createNewSession}
              className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
            >
              <Plus className="w-4 h-4" />
              New
            </button>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-2">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => setCurrentSession(session)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  currentSession?.id === session.id
                    ? 'bg-purple-50 border border-purple-200'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-2">
                  <MessageCircle className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {session.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {session.timestamp.toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                      })}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-border p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-gray-900">Goal Coach</h1>
                <p className="text-sm text-gray-500">Your AI-powered accountability partner</p>
              </div>
            </div>
          </div>
          <Button
            onClick={() => navigate('/onboarding')}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 gap-2"
          >
            <Sparkles className="w-4 h-4" />
            New Goal Setup
          </Button>
        </div>

        {/* Messages Area */}
        <ScrollArea className="flex-1 p-6">
          {!currentSession || currentSession.messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="w-10 h-10 text-purple-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Start a Coaching Session
                </h3>
                <p className="text-gray-500">
                  Tell me about your goals, and I'll help you break them down into actionable steps, 
                  stay motivated, and track your progress.
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {currentSession.messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-purple-600 text-white'
                        : 'bg-white border border-gray-200 text-gray-900'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-purple-200' : 'text-gray-400'
                    }`}>
                      {message.timestamp.toLocaleTimeString('en-US', { 
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                      })}
                    </p>
                  </div>
                  {message.role === 'user' && user?.picture && (
                    <img 
                      src={user.picture} 
                      alt={user.name}
                      className="w-8 h-8 rounded-full flex-shrink-0"
                    />
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="bg-white border-t border-border p-6">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end gap-3">
              <Input
                placeholder="Ask your coach anything..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={sendingMessage || !currentSession}
                className="flex-1 bg-gray-50 border-gray-200 rounded-xl px-4 py-3"
              />
              <Button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || sendingMessage || !currentSession}
                className="bg-gray-700 hover:bg-gray-800 rounded-xl px-4 py-3 h-auto"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
