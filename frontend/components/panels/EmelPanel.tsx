"use client";

import { useState, useEffect, useCallback } from "react";
import { getApiBase } from "../../lib/api/base";
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
  SignalsIcon,
  SignalsIcon as Volume2,
  SecurityShieldIcon as Shield,
  AlertIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle,
  CloseIcon as XCircle,
  ArrowUpRightIcon as ArrowUpRight,
  ArrowDownRightIcon as ArrowDownRight,
  MinusIcon as Minus,
  PulseIcon,
} from "../ui/CustomIcons";
import { ShieldCheck } from "lucide-react";

const API_BASE = getApiBase();

interface CheckItem {
  id?: number;
  name?: string;
  subtitle?: string;
  status?: "pass" | "warning" | "fail" | string;
  direction?: "up" | "down" | "neutral" | string;
  color?: "green" | "yellow" | "red" | string;
  label?: string;
  details?: Record<string, any>;
  comment?: string;
}

interface FactorContribution {
  weight?: number;
  status?: string;
  contribution?: number;
}

interface ConfluenceData {
  score?: number;
  raw_score?: number;
  ml_boost?: number;
  max_score?: number;
  min_signal_threshold?: number;
  strong_threshold?: number;
  weights_applied?: Record<string, number>;
  factor_contributions?: Record<string, FactorContribution>;
  bonuses?: Array<{ name: string; value: number }>;
  calculation_method?: string;
}

interface ReboundLeg {
  label?: string;
  is_high_probability?: boolean;
  is_exit_trigger?: boolean;
  score?: number;
  threshold?: number;
  expected_bounce_to?: number;
  take_profit_zone?: number;
  invalidation?: number;
  short_invalidation?: number;
  reasons?: string[];
  bonus_confirmations?: string[];
}

interface ReboundData {
  rebound_long?: ReboundLeg;
  rebound_exit?: ReboundLeg;
}

interface EmelData {
  symbol?: string;
  timeframe?: string;
  signal?: string;
  confidence?: number;
  price?: number;
  signal_timestamp?: string;
  timestamp?: string;
  checks?: CheckItem[];
  confluence?: ConfluenceData;
  summary?: {
    green_count?: number;
    yellow_count?: number;
    red_count?: number;
    decision?: string;
    decision_reason?: string;
    rejections?: string[];
    entry_conditions?: string[];
  };
  rebound?: ReboundData;
  error?: string;
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

function cn(color?: string) {
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

function StatusIcon({ s }: { s?: string }) {
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
      const json = await res.json().catch(() => null);
      if (res.ok && json && typeof json === "object" && !("error" in json && json.error)) {
        setData(json as EmelData);
        markRefreshed((json as any).signal_timestamp || (json as any).timestamp);
      }
    } catch (e) {
      console.error("EMEL fetch error:", e);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [activeSymbol, timeframe, markRefreshed]);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    const interval = setInterval(() => fetchData(false), 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const handler = () => fetchData(true);
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [fetchData]);

  useEffect(() => {
    if (wsData && typeof wsData === "object" && !("error" in (wsData as any) && (wsData as any).error)) {
      setData(wsData as EmelData);
      setLoading(false);
      markRefreshed((wsData as any).signal_timestamp || (wsData as any).timestamp);
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

  const summary = data?.summary;
  const checks = data?.checks ?? [];
  const confluence = data?.confluence;
  const rejections = summary?.rejections ?? [];
  const entryConditions = summary?.entry_conditions ?? [];
  const confidence = data?.confidence ?? 0;

  const sigColor = data?.signal === "BUY" || data?.signal === "STRONG_BUY" || data?.signal === "BUY_SETUP"
    ? theme.green
    : data?.signal === "SELL" || data?.signal === "STRONG_SELL" || data?.signal === "SELL_SETUP"
      ? theme.red
      : theme.warn;
  const gc = summary?.green_count || 0;
  const yc = summary?.yellow_count || 0;
  const rc = summary?.red_count || 0;
  const tot = gc + yc + rc || 1;

  const confluenceScore = confluence?.score ?? 0;
  const confluenceMax = confluence?.max_score ?? 100;
  const confluenceThreshold = confluence?.min_signal_threshold ?? 40;
  const confluenceStrong = confluence?.strong_threshold ?? 70;

  const reboundLong = data?.rebound?.rebound_long;
  const reboundExit = data?.rebound?.rebound_exit;

  return (
    <div className="flex flex-col rounded-xl overflow-hidden" style={{ background: theme.bg, border: `1px solid ${theme.border}`, fontFamily: FONT }}>
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
              {typeof data.price === "number" ? data.price.toFixed(2) : "--"}
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

      {data && (
        <div className="flex flex-col gap-[1px]" style={{ background: theme.border }}>
          <div className="grid grid-cols-5 gap-[1px]" style={{ background: theme.border }}>
            <div className="relative p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <div className="absolute top-4 left-4 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: sigColor }}></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5" style={{ backgroundColor: sigColor }}></span>
              </div>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "rgba(255,255,255,0.7)" }}>Signal</span>
              <span className="text-[28px] leading-none font-bold tracking-tight drop-shadow-sm" style={{ color: sigColor }}>{data.signal || "HOLD"}</span>
            </div>
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
            <div className="p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-1.5" style={{ color: "rgba(255,255,255,0.7)" }}>ML Conf</span>
              <span className="text-[28px] leading-none font-bold tracking-tight font-mono drop-shadow-sm" style={{ color: theme.accent }}>{confidence.toFixed(0)}%</span>
            </div>
            <div className="relative p-5 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
              <div className="absolute top-4 left-4 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: sigColor }}></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5" style={{ backgroundColor: sigColor }}></span>
              </div>
              <span className="text-[11px] uppercase tracking-widest font-bold mb-2.5" style={{ color: "rgba(255,255,255,0.7)" }}>Action</span>
              <span className="text-[14px] font-bold px-3 py-1.5 rounded" style={{ color: sigColor, background: `${sigColor}15`, border: `1px solid ${sigColor}30` }}>
                {summary?.decision || data.signal || "HOLD"}
              </span>
            </div>
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

          {(reboundLong || reboundExit) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-[1px]" style={{ background: theme.border }}>
              <div className="p-5 flex flex-col gap-3" style={{ background: theme.bg }}>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-widest font-bold" style={{ color: "rgba(255,255,255,0.7)" }}>Rebound Entry</span>
                  <span className="text-[11px] font-mono font-bold px-2.5 py-1 rounded" style={{
                    color: reboundLong?.is_high_probability ? theme.green : theme.warn,
                    background: reboundLong?.is_high_probability ? `${theme.green}15` : `${theme.warn}15`,
                    border: `1px solid ${reboundLong?.is_high_probability ? `${theme.green}30` : `${theme.warn}30`}`,
                  }}>
                    {reboundLong?.label || "NO_SIGNAL"}
                  </span>
                </div>
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider" style={{ color: theme.muted }}>Score</div>
                    <div className="text-[28px] leading-none font-bold font-mono" style={{ color: reboundLong?.is_high_probability ? theme.green : theme.warn }}>
                      {typeof reboundLong?.score === "number" ? reboundLong.score.toFixed(0) : "--"}
                    </div>
                  </div>
                  <div className="text-right text-[11px] font-mono">
                    <div style={{ color: theme.muted }}>Threshold</div>
                    <div style={{ color: theme.text }}>{typeof reboundLong?.threshold === "number" ? reboundLong.threshold.toFixed(0) : "--"}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="rounded-lg px-3 py-2" style={{ background: `${theme.green}08`, border: `1px solid ${theme.green}15` }}>
                    <div style={{ color: theme.muted }}>Bounce Target</div>
                    <div style={{ color: theme.green }}>{typeof reboundLong?.expected_bounce_to === "number" ? reboundLong.expected_bounce_to.toFixed(2) : "--"}</div>
                  </div>
                  <div className="rounded-lg px-3 py-2" style={{ background: `${theme.red}08`, border: `1px solid ${theme.red}15` }}>
                    <div style={{ color: theme.muted }}>Invalidation</div>
                    <div style={{ color: theme.red }}>{typeof reboundLong?.invalidation === "number" ? reboundLong.invalidation.toFixed(2) : "--"}</div>
                  </div>
                </div>
              </div>
              <div className="p-5 flex flex-col gap-3" style={{ background: theme.bg }}>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-widest font-bold" style={{ color: "rgba(255,255,255,0.7)" }}>Rebound Exit</span>
                  <span className="text-[11px] font-mono font-bold px-2.5 py-1 rounded" style={{
                    color: reboundExit?.is_exit_trigger ? theme.red : theme.warn,
                    background: reboundExit?.is_exit_trigger ? `${theme.red}15` : `${theme.warn}15`,
                    border: `1px solid ${reboundExit?.is_exit_trigger ? `${theme.red}30` : `${theme.warn}30`}`,
                  }}>
                    {reboundExit?.label || "HOLD_REBOUND"}
                  </span>
                </div>
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider" style={{ color: theme.muted }}>Score</div>
                    <div className="text-[28px] leading-none font-bold font-mono" style={{ color: reboundExit?.is_exit_trigger ? theme.red : theme.warn }}>
                      {typeof reboundExit?.score === "number" ? reboundExit.score.toFixed(0) : "--"}
                    </div>
                  </div>
                  <div className="text-right text-[11px] font-mono">
                    <div style={{ color: theme.muted }}>Threshold</div>
                    <div style={{ color: theme.text }}>{typeof reboundExit?.threshold === "number" ? reboundExit.threshold.toFixed(0) : "--"}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="rounded-lg px-3 py-2" style={{ background: `${theme.red}08`, border: `1px solid ${theme.red}15` }}>
                    <div style={{ color: theme.muted }}>Take Profit Zone</div>
                    <div style={{ color: theme.red }}>{typeof reboundExit?.take_profit_zone === "number" ? reboundExit.take_profit_zone.toFixed(2) : "--"}</div>
                  </div>
                  <div className="rounded-lg px-3 py-2" style={{ background: `${theme.warn}08`, border: `1px solid ${theme.warn}15` }}>
                    <div style={{ color: theme.muted }}>Short Invalidation</div>
                    <div style={{ color: theme.warn }}>{typeof reboundExit?.short_invalidation === "number" ? reboundExit.short_invalidation.toFixed(2) : "--"}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-12 gap-[1px]" style={{ background: theme.border }}>
            <div className="col-span-12 md:col-span-8 grid grid-cols-3 gap-[1px]" style={{ background: theme.border }}>
              {checks.map((check) => {
                const checkId = check.id ?? 0;
                const Icon = CHECK_ICONS[checkId] || Activity;
                const cc = cn(check.color);
                const leftBorderColor = check.color === "green" ? theme.green : check.color === "red" ? theme.red : theme.warn;
                const leftBorderGradient = check.color === "green" ? `linear-gradient(180deg, ${theme.green}40 0%, ${theme.green}10 100%)` : check.color === "red" ? `linear-gradient(180deg, ${theme.red}40 0%, ${theme.red}10 100%)` : `linear-gradient(180deg, ${theme.warn}40 0%, ${theme.warn}10 100%)`;
                const angle = checkId % 2 === 1 ? "135deg" : "45deg";
                const stripeColor1 = `color-mix(in srgb, ${leftBorderColor} 6%, transparent)`;
                const stripeColor2 = `color-mix(in srgb, ${leftBorderColor} 15%, transparent)`;
                const stripeBg = `repeating-linear-gradient(${angle}, ${stripeColor1}, ${stripeColor1} 40px, ${stripeColor2} 40px, ${stripeColor2} 80px)`;

                return (
                  <div key={checkId} className="flex flex-col h-full transition-colors duration-500" style={{ background: stripeBg }}>
                    <div className="flex flex-1">
                      <div style={{ width: 4, background: leftBorderGradient, minHeight: "100%" }} />
                      <div className="flex-1 p-3">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex gap-2">
                            <Badge n={checkId} color={cc.c} />
                            <div className="flex flex-col">
                              <span className="text-[11px] font-bold uppercase tracking-wider leading-none mb-1" style={{ color: theme.text }}>{check.name}</span>
                              <span className="text-[10px]" style={{ color: theme.text, opacity: 0.85 }}>{check.subtitle}</span>
                            </div>
                          </div>
                          <StatusIcon s={check.status} />
                        </div>
                        <div className="text-[11px] font-bold font-mono px-2.5 py-1.5 rounded inline-flex items-center gap-2 self-start mb-3 mt-1" style={{ color: cc.c, background: cc.bg, border: `1px solid ${cc.b}` }}>
                          <Icon className="w-3.5 h-3.5" /> {check.label}
                        </div>
                        <div className="flex flex-col gap-1 mb-2 font-mono">
                          {Object.entries(check.details || {}).slice(0, 2).map(([k, v]) => (
                            <DetailRow key={k} k={k} v={v} />
                          ))}
                        </div>
                        <div className="mt-auto pt-3 border-t text-[10px] font-medium leading-relaxed" style={{ borderColor: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.7)" }}>
                          {check.comment}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="col-span-12 md:col-span-4 p-5 flex flex-col h-full" style={{ background: theme.bg }}>
              <div className="text-[11px] font-bold uppercase tracking-widest mb-4 flex items-center justify-between" style={{ color: theme.muted }}>
                <span>Diagnostic Logs</span>
                <Layers className="w-3.5 h-3.5" />
              </div>

              <div className="flex flex-col gap-4">
                {confluence && (
                  <div className="p-3 rounded border" style={{ background: theme.surface, borderColor: theme.border }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold mb-2 flex items-center gap-1.5" style={{ color: theme.accent }}>
                      <Gauge className="w-3 h-3" /> Confluence Breakdown
                    </div>
                    <div className="flex flex-col gap-1 mb-2">
                      <div className="flex justify-between text-[10px]">
                        <span style={{ color: theme.muted }}>Raw Score</span>
                        <span className="font-mono font-bold" style={{ color: theme.text }}>{(confluence.raw_score ?? 0) > 0 ? "+" : ""}{(confluence.raw_score ?? 0).toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between text-[10px]">
                        <span style={{ color: theme.muted }}>ML Boost</span>
                        <span className="font-mono font-bold" style={{ color: (confluence.ml_boost ?? 0) >= 0 ? theme.green : theme.red }}>
                          {(confluence.ml_boost ?? 0) > 0 ? "+" : ""}{(confluence.ml_boost ?? 0).toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-[10px] pt-1 border-t" style={{ borderColor: theme.border }}>
                        <span style={{ color: theme.muted }}>Final Score</span>
                        <span className="font-mono font-bold" style={{ color: confluenceScore >= confluenceStrong ? theme.green : confluenceScore >= confluenceThreshold ? theme.warn : theme.red }}>
                          {(confluence.score ?? 0) > 0 ? "+" : ""}{(confluence.score ?? 0).toFixed(1)}
                        </span>
                      </div>
                    </div>
                    {confluence.factor_contributions && (
                      <div className="mt-2 pt-2 border-t" style={{ borderColor: theme.border }}>
                        <div className="text-[8px] uppercase tracking-wider mb-1" style={{ color: theme.muted }}>Factor Weights</div>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
                          {Object.entries(confluence.factor_contributions).slice(0, 6).map(([factor, info]: [string, any]) => (
                            <div key={factor} className="flex justify-between text-[9px]">
                              <span style={{ color: theme.muted }}>{factor}</span>
                              <span className="font-mono" style={{ color: info.contribution > 0 ? theme.green : info.contribution < 0 ? theme.red : theme.warn }}>
                                {info.contribution > 0 ? "+" : ""}{info.contribution}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {rejections.length > 0 ? (
                  <div className="p-3 rounded border" style={{ background: `${theme.red}05`, borderColor: `${theme.red}15` }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold mb-2 flex items-center gap-1.5" style={{ color: theme.red }}>
                      <XCircle className="w-3 h-3" /> Risk Factors
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {rejections.map((r, i) => (
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

                {entryConditions.length > 0 && (
                  <div className="p-3 rounded border" style={{ background: theme.surface, borderColor: theme.border }}>
                    <div className="text-[9px] uppercase tracking-widest font-bold mb-2 flex items-center gap-1.5" style={{ color: theme.accent }}>
                      <Activity className="w-3 h-3" /> {t("emel.whenToTrade")}
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {entryConditions.map((c, i) => (
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
