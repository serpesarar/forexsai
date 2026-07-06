import { useQuery } from "@tanstack/react-query";
import { getApiBase } from "./base";

const API_BASE = getApiBase();

// ── types ──────────────────────────────────────────────────────────────────
export interface ReflexSignal {
  id: number;
  symbol: string;
  event_time: string;
  entry_time: string | null;
  direction: "BUY" | "SELL";
  family: string;
  regime: string | null;
  entry_price: number | null;
  sl_price: number | null;
  exit_deadline: string;
  status: "active" | "closed_win" | "closed_loss" | "closed_flat" | "error";
  exit_time: string | null;
  exit_price: number | null;
  r_multiple: number | null;
  pnl_points: number | null;
  stretch: number | null;
  regime_mode?: string;
  mode: "shadow" | "live";
  explanation?: { why?: string } | null;
}

export interface ReflexSignalsResponse {
  symbol: string;
  days?: number;
  signals: ReflexSignal[];
  db?: boolean;
}

export interface ReflexRegimeStat {
  n: number;
  win_rate: number;
  ev_r: number;
}

export interface ReflexPerformance {
  symbol: string;
  days: number;
  n: number;
  active: number;
  win_rate: number | null;
  ev_r: number | null;
  profit_factor: number | null;
  avg_win: number | null;
  avg_loss: number | null;
  total_r: number;
  max_drawdown_r: number;
  by_regime: Record<string, ReflexRegimeStat>;
  db?: boolean;
}

// ── fetchers ───────────────────────────────────────────────────────────────
async function fetchReflexSignals(symbol: string, days = 7, limit = 50): Promise<ReflexSignalsResponse> {
  const params = new URLSearchParams({ symbol, days: String(days), limit: String(limit) });
  const res = await fetch(`${API_BASE}/api/reflex/signals?${params}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch reflex signals");
  return res.json();
}

async function fetchReflexPerformance(symbol: string, days = 30): Promise<ReflexPerformance> {
  const params = new URLSearchParams({ symbol, days: String(days) });
  const res = await fetch(`${API_BASE}/api/reflex/performance?${params}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch reflex performance");
  return res.json();
}

// ── hooks (live polling) ────────────────────────────────────────────────────
export function useReflexSignals(symbol: string, days = 7, limit = 50) {
  return useQuery({
    queryKey: ["reflex", "signals", symbol, days, limit],
    queryFn: () => fetchReflexSignals(symbol, days, limit),
    staleTime: 20000,
    refetchInterval: 30000,
  });
}

export function useReflexPerformance(symbol: string, days = 30) {
  return useQuery({
    queryKey: ["reflex", "performance", symbol, days],
    queryFn: () => fetchReflexPerformance(symbol, days),
    staleTime: 20000,
    refetchInterval: 30000,
  });
}
