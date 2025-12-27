import { Calendar, Wand2, FileDown } from "lucide-react";

const actions = [
  { icon: Calendar, label: "Sync to Calendar", color: "text-primary" },
  { icon: Wand2, label: "Re-optimize", color: "text-warning" },
  { icon: FileDown, label: "Export ICS", color: "text-success" },
];

export function QuickActions() {
  return (
    <div className="bg-card rounded-lg shadow-card p-4 animate-fade-in" style={{ animationDelay: "0.5s" }}>
      <h3 className="font-semibold text-foreground mb-4">Quick Actions</h3>
      <div className="space-y-2">
        {actions.map((action) => (
          <button
            key={action.label}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors text-left"
          >
            <action.icon className={`w-4 h-4 ${action.color}`} />
            <span className="text-sm text-foreground">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
