"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  ArrowUp,
  ArrowDown,
  Info,
  X,
  RefreshCw,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface LevelData {
  type: "resistance" | "current" | "support";
  name: string;
  price: number;
  distance: number;
  distance_display: string;
  strength: "strong" | "normal" | "current";
  is_next?: boolean;
}

interface ClearTrendData {
  symbol: string;
  timeframe: string;
  timestamp: string;
  price: {
    current: number;
    display: string;
    decimals: number;
  };
  trend: {
    direction: "UP" | "DOWN" | "NEUTRAL";
    strength: number;
    strength_percent: number;
    description: string;
    ema_20: number;
    ema_50: number;
  };
  levels: {
    all_levels: LevelData[];
    nearest_resistance: LevelData | null;
    nearest_support: LevelData | null;
    pivot: number;
    range_high: number;
    range_low: number;
  };
  trade_zones: {
    suggestion: string;
    entry_zone?: {
      min: number;
      max: number;
      description: string;
    };
    target?: number;
    stop?: number;
  };
  pip_value: number;
  explanations: Record<string, string>;
}

interface ClearTrendPanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ", icon: "📊" },
  { key: "XAUUSD", label: "XAUUSD", icon: "🥇" },
];

export default function ClearTrendPanel({ symbol: initialSymbol = "NDX.INDX" }: ClearTrendPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<ClearTrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");
  const [explanationModal, setExplanationModal] = useState<{ title: string; content: string } | null>(null);

  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "clear_trend");

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [activeSymbol, timeframe]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/clear-trend/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) {
        setData(json);
      }
    } catch (e) {
      console.error("Clear trend fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (wsData) { setData(wsData); setLoading(false); }
  }, [wsData]);

  useEffect(() => {
    if (!wsData) fetchData();
    if (!wsConnected) {
      const interval = setInterval(fetchData, 120000);
      return () => clearInterval(interval);
    }
  }, [activeSymbol, timeframe, wsConnected]);

  const openExplanation = (key: string, title: string) => {
    if (data?.explanations?.[key]) {
      setExplanationModal({ title, content: data.explanations[key] });
    }
  };

  if (loading && !data) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
        <div className="h-8 bg-gray-800 rounded w-1/3 mb-6" />
        <div className="h-40 bg-gray-800 rounded-lg mb-4" />
        <div className="h-32 bg-gray-800 rounded-lg" />
      </div>
    );
  }

  const getTrendIcon = () => {
    if (!data) return <Minus className="w-8 h-8 text-gray-400" />;
    if (data.trend.direction === "UP") return <TrendingUp className="w-8 h-8 text-green-400" />;
    if (data.trend.direction === "DOWN") return <TrendingDown className="w-8 h-8 text-red-400" />;
    return <Minus className="w-8 h-8 text-yellow-400" />;
  };

  const getTrendColor = () => {
    if (!data) return "text-gray-400";
    if (data.trend.direction === "UP") return "text-green-400";
    if (data.trend.direction === "DOWN") return "text-red-400";
    return "text-yellow-400";
  };

  const getTrendBg = () => {
    if (!data) return "from-gray-800 to-gray-900";
    if (data.trend.direction === "UP") return "from-green-900/40 to-green-800/20";
    if (data.trend.direction === "DOWN") return "from-red-900/40 to-red-800/20";
    return "from-yellow-900/40 to-yellow-800/20";
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 p-3 border-b border-gray-800">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Target className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white truncate">Clear Trend</h2>
              <p className="text-xs text-gray-400 truncate">Simple Trend Analysis</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Symbol Switcher */}
            <div className="flex rounded-lg overflow-hidden border border-gray-700">
              {SYMBOLS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => setActiveSymbol(s.key)}
                  className={`px-3 py-1.5 text-xs font-bold transition-all flex items-center gap-1 ${
                    activeSymbol === s.key
                      ? "bg-blue-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:text-white"
                  }`}
                >
                  <span>{s.icon}</span>
                  {s.label}
                </button>
              ))}
            </div>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="bg-gray-800 text-white text-xs px-2 py-1.5 rounded-lg border border-gray-700"
            >
              <option value="15m">15m</option>
              <option value="1H">1H</option>
              <option value="4H">4H</option>
              <option value="1D">1D</option>
            </select>
            <button
              onClick={fetchData}
              className="p-1.5 bg-gray-800 rounded-lg hover:bg-gray-700"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-gray-400 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {data && (
        <>
          {/* Main Price Display */}
          <div className={`p-6 bg-gradient-to-b ${getTrendBg()} text-center`}>
            <div className="flex items-center justify-center gap-3 mb-2">
              {getTrendIcon()}
              <span className={`text-4xl font-bold ${getTrendColor()}`}>
                {data.price.display}
              </span>
            </div>
            <p className={`text-sm ${getTrendColor()} mb-1`}>
              {data.trend.description}
            </p>
            <div className="flex items-center justify-center gap-2">
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-400">Güç:</span>
                <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${
                      data.trend.direction === "UP"
                        ? "bg-green-500"
                        : data.trend.direction === "DOWN"
                        ? "bg-red-500"
                        : "bg-yellow-500"
                    }`}
                    style={{ width: `${data.trend.strength_percent}%` }}
                  />
                </div>
                <span className="text-xs text-white">{data.trend.strength_percent}%</span>
              </div>
            </div>
          </div>

          {/* Support/Resistance Levels */}
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
                🎯 Support & Resistance Levels
              </h3>
              <button
                onClick={() => openExplanation("support", "What are Support and Resistance?")}
                className="text-gray-500 hover:text-blue-400 transition-colors"
              >
                <Info className="w-4 h-4" />
              </button>
            </div>

            {/* Levels Visual */}
            <div className="space-y-2">
              {data.levels.all_levels.map((level, index) => {
                const isCurrent = level.type === "current";
                const isResistance = level.type === "resistance";
                const isSupport = level.type === "support";
                
                return (
                  <div
                    key={index}
                    onClick={() => {
                      if (isResistance) openExplanation("r1_r2", "Resistance Levels");
                      else if (isSupport) openExplanation("s1_s2", "Support Levels");
                      else openExplanation("pivot", "Pivot Point");
                    }}
                    className={`relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all hover:opacity-80 ${
                      isCurrent
                        ? "bg-blue-600/30 border-2 border-blue-500"
                        : isResistance
                        ? "bg-red-500/20 border border-red-500/50"
                        : "bg-green-500/20 border border-green-500/50"
                    }`}
                  >
                    {/* Level Indicator */}
                    <div className={`w-12 h-8 rounded flex items-center justify-center text-xs font-bold ${
                      isCurrent
                        ? "bg-blue-600 text-white"
                        : isResistance
                        ? "bg-red-500/50 text-red-200"
                        : "bg-green-500/50 text-green-200"
                    }`}>
                      {isCurrent ? "NOW" : level.name.split(" ")[0]}
                    </div>

                    {/* Price */}
                    <div className="flex-1">
                      <div className={`text-lg font-bold ${
                        isCurrent ? "text-white" : isResistance ? "text-red-300" : "text-green-300"
                      }`}>
                        {level.price.toFixed(data.price.decimals)}
                      </div>
                      {level.name && !isCurrent && (
                        <div className="text-xs text-gray-500">
                          {level.name}
                        </div>
                      )}
                    </div>

                    {/* Distance */}
                    <div className={`text-right ${
                      isCurrent ? "text-blue-300" : isResistance ? "text-red-300" : "text-green-300"
                    }`}>
                      <div className="text-sm font-bold">
                        {level.distance_display}
                      </div>
                      <div className="text-xs text-gray-500">
                        {isCurrent ? "Current" : isResistance ? "Above" : "Below"}
                      </div>
                    </div>

                    {/* Next Level Indicator */}
                    {level.is_next && (
                      <div className="absolute -right-1 -top-1 w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center">
                        <ArrowUp className="w-3 h-3 text-black" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-3 mt-4">
              {data.levels.nearest_resistance && (
                <div 
                  onClick={() => openExplanation("resistance", "Nearest Resistance")}
                  className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 cursor-pointer hover:bg-red-500/20 transition-colors"
                >
                  <div className="text-xs text-red-400 mb-1">📈 Nearest Resistance</div>
                  <div className="text-lg font-bold text-red-300">
                    {data.levels.nearest_resistance.price.toFixed(data.price.decimals)}
                  </div>
                  <div className="text-xs text-red-400">
                    {data.levels.nearest_resistance.distance_display} above
                  </div>
                </div>
              )}
              {data.levels.nearest_support && (
                <div 
                  onClick={() => openExplanation("support", "Nearest Support")}
                  className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 cursor-pointer hover:bg-green-500/20 transition-colors"
                >
                  <div className="text-xs text-green-400 mb-1">📉 Nearest Support</div>
                  <div className="text-lg font-bold text-green-300">
                    {data.levels.nearest_support.price.toFixed(data.price.decimals)}
                  </div>
                  <div className="text-xs text-green-400">
                    {data.levels.nearest_support.distance_display} below
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Trade Suggestion */}
          <div className="p-4 bg-gray-800/50 border-t border-gray-800">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
                💡 Trading Suggestion
              </h3>
              <button
                onClick={() => openExplanation("entry_zone", "Entry Zone")}
                className="text-gray-500 hover:text-blue-400 transition-colors"
              >
                <Info className="w-4 h-4" />
              </button>
            </div>
            
            <div className={`rounded-lg p-4 border ${
              data.trend.direction === "UP"
                ? "bg-green-900/20 border-green-600"
                : data.trend.direction === "DOWN"
                ? "bg-red-900/20 border-red-600"
                : "bg-yellow-900/20 border-yellow-600"
            }`}>
              <p className="text-sm text-white mb-3">{data.trade_zones.suggestion}</p>
              
              {data.trade_zones.target && data.trade_zones.stop && (
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-xs text-gray-400 mb-1">🎯 Target</div>
                    <div className="text-xl font-bold text-green-400">
                      {data.trade_zones.target.toFixed(data.price.decimals)}
                    </div>
                    <button
                      onClick={() => openExplanation("target", "Target Price")}
                      className="text-xs text-gray-500 hover:text-blue-400 mt-1"
                    >
                      How is it calculated?
                    </button>
                  </div>
                  <div>
                    <div className="text-xs text-gray-400 mb-1">🛑 Stop</div>
                    <div className="text-xl font-bold text-red-400">
                      {data.trade_zones.stop.toFixed(data.price.decimals)}
                    </div>
                    <button
                      onClick={() => openExplanation("stop", "Stop-Loss")}
                      className="text-xs text-gray-500 hover:text-blue-400 mt-1"
                    >
                      How is it calculated?
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Explanation Modal */}
      {explanationModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl border border-gray-700 max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">{explanationModal.title}</h3>
              <button
                onClick={() => setExplanationModal(null)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-gray-300 leading-relaxed">{explanationModal.content}</p>
            <button
              onClick={() => setExplanationModal(null)}
              className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
