/**
 * Multi-Timeframe Analysis Hook
 * ==============================
 * Fetches MTF technical analysis data from backend API.
 * Includes EMA, Bollinger Bands, ATR, Volume, and MTF Confluence.
 */

import { useState, useEffect, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Timeframe = "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1";
export type Signal = "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL";
export type Trend = "BULLISH" | "BEARISH" | "NEUTRAL";
export type VolatilityLevel = "LOW" | "NORMAL" | "HIGH" | "EXTREME";

export interface EMAData {
  ema20: number;
  ema50: number;
  ema200: number;
  ema20_distance: number;
  ema50_distance: number;
  ema200_distance: number;
  price_above_ema20: boolean;
  price_above_ema50: boolean;
  price_above_ema200: boolean;
}

export interface BollingerBands {
  upper: number;
  middle: number;
  lower: number;
  bandwidth: number;
  percent_b: number;
  squeeze: boolean;
}

export interface ATRData {
  atr14: number;
  atr_percent: number;
  volatility_level: VolatilityLevel;
  dynamic_sl_pips: number;
  dynamic_tp_pips: number;
}

export interface VolumeAnalysis {
  current_volume: number;
  avg_volume_20: number;
  volume_ratio: number;
  volume_trend: "INCREASING" | "DECREASING" | "STABLE";
  volume_confirmation: boolean;
}

export interface SupportResistance {
  price: number;
  kind: "support" | "resistance";
  strength: number;
  distance_pips: number;
  touches: number;
}

export interface TimeframeAnalysis {
  timeframe: Timeframe;
  current_price: number;
  trend: Trend;
  signal: Signal;
  confidence: number;
  
  ema: EMAData;
  bollinger: BollingerBands;
  atr: ATRData;
  volume: VolumeAnalysis;
  
  rsi14: number;
  macd_signal: "BULLISH" | "BEARISH" | "NEUTRAL";
  
  supports: SupportResistance[];
  resistances: SupportResistance[];
  
  max_pip_threshold: number;
}

export interface MarketRegime {
  regime: "TRENDING" | "RANGING" | "VOLATILE";
  adx: number;
  plus_di: number;
  minus_di: number;
  trend_strength: "WEAK" | "MODERATE" | "STRONG" | "VERY_STRONG";
  trend_direction: Trend | null;
  di_spread: number;
  confidence_level: "HIGH_CONFIDENCE" | "LOW_CONFIDENCE" | "CONFLICTING";
  regime_quality: number;
}

export interface PriceAction {
  structure: "HH_HL" | "LL_LH" | "RANGING" | "CHOPPY";
  swing_highs: number[];
  swing_lows: number[];
  last_swing_high: number;
  last_swing_low: number;
  break_of_structure: boolean;
  change_of_character: boolean;
  liquidity_sweep: boolean;
  equal_highs_count: number;
  equal_lows_count: number;
  structure_quality: "VALID_BREAKOUT" | "FAKEOUT_TRAP" | "CHOPPY" | "AWAITING_CONFIRMATION";
}

export interface VolumeProfileData {
  poc: number;
  value_area_high: number;
  value_area_low: number;
  high_volume_nodes: number[];
  low_volume_nodes: number[];
  hvn_resistances: number[];
  hvn_supports: number[];
  poc_is_relevant: boolean;
}

export interface PivotPoints {
  pivot: number;
  r1: number;
  r2: number;
  r3: number;
  s1: number;
  s2: number;
  s3: number;
  timeframe: "DAILY" | "WEEKLY";
  pivot_type: "FIBONACCI" | "CLASSIC" | "CAMARILLA";
}

export interface CorrelationData {
  dxy_correlation: number;
  dxy_trend: Trend;
  dxy_strength: number;
  vix_level: number;
  vix_regime: "LOW" | "NORMAL" | "HIGH" | "EXTREME";
  bond_yield_trend: Trend;
  bond_yield_level: number;
  spx_trend: Trend;
  correlation_confirms: boolean;
  confluence_score: number;
  conflicting_signals: string[];
}

export interface PositionSizing {
  recommended_risk_percent: number;
  base_risk_percent: number;
  volatility_adjustment: number;
  correlation_adjustment: number;
  stop_loss_pips: number;
  take_profit_pips: number;
  risk_reward_ratio: number;
  position_size_lots: number;
  max_loss_usd: number;
  potential_profit_usd: number;
  session: "ASIA" | "LONDON" | "NEW_YORK" | "OVERLAP";
  session_volatility: "LOW" | "NORMAL" | "HIGH" | "EXTREME";
  high_impact_event: string | null;
}

export interface AdvancedAnalysis {
  market_regime: MarketRegime;
  price_action: PriceAction;
  volume_profile: VolumeProfileData;
  pivot_points: PivotPoints;
  position_sizing: PositionSizing;
  correlation: CorrelationData | null;
}

export interface MTFConfluence {
  overall_signal: Signal;
  overall_confidence: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  strongest_timeframe: Timeframe;
  weakest_timeframe: Timeframe;
  alignment_score: number;
  recommendation: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  market_regime: MarketRegime | null;
  price_action: PriceAction | null;
  volume_profile: VolumeProfileData | null;
  pivot_points: PivotPoints | null;
  correlation: CorrelationData | null;
  position_sizing: PositionSizing | null;
}

export interface MTFAnalysisResult {
  success: boolean;
  symbol: string;
  timestamp: string;
  current_price: number;
  pip_value: number;
  timeframes: Record<Timeframe, TimeframeAnalysis>;
  confluence: MTFConfluence;
  advanced?: AdvancedAnalysis;
}

export interface SingleTimeframeResult {
  success: boolean;
  symbol: string;
  timeframe: Timeframe;
  timestamp: string;
  analysis: TimeframeAnalysis;
}

export function useMTFAnalysis(symbol: string, refreshInterval: number = 30000) {
  const [data, setData] = useState<MTFAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/mtf/analysis?symbol=${encodeURIComponent(symbol)}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        setData(result);
        setError(null);
      } else {
        setError(result.error || "Failed to fetch MTF analysis");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchData();
    
    const interval = setInterval(fetchData, refreshInterval);
    
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return { data, isLoading, error, refetch: fetchData };
}

export function useSingleTimeframeAnalysis(
  symbol: string, 
  timeframe: Timeframe,
  refreshInterval: number = 30000
) {
  const [data, setData] = useState<TimeframeAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/mtf/timeframe/${encodeURIComponent(symbol)}/${timeframe}`
      );
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const result: SingleTimeframeResult = await response.json();
      
      if (result.success) {
        setData(result.analysis);
        setError(null);
      } else {
        setError("Failed to fetch timeframe analysis");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    fetchData();
    
    const interval = setInterval(fetchData, refreshInterval);
    
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return { data, isLoading, error, refetch: fetchData };
}

export function useConfluence(symbol: string, refreshInterval: number = 30000) {
  const [confluence, setConfluence] = useState<MTFConfluence | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/mtf/confluence/${encodeURIComponent(symbol)}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success && result.confluence) {
        setConfluence(result.confluence);
        setError(null);
      } else {
        setError("Failed to fetch confluence data");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchData();
    
    const interval = setInterval(fetchData, refreshInterval);
    
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return { confluence, isLoading, error, refetch: fetchData };
}
