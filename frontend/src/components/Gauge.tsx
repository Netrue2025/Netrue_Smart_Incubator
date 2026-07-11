interface GaugeProps {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  target?: number;
  large?: boolean;
}

export function Gauge({ label, value, min, max, unit, target, large }: GaugeProps) {
  const safe = Number.isFinite(value) ? value : min;
  const percent = Math.max(0, Math.min(1, (safe - min) / (max - min)));
  const circumference = 2 * Math.PI * 82;
  const dash = circumference * 0.75;
  const offset = dash - dash * percent;
  return (
    <div className="flex flex-col items-center justify-center">
      <div className={large ? "relative h-72 w-72" : "relative h-56 w-56"}>
        <svg viewBox="0 0 220 220" className="h-full w-full">
          <circle cx="110" cy="110" r="82" fill="none" stroke="hsl(var(--muted))" strokeWidth="18" strokeDasharray={`${dash} ${circumference}`} className="gauge-track" />
          <circle
            cx="110"
            cy="110"
            r="82"
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth="18"
            strokeDasharray={`${dash} ${circumference}`}
            strokeDashoffset={offset}
            className="gauge-track transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-sm uppercase tracking-wide text-foreground/60">{label}</span>
          <strong className={large ? "text-5xl" : "text-4xl"}>{safe.toFixed(1)}</strong>
          <span className="text-sm text-foreground/70">{unit}</span>
          {target !== undefined && <span className="mt-2 text-xs text-foreground/60">Target {target.toFixed(1)}{unit}</span>}
        </div>
      </div>
    </div>
  );
}
