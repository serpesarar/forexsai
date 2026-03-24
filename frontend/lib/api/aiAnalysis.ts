import { useQuery } from "@tanstack/react-query";
import { buildApiUrl } from "./base";

export type PanelDirection = "BUY" | "SELL" | "HOLD" | "NO_TRADE";
export type PanelBehavior = "uptrend" | "downtrend" | "range" | "mean_reversion" | "volatile";

export interface KeyLevel {
  type: string;
  price: number;
  distance: string;
}

export interface PanelKeyLevel {
  label: string;
  price: number | null;
  kind: string;
  source: string;
  distance: string;
}

export interface PanelBias {
  direction: PanelDirection;
  confidence: number;
  expected_behavior: PanelBehavior;
  summary: string;
  time_horizon: string;
  reasoning: string[];
}

export interface PanelEntryPlan {
  strategy: string;
  preferred_entry: number | null;
  entry_zone: { low: number | null; high: number | null } | null;
  stop_loss: number | null;
  take_profit: number | null;
  risk_reward: number | null;
  invalidation: string;
}

export interface PanelEventRiskItem {
  event_name: string;
  impact: "LOW" | "MEDIUM" | "HIGH";
  minutes_until: number | null;
}

export interface PanelSignal {
  headline: string;
  scalp_bias: PanelBias;
  intraday_bias: PanelBias;
  market_behavior: {
    state: PanelBehavior;
    summary: string;
    expected_volatility: string;
  };
  entry_plan: PanelEntryPlan;
  key_levels: PanelKeyLevel[];
  bull_case: string[];
  bear_case: string[];
  macro_risk: {
    level: "LOW" | "MEDIUM" | "HIGH";
    summary: string;
    drivers: string[];
  };
  event_risk: {
    level: "LOW" | "MEDIUM" | "HIGH";
    summary: string;
    events: PanelEventRiskItem[];
  };
  invalidation: string[];
  confidence_reasoning: string;
  top_factors: string[];
  counter_factors: string[];
  data_quality: {
    level: "LOW" | "MEDIUM" | "HIGH";
    missing_inputs: string[];
    notes: string[];
  };
}

export interface AnalysisMeta {
  analysis_version: string;
  prompt_version: string;
  provider: string;
  model: string;
  cache_hit: boolean;
  market_open: boolean;
  market_session: string;
  generated_at: string;
  expires_at: string;
  context_pack_version?: string;
}

export interface MarketContext {
  ny_time?: string;
  phase?: string;
  session_name?: string;
  regime?: Record<string, any>;
  event_risk_level?: string;
  volatility_level?: string;
}

export interface DataSources {
  context_pack?: boolean;
  market_regime?: boolean;
  unified_news?: boolean;
  economic_calendar?: boolean;
  comex_news?: boolean;
  oil_analysis?: boolean;
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
  panel_signal?: PanelSignal;
  analysis_meta?: AnalysisMeta;
  market_context?: MarketContext;
  data_sources?: DataSources;
  scalp_direction?: PanelDirection;
  scalp_confidence?: number;
}

export interface FullAnalysisData {
  ml_prediction: MLPrediction;
  claude_analysis: ClaudeAnalysis;
  ta_snapshot: TASnapshot;
}

async function fetchAIAnalysis(symbol: string, forceRefresh: boolean = false): Promise<FullAnalysisData> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 55000);
  
  try {
    const url = forceRefresh
      ? `${buildApiUrl(`/api/ai-analysis/${symbol}`)}?force_refresh=true`
      : buildApiUrl(`/api/ai-analysis/${symbol}`);
    const res = await fetch(url, {
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
  const timeoutId = setTimeout(() => controller.abort(), 55000);
  
  try {
    const res = await fetch(buildApiUrl("/api/ai-analysis/"), {
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

export function useAIAnalysis(symbol: string, enabled: boolean = false, refreshNonce: number = 0) {
  return useQuery({
    queryKey: ["ai-analysis", symbol, refreshNonce],
    queryFn: () => fetchAIAnalysis(symbol, refreshNonce > 0),
    enabled, // Only fetch when explicitly enabled (button click)
    refetchInterval: 3600000,
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
