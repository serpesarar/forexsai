"use client";

interface Props {
  confidence?: number;
  direction?: string;
  compact?: boolean;
}

export function ConfidenceBar({ confidence = 0, direction = "HOLD", compact }: Props) {
  const pct = Math.max(0, Math.min(100, Math.round(confidence || 0)));
  const dir = (direction || "HOLD").toUpperCase();
  const color = dir === "BUY" ? "bg-emerald-500" : dir === "SELL" ? "bg-rose-500" : "bg-slate-500";

  return (
    <div className="w-full">
      {!compact && (
        <div className="mb-1 flex items-center justify-between text-[11px] text-slate-400">
          <span>Confidence</span>
          <span className="font-semibold text-slate-200">{pct}%</span>
        </div>
      )}
      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default ConfidenceBar;
