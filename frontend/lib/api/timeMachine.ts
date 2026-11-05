/**
 * Zaman Makinesi API istemcisi — bir işlem planının olasılıkları ve ufuk-sonu fiyat aralığı.
 * Backend: GET /api/time-machine/{symbol} (routers/time_machine_router.py; yöntem day-trader-skill trader-timemachine, MIT)
 */

import { useQuery } from "@tanstack/react-query";
import { getApiBase } from "./base";

const API = getApiBase();

export type TradeSide = "buy" | "sell";
export type TmTimeframe = "5m" | "15m" | "1h";

export interface TimeMachinePlanInput {
  symbol: string;
  side: TradeSide;
  stopAtr: number;
  targetR: number;
  bars: number;
  tf?: TmTimeframe;
}

/** Ufuk-sonu fiyat bandı — /api/time-machine/{symbol}/band (DTS-03: %90 bant tüm TF/sembollerde kalibre). */
export interface RangeBand {
  symbol: string;
  tf: TmTimeframe;
  price: number;
  horizon_min: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  rel_p5: number;
  rel_p25: number;
  rel_p50: number;
  rel_p75: number;
  rel_p95: number;
  width_pct: number;
  pool_sessions: number;
  calibration: string;
}

export interface TimeMachineResult {
  symbol: string;
  last_bar: string;
  plan: {
    side: TradeSide;
    entry: number;
    stop: number;
    target: number;
    atr: number;
    stop_atr: number;
    target_r: number;
    bars: number;
    entry_time: string;
    pool_sessions: number;
    pool_from: string;
    pool_to: string;
  };
  mc: {
    replays: number;
    seed: number;
    bars_left: number;
    p_target: number;
    p_stop: number;
    p_neither: number;
    p_green: number;
    median_close: number;
    p5_close: number;
    p95_close: number;
    avg_R: number;
    r_at_target: number;
    bands: number[][];
  };
  history: {
    sessions: number;
    trades: number;
    target: number;
    stop: number;
    close: number;
    avg_R: number | null;
  };
  verdict: string;
  notes: string[];
  note: string;
}

export interface TimeMachineCalibration {
  _meta?: { test: string; date: string; plan: string; data: string };
  olasilik?: Record<string, { brier: number; brier_iklim: number; n: number; kovalar: [number, number, number][] }>;
  aralik?: Record<string, Record<string, number>>;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export function useTimeMachine(input: TimeMachinePlanInput) {
  const { symbol, side, stopAtr, targetR, bars, tf = "5m" } = input;
  const qs = `side=${side}&stop_atr=${stopAtr}&target_r=${targetR}&bars=${bars}&tf=${tf}`;
  return useQuery<TimeMachineResult>({
    queryKey: ["time-machine", symbol, side, stopAtr, targetR, bars, tf],
    queryFn: () => getJson(`/api/time-machine/${encodeURIComponent(symbol)}?${qs}`),
    staleTime: 60_000,
    placeholderData: (prev) => prev,
  });
}

export function useTimeMachineCalibration() {
  return useQuery<TimeMachineCalibration>({
    queryKey: ["time-machine", "calibration"],
    queryFn: () => getJson("/api/time-machine/calibration"),
    staleTime: 60 * 60_000,
  });
}

export function useRangeBand(symbol: string, tf: TmTimeframe = "5m", horizonMin = 60) {
  return useQuery<RangeBand>({
    queryKey: ["time-machine", "band", symbol, tf, horizonMin],
    queryFn: () => getJson(`/api/time-machine/${encodeURIComponent(symbol)}/band?tf=${tf}&horizon_min=${horizonMin}`),
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
    placeholderData: (prev) => prev,
  });
}
