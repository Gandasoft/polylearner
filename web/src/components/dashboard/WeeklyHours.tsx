import { Download } from "lucide-react";

const weekData = [
  { day: "Monday", hours: 8 },
  { day: "Tuesday", hours: 6 },
  { day: "Wednesday", hours: 5 },
  { day: "Thursday", hours: 3 },
  { day: "Friday", hours: 2 },
];

export function WeeklyHours() {
  return (
    <div className="bg-card rounded-lg shadow-card p-4 animate-fade-in" style={{ animationDelay: "0.3s" }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-foreground">This Week</h3>
        <button className="flex items-center gap-1 text-xs font-medium text-primary hover:underline">
          <Download className="w-3 h-3" />
          Export
        </button>
      </div>
      <div className="space-y-3">
        {weekData.map((item) => (
          <div key={item.day} className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{item.day}</span>
            <span className="font-medium text-foreground">{item.hours}h</span>
          </div>
        ))}
      </div>
    </div>
  );
}
