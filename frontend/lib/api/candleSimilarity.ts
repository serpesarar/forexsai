/**
 * Mum Benzerlik API istemcisi — son N mumun geçmişteki görsel eşleri.
 * Backend: GET /api/candle-similarity/{symbol}?tf=&n=&k=  (routers/candle_similarity_router.py)
 */

import { useQuery } from "@tanstack/react-query";
import { getApiBase } from "./base";

const API = getApiBase();
const REFRESH_MS = 60_000;

/** [open, high, low, close] — pencerenin kendi aralığına göre 0..1 */
export type NormCandle = [number, number, number, number];

export interface HorizonSummary {
  n: number;
  up_pct: number | null;
  median_pct: number | null;
  mean_pct: number | null;
  q25_pct: number | null;
  q75_pct: number | null;
  median_points: number | null;
  base_up_pct: number;
  base_median_abs_pct: number | null;
  p_value_vs_base: number | null;
  hour_median_abs_pct?: number | null;
}

export interface SimilarityMatch {
  rank: number;
  start: string;
  end: string;
  similarity: number;
  rms: number;
  rank_pct: number;
  end_close: number;
  fwd_pct: Record<string, number>;
  mfe_pct: number;
  mae_pct: number;
  chart?: { window: NormCandle[]; future: NormCandle[] };
}

export interface Reliability {
  n_queries: number;
  horizon_bars: number;
  test_from: string;
  direction_hit_pct: number;
  random_neighbors_hit_pct: number;
  always_majority_hit_pct: number;
  strong_n: number;
  strong_hit_pct: number | null;
  magnitude_corr_matches: number | null;
  magnitude_corr_hour_typical: number | null;
  verdict: string;
}

export interface SimilarityResponse {
  symbol: string;
  timeframe: string;
  window: number;
  source?: "canli" | "arsiv_sonu";
  price?: number;
  query?: { start: string; end: string; chart: NormCandle[] };
  library?: { start: string; end: string; bars: number; candidates: number };
  horizons_bars?: number[];
  horizons?: Record<string, HorizonSummary>;
  matches?: SimilarityMatch[];
  reliability?: Reliability | null;
  note?: string;
  error?: string;
}

export async function fetchSimilarity(symbol: string, tf: string, n: number, k = 20): Promise<SimilarityResponse> {
  const res = await fetch(`${API}/api/candle-similarity/${encodeURIComponent(symbol)}?tf=${tf}&n=${n}&k=${k}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export function useCandleSimilarity(symbol: string, tf: string, n: number, k = 20) {
  return useQuery<SimilarityResponse>({
    queryKey: ["candle-similarity", symbol, tf, n, k],
    queryFn: () => fetchSimilarity(symbol, tf, n, k),
    refetchInterval: REFRESH_MS,
    placeholderData: (prev) => prev,
  });
}
