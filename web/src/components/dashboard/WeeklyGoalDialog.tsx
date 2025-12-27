import { useState } from "react";
import { X, Target, Calendar, Sparkles } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { createWeeklyGoal, WeeklyGoalCreate } from "@/lib/api";

interface WeeklyGoalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGoalCreated?: () => void;
}

export function WeeklyGoalDialog({ open, onOpenChange, onGoalCreated }: WeeklyGoalDialogProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<WeeklyGoalCreate>({
    week_number: getCurrentWeekNumber(),
    goal: "",
  });

  function getCurrentWeekNumber(): number {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now.getTime() - start.getTime();
    const oneWeek = 1000 * 60 * 60 * 24 * 7;
    return Math.ceil(diff / oneWeek);
  }

  const handleSubmit = async () => {
    if (!formData.goal.trim()) {
      alert("Please enter a goal");
      return;
    }

    try {
      setLoading(true);
      await createWeeklyGoal(formData);
      setFormData({
        week_number: getCurrentWeekNumber(),
        goal: "",
      });
      onOpenChange(false);
      if (onGoalCreated) {
        onGoalCreated();
      }
    } catch (error) {
      console.error("Failed to create weekly goal:", error);
      alert("Failed to create weekly goal. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md p-0 gap-0 bg-card border-border overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <button onClick={() => onOpenChange(false)} className="text-muted-foreground hover:text-foreground">
            <X className="w-5 h-5" />
          </button>
          <h2 className="font-semibold text-foreground">New Weekly Goal</h2>
          <Button 
            size="sm" 
            className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? "Saving..." : "Save"}
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Week Number */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Week Number
            </label>
            <Input
              type="number"
              min="1"
              max="53"
              className="bg-secondary border-0 rounded-xl h-11"
              value={formData.week_number}
              onChange={(e) => setFormData({ ...formData, week_number: parseInt(e.target.value) || 1 })}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Current week: {getCurrentWeekNumber()}
            </p>
          </div>

          {/* Goal */}
          <div>
            <label className="text-sm text-muted-foreground mb-2 block flex items-center gap-2">
              <Target className="w-4 h-4" />
              Your Goal for This Week
            </label>
            <Textarea 
              placeholder="What do you want to accomplish this week?"
              className="bg-secondary border-0 rounded-xl resize-none min-h-[120px] placeholder:text-muted-foreground/60"
              value={formData.goal}
              onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Be specific about what you want to achieve
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-secondary/30">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="w-4 h-4 text-primary" />
            <span>Set your weekly focus</span>
          </div>
          <Button
            size="sm"
            className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg"
            onClick={handleSubmit}
            disabled={loading || !formData.goal.trim()}
          >
            Create Goal
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
