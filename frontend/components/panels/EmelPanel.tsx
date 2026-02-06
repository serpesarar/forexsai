"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Target,
  Layers,
  Gauge,
  Volume2,
  Brain,
  Shield,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface CheckItem {
  id: number;
  name: string;
  subtitle: string;
  status: "pass" | "warning" | "fail";
  direction: "up" | "down" | "neutral";
  color: "green" | "yellow" | "red";
  label: string;
  details: Record<string, any>;
  comment: string;
}

interface EmelData {
  symbol: string;
  timeframe: string;
  signal: string;
  confidence: number;
  price: number;
  checks: CheckItem[];
  summary: {
    green_count: number;
    yellow_count: number;
    red_count: number;
    decision: string;
    rejections: string[];
    entry_conditions: string[];
  };
}

interface EmelPanelProps {
  symbol?: string;
  onSwitchMode?: () => void;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
];

const CHECK_ICONS: Record<number, any> = {
  1: TrendingUp,
  2: Activity,
  3: Layers,
  4: Target,
  5: BarChart3,
  6: Gauge,
  7: Volume2,
  8: Brain,
  9: Shield,
};

export default function EmelPanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: EmelPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<EmelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/panel/emel/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) {
        setData(json);
      }
    } catch (e) {
      console.error("EMEL fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [activeSymbol, timeframe]);

  const getColorClass = (color: string) => {
    switch (color) {
      case "green":
        return "bg-green-500/20 border-green-500 text-green-400";
      case "yellow":
        return "bg-yellow-500/20 border-yellow-500 text-yellow-400";
      case "red":
        return "bg-red-500/20 border-red-500 text-red-400";
      default:
        return "bg-gray-500/20 border-gray-500 text-gray-400";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pass":
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case "fail":
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return null;
    }
  };

  if (loading && !data) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
        <div className="h-8 bg-gray-800 rounded w-1/3 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 p-3 border-b border-gray-800">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white truncate">{t("emel.title")}</h2>
              <p className="text-xs text-gray-400 truncate">{t("emel.subtitle")}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Symbol Switcher */}
            <div className="flex rounded-lg overflow-hidden border border-gray-700">
              {SYMBOLS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => setActiveSymbol(s.key)}
                  className={`px-2 py-1 text-xs font-bold transition-all ${
                    activeSymbol === s.key
                      ? "bg-blue-600 text-white"
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
              className="bg-gray-800 text-white text-xs px-2 py-1 rounded-lg border border-gray-700"
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
            {onSwitchMode && (
              <button
                onClick={onSwitchMode}
                className="flex items-center gap-1 bg-yellow-600 hover:bg-yellow-700 text-white px-2 py-1 rounded-lg text-xs"
              >
                <Zap className="w-3 h-3" />
                PULSE
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {data && (
        <div className="grid grid-cols-4 gap-4 p-4 bg-gray-800/50">
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-500 mb-1">{t("emel.signal")}</p>
            <p className={`text-xl font-bold ${
              data.signal === "BUY" ? "text-green-400" :
              data.signal === "SELL" ? "text-red-400" : "text-yellow-400"
            }`}>
              {data.signal}
            </p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-500 mb-1">{t("emel.confidence")}</p>
            <p className="text-xl font-bold text-blue-400">%{data.confidence.toFixed(0)}</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-500 mb-1">{t("emel.price")}</p>
            <p className="text-xl font-bold text-white">{data.price.toFixed(2)}</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-500 mb-1">{t("emel.score")}</p>
            <div className="flex items-center justify-center gap-1">
              <span className="text-green-400">{data.summary.green_count}🟢</span>
              <span className="text-yellow-400">{data.summary.yellow_count}🟡</span>
              <span className="text-red-400">{data.summary.red_count}🔴</span>
            </div>
          </div>
        </div>
      )}

      {/* 9 Checkpoint Cards */}
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
          📋 {t("emel.checkpoints")} ({data?.checks.length || 0}/9 {t("emel.active")})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data?.checks.map((check) => {
            const Icon = CHECK_ICONS[check.id] || Activity;
            return (
              <div
                key={check.id}
                className={`rounded-lg border p-4 ${getColorClass(check.color)}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      check.color === "green" ? "bg-green-500/30" :
                      check.color === "yellow" ? "bg-yellow-500/30" : "bg-red-500/30"
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{check.id}️⃣ {check.name}</p>
                      <p className="text-xs text-gray-500">{check.subtitle}</p>
                    </div>
                  </div>
                  {getStatusIcon(check.status)}
                </div>
                
                <div className={`text-sm font-bold mb-2 ${
                  check.color === "green" ? "text-green-400" :
                  check.color === "yellow" ? "text-yellow-400" : "text-red-400"
                }`}>
                  [{check.color === "green" ? "🟢" : check.color === "yellow" ? "🟡" : "🔴"}] {check.label}
                </div>

                {/* Details */}
                <div className="text-xs text-gray-400 space-y-1 mb-2">
                  {Object.entries(check.details).slice(0, 3).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                      <span className="text-gray-300">
                        {typeof value === "object" ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>

                <p className="text-xs text-gray-300 italic">📝 {check.comment}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Summary */}
      {data && (
        <div className="p-4 bg-gray-800/50 border-t border-gray-800">
          <div className={`rounded-lg p-4 border ${
            data.summary.decision === "BUY" ? "bg-green-900/20 border-green-600" :
            data.summary.decision === "SELL" ? "bg-red-900/20 border-red-600" :
            "bg-yellow-900/20 border-yellow-600"
          }`}>
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5" />
              <span className="font-bold text-white">{t("emel.decision")} {data.summary.decision}</span>
            </div>

            {data.summary.rejections.length > 0 && (
              <div className="mb-3">
                <p className="text-sm text-gray-400 mb-1">{t("emel.why")}</p>
                <div className="space-y-1">
                  {data.summary.rejections.map((r, i) => (
                    <p key={i} className="text-sm text-red-400">{r}</p>
                  ))}
                </div>
              </div>
            )}

            {data.summary.entry_conditions.length > 0 && (
              <div>
                <p className="text-sm text-gray-400 mb-1">{t("emel.whenToTrade")}</p>
                <div className="space-y-1">
                  {data.summary.entry_conditions.map((c, i) => (
                    <p key={i} className="text-sm text-blue-400">→ {c}</p>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-xs text-gray-500">
                💡 {t("emel.alternative")}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
