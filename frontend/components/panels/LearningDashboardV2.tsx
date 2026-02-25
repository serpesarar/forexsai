"use client";

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

// ── Colors ──────────────────────────────────────────────────────────────────
const C = {
  g: "#00ff88",
  r: "#ff3366",
  y: "#fbbf24",
  p: "#c084fc",
  cyan: "#22d3ee",
  blue: "#60a5fa",
  orange: "#fb923c",
};

const MODEL_THEME: Record<string, { label: string; color: string; Icon: any }> = {
  ml: { label: "ML Model", color: C.blue, Icon: SignalsIcon },
  pulse: { label: "Pulse Engine", color: C.cyan, Icon: PulseIcon },
  pulse1: { label: "Pulse 1 — Algo", color: C.cyan, Icon: PulseIcon },
  pulse2: { label: "Pulse 2 — ML", color: "#a78bfa", Icon: SignalsIcon },
  pulse3: { label: "Pulse 3 — MTF", color: "#34d399", Icon: PulseIcon },
  emel: { label: "EMEL 9-Check", color: C.p, Icon: EmelIcon },
  hybrid: { label: "Hybrid", color: C.y, Icon: LearningIcon },
};

function getTheme(model: string) {
  return MODEL_THEME[model] || MODEL_THEME.ml;
}

function symLabel(sym: string) {
  if (sym === "NDX.INDX") return "NASDAQ";
  if (sym === "GDAXI.INDX") return "DAX";
  if (sym === "CL.COMM") return "US Oil";
  if (sym === "XAUUSD") return "XAUUSD";
  return sym;
}

function symColor(sym: string): string {
  if (sym === "NDX.INDX") return C.blue;
  if (sym === "GDAXI.INDX") return C.orange;
  if (sym === "CL.COMM") return C.y;
  if (sym === "XAUUSD") return "#fde68a";
  return C.p;
}

// ── SVG Donut Gauge ──────────────────────────────────────────────────────────
function DonutGauge({ rate, color, size = 80 }: { rate: number; color: string; size?: number }) {
  const r = size * 0.38;
  const circ = 2 * Math.PI * r;
  const dash = (rate / 100) * circ;
  const cx = size / 2;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={cx} cy={cx} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={size * 0.09} />
      <circle
        cx={cx} cy={cx} r={r} fill="none"
        stroke={color} strokeWidth={size * 0.09}
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 4px ${color}60)`, transition: "stroke-dasharray 1s ease" }}
      />
    </svg>
  );
}

// ── Slim Progress Bar ─────────────────────────────────────────────────────────
function TpBar({ name, rate, color }: { name: string; rate: number; color: string }) {
  const c = rate >= 55 ? C.g : rate >= 30 ? C.y : C.r;
  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] font-mono w-6 shrink-0" style={{ color: "rgba(255,255,255,0.35)" }}>{name}</span>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(rate, 100)}%`, background: c, boxShadow: `0 0 4px ${c}50` }}
        />
      </div>
      <span className="text-[9px] font-mono w-8 text-right font-bold" style={{ color: c }}>{rate.toFixed(0)}%</span>
    </div>
  );
}

// ── Symbol Stat Card (inside ModelCard) ──────────────────────────────────────
function SymbolCard({ sym, d, modelColor }: { sym: string; d: any; modelColor: string }) {
  const name = symLabel(sym);
  const sc = symColor(sym);
  const wr = d.win_rate ?? 0;
  const wrColor = wr >= 55 ? C.g : wr >= 40 ? C.y : C.r;
  const netPos = (d.net_pips ?? 0) >= 0;

  return (
    <div
      className="rounded-xl p-3 flex flex-col gap-2"
      style={{ background: `${sc}06`, border: `1px solid ${sc}18` }}
    >
      {/* Symbol Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: sc, boxShadow: `0 0 6px ${sc}` }} />
          <span className="text-[12px] font-black font-mono" style={{ color: sc }}>{name}</span>
          <span className="text-[9px] text-white/25 font-mono">{d.total}sig</span>
        </div>
        {/* Mini donut */}
        <div className="relative">
          <DonutGauge rate={wr} color={wrColor} size={44} />
          <div className="absolute inset-0 flex items-center justify-center" style={{ transform: "rotate(0deg)" }}>
            <span className="text-[9px] font-black font-mono" style={{ color: wrColor }}>{wr}%</span>
          </div>
        </div>
      </div>

      {/* W / L / Exp pills */}
      <div className="flex gap-1.5 flex-wrap">
        <span className="px-2 py-0.5 rounded-md text-[9px] font-bold font-mono inline-flex items-center gap-1"
          style={{ background: `${C.g}12`, border: `1px solid ${C.g}25`, color: C.g }}>
          ✓ {d.completed}W
        </span>
        <span className="px-2 py-0.5 rounded-md text-[9px] font-bold font-mono inline-flex items-center gap-1"
          style={{ background: `${C.r}12`, border: `1px solid ${C.r}25`, color: C.r }}>
          ✗ {d.stopped}L
        </span>
        {d.expired !== undefined && d.expired > 0 && (
          <span className="px-2 py-0.5 rounded-md text-[9px] font-bold font-mono inline-flex items-center gap-1"
            style={{ background: "rgba(251,191,36,0.1)", border: "1px solid rgba(251,191,36,0.2)", color: C.y }}>
            ⌛ {d.expired}Exp
          </span>
        )}
        {d.net_pips !== undefined && (
          <span className="px-2 py-0.5 rounded-md text-[9px] font-bold font-mono ml-auto"
            style={{ color: netPos ? C.g : C.r, background: netPos ? `${C.g}10` : `${C.r}10`, border: `1px solid ${netPos ? C.g : C.r}20` }}>
            {netPos ? "+" : ""}{d.net_pips}p
          </span>
        )}
      </div>

      {/* Target bars */}
      {d.target_rates && Object.keys(d.target_rates).length > 0 && (
        <div className="space-y-1 pt-1" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          {Object.entries(d.target_rates).sort().map(([tp, rate]) => (
            <TpBar key={tp} name={tp} rate={rate as number} color={sc} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Model Performance Card (collapsible) ─────────────────────────────────────
function ModelCard({ model, stats }: { model: string; stats: ModelStats }) {
  const [open, setOpen] = useState(false);
  const theme = getTheme(model);
  const Icon = theme.Icon;
  const wr = stats.win_rate;
  const wrColor = wr >= 55 ? C.g : wr >= 40 ? C.y : C.r;
  const netPos = stats.net_pips >= 0;

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${theme.color}18` }}>
      {/* Header row — always visible */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3.5 hover:bg-white/[0.015] transition-colors"
      >
        {/* Model icon + name */}
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: `${theme.color}15`, border: `1px solid ${theme.color}30` }}>
          <Icon className="w-4.5 h-4.5" style={{ color: theme.color, width: 18, height: 18 }} />
        </div>
        <div className="text-left flex-1 min-w-0">
          <p className="text-[12px] font-extrabold font-mono" style={{ color: theme.color }}>{theme.label}</p>
          <p className="text-[9px] text-white/25 font-mono">{stats.total_signals} signals · {stats.completed}W {stats.stopped}L {stats.expired}Exp</p>
        </div>

        {/* Win Rate donut */}
        <div className="relative shrink-0">
          <DonutGauge rate={wr} color={wrColor} size={52} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[10px] font-black font-mono" style={{ color: wrColor }}>{wr}%</span>
          </div>
        </div>

        {/* Net Pips */}
        <div className="text-right shrink-0 hidden sm:block">
          <p className="text-[8px] uppercase tracking-widest text-white/25 mb-0.5">Net Pips</p>
          <p className="text-[14px] font-black font-mono" style={{ color: netPos ? C.g : C.r }}>
            {netPos ? "+" : ""}{stats.net_pips}
          </p>
        </div>

        {/* R/R */}
        <div className="text-right shrink-0 hidden md:block">
          <p className="text-[8px] uppercase tracking-widest text-white/25 mb-0.5">R/R</p>
          <p className="text-[14px] font-black font-mono" style={{ color: stats.risk_reward >= 1.5 ? C.g : C.y }}>
            {stats.risk_reward.toFixed(1)}
          </p>
        </div>

        {open ? <ChevronUp className="w-4 h-4 text-white/25 shrink-0" /> : <ChevronDown className="w-4 h-4 text-white/25 shrink-0" />}
      </button>

      {/* Expanded: global target rates + per-symbol cards */}
      {open && (
        <div className="px-4 pb-4 space-y-4" style={{ borderTop: `1px solid ${theme.color}12` }}>

          {/* Global P/L strip */}
          <div className="grid grid-cols-3 gap-2 pt-3">
            {[
              { label: "Avg Profit", val: `+${stats.avg_profit_pips}p`, color: C.g },
              { label: "Avg Loss", val: `-${stats.avg_loss_pips}p`, color: C.r },
              { label: "Total Net", val: `${netPos ? "+" : ""}${stats.net_pips}p`, color: netPos ? C.g : C.r },
            ].map(s => (
              <div key={s.label} className="rounded-xl p-2.5 text-center" style={{ background: `${s.color}08`, border: `1px solid ${s.color}15` }}>
                <p className="text-[7px] uppercase tracking-widest text-white/25 mb-0.5">{s.label}</p>
                <p className="text-[13px] font-black font-mono" style={{ color: s.color }}>{s.val}</p>
              </div>
            ))}
          </div>

          {/* Global target bars */}
          {Object.keys(stats.target_rates).length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[8px] uppercase tracking-widest text-white/25">Overall Target Hit Rates</p>
              {Object.entries(stats.target_rates).sort().map(([tp, rate]) => (
                <TpBar key={tp} name={tp} rate={rate} color={theme.color} />
              ))}
            </div>
          )}

          {/* Per-symbol grid */}
          {Object.keys(stats.symbols).length > 0 && (
            <div>
              <p className="text-[8px] uppercase tracking-widest text-white/25 mb-2">Per Symbol</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(stats.symbols).map(([sym, d]) => (
                  <SymbolCard key={sym} sym={sym} d={d} modelColor={theme.color} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Active Signal Card ────────────────────────────────────────────────────────
function ActiveSignalCard({ signal, onSelect }: { signal: ActiveSignal; onSelect: (id: string) => void }) {
  const isBuy = signal.ml_direction === "BUY";
  const isSell = signal.ml_direction === "SELL";
  const dirColor = isBuy ? C.g : isSell ? C.r : C.y;
  const sc = symColor(signal.symbol);
  const theme = getTheme(signal.model_type || "ml");

  const age = Math.round((Date.now() - new Date(signal.created_at).getTime()) / 60000);
  const targetsHit = signal.targets_hit ? Object.values(signal.targets_hit).filter(Boolean).length : 0;
  const totalTargets = signal.targets ? Object.keys(signal.targets).length : 0;
  const profitPos = (signal.highest_profit_pips ?? 0) > 0;

  return (
    <button
      onClick={() => onSelect(signal.id)}
      className="w-full text-left rounded-2xl overflow-hidden transition-all duration-200 hover:scale-[1.01] hover:brightness-110 active:scale-[0.99]"
      style={{
        background: `linear-gradient(135deg, ${sc}0A 0%, rgba(8,10,25,0.9) 100%)`,
        border: `1px solid ${sc}25`,
        boxShadow: `0 4px 24px ${sc}08`,
      }}
    >
      <div className="flex items-stretch gap-0">
        {/* Left accent bar */}
        <div className="w-1 rounded-l-2xl shrink-0 self-stretch" style={{ background: `linear-gradient(180deg, ${dirColor}, ${sc})` }} />

        <div className="flex-1 p-3 flex items-center gap-3">
          {/* Live pulse dot */}
          <div className="relative shrink-0">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: `${dirColor}15`, border: `1px solid ${dirColor}30` }}>
              {isBuy ? <ArrowUpRight className="w-4 h-4" style={{ color: dirColor }} />
                : isSell ? <ArrowDownRight className="w-4 h-4" style={{ color: dirColor }} />
                  : <Minus className="w-4 h-4" style={{ color: dirColor }} />}
            </div>
            {/* Pulsing dot */}
            <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
                style={{ background: dirColor }} />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5"
                style={{ background: dirColor }} />
            </span>
          </div>

          {/* Symbol + info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[14px] font-black font-mono" style={{ color: sc }}>{symLabel(signal.symbol)}</span>
              <span className="text-[11px] font-extrabold font-mono px-2 py-0.5 rounded-lg"
                style={{ color: dirColor, background: `${dirColor}15`, border: `1px solid ${dirColor}30` }}>
                {signal.ml_direction}
              </span>
              <span className="text-[9px] px-1.5 py-0.5 rounded-md font-mono"
                style={{ color: theme.color, background: `${theme.color}12`, border: `1px solid ${theme.color}20` }}>
                {signal.model_type}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <span className="text-[9px] font-mono text-white/30">{age}m ago</span>
              <span className="text-[9px] font-mono text-white/20">·</span>
              <span className="text-[9px] font-mono text-white/30">Entry {signal.ml_entry_price?.toFixed(2)}</span>
              <span className="text-[9px] font-mono text-white/20">·</span>
              <span className="text-[9px] font-mono" style={{ color: signal.ml_confidence >= 60 ? C.g : C.y }}>
                {signal.ml_confidence?.toFixed(0)}% conf
              </span>
            </div>
          </div>

          {/* Right stats */}
          <div className="shrink-0 flex flex-col items-end gap-1">
            {/* Max profit */}
            <span className="text-[13px] font-black font-mono" style={{ color: profitPos ? C.g : "rgba(255,255,255,0.3)" }}>
              {profitPos ? "+" : ""}{(signal.highest_profit_pips ?? 0).toFixed(1)}p
            </span>
            {/* Targets */}
            <div className="flex items-center gap-1">
              {Array.from({ length: totalTargets }).map((_, i) => (
                <div key={i} className="w-3 h-3 rounded-sm"
                  style={{
                    background: i < targetsHit ? C.g : "rgba(255,255,255,0.08)",
                    border: i < targetsHit ? `1px solid ${C.g}50` : "1px solid rgba(255,255,255,0.1)",
                    boxShadow: i < targetsHit ? `0 0 4px ${C.g}60` : "none",
                  }} />
              ))}
              {totalTargets === 0 && <span className="text-[9px] text-white/20 font-mono">—</span>}
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}

// ── Sparkline SVG (for modal fiyat çizelgesi) ────────────────────────────────
function SparkLine({ checks, direction }: { checks: SignalCheck[]; direction: string }) {
  if (checks.length < 2) return null;
  const profits = checks.map(c => c.profit_pips ?? 0);
  const min = Math.min(...profits, 0);
  const max = Math.max(...profits, 0);
  const range = max - min || 1;
  const W = 320, H = 60;
  const pts = profits.map((v, i) => {
    const x = (i / (profits.length - 1)) * W;
    const y = H - ((v - min) / range) * H;
    return `${x},${y}`;
  }).join(" ");

  const zeroY = H - ((0 - min) / range) * H;
  const strokeColor = direction === "BUY" ? "#00ff88" : "#ff3366";
  const fillId = `spark-fill-${direction}`;

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height: 60 }}>
      <defs>
        <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={strokeColor} stopOpacity="0.25" />
          <stop offset="100%" stopColor={strokeColor} stopOpacity="0.01" />
        </linearGradient>
      </defs>
      {/* Zero line */}
      <line x1="0" y1={zeroY} x2={W} y2={zeroY} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
      {/* Fill area */}
      <polyline
        points={[`0,${zeroY}`, ...pts.split(" ").map(p => p), `${W},${zeroY}`].join(" ")}
        fill={`url(#${fillId})`}
        stroke="none"
      />
      {/* Price line */}
      <polyline points={pts} fill="none" stroke={strokeColor} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round"
        style={{ filter: `drop-shadow(0 0 3px ${strokeColor}60)` }} />
    </svg>
  );
}

// ── Arc Target Indicator ──────────────────────────────────────────────────────
function ArcTarget({ name, hit, pips }: { name: string; hit: boolean; pips: any }) {
  return (
    <div className="flex flex-col items-center gap-1 relative">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300"
        style={{
          background: hit ? `${C.g}15` : "rgba(255,255,255,0.03)",
          border: `2px solid ${hit ? C.g : "rgba(255,255,255,0.08)"}`,
          boxShadow: hit ? `0 0 12px ${C.g}40, inset 0 0 8px ${C.g}15` : "none",
        }}>
        {hit
          ? <CheckCircle className="w-5 h-5" style={{ color: C.g }} />
          : <XCircle className="w-5 h-5" style={{ color: "rgba(255,255,255,0.2)" }} />}
      </div>
      <p className="text-[8px] font-bold font-mono" style={{ color: hit ? C.g : "rgba(255,255,255,0.25)" }}>{name}</p>
      {pips && <p className="text-[7px] font-mono text-white/20">{pips}p</p>}
    </div>
  );
}

// ── Signal Detail Modal (Sinematik) ───────────────────────────────────────────
function SignalDetailModal({ signalId, onClose }: { signalId: string; onClose: () => void }) {
  const { data, isLoading } = useSignalDetail(signalId);
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (isLoading) return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(8px)" }}>
      <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: "rgba(8,10,25,0.9)", border: "1px solid rgba(192,132,252,0.2)" }}>
        <RefreshCw className="w-6 h-6 animate-spin" style={{ color: C.p }} />
      </div>
    </div>
  );

  if (!data || data.error) return null;

  const sig = data.signal;
  const checks: SignalCheck[] = data.checks || [];
  const failure = data.failure;
  const isBuy = sig.ml_direction === "BUY";
  const dirColor = isBuy ? C.g : C.r;
  const sc = symColor(sig.symbol);
  const netProfit = checks.length > 0 ? checks[checks.length - 1].profit_pips : sig.highest_profit_pips;
  const profitPos = (netProfit ?? 0) >= 0;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      style={{ background: "rgba(0,0,0,0.8)", backdropFilter: "blur(12px)" }}
      onClick={onClose}
    >
      <div
        className="w-full sm:max-w-xl max-h-[92vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "linear-gradient(180deg, rgba(12,14,35,0.99) 0%, rgba(8,10,25,0.99) 100%)",
          border: `1px solid ${sc}20`,
          boxShadow: `0 -8px 60px ${sc}10, 0 0 120px rgba(0,0,0,0.5)`,
        }}
      >
        {/* ── CINEMATIC HEADER ── */}
        <div className="relative px-5 py-4 overflow-hidden" style={{
          background: `linear-gradient(135deg, ${sc}12 0%, ${dirColor}08 100%)`,
          borderBottom: `1px solid rgba(255,255,255,0.05)`,
        }}>
          {/* BG accent blobs */}
          <div className="absolute -top-6 -right-6 w-24 h-24 rounded-full pointer-events-none"
            style={{ background: `radial-gradient(circle, ${sc}20, transparent 70%)` }} />
          <div className="absolute -bottom-4 -left-4 w-16 h-16 rounded-full pointer-events-none"
            style={{ background: `radial-gradient(circle, ${dirColor}15, transparent 70%)` }} />

          <div className="relative flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
                style={{ background: `${dirColor}18`, border: `2px solid ${dirColor}35`, boxShadow: `0 0 16px ${dirColor}25` }}>
                {isBuy
                  ? <ArrowUpRight className="w-6 h-6" style={{ color: dirColor }} />
                  : <ArrowDownRight className="w-6 h-6" style={{ color: dirColor }} />}
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-[18px] font-black font-mono" style={{ color: sc }}>{symLabel(sig.symbol)}</h2>
                  <span className="text-[13px] font-extrabold font-mono px-2.5 py-0.5 rounded-xl"
                    style={{ color: dirColor, background: `${dirColor}18`, border: `1px solid ${dirColor}35` }}>
                    {sig.ml_direction}
                  </span>
                </div>
                <p className="text-[10px] font-mono text-white/30 mt-0.5">
                  {sig.model_type} · {sig.status} · {new Date(sig.created_at).toLocaleString()}
                </p>
              </div>
            </div>
            {/* Entry price */}
            <div className="text-right shrink-0">
              <p className="text-[8px] uppercase tracking-widest text-white/25 mb-0.5">Entry</p>
              <p className="text-[16px] font-black font-mono text-white">{sig.ml_entry_price?.toFixed(2)}</p>
            </div>
          </div>
        </div>

        {/* ── STATS ROW ── */}
        <div className="px-5 py-3 grid grid-cols-4 divide-x divide-white/5" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
          {[
            { label: "Max Profit", val: `+${(sig.highest_profit_pips || 0).toFixed(1)}p`, color: C.g },
            { label: "Max DD", val: `${(sig.lowest_drawdown_pips || 0).toFixed(1)}p`, color: C.r },
            { label: "Confidence", val: `${(sig.ml_confidence || 0).toFixed(0)}%`, color: C.p },
            { label: "Status", val: sig.status, color: sig.status === "completed" ? C.g : sig.status === "stopped" ? C.r : C.y },
          ].map(s => (
            <div key={s.label} className="text-center px-2 py-2 first:pl-0 last:pr-0">
              <p className="text-[7px] uppercase tracking-widest mb-0.5" style={{ color: "rgba(255,255,255,0.25)" }}>{s.label}</p>
              <p className="text-[13px] font-black font-mono" style={{ color: s.color }}>{s.val}</p>
            </div>
          ))}
        </div>

        {/* ── TARGET ARC INDICATORS ── */}
        {sig.targets_hit && (
          <div className="px-5 py-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <p className="text-[8px] uppercase tracking-widest text-white/25 mb-3">Target Levels</p>
            <div className="flex gap-4 justify-center flex-wrap">
              {Object.entries(sig.targets_hit).map(([tp, hit]) => (
                <ArcTarget key={tp} name={tp} hit={hit as boolean} pips={sig.targets?.[tp]} />
              ))}
            </div>
          </div>
        )}

        {/* ── SPARKLINE CHART ── */}
        {checks.length >= 2 && (
          <div className="px-5 py-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[8px] uppercase tracking-widest text-white/25">P/L Timeline</p>
              <span className="text-[12px] font-black font-mono" style={{ color: profitPos ? C.g : C.r }}>
                {profitPos ? "+" : ""}{(netProfit ?? 0).toFixed(1)} pips
              </span>
            </div>
            <div className="rounded-xl overflow-hidden" style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.04)" }}>
              <div className="px-3 pt-3 pb-1">
                <SparkLine checks={checks} direction={sig.ml_direction} />
              </div>
              {/* Time axis */}
              <div className="flex justify-between px-3 pb-2">
                <span className="text-[8px] font-mono text-white/20">
                  {new Date(checks[0].check_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                <span className="text-[8px] font-mono text-white/20">
                  {new Date(checks[checks.length - 1].check_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ── PRICE ACTION TABLE (last 6 checks) ── */}
        {checks.length > 0 && (
          <div className="px-5 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <p className="text-[8px] uppercase tracking-widest text-white/25 mb-2">Price Action (5-min checks)</p>
            <div className="max-h-40 overflow-y-auto rounded-xl" style={{ background: "rgba(0,0,0,0.2)" }}>
              <table className="w-full text-[9px] font-mono">
                <thead>
                  <tr className="text-white/20 sticky top-0" style={{ background: "rgba(8,10,25,0.9)" }}>
                    <th className="text-left py-1.5 px-2">Time</th>
                    <th className="text-right py-1.5 px-2">Price</th>
                    <th className="text-right py-1.5 px-2 hidden sm:table-cell">High</th>
                    <th className="text-right py-1.5 px-2 hidden sm:table-cell">Low</th>
                    <th className="text-right py-1.5 px-2">P/L</th>
                    <th className="text-right py-1.5 px-2">TP</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.slice().reverse().map((ch: SignalCheck, i: number) => {
                    const plColor = ch.profit_pips >= 0 ? C.g : C.r;
                    const hitCount = ch.target_status ? Object.values(ch.target_status).filter(Boolean).length : 0;
                    return (
                      <tr key={ch.id || i} style={{ borderTop: "1px solid rgba(255,255,255,0.03)" }}>
                        <td className="py-1.5 px-2 text-white/35">{new Date(ch.check_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                        <td className="py-1.5 px-2 text-right text-white/50">{ch.current_price?.toFixed(2)}</td>
                        <td className="py-1.5 px-2 text-right hidden sm:table-cell" style={{ color: `${C.g}70` }}>{ch.session_high?.toFixed(2) || "—"}</td>
                        <td className="py-1.5 px-2 text-right hidden sm:table-cell" style={{ color: `${C.r}70` }}>{ch.session_low?.toFixed(2) || "—"}</td>
                        <td className="py-1.5 px-2 text-right font-bold" style={{ color: plColor }}>
                          {ch.profit_pips >= 0 ? "+" : ""}{ch.profit_pips?.toFixed(1)}
                        </td>
                        <td className="py-1.5 px-2 text-right" style={{ color: hitCount > 0 ? C.g : "rgba(255,255,255,0.15)" }}>
                          {hitCount > 0 ? `${hitCount}✓` : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── FAILURE AUTOPSY ── */}
        {failure && (
          <div className="px-5 py-3" style={{ background: `${C.r}05`, borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <p className="text-[8px] uppercase tracking-widest mb-2.5 flex items-center gap-1" style={{ color: `${C.r}80` }}>
              <AlertTriangle className="w-3 h-3" style={{ color: C.r }} /> Failure Autopsy
            </p>
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
              {[
                { k: "Type", v: failure.failure_type },
                { k: "Market Regime", v: failure.market_regime },
                { k: "Confluence", v: `${failure.confluence_score}/5` },
              ].map(row => (
                <div key={row.k} className="flex justify-between gap-2 px-2.5 py-1.5 rounded-lg" style={{ background: "rgba(255,255,255,0.02)" }}>
                  <span className="text-white/25">{row.k}</span>
                  <span className="text-white/70 font-bold">{row.v}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── CLOSE ── */}
        <div className="px-5 pb-6 pt-4 flex justify-center">
          <button
            onClick={onClose}
            className="px-6 py-2 rounded-full text-[11px] font-bold font-mono transition-all hover:scale-105 active:scale-95"
            style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.4)" }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
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
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(8,10,25,0.88)",
        backdropFilter: "blur(24px)",
        border: "1px solid rgba(168,85,247,0.1)",
        boxShadow: "0 0 60px rgba(168,85,247,0.04)",
      }}
    >
      {/* ── HEADER ── */}
      <div className="flex items-center justify-between px-5 py-3.5" style={{
        background: "linear-gradient(180deg, rgba(168,85,247,0.08) 0%, transparent 100%)",
        borderBottom: "1px solid rgba(168,85,247,0.08)",
      }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, rgba(0,255,136,0.2), rgba(168,85,247,0.2))", border: "1px solid rgba(168,85,247,0.35)" }}>
            <LearningIcon size={20} style={{ color: C.p }} />
          </div>
          <div>
            <h2 className="text-[13px] font-extrabold font-mono tracking-wider" style={{ color: C.p }}>SIGNAL PERFORMANCE</h2>
            <p className="text-[8px] uppercase tracking-[0.3em]" style={{ color: "rgba(192,132,252,0.35)" }}>
              LEARNING ENGINE · LIFECYCLE TRACKER
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {dashboard?.active_signals !== undefined && (
            <span className="text-[10px] font-bold font-mono px-2 py-1 rounded-lg inline-flex items-center gap-1.5"
              style={{ color: C.g, background: `${C.g}10`, border: `1px solid ${C.g}25` }}>
              <Activity className="w-3 h-3" style={{ color: C.g }} />
              {dashboard.active_signals} active
            </span>
          )}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}
            className="text-[10px] font-mono font-bold px-2 py-1.5 rounded-lg appearance-none cursor-pointer"
            style={{ backgroundColor: "rgba(168,85,247,0.08)", color: "rgba(192,132,252,0.6)", border: "1px solid rgba(168,85,247,0.15)" }}>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
          <button onClick={handleCheck}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[10px] font-bold font-mono transition-all hover:scale-105 active:scale-95"
            style={{ background: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.2)", color: C.g }}>
            <RefreshCw className={`w-3 h-3 ${checking ? "animate-spin" : ""}`} />
            Check Now
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin" style={{ color: C.p }} />
        </div>
      ) : (
        <div className="p-4 space-y-5">

          {/* ── ACTIVE SIGNALS SECTION ── */}
          {activeSignals.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: C.g, boxShadow: `0 0 6px ${C.g}` }} />
                <p className="text-[10px] uppercase tracking-[0.2em] font-bold" style={{ color: "rgba(0,255,136,0.6)" }}>
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

          {/* ── MODEL PERFORMANCE SECTION ── */}
          {Object.keys(models).length > 0 ? (
            <div>
              <p className="text-[9px] uppercase tracking-[0.25em] text-white/25 mb-3 ml-1">Strategy Performance</p>
              <div className="space-y-2">
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
            <div className="text-center py-10">
              <EmelIcon size={40} style={{ color: "rgba(255,255,255,0.08)" }} />
              <p className="text-white/25 text-sm mt-3">No signal data yet for this period.</p>
              <p className="text-white/15 text-[10px] mt-1">Signals will appear as EMEL, Pulse, and ML panels generate BUY/SELL signals.</p>
            </div>
          )}

          {/* ── FAILURE PATTERNS ── */}
          {Object.keys(failBreak).length > 0 && (
            <div className="rounded-xl p-3.5" style={{ background: `${C.r}06`, border: `1px solid ${C.r}18` }}>
              <p className="text-[8px] uppercase tracking-[0.2em] mb-2.5 flex items-center gap-1.5"
                style={{ color: `${C.r}70` }}>
                <AlertTriangle className="w-3 h-3" style={{ color: C.r }} />
                Failure Pattern Breakdown
              </p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(failBreak).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[9px] font-mono"
                    style={{ background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.15)" }}>
                    <span className="text-white/50">{type.replace(/_/g, " ")}</span>
                    <span className="font-bold ml-0.5" style={{ color: C.r }}>{count}</span>
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
