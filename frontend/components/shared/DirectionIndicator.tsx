"use client";

import { ArrowUp, ArrowDown, Minus } from "lucide-react";

type Direction = "BUY" | "SELL" | "HOLD" | string;

interface Props {
  direction?: Direction;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function DirectionIndicator({ direction = "HOLD", size = "md", showLabel = true }: Props) {
  const dir = (direction || "HOLD").toUpperCase();
  const isBuy = dir === "BUY" || dir === "UP";
  const isSell = dir === "SELL" || dir === "DOWN";

  const sizeCls = size === "sm" ? "h-3.5 w-3.5" : size === "lg" ? "h-5 w-5" : "h-4 w-4";
  const textCls = size === "sm" ? "text-xs" : size === "lg" ? "text-base" : "text-sm";
  const pillCls = size === "sm" ? "px-2 py-0.5" : size === "lg" ? "px-3 py-1.5" : "px-2.5 py-1";

  const color = isBuy
    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
    : isSell
      ? "bg-rose-500/15 text-rose-400 border-rose-500/30"
      : "bg-slate-500/15 text-slate-400 border-slate-500/30";

  const Icon = isBuy ? ArrowUp : isSell ? ArrowDown : Minus;

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-bold ${color} ${pillCls} ${textCls}`}>
      <Icon className={sizeCls} />
      {showLabel && <span>{dir}</span>}
    </span>
  );
}

export default DirectionIndicator;
