"use client";
/**
 * SIGNAL PERFORMANCE — Premium Institutional Fintech Dashboard
 * Bloomberg Terminal meets modern AI startup aesthetic.
 * Design: #0B0F17 dark base, #141C2B cards, #4F8CFF AI accent
 */
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  RotateIcon as RefreshCw,
  AlertIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle,
  CloseIcon as XCircle,
  ActivityIcon as Activity,
  ArrowUpRightIcon as ArrowUpRight,
  ArrowDownRightIcon as ArrowDownRight,
  MinusIcon as Minus,
  ClockIcon as Clock,
  TargetIcon as Target,
  ChevronDownIcon as ChevronDown,
  ChevronUpIcon as ChevronUp,
} from "../ui/CustomIcons";
import { EmelIcon, PulseIcon, LearningIcon, SignalsIcon } from "../ui/CustomIcons";
import {
  useLifecycleDashboard, useActiveSignals, useSignalDetail,
  triggerLifecycleCheck, type ModelStats, type ActiveSignal, type SignalCheck,
} from "../../lib/api/learning";

// ── Institutional Color Palette ─────────────────────────────────────────────
const P = {
  bg: "#0B0F17",
  card: "#141C2B",
  surface: "#111827",
  border: "rgba(255,255,255,0.06)",
  text: "#E6EDF3",
  textSec: "#9AA4B2",
  muted: "#6B7280",
  green: "#16C784",
  red: "#EA3943",
  warn: "#F5A623",
  accent: "#4F8CFF",
  emerald: "#34D399",
  purple: "#A78BFA",
};

const MODEL_THEME: Record<string, { label: string; color: string; Icon: any }> = {
  ml: { label: "ML_Model", color: P.accent, Icon: SignalsIcon },
  pulse1: { label: "Pulse 1 — Algo", color: "#22D3EE", Icon: PulseIcon },
  pulse2: { label: "Pulse 2 — ML", color: P.purple, Icon: SignalsIcon },
  pulse3: { label: "Pulse 3 — MTF", color: P.emerald, Icon: PulseIcon },
  pulse: { label: "Pulse Engine", color: "#22D3EE", Icon: PulseIcon },
  emel: { label: "EMEL 9-Check", color: "#C084FC", Icon: EmelIcon },
  hybrid: { label: "Hybrid", color: P.warn, Icon: LearningIcon },
};

function getTheme(model: string) {
  return MODEL_THEME[model] || MODEL_THEME.ml;
}

function symLabel(sym: string) {
  if (sym === "NDX.INDX") return "NASDAQ";
  if (sym === "GDAXI.INDX") return "DAX";
  if (sym === "CL.COMM") return "US OIL";
  if (sym === "XAUUSD") return "XAUUSD";
  return sym;
}

function symIcon(sym: string): string {
  if (sym === "NDX.INDX") return "📈";
  if (sym === "GDAXI.INDX") return "🏛";
  if (sym === "CL.COMM") return "🛢";
  if (sym === "XAUUSD") return "⭐";
  return "📊";
}

// ── Confidence Ring (Subtle, No Glow) ────────────────────────────────────────
function ConfidenceRing({ rate, color, size = 56 }: { rate: number; color: string; size?: number }) {
  const r = size * 0.38;
  const circ = 2 * Math.PI * r;
  const dash = (rate / 100) * circ;
  const cx = size / 2;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={P.border} strokeWidth={size * 0.07} />
      <circle
        cx={cx} cy={cx} r={r} fill="none"
        stroke={color} strokeWidth={size * 0.07}
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeLinecap="round"
        style={{ transition: "stroke-dasharray 0.8s ease-out" }}
      />
    </svg>
  );
}

// ── Premium Progress Bar (6px, Rounded, Desaturated) ─────────────────────────
function TpBar({ name, rate }: { name: string; rate: number }) {
  const c = rate >= 50 ? P.green : rate >= 25 ? P.warn : P.red;
  return (
    <div className="flex items-center gap-2.5">
      <span
        className="w-7 shrink-0"
        style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.textSec, letterSpacing: "0.02em" }}
      >{name}</span>
      <div className="flex-1 rounded-full overflow-hidden" style={{ height: 6, background: "rgba(255,255,255,0.06)" }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(rate, 100)}%`, background: c, opacity: 0.85 }}
        />
      </div>
      <span
        className="w-10 text-right"
        style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: c }}
      >{rate.toFixed(0)}%</span>
    </div>
  );
}

// ── Mini Sparkline (Institutional: subtle, calm) ─────────────────────────────
function MiniSparkLine({ positive }: { positive: boolean }) {
  // Simple decorative sparkline using random-ish path
  const color = positive ? P.green : P.red;
  const d = positive
    ? "M2 18 L6 14 L10 16 L14 10 L18 12 L22 6 L26 8 L30 4 L34 6 L38 2"
    : "M2 2 L6 6 L10 4 L14 10 L18 8 L22 14 L26 12 L30 16 L34 14 L38 18";
  return (
    <svg width={40} height={20} viewBox="0 0 40 20" fill="none" style={{ opacity: 0.5 }}>
      <path d={d} stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Premium Asset Card (Reference Design Match) ─────────────────────────────
function SymbolCard({ sym, d }: { sym: string; d: any }) {
  const name = symLabel(sym);
  const icon = symIcon(sym);
  const wr = d.win_rate ?? 0;
  const netPips = d.net_pips ?? 0;
  const netPos = netPips >= 0;
  const conf = wr; // use win_rate as proxy for confidence display

  return (
    <div
      className="rounded-xl flex flex-col gap-3 transition-all duration-200 hover:translate-y-[-1px]"
      style={{
        background: P.card,
        border: `1px solid ${P.border}`,
        padding: "20px",
      }}
    >
      {/* Header: Icon + Name + Confidence */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span style={{ fontSize: 16 }}>{icon}</span>
          <span style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: P.text, letterSpacing: "-0.01em" }}>{name}</span>
        </div>
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.muted }}>
          ~ {conf.toFixed(0)}% confidence
        </span>
      </div>

      {/* Main PnL Number + Sparkline */}
      <div className="flex items-end justify-between">
        <span style={{
          fontFamily: FONT,
          fontSize: 32,
          fontWeight: 700,
          letterSpacing: "-0.5px",
          lineHeight: 1,
          color: netPos ? P.green : P.red,
        }}>
          {netPos ? "+" : ""}{netPips.toFixed(1)}p
        </span>
        <MiniSparkLine positive={netPos} />
      </div>

      {/* W / L row */}
      <div className="flex items-center gap-3" style={{ paddingTop: 4, borderTop: `1px solid ${P.border}` }}>
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.green }}>
          {d.completed ?? 0}W
        </span>
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: P.red }}>
          {d.stopped ?? 0}L
        </span>
        <span style={{ fontFamily: FONT, fontSize: 11, color: P.muted, marginLeft: "auto" }}>
          {d.total ?? 0} signals
        </span>
      </div>

      {/* Target Bars (TP1-TP4) */}
      {d.target_rates && Object.keys(d.target_rates).length > 0 && (
        <div className="flex flex-col gap-2" style={{ paddingTop: 8, borderTop: `1px solid ${P.border}` }}>
          {Object.entries(d.target_rates).sort().map(([tp, rate]) => (
            <TpBar key={tp} name={tp} rate={rate as number} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Model Performance Header (Institutional KPI Strip) ───────────────────────
function ModelCard({ model, stats }: { model: string; stats: ModelStats }) {
  const [open, setOpen] = useState(true);
  const theme = getTheme(model);
  const Icon = theme.Icon;
  const wr = stats.win_rate;
  const wrColor = wr >= 55 ? P.green : wr >= 40 ? P.warn : P.red;
  const netPos = stats.net_pips >= 0;

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ background: P.card, border: `1px solid ${P.border}` }}
    >
      {/* ── Model Header ── */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-4 px-5 py-4 transition-colors"
        style={{ borderBottom: open ? `1px solid ${P.border}` : "none" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.015)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        {/* Icon + Label */}
        <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `${theme.color}12`, border: `1px solid ${theme.color}20` }}>
          <Icon className="w-5 h-5" style={{ color: theme.color, width: 20, height: 20 }} />
        </div>
        <div className="text-left flex-1 min-w-0">
          <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: P.text, letterSpacing: "-0.01em" }}>{theme.label}</p>
          <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 400, color: P.muted }}>
            {stats.total_signals} signals · All sessions rsct
          </p>
        </div>

        {/* Win Rate Ring */}
        <div className="relative shrink-0">
          <ConfidenceRing rate={wr} color={wrColor} size={48} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 700, color: wrColor }}>{wr}%</span>
          </div>
        </div>

        {/* KPI: Total Net */}
        <div className="text-right shrink-0 hidden sm:flex flex-col items-end">
          <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.muted, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>
            TOTAL NET
          </span>
          <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: netPos ? P.green : P.red, letterSpacing: "-0.5px" }}>
            {netPos ? "+" : ""}{stats.net_pips.toFixed(1)}p
          </span>
        </div>

        {/* KPI: R/R */}
        <div className="text-right shrink-0 hidden md:flex flex-col items-end">
          <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.muted, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>
            R/R
          </span>
          <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: stats.risk_reward >= 1.5 ? P.green : P.warn, letterSpacing: "-0.3px" }}>
            {stats.risk_reward.toFixed(2)}
          </span>
        </div>

        {open ? <ChevronUp className="w-4 h-4 shrink-0" style={{ color: P.muted }} /> : <ChevronDown className="w-4 h-4 shrink-0" style={{ color: P.muted }} />}
      </button>

      {/* ── Expanded Content ── */}
      {open && (
        <div className="p-5 space-y-5">

          {/* KPI Strip: Total Profit / Total Loss / Best Signal */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "TOTAL PROFIT", val: `+${stats.total_profit_pips ?? stats.avg_profit_pips}p`, color: P.green },
              { label: "TOTAL LOSS", val: `-${stats.total_loss_pips ?? stats.avg_loss_pips}p`, color: P.red },
              { label: "AVG PROFIT", val: `+${stats.avg_profit_pips}p`, color: P.green },
            ].map(s => (
              <div key={s.label} className="rounded-lg text-center" style={{ background: P.surface, padding: "14px 12px", border: `1px solid ${P.border}` }}>
                <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 6 }}>
                  {s.label}
                </p>
                <p style={{ fontFamily: FONT, fontSize: 20, fontWeight: 700, color: s.color, letterSpacing: "-0.5px" }}>
                  {s.val}
                </p>
              </div>
            ))}
          </div>

          {/* Overall Target Rates */}
          {Object.keys(stats.target_rates).length > 0 && (
            <div className="space-y-2.5">
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" as const }}>
                Overall Target Hit Rates
              </p>
              <div className="rounded-lg" style={{ background: P.surface, padding: 16, border: `1px solid ${P.border}` }}>
                <div className="flex flex-col gap-3">
                  {Object.entries(stats.target_rates).sort().map(([tp, rate]) => (
                    <TpBar key={tp} name={tp} rate={rate} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Per-Symbol Asset Cards (Grid - Reference Design) */}
          {Object.keys(stats.symbols).length > 0 && (
            <div>
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 12 }}>
                Per Asset Performance
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(stats.symbols).map(([sym, d]) => (
                  <SymbolCard key={sym} sym={sym} d={d} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Active Signal Card (Premium, Calm) ──────────────────────────────────────
function ActiveSignalCard({ signal, onSelect }: { signal: ActiveSignal; onSelect: (id: string) => void }) {
  const isBuy = signal.ml_direction === "BUY";
  const isSell = signal.ml_direction === "SELL";
  const dirColor = isBuy ? P.green : isSell ? P.red : P.warn;
  const theme = getTheme(signal.model_type || "ml");

  const age = Math.round((Date.now() - new Date(signal.created_at).getTime()) / 60000);
  const targetsHit = signal.targets_hit ? Object.values(signal.targets_hit).filter(Boolean).length : 0;
  const totalTargets = signal.targets ? Object.keys(signal.targets).length : 0;
  const profitPos = (signal.highest_profit_pips ?? 0) > 0;

  return (
    <button
      onClick={() => onSelect(signal.id)}
      className="w-full text-left rounded-xl overflow-hidden transition-all duration-200"
      style={{
        background: P.card,
        border: `1px solid ${P.border}`,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
        e.currentTarget.style.transform = "translateY(-1px)";
        e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.3)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = P.border;
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div className="flex items-center gap-0">
        {/* Direction accent bar */}
        <div className="w-1 self-stretch shrink-0 rounded-l-xl" style={{ background: dirColor, opacity: 0.7 }} />

        <div className="flex-1 px-4 py-3 flex items-center gap-3">
          {/* Direction icon */}
          <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `${dirColor}10`, border: `1px solid ${dirColor}18` }}>
            {isBuy ? <ArrowUpRight className="w-4 h-4" style={{ color: dirColor }} />
              : isSell ? <ArrowDownRight className="w-4 h-4" style={{ color: dirColor }} />
                : <Minus className="w-4 h-4" style={{ color: dirColor }} />}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: P.text }}>{symLabel(signal.symbol)}</span>
              <span
                className="px-2 py-0.5 rounded"
                style={{ fontFamily: FONT, fontSize: 11, fontWeight: 600, color: dirColor, background: `${dirColor}10`, border: `1px solid ${dirColor}18` }}
              >{signal.ml_direction}</span>
              <span
                className="px-1.5 py-0.5 rounded"
                style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: theme.color, background: `${theme.color}10` }}
              >{signal.model_type}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>{age}m ago</span>
              <span style={{ color: P.muted }}>·</span>
              <span style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>Entry {signal.ml_entry_price?.toFixed(2)}</span>
              <span style={{ color: P.muted }}>·</span>
              <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: (signal.ml_confidence ?? 0) >= 60 ? P.green : P.warn }}>
                {signal.ml_confidence?.toFixed(0)}% conf
              </span>
            </div>
          </div>

          {/* Right: Profit + Targets */}
          <div className="shrink-0 flex flex-col items-end gap-1.5">
            <span style={{
              fontFamily: FONT, fontSize: 16, fontWeight: 700,
              color: profitPos ? P.green : P.muted,
              letterSpacing: "-0.3px"
            }}>
              {profitPos ? "+" : ""}{(signal.highest_profit_pips ?? 0).toFixed(1)}p
            </span>
            <div className="flex items-center gap-1">
              {Array.from({ length: totalTargets }).map((_, i) => (
                <div key={i} className="rounded-sm" style={{
                  width: 10, height: 10,
                  background: i < targetsHit ? P.green : "rgba(255,255,255,0.06)",
                  border: i < targetsHit ? `1px solid ${P.green}50` : `1px solid ${P.border}`,
                }} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}

// ── Sparkline SVG (for modal) ────────────────────────────────────────────────
function SparkLine({ checks, direction }: { checks: SignalCheck[]; direction: string }) {
  if (!checks || checks.length < 2) return null;
  const values = checks.map(c => c.profit_pips || 0);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;
  const w = 280; const h = 60; const pad = 4;
  const pts = values.map((v, i) => {
    const x = pad + ((w - 2 * pad) * i) / (values.length - 1);
    const y = h - pad - ((v - minVal) / range) * (h - 2 * pad);
    return `${x},${y}`;
  });
  const last = values[values.length - 1];
  const positive = last >= 0;
  const lineColor = positive ? P.green : P.red;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.15" />
          <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`M${pts[0]} ${pts.slice(1).map(p => `L${p}`).join(" ")} L${w - pad},${h - pad} L${pad},${h - pad} Z`}
        fill="url(#sparkGrad)" />
      <polyline points={pts.join(" ")} fill="none" stroke={lineColor} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
      <line x1={pad} y1={h / 2} x2={w - pad} y2={h / 2}
        stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} strokeDasharray="4 2" />
    </svg>
  );
}

// ── Arc Target Indicator ─────────────────────────────────────────────────────
function ArcTarget({ name, hit, pips }: { name: string; hit: boolean; pips: any }) {
  const color = hit ? P.green : P.muted;
  return (
    <div className="flex flex-col items-center gap-1.5"
      style={{ opacity: hit ? 1 : 0.5 }}>
      <div className="rounded-lg flex items-center justify-center" style={{
        width: 36, height: 36,
        background: hit ? `${P.green}12` : "rgba(255,255,255,0.03)",
        border: `1px solid ${hit ? `${P.green}30` : P.border}`,
      }}>
        {hit
          ? <CheckCircle className="w-4 h-4" style={{ color: P.green }} />
          : <Target className="w-4 h-4" style={{ color: P.muted }} />}
      </div>
      <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, color }}>{name}</span>
      <span style={{ fontFamily: FONT, fontSize: 9, color: P.muted }}>{pips}p</span>
    </div>
  );
}

// ── Signal Detail Modal (Premium) ────────────────────────────────────────────
function SignalDetailModal({ signalId, onClose }: { signalId: string; onClose: () => void }) {
  const overlayRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const { data, isLoading } = useSignalDetail(signalId);

  if (isLoading || !data) return (
    <div className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}>
      <RefreshCw className="w-6 h-6 animate-spin" style={{ color: P.accent }} />
    </div>
  );

  const sig = data.signal;
  if (!sig) return null;
  const isBuy = sig.ml_direction === "BUY";
  const dirColor = isBuy ? P.green : P.red;
  const theme = getTheme(sig.model_type || "ml");
  const checks = data.checks || [];
  const failure = data.failure;

  const targetsConfig = sig.targets || {};
  const targetsHit = sig.targets_hit || {};

  return (
    <div ref={overlayRef} className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}>
      <div className="w-full max-w-lg rounded-xl overflow-hidden"
        style={{ background: P.card, border: `1px solid ${P.border}`, maxHeight: "85vh", overflowY: "auto" }}>

        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ background: `${dirColor}10`, border: `1px solid ${dirColor}20` }}>
              {isBuy
                ? <ArrowUpRight className="w-5 h-5" style={{ color: dirColor }} />
                : <ArrowDownRight className="w-5 h-5" style={{ color: dirColor }} />}
            </div>
            <div>
              <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: P.text }}>
                {symLabel(sig.symbol)} · {sig.ml_direction}
              </p>
              <p style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>
                {sig.model_type} · {sig.ml_confidence?.toFixed(0)}% confidence
              </p>
            </div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
            style={{ background: "rgba(255,255,255,0.03)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}>
            <XCircle className="w-4 h-4" style={{ color: P.muted }} />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Entry + Status */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg" style={{ background: P.surface, padding: "12px", border: `1px solid ${P.border}` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 4 }}>Entry</p>
              <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: P.text }}>{sig.ml_entry_price?.toFixed(2)}</p>
            </div>
            <div className="rounded-lg" style={{ background: P.surface, padding: "12px", border: `1px solid ${P.border}` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 4 }}>Best P/L</p>
              <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: (sig.highest_profit_pips ?? 0) > 0 ? P.green : P.muted }}>
                {(sig.highest_profit_pips ?? 0) > 0 ? "+" : ""}{(sig.highest_profit_pips ?? 0).toFixed(1)}p
              </p>
            </div>
            <div className="rounded-lg" style={{ background: P.surface, padding: "12px", border: `1px solid ${P.border}` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 4 }}>Status</p>
              <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: sig.status === "completed" ? P.green : sig.status === "stopped" ? P.red : P.warn, textTransform: "capitalize" as const }}>
                {sig.status}
              </p>
            </div>
          </div>

          {/* Target Arc */}
          <div className="flex items-center justify-center gap-6 py-2">
            {Object.entries(targetsConfig).sort().map(([tp, pips]) => (
              <ArcTarget key={tp} name={tp} hit={!!targetsHit[tp]} pips={pips} />
            ))}
          </div>

          {/* Sparkline */}
          {checks.length >= 2 && (
            <div className="rounded-lg" style={{ background: P.surface, padding: 16, border: `1px solid ${P.border}` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 8 }}>P/L Timeline</p>
              <SparkLine checks={checks} direction={sig.ml_direction} />
            </div>
          )}

          {/* Failure Autopsy */}
          {failure && (
            <div className="rounded-lg" style={{ background: `${P.red}06`, padding: 14, border: `1px solid ${P.red}15` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.red, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 6 }}>
                Failure Autopsy
              </p>
              <p style={{ fontFamily: FONT, fontSize: 12, color: P.textSec, lineHeight: 1.5 }}>
                {failure.reason || "Market moved against signal direction."}
              </p>
              {failure.max_adverse_pips !== undefined && (
                <p style={{ fontFamily: FONT, fontSize: 11, color: P.red, marginTop: 4 }}>
                  Max adverse: -{Math.abs(failure.max_adverse_pips).toFixed(1)}p
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT — SIGNAL PERFORMANCE DASHBOARD
// ════════════════════════════════════════════════════════════════════════════
export default function LearningDashboardV2() {
  const [days, setDays] = useState(30);
  const [checking, setChecking] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);

  const { data: dashboard, isLoading, refetch } = useLifecycleDashboard(days);
  const { data: activeData, refetch: refetchActive } = useActiveSignals();

  const handleGlobalRefresh = useCallback(() => { refetch(); refetchActive(); }, [refetch, refetchActive]);

  useEffect(() => {
    window.addEventListener("dashboard-refresh", handleGlobalRefresh);
    return () => window.removeEventListener("dashboard-refresh", handleGlobalRefresh);
  }, [handleGlobalRefresh]);

  const handleCheck = async () => {
    setChecking(true);
    try { await triggerLifecycleCheck(); refetch(); refetchActive(); }
    catch (e) { console.error(e); }
    finally { setChecking(false); }
  };

  const models = dashboard?.model_stats || {};
  const failBreak = dashboard?.failure_breakdown || {};
  const activeSignals = activeData?.signals || [];

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        fontFamily: FONT,
        background: P.bg,
        border: `1px solid ${P.border}`,
      }}
    >
      {/* ── HEADER ── */}
      <div className="flex items-center justify-between px-5 py-4" style={{
        background: P.surface,
        borderBottom: `1px solid ${P.border}`,
      }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: `${P.accent}12`, border: `1px solid ${P.accent}20` }}>
            <LearningIcon size={18} style={{ color: P.accent }} />
          </div>
          <div>
            <h2 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text, letterSpacing: "-0.01em" }}>
              Signal Performance
            </h2>
            <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 400, color: P.muted }}>
              Learning Engine · Lifecycle Tracker
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {dashboard?.active_signals !== undefined && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg"
              style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.green, background: `${P.green}08`, border: `1px solid ${P.green}15` }}>
              <Activity className="w-3 h-3" style={{ color: P.green }} />
              {dashboard.active_signals} active
            </span>
          )}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg appearance-none cursor-pointer"
            style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, padding: "6px 10px", backgroundColor: P.surface, color: P.textSec, border: `1px solid ${P.border}` }}>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
          <button onClick={handleCheck}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all duration-150"
            style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, background: `${P.accent}10`, border: `1px solid ${P.accent}20`, color: P.accent }}
            onMouseEnter={(e) => (e.currentTarget.style.background = `${P.accent}18`)}
            onMouseLeave={(e) => (e.currentTarget.style.background = `${P.accent}10`)}>
            <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
            Check
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-16 flex items-center justify-center" style={{ background: P.bg }}>
          <RefreshCw className="w-5 h-5 animate-spin" style={{ color: P.accent }} />
        </div>
      ) : (
        <div className="p-5 space-y-5" style={{ background: P.bg }}>

          {/* ── ACTIVE SIGNALS ── */}
          {activeSignals.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: P.green }} />
                <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" as const }}>
                  Active Signals ({activeSignals.length})
                </p>
              </div>
              <div className="space-y-2">
                {activeSignals.map((sig) => (
                  <ActiveSignalCard key={sig.id} signal={sig} onSelect={setSelectedSignal} />
                ))}
              </div>
            </div>
          )}

          {/* ── MODEL PERFORMANCE ── */}
          {Object.keys(models).length > 0 ? (
            <div>
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 12 }}>
                Model Performance
              </p>
              <div className="space-y-3">
                {Object.entries(models)
                  .sort(([a], [b]) => {
                    const order: Record<string, number> = { ml: 0, pulse1: 1, pulse2: 2, pulse3: 3, pulse: 3.5, emel: 4, hybrid: 5 };
                    return (order[a] ?? 99) - (order[b] ?? 99);
                  })
                  .map(([model, stats]) => (
                    <ModelCard key={model} model={model} stats={stats} />
                  ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <EmelIcon size={36} style={{ color: "rgba(255,255,255,0.06)" }} />
              <p style={{ fontFamily: FONT, fontSize: 14, color: P.muted, marginTop: 12 }}>No signal data for this period.</p>
              <p style={{ fontFamily: FONT, fontSize: 12, color: P.muted, opacity: 0.5, marginTop: 4 }}>
                Signals appear as panels generate BUY/SELL decisions.
              </p>
            </div>
          )}

          {/* ── FAILURE BREAKDOWN ── */}
          {Object.keys(failBreak).length > 0 && (
            <div className="rounded-lg" style={{ background: `${P.red}05`, padding: 16, border: `1px solid ${P.red}10` }}>
              <p className="flex items-center gap-1.5" style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: `${P.red}90`, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 10 }}>
                <AlertTriangle className="w-3.5 h-3.5" style={{ color: P.red }} />
                Failure Breakdown
              </p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(failBreak).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                    style={{ background: `${P.red}08`, border: `1px solid ${P.red}12` }}>
                    <span style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>{type.replace(/_/g, " ")}</span>
                    <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.red }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── SIGNAL DETAIL MODAL ── */}
      {selectedSignal && (
        <SignalDetailModal signalId={selectedSignal} onClose={() => setSelectedSignal(null)} />
      )}
    </div>
  );
}
