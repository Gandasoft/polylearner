import { Bell, Settings, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  userName: string;
  taskCount: number;
}

export function Header({ userName, taskCount }: HeaderProps) {
  return (
    <header className="flex items-center justify-between mb-8">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-lg">T</span>
        </div>
        <span className="font-semibold text-foreground">TaskFlow AI</span>
      </div>
      <div className="flex items-center gap-3">
        <button className="p-2 hover:bg-accent rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-muted-foreground" />
        </button>
        <button className="p-2 hover:bg-accent rounded-lg transition-colors">
          <Settings className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>
    </header>
  );
}

export function Greeting({ userName, taskCount }: HeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Good morning, {userName}</h1>
        <p className="text-muted-foreground">
          You have {taskCount} tasks this week. Let's optimize your schedule.
        </p>
      </div>
      <Button className="gap-2">
        <Plus className="w-4 h-4" />
        Add Weekly Tasks
      </Button>
    </div>
  );
}
