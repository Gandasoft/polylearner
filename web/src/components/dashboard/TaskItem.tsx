import { Clock } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { FocusBadge } from "./FocusBadge";

interface TaskItemProps {
  title: string;
  time: string;
  duration: string;
  focusLevel: "high" | "medium" | "low" | "meeting";
  completed?: boolean;
}

export function TaskItem({ title, time, duration, focusLevel, completed = false }: TaskItemProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex items-center gap-3">
        <Checkbox checked={completed} className="border-border" />
        <div>
          <p className={`text-sm font-medium ${completed ? "line-through text-muted-foreground" : "text-foreground"}`}>
            {title}
          </p>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            <Clock className="w-3 h-3" />
            <span>{time}</span>
            <span>•</span>
            <span>{duration}</span>
          </div>
        </div>
      </div>
      <FocusBadge level={focusLevel} />
    </div>
  );
}
