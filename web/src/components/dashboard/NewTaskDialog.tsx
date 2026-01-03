import { useState, useEffect } from "react";
import { X, Sparkles, Calendar, Clock, Flag, UserPlus, Hash, AlertCircle, Camera, Mic, ArrowUp, FolderOpen } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { createTask, TaskCreate, getGoals, Goal } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface NewTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated?: () => void;
}

export function NewTaskDialog({ open, onOpenChange, onTaskCreated }: NewTaskDialogProps) {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [formData, setFormData] = useState<Partial<TaskCreate>>({
    title: "",
    category: "admin",
    time_hours: 1,
    goal: "",
    artifact: "notes",
    priority: 5,
  });

  useEffect(() => {
    if (open) {
      // Fetch goals when dialog opens
      getGoals()
        .then(setGoals)
        .catch(err => console.error("Failed to fetch goals:", err));
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!formData.title || !formData.goal) {
      alert("Please fill in title and goal");
      return;
    }

    try {
      setLoading(true);
      const response = await createTask(formData as TaskCreate);
      
      // Check for calendar permission errors
      if (response.calendar_scheduling?.error) {
        toast({
          title: "Calendar Access Required",
          description: "Please sign out and sign back in, granting calendar permissions to enable auto-scheduling.",
          variant: "destructive",
          duration: 6000,
        });
      } else if (response.calendar_scheduling?.scheduled) {
        toast({
          title: "Task Scheduled",
          description: `Task successfully scheduled on your calendar for ${new Date(response.calendar_scheduling.scheduled[0]?.start_time || '').toLocaleString()}.`,
          duration: 4000,
        });
      }
      
      setFormData({
        title: "",
        category: "admin",
        time_hours: 1,
        goal: "",
        artifact: "notes",
        priority: 5,
      });
      onOpenChange(false);
      if (onTaskCreated) {
        onTaskCreated();
      }
    } catch (error) {
      console.error("Failed to create task:", error);
      toast({
        title: "Error",
        description: "Failed to create task. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md p-0 gap-0 bg-white border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <button onClick={() => onOpenChange(false)} className="text-gray-500 hover:text-gray-900">
            <X className="w-5 h-5" />
          </button>
          <h2 className="font-semibold text-gray-900">New Task</h2>
          <Button 
            size="sm" 
            className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Saving..." : "Save"}
          </Button>
        </div>

        {/* Task Selection */}
        <div className="px-4 pb-4">
          <Select 
            value={formData.goal} 
            onValueChange={(value) => setFormData({ ...formData, goal: value })}
          >
            <SelectTrigger className="bg-transparent border-0 p-0 h-auto focus:ring-0 text-sm text-gray-900">
              <SelectValue placeholder="Select a goal for this task" className="text-gray-400" />
            </SelectTrigger>
            <SelectContent>
              {goals.length === 0 ? (
                <SelectItem value="no-goals" disabled>No goals available</SelectItem>
              ) : (
                goals.map((goal) => (
                  <SelectItem key={goal.id} value={goal.goal}>
                    {goal.goal}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Goal Input */}
        <div className="px-4 pb-4">
          <Textarea 
            placeholder="What is the goal of this task?"
            className="text-sm border-0 p-0 resize-none focus-visible:ring-0 placeholder:text-gray-400 min-h-[40px] bg-transparent text-gray-900"
            value={formData.goal}
            onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
          />
        </div>

        {/* AI Suggestion */}
        <div className="mx-4 mb-4 bg-purple-50 rounded-xl p-4 border border-purple-200">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span className="text-xs font-medium text-purple-600 uppercase">Smart Defaults</span>
            </div>
          </div>
          <p className="text-sm text-gray-700">
            Set category, time, and priority for optimal scheduling
          </p>
        </div>

        {/* Details Section */}
        <div className="px-4 pb-4">
          <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-3">Details</h4>
          
          {/* Category & Priority */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-sm text-gray-600 mb-2 block">Category</label>
              <Select 
                value={formData.category} 
                onValueChange={(value: any) => setFormData({ ...formData, category: value })}
              >
                <SelectTrigger className="bg-gray-50 border-0 rounded-xl h-11">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="research">Research</SelectItem>
                  <SelectItem value="coding">Coding</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="networking">Networking</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-2 block">Priority</label>
              <Select 
                value={formData.priority?.toString()} 
                onValueChange={(value) => setFormData({ ...formData, priority: parseInt(value) })}
              >
                <SelectTrigger className="bg-gray-50 border-0 rounded-xl h-11">
                  <div className="flex items-center gap-2">
                    <Flag className="w-4 h-4 text-gray-500" />
                    <SelectValue />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 - Lowest</SelectItem>
                  <SelectItem value="3">3 - Low</SelectItem>
                  <SelectItem value="5">5 - Medium</SelectItem>
                  <SelectItem value="7">7 - High</SelectItem>
                  <SelectItem value="10">10 - Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Time & Artifact */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-sm text-gray-600 mb-2 block">Time (hours)</label>
              <Select 
                value={formData.time_hours?.toString()} 
                onValueChange={(value) => setFormData({ ...formData, time_hours: parseFloat(value) })}
              >
                <SelectTrigger className="bg-gray-50 border-0 rounded-xl h-11">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <SelectValue />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0.25">15m</SelectItem>
                  <SelectItem value="0.5">30m</SelectItem>
                  <SelectItem value="1">1h</SelectItem>
                  <SelectItem value="2">2h</SelectItem>
                  <SelectItem value="4">4h</SelectItem>
                  <SelectItem value="8">8h</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-2 block">Artifact</label>
              <Select 
                value={formData.artifact} 
                onValueChange={(value: any) => setFormData({ ...formData, artifact: value })}
              >
                <SelectTrigger className="bg-gray-50 border-0 rounded-xl h-11">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-gray-500" />
                    <SelectValue />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="article">Article</SelectItem>
                  <SelectItem value="notes">Notes</SelectItem>
                  <SelectItem value="code">Code</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Due Date */}
          <div className="mb-4">
            <label className="text-sm text-gray-600 mb-2 block">Due Date (optional)</label>
            <Input
              type="date"
              className="bg-gray-50 border-0 rounded-xl h-11 text-gray-900"
              value={formData.due_date || ""}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            />
          </div>
        </div>

        {/* Bottom Toolbar */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-600">
              {formData.category && `${formData.category} • `}
              {formData.time_hours}h
            </span>
          </div>
          <Button
            size="sm"
            className="bg-purple-600 hover:bg-purple-700 rounded-full text-white"
            onClick={handleSubmit}
            disabled={loading || !formData.title || !formData.goal}
          >
            <ArrowUp className="w-4 h-4" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
