import { buildApiUrl } from "./base";

/** One (symbol, model_type, direction) scope from the replay report. */
export interface ReplayScope {
  symbol: string;
  model_type: string | null;
  direction: string | null;
  n: number;
  flipped: number;
  orig_completed: number;
  orig_stopped: number;
  orig_expired: number;
  corr_completed: number;
  corr_stopped: number;
  corr_expired: number;
  pnl_delta_pips_total: number;
  flip_rate_pct: number;
  orig_win_rate: number | null;
  corr_win_rate: number | null;
}

export interface ReplayReport {
  status: string;
  rows: number;
  scopes: ReplayScope[];
  filter?: { batch_id: string | null; symbol: string | null; days: number };
}

async function get<T>(endpoint: string): Promise<T> {
  const r = await fetch(buildApiUrl(endpoint), { cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export const replayApi = {
  /** Per-scope original-vs-corrected diff. days defaults wide enough to
   *  cover the full 2026-02-10→now replay window. */
  report: (days = 120) => get<ReplayReport>(`/api/replay/report?days=${days}`),
};
