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
    ratio?: number;
    available?: boolean;
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

/* ── Neon helpers ── */
const neonColors: Record<string, { accent: string; glow: string; bg: string }> = {
  up:      { accent: "#00ff88", glow: "rgba(0,255,136,0.15)", bg: "rgba(0,255,136,0.06)" },
  down:    { accent: "#ff3366", glow: "rgba(255,51,102,0.15)", bg: "rgba(255,51,102,0.06)" },
  neutral: { accent: "#f0b429", glow: "rgba(240,180,41,0.15)", bg: "rgba(240,180,41,0.06)" },
};

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

  const nc = data ? neonColors[data.trend.direction] || neonColors.neutral : neonColors.neutral;

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-40 rounded-xl mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px ${nc.glow}, inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* ── Header ── */}
      <div className="px-4 py-3 flex items-center justify-between flex-wrap gap-2" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${nc.accent}20`, boxShadow: `0 0 12px ${nc.accent}40` }}>
            <Zap className="w-4 h-4" style={{ color: nc.accent }} />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-bold text-white/90 truncate font-mono">{t("pulse.title")}</h2>
            <p className="text-[10px] truncate" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.subtitle")}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.1)" }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setActiveSymbol(s.key)}
                className="px-2.5 py-1 text-[10px] font-bold font-mono transition-all"
                style={{
                  background: activeSymbol === s.key ? `${nc.accent}25` : "rgba(255,255,255,0.03)",
                  color: activeSymbol === s.key ? nc.accent : "rgba(255,255,255,0.4)",
                  borderRight: "1px solid rgba(255,255,255,0.05)",
                }}
              >{s.label}</button>
            ))}
          </div>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
            className="text-[10px] font-mono px-2 py-1 rounded-lg" style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.08)" }}>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
          </select>
          <button onClick={fetchData} className="p-1.5 rounded-lg transition-all hover:brightness-150" style={{ background: "rgba(255,255,255,0.05)" }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: "rgba(255,255,255,0.35)" }} />
          </button>
          {onSwitchMode && (
            <button onClick={onSwitchMode} className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold font-mono"
              style={{ background: "rgba(99,102,241,0.2)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.3)" }}>
              <Brain className="w-3 h-3" /> EMEL
            </button>
          )}
        </div>
      </div>

      {/* ── Error ── */}
      {error && !data && !loading && (
        <div className="p-8 text-center">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-40" style={{ color: nc.accent }} />
          <p className="font-medium mb-1 font-mono text-sm" style={{ color: nc.accent }}>{activeSymbol}</p>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.insufficientData")}</p>
        </div>
      )}

      {data && (
        <>
          {/* ── Main Trend Gauge ── */}
          <div className="p-6 text-center" style={{ background: nc.bg }}>
            <div className="flex items-center justify-center gap-2 mb-2">
              {data.trend.direction === "up" ? (
                <ArrowUp className="w-7 h-7" style={{ color: nc.accent, filter: `drop-shadow(0 0 6px ${nc.accent})` }} />
              ) : data.trend.direction === "down" ? (
                <ArrowDown className="w-7 h-7" style={{ color: nc.accent, filter: `drop-shadow(0 0 6px ${nc.accent})` }} />
              ) : (
                <Activity className="w-7 h-7" style={{ color: nc.accent, filter: `drop-shadow(0 0 6px ${nc.accent})` }} />
              )}
              <span className="text-2xl font-bold font-mono" style={{ color: nc.accent, textShadow: `0 0 20px ${nc.glow}` }}>
                {data.trend.label}
              </span>
            </div>
            <p className="text-lg font-mono" style={{ color: nc.accent, opacity: 0.8 }}>
              {data.trend.strength_pct}% {t("pulse.strong")}
            </p>

            {/* Strength Bar */}
            <div className="w-full max-w-xs mx-auto mt-4">
              <div className="h-2.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${data.trend.strength_pct}%`, background: `linear-gradient(90deg, ${nc.accent}80, ${nc.accent})`, boxShadow: `0 0 12px ${nc.accent}60` }} />
              </div>
              <p className="text-[10px] font-mono mt-1.5" style={{ color: "rgba(255,255,255,0.25)" }}>({data.trend.strength.toFixed(2)}/1.0)</p>
            </div>

            {/* Last 5 Candles */}
            <div className="flex items-center justify-center gap-1.5 mt-4">
              <span className="text-[10px] font-mono mr-2" style={{ color: "rgba(255,255,255,0.25)" }}>{t("pulse.last5min")}</span>
              {data.trend.last_5_candles.map((candle, i) => (
                <span key={i} className="text-base" style={{ color: candle === "up" ? "#00ff88" : candle === "down" ? "#ff3366" : "rgba(255,255,255,0.3)", filter: `drop-shadow(0 0 4px ${candle === "up" ? "#00ff8860" : candle === "down" ? "#ff336660" : "transparent"})` }}>
                  {candle === "up" ? "▲" : candle === "down" ? "▼" : "●"}
                </span>
              ))}
            </div>
          </div>

          {/* ── Price & Time Bar ── */}
          <div className="flex items-center justify-center gap-6 sm:gap-10 px-4 py-3 flex-wrap" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(255,255,255,0.04)", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <div className="text-center">
              <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.price")}</span>
              <p className="text-lg font-bold font-mono text-white">{data.price.current.toFixed(2)}</p>
            </div>
            <div className="text-center">
              <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.change5m")}</span>
              <p className="text-lg font-bold font-mono" style={{ color: data.price.change_5 >= 0 ? "#00ff88" : "#ff3366" }}>
                {data.price.change_5 >= 0 ? "+" : ""}{data.price.change_5.toFixed(2)}%
              </p>
            </div>
            <div className="text-center">
              <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.update")}</span>
              <p className="text-xs font-mono" style={{ color: "rgba(255,255,255,0.5)" }}>{t("pulse.every5s")}</p>
            </div>
          </div>

          {/* ── 3-Column Grid ── */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 p-3">
            {/* Levels */}
            <div className="rounded-xl p-3.5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-3 flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Target className="w-3 h-3" style={{ color: "#00ccff" }} /> {t("pulse.levels")}
              </h3>
              <div className="space-y-1.5 text-sm font-mono">
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(255,51,102,0.06)" }}>
                  <span style={{ color: "#ff3366" }}>R2</span>
                  <span className="text-white/80">{data.levels.r2.toFixed(0)}</span>
                </div>
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(255,51,102,0.06)" }}>
                  <span style={{ color: "#ff3366" }}>R1</span>
                  <span className="text-white/80">{data.levels.r1.toFixed(0)}</span>
                </div>
                <div className="flex justify-between px-2 py-1.5 rounded-lg" style={{ background: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.15)" }}>
                  <span style={{ color: "#00ff88" }}>{t("pulse.priceLabel")}</span>
                  <span className="font-bold" style={{ color: "#00ff88" }}>{data.price.current.toFixed(0)}</span>
                </div>
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(0,204,255,0.06)" }}>
                  <span style={{ color: "#00ccff" }}>S1</span>
                  <span className="text-white/80">{data.levels.s1.price.toFixed(0)}{data.levels.s1.alert && " ⚡"}</span>
                </div>
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(0,204,255,0.06)" }}>
                  <span style={{ color: "#00ccff" }}>S2</span>
                  <span className="text-white/80">{data.levels.s2.toFixed(0)}</span>
                </div>
              </div>
              {data.levels.s1.alert && (
                <p className="text-[10px] font-mono mt-2" style={{ color: "#f0b429" }}>
                  ⚡ {t("pulse.nearSupport")} ({data.levels.s1.distance.toFixed(0)} {t("pulse.pts")})
                </p>
              )}
            </div>

            {/* Momentum */}
            <div className="rounded-xl p-3.5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-3 flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Activity className="w-3 h-3" style={{ color: "#818cf8" }} /> {t("pulse.momentum")}
              </h3>
              <div className="space-y-2.5">
                {([
                  { label: "RSI", value: data.momentum.rsi.value.toFixed(0), trend: data.momentum.rsi.trend },
                  { label: "MACD", value: `${data.momentum.macd.value > 0 ? "+" : ""}${data.momentum.macd.value.toFixed(2)}`, trend: data.momentum.macd.trend },
                  { label: "Stoch", value: data.momentum.stochastic.value.toFixed(0), trend: data.momentum.stochastic.trend },
                ] as const).map((m) => (
                  <div key={m.label} className="flex justify-between items-center px-2 py-1.5 rounded-lg font-mono text-sm" style={{ background: "rgba(255,255,255,0.02)" }}>
                    <span style={{ color: "rgba(255,255,255,0.4)" }}>{m.label}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-white/80">{m.value}</span>
                      <span style={{ color: m.trend === "up" ? "#00ff88" : "#ff3366", filter: `drop-shadow(0 0 4px ${m.trend === "up" ? "#00ff8860" : "#ff336660"})` }}>
                        {m.trend === "up" ? "▲" : "▼"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Volume */}
            <div className="rounded-xl p-3.5" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <h3 className="text-[10px] uppercase tracking-widest font-mono mb-3 flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                <Zap className="w-3 h-3" style={{ color: "#f0b429" }} /> {t("pulse.volume")}
              </h3>
              <div className="text-center py-3">
                <p className="text-xl font-bold font-mono" style={{
                  color: data.volume.status === "high" ? "#00ff88" : data.volume.status === "low" ? "#ff3366" : data.volume.status === "normal" ? "#f0b429" : "rgba(255,255,255,0.3)",
                  textShadow: `0 0 12px ${data.volume.status === "high" ? "rgba(0,255,136,0.3)" : data.volume.status === "low" ? "rgba(255,51,102,0.3)" : "transparent"}`,
                }}>
                  {data.volume.label}
                </p>
                {data.volume.available && data.volume.ratio != null && (
                  <p className="text-[10px] font-mono mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>{data.volume.ratio.toFixed(2)}x avg</p>
                )}
                <p className="text-[10px] font-mono mt-2" style={{ color: "rgba(255,255,255,0.2)" }}>
                  {data.volume.available
                    ? (data.volume.status === "high" ? t("pulse.buyersActive") : data.volume.status === "low" ? t("pulse.lowInterest") : "")
                    : t("pulse.noData")}
                </p>
              </div>
            </div>
          </div>

          {/* ── AI Suggestion ── */}
          <div className="px-3 pb-3">
            <div className="rounded-xl p-4" style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.12)", boxShadow: "0 0 20px rgba(99,102,241,0.05)" }}>
              <div className="flex items-center gap-2 mb-2.5">
                <Brain className="w-4 h-4" style={{ color: "#818cf8" }} />
                <span className="font-mono font-bold text-sm" style={{ color: "#818cf8" }}>{t("pulse.aiComment")}</span>
              </div>
              <p className="text-sm font-mono leading-relaxed" style={{ color: "rgba(255,255,255,0.55)" }}>{data.suggestion.text}</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3 text-center">
                <div className="rounded-lg py-2" style={{ background: "rgba(0,255,136,0.05)", border: "1px solid rgba(0,255,136,0.1)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.target")}</p>
                  <p className="font-bold font-mono" style={{ color: "#00ff88" }}>{data.suggestion.target.toFixed(0)}</p>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>+{data.suggestion.target_distance.toFixed(0)} pts</p>
                </div>
                <div className="rounded-lg py-2" style={{ background: "rgba(255,51,102,0.05)", border: "1px solid rgba(255,51,102,0.1)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.stop")}</p>
                  <p className="font-bold font-mono" style={{ color: "#ff3366" }}>{data.suggestion.stop.toFixed(0)}</p>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>-{data.suggestion.stop_distance.toFixed(0)} pts</p>
                </div>
                <div className="rounded-lg py-2" style={{ background: "rgba(0,204,255,0.05)", border: "1px solid rgba(0,204,255,0.1)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>R/R</p>
                  <p className="font-bold font-mono" style={{ color: "#00ccff" }}>{data.suggestion.rr_ratio.toFixed(2)}</p>
                </div>
                <div className="rounded-lg py-2" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.expectation")}</p>
                  <p className="font-bold font-mono text-white/70">{data.suggestion.timeframe_estimate}</p>
                </div>
              </div>
            </div>
          </div>

          {/* ── Action Buttons ── */}
          <div className="px-3 pb-3 flex gap-2 flex-wrap">
            <button className="flex-1 min-w-[90px] py-2 rounded-xl font-mono font-bold text-xs flex items-center justify-center gap-1.5 transition-all hover:brightness-125"
              style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)", boxShadow: "0 0 12px rgba(0,255,136,0.08)" }}>
              <TrendingUp className="w-3.5 h-3.5" /> {t("pulse.watchUp")}
            </button>
            <button className="flex-1 min-w-[90px] py-2 rounded-xl font-mono font-bold text-xs flex items-center justify-center gap-1.5 transition-all hover:brightness-125"
              style={{ background: "rgba(255,51,102,0.1)", color: "#ff3366", border: "1px solid rgba(255,51,102,0.2)", boxShadow: "0 0 12px rgba(255,51,102,0.08)" }}>
              <TrendingDown className="w-3.5 h-3.5" /> {t("pulse.watchDown")}
            </button>
            <button className="flex-1 min-w-[90px] py-2 rounded-xl font-mono font-bold text-xs flex items-center justify-center gap-1.5 transition-all hover:brightness-125"
              style={{ background: "rgba(255,255,255,0.04)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <Activity className="w-3.5 h-3.5" /> {t("pulse.detailedChart")}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
