"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { PanelHeader } from "../PanelHeader";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  ArrowUpRightIcon as TrendingUp,
  ActivityIcon as Activity,
  ChartsIcon as BarChart3,
  TargetIcon as Target,
  AnalysisIcon as Layers,
  ChartsIcon as Gauge,
  SignalsIcon as Volume2,
  SecurityShieldIcon as Shield,
  RotateIcon as RefreshCw,
  AlertIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle,
  CloseIcon as XCircle,
  ArrowUpRightIcon as ArrowUpRight,
  ArrowDownRightIcon as ArrowDownRight,
  MinusIcon as Minus,
} from "../ui/CustomIcons";
import { EmelIcon, PulseIcon, SignalsIcon } from "../ui/CustomIcons";
import { ShieldCheck } from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface CheckItem {
  id: number; name: string; subtitle: string;
  status: "pass" | "warning" | "fail"; direction: "up" | "down" | "neutral";
  color: "green" | "yellow" | "red"; label: string;
  details: Record<string, any>; comment: string;
}

interface EmelData {
  symbol: string; timeframe: string; signal: string; confidence: number; price: number;
  checks: CheckItem[];
  summary: { green_count: number; yellow_count: number; red_count: number; decision: string; rejections: string[]; entry_conditions: string[]; };
}

interface EmelPanelProps { symbol?: string; onSwitchMode?: () => void; }

const SYMBOLS = [{ key: "NDX.INDX", label: "NASDAQ" }, { key: "XAUUSD", label: "XAUUSD" }, { key: "GDAXI.INDX", label: "DAX" }, { key: "CL.COMM", label: "US Oil" }];

const CHECK_ICONS: Record<number, any> = {
  1: TrendingUp, 2: Activity, 3: Layers, 4: Target, 5: BarChart3, 6: Gauge, 7: Volume2, 8: SignalsIcon, 9: Shield,
};

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
const theme = {
  bg: "var(--bg-primary)",
  surface: "var(--bg-surface)",
  card: "var(--bg-card)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  purple: "var(--accent-purple)"
};

function cn(color: string) {
  return color === "green" ? { c: theme.green, bg: `${theme.green}05`, b: `${theme.green}15` }
    : color === "red" ? { c: theme.red, bg: `${theme.red}05`, b: `${theme.red}15` }
      : { c: theme.warn, bg: `${theme.warn}05`, b: `${theme.warn}15` };
}

function MtfPills({ tf }: { tf: Array<{ tf: string; dir: string }> }) {
  return (
    <div className="flex gap-1.5 flex-wrap mt-1">
      {tf.map((t) => {
        const c = t.dir === "up" ? theme.green : t.dir === "down" ? theme.red : theme.warn;
        const I = t.dir === "up" ? ArrowUpRight : t.dir === "down" ? ArrowDownRight : Minus;
        return (
          <div key={t.tf} className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold"
            style={{ background: `${c}10`, border: `1px solid ${c}20`, color: c }}>
            <I className="w-2.5 h-2.5" />{t.tf}
          </div>
        );
      })}
    </div>
  );
}

function DetailRow({ k, v }: { k: string; v: any }) {
  if (k === "timeframes" && Array.isArray(v)) return <MtfPills tf={v} />;
  const display = typeof v === "number" ? (Number.isInteger(v) ? String(v) : v.toFixed(2))
    : typeof v === "object" && v !== null ? Object.values(v).join(", ") : String(v);
  return (
    <div className="flex justify-between items-center py-0.5">
      <span className="text-[9px] uppercase tracking-wider" style={{ color: theme.muted }}>{k.replace(/_/g, " ")}</span>
      <span className="text-[10px] font-bold font-mono" style={{ color: theme.text }}>{display}</span>
    </div>
  );
}

function Badge({ n, color }: { n: number; color: string }) {
  return (
    <div className="w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold font-mono shrink-0"
      style={{ background: `${color}15`, border: `1px solid ${color}30`, color }}>
      {n}
    </div>
  );
}

function StatusIcon({ s }: { s: string }) {
  if (s === "pass") return <CheckCircle className="w-3.5 h-3.5" style={{ color: theme.green }} />;
  if (s === "warning") return <AlertTriangle className="w-3.5 h-3.5" style={{ color: theme.warn }} />;
  if (s === "fail") return <XCircle className="w-3.5 h-3.5" style={{ color: theme.red }} />;
  return null;
}

export default function EmelPanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: EmelPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<EmelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");
  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "emel");

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [activeSymbol, timeframe]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/panel/emel/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) setData(json);
    } catch (e) { console.error("EMEL fetch error:", e); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (wsData) { setData(wsData); setLoading(false); } }, [wsData]);
  useEffect(() => {
    if (!wsData) fetchData();
    if (!wsConnected) { const iv = setInterval(fetchData, 120000); return () => clearInterval(iv); }
  }, [activeSymbol, timeframe, wsConnected]);

  if (loading && !data) {
    return (
      <div className="animate-pulse p-6 bg-[#0B0F17] rounded-xl border border-white/5">
        <div className="h-12 w-1/3 bg-white/5 rounded-lg mb-6" />
        <div className="grid grid-cols-12 gap-[1px] bg-white/5 h-64 rounded-xl" />
      </div>
    );
  }

  const sigColor = data?.signal === "BUY" ? theme.green : data?.signal === "SELL" ? theme.red : theme.warn;
  const gc = data?.summary.green_count || 0;
  const yc = data?.summary.yellow_count || 0;
  const rc = data?.summary.red_count || 0;
  const tot = gc + yc + rc || 1;

  return (
    <div className="flex flex-col rounded-xl overflow-hidden" style={{ background: theme.bg, border: `1px solid ${theme.border}`, fontFamily: FONT }}>

      {/* ── HEADER (New Design) ── */}
      <PanelHeader
        title="EMEL"
        subtitle="ADVANCED ANALYSIS • 9 CHECKS"
        icon={<ShieldCheck size={24} strokeWidth={2.5} />}
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        iconColor="var(--accent-cyan)"
        symbols={SYMBOLS}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        timeframes={["15m", "1H", "4H", "1D"]}
        onRefresh={fetchData}
        loading={loading}
        panelId="emel-panel"
        extraContent={data ? (
          <div className="flex items-center gap-3">
            <div className="text-[26px] font-bold tracking-tighter leading-none font-mono" style={{ color: theme.text }}>
              {data.price.toFixed(2)}
            </div>
            {onSwitchMode && (
              <button 
                onClick={onSwitchMode} 
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold font-mono transition-all"
                style={{ background: `${theme.warn}15`, border: `1px solid ${theme.warn}30`, color: theme.warn }}
              >
                <PulseIcon size={12} style={{ color: theme.warn }} /> SWAP
              </button>
            )}
          </div>
        ) : undefined}
      />

      {/* ── MAIN CONTENT ── */}
      {data && (
        <div className="flex flex-col gap-[1px]" style={{ background: theme.border }}>

          {/* HERO SIGNAL STRIP (Top Row) */}
          <div className="grid grid-cols-4 gap-[1px]" style={{ background: theme.border }}>
            {/* Signal */}
            <div className="p-4 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <span className="text-[10px] uppercase tracking-widest font-bold mb-1" style={{ color: theme.muted }}>Signal</span>
              <span className="text-3xl font-bold tracking-tight" style={{ color: sigColor }}>{data.signal}</span>
            </div>
            {/* Confidence */}
            <div className="p-4 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <span className="text-[10px] uppercase tracking-widest font-bold mb-1" style={{ color: theme.muted }}>Confidence</span>
              <span className="text-3xl font-bold tracking-tight font-mono" style={{ color: theme.accent }}>{data.confidence.toFixed(0)}%</span>
            </div>
            {/* Decision */}
            <div className="p-4 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <span className="text-[10px] uppercase tracking-widest font-bold mb-2" style={{ color: theme.muted }}>Action</span>
              <span className="text-[14px] font-bold px-3 py-1 rounded" style={{ color: sigColor, background: `${sigColor}15`, border: `1px solid ${sigColor}30` }}>
                {data.summary.decision}
              </span>
            </div>
            {/* Score Breakdown */}
            <div className="p-4 flex flex-col justify-center" style={{ background: theme.bg }}>
              <span className="text-[10px] uppercase tracking-widest font-bold mb-2" style={{ color: theme.muted }}>Checkpoint Score</span>
              <div className="flex gap-0.5 rounded-full overflow-hidden mb-2" style={{ height: 6, background: "rgba(255,255,255,0.04)" }}>
                <div className="h-full" style={{ width: `${(gc / tot) * 100}%`, background: theme.green }} />
                <div className="h-full" style={{ width: `${(yc / tot) * 100}%`, background: theme.warn }} />
                <div className="h-full" style={{ width: `${(rc / tot) * 100}%`, background: theme.red }} />
              </div>
              <div className="flex justify-between items-center text-[10px] font-mono font-bold">
                <span style={{ color: theme.green }}>{gc} PASS</span>
                <span style={{ color: theme.warn }}>{yc} WARN</span>
                <span style={{ color: theme.red }}>{rc} FAIL</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-[1px]" style={{ background: theme.border }}>

            {/* 9 CHECKPOINTS GRID (8/12) */}
            <div className="col-span-12 md:col-span-8 grid grid-cols-3 gap-[1px]" style={{ background: theme.border }}>
              {data.checks.map((check) => {
                const Icon = CHECK_ICONS[check.id] || Activity;
                const cc = cn(check.color);
                return (
                  <div key={check.id} className="p-3 flex flex-col h-full" style={{ background: theme.bg }}>
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex gap-2">
                        <Badge n={check.id} color={cc.c} />
                        <div className="flex flex-col">
                          <span className="text-[10px] font-bold uppercase tracking-wider leading-none mb-0.5" style={{ color: theme.text }}>{check.name}</span>
                          <span className="text-[9px]" style={{ color: theme.muted }}>{check.subtitle}</span>
                        </div>
                      </div>
                      <StatusIcon s={check.status} />
                    </div>
                    {/* Current State */}
                    <div className="text-[10px] font-bold font-mono px-2 py-1 rounded inline-flex items-center gap-1.5 self-start mb-2" style={{ color: cc.c, background: cc.bg, border: `1px solid ${cc.b}` }}>
                      <Icon className="w-3 h-3" /> {check.label}
                    </div>
                    {/* Metric Rows */}
                    <div className="flex flex-col gap-1 mb-2 font-mono">
                      {Object.entries(check.details).slice(0, 2).map(([k, v]) => (
                        <DetailRow key={k} k={k} v={v} />
                      ))}
                    </div>
                    {/* Description Footer */}
                    <div className="mt-auto pt-2 border-t text-[9px] leading-relaxed" style={{ borderColor: theme.border, color: "rgba(255,255,255,0.4)" }}>
                      {check.comment}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* DIAGNOSTICS LOG (4/12) */}
            <div className="col-span-12 md:col-span-4 p-5 flex flex-col h-full" style={{ background: theme.bg }}>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-4 flex items-center justify-between" style={{ color: theme.muted }}>
                <span>Diagnostic Logs</span>
                <Layers className="w-3.5 h-3.5" />
              </div>

              <div className="flex flex-col gap-4">
                {/* Rejections */}
                {data.summary.rejections.length > 0 ? (
                  <div className="p-3 rounded border" style={{ background: `${theme.red}05`, borderColor: `${theme.red}15` }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold mb-2 flex items-center gap-1.5" style={{ color: theme.red }}>
                      <XCircle className="w-3 h-3" /> Risk Factors
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {data.summary.rejections.map((r, i) => (
                        <div key={i} className="text-[10px] flex items-start gap-1.5" style={{ color: theme.red }}>
                          <span className="mt-0.5 opacity-50">•</span>
                          <span className="leading-relaxed opacity-90">{r}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded border" style={{ background: `${theme.green}05`, borderColor: `${theme.green}15` }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold flex items-center gap-1.5" style={{ color: theme.green }}>
                      <CheckCircle className="w-3 h-3" /> No Risk Factors Detected
                    </div>
                  </div>
                )}

                {/* Entry Conditions */}
                {data.summary.entry_conditions.length > 0 && (
                  <div className="p-3 rounded border" style={{ background: theme.surface, borderColor: theme.border }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold mb-2 flex items-center gap-1.5" style={{ color: theme.accent }}>
                      <Activity className="w-3 h-3" /> {t("emel.whenToTrade")}
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {data.summary.entry_conditions.map((c, i) => (
                        <div key={i} className="text-[10px] flex items-start gap-1.5" style={{ color: theme.text }}>
                          <span className="mt-0.5" style={{ color: theme.accent }}>→</span>
                          <span className="leading-relaxed opacity-80">{c}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
