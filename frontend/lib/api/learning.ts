import { useQuery, useMutation } from "@tanstack/react-query";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

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

async function triggerCleanAllPending(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/learning/check-all-pending`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to clean all pending");
  return res.json();
}

export { triggerCleanAllPending };

// Per-model accuracy types
export interface ModelAccuracyItem {
  strategy: string;
  total_predictions: number;
  with_outcome: number;
  ml_accuracy: number | null;
  ml_correct: number;
  claude_accuracy: number | null;
  claude_correct: number;
  target_hit_rate: number | null;
  target_hits: number;
  stop_hit_rate: number | null;
  stop_hits: number;
}

export interface ModelAccuracyResponse {
  models: ModelAccuracyItem[];
  total: number;
  days: number;
  check_interval: string;
  symbol: string | null;
  error?: string;
}

async function fetchAccuracyByModel(symbol?: string, days: number = 30, checkInterval: string = "24h"): Promise<ModelAccuracyResponse> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("days", days.toString());
  params.append("check_interval", checkInterval);

  const res = await fetch(`${API_BASE}/api/learning/accuracy-by-model?${params}`);
  if (!res.ok) throw new Error("Failed to fetch accuracy by model");
  return res.json();
}

export function useAccuracyByModel(symbol?: string, days: number = 30, checkInterval: string = "24h") {
  return useQuery({
    queryKey: ["learning", "accuracy-by-model", symbol, days, checkInterval],
    queryFn: () => fetchAccuracyByModel(symbol, days, checkInterval),
    staleTime: 60000,
    refetchInterval: 120000,
  });
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
    refetchInterval: 120000,
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

// ============================================================
// PREDICTION HISTORY
// ============================================================

export interface PredictionHistoryItem {
  id: string;
  symbol: string;
  timestamp: string;
  ml_direction: string;
  ml_confidence: number;
  entry_price: number;
  target_price: number;
  stop_price: number;
  claude_direction: string | null;
  claude_confidence: number | null;
  has_outcome: boolean;
  exit_price?: number;
  high_price?: number;
  low_price?: number;
  price_change_pct?: number;
  actual_direction?: string;
  hit_target?: boolean;
  hit_stop?: boolean;
  ml_correct?: boolean;
  claude_correct?: boolean;
  outcome_time?: string;
}

export interface PredictionHistorySummary {
  total_predictions: number;
  with_outcome: number;
  pending_outcome: number;
  ml_correct: number;
  ml_accuracy: number | null;
  target_hits: number;
  stop_hits: number;
  period_days: number;
}

export interface PredictionHistoryResponse {
  predictions: PredictionHistoryItem[];
  summary: PredictionHistorySummary;
  error?: string;
}

async function fetchPredictionHistory(
  symbol?: string,
  days: number = 7,
  limit: number = 50
): Promise<PredictionHistoryResponse> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);
  params.append("days", days.toString());
  params.append("limit", limit.toString());

  const res = await fetch(`${API_BASE}/api/learning/prediction-history?${params}`);
  if (!res.ok) throw new Error("Failed to fetch prediction history");
  return res.json();
}

export function usePredictionHistory(symbol?: string, days: number = 7, limit: number = 50) {
  return useQuery({
    queryKey: ["prediction-history", symbol, days, limit],
    queryFn: () => fetchPredictionHistory(symbol, days, limit),
    staleTime: 60000, // 1 minute
    refetchInterval: 120000, // Auto refresh every 2 minutes
  });
}

// Fix ml_correct values in database where hit_target=true but ml_correct=false
export async function fixMlCorrectInDatabase(): Promise<{ success: boolean; updated_count?: number; error?: string }> {
  const res = await fetch(`${API_BASE}/api/learning/fix-ml-correct`, {
    method: "POST",
  });
  if (!res.ok) {
    const error = await res.text();
    return { success: false, error };
  }
  return res.json();
}

// Reset and recalculate UI stats
export async function resetUiStats(symbol?: string): Promise<any> {
  const params = new URLSearchParams();
  if (symbol) params.append("symbol", symbol);

  const res = await fetch(`${API_BASE}/api/learning/reset-ui-stats?${params}`, {
    method: "POST",
  });
  if (!res.ok) {
    const error = await res.text();
    return { success: false, error };
  }
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// SIGNAL LIFECYCLE v2 API
// ═══════════════════════════════════════════════════════════════════════════

export interface ActiveSignal {
  id: string;
  symbol: string;
  ml_direction: string;
  ml_confidence: number;
  ml_entry_price: number;
  model_type: string;
  strategy: string;
  status: string;
  targets: Record<string, number>;
  targets_hit: Record<string, boolean>;
  highest_profit_pips: number;
  lowest_drawdown_pips: number;
  stop_loss_pips: number;
  created_at: string;
}

export interface ModelStats {
  total_signals: number;
  completed: number;
  stopped: number;
  expired: number;
  win_rate: number;
  avg_profit_pips: number;
  avg_loss_pips: number;
  risk_reward: number;
  total_profit_pips: number;
  total_loss_pips: number;
  net_pips: number;
  target_rates: Record<string, number>;
  symbols: Record<string, { total: number; completed: number; stopped: number; expired?: number; win_rate?: number; net_pips?: number; target_rates?: Record<string, number> }>;
}

export interface LifecycleDashboard {
  period_days: number;
  model_stats: Record<string, ModelStats>;
  failure_breakdown: Record<string, number>;
  total_failures: number;
  active_signals: number;
  generated_at: string;
  error?: string;
}

export interface SignalCheck {
  id: string;
  signal_id: string;
  check_time: string;
  current_price: number;
  session_high: number | null;
  session_low: number | null;
  profit_pips: number;
  cumulative_high_pips: number;
  cumulative_low_pips: number;
  target_status: Record<string, boolean>;
}

export interface SignalDetail {
  signal: any;
  checks: SignalCheck[];
  failure: any | null;
  error?: string;
}

export interface LifecycleCheckSummary {
  checked: number;
  completed: number;
  stopped: number;
  expired: number;
  still_active: number;
  target_hits: Array<{ signal_id: string; symbol: string; direction: string }>;
  timestamp: string;
}

async function fetchActiveSignals(): Promise<{ signals: ActiveSignal[]; count: number }> {
  const res = await fetch(`${API_BASE}/api/signals/active`);
  if (!res.ok) throw new Error("Failed to fetch active signals");
  return res.json();
}

async function fetchLifecycleDashboard(days: number = 365): Promise<LifecycleDashboard> {
  const res = await fetch(`${API_BASE}/api/signals/dashboard?days=${days}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch lifecycle dashboard");
  return res.json();
}

async function fetchSignalDetail(signalId: string): Promise<SignalDetail> {
  const res = await fetch(`${API_BASE}/api/signals/detail/${signalId}`);
  if (!res.ok) throw new Error("Failed to fetch signal detail");
  return res.json();
}

async function triggerLifecycleCheck(): Promise<{ success: boolean; summary: LifecycleCheckSummary }> {
  const res = await fetch(`${API_BASE}/api/signals/check-now`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger lifecycle check");
  return res.json();
}

export function useActiveSignals() {
  return useQuery({
    queryKey: ["signals", "active"],
    queryFn: fetchActiveSignals,
    staleTime: 15000,
    refetchInterval: 120000,
  });
}

export function useLifecycleDashboard(days: number = 365) {
  return useQuery({
    queryKey: ["signals", "dashboard", days],
    queryFn: () => fetchLifecycleDashboard(days),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useSignalDetail(signalId: string | null) {
  return useQuery({
    queryKey: ["signals", "detail", signalId],
    queryFn: () => fetchSignalDetail(signalId!),
    enabled: !!signalId,
    staleTime: 10000,
  });
}

export { triggerLifecycleCheck };
