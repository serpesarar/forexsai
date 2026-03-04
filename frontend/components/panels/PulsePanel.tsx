"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { PanelHeader } from "../PanelHeader";
import {
  ActivityIcon as Activity,
  TargetIcon as Target,
  ArrowUpRightIcon as TrendingUp,
  ArrowDownRightIcon as TrendingDown,
} from "../ui/CustomIcons";

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
  { key: "USOIL.FOREX", label: "US Oil" },
];

/* ── Theme-aware Color Palette (CSS Variables) ── */
const getThemeColors = (direction: string) => {
  const isUp = direction === "up";
  const isDown = direction === "down";
  return {
    accent: isUp ? "var(--accent-positive)" : isDown ? "var(--accent-negative)" : "var(--accent-warning)",
    glow: isUp ? "rgba(22,199,132,0.08)" : isDown ? "rgba(234,57,67,0.08)" : "rgba(245,166,35,0.08)",
    bg: isUp ? "var(--success-bg)" : isDown ? "var(--danger-bg)" : "var(--warning-bg)",
  };
};

export default function PulsePanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: PulsePanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<PulseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState("5m");
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [signalAge, setSignalAge] = useState<string>("");
  const [signalTimestamp, setSignalTimestamp] = useState<Date | null>(null);


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
        // Reset signal age timer when new signal arrives
        if (json.signal_timestamp) {
          setSignalTimestamp(new Date(json.signal_timestamp));
        } else {
          setSignalTimestamp(new Date());
        }
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
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Signal age timer - updates every second
  useEffect(() => {
    if (!signalTimestamp) return;
    const tick = () => {
      const diff = Math.floor((Date.now() - signalTimestamp.getTime()) / 1000);
      if (diff < 60) {
        setSignalAge(`${diff}s`);
      } else {
        setSignalAge(`${Math.floor(diff / 60)}m ${diff % 60}s`);
      }
    };
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [signalTimestamp]);

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

  const nc = data ? getThemeColors(data.trend.direction) : getThemeColors("neutral");

  const getDirColor = (dir: string) => {
    if (dir === "up" || dir === "BUY") return "var(--accent-positive)";
    if (dir === "down" || dir === "SELL") return "var(--accent-negative)";
    return "var(--accent-warning)";
  };

  if (loading && !data) {
    return (
      <div className="animate-pulse p-6 rounded-xl border border-theme-subtle" style={{ background: "var(--bg-primary)" }}>
        <div className="h-12 w-1/3 bg-white/5 rounded-lg mb-6" />
        <div className="grid grid-cols-12 gap-[1px] bg-white/5 h-64 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-xl overflow-hidden" style={{ background: "var(--bg-primary)", border: "1px solid var(--border-subtle)", fontFamily: FONT }}>

      {/* ── HEADER (New Design) ── */}
      <PanelHeader
        title="PULSE 1"
        subtitle="ALGORITHMIC SCALP"
        icon={<Activity size={24} strokeWidth={2.5} />}
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        iconColor="var(--accent-cyan)"
        symbols={SYMBOLS}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        timeframes={["5m", "15m", "1h"]}
        onRefresh={fetchData}
        loading={loading}
        panelId="pulse-panel"
        signalAge={signalAge}
        extraContent={data ? (
          <div>
            <div className="text-[26px] font-bold tracking-tighter leading-none" style={{ color: "var(--text-primary)" }}>
              {data.price.current.toFixed(2)}
            </div>
            <div className="text-[12px] font-medium mt-1 flex items-center gap-1" style={{ color: data.price.change_5 > 0 ? "var(--accent-positive)" : data.price.change_5 < 0 ? "var(--accent-negative)" : "var(--text-muted)" }}>
              {data.price.change_5 > 0 ? "▲" : data.price.change_5 < 0 ? "▼" : ""}
              {Math.abs(data.price.change_5).toFixed(2)}% <span style={{ color: "var(--text-muted)" }}>(5m)</span>
            </div>
          </div>
        ) : undefined}
      />

      {/* ── ERROR DISPLAY ── */}
      {error && !data && !loading && (
        <div className="p-12 text-center flex flex-col items-center justify-center" style={{ background: "var(--bg-primary)" }}>
          <Activity className="w-10 h-10 mb-3 opacity-20" style={{ color: "var(--text-primary)" }} />
          <h3 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Data Unavailable</h3>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>{t("pulse.insufficientData")}</p>
        </div>
      )}

      {/* ── MAIN GRID (3 COLUMNS) ── */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-[1px]" style={{ background: "var(--border-subtle)" }}>

          {/* COLUMN 1: TREND & MACRO (4/12) */}
          <div className="col-span-12 md:col-span-4 p-5 flex flex-col gap-6" style={{ background: "var(--bg-primary)" }}>
            {/* Macro Trend */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>System Trend Bias</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-2xl font-bold tracking-tight" style={{ color: getDirColor(data.trend.direction) }}>
                  {data.trend.label.toUpperCase()}
                </span>
                <span className="text-[13px] font-medium pb-1" style={{ color: getDirColor(data.trend.direction), opacity: 0.8 }}>
                  {data.trend.strength_pct}%
                </span>
              </div>
              <div className="h-[6px] w-full rounded-full overflow-hidden" style={{ background: "var(--bg-input)" }}>
                <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${data.trend.strength_pct}%`, background: getDirColor(data.trend.direction) }} />
              </div>
              <div className="flex items-center justify-between mt-3">
                <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>Last 5 Candles (5m)</span>
                <div className="flex gap-1.5">
                  {data.trend.last_5_candles.map((c, i) => (
                    <div key={i} className="w-2.5 h-2.5 rounded-sm" style={{ background: c === "up" ? "var(--accent-positive)" : c === "down" ? "var(--accent-negative)" : "var(--accent-warning)", opacity: 0.8 }} />
                  ))}
                </div>
              </div>
            </div>

            {/* Momentum Oscillators */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Momentum (5m)</div>
              <div className="space-y-0.5">
                {[
                  { label: "RSI (14)", val: data.momentum.rsi.value.toFixed(1), t: data.momentum.rsi.trend },
                  { label: "MACD", val: data.momentum.macd.value.toFixed(3), t: data.momentum.macd.trend },
                  { label: "Stoch", val: data.momentum.stochastic.value.toFixed(1), t: data.momentum.stochastic.trend },
                ].map((item, i) => (
                  <div key={i} className="flex justify-between items-center py-2 px-3 rounded" style={{ background: "var(--bg-input)" }}>
                    <span className="text-[12px] font-medium" style={{ color: "var(--text-muted)" }}>{item.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[13px] font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>{item.val}</span>
                      <span className="text-[10px]" style={{ color: getDirColor(item.t) }}>{item.t === "up" ? "▲" : "▼"}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* COLUMN 2: LEVELS & VOLUME (4/12) */}
          <div className="col-span-12 md:col-span-4 p-5 flex flex-col gap-6" style={{ background: "var(--bg-primary)" }}>
            {/* Key Price Levels */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Key Price Levels</div>
              <div className="space-y-1">
                {[
                  { lbl: "R2", val: data.levels.r2, type: "res" },
                  { lbl: "R1", val: data.levels.r1, type: "res" },
                  { lbl: "PX", val: data.price.current, type: "curr" },
                  { lbl: "S1", val: data.levels.s1.price, type: "sup", alert: data.levels.s1.alert },
                  { lbl: "S2", val: data.levels.s2, type: "sup" },
                ].map((lvl, i) => (
                  <div key={i} className="flex justify-between items-center py-1.5 px-3 rounded border"
                    style={{
                      background: lvl.type === "curr" ? "var(--bg-input)" : lvl.alert ? "var(--info-bg)" : "transparent",
                      borderColor: lvl.type === "curr" ? "var(--border-default)" : lvl.alert ? "var(--info-border)" : "transparent",
                    }}>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold w-4" style={{ color: lvl.type === "res" ? "var(--accent-negative)" : lvl.type === "sup" ? "var(--accent-positive)" : "var(--text-primary)" }}>{lvl.lbl}</span>
                      {lvl.alert && <span className="text-[10px]" style={{ color: "var(--accent-info)" }}>⚡ Near</span>}
                    </div>
                    <span className={`text-[13px] ${lvl.type === "curr" ? "font-bold" : "font-medium"}`}
                      style={{ color: lvl.type === "curr" ? "var(--text-primary)" : "var(--text-muted)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
                      {lvl.val.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tick Volume */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Tick Volume Profile</div>
              <div className="p-3 rounded border flex justify-between items-center" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                <span className="text-[13px] font-bold" style={{ color: data.volume.status === "high" ? "var(--accent-positive)" : "var(--text-muted)" }}>
                  {data.volume.label.toUpperCase()}
                </span>
                {data.volume.ratio && (
                  <span className="text-[12px] font-medium" style={{ color: "var(--text-primary)" }}>
                    {data.volume.ratio.toFixed(2)}x <span style={{ color: "var(--text-muted)" }}>Avg Vol</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* COLUMN 3: AI SETUP (4/12) */}
          <div className="col-span-12 md:col-span-4 p-5 flex flex-col h-full" style={{ background: "var(--bg-primary)" }}>
            <div className="text-[11px] font-bold uppercase tracking-widest mb-3 flex items-center justify-between" style={{ color: "var(--text-muted)" }}>
              <span>Algorithmic Setup</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: "var(--info-bg)", color: "var(--accent-info)" }}>AI OPTIMIZED</span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* Target */}
              <div className="p-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                <div className="text-[10px] uppercase font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Take Profit (TP)</div>
                <div className="text-[18px] font-bold tracking-tight mb-0.5" style={{ color: "var(--accent-positive)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>{data.suggestion.target.toFixed(1)}</div>
                <div className="text-[11px] font-medium" style={{ color: "var(--text-muted)" }}>+{data.suggestion.target_distance.toFixed(1)} pts</div>
              </div>
              {/* Stop Loss */}
              <div className="p-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                <div className="text-[10px] uppercase font-semibold mb-1" style={{ color: "var(--text-muted)" }}>Stop Loss (SL)</div>
                <div className="text-[18px] font-bold tracking-tight mb-0.5" style={{ color: "var(--accent-negative)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>{data.suggestion.stop.toFixed(1)}</div>
                <div className="text-[11px] font-medium" style={{ color: "var(--text-muted)" }}>-{data.suggestion.stop_distance.toFixed(1)} pts</div>
              </div>
            </div>

            <div className="flex flex-col gap-2 mb-4">
              <div className="flex justify-between items-center py-2 border-b" style={{ borderColor: "var(--border-subtle)" }}>
                <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>Reward / Risk Ratio</span>
                <span className="text-[13px] font-bold" style={{ color: "var(--text-primary)" }}>{data.suggestion.rr_ratio.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b" style={{ borderColor: "var(--border-subtle)" }}>
                <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>Est. Horizon</span>
                <span className="text-[13px] font-bold" style={{ color: "var(--text-primary)" }}>{data.suggestion.timeframe_estimate}</span>
              </div>
            </div>

            {/* AI Log */}
            <div className="mt-auto p-3 rounded border flex-1" style={{ background: "var(--info-bg)", borderColor: "var(--info-border)" }}>
              <div className="text-[10px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "var(--accent-info)" }}>SYSTEM LOG _</div>
              <p className="text-[12px] leading-relaxed" style={{ color: "var(--text-primary)", opacity: 0.85 }}>
                {data.suggestion.text}
              </p>
            </div>

          </div>

        </div>
      )}
    </div>
  );
}
