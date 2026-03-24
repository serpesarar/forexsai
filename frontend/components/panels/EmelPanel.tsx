"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { useRefreshAge } from "../../hooks/useRefreshAge";
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

interface FactorContribution {
  weight: number;
  status: string;
  contribution: number;
}

interface ConfluenceData {
  score: number;
  raw_score: number;
  ml_boost: number;
  max_score: number;
  min_signal_threshold: number;
  strong_threshold: number;
  weights_applied: Record<string, number>;
  factor_contributions?: Record<string, FactorContribution>;
  bonuses?: Array<{ name: string; value: number }>;
  calculation_method: string;
}

interface EmelData {
  symbol: string; timeframe: string; signal: string; confidence: number; price: number;
  checks: CheckItem[];
  confluence?: ConfluenceData;
  summary: { green_count: number; yellow_count: number; red_count: number; decision: string; decision_reason?: string; rejections: string[]; entry_conditions: string[]; };
}

interface EmelPanelProps { symbol?: string; onSwitchMode?: () => void; }

const SYMBOLS = [{ key: "NDX.INDX", label: "NASDAQ" }, { key: "XAUUSD", label: "XAUUSD" }, { key: "GDAXI.INDX", label: "DAX" }, { key: "USOIL.FOREX", label: "US Oil" }];

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
  return color === "green" ? { c: theme.green, bg: `color-mix(in srgb, ${theme.green} 5%, transparent)`, b: `color-mix(in srgb, ${theme.green} 15%, transparent)` }
    : color === "red" ? { c: theme.red, bg: `color-mix(in srgb, ${theme.red} 5%, transparent)`, b: `color-mix(in srgb, ${theme.red} 15%, transparent)` }
      : { c: theme.warn, bg: `color-mix(in srgb, ${theme.warn} 5%, transparent)`, b: `color-mix(in srgb, ${theme.warn} 15%, transparent)` };
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
      <span className="text-[10px] uppercase tracking-wider" style={{ color: "rgba(255,255,255,0.7)" }}>{k.replace(/_/g, " ")}</span>
      <span className="text-[11px] font-bold font-mono" style={{ color: theme.text }}>{display}</span>
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
  const { refreshAge: signalAge, markRefreshed } = useRefreshAge();
  const { data: wsData } = useWSPanelData(activeSymbol, "emel");

  const fetchData = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      const res = await fetch(`${API_BASE}/api/panel/emel/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) {
        setData(json);
        markRefreshed();
      }
    } catch (e) { console.error("EMEL fetch error:", e); }
    finally { if (showLoading) setLoading(false); }
  }, [activeSymbol, timeframe, markRefreshed]);

  // Fetch when symbol or timeframe changes
  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  // Interval polling every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => fetchData(false), 60000); // Background refresh without loading
    return () => clearInterval(interval);
  }, [fetchData]);

  // Listen for global refresh event from header button
  useEffect(() => {
    const handler = () => fetchData(true);
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [fetchData]);

  // WebSocket data handling - reset freshness when live payload arrives
  useEffect(() => {
    if (wsData) {
      setData(wsData);
      setLoading(false);
      markRefreshed();
    }
  }, [wsData, markRefreshed]);

  if (loading && !data) {
    return (
      <div className="animate-pulse p-6 bg-[#0B0F17] rounded-xl border border-white/5">
        <div className="h-12 w-1/3 bg-white/5 rounded-lg mb-6" />
        <div className="grid grid-cols-12 gap-[1px] bg-white/5 h-64 rounded-xl" />
      </div>
    );
  }

  const sigColor = data?.signal === "BUY" || data?.signal === "STRONG_BUY" || data?.signal === "BUY_SETUP"
    ? theme.green
    : data?.signal === "SELL" || data?.signal === "STRONG_SELL" || data?.signal === "SELL_SETUP"
      ? theme.red
      : theme.warn;
  const gc = data?.summary.green_count || 0;
  const yc = data?.summary.yellow_count || 0;
  const rc = data?.summary.red_count || 0;
  const tot = gc + yc + rc || 1;

  // Confluence score
  const confluenceScore = data?.confluence?.score ?? 0;
  const confluenceMax = data?.confluence?.max_score ?? 100;
  const confluenceThreshold = data?.confluence?.min_signal_threshold ?? 40;
  const confluenceStrong = data?.confluence?.strong_threshold ?? 70;

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
        loading={loading}
        panelId="emel-panel"
        signalAge={signalAge}
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
          <div className="grid grid-cols-5 gap-[1px]" style={{ background: theme.border }}>
            {/* Signal */}
            <div className="relative p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <div className="absolute top-4 left-4 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: sigColor }}></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5" style={{ backgroundColor: sigColor }}></span>
              </div>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "rgba(255,255,255,0.7)" }}>Signal</span>
              <span className="text-[28px] leading-none font-bold tracking-tight drop-shadow-sm" style={{ color: sigColor }}>{data.signal}</span>
            </div>
            {/* Confluence Score - NEW */}
            <div className="p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "rgba(255,255,255,0.7)" }}>Confluence</span>
              <span className="text-[28px] leading-none font-bold tracking-tight font-mono drop-shadow-sm" style={{
                color: confluenceScore >= confluenceStrong ? theme.green :
                  confluenceScore >= confluenceThreshold ? theme.warn :
                    confluenceScore <= -confluenceStrong ? theme.red :
                      confluenceScore <= -confluenceThreshold ? theme.warn : theme.muted
              }}>
                {confluenceScore > 0 ? "+" : ""}{confluenceScore.toFixed(0)}
              </span>
              <div className="flex gap-0.5 rounded-full overflow-hidden mt-2" style={{ height: 4, width: 44, background: "rgba(255,255,255,0.06)" }}>
                <div className="h-full" style={{
                  width: `${Math.min(100, Math.max(0, (confluenceScore + confluenceMax) / (2 * confluenceMax) * 100))}%`,
                  background: confluenceScore >= 0 ? theme.green : theme.red
                }} />
              </div>
            </div>
            {/* Confidence */}
            <div className="p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "rgba(255,255,255,0.7)" }}>ML Conf</span>
              <span className="text-[28px] leading-none font-bold tracking-tight font-mono drop-shadow-sm" style={{ color: theme.accent }}>{data.confidence.toFixed(0)}%</span>
            </div>
            {/* Decision */}
            <div className="relative p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <div className="absolute top-4 left-4 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: sigColor }}></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5" style={{ backgroundColor: sigColor }}></span>
              </div>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-2.5" style={{ color: "rgba(255,255,255,0.7)" }}>Action</span>
              <span className="text-[14px] font-bold px-3 py-1.5 rounded" style={{ color: sigColor, background: `${sigColor}15`, border: `1px solid ${sigColor}30` }}>
                {data.summary.decision}
              </span>
            </div>
            {/* Score Breakdown */}
            <div className="p-5 flex flex-col justify-center" style={{ background: theme.bg }}>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-2.5" style={{ color: "rgba(255,255,255,0.7)" }}>Checks</span>
              <div className="flex gap-0.5 rounded-full overflow-hidden mb-2.5" style={{ height: 8, background: "rgba(255,255,255,0.06)" }}>
                <div className="h-full" style={{ width: `${(gc / tot) * 100}%`, background: theme.green }} />
                <div className="h-full" style={{ width: `${(yc / tot) * 100}%`, background: theme.warn }} />
                <div className="h-full" style={{ width: `${(rc / tot) * 100}%`, background: theme.red }} />
              </div>
              <div className="flex justify-between items-center text-[11px] font-mono font-bold">
                <span style={{ color: theme.green }}>{gc}✓</span>
                <span style={{ color: theme.warn }}>{yc}~</span>
                <span style={{ color: theme.red }}>{rc}✗</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-[1px]" style={{ background: theme.border }}>

            {/* 9 CHECKPOINTS GRID (8/12) */}
            <div className="col-span-12 md:col-span-8 grid grid-cols-3 gap-[1px]" style={{ background: theme.border }}>
              {data.checks.map((check) => {
                const Icon = CHECK_ICONS[check.id] || Activity;
                const cc = cn(check.color);
                // Sol renk şeridi için gradyan
                const leftBorderColor = check.color === "green" ? theme.green :
                  check.color === "red" ? theme.red : theme.warn;
                const leftBorderGradient = check.color === "green" ? `linear-gradient(180deg, ${theme.green}40 0%, ${theme.green}10 100%)` :
                  check.color === "red" ? `linear-gradient(180deg, ${theme.red}40 0%, ${theme.red}10 100%)` :
                    `linear-gradient(180deg, ${theme.warn}40 0%, ${theme.warn}10 100%)`;

                const angle = check.id % 2 === 1 ? "135deg" : "45deg";
                const stripeColor1 = `color-mix(in srgb, ${leftBorderColor} 6%, transparent)`;
                const stripeColor2 = `color-mix(in srgb, ${leftBorderColor} 15%, transparent)`;
                const stripeBg = `repeating-linear-gradient(${angle}, ${stripeColor1}, ${stripeColor1} 40px, ${stripeColor2} 40px, ${stripeColor2} 80px)`;

                return (
                  <div key={check.id} className="flex flex-col h-full transition-colors duration-500" style={{ background: stripeBg }}>
                    {/* Sol renk şeridi + içerik */}
                    <div className="flex flex-1">
                      {/* Sol renk şeridi */}
                      <div style={{
                        width: 4,
                        background: leftBorderGradient,
                        minHeight: '100%'
                      }} />
                      {/* İçerik */}
                      <div className="flex-1 p-3">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex gap-2">
                            <Badge n={check.id} color={cc.c} />
                            <div className="flex flex-col">
                              <span className="text-[11px] font-bold uppercase tracking-wider leading-none mb-1" style={{ color: theme.text }}>{check.name}</span>
                              <span className="text-[10px]" style={{ color: theme.text, opacity: 0.85 }}>{check.subtitle}</span>
                            </div>
                          </div>
                          <StatusIcon s={check.status} />
                        </div>
                        {/* Current State */}
                        <div className="text-[11px] font-bold font-mono px-2.5 py-1.5 rounded inline-flex items-center gap-2 self-start mb-3 mt-1" style={{ color: cc.c, background: cc.bg, border: `1px solid ${cc.b}` }}>
                          <Icon className="w-3.5 h-3.5" /> {check.label}
                        </div>
                        {/* Metric Rows */}
                        <div className="flex flex-col gap-1 mb-2 font-mono">
                          {Object.entries(check.details).slice(0, 2).map(([k, v]) => (
                            <DetailRow key={k} k={k} v={v} />
                          ))}
                        </div>
                        {/* Description Footer */}
                        <div className="mt-auto pt-3 border-t text-[10px] font-medium leading-relaxed" style={{ borderColor: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.7)" }}>
                          {check.comment}
                        </div>
                      </div>
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
                {/* Confluence Score Breakdown */}
                {data.confluence && (
                  <div className="p-3 rounded border" style={{ background: theme.surface, borderColor: theme.border }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold mb-2 flex items-center gap-1.5" style={{ color: theme.accent }}>
                      <Gauge className="w-3 h-3" /> Confluence Breakdown
                    </div>
                    <div className="flex flex-col gap-1 mb-2">
                      <div className="flex justify-between text-[10px]">
                        <span style={{ color: theme.muted }}>Raw Score</span>
                        <span className="font-mono font-bold" style={{ color: theme.text }}>{data.confluence.raw_score > 0 ? "+" : ""}{data.confluence.raw_score.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between text-[10px]">
                        <span style={{ color: theme.muted }}>ML Boost</span>
                        <span className="font-mono font-bold" style={{ color: data.confluence.ml_boost >= 0 ? theme.green : theme.red }}>
                          {data.confluence.ml_boost > 0 ? "+" : ""}{data.confluence.ml_boost.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-[10px] pt-1 border-t" style={{ borderColor: theme.border }}>
                        <span style={{ color: theme.muted }}>Final Score</span>
                        <span className="font-mono font-bold" style={{ color: confluenceScore >= confluenceStrong ? theme.green : confluenceScore >= confluenceThreshold ? theme.warn : theme.red }}>
                          {data.confluence.score > 0 ? "+" : ""}{data.confluence.score.toFixed(1)}
                        </span>
                      </div>
                    </div>
                    {/* Factor Contributions */}
                    {data.confluence.factor_contributions && (
                      <div className="mt-2 pt-2 border-t" style={{ borderColor: theme.border }}>
                        <div className="text-[8px] uppercase tracking-wider mb-1" style={{ color: theme.muted }}>Factor Weights</div>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
                          {Object.entries(data.confluence.factor_contributions).slice(0, 6).map(([factor, info]: [string, any]) => (
                            <div key={factor} className="flex justify-between text-[9px]">
                              <span style={{ color: theme.muted }}>{factor}</span>
                              <span className="font-mono" style={{
                                color: info.contribution > 0 ? theme.green : info.contribution < 0 ? theme.red : theme.warn
                              }}>
                                {info.contribution > 0 ? "+" : ""}{info.contribution}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

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
