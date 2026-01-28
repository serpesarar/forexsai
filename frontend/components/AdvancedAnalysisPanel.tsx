"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Shield,
  BarChart3,
  Zap,
  Droplets,
  Calendar,
  RefreshCw,
} from "lucide-react";

interface MTFAdvancedData {
  market_regime: {
    regime: string;
    adx: number;
    plus_di: number;
    minus_di: number;
    di_spread: number;
    confidence_level: string;
    trend_direction: string | null;
    regime_quality: number;
  };
  price_action: {
    structure: string;
    structure_quality: string;
    liquidity_sweep: boolean;
    equal_highs_count: number;
    equal_lows_count: number;
    break_of_structure: boolean;
  };
  volume_profile: {
    poc: number;
    hvn_resistances: number[];
    hvn_supports: number[];
    poc_is_relevant: boolean;
  };
  pivot_points: {
    pivot: number;
    r1: number;
    r2: number;
    r3: number;
    s1: number;
    s2: number;
    s3: number;
    pivot_type: string;
  };
  position_sizing: {
    recommended_risk_percent: number;
    volatility_adjustment: number;
    session: string;
    session_volatility: string;
    high_impact_event: string | null;
  };
  correlation: {
    dxy_trend: string;
    vix_level: number;
    vix_regime: string;
    correlation_confirms: boolean;
    conflicting_signals: string[];
  } | null;
}

interface AdvancedAnalysisPanelProps {
  symbol: string;
  className?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdvancedAnalysisPanel({ symbol, className = "" }: AdvancedAnalysisPanelProps) {
  const [data, setData] = useState<MTFAdvancedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const normalizedSymbol = symbol.toUpperCase() === "NASDAQ" ? "NDX.INDX" : symbol;
      const res = await fetch(`${API_BASE}/api/mtf-analysis/${normalizedSymbol}`);
      
      if (!res.ok) throw new Error("Failed to fetch MTF analysis");
      
      const json = await res.json();
      
      if (json.success && json.advanced) {
        setData(json.advanced);
        setLastUpdate(new Date());
        setError(null);
      } else {
        setError("No advanced data available");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4 ${className}`}>
        <div className="flex items-center justify-center h-48">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-red-700/50 p-4 ${className}`}>
        <div className="text-red-400 text-sm">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const { market_regime, price_action, volume_profile, pivot_points, position_sizing, correlation } = data;

  // Determine colors based on regime
  const regimeColor = market_regime.regime === "TRENDING" 
    ? "text-green-400" 
    : market_regime.regime === "RANGING" 
      ? "text-yellow-400" 
      : "text-red-400";

  const confidenceColor = market_regime.confidence_level === "HIGH_CONFIDENCE"
    ? "text-green-400"
    : market_regime.confidence_level === "LOW_CONFIDENCE"
      ? "text-yellow-400"
      : "text-red-400";

  const structureColor = price_action.structure_quality === "VALID_BREAKOUT"
    ? "text-green-400"
    : price_action.structure_quality === "FAKEOUT_TRAP"
      ? "text-red-400"
      : "text-yellow-400";

  const sessionColor = position_sizing.session === "OVERLAP"
    ? "text-purple-400"
    : position_sizing.session === "NEW_YORK"
      ? "text-blue-400"
      : position_sizing.session === "LONDON"
        ? "text-cyan-400"
        : "text-gray-400";

  return (
    <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span className="font-semibold text-white">MTF Advanced Analysis</span>
            <span className="text-xs text-gray-400 ml-2">{symbol}</span>
          </div>
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <button 
              onClick={fetchData}
              className="p-1 hover:bg-gray-700/50 rounded"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* High Impact Event Warning */}
        {position_sizing.high_impact_event && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <div className="text-red-400 font-semibold text-sm">
                {position_sizing.high_impact_event === "NFP_DAY" && "🔴 NFP GÜNÜ - Trade Önerilmez!"}
                {position_sizing.high_impact_event === "FOMC_POTENTIAL" && "🟠 FOMC Potansiyeli - Dikkatli Ol"}
                {position_sizing.high_impact_event === "CPI_WEEK" && "🟡 CPI Haftası - Volatilite Bekleniyor"}
              </div>
              <div className="text-red-300/70 text-xs">Risk %{position_sizing.volatility_adjustment * 100} oranında azaltıldı</div>
            </div>
          </div>
        )}

        {/* Liquidity Sweep Warning */}
        {price_action.liquidity_sweep && (
          <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-3 flex items-center gap-3">
            <Droplets className="w-5 h-5 text-yellow-400 flex-shrink-0" />
            <div>
              <div className="text-yellow-400 font-semibold text-sm">💧 Likidite Süpürmesi Tespit Edildi</div>
              <div className="text-yellow-300/70 text-xs">Ters hareket riski - Dikkatli ol</div>
            </div>
          </div>
        )}

        {/* Grid Layout */}
        <div className="grid grid-cols-2 gap-3">
          {/* Market Regime */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <span className="text-xs text-gray-400">Market Regime</span>
            </div>
            <div className={`text-lg font-bold ${regimeColor}`}>
              {market_regime.regime}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-500">ADX: {market_regime.adx.toFixed(1)}</span>
              <span className="text-xs text-gray-500">|</span>
              <span className={`text-xs ${confidenceColor}`}>
                {market_regime.confidence_level.replace("_", " ")}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              DI Spread: {market_regime.di_spread.toFixed(1)}
            </div>
          </div>

          {/* Price Action */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              {price_action.structure.includes("HH") ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : price_action.structure.includes("LL") ? (
                <TrendingDown className="w-4 h-4 text-red-400" />
              ) : (
                <Activity className="w-4 h-4 text-yellow-400" />
              )}
              <span className="text-xs text-gray-400">Price Action</span>
            </div>
            <div className={`text-lg font-bold ${structureColor}`}>
              {price_action.structure_quality.replace("_", " ")}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Structure: {price_action.structure}
            </div>
            {(price_action.equal_highs_count >= 2 || price_action.equal_lows_count >= 2) && (
              <div className="text-xs text-yellow-400 mt-1">
                {price_action.equal_highs_count >= 2 && `🎯 ${price_action.equal_highs_count}x EQ Highs`}
                {price_action.equal_lows_count >= 2 && ` 🎯 ${price_action.equal_lows_count}x EQ Lows`}
              </div>
            )}
          </div>

          {/* Session Info */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-gray-400">Trading Session</span>
            </div>
            <div className={`text-lg font-bold ${sessionColor}`}>
              {position_sizing.session}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Volatilite: {position_sizing.session_volatility}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Risk Ayarı: {(position_sizing.volatility_adjustment * 100).toFixed(0)}%
            </div>
          </div>

          {/* Position Sizing */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-gray-400">Position Sizing</span>
            </div>
            <div className="text-lg font-bold text-emerald-400">
              %{position_sizing.recommended_risk_percent.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Önerilen Risk
            </div>
          </div>
        </div>

        {/* Pivot Points */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-amber-400" />
            <span className="text-xs text-gray-400">Fibonacci Pivot Points</span>
            <span className="text-xs text-amber-400/70 ml-auto">{pivot_points.pivot_type}</span>
          </div>
          <div className="grid grid-cols-7 gap-1 text-center text-xs">
            <div className="bg-red-900/30 rounded p-1">
              <div className="text-red-400 font-medium">R3</div>
              <div className="text-gray-300">{pivot_points.r3.toFixed(1)}</div>
            </div>
            <div className="bg-red-900/50 rounded p-1 ring-1 ring-red-500/50">
              <div className="text-red-400 font-bold">R2★</div>
              <div className="text-gray-300">{pivot_points.r2.toFixed(1)}</div>
            </div>
            <div className="bg-red-900/30 rounded p-1">
              <div className="text-red-400 font-medium">R1</div>
              <div className="text-gray-300">{pivot_points.r1.toFixed(1)}</div>
            </div>
            <div className="bg-gray-700/50 rounded p-1">
              <div className="text-gray-400 font-medium">P</div>
              <div className="text-white">{pivot_points.pivot.toFixed(1)}</div>
            </div>
            <div className="bg-green-900/30 rounded p-1">
              <div className="text-green-400 font-medium">S1</div>
              <div className="text-gray-300">{pivot_points.s1.toFixed(1)}</div>
            </div>
            <div className="bg-green-900/50 rounded p-1 ring-1 ring-green-500/50">
              <div className="text-green-400 font-bold">S2★</div>
              <div className="text-gray-300">{pivot_points.s2.toFixed(1)}</div>
            </div>
            <div className="bg-green-900/30 rounded p-1">
              <div className="text-green-400 font-medium">S3</div>
              <div className="text-gray-300">{pivot_points.s3.toFixed(1)}</div>
            </div>
          </div>
          <div className="text-xs text-amber-400/70 mt-2 text-center">
            ★ R2/S2 (0.618 Fib) = En Güçlü Seviyeler
          </div>
        </div>

        {/* HVN Support/Resistance */}
        {(volume_profile.hvn_resistances.length > 0 || volume_profile.hvn_supports.length > 0) && (
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-400">HVN S/R (Gerçek Seviyeler)</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-red-400 mb-1">Dirençler</div>
                <div className="space-y-1">
                  {volume_profile.hvn_resistances.slice(0, 3).map((r, i) => (
                    <div key={i} className="text-xs text-gray-300 bg-red-900/20 rounded px-2 py-1">
                      {r.toFixed(2)}
                    </div>
                  ))}
                  {volume_profile.hvn_resistances.length === 0 && (
                    <div className="text-xs text-gray-500">Tespit edilemedi</div>
                  )}
                </div>
              </div>
              <div>
                <div className="text-xs text-green-400 mb-1">Destekler</div>
                <div className="space-y-1">
                  {volume_profile.hvn_supports.slice(0, 3).map((s, i) => (
                    <div key={i} className="text-xs text-gray-300 bg-green-900/20 rounded px-2 py-1">
                      {s.toFixed(2)}
                    </div>
                  ))}
                  {volume_profile.hvn_supports.length === 0 && (
                    <div className="text-xs text-gray-500">Tespit edilemedi</div>
                  )}
                </div>
              </div>
            </div>
            {volume_profile.poc_is_relevant && (
              <div className="text-xs text-purple-400 mt-2">
                POC: {volume_profile.poc.toFixed(2)} (Fiyat yakınında)
              </div>
            )}
          </div>
        )}

        {/* Correlation */}
        {correlation && (
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-gray-400">Korelasyon Analizi</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-gray-500">DXY</div>
                <div className={correlation.dxy_trend === "BULLISH" ? "text-green-400" : correlation.dxy_trend === "BEARISH" ? "text-red-400" : "text-gray-400"}>
                  {correlation.dxy_trend}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">VIX</div>
                <div className={correlation.vix_regime === "HIGH" || correlation.vix_regime === "EXTREME" ? "text-red-400" : "text-green-400"}>
                  {correlation.vix_level?.toFixed(1)} ({correlation.vix_regime})
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Onay</div>
                <div className={correlation.correlation_confirms ? "text-green-400" : "text-red-400"}>
                  {correlation.correlation_confirms ? "✓ Onaylı" : "✗ Çelişkili"}
                </div>
              </div>
            </div>
            {correlation.conflicting_signals && correlation.conflicting_signals.length > 0 && (
              <div className="mt-2 text-xs text-red-400">
                ⚠️ {correlation.conflicting_signals.join(", ")}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
