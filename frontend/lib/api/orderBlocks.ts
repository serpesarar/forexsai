import { useMutation, useQuery } from "@tanstack/react-query";

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

export type OrderBlockDetectPayload = {
  symbol: string;
  timeframe: "5m" | "15m" | "1h" | "4h";
  limit: number;
  config: {
    fractal_period: number;
    min_displacement_atr: number;
    min_score: number;
    zone_type: "wick" | "body";
    max_tests: number;
  };
};

export function useOrderBlockDetect(payload: OrderBlockDetectPayload) {
  return useQuery({
    queryKey: ["order-blocks", payload],
    queryFn: () =>
      fetcher("/api/order-blocks/detect", {
        method: "POST",
        body: JSON.stringify(payload)
      }),
    staleTime: 300000
  });
}

export function useOrderBlockEntry() {
  return useMutation({
    mutationFn: (payload: { symbol: string; timeframe: string; order_block_index: number }) =>
      fetcher("/api/order-blocks/check-entry", {
        method: "POST",
        body: JSON.stringify(payload)
      })
  });
}

export function useOrderBlockBacktest() {
  return useMutation({
    mutationFn: (payload: { symbol: string; timeframe: string; start_date: string; end_date: string }) =>
      fetcher("/api/order-blocks/backtest", {
        method: "POST",
        body: JSON.stringify(payload)
      })
  });
}
