"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { getApiBase } from "../../lib/api/base";
import { useI18nStore } from "../../lib/i18n/store";
import { useSignalCountdown } from "../../hooks/useSignalCountdown";
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
import { ShieldCheck, ChevronDown, ChevronRight } from "lucide-react";

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
  direction?: string;
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
  bonuses?: Array<{ name: string; value: number; hard_gate?: boolean; applied_to?: string }>;
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
}

interface EmelData {
  symbol?: string;
  timeframe?: string;
  effective_timeframe?: string;
  signal?: string;
  confidence?: number;
  price?: number;
  reliability?: number;
  signal_timestamp?: string;
  timestamp?: string;
  gates?: {
    is_ath_zone?: boolean;
    market_open?: boolean;
    notes?: string[];
  };
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
  rebound?: { rebound_long?: ReboundLeg; rebound_exit?: ReboundLeg };
  error?: string;
}

interface EmelPanelProps { symbol?: string; onSwitchMode?: () => void; }

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US Oil" },
];

// Tier assignment
const CORE_IDS = [1, 3, 6];       // Trend, MTF, Momentum
const CONTEXT_IDS = [2, 5, 7];    // Regime, S/R, Volume
const GUARD_IDS = [4, 8, 9];      // Pattern, Learning, Portfolio

const CHECK_ICONS: Record<number, any> = {
  1: TrendingUp, 2: Activity, 3: Layers, 4: Target,
  5: BarChart3, 6: Gauge, 7: Volume2, 8: SignalsIcon, 9: Shield,
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
  purple: "var(--accent-purple)",
};

function colorOf(c?: string) {
  return c === "green" ? theme.green : c === "red" ? theme.red : theme.warn;
}

function StatusIcon({ s, size = 14 }: { s?: string; size?: number }) {
  const sz = `${size}px`;
  if (s === "pass") return <CheckCircle style={{ width: sz, height: sz, color: theme.green }} />;
  if (s === "warning") return <AlertTriangle style={{ width: sz, height: sz, color: theme.warn }} />;
  if (s === "fail") return <XCircle style={{ width: sz, height: sz, color: theme.red }} />;
  return null;
}

function DirArrow({ d, size = 12 }: { d?: string; size?: number }) {
  const sz = `${size}px`;
  if (d === "up") return <ArrowUpRight style={{ width: sz, height: sz, color: theme.green }} />;
  if (d === "down") return <ArrowDownRight style={{ width: sz, height: sz, color: theme.red }} />;
  return <Minus style={{ width: sz, height: sz, color: theme.warn }} />;
}

function MtfPills({ tf }: { tf: Array<{ tf: string; dir: string }> }) {
  return (
    <div className="flex gap-1.5 flex-wrap">
      {tf.map((t) => {
        const c = t.dir === "up" ? theme.green : t.dir === "down" ? theme.red : theme.warn;
        return (
          <div key={t.tf} className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold"
            style={{ background: `${c}10`, border: `1px solid ${c}20`, color: c }}>
            <DirArrow d={t.dir} size={10} />{t.tf}
          </div>
        );
      })}
    </div>
  );
}

/** CORE check card — large, prominent (for Trend/MTF/Momentum) */
function CoreCheckCard({ check }: { check: CheckItem }) {
  const c = colorOf(check.color);
  const Icon = CHECK_ICONS[check.id || 0] || Activity;
  const details = check.details || {};
  const tfArr = Array.isArray((details as any).timeframes) ? (details as any).timeframes : null;

  return (
    <div className="flex flex-col p-4 gap-3 relative" style={{ background: theme.bg }}>
      <div className="absolute top-0 left-0 right-0 h-[3px]" style={{ background: c }} />
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded flex items-center justify-center"
            style={{ background: `${c}15`, border: `1px solid ${c}30`, color: c }}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-[11px] font-bold uppercase tracking-wider leading-none" style={{ color: theme.text }}>
              {check.name}
            </span>
            <span className="text-[9px] mt-1" style={{ color: theme.muted }}>{check.subtitle}</span>
          </div>
        </div>
        <StatusIcon s={check.status} size={16} />
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-[20px] font-bold tracking-tight leading-none" style={{ color: c }}>
          {check.label}
        </span>
        <DirArrow d={check.direction} />
      </div>

      {tfArr ? (
        <MtfPills tf={tfArr} />
      ) : (
        <div className="flex flex-col gap-0.5 font-mono">
          {Object.entries(details)
            .filter(([k]) => !["timeframes", "debug"].includes(k))
            .slice(0, 3)
            .map(([k, v]) => (
              <div key={k} className="flex justify-between text-[10px]">
                <span style={{ color: theme.muted }}>{k.replace(/_/g, " ")}</span>
                <span className="font-bold" style={{ color: theme.text }}>
                  {typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v)}
                </span>
              </div>
            ))}
        </div>
      )}

      <div className="text-[10px] leading-relaxed pt-2 border-t" style={{ borderColor: theme.border, color: "rgba(255,255,255,0.6)" }}>
        {check.comment}
      </div>
    </div>
  );
}

/** CONTEXT check — medium, compact */
function ContextCheckCard({ check }: { check: CheckItem }) {
  const c = colorOf(check.color);
  const Icon = CHECK_ICONS[check.id || 0] || Activity;
  return (
    <div className="flex flex-col p-3 gap-2" style={{ background: theme.bg, borderLeft: `3px solid ${c}` }}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5" style={{ color: c }} />
          <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: theme.text }}>{check.name}</span>
        </div>
        <StatusIcon s={check.status} size={12} />
      </div>
      <div className="text-[13px] font-bold" style={{ color: c }}>{check.label}</div>
      <div className="text-[9px] leading-snug" style={{ color: "rgba(255,255,255,0.55)" }}>{check.comment}</div>
    </div>
  );
}

/** GUARD check — compact single-line row */
function GuardCheckRow({ check }: { check: CheckItem }) {
  const c = colorOf(check.color);
  const Icon = CHECK_ICONS[check.id || 0] || Activity;
  return (
    <div className="flex items-center justify-between px-3 py-2" style={{ background: theme.bg }}>
      <div className="flex items-center gap-2">
        <Icon className="w-3 h-3" style={{ color: c }} />
        <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: theme.text }}>{check.name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold font-mono" style={{ color: c }}>{check.label}</span>
        <StatusIcon s={check.status} size={12} />
      </div>
    </div>
  );
}

export default function EmelPanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: EmelPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<EmelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");
  const [reboundOpen, setReboundOpen] = useState(false);
  const [breakdownOpen, setBreakdownOpen] = useState(false);
  const { markRefreshed } = useSignalCountdown("emel", 300, data?.signal_timestamp);
  const { data: wsData } = useWSPanelData(activeSymbol, "emel");

  const fetchData = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      const res = await fetch(`${API_BASE}/api/panel/emel/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json().catch(() => null);
      if (res.ok && json && typeof json === "object" && !("error" in json && json.error)) {
        setData(json as EmelData);
        markRefreshed();
      }
    } catch (e) {
      console.error("EMEL fetch error:", e);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [activeSymbol, timeframe, markRefreshed]);

  useEffect(() => { fetchData(true); }, [fetchData]);
  useEffect(() => {
    const i = setInterval(() => fetchData(false), 60000);
    return () => clearInterval(i);
  }, [fetchData]);
  useEffect(() => {
    const h = () => fetchData(true);
    window.addEventListener("dashboard-refresh", h);
    return () => window.removeEventListener("dashboard-refresh", h);
  }, [fetchData]);
  useEffect(() => {
    if (wsData && typeof wsData === "object" && !("error" in (wsData as any) && (wsData as any).error)) {
      setData(wsData as EmelData);
      setLoading(false);
      markRefreshed();
    }
  }, [wsData, markRefreshed]);

  const { coreChecks, contextChecks, guardChecks } = useMemo(() => {
    const arr = data?.checks ?? [];
    const byId = Object.fromEntries(arr.map((c) => [c.id, c]));
    return {
      coreChecks: CORE_IDS.map((id) => byId[id]).filter(Boolean) as CheckItem[],
      contextChecks: CONTEXT_IDS.map((id) => byId[id]).filter(Boolean) as CheckItem[],
      guardChecks: GUARD_IDS.map((id) => byId[id]).filter(Boolean) as CheckItem[],
    };
  }, [data?.checks]);

  if (loading && !data) {
    return (
      <div className="animate-pulse p-6 bg-[#0B0F17] rounded-xl border border-white/5">
        <div className="h-12 w-1/3 bg-white/5 rounded-lg mb-6" />
        <div className="grid grid-cols-12 gap-[1px] bg-white/5 h-64 rounded-xl" />
      </div>
    );
  }

  if (!data) return null;

  const summary = data.summary;
  const confluence = data.confluence;
  const gates = data.gates;
  const rejections = summary?.rejections ?? [];
  const entryConditions = summary?.entry_conditions ?? [];
  const confidence = data.confidence ?? 0;
  const reliability = data.reliability ?? 0;

  const sigIsBuy = ["BUY", "STRONG_BUY", "BUY_SETUP"].includes(data.signal || "");
  const sigIsSell = ["SELL", "STRONG_SELL", "SELL_SETUP"].includes(data.signal || "");
  const sigColor = sigIsBuy ? theme.green : sigIsSell ? theme.red : theme.warn;

  const gc = summary?.green_count || 0;
  const yc = summary?.yellow_count || 0;
  const rc = summary?.red_count || 0;
  const tot = gc + yc + rc || 1;

  const finalScore = confluence?.score ?? 0;
  const rawScore = confluence?.raw_score ?? 0;
  const mlBoost = confluence?.ml_boost ?? 0;
  const confluenceMax = confluence?.max_score ?? 100;
  const confluenceThreshold = confluence?.min_signal_threshold ?? 40;
  const confluenceStrong = confluence?.strong_threshold ?? 70;

  // Action box text
  let actionHeadline = "BEKLE";
  let actionBody = "Yetersiz konfluans — şartlar oluşmadı.";
  let actionColor = theme.warn;
  if (data.signal === "STRONG_BUY" || data.signal === "BUY") {
    actionHeadline = data.signal === "STRONG_BUY" ? "GÜÇLÜ ALIŞ" : "ALIŞ";
    actionBody = summary?.decision_reason || "Bullish konfluans oluştu.";
    actionColor = theme.green;
  } else if (data.signal === "STRONG_SELL" || data.signal === "SELL") {
    actionHeadline = data.signal === "STRONG_SELL" ? "GÜÇLÜ SATIŞ" : "SATIŞ";
    actionBody = summary?.decision_reason || "Bearish konfluans oluştu.";
    actionColor = theme.red;
  } else if (data.signal === "BUY_SETUP") {
    actionHeadline = "ALIŞ SETUP'I";
    actionBody = "Bekleyen setup — aşağıdaki koşullar oluşunca girin.";
    actionColor = theme.accent;
  } else if (data.signal === "SELL_SETUP") {
    actionHeadline = "SATIŞ SETUP'I";
    actionBody = "Bekleyen setup — aşağıdaki koşullar oluşunca girin.";
    actionColor = theme.accent;
  }

  const reboundLong = data.rebound?.rebound_long;
  const reboundExit = data.rebound?.rebound_exit;
  const hasRebound = !!(reboundLong || reboundExit);

  const fallbackUsed = data.effective_timeframe && data.effective_timeframe !== data.timeframe;

  return (
    <div className="flex flex-col rounded-xl overflow-hidden"
      style={{ background: theme.bg, border: `1px solid ${theme.border}`, fontFamily: FONT }}>
      <PanelHeader
        title="EMEL"
        subtitle="9-CHECK CONFLUENCE"
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
        signalCountdown={{
          modelKey: "emel",
          refreshIntervalSeconds: 300,
          signalTimestamp: data.signal_timestamp,
        }}
        extraContent={
          <div className="flex items-center gap-3">
            <div className="text-[26px] font-bold tracking-tighter leading-none font-mono" style={{ color: theme.text }}>
              {typeof data.price === "number" ? data.price.toFixed(2) : "--"}
            </div>
            {onSwitchMode && (
              <button
                onClick={onSwitchMode}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold font-mono"
                style={{ background: `${theme.warn}15`, border: `1px solid ${theme.warn}30`, color: theme.warn }}>
                <PulseIcon size={12} style={{ color: theme.warn }} /> SWAP
              </button>
            )}
          </div>
        }
      />

      {/* ═══════════════ HERO STRIP ═══════════════ */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-[1px]" style={{ background: theme.border }}>
        {/* Signal */}
        <div className="relative p-4 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
          <div className="absolute top-3 right-3 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ backgroundColor: sigColor }}></span>
            <span className="relative inline-flex rounded-full h-2 w-2" style={{ backgroundColor: sigColor }}></span>
          </div>
          <span className="text-[9px] uppercase tracking-widest font-bold mb-1" style={{ color: theme.muted }}>Signal</span>
          <span className="text-[24px] leading-none font-bold tracking-tight" style={{ color: sigColor }}>{data.signal || "HOLD"}</span>
        </div>
        {/* Confluence */}
        <div className="p-4 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
          <span className="text-[9px] uppercase tracking-widest font-bold mb-1" style={{ color: theme.muted }}>Confluence</span>
          <span className="text-[24px] leading-none font-bold tracking-tight font-mono" style={{
            color: finalScore >= confluenceStrong ? theme.green :
              finalScore >= confluenceThreshold ? theme.warn :
                finalScore <= -confluenceStrong ? theme.red :
                  finalScore <= -confluenceThreshold ? theme.warn : theme.muted,
          }}>
            {finalScore > 0 ? "+" : ""}{finalScore.toFixed(0)}
          </span>
          <div className="flex gap-0.5 rounded-full overflow-hidden mt-1.5" style={{ height: 3, width: 50, background: "rgba(255,255,255,0.06)" }}>
            <div className="h-full" style={{
              width: `${Math.min(100, Math.max(0, (finalScore + confluenceMax) / (2 * confluenceMax) * 100))}%`,
              background: finalScore >= 0 ? theme.green : theme.red,
            }} />
          </div>
        </div>
        {/* Confidence (reliability-weighted) */}
        <div className="p-4 flex flex-col justify-center items-center" style={{ background: theme.bg }}>
          <span className="text-[9px] uppercase tracking-widest font-bold mb-1" style={{ color: theme.muted }}>
            Confidence
            <span className="ml-1 font-mono opacity-60">×{reliability.toFixed(2)}</span>
          </span>
          <span className="text-[24px] leading-none font-bold tracking-tight font-mono" style={{ color: theme.accent }}>
            {confidence.toFixed(0)}%
          </span>
          <div className="text-[8px] mt-1" style={{ color: theme.muted }}>
            reliability = {(reliability * 100).toFixed(0)}%
          </div>
        </div>
        {/* Checks summary */}
        <div className="p-4 flex flex-col justify-center" style={{ background: theme.bg }}>
          <span className="text-[9px] uppercase tracking-widest font-bold mb-2" style={{ color: theme.muted }}>Checks</span>
          <div className="flex gap-0.5 rounded-full overflow-hidden mb-2" style={{ height: 6, background: "rgba(255,255,255,0.06)" }}>
            <div className="h-full" style={{ width: `${(gc / tot) * 100}%`, background: theme.green }} />
            <div className="h-full" style={{ width: `${(yc / tot) * 100}%`, background: theme.warn }} />
            <div className="h-full" style={{ width: `${(rc / tot) * 100}%`, background: theme.red }} />
          </div>
          <div className="flex justify-between items-center text-[10px] font-mono font-bold">
            <span style={{ color: theme.green }}>{gc}✓</span>
            <span style={{ color: theme.warn }}>{yc}~</span>
            <span style={{ color: theme.red }}>{rc}✗</span>
          </div>
        </div>
      </div>

      {/* ═══════════════ ACTION BOX ═══════════════ */}
      <div className="p-4 flex flex-col gap-3" style={{ background: `${actionColor}08`, borderTop: `1px solid ${theme.border}`, borderLeft: `4px solid ${actionColor}` }}>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <div className="text-[10px] uppercase tracking-widest font-bold mb-0.5" style={{ color: theme.muted }}>Action</div>
            <div className="text-[22px] font-bold tracking-tight leading-none" style={{ color: actionColor }}>{actionHeadline}</div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {fallbackUsed && (
              <span className="text-[9px] font-mono font-bold px-2 py-1 rounded"
                style={{ background: `${theme.warn}15`, border: `1px solid ${theme.warn}30`, color: theme.warn }}>
                TF FALLBACK → {data.effective_timeframe}
              </span>
            )}
            {gates?.is_ath_zone && (
              <span className="text-[9px] font-mono font-bold px-2 py-1 rounded"
                style={{ background: `${theme.purple}15`, border: `1px solid ${theme.purple}30`, color: theme.purple }}>
                ATH ZONE
              </span>
            )}
            {gates && gates.market_open === false && (
              <span className="text-[9px] font-mono font-bold px-2 py-1 rounded"
                style={{ background: `${theme.muted}15`, border: `1px solid ${theme.border}`, color: theme.muted }}>
                MARKET CLOSED
              </span>
            )}
          </div>
        </div>
        <div className="text-[11px] leading-relaxed" style={{ color: theme.text, opacity: 0.85 }}>{actionBody}</div>

        {entryConditions.length > 0 && (
          <div className="flex flex-col gap-1 pt-2 border-t" style={{ borderColor: theme.border }}>
            <div className="text-[9px] uppercase tracking-widest font-bold" style={{ color: theme.accent }}>Giriş İçin Gerekli</div>
            {entryConditions.map((c, i) => (
              <div key={i} className="text-[10px] flex items-start gap-1.5">
                <span style={{ color: theme.accent }}>→</span>
                <span style={{ color: theme.text, opacity: 0.8 }}>{c}</span>
              </div>
            ))}
          </div>
        )}

        {rejections.length > 0 && (
          <div className="flex flex-col gap-1 pt-2 border-t" style={{ borderColor: theme.border }}>
            <div className="text-[9px] uppercase tracking-widest font-bold" style={{ color: theme.red }}>Risk Faktörleri</div>
            {rejections.map((r, i) => (
              <div key={i} className="text-[10px] flex items-start gap-1.5" style={{ color: theme.red }}>
                <span className="opacity-50">•</span>
                <span className="opacity-90">{r}</span>
              </div>
            ))}
          </div>
        )}

        {gates?.notes && gates.notes.length > 0 && (
          <div className="flex flex-col gap-1 pt-2 border-t" style={{ borderColor: theme.border }}>
            <div className="text-[9px] uppercase tracking-widest font-bold" style={{ color: theme.purple }}>Gates</div>
            {gates.notes.map((n, i) => (
              <div key={i} className="text-[10px]" style={{ color: theme.purple, opacity: 0.9 }}>• {n}</div>
            ))}
          </div>
        )}
      </div>

      {/* ═══════════════ CORE CHECKS (3) ═══════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-[1px]" style={{ background: theme.border }}>
        {coreChecks.map((check) => <CoreCheckCard key={check.id} check={check} />)}
      </div>

      {/* ═══════════════ CONTEXT CHECKS (3) ═══════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-[1px]" style={{ background: theme.border, borderTop: `1px solid ${theme.border}` }}>
        {contextChecks.map((check) => <ContextCheckCard key={check.id} check={check} />)}
      </div>

      {/* ═══════════════ GUARD CHECKS (3) ═══════════════ */}
      <div className="flex flex-col" style={{ background: theme.border, borderTop: `1px solid ${theme.border}` }}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[1px]" style={{ background: theme.border }}>
          {guardChecks.map((check) => <GuardCheckRow key={check.id} check={check} />)}
        </div>
      </div>

      {/* ═══════════════ CONFLUENCE BREAKDOWN (collapsible) ═══════════════ */}
      {confluence && (
        <div style={{ background: theme.bg, borderTop: `1px solid ${theme.border}` }}>
          <button
            onClick={() => setBreakdownOpen((v) => !v)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition">
            <div className="flex items-center gap-2">
              <Gauge className="w-3.5 h-3.5" style={{ color: theme.accent }} />
              <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: theme.text }}>
                Confluence Breakdown
              </span>
              <span className="text-[10px] font-mono" style={{ color: theme.muted }}>
                raw {rawScore > 0 ? "+" : ""}{rawScore.toFixed(1)} + ml {mlBoost > 0 ? "+" : ""}{mlBoost.toFixed(1)} = {finalScore > 0 ? "+" : ""}{finalScore.toFixed(1)}
              </span>
            </div>
            {breakdownOpen ? <ChevronDown className="w-4 h-4" style={{ color: theme.muted }} /> : <ChevronRight className="w-4 h-4" style={{ color: theme.muted }} />}
          </button>
          {breakdownOpen && (
            <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Factor contributions */}
              {confluence.factor_contributions && (
                <div className="p-3 rounded border" style={{ background: theme.surface, borderColor: theme.border }}>
                  <div className="text-[9px] uppercase tracking-widest font-bold mb-2" style={{ color: theme.muted }}>Factor Contributions</div>
                  <div className="flex flex-col gap-1">
                    {Object.entries(confluence.factor_contributions).map(([factor, info]) => {
                      const contrib = info.contribution || 0;
                      const c = contrib > 0 ? theme.green : contrib < 0 ? theme.red : theme.warn;
                      return (
                        <div key={factor} className="flex items-center gap-2 text-[10px]">
                          <span className="w-16 capitalize" style={{ color: theme.muted }}>{factor}</span>
                          <span className="font-mono flex-1 text-right" style={{ color: theme.text }}>
                            w{info.weight} • {info.status}
                          </span>
                          <span className="font-mono font-bold w-10 text-right" style={{ color: c }}>
                            {contrib > 0 ? "+" : ""}{contrib.toFixed(1)}
                          </span>
                          <DirArrow d={info.direction} size={10} />
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {/* Bonuses */}
              <div className="p-3 rounded border" style={{ background: theme.surface, borderColor: theme.border }}>
                <div className="text-[9px] uppercase tracking-widest font-bold mb-2" style={{ color: theme.muted }}>Bonuses & Gates</div>
                {confluence.bonuses && confluence.bonuses.length > 0 ? (
                  <div className="flex flex-col gap-1">
                    {confluence.bonuses.map((b, i) => {
                      const c = b.hard_gate ? theme.purple : b.value > 0 ? theme.green : b.value < 0 ? theme.red : theme.muted;
                      return (
                        <div key={i} className="flex justify-between text-[10px]">
                          <span style={{ color: theme.text, opacity: 0.85 }}>{b.name}</span>
                          <span className="font-mono font-bold" style={{ color: c }}>
                            {b.hard_gate ? "GATE" : (b.value > 0 ? "+" : "") + b.value}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-[10px]" style={{ color: theme.muted }}>Aktif bonus/gate yok.</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════ REBOUND (collapsible) ═══════════════ */}
      {hasRebound && (
        <div style={{ background: theme.bg, borderTop: `1px solid ${theme.border}` }}>
          <button
            onClick={() => setReboundOpen((v) => !v)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition">
            <div className="flex items-center gap-2">
              <PulseIcon size={14} style={{ color: theme.accent }} />
              <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: theme.text }}>
                Rebound Analysis
              </span>
              {reboundLong?.label && (
                <span className="text-[10px] font-mono" style={{ color: theme.muted }}>
                  {reboundLong.label} / {reboundExit?.label || "--"}
                </span>
              )}
            </div>
            {reboundOpen ? <ChevronDown className="w-4 h-4" style={{ color: theme.muted }} /> : <ChevronRight className="w-4 h-4" style={{ color: theme.muted }} />}
          </button>
          {reboundOpen && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-[1px] px-0 pb-0" style={{ background: theme.border }}>
              {reboundLong && (
                <div className="p-4 flex flex-col gap-2" style={{ background: theme.bg }}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: theme.muted }}>Rebound Entry</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded" style={{
                      color: reboundLong.is_high_probability ? theme.green : theme.warn,
                      background: reboundLong.is_high_probability ? `${theme.green}15` : `${theme.warn}15`,
                      border: `1px solid ${reboundLong.is_high_probability ? `${theme.green}30` : `${theme.warn}30`}`,
                    }}>{reboundLong.label || "NO_SIGNAL"}</span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-[22px] font-bold font-mono" style={{ color: reboundLong.is_high_probability ? theme.green : theme.warn }}>
                      {typeof reboundLong.score === "number" ? reboundLong.score.toFixed(0) : "--"}
                    </span>
                    <span className="text-[10px] font-mono" style={{ color: theme.muted }}>
                      / threshold {typeof reboundLong.threshold === "number" ? reboundLong.threshold.toFixed(0) : "--"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                    <div className="rounded px-2 py-1" style={{ background: `${theme.green}08`, border: `1px solid ${theme.green}15` }}>
                      <div style={{ color: theme.muted }}>Bounce</div>
                      <div style={{ color: theme.green }}>{typeof reboundLong.expected_bounce_to === "number" ? reboundLong.expected_bounce_to.toFixed(2) : "--"}</div>
                    </div>
                    <div className="rounded px-2 py-1" style={{ background: `${theme.red}08`, border: `1px solid ${theme.red}15` }}>
                      <div style={{ color: theme.muted }}>Invalid</div>
                      <div style={{ color: theme.red }}>{typeof reboundLong.invalidation === "number" ? reboundLong.invalidation.toFixed(2) : "--"}</div>
                    </div>
                  </div>
                </div>
              )}
              {reboundExit && (
                <div className="p-4 flex flex-col gap-2" style={{ background: theme.bg }}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: theme.muted }}>Rebound Exit</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded" style={{
                      color: reboundExit.is_exit_trigger ? theme.red : theme.warn,
                      background: reboundExit.is_exit_trigger ? `${theme.red}15` : `${theme.warn}15`,
                      border: `1px solid ${reboundExit.is_exit_trigger ? `${theme.red}30` : `${theme.warn}30`}`,
                    }}>{reboundExit.label || "HOLD_REBOUND"}</span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-[22px] font-bold font-mono" style={{ color: reboundExit.is_exit_trigger ? theme.red : theme.warn }}>
                      {typeof reboundExit.score === "number" ? reboundExit.score.toFixed(0) : "--"}
                    </span>
                    <span className="text-[10px] font-mono" style={{ color: theme.muted }}>
                      / threshold {typeof reboundExit.threshold === "number" ? reboundExit.threshold.toFixed(0) : "--"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                    <div className="rounded px-2 py-1" style={{ background: `${theme.red}08`, border: `1px solid ${theme.red}15` }}>
                      <div style={{ color: theme.muted }}>TP Zone</div>
                      <div style={{ color: theme.red }}>{typeof reboundExit.take_profit_zone === "number" ? reboundExit.take_profit_zone.toFixed(2) : "--"}</div>
                    </div>
                    <div className="rounded px-2 py-1" style={{ background: `${theme.warn}08`, border: `1px solid ${theme.warn}15` }}>
                      <div style={{ color: theme.muted }}>Short Inv.</div>
                      <div style={{ color: theme.warn }}>{typeof reboundExit.short_invalidation === "number" ? reboundExit.short_invalidation.toFixed(2) : "--"}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
