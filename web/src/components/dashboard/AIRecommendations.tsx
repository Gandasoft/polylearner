import { Sparkles, CheckCircle2 } from "lucide-react";

const recommendations = [
  "Schedule deep work during your peak focus hours (9-11 AM)",
  "Group similar tasks to reduce context switching",
  "Add 15-minute breaks between high-intensity tasks",
];

export function AIRecommendations() {
  return (
    <div className="ai-gradient rounded-lg p-6 text-ai-foreground animate-fade-in" style={{ animationDelay: "0.1s" }}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4" />
            <span className="font-semibold text-sm">AI Recommendations</span>
          </div>
          <p className="text-sm opacity-90 mb-4">
            Based on your cognitive load patterns, we've optimized your schedule for maximum productivity.
          </p>
          <ul className="space-y-2">
            {recommendations.map((rec, index) => (
              <li key={index} className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="w-14 h-14 rounded-xl bg-white/20 flex items-center justify-center ml-4">
          <Sparkles className="w-7 h-7" />
        </div>
      </div>
    </div>
  );
}
