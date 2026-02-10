"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
} from "lucide-react";
import { useI18nStore } from "../../lib/i18n/store";
import { useProximityAnimation } from "../../hooks/useProximityAnimation";
import TrendChannelChart from "./TrendChannelChart";

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
    trend_channel: { upper: number[]; lower: number[]; middle: number[] };
  };
  explanations: Record<string, string>;
}

/* ──────────────────── Constants ──────────────────── */

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ", icon: "📊" },
  { key: "XAUUSD", label: "XAUUSD", icon: "🥇" },
];

/* ──────────────────── Sub-Components ──────────────────── */

function NeonStrengthBar({ percent, direction }: { percent: number; direction: string }) {
  const clampedPercent = Math.min(100, Math.max(0, percent));
  const getGradient = () => {
    if (direction === "UP") return "from-red-500 via-yellow-400 to-green-400";
    if (direction === "DOWN") return "from-green-400 via-yellow-400 to-red-500";
    return "from-gray-500 via-yellow-400 to-gray-500";
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-[10px] uppercase tracking-widest text-white/40 font-mono">Power</span>
      <div className="relative w-3 h-20 rounded-full overflow-hidden bg-white/5 border border-white/10">
        <motion.div
          className={`absolute bottom-0 left-0 right-0 rounded-full bg-gradient-to-t ${getGradient()}`}
          initial={{ height: 0 }}
          animate={{ height: `${clampedPercent}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          style={{
            boxShadow:
              direction === "UP"
                ? `0 0 ${8 + clampedPercent * 0.12}px rgba(0,255,136,0.6)`
                : direction === "DOWN"
                ? `0 0 ${8 + clampedPercent * 0.12}px rgba(255,51,102,0.6)`
                : `0 0 8px rgba(255,255,0,0.3)`,
          }}
        />
      </div>
      <span
        className="text-xs font-bold font-mono"
        style={{
          color: direction === "UP" ? "#00ff88" : direction === "DOWN" ? "#ff3366" : "#fbbf24",
          textShadow:
            direction === "UP"
              ? "0 0 8px rgba(0,255,136,0.6)"
              : direction === "DOWN"
              ? "0 0 8px rgba(255,51,102,0.6)"
              : "0 0 8px rgba(251,191,36,0.4)",
        }}
      >
        {clampedPercent}%
      </span>
    </div>
  );
}

function EmaPill({
  label,
  value,
  currentPrice,
  color,
  isProximate,
  decimals,
}: {
  label: string;
  value: number;
  currentPrice: number;
  color: string;
  isProximate: boolean;
  decimals: number;
}) {
  const isAbove = currentPrice > value;
  return (
    <motion.div
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border font-mono text-xs"
      style={{
        borderColor: `${color}${isProximate ? "80" : "30"}`,
        backgroundColor: `${color}${isProximate ? "18" : "08"}`,
        boxShadow: isProximate ? `0 0 12px ${color}40, inset 0 0 8px ${color}10` : "none",
      }}
      animate={isProximate ? { scale: [1, 1.03, 1] } : {}}
      transition={isProximate ? { duration: 1.5, repeat: Infinity } : {}}
    >
      <span style={{ color }} className="font-bold text-[10px]">
        {label}
      </span>
      <span className="text-white/80">{value.toFixed(decimals)}</span>
      {isAbove ? (
        <ArrowUp className="w-3 h-3" style={{ color: "#00ff88" }} />
      ) : (
        <ArrowDown className="w-3 h-3" style={{ color: "#ff3366" }} />
      )}
    </motion.div>
  );
}

function LevelCard({
  level,
  decimals,
  onClick,
  supportProximity,
  resistanceProximity,
}: {
  level: LevelData;
  decimals: number;
  onClick: () => void;
  supportProximity: boolean;
  resistanceProximity: boolean;
}) {
  const isCurrent = level.type === "current";
  const isResistance = level.type === "resistance";
  const isSupport = level.type === "support";

  const isProximate = (isSupport && supportProximity) || (isResistance && resistanceProximity);

  const borderColor = isCurrent
    ? "rgba(0,255,136,0.4)"
    : isResistance
    ? `rgba(255,51,102,${isProximate ? 0.6 : 0.25})`
    : `rgba(0,204,255,${isProximate ? 0.6 : 0.25})`;

  const bgColor = isCurrent
    ? "rgba(0,255,136,0.06)"
    : isResistance
    ? `rgba(255,51,102,${isProximate ? 0.12 : 0.05})`
    : `rgba(0,204,255,${isProximate ? 0.12 : 0.05})`;

  const glowColor = isCurrent
    ? "0 0 20px rgba(0,255,136,0.15)"
    : isResistance
    ? isProximate
      ? "0 0 16px rgba(255,51,102,0.25)"
      : "none"
    : isProximate
    ? "0 0 16px rgba(0,204,255,0.25)"
    : "none";

  return (
    <motion.div
      onClick={onClick}
      className="relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all group"
      style={{
        border: `1px solid ${borderColor}`,
        backgroundColor: bgColor,
        boxShadow: glowColor,
      }}
      whileHover={{ y: -2, boxShadow: isCurrent ? "0 0 30px rgba(0,255,136,0.25)" : isResistance ? "0 0 24px rgba(255,51,102,0.3)" : "0 0 24px rgba(0,204,255,0.3)" }}
      animate={isProximate ? { scale: [1, 1.01, 1] } : {}}
      transition={isProximate ? { duration: 1.2, repeat: Infinity } : { duration: 0.2 }}
    >
      {/* Level badge */}
      <div
        className="w-11 h-7 rounded-md flex items-center justify-center text-[10px] font-bold font-mono tracking-wide"
        style={{
          backgroundColor: isCurrent
            ? "rgba(0,255,136,0.2)"
            : isResistance
            ? "rgba(255,51,102,0.2)"
            : "rgba(0,204,255,0.2)",
          color: isCurrent ? "#00ff88" : isResistance ? "#ff3366" : "#00ccff",
          border: `1px solid ${isCurrent ? "rgba(0,255,136,0.3)" : isResistance ? "rgba(255,51,102,0.3)" : "rgba(0,204,255,0.3)"}`,
        }}
      >
        {isCurrent ? "NOW" : level.name.split(" ")[0]}
      </div>

      {/* Price */}
      <div className="flex-1 min-w-0">
        <div
          className="text-base font-bold font-mono"
          style={{
            color: isCurrent ? "#00ff88" : isResistance ? "#ff3366" : "#00ccff",
            textShadow: isCurrent ? "0 0 12px rgba(0,255,136,0.5)" : "none",
          }}
        >
          {level.price.toFixed(decimals)}
        </div>
        {!isCurrent && level.name && (
          <div className="text-[10px] text-white/30 font-mono truncate">{level.name}</div>
        )}
      </div>

      {/* Distance */}
      <div className="text-right">
        <div
          className="text-xs font-bold font-mono"
          style={{
            color: isCurrent ? "#00ff88" : isResistance ? "#ff3366" : "#00ccff",
          }}
        >
          {level.distance_display}
        </div>
        <div className="text-[10px] text-white/25 font-mono">
          {isCurrent ? "HERE" : isResistance ? "Above" : "Below"}
        </div>
      </div>

      {/* Pulse indicator for "HERE" */}
      {isCurrent && (
        <motion.div
          className="absolute -left-0.5 top-1/2 -translate-y-1/2 w-1 h-6 rounded-full"
          style={{ backgroundColor: "#00ff88" }}
          animate={{ opacity: [0.4, 1, 0.4], scaleY: [0.8, 1.1, 0.8] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}

      {/* Next level marker */}
      {level.is_next && (
        <div
          className="absolute -right-1 -top-1 w-4 h-4 rounded-full flex items-center justify-center text-[8px]"
          style={{
            backgroundColor: isResistance ? "#ff3366" : "#00ccff",
            boxShadow: isResistance ? "0 0 8px rgba(255,51,102,0.5)" : "0 0 8px rgba(0,204,255,0.5)",
          }}
        >
          <Zap className="w-2.5 h-2.5 text-white" />
        </div>
      )}
    </motion.div>
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
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [activeSymbol, timeframe]);

  const openExplanation = (key: string, title: string) => {
    if (data?.explanations?.[key]) {
      setExplanationModal({ title, content: data.explanations[key] });
    }
  };

  // Proximity hook
  const proximity = useProximityAnimation(
    data?.price?.current ?? 0,
    data?.levels?.nearest_support?.price ?? null,
    data?.levels?.nearest_resistance?.price ?? null,
    data?.trend?.ema_20 ?? null
  );

  /* ── Loading skeleton ── */
  if (loading && !data) {
    return (
      <div
        className="rounded-3xl p-6 animate-pulse"
        style={{
          background: "rgba(15,23,42,0.4)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <div className="h-8 bg-white/5 rounded-xl w-1/3 mb-6" />
        <div className="h-48 bg-white/5 rounded-2xl mb-4" />
        <div className="h-40 bg-white/5 rounded-2xl" />
      </div>
    );
  }

  if (!data) return null;

  const trendColor = data.trend.direction === "UP" ? "#00ff88" : data.trend.direction === "DOWN" ? "#ff3366" : "#fbbf24";
  const trendLabel = data.trend.direction === "UP" ? "BULLISH TREND" : data.trend.direction === "DOWN" ? "BEARISH CORRECTION" : "NEUTRAL ZONE";

  // Chart data
  const chartCloses = data.chart_data?.closes ?? [];
  const chartUpper = data.chart_data?.trend_channel?.upper ?? [];
  const chartLower = data.chart_data?.trend_channel?.lower ?? [];
  const chartMiddle = data.chart_data?.trend_channel?.middle ?? [];

  const supportLevelsForChart = (data.levels.all_levels || [])
    .filter((l) => l.type === "support")
    .map((l) => ({ price: l.price, label: l.name.split(" ")[0] }));
  const resistanceLevelsForChart = (data.levels.all_levels || [])
    .filter((l) => l.type === "resistance")
    .map((l) => ({ price: l.price, label: l.name.split(" ")[0] }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative rounded-3xl overflow-hidden"
      style={{
        background: "rgba(15,23,42,0.4)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(255,255,255,0.08)",
        boxShadow: `0 0 40px rgba(0,255,136,0.06), 0 4px 60px rgba(0,0,0,0.4)`,
      }}
    >
      {/* Ambient glow based on proximity */}
      {proximity.resistanceProximity && (
        <div
          className="absolute inset-0 pointer-events-none rounded-3xl"
          style={{
            boxShadow: `inset 0 0 60px rgba(255,51,102,${proximity.resistanceIntensity * 0.08})`,
          }}
        />
      )}
      {proximity.supportProximity && (
        <div
          className="absolute inset-0 pointer-events-none rounded-3xl"
          style={{
            boxShadow: `inset 0 0 60px rgba(0,204,255,${proximity.supportIntensity * 0.08})`,
          }}
        />
      )}

      {/* ═══ HEADER ═══ */}
      <div
        className="flex items-center justify-between p-4 border-b"
        style={{ borderColor: "rgba(255,255,255,0.06)", background: "rgba(0,0,0,0.2)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.15))",
              border: "1px solid rgba(0,255,136,0.2)",
              boxShadow: "0 0 12px rgba(0,255,136,0.1)",
            }}
          >
            <Crosshair className="w-5 h-5" style={{ color: "#00ff88" }} />
          </div>
          <div>
            <h2
              className="text-sm font-bold tracking-wide font-mono"
              style={{ color: "#00ff88", textShadow: "0 0 10px rgba(0,255,136,0.3)" }}
            >
              CLEAR TREND
            </h2>
            <p className="text-[10px] uppercase tracking-[0.2em] text-white/30">Neon Trend Analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {/* Symbol Switcher */}
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {SYMBOLS.map((s) => (
              <button
                key={s.key}
                onClick={() => setActiveSymbol(s.key)}
                className="px-2.5 py-1.5 text-[10px] font-bold font-mono transition-all flex items-center gap-1"
                style={{
                  backgroundColor: activeSymbol === s.key ? "rgba(0,255,136,0.15)" : "rgba(255,255,255,0.03)",
                  color: activeSymbol === s.key ? "#00ff88" : "rgba(255,255,255,0.4)",
                  borderRight: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <span>{s.icon}</span>
                {s.label}
              </button>
            ))}
          </div>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="text-[10px] font-mono font-bold px-2 py-1.5 rounded-lg"
            style={{
              backgroundColor: "rgba(255,255,255,0.05)",
              color: "rgba(255,255,255,0.6)",
              border: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            <option value="15m">15m</option>
            <option value="1H">1H</option>
            <option value="4H">4H</option>
            <option value="1D">1D</option>
          </select>
          <button
            onClick={fetchData}
            className="p-1.5 rounded-lg transition-all"
            style={{
              backgroundColor: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              style={{ color: "rgba(255,255,255,0.4)" }}
            />
          </button>
        </div>
      </div>

      {/* ═══ PRICE + STRENGTH BAR ═══ */}
      <div className="flex items-center justify-between px-6 py-5">
        <div className="flex-1">
          {/* EMA Pills */}
          <motion.div
            className="flex flex-wrap gap-1.5 mb-3"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2, staggerChildren: 0.1 }}
          >
            <EmaPill
              label="EMA20"
              value={data.trend.ema_20}
              currentPrice={data.price.current}
              color="#ec4899"
              isProximate={proximity.ema20Proximity}
              decimals={data.price.decimals}
            />
            <EmaPill
              label="EMA50"
              value={data.trend.ema_50}
              currentPrice={data.price.current}
              color="#f97316"
              isProximate={false}
              decimals={data.price.decimals}
            />
            {data.trend.ema_200 != null && data.trend.ema_200 > 0 && (
              <EmaPill
                label="EMA200"
                value={data.trend.ema_200}
                currentPrice={data.price.current}
                color="#e2e8f0"
                isProximate={false}
                decimals={data.price.decimals}
              />
            )}
          </motion.div>

          {/* Main Price */}
          <div className="flex items-center gap-3">
            {data.trend.direction === "UP" ? (
              <TrendingUp className="w-7 h-7" style={{ color: trendColor, filter: `drop-shadow(0 0 6px ${trendColor}60)` }} />
            ) : data.trend.direction === "DOWN" ? (
              <TrendingDown className="w-7 h-7" style={{ color: trendColor, filter: `drop-shadow(0 0 6px ${trendColor}60)` }} />
            ) : (
              <Minus className="w-7 h-7" style={{ color: trendColor }} />
            )}

            <motion.span
              className="text-4xl font-bold font-mono relative"
              style={{
                color: trendColor,
                textShadow: `0 0 20px ${trendColor}80, 0 0 40px ${trendColor}30`,
              }}
              animate={priceFlash ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              {data.price.display}
              {/* Live pulse dot */}
              <motion.span
                className="absolute -top-1 -right-3 w-2 h-2 rounded-full"
                style={{ backgroundColor: trendColor }}
                animate={{ opacity: [1, 0.3, 1], scale: [1, 1.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </motion.span>
          </div>

          {/* Trend label */}
          <p
            className="text-[11px] font-mono tracking-widest mt-1.5 uppercase"
            style={{
              color: trendColor,
              textShadow: `0 0 8px ${trendColor}40`,
              opacity: 0.8,
            }}
          >
            {trendLabel}
          </p>
        </div>

        {/* Vertical Strength Bar */}
        <NeonStrengthBar percent={data.trend.strength_percent} direction={data.trend.direction} />
      </div>

      {/* ═══ TREND CHANNEL CHART ═══ */}
      {chartCloses.length > 5 && (
        <div className="px-4 pb-2">
          <div
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(2,6,23,0.6)",
              border: "1px solid rgba(255,255,255,0.05)",
            }}
          >
            <TrendChannelChart
              closes={chartCloses}
              upper={chartUpper}
              lower={chartLower}
              middle={chartMiddle}
              supportLevels={supportLevelsForChart}
              resistanceLevels={resistanceLevelsForChart}
              currentPrice={data.price.current}
              supportProximity={proximity.supportProximity}
              resistanceProximity={proximity.resistanceProximity}
              supportIntensity={proximity.supportIntensity}
              resistanceIntensity={proximity.resistanceIntensity}
            />
          </div>
        </div>
      )}

      {/* ═══ SUPPORT / RESISTANCE LEVELS ═══ */}
      <div className="px-4 pb-3">
        <div className="flex items-center justify-between mb-2.5">
          <h3
            className="text-[10px] uppercase tracking-[0.2em] font-mono flex items-center gap-2"
            style={{ color: "rgba(255,255,255,0.35)" }}
          >
            <Shield className="w-3.5 h-3.5" style={{ color: "#00ccff" }} />
            Support & Resistance
          </h3>
          <button
            onClick={() => openExplanation("support", "Support & Resistance")}
            className="text-white/20 hover:text-white/50 transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="space-y-1.5">
          {data.levels.all_levels.map((level, index) => (
            <LevelCard
              key={index}
              level={level}
              decimals={data.price.decimals}
              onClick={() => {
                if (level.type === "resistance") openExplanation("r1_r2", "Resistance Levels");
                else if (level.type === "support") openExplanation("s1_s2", "Support Levels");
                else openExplanation("pivot", "Pivot Point");
              }}
              supportProximity={proximity.supportProximity}
              resistanceProximity={proximity.resistanceProximity}
            />
          ))}
        </div>
      </div>

      {/* ═══ NEAREST LEVELS ═══ */}
      <div className="px-4 pb-3">
        <div className="grid grid-cols-2 gap-2.5">
          {data.levels.nearest_resistance && (
            <motion.div
              onClick={() => openExplanation("resistance", "Nearest Resistance")}
              className="rounded-xl p-3 cursor-pointer transition-all"
              style={{
                backgroundColor: "rgba(255,51,102,0.05)",
                border: `1px solid rgba(255,51,102,${proximity.resistanceProximity ? 0.4 : 0.15})`,
                boxShadow: proximity.resistanceProximity ? "0 0 16px rgba(255,51,102,0.15)" : "none",
              }}
              whileHover={{ y: -2 }}
            >
              <div className="flex items-center gap-1.5 mb-1.5">
                <ArrowUp className="w-3 h-3" style={{ color: "#ff3366" }} />
                <span className="text-[10px] font-mono uppercase tracking-wider" style={{ color: "#ff3366" }}>
                  Nearest Resistance
                </span>
              </div>
              <div className="text-lg font-bold font-mono" style={{ color: "#ff3366" }}>
                {data.levels.nearest_resistance.price.toFixed(data.price.decimals)}
              </div>
              <div className="text-[10px] font-mono" style={{ color: "rgba(255,51,102,0.6)" }}>
                {data.levels.nearest_resistance.distance_display} above
              </div>
            </motion.div>
          )}
          {data.levels.nearest_support && (
            <motion.div
              onClick={() => openExplanation("support", "Nearest Support")}
              className="rounded-xl p-3 cursor-pointer transition-all"
              style={{
                backgroundColor: "rgba(0,204,255,0.05)",
                border: `1px solid rgba(0,204,255,${proximity.supportProximity ? 0.4 : 0.15})`,
                boxShadow: proximity.supportProximity ? "0 0 16px rgba(0,204,255,0.15)" : "none",
              }}
              whileHover={{ y: -2 }}
            >
              <div className="flex items-center gap-1.5 mb-1.5">
                <ArrowDown className="w-3 h-3" style={{ color: "#00ccff" }} />
                <span className="text-[10px] font-mono uppercase tracking-wider" style={{ color: "#00ccff" }}>
                  Nearest Support
                </span>
              </div>
              <div className="text-lg font-bold font-mono" style={{ color: "#00ccff" }}>
                {data.levels.nearest_support.price.toFixed(data.price.decimals)}
              </div>
              <div className="text-[10px] font-mono" style={{ color: "rgba(0,204,255,0.6)" }}>
                {data.levels.nearest_support.distance_display} below
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* ═══ TRADING SUGGESTION ═══ */}
      <div
        className="px-4 pb-4 pt-3 border-t"
        style={{ borderColor: "rgba(255,255,255,0.05)", background: "rgba(0,0,0,0.15)" }}
      >
        <div className="flex items-center justify-between mb-2.5">
          <h3
            className="text-[10px] uppercase tracking-[0.2em] font-mono flex items-center gap-2"
            style={{ color: "rgba(255,255,255,0.35)" }}
          >
            <Target className="w-3.5 h-3.5" style={{ color: trendColor }} />
            Trading Suggestion
          </h3>
          <button
            onClick={() => openExplanation("entry_zone", "Entry Zone")}
            className="text-white/20 hover:text-white/50 transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
        </div>

        <div
          className="rounded-xl p-4"
          style={{
            backgroundColor:
              data.trend.direction === "UP"
                ? "rgba(0,255,136,0.04)"
                : data.trend.direction === "DOWN"
                ? "rgba(255,51,102,0.04)"
                : "rgba(251,191,36,0.04)",
            border: `1px solid ${trendColor}20`,
          }}
        >
          <p className="text-xs text-white/70 mb-3 font-mono">{data.trade_zones.suggestion}</p>

          {data.trade_zones.target != null && data.trade_zones.stop != null && (
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center">
                <div className="text-[10px] text-white/30 mb-1 font-mono uppercase tracking-wider">
                  <Crosshair className="w-3 h-3 inline mr-1" style={{ color: "#00ff88" }} />
                  Target
                </div>
                <div
                  className="text-xl font-bold font-mono"
                  style={{ color: "#00ff88", textShadow: "0 0 8px rgba(0,255,136,0.3)" }}
                >
                  {data.trade_zones.target.toFixed(data.price.decimals)}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[10px] text-white/30 mb-1 font-mono uppercase tracking-wider">
                  <Shield className="w-3 h-3 inline mr-1" style={{ color: "#ff3366" }} />
                  Stop Loss
                </div>
                <div
                  className="text-xl font-bold font-mono"
                  style={{ color: "#ff3366", textShadow: "0 0 8px rgba(255,51,102,0.3)" }}
                >
                  {data.trade_zones.stop.toFixed(data.price.decimals)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ═══ EXPLANATION MODAL ═══ */}
      <AnimatePresence>
        {explanationModal && (
          <motion.div
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
            style={{ backgroundColor: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setExplanationModal(null)}
          >
            <motion.div
              className="max-w-md w-full p-6 rounded-2xl"
              style={{
                background: "rgba(15,23,42,0.95)",
                border: "1px solid rgba(0,255,136,0.15)",
                boxShadow: "0 0 40px rgba(0,255,136,0.1), 0 20px 60px rgba(0,0,0,0.5)",
              }}
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold font-mono" style={{ color: "#00ff88" }}>
                  {explanationModal.title}
                </h3>
                <button onClick={() => setExplanationModal(null)} className="text-white/40 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-white/60 leading-relaxed">{explanationModal.content}</p>
              <button
                onClick={() => setExplanationModal(null)}
                className="mt-5 w-full py-2 rounded-xl text-sm font-bold font-mono"
                style={{
                  background: "rgba(0,255,136,0.1)",
                  border: "1px solid rgba(0,255,136,0.25)",
                  color: "#00ff88",
                }}
              >
                Got it
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
