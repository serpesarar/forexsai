import { useQuery, useMutation } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LearningHealth {
  db_available: boolean;
  message: string;
}

export interface AccuracySummary {
  symbol: string | null;
  period_days: number;
  check_interval: string;
  total_predictions: number;
  ml_accuracy: number | null;
  ml_correct_count: number | null;
  claude_accuracy: number | null;
  claude_correct_count: number | null;
  both_correct_rate: number | null;
  either_correct_rate: number | null;
}

export interface FactorAnalysis {
  symbol: string | null;
  period_days: number;
  sample_size: number;
  numeric_factors: Record<string, {
    avg_when_correct: number;
    avg_when_incorrect: number;
    difference_pct: number;
    samples_correct: number;
    samples_incorrect: number;
    insight: string;
  }>;
  categorical_factors: Record<string, Record<string, {
    accuracy: number;
    sample_size: number;
    correct_count: number;
  }>>;
  generated_at: string;
}

export interface Prediction {
  id: string;
  created_at: string;
  symbol: string;
  timeframe: string;
  ml_direction: string;
  ml_confidence: number;
  claude_direction: string | null;
  claude_confidence: number | null;
  factors: Record<string, any>;
  outcome_checked: boolean;
}

export interface LearningDashboard {
  db_available: boolean;
  symbol: string | null;
  period_days: number;
  accuracy: AccuracySummary;
  active_insights: any[];
  factor_analysis: FactorAnalysis | null;
}

export interface PredictionsResponse {
  predictions: Prediction[];
  count: number;
}

async function fetchLearningHealth(): Promise<LearningHealth> {
  const res = await fetch(`${API_BASE}/api/learning/health`);
  if (!res.ok) throw new Error("Failed to fetch learning health");
  return res.json();
}

async function fetchLearningDashboard(symbol?: string, days: number = 7): Promise<LearningDashboard> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("days", days.toString());
  
  const res = await fetch(`${API_BASE}/api/learning/dashboard?${params}`);
  if (!res.ok) throw new Error("Failed to fetch learning dashboard");
  return res.json();
}

async function fetchAccuracy(symbol?: string, days: number = 7): Promise<AccuracySummary> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("days", days.toString());
  
  const res = await fetch(`${API_BASE}/api/learning/accuracy?${params}`);
  if (!res.ok) throw new Error("Failed to fetch accuracy");
  return res.json();
}

async function fetchPredictions(symbol?: string, limit: number = 20): Promise<PredictionsResponse> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("limit", limit.toString());
  
  const res = await fetch(`${API_BASE}/api/learning/predictions?${params}`);
  if (!res.ok) throw new Error("Failed to fetch predictions");
  return res.json();
}

async function fetchFactorAnalysis(symbol?: string, days: number = 30): Promise<FactorAnalysis> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("days", days.toString());
  
  const res = await fetch(`${API_BASE}/api/learning/factor-analysis?${params}`);
  if (!res.ok) throw new Error("Failed to fetch factor analysis");
  return res.json();
}

async function triggerOutcomeCheck(interval: string = "24h"): Promise<any> {
  const res = await fetch(`${API_BASE}/api/learning/check-outcomes?check_interval=${interval}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to trigger outcome check");
  return res.json();
}

export function useLearningHealth() {
  return useQuery({
    queryKey: ["learning", "health"],
    queryFn: fetchLearningHealth,
    staleTime: 60000,
  });
}

export function useLearningDashboard(symbol?: string, days: number = 7) {
  return useQuery({
    queryKey: ["learning", "dashboard", symbol, days],
    queryFn: () => fetchLearningDashboard(symbol, days),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useAccuracy(symbol?: string, days: number = 7) {
  return useQuery({
    queryKey: ["learning", "accuracy", symbol, days],
    queryFn: () => fetchAccuracy(symbol, days),
    staleTime: 30000,
  });
}

export function usePredictions(symbol?: string, limit: number = 20) {
  return useQuery({
    queryKey: ["learning", "predictions", symbol, limit],
    queryFn: () => fetchPredictions(symbol, limit),
    staleTime: 10000,
    refetchInterval: 30000,
  });
}

export function useFactorAnalysis(symbol?: string, days: number = 30) {
  return useQuery({
    queryKey: ["learning", "factor-analysis", symbol, days],
    queryFn: () => fetchFactorAnalysis(symbol, days),
    staleTime: 60000,
  });
}

export { triggerOutcomeCheck };

// Multi-target types
export interface TargetConfig {
  name: string;
  pips: number;
}

export interface SymbolTargetConfig {
  symbol: string;
  pip_value: number;
  targets: TargetConfig[];
  stoploss_pips: number;
}

export interface TargetAccuracyItem {
  hit_count: number;
  total: number;
  hit_rate: number;
}

export interface MultiTargetAccuracy {
  symbol: string | null;
  period_days: number;
  check_interval: string;
  total_predictions: number;
  analyzed_predictions: number;
  target_accuracy: Record<string, TargetAccuracyItem>;
  stoploss_hit_rate: number;
  stoploss_hits: number;
  ml_accuracy: number | null;
  claude_accuracy: number | null;
}

export interface MultiTargetDashboard {
  db_available: boolean;
  symbol: string | null;
  period_days: number;
  config: {
    pip_value: number;
    targets: TargetConfig[];
    stoploss_pips: number;
  } | null;
  accuracy_1h: MultiTargetAccuracy | null;
  accuracy_24h: MultiTargetAccuracy | null;
  basic_accuracy: AccuracySummary | null;
}

async function fetchMultiTargetDashboard(symbol?: string, days: number = 7): Promise<MultiTargetDashboard> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("days", days.toString());
  
  const res = await fetch(`${API_BASE}/api/learning/multi-target-dashboard?${params}`);
  if (!res.ok) throw new Error("Failed to fetch multi-target dashboard");
  return res.json();
}

async function fetchTargetConfig(symbol: string): Promise<SymbolTargetConfig> {
  const res = await fetch(`${API_BASE}/api/learning/target-config/${symbol}`);
  if (!res.ok) throw new Error("Failed to fetch target config");
  return res.json();
}

async function trigger1hOutcomeCheck(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/learning/check-outcomes-1h`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to trigger 1h outcome check");
  return res.json();
}

export function useMultiTargetDashboard(symbol?: string, days: number = 7) {
  return useQuery({
    queryKey: ["learning", "multi-target-dashboard", symbol, days],
    queryFn: () => fetchMultiTargetDashboard(symbol, days),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useTargetConfig(symbol: string) {
  return useQuery({
    queryKey: ["learning", "target-config", symbol],
    queryFn: () => fetchTargetConfig(symbol),
    staleTime: 300000, // 5 minutes - config doesn't change often
  });
}

export { trigger1hOutcomeCheck };

// ============================================
// ADAPTIVE TP/SL API
// ============================================

export interface AdaptiveTPSL {
  entry: number;
  tp1: number;
  tp2: number;
  tp3: number;
  stop_loss: number;
  confidence: number;
  reasoning: string[];
  fib_levels: Record<string, number>;
  key_levels: Array<{ type: string; price: number }>;
  learned_adjustments: {
    adjustments: Array<{ type: string; action: string; frequency: string }>;
    confidence_modifier: number;
    total_analyzed?: number;
  };
}

export interface TPSuccessAnalysis {
  total: number;
  tp_analysis: Record<string, { success_rate: number; hit_count: number; total: number }>;
  optimal_tp: string | null;
  recommendations: string[];
  period_days: number;
}

export interface FailurePattern {
  id: string;
  prediction_id: string;
  symbol: string;
  direction: string;
  entry_price: number;
  failure_price: number;
  failure_reason: string;
  rsi_at_failure: number | null;
  volume_change: number | null;
  nearest_resistance: number | null;
  nearest_support: number | null;
  fib_level_hit: string | null;
  macd_divergence: boolean;
  recommendation: string;
  created_at: string;
}

async function fetchAdaptiveTPSL(
  symbol: string,
  direction: string,
  entryPrice: number
): Promise<AdaptiveTPSL> {
  const res = await fetch(`${API_BASE}/api/learning/adaptive-tp-sl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol,
      direction,
      entry_price: entryPrice,
    }),
  });
  if (!res.ok) throw new Error("Failed to fetch adaptive TP/SL");
  return res.json();
}

async function fetchTPSuccessAnalysis(
  symbol?: string,
  days: number = 7
): Promise<TPSuccessAnalysis> {
  const params = new URLSearchParams({ days: String(days) });
  if (symbol) params.append("symbol", symbol);
  const res = await fetch(`${API_BASE}/api/learning/tp-success-analysis?${params}`);
  if (!res.ok) throw new Error("Failed to fetch TP success analysis");
  return res.json();
}

async function fetchFailurePatterns(
  symbol?: string,
  direction?: string,
  limit: number = 50
): Promise<{ patterns: FailurePattern[]; count: number; reason_stats: Record<string, number> }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (symbol) params.append("symbol", symbol);
  if (direction) params.append("direction", direction);
  const res = await fetch(`${API_BASE}/api/learning/failure-patterns?${params}`);
  if (!res.ok) throw new Error("Failed to fetch failure patterns");
  return res.json();
}

export function useAdaptiveTPSL(symbol: string, direction: string, entryPrice: number, enabled: boolean = true) {
  return useQuery({
    queryKey: ["learning", "adaptive-tp-sl", symbol, direction, entryPrice],
    queryFn: () => fetchAdaptiveTPSL(symbol, direction, entryPrice),
    enabled: enabled && !!symbol && !!direction && entryPrice > 0,
    staleTime: 60000, // 1 minute
  });
}

export function useTPSuccessAnalysis(symbol?: string, days: number = 7) {
  return useQuery({
    queryKey: ["learning", "tp-success-analysis", symbol, days],
    queryFn: () => fetchTPSuccessAnalysis(symbol, days),
    staleTime: 60000,
  });
}

export function useFailurePatterns(symbol?: string, direction?: string, limit: number = 50) {
  return useQuery({
    queryKey: ["learning", "failure-patterns", symbol, direction, limit],
    queryFn: () => fetchFailurePatterns(symbol, direction, limit),
    staleTime: 60000,
  });
}

// =============================================================================
// CLAUDE NEWS ANALYSIS API
// =============================================================================

export interface ClaudeNewsAnalysis {
  headline: string;
  sentiment: number;
  confidence: number;
  category: string;
  time_sensitivity: string;
  key_entities: string[];
  rationale: string;
  override_signal: string | null;
}

export interface ClaudeAnalysisResponse {
  symbol: string;
  timestamp: string;
  news_count: number;
  analyzed_count: number;
  overall_sentiment: number;
  overall_confidence: number;
  direction_bias: string;
  analyses: ClaudeNewsAnalysis[];
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  has_override: boolean;
  override_signal: string | null;
  override_reason: string | null;
  categories: Record<string, number>;
  tokens_used: number;
  estimated_cost_usd: number;
  market_commentary: string;
  key_risks: string[];
  key_opportunities: string[];
}

export interface CachedNewsItem {
  headline: string;
  source: string;
  published_at: string | null;
  fetched_at: string;
  keyword_sentiment: number;
  keyword_confidence: number;
  claude_analyzed: boolean;
  claude_sentiment: number | null;
}

export interface CachedNewsResponse {
  symbol: string;
  news_count: number;
  news: CachedNewsItem[];
}

export interface RefreshResponse {
  symbol: string;
  fetched_count: number;
  saved_count: number;
  message: string;
}

async function analyzeNewsWithClaude(symbol: string, limit = 15, hoursBack = 24): Promise<ClaudeAnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/claude-news/analyze/${symbol}?limit=${limit}&hours_back=${hoursBack}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to analyze news with Claude");
  return res.json();
}

async function getCachedNews(symbol: string, limit = 20, hoursBack = 24): Promise<CachedNewsResponse> {
  const res = await fetch(`${API_BASE}/api/claude-news/cached/${symbol}?limit=${limit}&hours_back=${hoursBack}`);
  if (!res.ok) throw new Error("Failed to get cached news");
  return res.json();
}

async function refreshNewsCache(symbol: string, limit = 30): Promise<RefreshResponse> {
  const res = await fetch(`${API_BASE}/api/claude-news/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, limit }),
  });
  if (!res.ok) throw new Error("Failed to refresh news cache");
  return res.json();
}

export function useClaudeNewsAnalysis(symbol: string, enabled = false) {
  return useQuery({
    queryKey: ["claude-news", "analyze", symbol],
    queryFn: () => analyzeNewsWithClaude(symbol),
    enabled,
    staleTime: 300000, // 5 minutes - expensive API call
    refetchOnWindowFocus: false,
  });
}

export function useCachedNews(symbol: string) {
  return useQuery({
    queryKey: ["claude-news", "cached", symbol],
    queryFn: () => getCachedNews(symbol),
    staleTime: 60000, // 1 minute
  });
}

export function useRefreshNewsCache() {
  return useMutation({
    mutationFn: ({ symbol, limit }: { symbol: string; limit?: number }) => 
      refreshNewsCache(symbol, limit),
  });
}

export function useAnalyzeWithClaude() {
  return useMutation({
    mutationFn: ({ symbol, limit, hoursBack }: { symbol: string; limit?: number; hoursBack?: number }) =>
      analyzeNewsWithClaude(symbol, limit, hoursBack),
  });
}
