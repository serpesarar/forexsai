"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { PanelHeader } from "../PanelHeader";
import {
  ArrowUpIcon as TrendingUp,
  ArrowDownIcon as TrendingDown,
  ActivityIcon as Activity,
  TargetIcon as Target,
  ZapIcon as Zap,
  ArrowUpIcon as ArrowUp,
  ArrowDownIcon as ArrowDown,
  ClockIcon as Clock,
  EyeIcon as Eye,
  CheckCircleIcon as CheckCircle,
  AlertIcon as AlertTriangle,
  ChartsIcon as BarChart3,
  SecurityShieldIcon as Shield,
  MountainIcon as Mountain,
} from "../ui/CustomIcons";
import { Brain } from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

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
  regime?: {
    type: string;
    adx: number;
    session: string;
    is_ath: boolean;
    rsi_mode: string;
    allowed_directions: string[];
    min_rr: number;
    ml_confidence_floor?: { scout: number; confirm: number };
  };
}

interface PulseMLPanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US Oil" },
];

const TIMEFRAMES = ["5m", "15m", "30m", "1H", "4H"];

const signalStyles: Record<string, { accent: string; glow: string; bg: string }> = {
  CONFIRM: { accent: "var(--accent-positive)", glow: "rgba(22,199,132,0.06)", bg: "var(--success-bg)" },
  SCOUT: { accent: "var(--accent-warning)", glow: "rgba(245,166,35,0.06)", bg: "var(--warning-bg)" },
  HOLD: { accent: "var(--accent-info)", glow: "rgba(79,140,255,0.06)", bg: "var(--info-bg)" },
};

const dirColor: Record<string, string> = { BUY: "var(--accent-positive)", SELL: "var(--accent-negative)", HOLD: "var(--accent-info)", NEUTRAL: "var(--accent-warning)" };

export default function PulseMLPanel({ symbol: initialSymbol = "NDX.INDX" }: PulseMLPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState("15m");
  const [data, setData] = useState<PulseMLData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [signalAge, setSignalAge] = useState<string>("");
  const [signalTimestamp, setSignalTimestamp] = useState<Date | null>(null);


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
        if (json.signal_timestamp) {
          setSignalTimestamp(new Date(json.signal_timestamp));
        } else {
          setSignalTimestamp(new Date());
        }
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

  const st = signalStyles[data?.signal_type || "HOLD"] || signalStyles.HOLD;

  const getDirColor = (dir: string) => {
    if (dir === "BUY" || dir === "up" || dir === "UP") return "var(--accent-positive)";
    if (dir === "SELL" || dir === "down" || dir === "DOWN") return "var(--accent-negative)";
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

  if (error) {
    return (
      <div className="rounded-xl p-12 text-center flex flex-col items-center justify-center font-['Inter']" style={{ background: "var(--bg-primary)", border: "1px solid var(--border-subtle)" }}>
        <Activity className="w-10 h-10 mb-3 opacity-20" style={{ color: "var(--text-primary)" }} />
        <h3 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Data Unavailable</h3>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>{error}</p>
        <button onClick={() => { setLoading(true); fetchData(); }} className="mt-4 px-3 py-1.5 rounded bg-white/5 text-xs text-white/50 hover:bg-white/10 transition-colors">
          Retry Connection
        </button>
      </div>
    );
  }

  const bd = data?.score_breakdown;
  const maxScore = 100;
  const scorePct = ((data?.pulse_score || 0) / maxScore) * 100;

  return (
    <div className="flex flex-col rounded-xl overflow-hidden" style={{ background: "var(--bg-primary)", border: "1px solid var(--border-subtle)", fontFamily: FONT }}>

      {/* ── HEADER (New Design) ── */}
      <PanelHeader
        title="PULSE 2"
        subtitle="ML HYBRID"
        icon={<Brain size={24} strokeWidth={2.5} />}
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        iconColor="var(--accent-cyan)"
        symbols={SYMBOLS}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        timeframes={TIMEFRAMES}
        onRefresh={() => { setLoading(true); fetchData(); }}
        loading={loading}
        panelId="pulse-ml"
        signalAge={signalAge}
        extraContent={data ? (
          <div>
            <div className="text-[26px] font-bold tracking-tighter leading-none" style={{ color: "var(--text-primary)" }}>
              {data.price.toFixed(2)}
            </div>
          </div>
        ) : undefined}
      />

      {/* ── MAIN GRID (3 COLUMNS) ── */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-[1px]" style={{ background: "var(--border-subtle)" }}>

          {/* COLUMN 1: ML OUTPUT & REGIME (4/12) */}
          <div className="col-span-12 md:col-span-4 p-5 flex flex-col gap-6" style={{ background: "var(--bg-primary)" }}>
            {/* Model Output */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>ML Model Prediction</div>
              <div className="flex items-end gap-3 mb-2">
                <span className="text-2xl font-bold tracking-tight" style={{ color: getDirColor(data.signal) }}>
                  {data.signal}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded uppercase font-bold tracking-wider mb-1"
                  style={{
                    background: data.signal_type === "CONFIRM" ? "var(--success-bg)" : data.signal_type === "SCOUT" ? "var(--warning-bg)" : "var(--info-bg)",
                    color: data.signal_type === "CONFIRM" ? "var(--accent-positive)" : data.signal_type === "SCOUT" ? "var(--accent-warning)" : "var(--accent-info)",
                  }}>
                  {data.signal_type}
                </span>
              </div>
              <div className="h-[6px] w-full rounded-full overflow-hidden mt-3" style={{ background: "var(--bg-input)" }}>
                <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${scorePct}%`, background: getDirColor(data.signal) }} />
              </div>
              <div className="flex items-center justify-between mt-2 font-mono text-[10px]">
                <span style={{ color: "var(--text-muted)" }}>Score: {data.pulse_score}/{maxScore}</span>
                <span style={{ color: "var(--text-secondary)" }}>Conf: {data.confidence.toFixed(1)}%</span>
              </div>
            </div>

            {/* Market Regime */}
            {data.regime && (
              <div>
                <div className="text-[11px] font-bold uppercase tracking-widest mb-3 flex items-center justify-between" style={{ color: "var(--text-muted)" }}>
                  <span>Market Regime</span>
                  {data.regime.is_ath && <span className="flex items-center gap-1 text-[9px] text-[var(--accent-warning)] border border-[var(--accent-warning)] px-1 rounded bg-[var(--warning-bg)]"><Mountain size={10} /> ATH</span>}
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between items-center py-1.5 px-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                    <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>Classification</span>
                    <span className="text-[12px] font-bold" style={{ color: data.regime.type.includes("UP") ? "var(--accent-positive)" : data.regime.type.includes("DOWN") ? "var(--accent-negative)" : "var(--accent-info)" }}>
                      {data.regime.type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-1.5 px-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                    <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>ADX Strength</span>
                    <span className="text-[12px] font-semibold text-white/80 font-mono">{data.regime.adx}</span>
                  </div>
                  <div className="flex justify-between items-center py-1.5 px-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                    <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>Session</span>
                    <span className="text-[12px] font-semibold text-white/80">{data.regime.session}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* COLUMN 2: COMPONENT SCORES (4/12) */}
          <div className="col-span-12 md:col-span-4 p-5 flex flex-col gap-6" style={{ background: "var(--bg-primary)" }}>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-3 flex justify-between" style={{ color: "var(--text-muted)" }}>
                <span>Model Components</span>
                <span>MAX 100</span>
              </div>
              {bd && (
                <div className="space-y-1">
                  {[
                    { label: "ML Engine", pts: bd.ml.pts, max: 35, detail: bd.ml.direction },
                    { label: "EMA Cross", pts: bd.ema.pts, max: 25, detail: bd.ema.status },
                    { label: "MACD Hist", pts: bd.macd.pts, max: 15, detail: bd.macd.hist.toFixed(3) },
                    { label: "RSI Flow", pts: bd.rsi.pts, max: 15, detail: bd.rsi.value.toFixed(1) },
                    { label: "Volume Profile", pts: bd.volume.pts, max: 10, detail: `${bd.volume.pts}pts` },
                  ].map((comp, i) => (
                    <div key={i} className="flex justify-between items-center py-2 px-3 rounded" style={{ background: "var(--bg-input)" }}>
                      <div className="flex flex-col">
                        <span className="text-[12px] font-medium" style={{ color: "var(--text-muted)" }}>{comp.label}</span>
                        <span className="text-[9px]" style={{ color: "var(--text-disabled)" }}>{comp.detail}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>{comp.pts}</span>
                        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>/ {comp.max}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* COLUMN 3: AI SETUP (4/12) */}
          <div className="col-span-12 md:col-span-4 p-5 flex flex-col h-full" style={{ background: "var(--bg-primary)" }}>
            <div className="text-[11px] font-bold uppercase tracking-widest mb-3 flex items-center justify-between" style={{ color: "var(--text-muted)" }}>
              <span>Algorithmic Setup</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded" style={{ background: "var(--purple-bg)", color: "var(--accent-purple)" }}>ML SECURED</span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* Target */}
              <div className="p-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                <div className="text-[10px] uppercase font-semibold mb-1 flex items-center gap-1.5" style={{ color: "var(--text-muted)" }}><Target className="w-3 h-3" style={{ color: "var(--accent-positive)" }} /> Target (TP)</div>
                <div className="text-[18px] font-bold tracking-tight" style={{ color: "var(--accent-positive)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>{data.target.toFixed(2)}</div>
              </div>
              {/* Stop Loss */}
              <div className="p-3 rounded border" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
                <div className="text-[10px] uppercase font-semibold mb-1 flex items-center gap-1.5" style={{ color: "var(--text-muted)" }}><AlertTriangle className="w-3 h-3" style={{ color: "var(--accent-negative)" }} /> Stop (SL)</div>
                <div className="text-[18px] font-bold tracking-tight" style={{ color: "var(--accent-negative)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>{data.stop.toFixed(2)}</div>
              </div>
            </div>

            <div className="p-3 rounded border flex justify-between items-center mb-4" style={{ background: "var(--bg-surface)", borderColor: "var(--border-subtle)" }}>
              <span className="text-[11px] font-medium uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>Reward / Risk Ratio</span>
              <span className="text-[14px] font-bold" style={{ color: "var(--accent-info)" }}>{data.rr_ratio.toFixed(2)} <span className="text-[10px] text-[var(--text-disabled)]">x</span></span>
            </div>

            {/* AI Log */}
            <div className="mt-auto flex flex-col gap-2">
              <div className="p-3 rounded border flex-1" style={{ background: "var(--purple-bg)", borderColor: "var(--purple-border)" }}>
                <div className="text-[10px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "var(--accent-purple)" }}>ML NOTES _</div>
                <p className="text-[12px] leading-relaxed" style={{ color: "var(--text-primary)", opacity: 0.85 }}>
                  {data.suggestion}
                </p>
              </div>

              {data.details.notes && data.details.notes.length > 0 && (
                <div className="flex justify-between items-center text-[9px] uppercase px-1">
                  <span style={{ color: "var(--text-muted)" }}>Diagnostic factors: {data.details.notes.length}</span>
                </div>
              )}
            </div>

          </div>

        </div>
      )}
    </div>
  );
}
