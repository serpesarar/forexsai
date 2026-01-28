"use client";

import { useEffect, useState, useCallback } from "react";
import {
  CandlestickChart,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  Clock,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface CandlestickPattern {
  id: string;
  name: string;
  name_tr: string;
  signal: "bullish" | "bearish" | "neutral";
  strength: number;
  timeframe: string;
  confidence: number;
  description_tr: string;
  action_tr: string;
}

interface TimeframeData {
  patterns: CandlestickPattern[];
  count: number;
  error?: string;
}

interface CandlestickData {
  symbol: string;
  timestamp: string;
  timeframes: Record<string, TimeframeData>;
  all_patterns: CandlestickPattern[];
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  strongest_signal: string | null;
  ml_adjustment: number;
}

interface CandlestickPatternPanelProps {
  symbol?: string;
  className?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIMEFRAME_LABELS: Record<string, string> = {
  "15m": "M15",
  "30m": "M30",
  "1h": "H1",
  "4h": "H4",
};

export default function CandlestickPatternPanel({ 
  symbol = "XAUUSD", 
  className = "" 
}: CandlestickPatternPanelProps) {
  const [data, setData] = useState<CandlestickData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("all");
  const [expandedPattern, setExpandedPattern] = useState<string | null>(null);
  const [activeSymbol, setActiveSymbol] = useState(symbol);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/candlestick-patterns/${activeSymbol}`);
      const result = await response.json();
      
      if (result.success) {
        setData(result.data);
        setError(null);
      } else {
        setError(result.error || "Veri alınamadı");
      }
      setLastUpdate(new Date());
    } catch (err) {
      setError("Bağlantı hatası");
    } finally {
      setLoading(false);
    }
  }, [activeSymbol]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchData]);

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "bullish":
      case "BULLISH":
        return "text-green-400";
      case "bearish":
      case "BEARISH":
        return "text-red-400";
      default:
        return "text-yellow-400";
    }
  };

  const getSignalBg = (signal: string) => {
    switch (signal) {
      case "bullish":
      case "BULLISH":
        return "bg-green-900/20 border-green-500/30";
      case "bearish":
      case "BEARISH":
        return "bg-red-900/20 border-red-500/30";
      default:
        return "bg-yellow-900/20 border-yellow-500/30";
    }
  };

  const getStrengthBars = (strength: number) => {
    return Array.from({ length: 3 }, (_, i) => (
      <div
        key={i}
        className={`w-1.5 h-3 rounded-sm ${
          i < strength ? "bg-current" : "bg-gray-600"
        }`}
      />
    ));
  };

  const filteredPatterns = data?.all_patterns.filter(
    (p) => selectedTimeframe === "all" || p.timeframe === selectedTimeframe
  ) || [];

  if (loading && !data) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 text-amber-400 animate-spin" />
          <span className="ml-2 text-gray-400">Mum formasyonları analiz ediliyor...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-900/50 to-orange-900/50 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CandlestickChart className="w-5 h-5 text-amber-400" />
            <span className="font-semibold text-white">Mum Formasyonları</span>
          </div>
          <div className="flex items-center gap-2">
            {/* Symbol Selector */}
            <select
              value={activeSymbol}
              onChange={(e) => setActiveSymbol(e.target.value)}
              className="bg-gray-800/50 text-xs text-gray-300 border border-gray-600/50 rounded px-2 py-1"
            >
              <option value="XAUUSD">GOLD</option>
              <option value="NAS100">NASDAQ</option>
            </select>
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
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* Summary */}
            <div className="grid grid-cols-4 gap-2">
              <div className="bg-green-900/20 rounded-lg p-2 text-center">
                <div className="text-lg font-bold text-green-400">{data.bullish_count}</div>
                <div className="text-xs text-gray-400">Boğa</div>
              </div>
              <div className="bg-red-900/20 rounded-lg p-2 text-center">
                <div className="text-lg font-bold text-red-400">{data.bearish_count}</div>
                <div className="text-xs text-gray-400">Ayı</div>
              </div>
              <div className="bg-yellow-900/20 rounded-lg p-2 text-center">
                <div className="text-lg font-bold text-yellow-400">{data.neutral_count}</div>
                <div className="text-xs text-gray-400">Nötr</div>
              </div>
              <div className={`rounded-lg p-2 text-center ${getSignalBg(data.strongest_signal || "")}`}>
                <div className={`text-sm font-bold ${getSignalColor(data.strongest_signal || "")}`}>
                  {data.strongest_signal || "—"}
                </div>
                <div className="text-xs text-gray-400">Sinyal</div>
              </div>
            </div>

            {/* ML Adjustment Indicator */}
            {data.ml_adjustment !== 0 && (
              <div className={`rounded-lg p-2 flex items-center justify-between ${
                data.ml_adjustment > 0 ? "bg-green-900/20" : "bg-red-900/20"
              }`}>
                <span className="text-xs text-gray-400">ML Güven Ayarı:</span>
                <span className={`text-sm font-bold ${
                  data.ml_adjustment > 0 ? "text-green-400" : "text-red-400"
                }`}>
                  {data.ml_adjustment > 0 ? "+" : ""}{(data.ml_adjustment * 100).toFixed(0)}%
                </span>
              </div>
            )}

            {/* Timeframe Filter */}
            <div className="flex gap-1">
              <button
                onClick={() => setSelectedTimeframe("all")}
                className={`px-3 py-1 text-xs rounded ${
                  selectedTimeframe === "all"
                    ? "bg-amber-500/30 text-amber-400"
                    : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50"
                }`}
              >
                Tümü
              </button>
              {Object.entries(TIMEFRAME_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setSelectedTimeframe(key)}
                  className={`px-3 py-1 text-xs rounded ${
                    selectedTimeframe === key
                      ? "bg-amber-500/30 text-amber-400"
                      : "bg-gray-800/50 text-gray-400 hover:bg-gray-700/50"
                  }`}
                >
                  {label}
                  {data.timeframes[key]?.count > 0 && (
                    <span className="ml-1 text-amber-400">
                      ({data.timeframes[key].count})
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Pattern List */}
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {filteredPatterns.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <CandlestickChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Bu zaman diliminde aktif formasyon yok</p>
                </div>
              ) : (
                filteredPatterns.map((pattern, idx) => (
                  <div
                    key={`${pattern.id}-${pattern.timeframe}-${idx}`}
                    className={`rounded-lg border transition-all ${getSignalBg(pattern.signal)}`}
                  >
                    {/* Pattern Header */}
                    <button
                      onClick={() => setExpandedPattern(
                        expandedPattern === `${pattern.id}-${idx}` ? null : `${pattern.id}-${idx}`
                      )}
                      className="w-full p-3 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        {pattern.signal === "bullish" ? (
                          <TrendingUp className="w-5 h-5 text-green-400" />
                        ) : pattern.signal === "bearish" ? (
                          <TrendingDown className="w-5 h-5 text-red-400" />
                        ) : (
                          <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        )}
                        <div className="text-left">
                          <div className={`font-medium ${getSignalColor(pattern.signal)}`}>
                            {pattern.name_tr}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Clock className="w-3 h-3" />
                            {TIMEFRAME_LABELS[pattern.timeframe] || pattern.timeframe}
                            <span className="mx-1">•</span>
                            <div className="flex items-center gap-0.5">
                              {getStrengthBars(pattern.strength)}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold ${getSignalColor(pattern.signal)}`}>
                          %{pattern.confidence.toFixed(0)}
                        </span>
                        {expandedPattern === `${pattern.id}-${idx}` ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                    </button>

                    {/* Expanded Details */}
                    {expandedPattern === `${pattern.id}-${idx}` && (
                      <div className="px-3 pb-3 pt-0 border-t border-gray-700/30">
                        <div className="mt-2 space-y-2">
                          <div className="bg-gray-800/50 rounded p-2">
                            <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                              <Info className="w-3 h-3" />
                              Açıklama
                            </div>
                            <p className="text-sm text-gray-300">{pattern.description_tr}</p>
                          </div>
                          <div className={`rounded p-2 ${
                            pattern.signal === "bullish" 
                              ? "bg-green-900/30" 
                              : pattern.signal === "bearish"
                                ? "bg-red-900/30"
                                : "bg-yellow-900/30"
                          }`}>
                            <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                              {pattern.signal === "bullish" ? (
                                <TrendingUp className="w-3 h-3 text-green-400" />
                              ) : pattern.signal === "bearish" ? (
                                <TrendingDown className="w-3 h-3 text-red-400" />
                              ) : (
                                <AlertTriangle className="w-3 h-3 text-yellow-400" />
                              )}
                              Ne Yapmalı?
                            </div>
                            <p className={`text-sm font-medium ${getSignalColor(pattern.signal)}`}>
                              {pattern.action_tr}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
