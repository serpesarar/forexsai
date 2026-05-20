import { buildApiUrl } from "./base";

export interface CrossModelInfo {
  enabled: boolean;
  model_type: string;
  strategy: string;
  symbol: string;
  timeframe: string;
  description: string;
}

export interface CrossModelPreview {
  symbol: string;
  direction: "BUY" | "SELL" | "HOLD";
  confidence: number;
  probability_up: number;
  probability_down: number;
  entry_price: number;
  target_price: number;
  stop_price: number;
  model_used: string;
  experiment: string;
  timestamp: string;
  cached?: boolean;
  error?: string | null;
}

export interface CrossModelRecentSignal {
  id: string;
  direction: "BUY" | "SELL";
  confidence: number;
  status: "active" | "completed" | "stopped" | "expired";
  resolution: string | null;
  created_at: string;
  exit_time: string | null;
}

export interface CrossModelStats {
  enabled: boolean;
  available: boolean;
  window_days?: number;
  model_type?: string;
  total_signals?: number;
  active?: number;
  resolved?: number;
  real_wins?: number;
  sl_hits?: number;
  window_wins?: number;
  real_win_rate_pct?: number | null;
  net_pips?: number;
  last_tick_at?: string | null;
  last_tick_status?: string | null;
  recent_signals?: CrossModelRecentSignal[];
  reason?: string;
  error?: string;
}

async function get<T>(endpoint: string): Promise<T> {
  const r = await fetch(buildApiUrl(endpoint), { cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export const crossModelApi = {
  info: () => get<CrossModelInfo>("/api/experiments/cross-model/info"),
  preview: () => get<CrossModelPreview>("/api/experiments/cross-model/preview"),
  stats: (days = 14) =>
    get<CrossModelStats>(`/api/experiments/cross-model/stats?days=${days}`),
};
