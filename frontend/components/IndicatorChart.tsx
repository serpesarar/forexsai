"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CandleData } from "./useChartData";

interface IndicatorChartProps {
  candles: CandleData[];
  rsi: (number | null)[];
  macd: {
    macdLine: (number | null)[];
    signal: (number | null)[];
    histogram: (number | null)[];
  };
}

function formatTime(timestamp: number) {
  return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function IndicatorChart({ candles, rsi, macd }: IndicatorChartProps) {
  const rsiData = useMemo(
    () =>
      candles.map((candle, index) => ({
        time: candle.timestamp,
        value: rsi[index] ?? null,
      })),
    [candles, rsi]
  );

  const macdData = useMemo(
    () =>
      candles.map((candle, index) => ({
        time: candle.timestamp,
        macd: macd.macdLine[index] ?? null,
        signal: macd.signal[index] ?? null,
        hist: macd.histogram[index] ?? null,
      })),
    [candles, macd]
  );

  return (
    <div className="space-y-6">
      <div className="h-48 bg-[#0a0e27] rounded-xl border border-white/10 p-4">
        <div className="flex items-center justify-between text-xs text-textSecondary mb-2">
          <span>RSI (14)</span>
          <span>{rsi[rsi.length - 1] ? rsi[rsi.length - 1]?.toFixed(1) : "--"}</span>
        </div>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={rsiData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="rsiFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4c6ef5" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#4c6ef5" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="time"
              tickFormatter={formatTime}
              stroke="rgba(255,255,255,0.4)"
              tick={{ fontSize: 10 }}
            />
            <YAxis domain={[0, 100]} stroke="rgba(255,255,255,0.4)" tick={{ fontSize: 10 }} />
            <Tooltip
              formatter={(value: number) => value?.toFixed(2)}
              labelFormatter={(label) => formatTime(label as number)}
              contentStyle={{
                background: "#11162f",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
              }}
            />
            <Area type="monotone" dataKey="value" stroke="#4c6ef5" fill="url(#rsiFill)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="h-52 bg-[#0a0e27] rounded-xl border border-white/10 p-4">
        <div className="flex items-center justify-between text-xs text-textSecondary mb-2">
          <span>MACD (12,26,9)</span>
          <span>{macd.macdLine[macd.macdLine.length - 1]?.toFixed(2) ?? "--"}</span>
        </div>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={macdData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="time"
              tickFormatter={formatTime}
              stroke="rgba(255,255,255,0.4)"
              tick={{ fontSize: 10 }}
            />
            <YAxis stroke="rgba(255,255,255,0.4)" tick={{ fontSize: 10 }} />
            <Tooltip
              formatter={(value: number) => value?.toFixed(2)}
              labelFormatter={(label) => formatTime(label as number)}
              contentStyle={{
                background: "#11162f",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
              }}
            />
            <Line type="monotone" dataKey="macd" stroke="#26a69a" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="signal" stroke="#ff9800" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
