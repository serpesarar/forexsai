import { useQuery } from "@tanstack/react-query";
import { buildApiUrl } from "./base";

export interface KeyLevel {
  type: string;
  price: number;
  distance: string;
}

export interface PredictionData {
  symbol: string;
  direction: "BUY" | "SELL" | "HOLD";
  confidence: number;
  probability_up: number;
  probability_down: number;
  target_pips: number;
  stop_pips: number;
  risk_reward: number;
  entry_price: number;
  target_price: number;
  stop_price: number;
  technical_score: number;
  momentum_score: number;
  trend_score: number;
  volatility_regime: string;
  reasoning: string[];
  key_levels: KeyLevel[];
  timestamp: string;
  model_version: string;
}

async function fetchPrediction(
  symbol: string,
  enabledFactors?: string[],
  logToDb: boolean = false,
  strategy?: string | null
): Promise<PredictionData> {
  const params = new URLSearchParams();
  if (strategy) {
    params.append("strategy", strategy);
  }
  if (enabledFactors && enabledFactors.length > 0) {
    params.append("enabled_factors", enabledFactors.join(","));
  }
  if (logToDb) {
    params.append("log_to_db", "true");
  }
  const queryString = params.toString();
  const url = buildApiUrl(`/api/prediction/${symbol}${queryString ? `?${queryString}` : ""}`);
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch prediction for ${symbol}`);
  }
  return res.json();
}

// Fetch with custom factors (for factor panel)
export async function fetchPredictionWithFactors(symbol: string, enabledFactors: string[]): Promise<PredictionData> {
  return fetchPrediction(symbol, enabledFactors);
}

// Fetch with strategy preset (for layer panel) - logs to DB for learning
export async function fetchPredictionWithStrategy(symbol: string, strategy: string): Promise<PredictionData> {
  const url = buildApiUrl(`/api/prediction/${symbol}?strategy=${strategy}&log_to_db=true`);
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch prediction for ${symbol} with strategy ${strategy}`);
  }
  return res.json();
}

async function fetchAllPredictions(): Promise<PredictionData[]> {
  const res = await fetch(buildApiUrl("/api/prediction/"));
  if (!res.ok) {
    throw new Error("Failed to fetch predictions");
  }
  return res.json();
}

export function usePrediction(symbol: string, logToDb: boolean = true) {
  return useQuery({
    queryKey: ["prediction", symbol, logToDb],
    queryFn: () => fetchPrediction(symbol, undefined, logToDb),
    refetchInterval: 60000, // Refresh every 60 seconds - logs to DB each time
    staleTime: 10000, // Data is stale after 10 seconds (allows manual refresh)
    gcTime: 60000, // Keep in cache for 1 minute
  });
}

export function usePredictionWithConfig(
  symbol: string,
  config: { strategy?: string | null; enabledFactors?: string[] | null },
  logToDb: boolean = true
) {
  const strategy = config.strategy || null;
  const enabledFactors = config.enabledFactors || undefined;
  return useQuery({
    queryKey: ["prediction", symbol, logToDb, strategy, enabledFactors?.join(",") || ""],
    queryFn: () => fetchPrediction(symbol, enabledFactors, logToDb, strategy),
    refetchInterval: 60000,
    staleTime: 10000,
    gcTime: 60000,
  });
}

export function useAllPredictions() {
  return useQuery({
    queryKey: ["predictions", "all"],
    queryFn: fetchAllPredictions,
    refetchInterval: 60000,
    staleTime: 30000,
  });
}
