"use client";

import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CachedSymbolData {
  symbol: string;
  updated_at: string;
  ml_prediction: {
    symbol: string;
    direction: string;
    confidence: number;
    probability_up: number;
    probability_down: number;
    entry_price: number;
    target_price: number;
    stop_price: number;
    risk_reward: number;
    technical_score: number;
    momentum_score: number;
    trend_score: number;
    volatility_regime: string;
  };
  ta_snapshot: {
    current_price: number;
    trend: string;
    supports: Array<{ price: number; strength: number; hits: number }>;
    resistances: Array<{ price: number; strength: number; hits: number }>;
    ema: { ema20: number; ema50: number; ema200: number };
    rsi: number;
    volatility: string;
  };
  macro: {
    dxy: { symbol: string; price: number | null };
    vix: { symbol: string; price: number | null };
    usdtry: { symbol: string; price: number | null };
  };
  session: { current: string; hour_utc: number };
  volume: { status: string; ratio: number };
  volatility: { level: string; vix: number | null };
  news: {
    headlines: Array<{ title: string; source?: string }>;
    count: number;
  };
  current_price?: number;
}

async function fetchCachedData(symbol: string): Promise<CachedSymbolData | null> {
  try {
    const res = await fetch(`${API_BASE}/api/data/cached/${encodeURIComponent(symbol)}`);
    if (!res.ok) return null;
    const json = await res.json();
    if (json.success && json.data) {
      // Handle both context_pack (full) and individual fields
      const data = json.data.context_pack || json.data;
      return {
        symbol: data.symbol || symbol,
        updated_at: data.updated_at || json.data.updated_at,
        ml_prediction: data.ml_prediction || json.data.ml_prediction || {},
        ta_snapshot: data.ta_snapshot || json.data.ta_snapshot || {},
        macro: data.macro || json.data.macro || {},
        session: data.session || json.data.session || {},
        volume: data.volume || json.data.volume || {},
        volatility: data.volatility || json.data.volatility || {},
        news: data.news || json.data.news || { headlines: [], count: 0 },
        current_price: data.current_price || json.data.current_price,
      };
    }
    return null;
  } catch (error) {
    console.error(`Failed to fetch cached data for ${symbol}:`, error);
    return null;
  }
}

export function useCachedDashboardData() {
  // Fetch cached data for both symbols
  const nasdaqQuery = useQuery({
    queryKey: ["cached-dashboard", "NDX.INDX"],
    queryFn: () => fetchCachedData("NDX.INDX"),
    staleTime: 5000,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const xauusdQuery = useQuery({
    queryKey: ["cached-dashboard", "XAUUSD"],
    queryFn: () => fetchCachedData("XAUUSD"),
    staleTime: 5000,
    refetchInterval: 5000,
  });

  const isLoading = nasdaqQuery.isLoading || xauusdQuery.isLoading;
  const hasData = !!(nasdaqQuery.data || xauusdQuery.data);

  return {
    nasdaq: nasdaqQuery.data,
    xauusd: xauusdQuery.data,
    isLoading,
    hasData,
    refetch: () => {
      nasdaqQuery.refetch();
      xauusdQuery.refetch();
    },
  };
}

// Helper to convert cached data to signal card format
export function cachedToSignalCard(cached: CachedSymbolData | null, symbol: string) {
  if (!cached) return null;

  const ta: any = cached.ta_snapshot || {};
  const ml: any = cached.ml_prediction || {};
  const currentPrice = cached.current_price || ta.current_price || 0;

  const supports = (ta.supports || []).map((s: any) => ({
    price: s.price,
    type: "support" as const,
    strength: s.strength || 0.5,
    reliability: 0.7,
    hits: s.hits || 5,
    lastTouched: new Date().toISOString(),
    distance: Number((currentPrice - s.price).toFixed(2)),
    distancePct: Number((((currentPrice - s.price) / (currentPrice || 1)) * 100).toFixed(2)),
  }));

  const resistances = (ta.resistances || []).map((r: any) => ({
    price: r.price,
    type: "resistance" as const,
    strength: r.strength || 0.5,
    reliability: 0.7,
    hits: r.hits || 5,
    lastTouched: new Date().toISOString(),
    distance: Number((currentPrice - r.price).toFixed(2)),
    distancePct: Number((((currentPrice - r.price) / (currentPrice || 1)) * 100).toFixed(2)),
  }));

  const sr = [...supports.slice(0, 2), ...resistances.slice(0, 2)];
  const nearestSupport = supports[0] || { price: 0, distance: 0, distancePct: 0 };
  const nearestResistance = resistances[0] || { price: 0, distance: 0, distancePct: 0 };

  const ema = ta.ema || {};
  const ema20 = ema.ema20 || currentPrice;
  const ema50 = ema.ema50 || currentPrice;
  const ema200 = ema.ema200 || currentPrice;

  // Determine trend from ML prediction or TA
  const direction = ml.direction || "NEUTRAL";
  const trend = direction === "UP" ? "BULLISH" : direction === "DOWN" ? "BEARISH" : "NEUTRAL";
  const confidence = Math.round((ml.confidence || 0.5) * 100);

  return {
    symbol,
    currentPrice,
    signal: direction === "UP" ? "BUY" : direction === "DOWN" ? "SELL" : "HOLD",
    confidence,
    trend,
    trendStrength: confidence,
    volatility: cached.volatility?.level || ta.volatility || "MEDIUM",
    volumeConfirmed: cached.volume?.status === "STRONG",
    metrics: [
      { label: "RSI", value: `${Math.round(ta.rsi || 50)} (Neutral)` },
      { label: "Trend", value: trend },
      { label: "Support", value: `${nearestSupport.price?.toLocaleString() || "--"} (${Math.round((nearestSupport.strength || 0.5) * 10)}/10)` },
      { label: "Volatility", value: cached.volatility?.level || "Medium" },
    ],
    liveMetrics: {
      supportResistance: sr,
      nearestSupport: { price: nearestSupport.price, distance: nearestSupport.distance, distancePct: nearestSupport.distancePct },
      nearestResistance: { price: nearestResistance.price, distance: nearestResistance.distance, distancePct: nearestResistance.distancePct },
      trendChannel: {
        distanceToUpper: 100,
        distanceToLower: -100,
        trendStrength: confidence / 100,
        channelWidth: 200,
        rSquared: 0.75,
        slope: direction === "UP" ? 0.5 : direction === "DOWN" ? -0.5 : 0,
        trendQuality: confidence > 70 ? "strong" : confidence > 50 ? "moderate" : "weak",
      },
      emaDistances: {
        ema20: { distance: Number((currentPrice - ema20).toFixed(2)), distancePct: Number((((currentPrice - ema20) / (currentPrice || 1)) * 100).toFixed(2)), emaValue: ema20, period: 20 },
        ema50: { distance: Number((currentPrice - ema50).toFixed(2)), distancePct: Number((((currentPrice - ema50) / (currentPrice || 1)) * 100).toFixed(2)), emaValue: ema50, period: 50 },
        ema200: { distance: Number((currentPrice - ema200).toFixed(2)), distancePct: Number((((currentPrice - ema200) / (currentPrice || 1)) * 100).toFixed(2)), emaValue: ema200, period: 200 },
      },
    },
    reasons: ml.direction === "UP" 
      ? ["ML Model: Bullish signal", `Confidence: ${confidence}%`]
      : ml.direction === "DOWN"
        ? ["ML Model: Bearish signal", `Confidence: ${confidence}%`]
        : ["Market consolidating", "Wait for clearer signal"],
  };
}
