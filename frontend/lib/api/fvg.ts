import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface FVG {
  index: number;
  type: "bullish" | "bearish";
  gap_high: number;
  gap_low: number;
  gap_size: number;
  gap_percent: number;
  impulse_size: number;
  timestamp: number;
  is_filled: boolean;
  fill_percent: number;
  fill_index: number | null;
  is_valid: boolean;
  score: number;
  distance_to_price?: number;
  distance_percent?: number;
}

export interface FVGDetectResponse {
  symbol: string;
  timeframe: string;
  total_fvgs: number;
  bullish_fvgs: number;
  bearish_fvgs: number;
  unfilled_count: number;
  fvgs: FVG[];
  nearest_bullish: FVG | null;
  nearest_bearish: FVG | null;
}

export interface FVGDetectRequest {
  symbol: string;
  timeframe?: string;
  limit?: number;
  min_gap_percent?: number;
  min_body_percent?: number;
}

async function detectFVGs(request: FVGDetectRequest): Promise<FVGDetectResponse> {
  const res = await fetch(`${API_BASE}/api/fvg/detect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error("Failed to detect FVGs");
  return res.json();
}

async function getUnfilledFVGs(symbol: string, limit: number = 100): Promise<{
  symbol: string;
  current_price: number;
  unfilled_fvgs: FVG[];
  count: number;
}> {
  const res = await fetch(`${API_BASE}/api/fvg/unfilled/${symbol}?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to get unfilled FVGs");
  return res.json();
}

export function useFVGDetect(request: FVGDetectRequest) {
  return useQuery({
    queryKey: ["fvg", "detect", request.symbol, request.timeframe, request.limit],
    queryFn: () => detectFVGs(request),
    staleTime: 60000,
    refetchInterval: 120000,
  });
}

export function useUnfilledFVGs(symbol: string, limit: number = 100) {
  return useQuery({
    queryKey: ["fvg", "unfilled", symbol, limit],
    queryFn: () => getUnfilledFVGs(symbol, limit),
    staleTime: 60000,
    refetchInterval: 120000,
  });
}
