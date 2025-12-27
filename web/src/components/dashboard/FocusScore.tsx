export function FocusScore() {
  const score = 85;
  
  return (
    <div className="bg-card rounded-lg shadow-card p-4 animate-fade-in" style={{ animationDelay: "0.4s" }}>
      <h3 className="font-semibold text-foreground mb-4">Focus Score</h3>
      <div className="flex flex-col items-center">
        <div 
          className="relative w-24 h-24 rounded-full focus-score-ring flex items-center justify-center"
          style={{ "--score": score } as React.CSSProperties}
        >
          <div className="absolute inset-2 bg-card rounded-full flex items-center justify-center">
            <span className="text-2xl font-bold text-foreground">{score}</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground text-center mt-3">
          Your schedule is optimized for peak productivity
        </p>
      </div>
    </div>
  );
}
