"use client";

import { useState, useEffect } from "react";
import { getApiBase } from "../../lib/api/base";
import { useI18nStore } from "../../lib/i18n/store";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  TrendingUpIcon as TrendingUp,
  ArrowDownIcon as TrendingDown,
  MinusIcon as Minus,
  TargetIcon as Target,
  ArrowUpIcon as ArrowUp,
  ArrowDownIcon as ArrowDown,
  InfoIcon as Info,
  CloseIcon as X,
} from "../ui/CustomIcons";
import { LineChart } from "lucide-react";
import PanelHeader from "../PanelHeader";
import TrendChannelChart from "./TrendChannelChart";
const API_BASE = getApiBase();
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  textSec: "var(--text-secondary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  blue: "var(--blue)",
};

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
  chart_data?: {
    closes: number[];
    dates?: string[];
    trend_channel: {
      upper: number[];
      lower: number[];
      middle: number[];
    };
  };
  explanations: Record<string, string>;
}

interface ClearTrendPanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ", icon: "📊" },
  { key: "XAUUSD", label: "XAUUSD", icon: "🥇" },
  { key: "GDAXI.INDX", label: "DAX", icon: "🇩🇪" },
  { key: "USOIL.FOREX", label: "US Oil", icon: "🛢️" },
];

export default function ClearTrendPanelV3({ symbol: initialSymbol = "NDX.INDX" }: ClearTrendPanelProps) {
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
      <div className="bg-transparent p-2 animate-pulse">
        <div className="h-8 bg-gray-800 rounded w-1/3 mb-6" />
        <div className="h-40 bg-gray-800 rounded-lg mb-4" />
        <div className="h-32 bg-gray-800 rounded-lg" />
      </div>
    );
  }

  const getTrendColor = () => {
    if (!data) return P.muted;
    if (data.trend.direction === "UP") return P.green;
    if (data.trend.direction === "DOWN") return P.red;
    return P.warn;
  };

  const getTrendBg = () => {
    if (!data) return "rgba(255,255,255,0.02)";
    if (data.trend.direction === "UP") return `${P.green}06`;
    if (data.trend.direction === "DOWN") return `${P.red}06`;
    return `${P.warn}06`;
  };

  const getTrendBorder = () => {
    if (!data) return P.border;
    if (data.trend.direction === "UP") return `${P.green}20`;
    if (data.trend.direction === "DOWN") return `${P.red}20`;
    return `${P.warn}20`;
  };

  return (
    <div className="bg-transparent overflow-hidden">
      <PanelHeader
        title="CLEAR TREND V3"
        subtitle="ADVANCED TREND ANALYSIS"
        icon={<LineChart size={24} strokeWidth={2.5} />}
        iconColor="var(--accent-cyan)"
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        symbols={[
          { key: "NDX.INDX", label: "NASDAQ" },
          { key: "XAUUSD", label: "XAUUSD" },
          { key: "GDAXI.INDX", label: "DAX" },
          { key: "USOIL.FOREX", label: "US Oil" },
        ]}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        onRefresh={fetchData}
        loading={loading}
        panelId="clear-trend-v3"
      />

      {data && (
        <>
          {/* Main Price Display */}
          <div className="rounded-xl p-4 text-center" style={{ background: getTrendBg(), border: `1px solid ${getTrendBorder()}` }}>
            <div className="flex items-center justify-center gap-3 mb-2">
              {data.trend.direction === "UP" ? (
                <TrendingUp className="w-8 h-8" style={{ color: P.green }} />
              ) : data.trend.direction === "DOWN" ? (
                <TrendingDown className="w-8 h-8" style={{ color: P.red }} />
              ) : (
                <Minus className="w-8 h-8" style={{ color: P.warn }} />
              )}
              <span style={{ fontFamily: FONT, fontSize: 36, fontWeight: 700, letterSpacing: "-0.5px", color: getTrendColor() }}>
                {data.price.display}
              </span>
            </div>
            <p style={{ fontFamily: FONT, fontSize: 14, color: getTrendColor(), marginBottom: 8 }}>
              {data.trend.description}
            </p>
            <div className="flex items-center justify-center gap-2">
              <div className="flex items-center gap-1">
                <span style={{ fontFamily: FONT, fontSize: 12, color: P.muted }}>Güç:</span>
                <div className="rounded-full overflow-hidden" style={{ width: 80, height: 6, background: P.border }}>
                  <div
                    style={{
                      width: `${data.trend.strength_percent}%`, height: "100%", borderRadius: 999,
                      background: data.trend.direction === "UP" ? P.green : data.trend.direction === "DOWN" ? P.red : P.warn,
                      opacity: 0.85,
                    }}
                  />
                </div>
                <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.text }}>{data.trend.strength_percent}%</span>
              </div>
            </div>
          </div>

          {/* CHART AREA - Added for visual clarity */}
          {data.chart_data && data.chart_data.closes.length > 5 && (
            <div className="bg-transparent p-2">
              <TrendChannelChart
                closes={data.chart_data.closes}
                dates={data.chart_data.dates || []}
                upper={data.chart_data.trend_channel.upper}
                lower={data.chart_data.trend_channel.lower}
                middle={data.chart_data.trend_channel.middle}
                supportLevels={data.levels.all_levels
                  .filter(l => l.type === 'support')
                  .map(l => ({ price: l.price, label: l.name.split(' ')[0], strength: l.strength }))}
                resistanceLevels={data.levels.all_levels
                  .filter(l => l.type === 'resistance')
                  .map(l => ({ price: l.price, label: l.name.split(' ')[0], strength: l.strength }))}
                currentPrice={data.price.current}
                decimals={data.price.decimals}
                supportProximity={!!data.levels.nearest_support && parseFloat(data.levels.nearest_support.distance_display) < 20}
                resistanceProximity={!!data.levels.nearest_resistance && parseFloat(data.levels.nearest_resistance.distance_display) < 20}
                supportIntensity={data.trend.direction === 'DOWN' ? 1 : 0.5}
                resistanceIntensity={data.trend.direction === 'UP' ? 1 : 0.5}
              />
            </div>
          )}

          {/* Support/Resistance Levels */}
          <div className="p-2">
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
                    className="relative flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all hover:opacity-90"
                    style={{
                      background: isCurrent ? `${P.accent}15` : isResistance ? `${P.red}10` : `${P.green}10`,
                      border: `1px solid ${isCurrent ? `${P.accent}30` : isResistance ? `${P.red}25` : `${P.green}25`}`,
                    }}
                  >
                    {/* Level Indicator */}
                    <div className="flex items-center justify-center text-xs font-bold rounded" style={{
                      width: 48, height: 32,
                      background: isCurrent ? `${P.accent}25` : isResistance ? `${P.red}25` : `${P.green}25`,
                      color: isCurrent ? P.accent : isResistance ? P.red : P.green,
                    }}>
                      {isCurrent ? "NOW" : level.name.split(" ")[0]}
                    </div>

                    {/* Price */}
                    <div className="flex-1">
                      <div style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: isCurrent ? P.text : isResistance ? P.red : P.green }}>
                        {level.price.toFixed(data.price.decimals)}
                      </div>
                      {level.name && !isCurrent && (
                        <div className="text-xs text-gray-500">
                          {level.name}
                        </div>
                      )}
                    </div>

                    {/* Distance */}
                    <div className={`text-right ${isCurrent ? "text-blue-300" : isResistance ? "text-red-300" : "text-green-300"
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
                  className="rounded-lg p-3 cursor-pointer"
                  style={{ background: `${P.red}08`, border: `1px solid ${P.red}20` }}
                >
                  <div style={{ fontFamily: FONT, fontSize: 11, color: P.red, marginBottom: 4 }}>↑ Nearest Resistance</div>
                  <div style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: P.red }}>
                    {data.levels.nearest_resistance.price.toFixed(data.price.decimals)}
                  </div>
                  <div style={{ fontFamily: FONT, fontSize: 11, color: P.red, opacity: 0.75 }}>
                    {data.levels.nearest_resistance.distance_display} above
                  </div>
                </div>
              )}
              {data.levels.nearest_support && (
                <div
                  onClick={() => openExplanation("support", "Nearest Support")}
                  className="rounded-lg p-3 cursor-pointer"
                  style={{ background: `${P.green}08`, border: `1px solid ${P.green}20` }}
                >
                  <div style={{ fontFamily: FONT, fontSize: 11, color: P.green, marginBottom: 4 }}>↓ Nearest Support</div>
                  <div style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: P.green }}>
                    {data.levels.nearest_support.price.toFixed(data.price.decimals)}
                  </div>
                  <div style={{ fontFamily: FONT, fontSize: 11, color: P.green, opacity: 0.75 }}>
                    {data.levels.nearest_support.distance_display} below
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Trade Suggestion */}
          <div className="p-2 bg-transparent">
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

            <div className="rounded-xl p-4" style={{
              background: data.trend.direction === "UP" ? `${P.green}08` : data.trend.direction === "DOWN" ? `${P.red}08` : `${P.warn}08`,
              border: `1px solid ${data.trend.direction === "UP" ? `${P.green}20` : data.trend.direction === "DOWN" ? `${P.red}20` : `${P.warn}20`}`,
            }}>
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
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setExplanationModal(null)}>
          <div
            className="rounded-xl max-w-md w-full p-6"
            style={{ background: P.surface, border: `1px solid ${P.border}`, boxShadow: '0 20px 60px rgba(0,0,0,0.5)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: P.text }}>{explanationModal.title}</h3>
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
