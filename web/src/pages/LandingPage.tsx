import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Brain, Calendar, Target, TrendingUp, Sparkles, CheckCircle2, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from "@/contexts/AuthContext";
import { useEffect, useState } from "react";

const LandingPage = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, navigate]);

  const handleGoogleSignIn = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      console.log('Google Sign-In successful, access token received');
      setIsLoggingIn(true);
      try {
        // Send the access token to backend for authentication
        console.log('Sending access token to backend...');
        await login(tokenResponse.access_token, tokenResponse.expires_in);
        console.log('Login successful, navigating to dashboard...');
        navigate("/dashboard");
      } catch (error) {
        console.error('Authentication error:', error);
        alert('Authentication failed. Check console for details.');
      } finally {
        setIsLoggingIn(false);
      }
    },
    onError: () => {
      console.error('Login Failed');
    },
    scope: 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events'
  });

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Brain className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">PolyLearner</span>
          </div>
          {!isAuthenticated && (
            <Button onClick={handleGoogleSignIn} size="sm" disabled={isLoggingIn}>
              {isLoggingIn ? 'Signing in...' : 'Sign In'}
            </Button>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm mb-6">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Learning Assistant</span>
          </div>
          
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6">
            Master Multiple Skills with
            <span className="block mt-2 bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
              Intelligent Task Management
            </span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            PolyLearner uses AI to help you balance multiple learning goals, optimize your schedule, and track your progress—all in one place.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button onClick={handleGoogleSignIn} size="lg" className="w-full sm:w-auto gap-2" disabled={isLoggingIn}>
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              {isLoggingIn ? 'Signing in...' : 'Continue with Google'}
            </Button>
            <Button onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })} size="lg" variant="outline" className="w-full sm:w-auto">
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 bg-card border-border">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Brain className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">AI Recommendations</h3>
            <p className="text-muted-foreground">
              Get personalized task suggestions based on your goals, schedule, and cognitive load patterns.
            </p>
          </Card>

          <Card className="p-6 bg-card border-border">
            <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center mb-4">
              <Calendar className="w-6 h-6 text-green-500" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Smart Scheduling</h3>
            <p className="text-muted-foreground">
              Automatically schedule tasks during your peak focus hours for maximum productivity.
            </p>
          </Card>

          <Card className="p-6 bg-card border-border">
            <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center mb-4">
              <TrendingUp className="w-6 h-6 text-purple-500" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">Progress Tracking</h3>
            <p className="text-muted-foreground">
              Monitor your completion rates, focus time, and weekly goals with detailed analytics.
            </p>
          </Card>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="container mx-auto px-4 py-20 bg-card/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-foreground mb-12">How It Works</h2>
          
          <div className="space-y-8">
            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
                  1
                </div>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Set Your Goals</h3>
                <p className="text-muted-foreground">
                  Define your weekly learning objectives and long-term goals. Whether it's mastering a new programming language, learning design principles, or studying for exams—PolyLearner adapts to your needs.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
                  2
                </div>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Create Tasks</h3>
                <p className="text-muted-foreground">
                  Break down your goals into actionable tasks. Assign categories, priorities, time estimates, and deadlines. Our AI analyzes your inputs to understand your learning patterns.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
                  3
                </div>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Follow AI Guidance</h3>
                <p className="text-muted-foreground">
                  Receive personalized recommendations on what to work on next, when to schedule breaks, and how to optimize your study sessions based on your cognitive load and progress.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
                  4
                </div>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Track Progress</h3>
                <p className="text-muted-foreground">
                  Monitor your completion rates, focus time, and weekly achievements. Visualize your learning journey with detailed analytics and insights.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features List */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-foreground mb-12">Everything You Need</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-1">Cognitive Load Tracking</h4>
                <p className="text-muted-foreground text-sm">Monitor your mental capacity and avoid burnout</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-1">Focus Time Optimization</h4>
                <p className="text-muted-foreground text-sm">Identify and leverage your peak productivity hours</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-1">Multi-Goal Management</h4>
                <p className="text-muted-foreground text-sm">Balance multiple learning objectives simultaneously</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-1">Intelligent Scheduling</h4>
                <p className="text-muted-foreground text-sm">Auto-schedule tasks based on priority and availability</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-1">Progress Analytics</h4>
                <p className="text-muted-foreground text-sm">Detailed metrics and visualizations of your journey</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-semibold text-foreground mb-1">Weekly Reviews</h4>
                <p className="text-muted-foreground text-sm">Reflect on achievements and adjust strategies</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center bg-gradient-to-r from-primary/10 to-purple-500/10 rounded-2xl p-12 border border-border">
          <Zap className="w-16 h-16 mx-auto mb-6 text-primary" />
          <h2 className="text-4xl font-bold text-foreground mb-4">Ready to Start Learning Smarter?</h2>
          <p className="text-xl text-muted-foreground mb-8">
            Join PolyLearner today and transform the way you manage your learning journey.
          </p>
          <Button onClick={handleGoogleSignIn} size="lg" className="gap-2" disabled={isLoggingIn}>
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {isLoggingIn ? 'Signing in...' : 'Get Started with Google'}
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-primary flex items-center justify-center">
                <Brain className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">PolyLearner</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 PolyLearner. AI-powered learning management.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
