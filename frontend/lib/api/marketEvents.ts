/**
 * Market Events API Client
 * Mum bazlı "Ne oldu?" bağlamı + grafik olay işaretçileri.
 * Haber akışı bağlı olmasa da çalışır (makro + takvim + seans + teknik anomali).
 */

import { getApiBase } from "./base";

const API_BASE = getApiBase();
const REQUEST_TIMEOUT_MS = 15000;

export interface MacroDriver {
  key: string;
  label: string;
  change_pct: number;
  direction: "up" | "down";
  impact_on_symbol: "bullish" | "bearish" | "neutral";
  is_significant: boolean;
  weight: number;
  note_tr: string;
  note_en: string;
  sparkline: number[];
}

export interface CandleEvent {
  type: "news" | "economic" | "earnings";
  id: string;
  timestamp: string;
  title: string;
  title_tr: string;
  impact?: string;
  direction: string;
  detail_tr?: string;
  detail_en?: string;
  forecast?: string;
  previous?: string;
  score?: number;
  url?: string;
  source?: string;
}

export interface CandleContextResponse {
  success: boolean;
  error?: string;
  symbol: string;
  symbol_display?: string;
  timeframe?: string;
  candle?: {
    timestamp: number;
    start_utc: string;
    end_utc: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    change_pct: number;
    range_pct: number;
    direction: "up" | "down" | "flat";
    gap_pct: number | null;
  };
  significance?: {
    is_significant: boolean;
    magnitude: "minor" | "notable" | "big" | "extreme";
    magnitude_tr: string;
    magnitude_en: string;
    range_vs_atr: number | null;
    range_percentile: number | null;
    volume_ratio: number | null;
    body_ratio: number | null;
  };
  session?: {
    session: string;
    emoji: string;
    label_tr: string;
    label_en: string;
    ny_time?: string;
    is_holiday: boolean;
    is_half_day: boolean;
    session_overlap: boolean;
    open_proximity_tr?: string | null;
    open_proximity_en?: string | null;
  };
  macro?: MacroDriver[];
  events?: CandleEvent[];
  explanation?: {
    summary_tr: string;
    summary_en: string;
    bullets_tr: string[];
    bullets_en: string[];
    technical_tr: string;
    technical_en: string;
    confidence: number;
    sources: string[];
  };
}

export interface EventMarker {
  id: string;
  time: string | number;
  position: "aboveBar" | "belowBar" | "inBar";
  color: string;
  shape: "circle" | "square" | "arrowUp" | "arrowDown";
  text: string;
  size: number;
  headline: string;
  headline_en?: string;
  direction: string;
  score: number;
  urgency: string;
  catalyst_type?: "news" | "economic" | "earnings" | "macro" | "anomaly";
  is_economic_event?: boolean;
  is_earnings_event?: boolean;
  event_name?: string;
  event_id?: string | null;
  reasoning_tr?: string;
  importance_level?: string;
  importance_score?: number;
  importance_reason?: string;
  ai_confidence?: number;
  url?: string;
}

async function fetchWithTimeout(url: string): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

/** Tıklanan mumun tam "Ne oldu?" bağlamını getirir. */
export async function fetchCandleContext(
  symbol: string,
  timestampSeconds: number,
  timeframe: string,
  lang: string = "tr"
): Promise<CandleContextResponse> {
  const params = new URLSearchParams({
    symbol,
    timestamp: String(Math.floor(timestampSeconds)),
    timeframe,
    lang,
  });
  const res = await fetchWithTimeout(`${API_BASE}/api/market-events/candle-context?${params}`);
  if (!res.ok) {
    throw new Error(`candle-context failed: ${res.status}`);
  }
  return res.json();
}

/** Grafik olay işaretçilerini getirir (takvim + haber + makro spike + anomali). */
export async function fetchEventMarkers(
  symbol: string,
  hours: number = 168,
  timeframe: string = "1h",
  maxMarkers: number = 80
): Promise<{ success: boolean; markers: EventMarker[] }> {
  const params = new URLSearchParams({
    hours: String(hours),
    timeframe,
    max_markers: String(maxMarkers),
  });
  const res = await fetchWithTimeout(
    `${API_BASE}/api/market-events/markers/${encodeURIComponent(symbol)}?${params}`
  );
  if (!res.ok) {
    throw new Error(`event markers failed: ${res.status}`);
  }
  return res.json();
}
