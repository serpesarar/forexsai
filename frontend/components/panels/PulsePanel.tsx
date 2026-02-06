"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  RefreshCw,
  Brain,
  Zap,
  ArrowUp,
  ArrowDown,
  Clock,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface PulseData {
  symbol: string;
  timeframe: string;
  timestamp: string;
  trend: {
    direction: "up" | "down" | "neutral";
    strength: number;
    label: string;
    strength_pct: number;
    last_5_candles: string[];
  };
  price: {
    current: number;
    change_5: number;
  };
  levels: {
    r2: number;
    r1: number;
    pivot: number;
    s1: { price: number; distance: number; alert: boolean };
    s2: number;
    nearest: string;
    nearest_distance: number;
  };
  momentum: {
    rsi: { value: number; trend: string };
    macd: { value: number; trend: string };
    stochastic: { value: number; trend: string };
  };
  volume: {
    status: string;
    label: string;
  };
  suggestion: {
    text: string;
    target: number;
    stop: number;
    target_distance: number;
    stop_distance: number;
    rr_ratio: number;
    timeframe_estimate: string;
  };
}

interface PulsePanelProps {
  symbol?: string;
  onSwitchMode?: () => void;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
];

export default function PulsePanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: PulsePanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<PulseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState("5m");
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const res = await fetch(`${API_BASE}/api/panel/pulse/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (json.error) {
        setError(json.error);
        setData(null);
      } else {
        setData(json);
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error("PULSE fetch error:", e);
      setError("fetch_error");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [activeSymbol, timeframe]);

  const getTrendColor = (direction: string) => {
    if (direction === "up") return "text-green-400";
    if (direction === "down") return "text-red-400";
    return "text-yellow-400";
  };

  const getTrendBg = (direction: string) => {
    if (direction === "up") return "from-green-900/50 to-green-800/30";
    if (direction === "down") return "from-red-900/50 to-red-800/30";
    return "from-yellow-900/50 to-yellow-800/30";
  };

  if (loading && !data) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
        <div className="h-40 bg-gray-800 rounded-lg mb-4" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-900/50 to-orange-900/50 p-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-600 rounded-lg flex items-center justify-center animate-pulse">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{t("pulse.title")}</h2>
              <p className="text-xs text-gray-400">{t("pulse.subtitle")}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Symbol Switcher */}
            <div className="flex rounded-lg overflow-hidden border border-gray-700">
              {SYMBOLS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => setActiveSymbol(s.key)}
                  className={`px-3 py-1.5 text-xs font-bold transition-all ${
                    activeSymbol === s.key
                      ? "bg-yellow-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:text-white"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="bg-gray-800 text-white text-sm px-3 py-1.5 rounded-lg border border-gray-700"
            >
              <option value="5m">5m</option>
              <option value="15m">15m</option>
            </select>
            <button
              onClick={fetchData}
              className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? "animate-spin" : ""}`} />
            </button>
            {onSwitchMode && (
              <button
                onClick={onSwitchMode}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-xs"
              >
                <Brain className="w-3.5 h-3.5" />
                EMEL
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && !data && !loading && (
        <div className="p-8 text-center">
          <Activity className="w-12 h-12 text-yellow-500 mx-auto mb-3 opacity-50" />
          <p className="text-yellow-400 font-medium mb-1">{activeSymbol}</p>
          <p className="text-gray-400 text-sm">{t("pulse.insufficientData")}</p>
        </div>
      )}

      {data && (
        <>
          {/* Main Trend Gauge */}
          <div className={`p-6 bg-gradient-to-b ${getTrendBg(data.trend.direction)}`}>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                {data.trend.direction === "up" ? (
                  <ArrowUp className="w-8 h-8 text-green-400" />
                ) : data.trend.direction === "down" ? (
                  <ArrowDown className="w-8 h-8 text-red-400" />
                ) : (
                  <Activity className="w-8 h-8 text-yellow-400" />
                )}
                <span className={`text-3xl font-bold ${getTrendColor(data.trend.direction)}`}>
                  {data.trend.label}
                </span>
              </div>
              <p className={`text-xl ${getTrendColor(data.trend.direction)}`}>
                {data.trend.strength_pct}% {t("pulse.strong")}
              </p>
              
              {/* Strength Bar */}
              <div className="w-full max-w-md mx-auto mt-4">
                <div className="h-4 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      data.trend.direction === "up" ? "bg-green-500" :
                      data.trend.direction === "down" ? "bg-red-500" : "bg-yellow-500"
                    }`}
                    style={{ width: `${data.trend.strength_pct}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">({data.trend.strength.toFixed(2)}/1.0)</p>
              </div>

              {/* Last 5 Candles */}
              <div className="flex items-center justify-center gap-1 mt-4">
                <span className="text-xs text-gray-500 mr-2">{t("pulse.last5min")}</span>
                {data.trend.last_5_candles.map((candle, i) => (
                  <span key={i} className="text-lg">
                    {candle === "up" ? "▲" : candle === "down" ? "▼" : "●"}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Price & Time Bar */}
          <div className="flex items-center justify-center gap-8 p-3 bg-gray-800/50 border-b border-gray-800">
            <div className="text-center">
              <span className="text-gray-500 text-xs">💰 {t("pulse.price")}</span>
              <p className="text-xl font-bold text-white">{data.price.current.toFixed(2)}</p>
            </div>
            <div className="text-center">
              <span className="text-gray-500 text-xs">📈 {t("pulse.change5m")}</span>
              <p className={`text-xl font-bold ${data.price.change_5 >= 0 ? "text-green-400" : "text-red-400"}`}>
                {data.price.change_5 >= 0 ? "+" : ""}{data.price.change_5.toFixed(2)}%
              </p>
            </div>
            <div className="text-center">
              <span className="text-gray-500 text-xs">⏱️ {t("pulse.update")}</span>
              <p className="text-sm text-gray-300">{t("pulse.every5s")}</p>
            </div>
          </div>

          {/* Three Column Grid */}
          <div className="grid grid-cols-3 gap-4 p-4">
            {/* Levels */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1">
                🎯 {t("pulse.levels")}
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-red-400">R2:</span>
                  <span className="text-white">{data.levels.r2.toFixed(0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-red-400">R1:</span>
                  <span className="text-white">{data.levels.r1.toFixed(0)}</span>
                </div>
                <div className="flex justify-between bg-blue-900/30 -mx-2 px-2 py-1 rounded">
                  <span className="text-blue-400">{t("pulse.priceLabel")}</span>
                  <span className="text-white font-bold">{data.price.current.toFixed(0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-400">S1:</span>
                  <span className="text-white">
                    {data.levels.s1.price.toFixed(0)}
                    {data.levels.s1.alert && " ⭐"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-400">S2:</span>
                  <span className="text-white">{data.levels.s2.toFixed(0)}</span>
                </div>
              </div>
              {data.levels.s1.alert && (
                <p className="text-xs text-yellow-400 mt-2">
                  ⭐ {t("pulse.nearSupport")} ({data.levels.s1.distance.toFixed(0)} {t("pulse.pts")})
                </p>
              )}
            </div>

            {/* Momentum */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1">
                📊 {t("pulse.momentum")}
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">RSI:</span>
                  <div className="flex items-center gap-1">
                    <span className="text-white">{data.momentum.rsi.value.toFixed(0)}</span>
                    <span className={data.momentum.rsi.trend === "up" ? "text-green-400" : "text-red-400"}>
                      {data.momentum.rsi.trend === "up" ? "▲" : "▼"}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">MACD:</span>
                  <div className="flex items-center gap-1">
                    <span className="text-white">{data.momentum.macd.value > 0 ? "+" : ""}{data.momentum.macd.value.toFixed(2)}</span>
                    <span className={data.momentum.macd.trend === "up" ? "text-green-400" : "text-red-400"}>
                      {data.momentum.macd.trend === "up" ? "▲" : "▼"}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Stoch:</span>
                  <div className="flex items-center gap-1">
                    <span className="text-white">{data.momentum.stochastic.value.toFixed(0)}</span>
                    <span className={data.momentum.stochastic.trend === "up" ? "text-green-400" : "text-red-400"}>
                      {data.momentum.stochastic.trend === "up" ? "▲" : "▼"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Volume */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1">
                💹 {t("pulse.volume")}
              </h3>
              <div className="text-center py-4">
                <p className={`text-2xl font-bold ${
                  data.volume.status === "high" ? "text-green-400" :
                  data.volume.status === "low" ? "text-red-400" : "text-gray-400"
                }`}>
                  {data.volume.label}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  {data.volume.status === "high" ? t("pulse.buyersActive") :
                   data.volume.status === "low" ? t("pulse.lowInterest") : t("pulse.noData")}
                </p>
              </div>
            </div>
          </div>

          {/* AI Suggestion Box */}
          <div className="p-4">
            <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-lg p-4 border border-blue-800">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="w-5 h-5 text-blue-400" />
                <span className="font-medium text-white">💡 {t("pulse.aiComment")}</span>
              </div>
              <p className="text-gray-300 text-sm mb-4">{data.suggestion.text}</p>
              
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-xs text-gray-500">🎯 {t("pulse.target")}</p>
                  <p className="text-green-400 font-bold">{data.suggestion.target.toFixed(0)}</p>
                  <p className="text-xs text-gray-500">+{data.suggestion.target_distance.toFixed(0)} pts</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">🛑 {t("pulse.stop")}</p>
                  <p className="text-red-400 font-bold">{data.suggestion.stop.toFixed(0)}</p>
                  <p className="text-xs text-gray-500">-{data.suggestion.stop_distance.toFixed(0)} pts</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">⚖️ R/R</p>
                  <p className="text-blue-400 font-bold">{data.suggestion.rr_ratio.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">⏱️ {t("pulse.expectation")}</p>
                  <p className="text-gray-300 font-bold">{data.suggestion.timeframe_estimate}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="p-4 pt-0 flex gap-2">
            <button className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2">
              <TrendingUp className="w-5 h-5" />
              {t("pulse.watchUp")}
            </button>
            <button className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2">
              <TrendingDown className="w-5 h-5" />
              {t("pulse.watchDown")}
            </button>
            <button className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2">
              <Activity className="w-5 h-5" />
              {t("pulse.detailedChart")}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
