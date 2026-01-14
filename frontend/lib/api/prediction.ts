import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

async function fetchPrediction(symbol: string): Promise<PredictionData> {
  const res = await fetch(`${API_BASE}/api/prediction/${symbol}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch prediction for ${symbol}`);
  }
  return res.json();
}

async function fetchAllPredictions(): Promise<PredictionData[]> {
  const res = await fetch(`${API_BASE}/api/prediction/`);
  if (!res.ok) {
    throw new Error("Failed to fetch predictions");
  }
  return res.json();
}

export function usePrediction(symbol: string) {
  return useQuery({
    queryKey: ["prediction", symbol],
    queryFn: () => fetchPrediction(symbol),
    refetchInterval: 60000, // Refresh every 60 seconds
    staleTime: 30000,
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
