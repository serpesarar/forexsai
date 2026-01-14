import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }
  return response.json() as Promise<T>;
}

export function useRtyhiimDetect(symbol: string = "NDX.INDX") {
  return useQuery({
    queryKey: ["rtyhiim", symbol],
    queryFn: () => fetcher(`/api/rtyhiim/detect?symbol=${encodeURIComponent(symbol)}`, { method: "POST", body: "{}" }),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 15000
  });
}

export interface ConsolidationData {
  is_consolidating: boolean;
  range_high: number;
  range_low: number;
  range_size: number;
  range_percent: number;
  midpoint: number;
  current_price: number;
  position_in_range: number;
  atr: number;
  volatility_ratio: number;
  consolidation_score: number;
  candles_analyzed: number;
  breakout_direction: string | null;
  // Swing point based detection
  swing_highs: number[];
  swing_lows: number[];
  swing_high_consistency: boolean;
  swing_low_consistency: boolean;
  swing_count: number;
  high_deviation: number;
  low_deviation: number;
}

export function useConsolidation(symbol: string = "NDX.INDX", lookback: number = 20, interval: string = "1m") {
  return useQuery<ConsolidationData>({
    queryKey: ["consolidation", symbol, lookback, interval],
    queryFn: () => fetcher(`/api/rtyhiim/consolidation?symbol=${encodeURIComponent(symbol)}&lookback=${lookback}&interval=${interval}`),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}
