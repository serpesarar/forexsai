"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { PanelInfoButton } from "../PanelInfoButton";
import {
  ArrowUpIcon as ArrowUp,
  ArrowDownIcon as ArrowDown,
  ActivityIcon as Activity,
  TargetIcon as Target,
  RotateIcon as RefreshCw,
  ArrowUpRightIcon as TrendingUp,
  ArrowDownRightIcon as TrendingDown,
} from "../ui/CustomIcons";
import { PulseIcon, EmelIcon, SignalsIcon } from "../ui/CustomIcons";

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

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
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "CL.COMM", label: "US Oil" },
];

/* ── Institutional Color Palette ── */
const P = { bg: "#0B0F17", card: "#141C2B", surface: "#111827", border: "rgba(255,255,255,0.06)", text: "#E6EDF3", muted: "#6B7280", green: "#16C784", red: "#EA3943", warn: "#F5A623", accent: "#4F8CFF" };
const neonColors: Record<string, { accent: string; glow: string; bg: string }> = {
  up: { accent: P.green, glow: "rgba(22,199,132,0.08)", bg: "rgba(22,199,132,0.05)" },
  down: { accent: P.red, glow: "rgba(234,57,67,0.08)", bg: "rgba(234,57,67,0.05)" },
  neutral: { accent: P.warn, glow: "rgba(245,166,35,0.08)", bg: "rgba(245,166,35,0.05)" },
};

export default function PulsePanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: PulsePanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<PulseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState("5m");
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);


  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
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
  }, [activeSymbol, timeframe]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Listen for global refresh event from header button
  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("pulse-refresh", handler);
    window.addEventListener("dashboard-refresh", handler);
    return () => {
      window.removeEventListener("pulse-refresh", handler);
      window.removeEventListener("dashboard-refresh", handler);
    };
  }, [fetchData]);

  const nc = data ? neonColors[data.trend.direction] || neonColors.neutral : neonColors.neutral;

  if (loading && !data) {
    return (
      <div className="p-2 animate-pulse bg-transparent">
        <div className="h-40 mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden bg-transparent border-0 shadow-none">

      {/* ── Header ── */}
      <div className="px-2 py-2 flex items-center justify-between flex-wrap gap-2 bg-transparent">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${P.accent}12`, border: `1px solid ${P.accent}20` }}>
            <PulseIcon size={16} style={{ color: P.accent }} />
          </div>
          <div className="min-w-0">
            <h2 style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: P.text }}>{t("pulse.title")}</h2>
            <p style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>{t("pulse.subtitle")}</p>
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
          <PanelInfoButton panelId="pulse-panel" />
          {onSwitchMode && (
            <button onClick={onSwitchMode} className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold font-mono"
              style={{ background: "rgba(99,102,241,0.2)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.3)" }}>
              <EmelIcon size={12} style={{ color: "#818cf8" }} /> EMEL
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
          <div className="p-2 text-center bg-transparent">
            <div className="flex items-center justify-center gap-2 mb-2">
              {data.trend.direction === "up" ? (
                <ArrowUp className="w-7 h-7" style={{ color: nc.accent }} />
              ) : data.trend.direction === "down" ? (
                <ArrowDown className="w-7 h-7" style={{ color: nc.accent }} />
              ) : (
                <Activity className="w-7 h-7" style={{ color: nc.accent }} />
              )}
              <span style={{ fontFamily: FONT, fontSize: 28, fontWeight: 700, color: nc.accent, letterSpacing: "-0.5px" }}>
                {data.trend.label}
              </span>
            </div>
            <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 500, color: nc.accent, opacity: 0.8 }}>
              {data.trend.strength_pct}% {t("pulse.strong")}
            </p>

            {/* Strength Bar */}
            <div className="w-full max-w-xs mx-auto mt-4">
              <div className="rounded-full overflow-hidden" style={{ height: 6, background: P.border }}>
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${data.trend.strength_pct}%`, background: nc.accent, opacity: 0.85 }} />
              </div>
              <p style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 6 }}>({data.trend.strength.toFixed(2)}/1.0)</p>
            </div>

            {/* Last 5 Candles */}
            <div className="flex items-center justify-center gap-1.5 mt-4">
              <span className="text-[10px] font-mono mr-2" style={{ color: "rgba(255,255,255,0.25)" }}>{t("pulse.last5min")}</span>
              {data.trend.last_5_candles.map((candle, i) => (
                <span key={i} style={{ fontSize: 16, color: candle === "up" ? P.green : candle === "down" ? P.red : P.muted }}>
                  {candle === "up" ? "▲" : candle === "down" ? "▼" : "●"}
                </span>
              ))}
            </div>
          </div>

          {/* ── Price & Time Bar ── */}
          <div className="flex items-center justify-center gap-6 sm:gap-10 px-2 py-2 flex-wrap bg-transparent">
            <div className="text-center">
              <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.06em", textTransform: "uppercase" as const }}>{t("pulse.price")}</span>
              <p style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: P.text, letterSpacing: "-0.3px" }}>{data.price.current.toFixed(2)}</p>
            </div>
            <div className="text-center">
              <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.06em", textTransform: "uppercase" as const }}>{t("pulse.change5m")}</span>
              <p style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: data.price.change_5 >= 0 ? P.green : P.red, letterSpacing: "-0.3px" }}>
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
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: `${P.red}06` }}>
                  <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.red }}>R2</span>
                  <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.r2.toFixed(0)}</span>
                </div>
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: `${P.red}06` }}>
                  <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.red }}>R1</span>
                  <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.r1.toFixed(0)}</span>
                </div>
                <div className="flex justify-between px-2 py-1.5 rounded-lg" style={{ background: `${P.green}08`, border: `1px solid ${P.green}20` }}>
                  <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.green }}>{t("pulse.priceLabel")}</span>
                  <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.green }}>{data.price.current.toFixed(0)}</span>
                </div>
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: `${P.accent}06` }}>
                  <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.accent }}>S1</span>
                  <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.s1.price.toFixed(0)}{data.levels.s1.alert && " ⚡"}</span>
                </div>
                <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: `${P.accent}06` }}>
                  <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.accent }}>S2</span>
                  <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.s2.toFixed(0)}</span>
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
                      <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{m.value}</span>
                      <span style={{ color: m.trend === "up" ? P.green : P.red }}>
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
                <PulseIcon size={12} style={{ color: "#f0b429" }} /> {t("pulse.volume")}
              </h3>
              <div className="text-center py-3">
                <p style={{ fontFamily: FONT, fontSize: 20, fontWeight: 700, color: data.volume.status === "high" ? P.green : data.volume.status === "low" ? P.red : data.volume.status === "normal" ? P.warn : P.muted }}>
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
            <div className="rounded-xl p-4" style={{ background: `${P.accent}06`, border: `1px solid ${P.accent}12` }}>
              <div className="flex items-center gap-2 mb-2.5">
                <SignalsIcon size={16} style={{ color: P.accent }} />
                <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.accent }}>{t("pulse.aiComment")}</span>
              </div>
              <p style={{ fontFamily: FONT, fontSize: 12, lineHeight: 1.6, color: "rgba(230,237,243,0.65)" }}>{data.suggestion.text}</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3 text-center">
                <div className="rounded-lg py-2" style={{ background: `${P.green}06`, border: `1px solid ${P.green}15` }}>
                  <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.05em" }}>{t("pulse.target")}</p>
                  <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 700, color: P.green }}>{data.suggestion.target.toFixed(0)}</p>
                  <p style={{ fontFamily: FONT, fontSize: 9, color: P.muted }}>+{data.suggestion.target_distance.toFixed(0)} pts</p>
                </div>
                <div className="rounded-lg py-2" style={{ background: `${P.red}06`, border: `1px solid ${P.red}15` }}>
                  <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.05em" }}>{t("pulse.stop")}</p>
                  <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 700, color: P.red }}>{data.suggestion.stop.toFixed(0)}</p>
                  <p style={{ fontFamily: FONT, fontSize: 9, color: P.muted }}>-{data.suggestion.stop_distance.toFixed(0)} pts</p>
                </div>
                <div className="rounded-lg py-2" style={{ background: `${P.accent}06`, border: `1px solid ${P.accent}15` }}>
                  <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.05em" }}>R/R</p>
                  <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 700, color: P.accent }}>{data.suggestion.rr_ratio.toFixed(2)}</p>
                </div>
                <div className="rounded-lg py-2" style={{ background: P.surface, border: `1px solid ${P.border}` }}>
                  <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.05em" }}>{t("pulse.expectation")}</p>
                  <p style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "rgba(230,237,243,0.7)" }}>{data.suggestion.timeframe_estimate}</p>
                </div>
              </div>
            </div>
          </div>

          {/* ── Action Buttons ── */}
          <div className="px-3 pb-3 flex gap-2 flex-wrap">
            <button className="flex-1 min-w-[90px] py-2 rounded-xl flex items-center justify-center gap-1.5 transition-all duration-150"
              style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, background: `${P.green}08`, color: P.green, border: `1px solid ${P.green}18` }}
              onMouseEnter={(e) => (e.currentTarget.style.background = `${P.green}15`)}
              onMouseLeave={(e) => (e.currentTarget.style.background = `${P.green}08`)}>
              <TrendingUp className="w-3.5 h-3.5" /> {t("pulse.watchUp")}
            </button>
            <button className="flex-1 min-w-[90px] py-2 rounded-xl flex items-center justify-center gap-1.5 transition-all duration-150"
              style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, background: `${P.red}08`, color: P.red, border: `1px solid ${P.red}18` }}
              onMouseEnter={(e) => (e.currentTarget.style.background = `${P.red}15`)}
              onMouseLeave={(e) => (e.currentTarget.style.background = `${P.red}08`)}>
              <TrendingDown className="w-3.5 h-3.5" /> {t("pulse.watchDown")}
            </button>
            <button className="flex-1 min-w-[90px] py-2 rounded-xl flex items-center justify-center gap-1.5 transition-all duration-150"
              style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, background: P.surface, color: P.muted, border: `1px solid ${P.border}` }}>
              <Activity className="w-3.5 h-3.5" /> {t("pulse.detailedChart")}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
