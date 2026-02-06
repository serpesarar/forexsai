"use client";

import { useState, useEffect } from "react";
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
  Eye,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface PulseV3Data {
  symbol: string;
  timestamp: string;
  pulse_score: number;
  max_score: number;
  signal_type: "CONFIRM" | "SCOUT" | "HOLD";
  direction: "BUY" | "SELL" | "NEUTRAL";
  confidence: number;
  price: number;
  timeframes: {
    [key: string]: {
      raw_score: number;
      max: number;
      trend: string;
      details: any;
    };
  };
  levels: {
    r2: number;
    r1: number;
    pivot: number;
    s1: number;
    s2: number;
    target: number;
    stop: number;
  };
  rr_ratio: number;
  suggestion: string;
  entry_zones: Array<{ price: number; share: number; label: string }>;
  notes: string[];
  valid_for_seconds: number;
}

interface PulseV3PanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
];

export default function PulseV3Panel({ symbol: initialSymbol = "NDX.INDX" }: PulseV3PanelProps) {
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<PulseV3Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/panel/pulse-v3/${activeSymbol}`);
      const json = await res.json();
      if (!json.error) {
        setData(json);
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error("PULSE V3 fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [activeSymbol]);

  const getSignalColor = (type: string) => {
    if (type === "CONFIRM") return "from-green-900/60 to-green-800/30";
    if (type === "SCOUT") return "from-yellow-900/60 to-yellow-800/30";
    return "from-gray-900/60 to-gray-800/30";
  };

  const getSignalBadge = (type: string) => {
    if (type === "CONFIRM")
      return { bg: "bg-green-500", text: "GÜÇLÜ SİNYAL", icon: CheckCircle };
    if (type === "SCOUT")
      return { bg: "bg-yellow-500", text: "İZLEME MODU", icon: Eye };
    return { bg: "bg-gray-500", text: "BEKLE", icon: Clock };
  };

  const getTrendIcon = (trend: string) => {
    if (trend === "up") return <ArrowUp className="w-4 h-4 text-green-400" />;
    if (trend === "down")
      return <ArrowDown className="w-4 h-4 text-red-400" />;
    return <Activity className="w-4 h-4 text-yellow-400" />;
  };

  const getTrendColor = (trend: string) => {
    if (trend === "up") return "text-green-400";
    if (trend === "down") return "text-red-400";
    return "text-yellow-400";
  };

  if (loading && !data) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
        <div className="h-10 bg-gray-800 rounded w-2/3 mb-4" />
        <div className="h-32 bg-gray-800 rounded-lg mb-4" />
        <div className="grid grid-cols-3 gap-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const badge = getSignalBadge(data.signal_type);
  const BadgeIcon = badge.icon;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-900/50 to-amber-900/50 p-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                PULSE 3 - HYBRID SCALP
              </h2>
              <p className="text-xs text-gray-400">
                3 Zamanlı • Hızlı • Her 30sn Güncelleme
              </p>
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
                      ? "bg-orange-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:text-white"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <button
              onClick={fetchData}
              className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
            >
              <RefreshCw
                className={`w-4 h-4 text-gray-400 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Main Score + Signal */}
      <div className={`p-6 bg-gradient-to-b ${getSignalColor(data.signal_type)}`}>
        <div className="text-center">
          {/* Score Circle */}
          <div className="relative inline-flex items-center justify-center w-28 h-28 mb-3">
            <svg className="w-28 h-28 -rotate-90">
              <circle
                cx="56"
                cy="56"
                r="48"
                fill="none"
                stroke="#1f2937"
                strokeWidth="8"
              />
              <circle
                cx="56"
                cy="56"
                r="48"
                fill="none"
                stroke={
                  data.signal_type === "CONFIRM"
                    ? "#22c55e"
                    : data.signal_type === "SCOUT"
                      ? "#eab308"
                      : "#6b7280"
                }
                strokeWidth="8"
                strokeDasharray={`${(data.pulse_score / 100) * 301.6} 301.6`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute text-center">
              <span className="text-2xl font-bold text-white">
                {data.pulse_score}
              </span>
              <span className="text-xs text-gray-400 block">/100</span>
            </div>
          </div>

          {/* Signal Badge */}
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${badge.bg} text-black font-bold text-sm`}
          >
            <BadgeIcon className="w-4 h-4" />
            {badge.text}
          </div>

          {/* Direction */}
          <div className="mt-3 flex items-center justify-center gap-2">
            {data.direction === "BUY" ? (
              <TrendingUp className="w-6 h-6 text-green-400" />
            ) : data.direction === "SELL" ? (
              <TrendingDown className="w-6 h-6 text-red-400" />
            ) : (
              <Activity className="w-6 h-6 text-yellow-400" />
            )}
            <span
              className={`text-xl font-bold ${
                data.direction === "BUY"
                  ? "text-green-400"
                  : data.direction === "SELL"
                    ? "text-red-400"
                    : "text-yellow-400"
              }`}
            >
              {data.direction === "BUY"
                ? "ALIŞ"
                : data.direction === "SELL"
                  ? "SATIŞ"
                  : "NÖTR"}
            </span>
          </div>

          {/* Price */}
          <p className="text-gray-400 text-sm mt-1">
            Fiyat: <span className="text-white font-bold">{data.price}</span>
          </p>
        </div>
      </div>

      {/* 3 Timeframe Scores */}
      <div className="grid grid-cols-3 gap-3 p-4">
        {Object.entries(data.timeframes).map(([tf, info]) => (
          <div
            key={tf}
            className="bg-gray-800 rounded-lg p-3 text-center border border-gray-700"
          >
            <div className="text-xs text-gray-500 mb-1 uppercase font-medium">
              {tf}
            </div>
            <div className="flex items-center justify-center gap-1 mb-1">
              {getTrendIcon(info.trend)}
              <span className="text-lg font-bold text-white">
                {info.raw_score}
              </span>
              <span className="text-xs text-gray-500">/{info.max}</span>
            </div>
            <div className={`text-xs ${getTrendColor(info.trend)}`}>
              {info.trend === "up"
                ? "Yukarı"
                : info.trend === "down"
                  ? "Aşağı"
                  : "Nötr"}
            </div>
            {/* Progress bar */}
            <div className="h-1.5 bg-gray-700 rounded-full mt-2 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  info.trend === "up"
                    ? "bg-green-500"
                    : info.trend === "down"
                      ? "bg-red-500"
                      : "bg-yellow-500"
                }`}
                style={{ width: `${(info.raw_score / info.max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Levels + R/R */}
      <div className="grid grid-cols-2 gap-4 px-4 pb-4">
        {/* Levels */}
        <div className="bg-gray-800 rounded-lg p-3">
          <h3 className="text-xs font-medium text-gray-400 mb-2 flex items-center gap-1">
            <Target className="w-3 h-3" /> SEVİYELER
          </h3>
          <div className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-red-400">R2:</span>
              <span className="text-white">{data.levels.r2.toFixed(0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-400">R1:</span>
              <span className="text-white">{data.levels.r1.toFixed(0)}</span>
            </div>
            <div className="flex justify-between bg-blue-900/30 -mx-2 px-2 py-0.5 rounded">
              <span className="text-blue-400">Pivot:</span>
              <span className="text-white font-bold">
                {data.levels.pivot.toFixed(0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-400">S1:</span>
              <span className="text-white">{data.levels.s1.toFixed(0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-green-400">S2:</span>
              <span className="text-white">{data.levels.s2.toFixed(0)}</span>
            </div>
          </div>
        </div>

        {/* Target/Stop/R:R */}
        <div className="bg-gray-800 rounded-lg p-3">
          <h3 className="text-xs font-medium text-gray-400 mb-2 flex items-center gap-1">
            <Brain className="w-3 h-3" /> HEDEf / STOP
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-green-400">Hedef:</span>
              <span className="text-white font-bold">
                {data.levels.target.toFixed(0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-red-400">Stop:</span>
              <span className="text-white font-bold">
                {data.levels.stop.toFixed(0)}
              </span>
            </div>
            <div
              className={`flex justify-between p-1.5 rounded ${
                data.rr_ratio >= 1.5
                  ? "bg-green-900/30"
                  : data.rr_ratio >= 1.2
                    ? "bg-yellow-900/30"
                    : "bg-red-900/30"
              }`}
            >
              <span className="text-gray-300">R/R:</span>
              <span
                className={`font-bold ${
                  data.rr_ratio >= 1.5
                    ? "text-green-400"
                    : data.rr_ratio >= 1.2
                      ? "text-yellow-400"
                      : "text-red-400"
                }`}
              >
                {data.rr_ratio.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Suggestion */}
      <div className="px-4 pb-4">
        <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-lg p-3 border border-blue-800">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4 text-blue-400" />
            <span className="font-medium text-white text-sm">ANALİZ</span>
          </div>
          <p className="text-gray-300 text-sm">{data.suggestion}</p>
        </div>
      </div>

      {/* Entry Zones */}
      {data.entry_zones && data.entry_zones.length > 0 && (
        <div className="px-4 pb-4">
          <h4 className="text-xs font-medium text-gray-400 mb-2">
            GİRİŞ BÖLGELERİ
          </h4>
          <div className="grid grid-cols-3 gap-2">
            {data.entry_zones.map((zone, idx) => (
              <div
                key={idx}
                className="bg-gray-800 rounded-lg p-2 text-center text-sm"
              >
                <p className="text-xs text-gray-500">{zone.label}</p>
                <p className="text-white font-bold">{zone.price}</p>
                <p className="text-xs text-blue-400">%{zone.share}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {data.notes && data.notes.length > 0 && (
        <div className="px-4 pb-3">
          {data.notes.map((note, i) => (
            <div
              key={i}
              className="flex items-center gap-1 text-xs text-yellow-400"
            >
              <AlertTriangle className="w-3 h-3" />
              {note}
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-800/50 border-t border-gray-800 text-center">
        <p className="text-xs text-gray-500">
          {lastUpdate
            ? `Son güncelleme: ${lastUpdate.toLocaleTimeString()}`
            : "Güncelleniyor..."}{" "}
          | Geçerlilik: {(data.valid_for_seconds / 60).toFixed(0)} dk
        </p>
      </div>
    </div>
  );
}
