import { useMutation, useQuery } from "@tanstack/react-query";
import { buildApiUrl } from "./base";

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(endpoint), {
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

export type OrderBlockCombinedSignal = {
  action: string;
  confidence: number;
  reasoning: string[];
  reasons: string[];
};

export type OrderBlockDetectResponse = {
  symbol: string;
  timeframe: string;
  total_order_blocks: number;
  bearish_obs: number;
  bullish_obs: number;
  order_blocks: Array<Record<string, unknown>>;
  active_signals: Array<Record<string, unknown>>;
  combined_signal?: OrderBlockCombinedSignal;
  structure?: Record<string, unknown>;
  choch_list?: Array<Record<string, unknown>>;
  bos_list?: Array<Record<string, unknown>>;
  fvg_list?: Array<Record<string, unknown>>;
  trend?: string;
  support_resistance?: Record<string, unknown>;
  timestamp?: string;
  warning?: string;
};

export type OrderBlockBacktestPayload = {
  symbol: string;
  timeframe: "5m" | "15m" | "30m" | "1h" | "4h" | "1d";
  start_date?: string;
  end_date?: string;
  config?: OrderBlockDetectPayload["config"];
};

export type OrderBlockBacktestResult = {
  signal: string;
  entry: number;
  outcome: string;
};

export type OrderBlockBacktestResponse = {
  total_signals: number;
  wins: number;
  losses: number;
  win_rate: number;
  results: OrderBlockBacktestResult[];
  total_trades: number;
  avg_risk_reward: number;
  total_profit: number;
  max_drawdown: number;
  sharpe_ratio: number;
};

export function useOrderBlockDetect(payload: OrderBlockDetectPayload) {
  return useQuery({
    queryKey: ["order-blocks", payload],
    queryFn: () =>
      fetcher<OrderBlockDetectResponse>("/api/order-blocks/detect", {
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
    mutationFn: (payload: OrderBlockBacktestPayload) =>
      fetcher<OrderBlockBacktestResponse>("/api/order-blocks/backtest", {
        method: "POST",
        body: JSON.stringify(payload)
      })
  });
}
