import { useQuery } from "@tanstack/react-query";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

export interface KeyLevel {
  type: string;
  price: number;
  distance: string;
}

export interface TASnapshot {
  close: number;
  ema_20: number;
  ema_50: number;
  ema_200: number;
  rsi_14: number;
  macd_hist: number;
  atr_14: number;
  boll_zscore: number;
}

export interface MLPrediction {
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
}

export interface ClaudeAnalysis {
  symbol: string;
  ml_direction: string;
  claude_direction: "BUY" | "SELL" | "HOLD";
  claude_confidence: number;
  agreement: boolean;
  general_assessment: string;
  strengths: string[];
  weaknesses: string[];
  recommended_entry: number;
  recommended_sl: number;
  recommended_tp: number;
  position_size_suggestion: string;
  key_observations: string[];
  risk_factors: string[];
  timestamp: string;
  model_used: string;
}

export interface FullAnalysisData {
  ml_prediction: MLPrediction;
  claude_analysis: ClaudeAnalysis;
  ta_snapshot: TASnapshot;
}

async function fetchAIAnalysis(symbol: string): Promise<FullAnalysisData> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
  
  try {
    const res = await fetch(`${API_BASE}/api/ai-analysis/${symbol}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      throw new Error(`Failed to fetch AI analysis for ${symbol}`);
    }
    return res.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`AI analysis timed out for ${symbol}. Please try again.`);
    }
    throw error;
  }
}

async function fetchAllAIAnalysis(): Promise<FullAnalysisData[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
  
  try {
    const res = await fetch(`${API_BASE}/api/ai-analysis/`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      throw new Error("Failed to fetch AI analysis");
    }
    return res.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error("AI analysis timed out. Please try again.");
    }
    throw error;
  }
}

export function useAIAnalysis(symbol: string, enabled: boolean = false) {
  return useQuery({
    queryKey: ["ai-analysis", symbol],
    queryFn: () => fetchAIAnalysis(symbol),
    enabled, // Only fetch when explicitly enabled (button click)
    refetchInterval: false, // No auto-refresh - save API calls
    staleTime: 300000, // 5 minutes - data stays fresh longer
    gcTime: 600000, // 10 minutes cache
  });
}

export function useAllAIAnalysis(enabled: boolean = false) {
  return useQuery({
    queryKey: ["ai-analysis", "all"],
    queryFn: fetchAllAIAnalysis,
    enabled,
    refetchInterval: false,
    staleTime: 300000,
    gcTime: 600000,
  });
}
