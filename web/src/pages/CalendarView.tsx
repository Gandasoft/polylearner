import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Menu, Share, RefreshCw, Calendar, BarChart3, CheckSquare, Settings, Play, MoreHorizontal, Video, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { NewTaskDialog } from "@/components/dashboard/NewTaskDialog";
import { getSchedule, WeekScheduleResponse, ScheduleBlock } from "@/lib/api";

const weekDays = [
  { day: "MON", date: 23 },
  { day: "TUE", date: 24, isToday: true, hasEvent: true },
  { day: "WED", date: 25 },
  { day: "THU", date: 26 },
  { day: "FRI", date: 27 },
  { day: "SAT", date: 28 },
];

export default function CalendarView() {
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [scheduleData, setScheduleData] = useState<WeekScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    loadSchedule();
  }, []);

  async function loadSchedule() {
    try {
      setLoading(true);
      const data = await getSchedule();
      setScheduleData(data);
    } catch (error) {
      console.error('Failed to load schedule:', error);
    } finally {
      setLoading(false);
    }
  }

  // Filter schedule blocks for today
  const todaySchedule = scheduleData?.schedule.filter(block => {
    const blockDate = new Date(block.start_time);
    return blockDate.toDateString() === selectedDate.toDateString();
  }) || [];

  const formatTime = (isoTime: string) => {
    const date = new Date(isoTime);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      coding: 'bg-blue-500/20 text-blue-600',
      research: 'bg-purple-500/20 text-purple-600',
      admin: 'bg-gray-500/20 text-gray-600',
      networking: 'bg-green-500/20 text-green-600',
    };
    return colors[category] || colors.admin;
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Main Content */}
      <div className="flex-1 max-w-md mx-auto p-4 pb-20">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button className="text-muted-foreground hover:text-foreground">
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h1 className="font-bold text-lg text-foreground">{selectedDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}</h1>
              <p className="text-xs text-muted-foreground">
                {selectedDate.toDateString() === new Date().toDateString() ? 'Today' : selectedDate.toLocaleDateString('en-US', { weekday: 'long' })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-muted-foreground hover:text-foreground">
              <Share className="w-5 h-5" />
            </button>
            <button 
              className="p-2 bg-primary rounded-full text-primary-foreground"
              onClick={loadSchedule}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Week Selector */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {weekDays.map((item) => (
            <button
              key={item.day}
              className={`flex flex-col items-center min-w-[48px] py-2 px-3 rounded-xl transition-colors ${
                item.isToday 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:bg-secondary'
              }`}
            >
              <span className="text-xs font-medium">{item.day}</span>
              <span className={`text-lg font-bold ${item.isToday ? '' : 'text-foreground'}`}>{item.date}</span>
              {item.hasEvent && <span className="w-1 h-1 bg-current rounded-full mt-1" />}
            </button>
          ))}
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Current Time Indicator */}
          <div className="absolute left-12 right-0 top-[60px] flex items-center z-10">
            <span className="text-xs text-primary font-medium mr-2">
              {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
            </span>
            <div className="w-2 h-2 bg-primary rounded-full" />
            <div className="flex-1 h-0.5 bg-primary" />
          </div>

          {/* Schedule Items */}
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">Loading schedule...</p>
              </div>
            ) : todaySchedule.length > 0 ? (
              todaySchedule.map((block) => (
                <div key={`${block.task_id}-${block.start_time}`} className="flex gap-3">
                  {/* Time */}
                  <div className="w-12 text-right">
                    <span className="text-xs text-muted-foreground">{formatTime(block.start_time)}</span>
                  </div>

                  {/* Content */}
                  <div className="flex-1 bg-card rounded-2xl p-4 border border-border">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded font-medium uppercase ${getCategoryColor(block.category)}`}>
                          {block.category}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded font-medium bg-secondary text-foreground">
                          {block.duration_hours}h
                        </span>
                      </div>
                      <button className="text-muted-foreground hover:text-foreground">
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </div>
                    <h3 className="font-semibold text-foreground mb-1">{block.task_title}</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      {formatTime(block.start_time)} - {formatTime(block.end_time)}
                    </p>
                    <Button size="sm" className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2 rounded-lg">
                      <Play className="w-3.5 h-3.5" />
                      Start Focus
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No tasks scheduled for this day</p>
                <Button 
                  className="mt-4" 
                  onClick={() => setTaskDialogOpen(true)}
                >
                  Create Task
                </Button>
              </div>
            )}
          </div>

          {/* AI Suggestions */}
          {scheduleData?.recommendations && scheduleData.recommendations.length > 0 && (
            <div className="mt-4 ml-14 bg-secondary/50 rounded-xl p-4 border border-primary/30">
              <div className="flex items-start gap-2 mb-2">
                <span className="text-primary text-lg">✨</span>
                <div>
                  <span className="text-xs font-medium text-primary">AI Suggestion</span>
                  <p className="text-sm text-foreground">{scheduleData.recommendations[0].suggestion}</p>
                  <p className="text-xs text-muted-foreground mt-1">{scheduleData.recommendations[0].reason}</p>
                </div>
              </div>
              <div className="flex gap-3 ml-6">
                <button className="text-sm text-primary hover:underline font-medium">View All</button>
                <button className="text-sm text-muted-foreground hover:text-foreground">Dismiss</button>
              </div>
            </div>
          )}

          {/* Cognitive Tax Score */}
          {scheduleData && (
            <div className="mt-4 ml-14 bg-card rounded-xl p-4 border border-border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Cognitive Tax Score</p>
                  <p className="text-2xl font-bold text-foreground">
                    {(scheduleData.cognitive_tax_score * 100).toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase">Total Hours</p>
                  <p className="text-2xl font-bold text-foreground">
                    {scheduleData.total_hours.toFixed(1)}h
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Floating Add Button */}
        <button 
          onClick={() => setTaskDialogOpen(true)}
          className="fixed bottom-20 right-4 w-14 h-14 bg-primary hover:bg-primary/90 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105"
        >
          <Plus className="w-6 h-6 text-primary-foreground" />
        </button>
      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
        <div className="max-w-md mx-auto flex items-center justify-around py-3">
          <Link to="/" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground">
            <Calendar className="w-5 h-5" />
            <span className="text-xs">Day</span>
          </Link>
          <Link to="/calendar" className="flex flex-col items-center gap-1 text-primary">
            <BarChart3 className="w-5 h-5" />
            <span className="text-xs">Week</span>
          </Link>
          <Link to="/" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground">
            <CheckSquare className="w-5 h-5" />
            <span className="text-xs">Tasks</span>
          </Link>
          <Link to="/" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-foreground">
            <Settings className="w-5 h-5" />
            <span className="text-xs">Settings</span>
          </Link>
        </div>
      </nav>

      <NewTaskDialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen} onTaskCreated={loadSchedule} />
    </div>
  );
}
