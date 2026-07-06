import { useQuery } from "@tanstack/react-query";
import { buildApiUrl } from "./base";

export type DailyBiasDirection = "bullish" | "bearish" | "neutral" | "choppy";

export interface DailyBias {
  bias_date: string;
  symbol: string;
  nasdaq_daily_bias: DailyBiasDirection;
  confidence: number;
  expected_close?: string | null;
  trade_mode?: string | null;
  risk_level?: string | null;
  main_support?: number | null;
  main_resistance?: number | null;
  invalid_if?: string | null;
  reason_summary?: string | null;
  agent_agreement?: string | null;
  debate_winner?: string | null;
  is_invalidated?: boolean | null;
  invalidated_at?: string | null;
}

export interface DailyBiasResponse {
  symbol: string;
  bias: DailyBias | null;
  status: "ok" | "no_bias_today";
}

async function fetchDailyBias(symbol: string): Promise<DailyBiasResponse> {
  const url = buildApiUrl(`/api/miroshark/current-bias?symbol=${encodeURIComponent(symbol)}`);
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch daily bias for ${symbol}`);
  }
  return res.json();
}

// Bias is a once-a-day snapshot; poll every 5 min so intraday invalidation
// (is_invalidated flipping) surfaces without hammering the endpoint.
export function useDailyBias(symbol: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["daily-bias", symbol],
    queryFn: () => fetchDailyBias(symbol),
    enabled,
    refetchInterval: 300000,
    staleTime: 120000,
  });
}
