"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import DashboardCard from "./DashboardCard";

interface ChartPoint {
  date: string;
  value: number;
}

interface CumulativeChartProps {
  data: ChartPoint[];
  isLoading?: boolean;
}

export default function CumulativeChart({ data, isLoading = false }: CumulativeChartProps) {
  const formattedData = data.map((point) => ({
    ...point,
    positive: Math.max(point.value, 0),
    negative: Math.min(point.value, 0)
  }));

  return (
    <DashboardCard title="Cumulative P&L" className="h-full">
      {isLoading ? (
        <div className="space-y-4">
          <div className="skeleton h-64 w-full" />
          <div className="flex gap-2">
            <div className="skeleton h-4 w-24" />
            <div className="skeleton h-4 w-16" />
          </div>
        </div>
      ) : (
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formattedData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="positiveFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4ade80" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#4ade80" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="negativeFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f87171" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#f87171" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" tickLine={false} axisLine={false} />
              <YAxis
                stroke="rgba(255,255,255,0.4)"
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${value / 1000}k`}
              />
              <Tooltip
                contentStyle={{
                  background: "#1a1d29",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "12px",
                  color: "#fff"
                }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, "P&L"]}
              />
              <Area
                type="monotone"
                dataKey="positive"
                stroke="#4ade80"
                fill="url(#positiveFill)"
                strokeWidth={2}
                dot={false}
                isAnimationActive
              />
              <Area
                type="monotone"
                dataKey="negative"
                stroke="#f87171"
                fill="url(#negativeFill)"
                strokeWidth={2}
                dot={false}
                isAnimationActive
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </DashboardCard>
  );
}
