"use client";

type Status = "CONFIRM" | "SCOUT" | "HOLD" | "ACTIVE" | string;

interface Props {
  status?: Status;
  size?: "sm" | "md";
}

export function StatusBadge({ status = "HOLD", size = "sm" }: Props) {
  const s = (status || "HOLD").toUpperCase();
  const sizeCls = size === "sm" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-1";

  let color = "bg-slate-700/40 text-slate-300 border-slate-600/40";
  if (s === "CONFIRM" || s === "ACTIVE") color = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
  else if (s === "SCOUT") color = "bg-cyan-500/10 text-cyan-300 border-cyan-500/30 border-dashed";

  return (
    <span className={`inline-flex items-center rounded-md border font-semibold uppercase tracking-wide ${color} ${sizeCls}`}>
      {s}
    </span>
  );
}

export default StatusBadge;
