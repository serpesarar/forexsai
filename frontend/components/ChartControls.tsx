"use client";

import type { ChartTimeframe } from "../lib/store";

interface ChartControlsProps {
  timeframe: ChartTimeframe;
  onTimeframeChange: (value: ChartTimeframe) => void;
}

const timeframes: ChartTimeframe[] = ["5m", "15m", "1h", "4h", "1d"];

export default function ChartControls({ timeframe, onTimeframeChange }: ChartControlsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {timeframes.map((value) => (
        <button
          key={value}
          onClick={() => onTimeframeChange(value)}
          className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
            timeframe === value ? "bg-white text-background" : "bg-white/10 text-white"
          }`}
        >
          {value.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
