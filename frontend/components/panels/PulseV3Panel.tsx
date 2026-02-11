"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { useWSPanelData } from "../../contexts/WebSocketContext";
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

/* ── Neon helpers ── */
const signalNeon: Record<string, { accent: string; glow: string; bg: string }> = {
  CONFIRM: { accent: "#00ff88", glow: "rgba(0,255,136,0.15)", bg: "rgba(0,255,136,0.06)" },
  SCOUT:   { accent: "#f0b429", glow: "rgba(240,180,41,0.15)", bg: "rgba(240,180,41,0.06)" },
  HOLD:    { accent: "#818cf8", glow: "rgba(129,140,248,0.15)", bg: "rgba(129,140,248,0.06)" },
};

const dirNeon: Record<string, string> = { BUY: "#00ff88", SELL: "#ff3366", NEUTRAL: "#f0b429" };

export default function PulseV3Panel({ symbol: initialSymbol = "NDX.INDX" }: PulseV3PanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<PulseV3Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // WebSocket data — real-time, no polling needed
  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "pulse_v3");

  const fetchData = async () => {
    try {
      setError(null);
      const res = await fetch(`${API_BASE}/api/panel/pulse-v3/${activeSymbol}`);
      const json = await res.json();
      if (json.error) {
        setError(json.error);
        setData(null);
      } else {
        setData(json);
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error("PULSE V3 fetch error:", e);
      setError("fetch_error");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  // Use WS data when available
  useEffect(() => {
    if (wsData) {
      setData(wsData);
      setLastUpdate(new Date());
      setLoading(false);
      setError(null);
    }
  }, [wsData]);

  // HTTP fetch on mount + polling only when WS is NOT connected
  useEffect(() => {
    if (!wsData) {
      setLoading(true);
      fetchData();
    }
    if (!wsConnected) {
      const interval = setInterval(fetchData, 60000);
      return () => clearInterval(interval);
    }
  }, [activeSymbol, wsConnected]);

  // Listen for global refresh event from header button
  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("pulse-refresh", handler);
    return () => window.removeEventListener("pulse-refresh", handler);
  }, [activeSymbol]);

  const getSignalBadge = (type: string) => {
    if (type === "CONFIRM") return { text: t("pulseV3.strongSignal"), icon: CheckCircle };
    if (type === "SCOUT") return { text: t("pulseV3.watchMode"), icon: Eye };
    return { text: t("pulseV3.wait"), icon: Clock };
  };

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="h-10 rounded w-2/3 mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="h-32 rounded-xl mb-4" style={{ background: "rgba(255,255,255,0.04)" }} />
        <div className="grid grid-cols-3 gap-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
      </div>
    );
  }

  if (error && !data && !loading) {
    return (
      <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="px-4 py-3 flex items-center gap-2.5" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "rgba(240,180,41,0.2)", boxShadow: "0 0 12px rgba(240,180,41,0.3)" }}>
            <Zap className="w-4 h-4" style={{ color: "#f0b429" }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">{t("pulseV3.title")}</h2>
            <p className="text-[10px]" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulseV3.subtitle")}</p>
          </div>
        </div>
        <div className="p-8 text-center">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-40" style={{ color: "#f0b429" }} />
          <p className="font-medium mb-1 font-mono text-sm" style={{ color: "#f0b429" }}>{activeSymbol}</p>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulse.insufficientData")}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const nc = signalNeon[data.signal_type] || signalNeon.HOLD;
  const dc = dirNeon[data.direction] || dirNeon.NEUTRAL;
  const badge = getSignalBadge(data.signal_type);
  const BadgeIcon = badge.icon;

  const scoreStroke = nc.accent;
  const scorePct = (data.pulse_score / 100) * 301.6;

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: `0 0 40px ${nc.glow}, inset 0 1px 0 rgba(255,255,255,0.04)` }}>

      {/* ── Header ── */}
      <div className="px-4 py-3 flex items-center justify-between flex-wrap gap-2" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: `${nc.accent}20`, boxShadow: `0 0 12px ${nc.accent}40` }}>
            <Zap className="w-4 h-4" style={{ color: nc.accent }} />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-bold text-white/90 truncate font-mono">{t("pulseV3.title")}</h2>
            <p className="text-[10px] truncate" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulseV3.subtitle")}</p>
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
          <button onClick={fetchData} className="p-1.5 rounded-lg transition-all hover:brightness-150" style={{ background: "rgba(255,255,255,0.05)" }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: "rgba(255,255,255,0.35)" }} />
          </button>
        </div>
      </div>

      {/* ── Main Score + Signal ── */}
      <div className="p-6 text-center" style={{ background: nc.bg }}>
        {/* Score Circle */}
        <div className="relative inline-flex items-center justify-center w-28 h-28 mb-3">
          <svg className="w-28 h-28 -rotate-90">
            <circle cx="56" cy="56" r="48" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
            <circle cx="56" cy="56" r="48" fill="none" stroke={scoreStroke} strokeWidth="8"
              strokeDasharray={`${scorePct} 301.6`} strokeLinecap="round"
              style={{ filter: `drop-shadow(0 0 8px ${nc.accent}60)` }} />
          </svg>
          <div className="absolute text-center">
            <span className="text-2xl font-bold font-mono" style={{ color: nc.accent, textShadow: `0 0 12px ${nc.glow}` }}>{data.pulse_score}</span>
            <span className="text-[10px] font-mono block" style={{ color: "rgba(255,255,255,0.25)" }}>/100</span>
          </div>
        </div>

        {/* Signal Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold font-mono"
          style={{ background: `${nc.accent}20`, color: nc.accent, border: `1px solid ${nc.accent}40`, boxShadow: `0 0 16px ${nc.accent}30` }}>
          <BadgeIcon className="w-3.5 h-3.5" />
          {badge.text}
        </div>

        {/* Direction */}
        <div className="mt-3 flex items-center justify-center gap-2">
          {data.direction === "BUY" ? (
            <TrendingUp className="w-5 h-5" style={{ color: dc, filter: `drop-shadow(0 0 6px ${dc})` }} />
          ) : data.direction === "SELL" ? (
            <TrendingDown className="w-5 h-5" style={{ color: dc, filter: `drop-shadow(0 0 6px ${dc})` }} />
          ) : (
            <Activity className="w-5 h-5" style={{ color: dc, filter: `drop-shadow(0 0 6px ${dc})` }} />
          )}
          <span className="text-lg font-bold font-mono" style={{ color: dc, textShadow: `0 0 12px ${dc}40` }}>
            {data.direction === "BUY" ? t("pulseV3.buy") : data.direction === "SELL" ? t("pulseV3.sell") : t("pulseV3.neutral")}
          </span>
        </div>

        <p className="text-sm font-mono mt-1.5" style={{ color: "rgba(255,255,255,0.35)" }}>
          {t("pulseV3.priceLabel")} <span className="font-bold text-white/80">{data.price}</span>
        </p>
      </div>

      {/* ── 3 Timeframe Scores ── */}
      <div className="grid grid-cols-3 gap-2.5 p-3">
        {Object.entries(data.timeframes).map(([tf, info]) => {
          const trendC = info.trend === "up" ? "#00ff88" : info.trend === "down" ? "#ff3366" : "#f0b429";
          return (
            <div key={tf} className="rounded-xl p-3 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div className="text-[10px] uppercase tracking-widest font-mono mb-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>{tf}</div>
              <div className="flex items-center justify-center gap-1 mb-1">
                {info.trend === "up" ? <ArrowUp className="w-3.5 h-3.5" style={{ color: trendC }} /> :
                  info.trend === "down" ? <ArrowDown className="w-3.5 h-3.5" style={{ color: trendC }} /> :
                  <Activity className="w-3.5 h-3.5" style={{ color: trendC }} />}
                <span className="text-lg font-bold font-mono text-white/90">{info.raw_score}</span>
                <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.25)" }}>/{info.max}</span>
              </div>
              <div className="text-[10px] font-mono" style={{ color: trendC }}>
                {info.trend === "up" ? t("pulseV3.up") : info.trend === "down" ? t("pulseV3.down") : t("pulseV3.neutral")}
              </div>
              <div className="h-1.5 rounded-full mt-2 overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(info.raw_score / info.max) * 100}%`, background: `linear-gradient(90deg, ${trendC}80, ${trendC})`, boxShadow: `0 0 8px ${trendC}50` }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Levels + R/R ── */}
      <div className="grid grid-cols-2 gap-2.5 px-3 pb-3">
        <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
          <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2.5 flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
            <Target className="w-3 h-3" style={{ color: "#00ccff" }} /> {t("pulseV3.levels")}
          </h3>
          <div className="space-y-1.5 text-sm font-mono">
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: "rgba(255,51,102,0.06)" }}>
              <span style={{ color: "#ff3366" }}>R2</span>
              <span className="text-white/80">{data.levels.r2.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: "rgba(255,51,102,0.06)" }}>
              <span style={{ color: "#ff3366" }}>R1</span>
              <span className="text-white/80">{data.levels.r1.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.15)" }}>
              <span style={{ color: "#00ff88" }}>Pivot</span>
              <span className="font-bold" style={{ color: "#00ff88" }}>{data.levels.pivot.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: "rgba(0,204,255,0.06)" }}>
              <span style={{ color: "#00ccff" }}>S1</span>
              <span className="text-white/80">{data.levels.s1.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: "rgba(0,204,255,0.06)" }}>
              <span style={{ color: "#00ccff" }}>S2</span>
              <span className="text-white/80">{data.levels.s2.toFixed(0)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
          <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2.5 flex items-center gap-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>
            <Brain className="w-3 h-3" style={{ color: "#818cf8" }} /> {t("pulseV3.targetStop")}
          </h3>
          <div className="space-y-1.5 text-sm font-mono">
            <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(0,255,136,0.06)" }}>
              <span style={{ color: "#00ff88" }}>{t("pulseV3.target")}</span>
              <span className="font-bold" style={{ color: "#00ff88" }}>{data.levels.target.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "rgba(255,51,102,0.06)" }}>
              <span style={{ color: "#ff3366" }}>{t("pulseV3.stop")}</span>
              <span className="font-bold" style={{ color: "#ff3366" }}>{data.levels.stop.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-1.5 rounded-lg" style={{
              background: data.rr_ratio >= 1.5 ? "rgba(0,255,136,0.06)" : data.rr_ratio >= 1.2 ? "rgba(240,180,41,0.06)" : "rgba(255,51,102,0.06)",
              border: `1px solid ${data.rr_ratio >= 1.5 ? "rgba(0,255,136,0.15)" : data.rr_ratio >= 1.2 ? "rgba(240,180,41,0.15)" : "rgba(255,51,102,0.15)"}`,
            }}>
              <span style={{ color: "rgba(255,255,255,0.4)" }}>R/R</span>
              <span className="font-bold" style={{ color: data.rr_ratio >= 1.5 ? "#00ff88" : data.rr_ratio >= 1.2 ? "#f0b429" : "#ff3366" }}>{data.rr_ratio.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── AI Suggestion ── */}
      <div className="px-3 pb-3">
        <div className="rounded-xl p-3.5" style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.12)", boxShadow: "0 0 20px rgba(99,102,241,0.05)" }}>
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4" style={{ color: "#818cf8" }} />
            <span className="font-mono font-bold text-sm" style={{ color: "#818cf8" }}>{t("pulseV3.analysis")}</span>
          </div>
          <p className="text-sm font-mono leading-relaxed" style={{ color: "rgba(255,255,255,0.55)" }}>{data.suggestion}</p>
        </div>
      </div>

      {/* ── Entry Zones ── */}
      {data.entry_zones && data.entry_zones.length > 0 && (
        <div className="px-3 pb-3">
          <h4 className="text-[10px] uppercase tracking-widest font-mono mb-2 px-1" style={{ color: "rgba(255,255,255,0.3)" }}>{t("pulseV3.entryZones")}</h4>
          <div className="grid grid-cols-3 gap-2">
            {data.entry_zones.map((zone, idx) => (
              <div key={idx} className="rounded-xl p-2.5 text-center font-mono" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <p className="text-[9px]" style={{ color: "rgba(255,255,255,0.3)" }}>{zone.label}</p>
                <p className="text-sm font-bold text-white/80">{zone.price}</p>
                <p className="text-[10px]" style={{ color: "#00ccff" }}>%{zone.share}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Notes ── */}
      {data.notes && data.notes.length > 0 && (
        <div className="px-3 pb-3 space-y-1">
          {data.notes.map((note, i) => (
            <div key={i} className="flex items-center gap-1.5 text-[10px] font-mono" style={{ color: "#f0b429" }}>
              <AlertTriangle className="w-3 h-3 shrink-0" /> {note}
            </div>
          ))}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="px-4 py-2 text-center" style={{ background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <p className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>
          {lastUpdate ? `${t("pulseV3.lastUpdate")} ${lastUpdate.toLocaleTimeString()}` : t("pulseV3.updating")}{" "}
          | {t("pulseV3.validity")} {(data.valid_for_seconds / 60).toFixed(0)} {t("pulseV3.min")}
        </p>
      </div>
    </div>
  );
}
