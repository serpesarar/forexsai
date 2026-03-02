"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { PanelHeaderCompact } from "../PanelHeader";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  ArrowUpIcon as TrendingUp,
  ArrowDownIcon as TrendingDown,
  ActivityIcon as Activity,
  TargetIcon as Target,
  RotateIcon as RefreshCw,
  BrainIcon as Brain,
  ZapIcon as Zap,
  ArrowUpIcon as ArrowUp,
  ArrowDownIcon as ArrowDown,
  ClockIcon as Clock,
  EyeIcon as Eye,
  CheckCircleIcon as CheckCircle,
  AlertIcon as AlertTriangle,
  SecurityShieldIcon as Shield,
  MountainIcon as Mountain,
  TargetIcon as Crosshair,
} from "../ui/CustomIcons";

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
const P = { bg: "var(--bg-primary)", card: "var(--bg-card)", surface: "var(--bg-surface)", border: "var(--border-subtle)", text: "var(--text-primary)", muted: "var(--text-muted)", green: "var(--accent-positive)", red: "var(--accent-negative)", warn: "var(--accent-warning)", accent: "var(--accent-info)", cyan: "var(--accent-info)", gold: "var(--accent-warning)" };

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
  regime?: {
    type: string;
    adx: number;
    session: string;
    is_ath: boolean;
    rsi_mode: string;
    allowed_directions: string[];
    min_rr: number;
  };
  order_blocks?: Array<{
    type: string;
    low: number;
    high: number;
    strength: number;
    is_nearby: boolean;
  }>;
}

interface PulseV3PanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US Oil" },
];

/* ── Institutional Color Palette ── */
const signalNeon: Record<string, { accent: string; glow: string; bg: string }> = {
  CONFIRM: { accent: P.green, glow: "var(--accent-positive-06)", bg: "var(--accent-positive-04)" },
  SCOUT: { accent: P.warn, glow: "var(--accent-warning-06)", bg: "var(--accent-warning-04)" },
  HOLD: { accent: P.accent, glow: "var(--accent-info-06)", bg: "var(--accent-info-04)" },
};

const dirNeon: Record<string, string> = { BUY: P.green, SELL: P.red, NEUTRAL: P.warn };

export default function PulseV3Panel({ symbol: initialSymbol = "NDX.INDX" }: PulseV3PanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<PulseV3Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);


  // WebSocket data — real-time, no polling needed
  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "pulse_v3");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
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
  }, [activeSymbol]);

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
      fetchData();
    }
    if (!wsConnected) {
      const interval = setInterval(fetchData, 60000);
      return () => clearInterval(interval);
    }
  }, [fetchData, wsConnected, wsData]);

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

  const getSignalBadge = (type: string) => {
    if (type === "CONFIRM") return { text: t("pulseV3.strongSignal"), icon: CheckCircle };
    if (type === "SCOUT") return { text: t("pulseV3.watchMode"), icon: Eye };
    return { text: t("pulseV3.wait"), icon: Clock };
  };

  if (loading && !data) {
    return (
      <div className="p-2 animate-pulse bg-transparent">
        <div className="h-10 rounded w-2/3 mb-4" style={{ background: "var(--bg-hover)" }} />
        <div className="h-32 rounded-xl mb-4" style={{ background: "var(--bg-hover)" }} />
        <div className="grid grid-cols-3 gap-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl" style={{ background: "var(--bg-hover)" }} />
          ))}
        </div>
      </div>
    );
  }

  if (error && !data && !loading) {
    return (
      <div className="overflow-hidden bg-transparent">
        <div className="px-2 py-2 flex items-center gap-2.5 bg-transparent">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "var(--accent-warning-20)", boxShadow: "0 0 12px var(--accent-warning-30)" }}>
            <Zap className="w-4 h-4" style={{ color: P.warn }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white/90 font-mono">{t("pulseV3.title")}</h2>
            <p className="text-[10px]" style={{ color: P.muted }}>{t("pulseV3.subtitle")}</p>
          </div>
        </div>
        <div className="p-8 text-center">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-40" style={{ color: P.warn }} />
          <p className="font-medium mb-1 font-mono text-sm" style={{ color: P.warn }}>{activeSymbol}</p>
          <p className="text-sm" style={{ color: P.muted }}>{t("pulse.insufficientData")}</p>
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
    <div className="overflow-hidden bg-transparent shadow-none border-0">

      {/* ── Header (New Design) ── */}
      <PanelHeaderCompact
        title="PULSE 3"
        subtitle="HYBRID SCALP"
        icon={<Zap size={24} strokeWidth={2.5} />}
        iconColor="var(--accent-cyan)"
        onRefresh={fetchData}
        loading={loading}
        panelId="pulse-v3"
      >
        <div className="flex rounded-lg overflow-hidden" style={{ border: "1px solid var(--border-default)" }}>
          {SYMBOLS.map((s) => (
            <button key={s.key} onClick={() => setActiveSymbol(s.key)}
              className="px-3 py-1.5 text-xs font-semibold transition-all"
              style={{
                background: activeSymbol === s.key ? "rgba(255,255,255,0.04)" : "transparent",
                color: activeSymbol === s.key ? "var(--text-primary)" : "var(--text-secondary)",
                borderRight: "1px solid var(--border-subtle)",
                fontWeight: activeSymbol === s.key ? 600 : 500,
                minHeight: "32px",
              }}
            >{s.label}</button>
          ))}
        </div>
      </PanelHeaderCompact>



      {/* ── Main Score + Signal ── */}
      <div className="p-2 text-center bg-transparent">
        {/* Score Circle */}
        <div className="relative inline-flex items-center justify-center w-28 h-28 mb-3">
          <svg className="w-28 h-28 -rotate-90">
            <circle cx="56" cy="56" r="48" fill="none" stroke={P.border} strokeWidth="6" />
            <circle cx="56" cy="56" r="48" fill="none" stroke={scoreStroke} strokeWidth="6"
              strokeDasharray={`${scorePct} 301.6`} strokeLinecap="round" />
          </svg>
          <div className="absolute text-center">
            <span style={{ fontFamily: FONT, fontSize: 28, fontWeight: 700, letterSpacing: "-0.5px", color: nc.accent }}>{data.pulse_score}</span>
            <span style={{ fontFamily: FONT, fontSize: 10, display: "block", color: P.muted }}>/100</span>
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
            <TrendingUp className="w-5 h-5" style={{ color: dc }} />
          ) : data.direction === "SELL" ? (
            <TrendingDown className="w-5 h-5" style={{ color: dc }} />
          ) : (
            <Activity className="w-5 h-5" style={{ color: dc }} />
          )}
          <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: dc }}>
            {data.direction === "BUY" ? t("pulseV3.buy") : data.direction === "SELL" ? t("pulseV3.sell") : t("pulseV3.neutral")}
          </span>
        </div>

        <p className="text-sm font-mono mt-1.5" style={{ color: P.muted }}>
          {t("pulseV3.priceLabel")} <span className="font-bold text-white/80">{data.price}</span>
        </p>

        {/* ── Regime Badge ── */}
        {data.regime && (
          <div className="flex items-center justify-center gap-2 mt-3 flex-wrap">
            {/* Regime Type */}
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold font-mono"
              style={{
                background: data.regime.type.includes("TREND_UP") ? `${P.green}10` :
                  data.regime.type.includes("TREND_DOWN") ? `${P.red}10` :
                    data.regime.type === "RANGING" ? `${P.warn}10` : `${P.accent}10`,
                color: data.regime.type.includes("TREND_UP") ? P.green :
                  data.regime.type.includes("TREND_DOWN") ? P.red :
                    data.regime.type === "RANGING" ? P.warn : P.accent,
                border: `1px solid ${data.regime.type.includes("TREND_UP") ? `${P.green}20` :
                  data.regime.type.includes("TREND_DOWN") ? `${P.red}20` :
                    data.regime.type === "RANGING" ? `${P.warn}20` : `${P.accent}20`}`,
              }}>
              <Shield className="w-3 h-3" />
              {data.regime.type.replace(/_/g, " ")}
            </div>
            {/* ADX */}
            <div className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold"
              style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.08)" }}>
              ADX {data.regime.adx}
            </div>
            {/* Session */}
            <div className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold"
              style={{ background: "var(--accent-info-08)", color: P.accent, border: "1px solid var(--accent-info-15)" }}>
              {data.regime.session}
            </div>
            {/* ATH */}
            {data.regime.is_ath && (
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold"
                style={{ background: "var(--accent-warning-12)", color: P.warn, border: "1px solid var(--accent-warning-25)" }}>
                <Mountain className="w-3 h-3" /> ATH
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── 3 Timeframe Scores ── */}
      <div className="grid grid-cols-3 gap-2.5 p-3">
        {Object.entries(data.timeframes).map(([tf, info]) => {
          const trendC = info.trend === "up" ? P.green : info.trend === "down" ? P.red : P.warn;
          return (
            <div key={tf} className="rounded-xl p-3 text-center" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
              <div className="text-[10px] uppercase tracking-widest font-mono mb-1.5" style={{ color: P.muted }}>{tf}</div>
              <div className="flex items-center justify-center gap-1 mb-1">
                {info.trend === "up" ? <ArrowUp className="w-3.5 h-3.5" style={{ color: trendC }} /> :
                  info.trend === "down" ? <ArrowDown className="w-3.5 h-3.5" style={{ color: trendC }} /> :
                    <Activity className="w-3.5 h-3.5" style={{ color: trendC }} />}
                <span className="text-lg font-bold font-mono text-white/90">{info.raw_score}</span>
                <span className="text-[10px] font-mono" style={{ color: P.muted }}>/{info.max}</span>
              </div>
              <div className="text-[10px] font-mono" style={{ color: trendC }}>
                {info.trend === "up" ? t("pulseV3.up") : info.trend === "down" ? t("pulseV3.down") : t("pulseV3.neutral")}
              </div>
              <div className="rounded-full mt-2 overflow-hidden" style={{ height: 4, background: P.border }}>
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(info.raw_score / info.max) * 100}%`, background: trendC, opacity: 0.85 }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Levels + R/R ── */}
      <div className="grid grid-cols-2 gap-2.5 px-3 pb-3">
        <div className="rounded-xl p-3" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
          <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2.5 flex items-center gap-1.5" style={{ color: P.muted }}>
            <Target className="w-3 h-3" style={{ color: P.accent }} /> {t("pulseV3.levels")}
          </h3>
          <div className="space-y-1.5 text-sm font-mono">
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: `${P.red}06` }}>
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.red }}>R2</span>
              <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.r2.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: `${P.red}06` }}>
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.red }}>R1</span>
              <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.r1.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: `${P.green}08`, border: `1px solid ${P.green}20` }}>
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.green }}>Pivot</span>
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.green }}>{data.levels.pivot.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: `${P.accent}06` }}>
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.accent }}>S1</span>
              <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.s1.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-0.5 rounded-lg" style={{ background: `${P.accent}06` }}>
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.accent }}>S2</span>
              <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>{data.levels.s2.toFixed(0)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl p-3" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
          <h3 className="text-[10px] uppercase tracking-widest font-mono mb-2.5 flex items-center gap-1.5" style={{ color: P.muted }}>
            <Brain className="w-3 h-3" style={{ color: P.accent }} /> {t("pulseV3.targetStop")}
          </h3>
          <div className="space-y-1.5 text-sm font-mono">
            <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "var(--accent-positive-06)" }}>
              <span style={{ color: P.green }}>{t("pulseV3.target")}</span>
              <span className="font-bold" style={{ color: P.green }}>{data.levels.target.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-1 rounded-lg" style={{ background: "var(--accent-negative-06)" }}>
              <span style={{ color: P.red }}>{t("pulseV3.stop")}</span>
              <span className="font-bold" style={{ color: P.red }}>{data.levels.stop.toFixed(0)}</span>
            </div>
            <div className="flex justify-between px-2 py-1.5 rounded-lg" style={{
              background: data.rr_ratio >= 1.5 ? "var(--accent-positive-06)" : data.rr_ratio >= 1.2 ? "var(--accent-warning-06)" : "var(--accent-negative-06)",
              border: `1px solid ${data.rr_ratio >= 1.5 ? "var(--accent-positive-15)" : data.rr_ratio >= 1.2 ? "var(--accent-warning-15)" : "var(--accent-negative-15)"}`,
            }}>
              <span style={{ color: P.muted }}>R/R</span>
              <span className="font-bold" style={{ color: data.rr_ratio >= 1.5 ? P.green : data.rr_ratio >= 1.2 ? P.warn : P.red }}>{data.rr_ratio.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── AI Suggestion ── */}
      <div className="px-3 pb-3">
        <div className="rounded-xl p-3.5" style={{ background: `${P.accent}05`, border: `1px solid ${P.accent}12` }}>
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4" style={{ color: P.accent }} />
            <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.accent }}>{t("pulseV3.analysis")}</span>
          </div>
          <p style={{ fontFamily: FONT, fontSize: 12, lineHeight: 1.6, color: P.text }}>{data.suggestion}</p>
        </div>
      </div>

      {/* ── Entry Zones ── */}
      {data.entry_zones && data.entry_zones.length > 0 && (
        <div className="px-3 pb-3">
          <h4 className="text-[10px] uppercase tracking-widest font-mono mb-2 px-1" style={{ color: P.muted }}>{t("pulseV3.entryZones")}</h4>
          <div className="grid grid-cols-3 gap-2">
            {data.entry_zones.map((zone, idx) => (
              <div key={idx} className="rounded-xl p-2.5 text-center font-mono" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                <p className="text-[9px]" style={{ color: P.muted }}>{zone.label}</p>
                <p className="text-sm font-bold text-white/80">{zone.price}</p>
                <p className="text-[10px]" style={{ color: P.accent }}>%{zone.share}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Order Blocks ── */}
      {data.order_blocks && data.order_blocks.length > 0 && (
        <div className="px-3 pb-3">
          <h4 className="text-[10px] uppercase tracking-widest font-mono mb-2 px-1 flex items-center gap-1.5" style={{ color: P.muted }}>
            <Crosshair className="w-3 h-3" style={{ color: P.accent }} /> Order Blocks (4H)
          </h4>
          <div className="flex gap-2 flex-wrap">
            {data.order_blocks.filter(ob => ob.is_nearby).map((ob, idx) => (
              <div key={idx} className="rounded-lg px-3 py-1.5 font-mono text-[10px]" style={{
                background: ob.type === "bullish" ? `${P.green}06` : `${P.red}06`,
                border: `1px solid ${ob.type === "bullish" ? `${P.green}15` : `${P.red}15`}`,
                color: ob.type === "bullish" ? P.green : P.red,
              }}>
                <span className="font-bold">{ob.type === "bullish" ? "▲" : "▼"} {ob.low.toFixed(0)}–{ob.high.toFixed(0)}</span>
                <span className="ml-2 opacity-60">str: {(ob.strength * 100).toFixed(0)}%</span>
              </div>
            ))}
            {data.order_blocks.filter(ob => ob.is_nearby).length === 0 && (
              <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.2)" }}>No nearby OBs</span>
            )}
          </div>
        </div>
      )}

      {/* ── Notes ── */}
      {data.notes && data.notes.length > 0 && (
        <div className="px-3 pb-3 space-y-1">
          {data.notes.map((note, i) => (
            <div key={i} className="flex items-center gap-1.5 text-[10px] font-mono" style={{ color: P.warn }}>
              <AlertTriangle className="w-3 h-3 shrink-0" /> {note}
            </div>
          ))}
        </div>
      )}

      {/* ── Footer ── */}
      <div className="px-2 py-2 text-center bg-transparent">
        <p className="text-[10px] font-mono" style={{ color: P.muted }}>
          {lastUpdate ? `${t("pulseV3.lastUpdate")} ${lastUpdate.toLocaleTimeString()}` : t("pulseV3.updating")}{" "}
          | {t("pulseV3.validity")} {(data.valid_for_seconds / 60).toFixed(0)} {t("pulseV3.min")}
        </p>
      </div>
    </div>
  );
}
