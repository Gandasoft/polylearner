import { MoreHorizontal } from "lucide-react";
import { TaskItem } from "./TaskItem";

interface Task {
  id: string;
  title: string;
  time: string;
  duration: string;
  focusLevel: "high" | "medium" | "low" | "meeting";
  completed?: boolean;
}

interface DayScheduleProps {
  day: string;
  hoursScheduled: number;
  tasks: Task[];
  delay?: number;
}

export function DaySchedule({ day, hoursScheduled, tasks, delay = 0 }: DayScheduleProps) {
  return (
    <div 
      className="bg-card rounded-lg shadow-card animate-fade-in" 
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-foreground">{day}</h3>
          <span className="text-sm text-muted-foreground">{hoursScheduled} hours scheduled</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-success">Optimized</span>
          <button className="p-1 hover:bg-accent rounded transition-colors">
            <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>
      <div className="px-4">
        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            title={task.title}
            time={task.time}
            duration={task.duration}
            focusLevel={task.focusLevel}
            completed={task.completed}
          />
        ))}
      </div>
    </div>
  );
}
