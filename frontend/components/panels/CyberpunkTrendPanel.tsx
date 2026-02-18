"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  Zap,
  Shield,
  Crosshair,
  Activity,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { useI18nStore } from "../../lib/i18n/store";
import { useProximityAnimation } from "../../hooks/useProximityAnimation";
import { PanelInfoButton } from "../PanelInfoButton";
import TrendChannelChart from "./TrendChannelChart";
import { useFullscreen } from "../../hooks/useFullscreen";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

/* ──────────────────── Types ──────────────────── */

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
  price: { current: number; display: string; decimals: number };
  trend: {
    direction: "UP" | "DOWN" | "NEUTRAL";
    strength: number;
    strength_percent: number;
    description: string;
    ema_20: number;
    ema_50: number;
    ema_200?: number;
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
    entry_zone?: { min: number; max: number; description: string };
    target?: number;
    stop?: number;
  };
  pip_value: number;
  chart_data?: {
    closes: number[];
    dates: string[];
    trend_channel: { upper: number[]; lower: number[]; middle: number[] };
  };
  explanations: Record<string, string>;
}

/* ──────────────────── Constants ──────────────────── */

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ", icon: "📊" },
  { key: "XAUUSD", label: "XAUUSD", icon: "🥇" },
  { key: "GDAXI.INDX", label: "DAX", icon: "🇩🇪" },
  { key: "CL.COMM", label: "US Oil", icon: "🛢️" },
];

/* ──────────────────── Sub-Components ──────────────────── */

function HorizontalStrengthBar({ percent, direction }: { percent: number; direction: string }) {
  const clamped = Math.min(100, Math.max(0, percent));
  const color = direction === "UP" ? "#00ff88" : direction === "DOWN" ? "#ff3366" : "#fbbf24";
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] uppercase tracking-widest text-white/30 font-mono">Trend Power</span>
        <span className="text-xs font-bold font-mono" style={{ color, textShadow: `0 0 6px ${color}60` }}>
          {clamped}%
        </span>
      </div>
      <div className="relative w-full h-2 rounded-full overflow-hidden bg-white/5 border border-white/10">
        <motion.div
          className="absolute top-0 left-0 h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${clamped}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          style={{
            background: `linear-gradient(90deg, ${color}40, ${color})`,
            boxShadow: `0 0 10px ${color}80`,
          }}
        />
      </div>
    </div>
  );
}

function EmaPill({ label, value, currentPrice, color, isProximate, decimals }: {
  label: string; value: number; currentPrice: number; color: string; isProximate: boolean; decimals: number;
}) {
  const isAbove = currentPrice > value;
  return (
    <motion.div
      className="flex items-center gap-1.5 px-2 py-1 rounded-full border font-mono text-[11px]"
      style={{
        borderColor: `${color}${isProximate ? "80" : "30"}`,
        backgroundColor: `${color}${isProximate ? "18" : "08"}`,
        boxShadow: isProximate ? `0 0 12px ${color}40` : "none",
      }}
      animate={isProximate ? { scale: [1, 1.03, 1] } : {}}
      transition={isProximate ? { duration: 1.5, repeat: Infinity } : {}}
    >
      <span style={{ color }} className="font-bold text-[9px]">{label}</span>
      <span className="text-white/70">{value.toFixed(decimals)}</span>
      {isAbove ? <ArrowUp className="w-2.5 h-2.5" style={{ color: "#00ff88" }} /> : <ArrowDown className="w-2.5 h-2.5" style={{ color: "#ff3366" }} />}
    </motion.div>
  );
}

function CompactLevelRow({ level, decimals }: { level: LevelData; decimals: number }) {
  const isCurrent = level.type === "current";
  const isRes = level.type === "resistance";
  const color = isCurrent ? "#00ff88" : isRes ? "#ff3366" : "#00ccff";

  return (
    <div
      className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg transition-all"
      style={{
        backgroundColor: `${color}08`,
        border: `1px solid ${color}20`,
      }}
    >
      <div
        className="w-10 h-6 rounded flex items-center justify-center text-[10px] font-bold font-mono shrink-0"
        style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}30` }}
      >
        {isCurrent ? "NOW" : level.name.split(" ")[0]}
      </div>
      <span className="font-mono text-sm font-bold flex-1" style={{ color, textShadow: isCurrent ? `0 0 8px ${color}50` : "none" }}>
        {level.price.toFixed(decimals)}
      </span>
      <span className="text-[11px] font-mono" style={{ color: `${color}99` }}>
        {level.distance_display}
      </span>
      {level.is_next && <Zap className="w-3 h-3 shrink-0" style={{ color }} />}
    </div>
  );
}

/* ──────────────────── Main Panel ──────────────────── */

export default function CyberpunkTrendPanel({ symbol: initialSymbol = "NDX.INDX" }: { symbol?: string }) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<ClearTrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");
  const [explanationModal, setExplanationModal] = useState<{ title: string; content: string } | null>(null);
  const [priceFlash, setPriceFlash] = useState(false);
  const { isFullscreen, toggleFullscreen } = useFullscreen();

  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "clear_trend");

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [activeSymbol, timeframe]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/clear-trend/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) {
        if (data && json.price?.current !== data.price?.current) {
          setPriceFlash(true);
          setTimeout(() => setPriceFlash(false), 600);
        }
        setData(json);
      }
    } catch (e) {
      console.error("Clear trend fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, [activeSymbol, timeframe, data]);

  useEffect(() => {
    if (wsData) {
      if (data && wsData.price?.current !== data.price?.current) {
        setPriceFlash(true);
        setTimeout(() => setPriceFlash(false), 600);
      }
      setData(wsData);
      setLoading(false);
    }
  }, [wsData]);

  useEffect(() => {
    if (!wsData) fetchData();
    if (!wsConnected) {
      const interval = setInterval(fetchData, 15000);
      return () => clearInterval(interval);
    }
  }, [activeSymbol, timeframe, wsConnected]);

  // Listen for global refresh event from header button
  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("pulse-refresh", handler);
    return () => window.removeEventListener("pulse-refresh", handler);
  }, [activeSymbol, timeframe]);

  const openExplanation = (key: string, title: string) => {
    if (data?.explanations?.[key]) setExplanationModal({ title, content: data.explanations[key] });
  };

  const proximity = useProximityAnimation(
    data?.price?.current ?? 0,
    data?.levels?.nearest_support?.price ?? null,
    data?.levels?.nearest_resistance?.price ?? null,
    data?.trend?.ema_20 ?? null
  );

  /* ── Loading skeleton ── */
  if (loading && !data) {
    return (
      <div className="rounded-3xl p-6 animate-pulse" style={{ background: "rgba(15,23,42,0.4)", backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,0.08)" }}>
        <div className="h-8 bg-white/5 rounded-xl w-1/3 mb-6" />
        <div className="flex gap-6">
          <div className="flex-[2] h-80 bg-white/5 rounded-2xl" />
          <div className="flex-1 h-80 bg-white/5 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  const trendColor = data.trend.direction === "UP" ? "#00ff88" : data.trend.direction === "DOWN" ? "#ff3366" : "#fbbf24";
  const trendLabel = data.trend.direction === "UP" ? "BULLISH" : data.trend.direction === "DOWN" ? "BEARISH" : "NEUTRAL";

  const chartCloses = data.chart_data?.closes ?? [];
  const chartDates = data.chart_data?.dates ?? [];
  const chartUpper = data.chart_data?.trend_channel?.upper ?? [];
  const chartLower = data.chart_data?.trend_channel?.lower ?? [];
  const chartMiddle = data.chart_data?.trend_channel?.middle ?? [];

  const supportLevelsForChart = (data.levels.all_levels || [])
    .filter((l) => l.type === "support")
    .map((l) => ({ price: l.price, label: l.name.split(" ")[0], strength: l.strength }));
  const resistanceLevelsForChart = (data.levels.all_levels || [])
    .filter((l) => l.type === "resistance")
    .map((l) => ({ price: l.price, label: l.name.split(" ")[0], strength: l.strength }));

  const resistanceLevels = (data.levels.all_levels || []).filter((l) => l.type === "resistance");
  const supportLevels = (data.levels.all_levels || []).filter((l) => l.type === "support");
  const currentLevel = (data.levels.all_levels || []).find((l) => l.type === "current");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`relative rounded-3xl overflow-hidden ${isFullscreen ? 'fixed inset-0 z-[9999] !rounded-none flex flex-col' : ''}`}
      style={{
        background: "rgba(10,15,30,0.5)",
        backdropFilter: "blur(24px)",
        border: isFullscreen ? "none" : "1px solid rgba(255,255,255,0.06)",
        boxShadow: `0 0 60px rgba(0,255,136,0.04), 0 4px 80px rgba(0,0,0,0.5)`,
      }}
    >
      {/* Ambient proximity glow */}
      {proximity.resistanceProximity && (
        <div className="absolute inset-0 pointer-events-none rounded-3xl" style={{ boxShadow: `inset 0 0 80px rgba(255,51,102,${proximity.resistanceIntensity * 0.06})` }} />
      )}
      {proximity.supportProximity && (
        <div className="absolute inset-0 pointer-events-none rounded-3xl" style={{ boxShadow: `inset 0 0 80px rgba(0,204,255,${proximity.supportIntensity * 0.06})` }} />
      )}

      {/* ═══ HEADER BAR ═══ */}
      <div className="flex items-center justify-between px-5 py-3 border-b" style={{ borderColor: "rgba(255,255,255,0.05)", background: "rgba(0,0,0,0.25)" }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.15))", border: "1px solid rgba(0,255,136,0.2)" }}>
            <Activity className="w-4 h-4" style={{ color: "#00ff88" }} />
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-wide font-mono" style={{ color: "#00ff88", textShadow: "0 0 10px rgba(0,255,136,0.3)" }}>
              CLEAR TREND <span className="text-xs text-white bg-red-600 px-1 rounded ml-2">v2.2</span>
              <span className="text-[9px] ml-2 text-gray-500">C:{chartCloses.length} D:{chartDates.length}</span>
            </h2>
            <p className="text-[9px] uppercase tracking-[0.25em] text-white/25">Neon Trend Analysis</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Symbol Switcher */}
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setActiveSymbol(s.key)}
                className="px-3 py-1.5 text-[10px] font-bold font-mono transition-all flex items-center gap-1"
                style={{
                  backgroundColor: activeSymbol === s.key ? "rgba(0,255,136,0.15)" : "rgba(255,255,255,0.03)",
                  color: activeSymbol === s.key ? "#00ff88" : "rgba(255,255,255,0.35)",
                  borderRight: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <span>{s.icon}</span>{s.label}
              </button>
            ))}
          </div>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
            className="text-[10px] font-mono font-bold px-2 py-1.5 rounded-lg appearance-none cursor-pointer"
            style={{ backgroundColor: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.1)" }}
          >
            <option value="15m">15m</option>
            <option value="1H">1H</option>
            <option value="4H">4H</option>
            <option value="1D">1D</option>
          </select>
          <button onClick={fetchData} className="p-1.5 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: "rgba(255,255,255,0.35)" }} />
          </button>
          <button onClick={toggleFullscreen} className="p-1.5 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }} title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" style={{ color: "rgba(255,255,255,0.35)" }} /> : <Maximize2 className="w-3.5 h-3.5" style={{ color: "rgba(255,255,255,0.35)" }} />}
          </button>
          <PanelInfoButton panelId="clear-trend" />
        </div>
      </div>

      {/* ═══ MAIN CONTENT: Chart (left) + Sidebar (right) ═══ */}
      <div className="flex flex-col lg:flex-row">

        {/* ── LEFT: CHART HERO ── */}
        <div className="flex-[2] min-w-0 p-4 flex flex-col gap-3">
          {/* Price bar above chart */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {data.trend.direction === "UP" ? (
                <TrendingUp className="w-6 h-6" style={{ color: trendColor, filter: `drop-shadow(0 0 6px ${trendColor}60)` }} />
              ) : data.trend.direction === "DOWN" ? (
                <TrendingDown className="w-6 h-6" style={{ color: trendColor, filter: `drop-shadow(0 0 6px ${trendColor}60)` }} />
              ) : (
                <Minus className="w-6 h-6" style={{ color: trendColor }} />
              )}
              <motion.span
                className="text-3xl font-bold font-mono relative"
                style={{ color: trendColor, textShadow: `0 0 20px ${trendColor}80, 0 0 40px ${trendColor}30` }}
                animate={priceFlash ? { scale: [1, 1.05, 1] } : {}}
                transition={{ duration: 0.3 }}
              >
                {data.price.display}
                <motion.span
                  className="absolute -top-1 -right-2.5 w-2 h-2 rounded-full"
                  style={{ backgroundColor: trendColor }}
                  animate={{ opacity: [1, 0.3, 1], scale: [1, 1.3, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              </motion.span>
              <span className="text-[11px] font-mono font-bold uppercase tracking-widest px-2 py-0.5 rounded"
                style={{ color: trendColor, backgroundColor: `${trendColor}15`, border: `1px solid ${trendColor}30` }}
              >
                {trendLabel}
              </span>
            </div>

            {/* EMA Pills */}
            <div className="hidden md:flex items-center gap-1.5">
              <EmaPill label="EMA20" value={data.trend.ema_20} currentPrice={data.price.current} color="#ec4899" isProximate={proximity.ema20Proximity} decimals={data.price.decimals} />
              <EmaPill label="EMA50" value={data.trend.ema_50} currentPrice={data.price.current} color="#f97316" isProximate={false} decimals={data.price.decimals} />
              {data.trend.ema_200 != null && data.trend.ema_200 > 0 && (
                <EmaPill label="EMA200" value={data.trend.ema_200} currentPrice={data.price.current} color="#e2e8f0" isProximate={false} decimals={data.price.decimals} />
              )}
            </div>
          </div>

          {/* Strength bar */}
          <HorizontalStrengthBar percent={data.trend.strength_percent} direction={data.trend.direction} />

          {/* CHART */}
          {chartCloses.length > 5 ? (
            <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.04)" }}>
              <TrendChannelChart
                closes={chartCloses}
                dates={chartDates}
                upper={chartUpper}
                lower={chartLower}
                middle={chartMiddle}
                supportLevels={supportLevelsForChart}
                resistanceLevels={resistanceLevelsForChart}
                currentPrice={data.price.current}
                decimals={data.price.decimals}
                supportProximity={proximity.supportProximity}
                resistanceProximity={proximity.resistanceProximity}
                supportIntensity={proximity.supportIntensity}
                resistanceIntensity={proximity.resistanceIntensity}
              />
            </div>
          ) : (
            <div className="h-64 rounded-2xl flex items-center justify-center" style={{ background: "rgba(2,6,23,0.5)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <p className="text-white/20 text-sm font-mono">Loading chart data...</p>
            </div>
          )}

          {/* Mobile-only EMA pills */}
          <div className="flex md:hidden flex-wrap gap-1.5">
            <EmaPill label="EMA20" value={data.trend.ema_20} currentPrice={data.price.current} color="#ec4899" isProximate={proximity.ema20Proximity} decimals={data.price.decimals} />
            <EmaPill label="EMA50" value={data.trend.ema_50} currentPrice={data.price.current} color="#f97316" isProximate={false} decimals={data.price.decimals} />
            {data.trend.ema_200 != null && data.trend.ema_200 > 0 && (
              <EmaPill label="EMA200" value={data.trend.ema_200} currentPrice={data.price.current} color="#e2e8f0" isProximate={false} decimals={data.price.decimals} />
            )}
          </div>
        </div>

        {/* ── RIGHT: DATA SIDEBAR ── */}
        <div className="flex-1 min-w-[280px] max-w-[360px] border-l flex flex-col" style={{ borderColor: "rgba(255,255,255,0.05)", background: "rgba(0,0,0,0.15)" }}>

          {/* S/R Section Header */}
          <div className="flex items-center justify-between px-4 pt-4 pb-2">
            <h3 className="text-[10px] uppercase tracking-[0.2em] font-mono flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.35)" }}>
              <Shield className="w-3.5 h-3.5" style={{ color: "#00ccff" }} />
              Support & Resistance
            </h3>
            <button onClick={() => openExplanation("support", "Support & Resistance")} className="text-white/20 hover:text-white/40 transition-colors">
              <Info className="w-3 h-3" />
            </button>
          </div>

          {/* Resistance levels */}
          <div className="px-3 space-y-1">
            {resistanceLevels.map((level, i) => (
              <CompactLevelRow key={`r-${i}`} level={level} decimals={data.price.decimals} />
            ))}
          </div>

          {/* Current Price */}
          {currentLevel && (
            <div className="px-3 py-1.5">
              <motion.div
                className="flex items-center gap-2 px-3 py-2 rounded-lg relative overflow-hidden"
                style={{ backgroundColor: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.25)", boxShadow: "0 0 20px rgba(0,255,136,0.08)" }}
              >
                <motion.div className="absolute left-0 top-0 bottom-0 w-1 rounded-r" style={{ backgroundColor: "#00ff88" }}
                  animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }}
                />
                <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded" style={{ color: "#00ff88", backgroundColor: "rgba(0,255,136,0.15)" }}>NOW</span>
                <span className="font-mono text-sm font-bold flex-1" style={{ color: "#00ff88", textShadow: "0 0 10px rgba(0,255,136,0.4)" }}>
                  {currentLevel.price.toFixed(data.price.decimals)}
                </span>
                <span className="text-[10px] font-mono" style={{ color: "#00ff8880" }}>HERE</span>
              </motion.div>
            </div>
          )}

          {/* Support levels */}
          <div className="px-3 space-y-1 pb-3">
            {supportLevels.map((level, i) => (
              <CompactLevelRow key={`s-${i}`} level={level} decimals={data.price.decimals} />
            ))}
          </div>

          {/* Divider */}
          <div className="mx-4 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }} />

          {/* Nearest Levels Summary */}
          <div className="px-4 py-3 grid grid-cols-2 gap-2">
            {data.levels.nearest_resistance && (
              <div className="rounded-lg p-2.5" style={{ backgroundColor: "rgba(255,51,102,0.06)", border: "1px solid rgba(255,51,102,0.15)" }}>
                <div className="text-[8px] font-mono uppercase tracking-wider mb-1" style={{ color: "#ff336680" }}>Nearest Resistance</div>
                <div className="text-sm font-bold font-mono" style={{ color: "#ff3366" }}>{data.levels.nearest_resistance.price.toFixed(data.price.decimals)}</div>
                <div className="text-[9px] font-mono" style={{ color: "#ff336660" }}>{data.levels.nearest_resistance.distance_display}</div>
              </div>
            )}
            {data.levels.nearest_support && (
              <div className="rounded-lg p-2.5" style={{ backgroundColor: "rgba(0,204,255,0.06)", border: "1px solid rgba(0,204,255,0.15)" }}>
                <div className="text-[8px] font-mono uppercase tracking-wider mb-1" style={{ color: "#00ccff80" }}>Nearest Support</div>
                <div className="text-sm font-bold font-mono" style={{ color: "#00ccff" }}>{data.levels.nearest_support.price.toFixed(data.price.decimals)}</div>
                <div className="text-[9px] font-mono" style={{ color: "#00ccff60" }}>{data.levels.nearest_support.distance_display}</div>
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="mx-4 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }} />

          {/* Trading Suggestion */}
          <div className="px-4 py-3 flex-1">
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3.5 h-3.5" style={{ color: trendColor }} />
              <span className="text-[10px] uppercase tracking-[0.2em] font-mono" style={{ color: "rgba(255,255,255,0.35)" }}>Trade Setup</span>
            </div>
            <p className="text-[11px] text-white/50 mb-3 font-mono leading-relaxed">{data.trade_zones.suggestion}</p>

            {data.trade_zones.target != null && data.trade_zones.stop != null && (
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center rounded-lg py-2" style={{ backgroundColor: "rgba(0,255,136,0.06)", border: "1px solid rgba(0,255,136,0.15)" }}>
                  <div className="text-[8px] text-white/25 font-mono uppercase tracking-wider mb-0.5">
                    <Crosshair className="w-2.5 h-2.5 inline mr-0.5" style={{ color: "#00ff88" }} />Target
                  </div>
                  <div className="text-base font-bold font-mono" style={{ color: "#00ff88", textShadow: "0 0 6px rgba(0,255,136,0.3)" }}>
                    {data.trade_zones.target.toFixed(data.price.decimals)}
                  </div>
                </div>
                <div className="text-center rounded-lg py-2" style={{ backgroundColor: "rgba(255,51,102,0.06)", border: "1px solid rgba(255,51,102,0.15)" }}>
                  <div className="text-[8px] text-white/25 font-mono uppercase tracking-wider mb-0.5">
                    <Shield className="w-2.5 h-2.5 inline mr-0.5" style={{ color: "#ff3366" }} />Stop
                  </div>
                  <div className="text-base font-bold font-mono" style={{ color: "#ff3366", textShadow: "0 0 6px rgba(255,51,102,0.3)" }}>
                    {data.trade_zones.stop.toFixed(data.price.decimals)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ═══ EXPLANATION MODAL ═══ */}
      <AnimatePresence>
        {explanationModal && (
          <motion.div
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
            style={{ backgroundColor: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setExplanationModal(null)}
          >
            <motion.div
              className="max-w-md w-full p-6 rounded-2xl"
              style={{ background: "rgba(15,23,42,0.95)", border: "1px solid rgba(0,255,136,0.15)", boxShadow: "0 0 40px rgba(0,255,136,0.1)" }}
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold font-mono" style={{ color: "#00ff88" }}>{explanationModal.title}</h3>
                <button onClick={() => setExplanationModal(null)} className="text-white/40 hover:text-white"><X className="w-5 h-5" /></button>
              </div>
              <p className="text-sm text-white/60 leading-relaxed">{explanationModal.content}</p>
              <button onClick={() => setExplanationModal(null)} className="mt-5 w-full py-2 rounded-xl text-sm font-bold font-mono"
                style={{ background: "rgba(0,255,136,0.1)", border: "1px solid rgba(0,255,136,0.25)", color: "#00ff88" }}>
                Got it
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
