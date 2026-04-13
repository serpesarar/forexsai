"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getApiBase } from "../../lib/api/base";
import { useWSPanelData, useWSSymbolData } from "../../contexts/WebSocketContext";
import {
  LoadingIcon,
  PulseIcon,
  SignalsIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  NeutralIcon,
  TargetIcon,
  InfoIcon,
  CloseIcon,
  ZapIcon,
  SecurityShieldIcon,
  ExpandIcon,
  ShrinkIcon,
  NasdaqIcon,
  GoldIcon,
  DaxIcon,
  OilIcon,
} from "../ui/CustomIcons";
import { useI18nStore } from "../../lib/i18n/store";
import { useProximityAnimation } from "../../hooks/useProximityAnimation";
import { PanelHeader } from "../PanelHeader";
import TrendChannelChart from "./TrendChannelChart";
import { useFullscreen } from "../../hooks/useFullscreen";
import { Cpu } from "lucide-react";

const API_BASE = getApiBase();

// ── Theme-aware Color Palette (CSS Variables) ───────────────────────────────
const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  cyan: "var(--accent-cyan)",
  purple: "var(--accent-purple)",
  pink: "var(--accent-pink)",
  orange: "var(--accent-orange)",
};

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
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US Oil" },
];

const TIMEFRAMES = ["15m", "1H", "4H", "1D"];

/* ──────────────────── Sub-Components ──────────────────── */

function HorizontalStrengthBar({ percent, direction }: { percent: number; direction: string }) {
  const clamped = Math.min(100, Math.max(0, percent));
  const color = direction === "UP" ? P.green : direction === "DOWN" ? P.red : P.warn;
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
      {isAbove ? <ArrowUpIcon size={10} style={{ color: P.green }} /> : <ArrowDownIcon size={10} style={{ color: P.red }} />}
    </motion.div>
  );
}

function CompactLevelRow({ level, decimals }: { level: LevelData; decimals: number }) {
  const isCurrent = level.type === "current";
  const isRes = level.type === "resistance";
  const color = isCurrent ? P.green : isRes ? P.red : P.accent;

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
      {level.is_next && <ZapIcon size={12} style={{ color }} />}
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
  const panelRef = useRef<HTMLDivElement | null>(null);
  const prevPriceRef = useRef<number | null>(null);

  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "clear_trend");
  const wsSymbol = useWSSymbolData(activeSymbol);
  const livePrice = wsSymbol?.data?.current_price ?? null;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/clear-trend/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) {
        const newPrice = json.price?.current;
        if (prevPriceRef.current !== null && newPrice !== prevPriceRef.current) {
          setPriceFlash(true);
          setTimeout(() => setPriceFlash(false), 600);
        }
        prevPriceRef.current = newPrice ?? null;
        setData(json);
      }
    } catch (e) {
      console.error("Clear trend fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, [activeSymbol, timeframe]);

  // Always re-fetch when symbol or timeframe changes (WS broadcasts default TF only)
  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSymbol, timeframe]);

  // WS data update
  useEffect(() => {
    if (wsData) {
      const newPrice = wsData.price?.current;
      if (prevPriceRef.current !== null && newPrice !== prevPriceRef.current) {
        setPriceFlash(true);
        setTimeout(() => setPriceFlash(false), 600);
      }
      prevPriceRef.current = newPrice ?? null;
      setData(wsData);
      setLoading(false);
    }
  }, [wsData]);

  // Polling fallback when WS disconnected
  useEffect(() => {
    if (!wsConnected) {
      const interval = setInterval(fetchData, 15000);
      return () => clearInterval(interval);
    }
  }, [wsConnected, fetchData]);

  // Dashboard / pulse refresh events
  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    window.addEventListener("pulse-refresh", handler);
    return () => {
      window.removeEventListener("dashboard-refresh", handler);
      window.removeEventListener("pulse-refresh", handler);
    };
  }, [fetchData]);

  const openExplanation = (key: string, title: string) => {
    if (data?.explanations?.[key]) setExplanationModal({ title, content: data.explanations[key] });
  };

  // Live price overlay: recalculate S/R distances on every tick without re-fetching
  const liveData = useMemo<ClearTrendData | null>(() => {
    if (!data) return null;
    if (!livePrice || livePrice <= 0) return data;
    if (Math.abs(livePrice - data.price.current) < (data.pip_value || 1) * 0.01) return data;

    const pipVal = data.pip_value || 1;
    const decimals = data.price.decimals ?? 2;
    const unit = "pts";

    const updatedLevels = data.levels.all_levels.map((level: any) => {
      if (level.type === "current") {
        return { ...level, price: Math.round(livePrice * Math.pow(10, decimals)) / Math.pow(10, decimals) };
      }
      const dist = Math.abs(level.price - livePrice) / pipVal;
      const prefix = level.type === "resistance" ? "+" : "-";
      return {
        ...level,
        distance: Math.round(dist * 10) / 10,
        distance_display: `${prefix}${(Math.round(dist * 10) / 10)} ${unit}`,
      };
    });

    const resistances = updatedLevels.filter((l: any) => l.type === "resistance");
    const supports = updatedLevels.filter((l: any) => l.type === "support");
    const nearestRes = resistances.length ? resistances.reduce((a: any, b: any) => (a.distance < b.distance ? a : b)) : null;
    const nearestSup = supports.length ? supports.reduce((a: any, b: any) => (a.distance < b.distance ? a : b)) : null;

    return {
      ...data,
      price: { ...data.price, current: livePrice, display: livePrice.toFixed(decimals) },
      levels: { ...data.levels, all_levels: updatedLevels, nearest_resistance: nearestRes, nearest_support: nearestSup },
    };
  }, [data, livePrice]);

  const d = liveData;

  const proximity = useProximityAnimation(
    d?.price?.current ?? 0,
    d?.levels?.nearest_support?.price ?? null,
    d?.levels?.nearest_resistance?.price ?? null,
    d?.trend?.ema_20 ?? null
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

  if (!d) return null;

  const trendColor = d.trend.direction === "UP" ? P.green : d.trend.direction === "DOWN" ? P.red : P.warn;
  const trendLabel = d.trend.direction === "UP" ? "BULLISH" : d.trend.direction === "DOWN" ? "BEARISH" : "NEUTRAL";

  const chartCloses = d.chart_data?.closes ?? [];
  const chartDates = d.chart_data?.dates ?? [];
  const chartUpper = d.chart_data?.trend_channel?.upper ?? [];
  const chartLower = d.chart_data?.trend_channel?.lower ?? [];
  const chartMiddle = d.chart_data?.trend_channel?.middle ?? [];

  const supportLevelsForChart = (d.levels.all_levels || [])
    .filter((l) => l.type === "support")
    .map((l) => ({ price: l.price, label: l.name.split(" ")[0], strength: l.strength }));
  const resistanceLevelsForChart = (d.levels.all_levels || [])
    .filter((l) => l.type === "resistance")
    .map((l) => ({ price: l.price, label: l.name.split(" ")[0], strength: l.strength }));

  const resistanceLevels = (d.levels.all_levels || []).filter((l) => l.type === "resistance");
  const supportLevels = (d.levels.all_levels || []).filter((l) => l.type === "support");
  const currentLevel = (d.levels.all_levels || []).find((l) => l.type === "current");

  return (
    <motion.div
      ref={panelRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`relative rounded-none overflow-hidden ${isFullscreen ? 'fixed inset-0 z-[9999] flex flex-col bg-[#060a1f]' : ''}`}
      style={{
        background: isFullscreen ? "#060a1f" : "transparent",
        backdropFilter: isFullscreen ? "none" : "blur(24px)",
        border: "none",
        boxShadow: "none",
      }}
    >
      {/* Ambient proximity glow */}
      {proximity.resistanceProximity && (
        <div className="absolute inset-0 pointer-events-none rounded-3xl" style={{ boxShadow: `inset 0 0 80px rgba(255,51,102,${proximity.resistanceIntensity * 0.06})` }} />
      )}
      {proximity.supportProximity && (
        <div className="absolute inset-0 pointer-events-none rounded-3xl" style={{ boxShadow: `inset 0 0 80px rgba(0,204,255,${proximity.supportIntensity * 0.06})` }} />
      )}

      {/* ═══ HEADER BAR (PanelHeader) ═══ */}
      <PanelHeader
        title="CYBER TREND"
        subtitle="AI-POWERED ANALYSIS"
        icon={<Cpu size={24} strokeWidth={2.5} />}
        iconColor="var(--accent-cyan)"
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        symbols={SYMBOLS}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        onRefresh={fetchData}
        loading={loading}
        panelId="cyber-trend"
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        timeframes={TIMEFRAMES}
        onFullscreen={() => void toggleFullscreen(panelRef.current)}
        isFullscreen={isFullscreen}
      />

      {/* ═══ MAIN CONTENT: Chart (left) + Sidebar (right) ═══ */}
      <div className="flex flex-col lg:flex-row">

        {/* ── LEFT: CHART HERO ── */}
        <div className="flex-[2] min-w-0 p-4 flex flex-col gap-3">
          {/* Price bar above chart */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {d.trend.direction === "UP" ? (
                <ArrowUpIcon size={24} style={{ color: trendColor, filter: `drop-shadow(0 0 6px ${trendColor}60)` }} />
              ) : d.trend.direction === "DOWN" ? (
                <ArrowDownIcon size={24} style={{ color: trendColor, filter: `drop-shadow(0 0 6px ${trendColor}60)` }} />
              ) : (
                <NeutralIcon size={24} style={{ color: trendColor }} />
              )}
              <motion.span
                className="text-3xl font-bold font-mono relative"
                style={{ color: trendColor, textShadow: `0 0 20px ${trendColor}80, 0 0 40px ${trendColor}30` }}
                animate={priceFlash ? { scale: [1, 1.05, 1] } : {}}
                transition={{ duration: 0.3 }}
              >
                {d.price.display}
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
              <EmaPill label="EMA20" value={d.trend.ema_20} currentPrice={d.price.current} color={P.pink} isProximate={proximity.ema20Proximity} decimals={d.price.decimals} />
              <EmaPill label="EMA50" value={d.trend.ema_50} currentPrice={d.price.current} color={P.orange} isProximate={false} decimals={d.price.decimals} />
              {d.trend.ema_200 != null && d.trend.ema_200 > 0 && (
                <EmaPill label="EMA200" value={d.trend.ema_200} currentPrice={d.price.current} color={P.text} isProximate={false} decimals={d.price.decimals} />
              )}
            </div>
          </div>

          {/* Strength bar */}
          <HorizontalStrengthBar percent={d.trend.strength_percent} direction={d.trend.direction} />

          {/* CHART */}
          {chartCloses.length > 5 ? (
            <div className="overflow-hidden">
              <TrendChannelChart
                closes={chartCloses}
                dates={chartDates}
                upper={chartUpper}
                lower={chartLower}
                middle={chartMiddle}
                supportLevels={supportLevelsForChart}
                resistanceLevels={resistanceLevelsForChart}
                currentPrice={d.price.current}
                decimals={d.price.decimals}
                supportProximity={proximity.supportProximity}
                resistanceProximity={proximity.resistanceProximity}
                supportIntensity={proximity.supportIntensity}
                resistanceIntensity={proximity.resistanceIntensity}
              />
            </div>
          ) : (
            <div className="h-64 rounded-2xl flex items-center justify-center" style={{ background: P.border }}>
              <p className="text-white/20 text-sm font-mono">Loading chart data...</p>
            </div>
          )}

          {/* Mobile-only EMA pills */}
          <div className="flex md:hidden flex-wrap gap-1.5">
            <EmaPill label="EMA20" value={d.trend.ema_20} currentPrice={d.price.current} color={P.pink} isProximate={proximity.ema20Proximity} decimals={d.price.decimals} />
            <EmaPill label="EMA50" value={d.trend.ema_50} currentPrice={d.price.current} color={P.orange} isProximate={false} decimals={d.price.decimals} />
            {d.trend.ema_200 != null && d.trend.ema_200 > 0 && (
              <EmaPill label="EMA200" value={d.trend.ema_200} currentPrice={d.price.current} color={P.text} isProximate={false} decimals={d.price.decimals} />
            )}
          </div>
        </div>

        {/* ── RIGHT: DATA SIDEBAR ── */}
        <div className="flex-1 min-w-[280px] max-w-[360px] flex flex-col bg-transparent">

          {/* S/R Section Header */}
          <div className="flex items-center justify-between px-4 pt-4 pb-2">
            <h3 className="text-[10px] uppercase tracking-[0.2em] font-mono flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.35)" }}>
              <SecurityShieldIcon size={14} style={{ color: P.accent }} />
              Support & Resistance
            </h3>
            <button onClick={() => openExplanation("support", "Support & Resistance")} className="text-white/20 hover:text-white/40 transition-colors">
              <InfoIcon size={12} />
            </button>
          </div>

          {/* Resistance levels */}
          <div className="px-3 space-y-1">
            {resistanceLevels.map((level, i) => (
              <CompactLevelRow key={`r-${i}`} level={level} decimals={d.price.decimals} />
            ))}
          </div>

          {/* Current Price */}
          {currentLevel && (
            <div className="px-3 py-1.5">
              <motion.div
                className="flex items-center gap-2 px-3 py-2 rounded-lg relative overflow-hidden"
                style={{ color: P.green, backgroundColor: `${P.green}15`, border: `1px solid ${P.green}25`, boxShadow: `0 0 20px ${P.green}08` }}
              >
                <motion.div className="absolute left-0 top-0 bottom-0 w-1 rounded-r" style={{ backgroundColor: P.green }}
                  animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }}
                />
                <span className="text-[9px] font-bold font-mono px-1.5 py-0.5 rounded" style={{ color: P.green, backgroundColor: `${P.green}15` }}>NOW</span>
                <span className="font-mono text-sm font-bold flex-1" style={{ color: P.green, textShadow: `0 0 10px ${P.green}80` }}>
                  {currentLevel.price.toFixed(d.price.decimals)}
                </span>
                <span className="text-[10px] font-mono" style={{ color: `${P.green}80` }}>HERE</span>
              </motion.div>
            </div>
          )}

          {/* Support levels */}
          <div className="px-3 space-y-1 pb-3">
            {supportLevels.map((level, i) => (
              <CompactLevelRow key={`s-${i}`} level={level} decimals={d.price.decimals} />
            ))}
          </div>

          {/* Divider */}
          <div className="mx-4 border-t" style={{ borderColor: P.border }} />

          {/* Nearest Levels Summary */}
          <div className="px-4 py-3 grid grid-cols-2 gap-2">
            {d.levels.nearest_resistance && (
              <div className="rounded-lg p-2.5" style={{ backgroundColor: `${P.red}06`, border: `1px solid ${P.red}15` }}>
                <div className="text-[8px] font-mono uppercase tracking-wider mb-1" style={{ color: `${P.red}80` }}>Nearest Resistance</div>
                <div className="text-sm font-bold font-mono" style={{ color: P.red }}>{d.levels.nearest_resistance.price.toFixed(d.price.decimals)}</div>
                <div className="text-[9px] font-mono" style={{ color: `${P.red}60` }}>{d.levels.nearest_resistance.distance_display}</div>
              </div>
            )}
            {d.levels.nearest_support && (
              <div className="rounded-lg p-2.5" style={{ backgroundColor: `${P.accent}06`, border: `1px solid ${P.accent}15` }}>
                <div className="text-[8px] font-mono uppercase tracking-wider mb-1" style={{ color: `${P.accent}80` }}>Nearest Support</div>
                <div className="text-sm font-bold font-mono" style={{ color: P.accent }}>{d.levels.nearest_support.price.toFixed(d.price.decimals)}</div>
                <div className="text-[9px] font-mono" style={{ color: `${P.accent}60` }}>{d.levels.nearest_support.distance_display}</div>
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="mx-4 border-t" style={{ borderColor: P.border }} />

          {/* Trading Suggestion */}
          <div className="px-4 py-3 flex-1">
            <div className="flex items-center gap-1.5 mb-2">
              <TargetIcon size={14} style={{ color: trendColor }} />
              <span className="text-[10px] uppercase tracking-[0.2em] font-mono" style={{ color: "rgba(255,255,255,0.35)" }}>Trade Setup</span>
            </div>
            <p className="text-[11px] text-white/50 mb-3 font-mono leading-relaxed">{d.trade_zones.suggestion}</p>

            {d.trade_zones.target != null && d.trade_zones.stop != null && (
              <div className="grid grid-cols-2 gap-2">
                <div className="text-center rounded-lg py-2" style={{ background: `${P.green}05`, border: `1px solid ${P.green}10` }}>
                  <div className="text-[8px] text-white/25 font-mono uppercase tracking-wider mb-0.5">
                    <TargetIcon size={10} className="inline mr-0.5" style={{ color: P.green }} />Target
                  </div>
                  <div className="text-base font-bold font-mono" style={{ color: P.green, textShadow: `0 0 6px ${P.green}30` }}>
                    {d.trade_zones.target.toFixed(d.price.decimals)}
                  </div>
                </div>
                <div className="text-center rounded-lg py-2" style={{ background: `${P.red}05`, border: `1px solid ${P.red}10` }}>
                  <div className="text-[8px] text-white/25 font-mono uppercase tracking-wider mb-0.5">
                    <SecurityShieldIcon size={10} className="inline mr-0.5" style={{ color: P.red }} />Stop
                  </div>
                  <div className="text-base font-bold font-mono" style={{ color: P.red, textShadow: `0 0 6px ${P.red}30` }}>
                    {d.trade_zones.stop.toFixed(d.price.decimals)}
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
            style={{ background: P.surface, backdropFilter: "blur(8px)" }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setExplanationModal(null)}
          >
            <motion.div
              className="max-w-md w-full p-6 rounded-2xl"
              style={{ background: P.surface, border: `1px solid ${P.green}15`, boxShadow: `0 0 40px ${P.green}10` }}
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold font-mono" style={{ color: P.green }}>{explanationModal.title}</h3>
                <button onClick={() => setExplanationModal(null)} className="text-white/40 hover:text-white"><CloseIcon size={20} /></button>
              </div>
              <p className="text-sm text-white/60 leading-relaxed">{explanationModal.content}</p>
              <button onClick={() => setExplanationModal(null)} className="mt-5 w-full py-2 rounded-xl text-sm font-bold font-mono"
                style={{ background: `${P.green}10`, border: `1px solid ${P.green}25`, color: P.green }}>
                Got it
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
