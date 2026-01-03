import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Sparkles, CheckCircle2, XCircle, Lightbulb, Target, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { validateGoal, suggestTasks, createTasksFromSuggestions, type GoalSubmission, type GoalValidationResponse, type TaskSuggestionResponse, type SuggestedTask } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

type Step = 'intro' | 'goal-input' | 'validation' | 'tasks' | 'review';

export default function GoalOnboarding() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const [step, setStep] = useState<Step>('intro');
  const [loading, setLoading] = useState(false);
  
  // Redirect to landing page if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);
  
  // Form data
  const [goal, setGoal] = useState('');
  const [originalGoalFromValidation, setOriginalGoalFromValidation] = useState('');
  const [goalId, setGoalId] = useState<number | null>(null);
  
  // Validation result
  const [validationResult, setValidationResult] = useState<GoalValidationResponse | null>(null);
  
  // Task suggestions
  const [taskSuggestions, setTaskSuggestions] = useState<TaskSuggestionResponse | null>(null);
  const [selectedTasks, setSelectedTasks] = useState<Set<number>>(new Set());

  const handleValidateGoal = async () => {
    if (!goal.trim()) return;
    
    setLoading(true);
    try {
      const submission: GoalSubmission = {
        goal: goal.trim(),
        goal_id: goalId || undefined,  // Pass existing goal_id if we have one
      };
      
      const result = await validateGoal(submission);
      setValidationResult(result);
      setGoalId(result.goal_id);  // Store the goal_id from validation
      setOriginalGoalFromValidation(goal.trim());  // Store original goal to detect changes
      setStep('validation');
    } catch (error) {
      console.error('Goal analysis error:', error);
      
      // Create a fallback result that allows user to proceed
      // Note: No goal_id since validation failed - will be created when generating tasks
      const fallbackResult: GoalValidationResponse = {
        goal_id: 0,  // Placeholder - will be created during task generation
        is_valid: false,
        validation_details: {
          specific: goal.length > 20,
          measurable: /\d+|hours|weeks|projects?|by|until/i.test(goal),
          achievable: true,
          relevant: true,
          time_bound: /by|until|within|in \d+/i.test(goal)
        },
        feedback: "We're having trouble connecting to our AI service, but you can still proceed! Here are some tips to make your goal even better.",
        suggestions: [
          "Add specific numbers or milestones (e.g., '3 projects', '40 hours')",
          "Include a clear deadline or timeframe",
          "Specify what success looks like"
        ],
        refined_versions: [
          {
            goal: goal.trim(),
            improvement: "Your original goal",
            why_better: "Start with what you have and refine as you go"
          }
        ]
      };
      
      setValidationResult(fallbackResult);
      setGoalId(null);  // Reset goal_id since validation failed
      setOriginalGoalFromValidation(goal.trim());  // Store original goal to detect changes
      setStep('validation');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateTasks = async () => {
    if (!goal.trim()) return;
    
    setLoading(true);
    try {
      const submission: GoalSubmission = {
        goal: goal.trim(),
        goal_id: goalId || undefined,  // Pass the goal_id from validation to update existing goal
      };
      
      const result = await suggestTasks(submission);
      setGoalId(result.goal_id);  // Update with returned goal_id (should be same as before)
      setTaskSuggestions(result);
      // Select all tasks by default
      setSelectedTasks(new Set(result.suggested_tasks.map((_, idx) => idx)));
      setStep('tasks');
    } catch (error: any) {
      console.error('Task generation error:', error);
      // Still show an alert since we can't proceed without tasks
      const errorMsg = error.message || 'Unable to generate task suggestions at this time. Please try again or contact support if the issue persists.';
      alert(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTasks = async () => {
    if (!taskSuggestions || goalId === null) return;
    
    setLoading(true);
    try {
      const tasksToCreate = taskSuggestions.suggested_tasks.filter((_, idx) => selectedTasks.has(idx));
      const result = await createTasksFromSuggestions(tasksToCreate, goalId);  // Pass the goal_id
      
      // Check for calendar permission errors
      let hasCalendarError = false;
      if (result && Array.isArray(result)) {
        for (const task of result) {
          if (task.calendar_scheduling?.error) {
            hasCalendarError = true;
            break;
          }
        }
      }
      
      if (hasCalendarError) {
        toast({
          title: "Tasks Created (Calendar Access Required)",
          description: "Your tasks were created but couldn't be scheduled. Please sign out and sign back in, granting calendar permissions to enable auto-scheduling.",
          variant: "destructive",
          duration: 8000,
        });
      } else {
        toast({
          title: "Success!",
          description: "Your tasks have been created and scheduled on your calendar.",
          duration: 4000,
        });
      }
      
      setStep('review');
    } catch (error) {
      console.error('Task creation error:', error);
      toast({
        title: "Error",
        description: "Unable to create tasks at this time. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleTaskSelection = (idx: number) => {
    const newSelected = new Set(selectedTasks);
    if (newSelected.has(idx)) {
      newSelected.delete(idx);
    } else {
      newSelected.add(idx);
    }
    setSelectedTasks(newSelected);
  };

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Progress indicator */}
        <div className="mb-8 flex items-center justify-center gap-2">
          {['intro', 'goal-input', 'validation', 'tasks', 'review'].map((s, idx) => (
            <div key={s} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                s === step ? 'bg-primary text-primary-foreground' :
                ['intro', 'goal-input', 'validation', 'tasks', 'review'].indexOf(step) > idx ? 'bg-success text-white' :
                'bg-muted text-muted-foreground'
              }`}>
                {idx + 1}
              </div>
              {idx < 4 && (
                <div className={`w-12 h-1 ${
                  ['intro', 'goal-input', 'validation', 'tasks', 'review'].indexOf(step) > idx ? 'bg-success' : 'bg-muted'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Intro Step */}
        {step === 'intro' && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <Target className="w-8 h-8 text-primary" />
                <CardTitle className="text-3xl">Welcome to PolyLearner!</CardTitle>
              </div>
              <CardDescription className="text-base">
                Let's start by setting a clear, measurable goal for your learning journey.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-start gap-3 p-4 bg-secondary/50 rounded-lg">
                  <Sparkles className="w-5 h-5 text-primary mt-1" />
                  <div>
                    <h4 className="font-semibold mb-1">SMART Goals</h4>
                    <p className="text-sm text-muted-foreground">
                      We'll help you create goals that are <strong>Specific, Measurable, Achievable, Relevant, and Time-bound</strong>.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-4 bg-secondary/50 rounded-lg">
                  <Lightbulb className="w-5 h-5 text-warning mt-1" />
                  <div>
                    <h4 className="font-semibold mb-1">AI-Powered Breakdown</h4>
                    <p className="text-sm text-muted-foreground">
                      Our AI will break down your goal into actionable tasks optimized for your productivity.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-4 bg-secondary/50 rounded-lg">
                  <Zap className="w-5 h-5 text-success mt-1" />
                  <div>
                    <h4 className="font-semibold mb-1">Energy Optimization</h4>
                    <p className="text-sm text-muted-foreground">
                      Tasks are scheduled based on your peak energy times and productivity science.
                    </p>
                  </div>
                </div>
              </div>

              <Button onClick={() => setStep('goal-input')} size="lg" className="w-full">
                Get Started <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Goal Input Step */}
        {step === 'goal-input' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">What's your goal?</CardTitle>
              <CardDescription>
                Describe what you want to achieve. Our AI will help you refine it and break it down into actionable tasks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="goal">Your Goal</Label>
                <Textarea
                  id="goal"
                  placeholder="Example: I want to complete my AWS certification"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  rows={6}
                  className="resize-none"
                />
                <p className="text-xs text-muted-foreground">
                  💡 Tip: Just describe what you want to accomplish. We'll help you make it specific and measurable.
                </p>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('intro')}>
                  Back
                </Button>
                <Button onClick={handleValidateGoal} disabled={!goal.trim() || loading} className="flex-1">
                  {loading ? 'Analyzing...' : 'Analyze Goal'} <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Validation Result Step */}
        {step === 'validation' && validationResult && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Sparkles className="w-8 h-8 text-primary" />
                <CardTitle className="text-2xl">
                  {validationResult.is_valid ? 'Great Goal!' : 'Here are some refined versions'}
                </CardTitle>
              </div>
              <CardDescription>
                {validationResult.is_valid 
                  ? 'Your goal meets SMART criteria! You can proceed or select a refined version below.'
                  : 'Your goal has potential! Here are refined versions to help you make it even better.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-4 bg-secondary/50 rounded-lg">
                <p className="text-sm leading-relaxed">{validationResult.feedback}</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {Object.entries(validationResult.validation_details).map(([key, value]) => (
                  <div key={key} className="flex flex-col items-center gap-2 p-3 bg-card border rounded-lg">
                    {value ? (
                      <CheckCircle2 className="w-5 h-5 text-success" />
                    ) : (
                      <XCircle className="w-5 h-5 text-muted-foreground" />
                    )}
                    <span className="text-xs font-medium capitalize">{key.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>

              {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Lightbulb className="w-4 h-4" />
                    Tips for Improvement
                  </h4>
                  <ul className="space-y-2">
                    {validationResult.suggestions.map((suggestion, idx) => (
                      <li key={idx} className="text-sm flex items-start gap-2 pl-6">
                        <span className="text-primary">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Refined Goal Versions */}
              {validationResult.refined_versions && validationResult.refined_versions.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Choose a Goal Version
                  </h4>
                  <div className="space-y-3">
                    {validationResult.refined_versions.map((version, idx) => (
                      <div
                        key={idx}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-primary ${
                          goal === version.goal ? 'border-primary bg-primary/5' : 'border-border'
                        }`}
                        onClick={() => setGoal(version.goal)}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                            goal === version.goal ? 'bg-primary text-primary-foreground' : 'bg-secondary text-foreground'
                          }`}>
                            {idx + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium mb-1">{version.goal}</p>
                            <p className="text-xs text-muted-foreground mb-1">
                              <strong>Improvement:</strong> {version.improvement}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              <strong>Why better:</strong> {version.why_better}
                            </p>
                          </div>
                          {goal === version.goal && (
                            <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('goal-input')}>
                  Edit Goal
                </Button>
                <Button 
                  onClick={handleGenerateTasks} 
                  disabled={loading} 
                  className="flex-1"
                >
                  {loading ? 'Generating Tasks...' : 'Generate Task Breakdown'} <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Task Suggestions Step */}
        {step === 'tasks' && taskSuggestions && (
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">Your Personalized Task Plan</CardTitle>
              <CardDescription>
                Review and select the tasks you want to add to your schedule
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Total Tasks</p>
                  <p className="text-2xl font-bold">{taskSuggestions.suggested_tasks.length}</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Total Hours</p>
                  <p className="text-2xl font-bold">{taskSuggestions.estimated_total_hours}h</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">High Energy</p>
                  <p className="text-2xl font-bold">{taskSuggestions.energy_allocation.high_energy_hours}h</p>
                </div>
              </div>

              {/* Strategy */}
              <div className="p-4 bg-primary/10 border border-primary rounded-lg">
                <h4 className="font-semibold mb-2 text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Scheduling Strategy
                </h4>
                <p className="text-sm">{taskSuggestions.scheduling_strategy}</p>
              </div>

              {/* Task List */}
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {taskSuggestions.suggested_tasks.map((task, idx) => (
                  <div
                    key={idx}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedTasks.has(idx) ? 'bg-primary/10 border-primary' : 'bg-card hover:bg-secondary/50'
                    }`}
                    onClick={() => toggleTaskSelection(idx)}
                  >
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={selectedTasks.has(idx)}
                        onCheckedChange={() => toggleTaskSelection(idx)}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold mb-1">{task.title}</h4>
                        <p className="text-sm text-muted-foreground mb-2">{task.goal}</p>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline">{task.category}</Badge>
                          <Badge variant="outline">{task.time_hours}h</Badge>
                          <Badge variant="outline" className="capitalize">{task.energy_level} energy</Badge>
                          <Badge variant="secondary">Priority {task.priority}</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('validation')}>
                  Back
                </Button>
                <Button
                  onClick={handleCreateTasks}
                  disabled={selectedTasks.size === 0 || loading}
                  className="flex-1"
                >
                  {loading ? 'Creating Tasks...' : `Create ${selectedTasks.size} Task${selectedTasks.size !== 1 ? 's' : ''}`}
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Review Step */}
        {step === 'review' && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-8 h-8 text-success" />
                <CardTitle className="text-2xl">You're All Set!</CardTitle>
              </div>
              <CardDescription>
                Your tasks have been created and are ready to be scheduled.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="p-6 bg-success/10 border border-success rounded-lg text-center">
                <p className="text-lg font-semibold mb-2">🎉 Goal Created Successfully!</p>
                <p className="text-sm text-muted-foreground">
                  {selectedTasks.size} tasks have been added to your dashboard
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="font-semibold">Next Steps:</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">1.</span>
                    <span>Review your tasks on the dashboard</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">2.</span>
                    <span>AI will generate an optimized schedule based on your energy levels</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">3.</span>
                    <span>Start working on your highest priority tasks</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">4.</span>
                    <span>Track your progress and adjust as needed</span>
                  </li>
                </ul>
              </div>

              <Button onClick={() => navigate('/dashboard')} size="lg" className="w-full">
                Go to Dashboard <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
