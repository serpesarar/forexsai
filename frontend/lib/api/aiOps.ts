import { buildApiUrl } from "./base";

export type Severity = "critical" | "high" | "medium" | "low";
export type ProposalStatus =
  | "pending" | "reviewed" | "approved" | "rejected"
  | "implemented" | "rolled_back";

export interface ProposedFix {
  type: "filter_rule" | "threshold_tweak" | "feature_addition" | "weight_adjustment" | "retrain";
  description: string;
  implementation_hint?: string;
  estimated_impact?: string;
  risk: "low" | "medium" | "high";
}

export interface MetricBlock {
  n_signals?: number;
  n_resolved?: number;
  n_wins?: number;
  win_rate?: number | null;
  total_pnl_pips?: number;
  avg_pnl_pips?: number | null;
  max_drawdown_pips?: number;
  ci_low_pct?: number | null;
  ci_high_pct?: number | null;
  profit_factor?: number | null;
}

export interface SimulatedMetric {
  status: "ok" | "manual_review_required" | "error";
  window_days: number;
  original: MetricBlock;
  simulated: MetricBlock;
  deltas: {
    win_rate_pp?: number | null;
    pnl_pips?: number;
    max_drawdown_pp?: number;
    profit_factor_delta?: number | null;
    n_signals_blocked?: number;
    blocked_pnl_avoided?: number;
    blocked_was_loss?: number;
    blocked_was_win?: number;
    verdict?: "unanimously_better" | "mixed" | "unanimously_worse" | "insignificant" | "insufficient_data";
    // Walk-forward overfitting check
    robustness?: {
      status: "robust" | "marginally_overfit" | "overfit" | "highly_overfit"
            | "broken" | "insufficient_data" | "insignificant_in_sample";
      in_sample_winrate_delta?: number | null;
      oos_winrate_delta?: number | null;
      in_sample_pnl_delta?: number;
      oos_pnl_delta?: number;
      robustness_ratio?: number | null;
      interpretation?: string;
    };
    training_window_days?: number;
    in_sample?: { n_signals: number; deltas: any | null };
    out_of_sample?: { n_signals: number; deltas: any | null };
  };
  fixes_evaluated: { type: string; description: string; n_blocked: number; block_rate_pct: number }[];
  fixes_skipped: { type: string; description: string; reason: string }[];
  error?: string | null;
  simulated_at: string;
}

export interface LiveTrackingMetric {
  started_at: string;
  checked_days: number;
  daily_snapshots: Array<{
    checked_at: string;
    age_days: number;
    n_signals: number;
    win_rate: number | null;
    total_pnl_pips: number;
    max_drawdown_pips: number;
    ci_low_pct: number | null;
    ci_high_pct: number | null;
  }>;
  overall: MetricBlock;
  vs_simulation: {
    sim_winrate_delta: number | null;
    live_winrate_delta: number | null;
    divergence_factor: number | null;
  };
  status: "tracking" | "confirmed" | "degraded" | "degraded_drawdown" | "insufficient_data";
}

export interface TrackedProposal {
  id: string;
  symbol: string;
  model_type: string;
  severity: Severity;
  root_cause: string | null;
  simulated_metric: SimulatedMetric | null;
  live_tracking_metric: LiveTrackingMetric | null;
  live_tracking_started_at: string | null;
  live_tracking_last_check: string | null;
  rollback_recommended: boolean | null;
  rollback_recommendation_reason: string | null;
  reviewed_at: string | null;
}

export interface Proposal {
  id: string;
  cluster_id: string | null;
  symbol: string;
  model_type: string;
  severity: Severity;
  status: ProposalStatus;
  llm_model: string | null;
  root_cause: string | null;
  proposed_fixes: ProposedFix[];
  alternative_explanations: string[];
  requires_data: string | null;
  pre_change_metric: Record<string, any> | null;
  post_change_metric: Record<string, any> | null;
  simulated_metric: SimulatedMetric | null;
  simulated_at: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  pr_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface FailureCluster {
  id: string;
  symbol: string;
  model_type: string;
  direction: string | null;
  cluster_signature: string;
  common_tags: string[];
  sample_size: number;
  win_rate: number;
  total_pnl_pips: number;
  avg_confidence: number;
  representative_prediction_ids: string[];
  window_start: string;
  window_end: string;
  sent_to_llm: boolean;
  proposal_id: string | null;
  created_at: string;
}

export interface Stats {
  available: boolean;
  total?: number;
  by_status?: Record<string, number>;
  by_severity?: Record<string, number>;
  clusters_total?: number;
  error?: string;
}

async function get<T>(endpoint: string): Promise<T> {
  const r = await fetch(buildApiUrl(endpoint), { cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

async function patch<T>(endpoint: string, body: object): Promise<T> {
  const r = await fetch(buildApiUrl(endpoint), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

async function post<T>(endpoint: string, body: object): Promise<T> {
  const r = await fetch(buildApiUrl(endpoint), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export interface TpSlRecommendation {
  id: string;
  symbol: string;
  model_type: string | null;
  direction: "BUY" | "SELL" | null;
  timeframe: string | null;
  sample_size: number;
  analysis_window_days: number;
  current_tp_pips: number | null;
  current_sl_pips: number | null;
  current_net_pnl_pips: number | null;
  current_win_rate: number | null;
  recommended_tp_pips: number;
  recommended_sl_pips: number;
  recommended_net_pnl_pips: number | null;
  recommended_win_rate: number | null;
  expected_pnl_delta_pips: number | null;
  expected_winrate_delta_pp: number | null;
  mfe_distribution: Record<string, number>;
  mae_distribution: Record<string, number>;
  grid_top5: Array<{ tp: number; sl: number; net_pnl: number; win_rate: number | null; rr_ratio: number | null }>;
  status: "pending" | "reviewed" | "applied" | "rejected";
  severity: "critical" | "high" | "medium" | "low" | "none";
  reasoning: string | null;
  reviewed_at: string | null;
  applied_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface PatternMiningStatus {
  local_file_exists: boolean;
  local_generated_at?: string;
  local_rules_count?: number;
  local_window_days?: number;
  recent_runs?: Array<{
    id: string;
    generated_at: string;
    rules_count: number;
    winning_count: number;
    avoid_count: number;
    total_signals: number;
    window_days: number;
    triggered_by: string;
    duration_seconds: number;
    status: string;
  }>;
  latest_run?: {
    generated_at: string;
    rules_count: number;
    triggered_by: string;
  };
}

export const aiOps = {
  stats: () => get<Stats>("/api/ai-ops/stats"),
  listProposals: (params: {
    status?: ProposalStatus;
    severity?: Severity;
    symbol?: string;
    model_type?: string;
    limit?: number;
  } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && q.set(k, String(v)));
    return get<{ proposals: Proposal[]; count: number }>(`/api/ai-ops/proposals?${q}`);
  },
  getProposal: (id: string) =>
    get<{ proposal: Proposal; cluster: FailureCluster | null; sample_failures: any[] }>(
      `/api/ai-ops/proposals/${id}`
    ),
  approve: (id: string, body: { reviewer?: string; create_github_issue?: boolean; note?: string }) =>
    patch<{
      ok: boolean;
      status: string;
      issue_url: string | null;
      github_error: { reason: string; detail: string; repo?: string; token_source?: string } | null;
    }>(`/api/ai-ops/proposals/${id}/approve`, body),
  reject: (id: string, body: { reviewer?: string; reason?: string }) =>
    patch<{ ok: boolean; status: string }>(`/api/ai-ops/proposals/${id}/reject`, body),
  simulate: (id: string, windowDays = 60) =>
    post<{ ok: boolean; result: SimulatedMetric }>(
      `/api/ai-ops/proposals/${id}/simulate?window_days=${windowDays}`, {}
    ),
  manualRun: (windowDays = 7) =>
    post<{ ok: boolean; status: string; window_days: number }>(
      `/api/ai-ops/run`, { window_days: windowDays }
    ),
  listClusters: (params: {
    symbol?: string;
    model_type?: string;
    sent_to_llm?: boolean;
    limit?: number;
  } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && q.set(k, String(v)));
    return get<{ clusters: FailureCluster[] }>(`/api/ai-ops/clusters?${q}`);
  },
  // TP/SL Optimizer
  tpSlList: (params: { symbol?: string; status?: string; severity?: string; limit?: number } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && q.set(k, String(v)));
    return get<{ recommendations: TpSlRecommendation[] }>(`/api/ai-ops/tp-sl/recommendations?${q}`);
  },
  tpSlRun: (days = 60, symbol?: string) =>
    post<{ ok: boolean; status: string; days: number; symbol: string }>(
      `/api/ai-ops/tp-sl/run?days=${days}${symbol ? `&symbol=${encodeURIComponent(symbol)}` : ""}`, {}
    ),
  tpSlApply: (id: string, body: { reviewer?: string; notes?: string }) =>
    patch<{ ok: boolean }>(`/api/ai-ops/tp-sl/recommendations/${id}/apply`, body),
  tpSlReject: (id: string, body: { reviewer?: string; reason?: string }) =>
    patch<{ ok: boolean }>(`/api/ai-ops/tp-sl/recommendations/${id}/reject`, body),
  miningStatus: () => get<PatternMiningStatus>("/api/ai-ops/pattern-mining/status"),
  triggerMining: (days = 60) =>
    post<{ ok: boolean; status: string; days: number; note: string }>(
      `/api/ai-ops/pattern-mining/run?days=${days}`, {}
    ),
  listTracked: () => get<{ tracked: TrackedProposal[] }>("/api/ai-ops/proposals/tracked"),
  checkLive: (id: string) =>
    post<{ ok: boolean; result: any }>(`/api/ai-ops/proposals/${id}/check-live`, {}),
};
