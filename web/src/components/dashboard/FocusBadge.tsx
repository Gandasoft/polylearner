interface FocusBadgeProps {
  level: "high" | "medium" | "low" | "meeting";
}

const levelConfig = {
  high: {
    label: "High Focus",
    className: "bg-focus-high/10 text-focus-high",
  },
  medium: {
    label: "Medium Focus",
    className: "bg-focus-medium/10 text-focus-medium",
  },
  low: {
    label: "Low Focus",
    className: "bg-focus-low/10 text-focus-low",
  },
  meeting: {
    label: "Meeting",
    className: "bg-focus-meeting/10 text-focus-meeting",
  },
};

export function FocusBadge({ level }: FocusBadgeProps) {
  const config = levelConfig[level];
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  );
}
