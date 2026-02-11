"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  RefreshCw,
  Zap,
  ArrowUp,
  ArrowDown,
  Clock,
  Eye,
  CheckCircle,
  AlertTriangle,
  BarChart3,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface ScoreBreakdown {
  ml: { pts: number; confidence: number; direction: string };
  ema: { pts: number; status: string; ema20: number; ema50: number };
  macd: { pts: number; hist: number };
  rsi: { pts: number; value: number };
  volume: { pts: number };
}

interface PulseMLData {
  symbol: string;
  timeframe: string;
  timestamp: string;
  signal: "BUY" | "SELL" | "HOLD";
  signal_type: "CONFIRM" | "SCOUT" | "HOLD";
  pulse_score: number;
  confidence: number;
  model_type: string;
  price: number;
  target: number;
  stop: number;
  rr_ratio: number;
  score_breakdown: ScoreBreakdown;
  details: {
    ml_direction: string;
    ema_20: number;
    ema_50: number;
    rsi_14: number;
    macd_hist: number;
    notes: string[];
  };
  suggestion: string;
}

interface PulseMLPanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
];

const TIMEFRAMES = ["5m", "15m", "30m", "1H", "4H"];

const signalStyles: Record<string, { accent: string; glow: string; bg: string }> = {
  CONFIRM: { accent: "#00ff88", glow: "rgba(0,255,136,0.15)", bg: "rgba(0,255,136,0.06)" },
  SCOUT:   { accent: "#f0b429", glow: "rgba(240,180,41,0.15)", bg: "rgba(240,180,41,0.06)" },
  HOLD:    { accent: "#818cf8", glow: "rgba(129,140,248,0.15)", bg: "rgba(129,140,248,0.06)" },
};

const dirColor: Record<string, string> = { BUY: "#00ff88", SELL: "#ff3366", HOLD: "#818cf8", NEUTRAL: "#f0b429" };

export default function PulseMLPanel({ symbol: initialSymbol = "NDX.INDX" }: PulseMLPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState("15m");
  const [data, setData] = useState<PulseMLData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch(`${API_BASE}/api/panel/pulse-ml/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (json.error) {
        setError(json.error);
        setData(null);
      } else {
        setData(json);
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error("PULSE ML fetch error:", e);
      setError("fetch_error");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [activeSymbol, timeframe]);

  useEffect(() => {
    setLoading(true);
    fetchData();
    const interval = setInterval(fetchData, 120000);
    return () => clearInterval(interval);
  }, [activeSymbol, timeframe]);

  // Listen for global refresh event from header button
  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("pulse-refresh", handler);
    return () => window.removeEventListener("pulse-refresh", handler);
  }, [fetchData]);

  const st = signalStyles[data?.signal_type || "HOLD"] || signalStyles.HOLD;

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-8 rounded w-2/3 mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="h-24 rounded-xl mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 rounded-lg" style={{ background: "rgba(255,255,255,0.04)" }} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl p-6" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5" style={{ color: "#a78bfa" }} />
            <span className="text-sm font-bold tracking-wider" style={{ color: "#a78bfa" }}>PULSE 2 — ML HYBRID</span>
          </div>
          <button onClick={() => { setLoading(true); fetchData(); }} className="p-1.5 rounded-lg hover:bg-white/10 transition">
            <RefreshCw className="w-4 h-4 text-white/40" />
          </button>
        </div>
        <div className="flex items-center gap-2 text-amber-400 text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  const bd = data?.score_breakdown;
  const maxScore = 100;
  const scorePct = ((data?.pulse_score || 0) / maxScore) * 100;

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: `1px solid ${st.accent}20` }}>
      {/* Header */}
      <div className="px-5 pt-4 pb-3 flex items-center justify-between" style={{ background: st.bg }}>
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5" style={{ color: st.accent }} />
          <span className="text-sm font-bold tracking-wider" style={{ color: st.accent }}>PULSE 2 — ML HYBRID</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { setLoading(true); fetchData(); }} className="p-1.5 rounded-lg hover:bg-white/10 transition">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} style={{ color: "rgba(255,255,255,0.4)" }} />
          </button>
        </div>
      </div>

      <div className="px-5 pb-5">
        {/* Symbol + Timeframe Tabs */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex gap-1">
            {SYMBOLS.map(s => (
              <button key={s.key} onClick={() => setActiveSymbol(s.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${activeSymbol === s.key ? "text-white" : "text-white/30 hover:text-white/60"}`}
                style={activeSymbol === s.key ? { background: st.accent + "20", color: st.accent } : {}}>
                {s.label}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            {TIMEFRAMES.map(tf => (
              <button key={tf} onClick={() => setTimeframe(tf)}
                className={`px-2 py-1 rounded text-[10px] font-bold transition-all ${timeframe === tf ? "text-white bg-white/10" : "text-white/30 hover:text-white/50"}`}>
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Main Signal Area */}
        {data && (
          <>
            <div className="mt-4 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-3xl font-black" style={{ color: dirColor[data.signal] || "#fff" }}>
                    {data.signal}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold" style={{ background: st.accent + "20", color: st.accent }}>
                    {data.signal_type}
                  </span>
                </div>
                <div className="text-white/40 text-xs mt-1">
                  Score: {data.pulse_score}/{maxScore} • Conf: {data.confidence.toFixed(1)}%
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-mono font-bold text-white">
                  ${data.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
                <div className="text-[10px] text-white/40 mt-1">
                  {lastUpdate ? lastUpdate.toLocaleTimeString() : "—"}
                </div>
              </div>
            </div>

            {/* Score Bar */}
            <div className="mt-3 h-2 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${scorePct}%`, background: `linear-gradient(90deg, ${st.accent}40, ${st.accent})` }} />
            </div>

            {/* Score Breakdown */}
            {bd && (
              <div className="mt-4 grid grid-cols-5 gap-2">
                {[
                  { label: "ML", pts: bd.ml.pts, max: 35, detail: bd.ml.direction, icon: Brain },
                  { label: "EMA", pts: bd.ema.pts, max: 25, detail: bd.ema.status, icon: TrendingUp },
                  { label: "MACD", pts: bd.macd.pts, max: 15, detail: bd.macd.hist.toFixed(3), icon: BarChart3 },
                  { label: "RSI", pts: bd.rsi.pts, max: 15, detail: bd.rsi.value.toFixed(1), icon: Activity },
                  { label: "VOL", pts: bd.volume.pts, max: 10, detail: `${bd.volume.pts}p`, icon: Zap },
                ].map(item => {
                  const Icon = item.icon;
                  const pct = (item.pts / item.max) * 100;
                  return (
                    <div key={item.label} className="text-center rounded-xl p-2" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <Icon className="w-3.5 h-3.5 mx-auto mb-1" style={{ color: st.accent }} />
                      <div className="text-[10px] font-bold text-white/60">{item.label}</div>
                      <div className="text-xs font-mono font-bold text-white mt-0.5">{item.pts}</div>
                      <div className="mt-1 h-1 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${Math.min(100, pct)}%`, background: st.accent }} />
                      </div>
                      <div className="text-[9px] text-white/30 mt-0.5 truncate">{item.detail}</div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Target / Stop / R:R */}
            <div className="mt-4 grid grid-cols-3 gap-2">
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.1)" }}>
                <Target className="w-3.5 h-3.5 mx-auto mb-1 text-green-400" />
                <div className="text-[10px] text-white/40">TARGET</div>
                <div className="text-sm font-mono font-bold text-green-400">${data.target.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(255,51,102,0.04)", border: "1px solid rgba(255,51,102,0.1)" }}>
                <AlertTriangle className="w-3.5 h-3.5 mx-auto mb-1 text-red-400" />
                <div className="text-[10px] text-white/40">STOP</div>
                <div className="text-sm font-mono font-bold text-red-400">${data.stop.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ background: "rgba(129,140,248,0.04)", border: "1px solid rgba(129,140,248,0.1)" }}>
                <Zap className="w-3.5 h-3.5 mx-auto mb-1 text-indigo-400" />
                <div className="text-[10px] text-white/40">R:R</div>
                <div className="text-sm font-mono font-bold text-indigo-400">{data.rr_ratio}x</div>
              </div>
            </div>

            {/* Suggestion */}
            <div className="mt-3 px-3 py-2 rounded-xl text-xs text-white/60" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)" }}>
              {data.suggestion}
            </div>

            {/* Notes */}
            {data.details.notes && data.details.notes.length > 0 && (
              <div className="mt-2 space-y-1">
                {data.details.notes.slice(0, 3).map((note, i) => (
                  <div key={i} className="text-[10px] text-white/30">• {note}</div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
