import { ListTodo, Clock, Target, TrendingDown } from "lucide-react";
import { Header, Greeting } from "@/components/dashboard/Header";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { AIRecommendations } from "@/components/dashboard/AIRecommendations";
import { DaySchedule } from "@/components/dashboard/DaySchedule";
import { WeeklyHours } from "@/components/dashboard/WeeklyHours";
import { FocusScore } from "@/components/dashboard/FocusScore";
import { QuickActions } from "@/components/dashboard/QuickActions";

const scheduleData = {
  monday: [
    { id: "1", title: "Review project proposals", time: "9:00 - 11:00 AM", duration: "2 hours", focusLevel: "high" as const },
    { id: "2", title: "Team standup meeting", time: "11:15 - 11:45 AM", duration: "30 min", focusLevel: "meeting" as const },
    { id: "3", title: "Email and admin tasks", time: "2:00 - 3:30 PM", duration: "1.5 hours", focusLevel: "low" as const },
  ],
  tuesday: [
    { id: "4", title: "Code review session", time: "9:00 - 11:00 AM", duration: "2 hours", focusLevel: "high" as const },
    { id: "5", title: "Client presentation prep", time: "2:00 - 4:00 PM", duration: "2 hours", focusLevel: "medium" as const },
  ],
  wednesday: [
    { id: "6", title: "Strategic planning", time: "9:00 - 12:00 PM", duration: "3 hours", focusLevel: "high" as const },
  ],
};

const stats = [
  { icon: ListTodo, iconBgColor: "bg-primary", value: "8", label: "Total Tasks" },
  { icon: Clock, iconBgColor: "bg-success", value: "24h", label: "Total Hours" },
  { icon: Target, iconBgColor: "bg-primary", value: "85%", label: "Optimization" },
  { icon: TrendingDown, iconBgColor: "bg-focus-medium", value: "12%", label: "Tax Reduction" },
];

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <Header userName="John" taskCount={8} />
        <Greeting userName="John" taskCount={8} />
        
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {stats.map((stat, index) => (
            <StatsCard
              key={stat.label}
              icon={stat.icon}
              iconBgColor={stat.iconBgColor}
              value={stat.value}
              label={stat.label}
            />
          ))}
        </div>

        {/* AI Recommendations */}
        <div className="mb-6">
          <AIRecommendations />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Schedule Column */}
          <div className="lg:col-span-2 space-y-4">
            <DaySchedule
              day="Monday"
              hoursScheduled={8}
              tasks={scheduleData.monday}
              delay={0.2}
            />
            <DaySchedule
              day="Tuesday"
              hoursScheduled={6}
              tasks={scheduleData.tuesday}
              delay={0.25}
            />
            <DaySchedule
              day="Wednesday"
              hoursScheduled={5}
              tasks={scheduleData.wednesday}
              delay={0.3}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <WeeklyHours />
            <FocusScore />
            <QuickActions />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
