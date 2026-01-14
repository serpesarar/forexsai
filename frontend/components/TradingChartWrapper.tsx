"use client";

import { useQuery } from "@tanstack/react-query";
import TradingChart from "./TradingChart";

interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartDataResponse {
  symbol: string;
  timeframe: string;
  data: CandleData[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchChartData(symbol: string, timeframe: string): Promise<CandleData[]> {
  const res = await fetch(
    `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=500`
  );
  if (!res.ok) throw new Error("Failed to fetch chart data");
  const data: ChartDataResponse = await res.json();
  return data.data || [];
}

interface TradingChartWrapperProps {
  symbol: string;
  symbolLabel: string;
  timeframe?: string;
  height?: number;
}

export default function TradingChartWrapper({
  symbol,
  symbolLabel,
  timeframe = "1d",
  height = 400,
}: TradingChartWrapperProps) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["chart-data", symbol, timeframe],
    queryFn: () => fetchChartData(symbol, timeframe),
    placeholderData: (prev) => prev,
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000,
  });

  if (error) {
    return (
      <div className="glass-card rounded-2xl p-8 text-center">
        <p className="text-danger">Grafik verisi yüklenemedi</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  return (
    <TradingChart
      symbol={symbol}
      symbolLabel={symbolLabel}
      data={data || []}
      height={height}
      onRefresh={() => refetch()}
      isLoading={isLoading}
    />
  );
}
