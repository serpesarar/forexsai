"use client";

import type { LegendPoint } from "./CandlestickChart";

interface ChartLegendProps {
  symbol: string;
  timeframe: string;
  legend: LegendPoint | null;
  latestPrice?: number | null;
  emaValues?: Record<number, number | null>;
  rsi?: number | null;
  macd?: number | null;
}

export default function ChartLegend({
  symbol,
  timeframe,
  legend,
  latestPrice,
  emaValues,
  rsi,
  macd,
}: ChartLegendProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-textSecondary">
      <span className="font-semibold text-white">{symbol}</span>
      <span className="uppercase">{timeframe}</span>
      {legend ? (
        <span>
          O {legend.open.toFixed(2)} H {legend.high.toFixed(2)} L {legend.low.toFixed(2)} C {legend.close.toFixed(2)}
        </span>
      ) : latestPrice ? (
        <span>Last {latestPrice.toFixed(2)}</span>
      ) : null}
      <span>EMA20 {emaValues?.[20]?.toFixed(2) ?? "--"}</span>
      <span>EMA50 {emaValues?.[50]?.toFixed(2) ?? "--"}</span>
      <span>EMA200 {emaValues?.[200]?.toFixed(2) ?? "--"}</span>
      <span>RSI {rsi?.toFixed(1) ?? "--"}</span>
      <span>MACD {macd?.toFixed(2) ?? "--"}</span>
    </div>
  );
}
