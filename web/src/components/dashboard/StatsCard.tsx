import { LucideIcon } from "lucide-react";

interface StatsCardProps {
  icon: LucideIcon;
  iconBgColor: string;
  value: string;
  label: string;
}

export function StatsCard({ icon: Icon, iconBgColor, value, label }: StatsCardProps) {
  return (
    <div className="bg-card rounded-lg p-5 shadow-card hover:shadow-card-hover transition-shadow duration-200">
      <div className={`w-10 h-10 rounded-lg ${iconBgColor} flex items-center justify-center mb-3`}>
        <Icon className="w-5 h-5 text-primary-foreground" />
      </div>
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}
