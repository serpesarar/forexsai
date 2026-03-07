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
import { useQuery } from "@tanstack/react-query";
import { EmelIcon, PulseIcon, LearningIcon, SignalsIcon } from "../ui/CustomIcons";
import {
  useLifecycleDashboard, useActiveSignals, useSignalDetail,
  triggerLifecycleCheck, type ModelStats, type ActiveSignal, type SignalCheck,
} from "../../lib/api/learning";
import { getApiBase } from "../../lib/api/base";
import { ModelPerformanceModal } from "./ModelPerformanceModal";

// ── Theme-aware Color Palette (CSS Variables) ───────────────────────────────

const MODEL_THEME: Record<string, { label: string; color: string; Icon: any }> = {
  ml: { label: "ML_Model", color: "var(--accent-info)", Icon: SignalsIcon },
  pulse1: { label: "Pulse 1 — Algo", color: "#22D3EE", Icon: PulseIcon },
  pulse2: { label: "Pulse 2 — ML", color: "var(--accent-purple)", Icon: SignalsIcon },
  pulse3: { label: "Pulse 3 — MTF", color: "var(--accent-positive)", Icon: PulseIcon },
  pulse: { label: "Pulse Engine", color: "#22D3EE", Icon: PulseIcon },
  emel: { label: "EMEL 9-Check", color: "#C084FC", Icon: EmelIcon },
  emel_inverse: { label: "Tersine NASDAQ", color: "#F97316", Icon: EmelIcon },
  hybrid: { label: "Hybrid", color: "var(--accent-warning)", Icon: LearningIcon },
};

const TIMEFRAME_ORDER = ["5m", "15m", "30m", "1h", "4h", "1d"];

const LEGACY_MODEL_TIMEFRAMES: Record<string, string[]> = {
  ml: ["1h"],
  emel: ["5m", "15m", "1h", "4h"],
  emel_inverse: ["5m", "15m", "1h", "4h"],
  pulse1: ["5m", "15m"],
  pulse2: ["5m", "15m", "1h"],
  pulse3: ["1h"],
};

function getTheme(model: string) {
  return MODEL_THEME[model] || MODEL_THEME.ml;
}

function symLabel(sym: string) {
  if (sym === "NDX.INDX") return "NASDAQ";
  if (sym === "GDAXI.INDX") return "DAX";
  if (sym === "CL.F" || sym === "USOIL.FOREX") return "US OIL";
  if (sym === "XAUUSD") return "XAUUSD";
  return sym;
}

function symIcon(sym: string): string {
  if (sym === "NDX.INDX") return "📈";
  if (sym === "GDAXI.INDX") return "🏛";
  if (sym === "CL.F" || sym === "USOIL.FOREX") return "🛢";
  if (sym === "XAUUSD") return "⭐";
  return "📊";
}

// ════════════════════════════════════════════════════════════════════════════
// HELPER COMPONENTS
// ════════════════════════════════════════════════════════════════════════════

function SymbolCard({ sym, d }: { sym: string; d: any }) {
  const name = symLabel(sym);
  const icon = symIcon(sym);
  const wr = d.win_rate ?? 0;
  const netPips = d.net_pips ?? 0;
  const netPos = netPips >= 0;
  const conf = wr;

  return (
    <div
      className="rounded-xl flex flex-col gap-3 transition-all duration-200 hover:translate-y-[-1px]"
      style={{
        background: "var(--bg-card)",
        border: `1px solid var(--border-subtle)`,
        padding: "20px",
      }}
    >
      {/* Header: Icon + Name + Confidence */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span style={{ fontSize: 16 }}>{icon}</span>
          <span style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>{name}</span>
        </div>
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: "var(--text-muted)" }}>
          ~ {conf.toFixed(0)}% confidence
        </span>
      </div>

      {/* Main PnL Number */}
      <div className="flex items-end justify-between">
        <span style={{
          fontFamily: FONT,
          fontSize: 32,
          fontWeight: 700,
          letterSpacing: "-0.5px",
          lineHeight: 1,
          color: netPos ? "var(--accent-positive)" : "var(--accent-negative)",
        }}>
          {netPos ? "+" : ""}{netPips.toFixed(1)}p
        </span>
      </div>

      {/* W / L row */}
      <div className="flex items-center gap-3" style={{ paddingTop: 4, borderTop: `1px solid var(--border-subtle)` }}>
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: "var(--accent-positive)" }}>
          {d.completed ?? 0}W
        </span>
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: "var(--accent-negative)" }}>
          {d.stopped ?? 0}L
        </span>
        <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
          {d.total ?? 0} signals
        </span>
      </div>

      {/* Target Bars (TP1-TP4) */}
      {d.target_rates && Object.keys(d.target_rates).length > 0 && (
        <div className="flex flex-col gap-2" style={{ paddingTop: 8, borderTop: `1px solid var(--border-subtle)` }}>
          {Object.entries(d.target_rates).sort().map(([tp, rate]) => (
            <TpBar key={tp} name={tp} rate={rate as number} />
          ))}
        </div>
      )}
    </div>
  );
}

function ModelCard({ model, stats, onSelectSymbol }: { model: string; stats: ModelStats; onSelectSymbol: (symbol: string, model: string) => void }) {
  const [open, setOpen] = useState(true);
  const theme = getTheme(model);
  const Icon = theme.Icon;
  const wr = stats.win_rate;
  const wrColor = wr >= 55 ? "var(--accent-positive)" : wr >= 40 ? "var(--accent-warning)" : "var(--accent-negative)";
  const netPos = stats.net_pips >= 0;
  const visibleTimeframes = LEGACY_MODEL_TIMEFRAMES[model] || TIMEFRAME_ORDER;
  const visibleTimeframeSet = new Set(visibleTimeframes);
  const timeframeEntries = Object.entries(stats.timeframe_stats || {})
    .sort(([a], [b]) => {
      const aIndex = TIMEFRAME_ORDER.indexOf(a);
      const bIndex = TIMEFRAME_ORDER.indexOf(b);
      return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex);
    })
    .filter(([tf, value]) => visibleTimeframeSet.has(tf) && (value?.total || 0) > 0);

  const API_BASE = getApiBase();
  const { data: matrixData, isLoading: matrixLoading } = useQuery({
    queryKey: ["signals-matrix", model],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/learning/signals/matrix?model=${model}`);
      if (!res.ok) throw new Error("Failed to fetch matrix");
      const data = await res.json();
      return data.matrix;
    },
    staleTime: 30000,
    enabled: open,
  });

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ background: "var(--bg-card)", border: `1px solid var(--border-subtle)` }}
    >
      {/* ── Model Header ── */}
      <div
        className="w-full flex items-center gap-4 px-5 py-4 transition-colors cursor-pointer"
        style={{ borderBottom: open ? `1px solid var(--border-subtle)` : "none" }}
        onClick={() => setOpen(!open)}
        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.015)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        {/* Icon + Label */}
        <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `${theme.color}12`, border: `1px solid ${theme.color}20` }}>
          <Icon className="w-5 h-5" style={{ color: theme.color, width: 20, height: 20 }} />
        </div>
        <div className="text-left flex-1 min-w-0">
          <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>{theme.label}</p>
          <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 400, color: "var(--text-muted)" }}>
            {stats.total_signals} signals · All sessions
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
          <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" as const }}>
            TOTAL NET
          </span>
          <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: netPos ? "var(--accent-positive)" : "var(--accent-negative)", letterSpacing: "-0.5px" }}>
            {netPos ? "+" : ""}{stats.net_pips.toFixed(1)}p
          </span>
        </div>

        {/* KPI: R/R */}
        <div className="text-right shrink-0 hidden md:flex flex-col items-end">
          <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" as const }}>
            R/R
          </span>
          <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: stats.risk_reward >= 1.5 ? "var(--accent-positive)" : "var(--accent-warning)", letterSpacing: "-0.3px" }}>
            {stats.risk_reward.toFixed(2)}
          </span>
        </div>

        {open ? <ChevronUp className="w-4 h-4 shrink-0" style={{ color: "var(--text-muted)" }} /> : <ChevronDown className="w-4 h-4 shrink-0" style={{ color: "var(--text-muted)" }} />}
      </div>

      {/* ── Expanded Content ── */}
      {open && (
        <div className="p-5 space-y-5">
          {/* KPI Strip */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "TOTAL PROFIT", val: `+${stats.total_profit_pips ?? stats.avg_profit_pips}p`, color: "var(--accent-positive)" },
              { label: "TOTAL LOSS", val: `-${stats.total_loss_pips ?? stats.avg_loss_pips}p`, color: "var(--accent-negative)" },
              { label: "AVG PROFIT", val: `+${stats.avg_profit_pips}p`, color: "var(--accent-positive)" },
            ].map(s => (
              <div key={s.label} className="rounded-lg text-center" style={{ background: "var(--bg-surface)", padding: "14px 12px", border: `1px solid var(--border-subtle)` }}>
                <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 6 }}>
                  {s.label}
                </p>
                <p style={{ fontFamily: FONT, fontSize: 20, fontWeight: 700, color: s.color, letterSpacing: "-0.5px" }}>
                  {s.val}
                </p>
              </div>
            ))}
          </div>

          {timeframeEntries.length > 0 && (
            <div>
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 12 }}>
                Timeframe Edge
              </p>
              <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                {timeframeEntries.map(([tf, tfStats]) => {
                  const tfNetPositive = (tfStats.net_pips ?? 0) >= 0;
                  const tfTone = (tfStats.win_rate ?? 0) >= 55
                    ? "var(--accent-positive)"
                    : (tfStats.win_rate ?? 0) >= 40
                      ? "var(--accent-warning)"
                      : "var(--accent-negative)";

                  return (
                    <div
                      key={tf}
                      className="rounded-lg"
                      style={{
                        background: "var(--bg-surface)",
                        padding: 14,
                        border: `1px solid var(--border-subtle)`,
                      }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 700, color: "var(--text-primary)", textTransform: "uppercase" as const }}>
                          {tf}
                        </span>
                        <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 600, color: tfTone }}>
                          {tfStats.win_rate?.toFixed(1) ?? "0.0"}%
                        </span>
                      </div>
                      <div className="mt-3 flex items-end justify-between gap-2">
                        <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: tfNetPositive ? "var(--accent-positive)" : "var(--accent-negative)", letterSpacing: "-0.02em" }}>
                          {(tfStats.net_pips ?? 0) >= 0 ? "+" : ""}{(tfStats.net_pips ?? 0).toFixed(1)}p
                        </span>
                        <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>
                          {tfStats.total} sig
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Overall Target Rates */}
          {Object.keys(stats.target_rates).length > 0 && (
            <div className="space-y-2.5">
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const }}>
                Overall Target Hit Rates
              </p>
              <div className="rounded-lg" style={{ background: "var(--bg-surface)", padding: 16, border: `1px solid var(--border-subtle)` }}>
                <div className="flex flex-col gap-3">
                  {Object.entries(stats.target_rates).sort().map(([tp, rate]) => (
                    <TpBar key={tp} name={tp} rate={rate} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Per-Symbol Asset Cards */}
          {Object.keys(stats.symbols).length > 0 && (
            <div>
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 12 }}>
                Per Asset Performance
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(stats.symbols).map(([sym, d]) => (
                  <div
                    key={sym}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectSymbol(sym, model);
                    }}
                    className="cursor-pointer"
                  >
                    <SymbolCard sym={sym} d={d} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timeframe Matrix View */}
          {Object.keys(stats.symbols).length > 0 && (
            <div>
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 12 }}>
                Timeframe Breakdown (Live)
              </p>
              <div className="rounded-lg overflow-x-auto scrollbar-hide" style={{ background: "var(--bg-surface)", border: `1px solid var(--border-subtle)` }}>
                {matrixLoading ? (
                  <div className="p-6 flex items-center justify-center">
                    <RefreshCw className="w-4 h-4 animate-spin" style={{ color: "var(--text-muted)" }} />
                  </div>
                ) : !matrixData || Object.keys(matrixData).length === 0 ? (
                  <div className="p-6 text-center text-[12px]" style={{ color: "var(--text-muted)" }}>
                    No active signals found.
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse min-w-[500px]">
                    <thead>
                      <tr style={{ background: "rgba(255,255,255,0.02)" }}>
                        <th className="py-3 px-4 text-[10px] font-semibold uppercase tracking-[0.08em] border-b border-[var(--border-subtle)]" style={{ color: "var(--text-muted)" }}>Symbol</th>
                        {visibleTimeframes.map(tf => (
                          <th key={tf} className="py-3 px-4 text-[10px] font-semibold uppercase tracking-[0.08em] border-b border-[var(--border-subtle)] text-center" style={{ color: "var(--text-muted)" }}>{tf}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"].map(symId => {
                        const rowData = matrixData[symId] || matrixData[symId.split('.')[0]];
                        if (!rowData) return null;
                        const name = symLabel(symId);
                        const icon = symIcon(symId);
                        return (
                          <tr key={symId} className="border-b transition-colors cursor-pointer" style={{ borderColor: "var(--border-subtle)" }}
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectSymbol(symId, model);
                            }}
                            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
                            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                            <td className="py-3 px-4 flex items-center gap-2">
                              <span className="text-[14px]">{icon}</span>
                              <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>{name}</span>
                            </td>
                            {visibleTimeframes.map(tf => {
                              const cell = rowData[tf];
                              if (!cell) return <td key={tf} className="py-3 px-4 text-center text-[var(--text-muted)]">-</td>;
                              const isHold = cell.direction === "HOLD";
                              const isOld = cell.age_hours > 24;
                              const dotColor = cell.direction === "BUY" ? "var(--accent-positive)" : cell.direction === "SELL" ? "var(--accent-negative)" : "var(--accent-warning)";
                              const textColor = cell.direction === "BUY" ? "var(--accent-positive)" : cell.direction === "SELL" ? "var(--accent-negative)" : "var(--text-muted)";
                              return (
                                <td key={tf} className={`py-3 px-4 text-center ${isOld ? 'opacity-40' : ''}`} title={isOld ? 'Signal older than 24h' : ''}>
                                  <div className="inline-flex items-center justify-center gap-1.5 px-2.5 py-1 rounded-md" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
                                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: isHold ? 'transparent' : dotColor, border: isHold ? '1px solid var(--text-muted)' : 'none', boxShadow: isHold ? 'none' : `0 0 6px ${dotColor}80` }}></span>
                                    <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 600, color: textColor }}>{isHold ? '-' : cell.confidence.toFixed(0)}</span>
                                  </div>
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT — SIGNAL PERFORMANCE DASHBOARD
// ════════════════════════════════════════════════════════════════════════════
export default function LearningDashboardV2() {
  const [days, setDays] = useState(0);
  const [checking, setChecking] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);
  const [signalListFilter, setSignalListFilter] = useState<{ model?: string; symbol?: string } | null>(null);
  const [selectedModelPerformance, setSelectedModelPerformance] = useState<{ symbol: string; model: string } | null>(null);

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

  // ── Helper Components (extracted outside to prevent infinite renders) ──

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        fontFamily: FONT,
        background: "var(--bg-primary)",
        border: `1px solid var(--border-subtle)`,
      }}
    >
      {/* ── HEADER ── */}
      <div className="flex items-center justify-between px-5 py-4" style={{
        background: "var(--bg-surface)",
        borderBottom: `1px solid var(--border-subtle)`,
      }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: `var(--accent-info)12`, border: `1px solid var(--accent-info)20` }}>
            <LearningIcon size={18} style={{ color: "var(--accent-info)" }} />
          </div>
          <div>
            <h2 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
              Signal Performance
            </h2>
            <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 400, color: "var(--text-muted)" }}>
              Learning Engine · Lifecycle Tracker
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {dashboard?.active_signals !== undefined && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg"
              style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--accent-positive)", background: `var(--accent-positive)08`, border: `1px solid var(--accent-positive)15` }}>
              <Activity className="w-3 h-3" style={{ color: "var(--accent-positive)" }} />
              {dashboard.active_signals} active
            </span>
          )}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg appearance-none cursor-pointer"
            style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, padding: "6px 10px", backgroundColor: "var(--bg-surface)", color: "var(--text-secondary)", border: `1px solid var(--border-subtle)` }}>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>365 days</option>
            <option value={0}>All Time</option>
          </select>
          <button onClick={handleCheck}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all duration-150"
            style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, background: `var(--accent-info)10`, border: `1px solid var(--accent-info)20`, color: "var(--accent-info)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = `var(--accent-info)18`)}
            onMouseLeave={(e) => (e.currentTarget.style.background = `var(--accent-info)10`)}>
            <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
            Check
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-16 flex items-center justify-center" style={{ background: "var(--bg-primary)" }}>
          <RefreshCw className="w-5 h-5 animate-spin" style={{ color: "var(--accent-info)" }} />
        </div>
      ) : (
        <div className="p-5 space-y-5" style={{ background: "var(--bg-primary)" }}>

          {/* ── ACTIVE SIGNALS ── */}
          {activeSignals.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--accent-positive)" }} />
                <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const }}>
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
              <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 12 }}>
                Model Performance
              </p>
              <div className="space-y-3">
                {Object.entries(models)
                  .sort(([a], [b]) => {
                    const order: Record<string, number> = { ml: 0, pulse1: 1, pulse2: 2, pulse3: 3, pulse: 3.5, emel: 4, emel_inverse: 4.5, hybrid: 5 };
                    return (order[a] ?? 99) - (order[b] ?? 99);
                  })
                  .map(([model, stats]) => {
                    const firstSymbol = Object.keys(stats.symbols || {})[0] || "";
                    return (
                      <div
                        key={model}
                      >
                        <ModelCard model={model} stats={stats} onSelectSymbol={(sym, mod) => setSelectedModelPerformance({ symbol: sym, model: mod })} />
                      </div>
                    );
                  })}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <EmelIcon size={36} style={{ color: "rgba(255,255,255,0.06)" }} />
              <p style={{ fontFamily: FONT, fontSize: 14, color: "var(--text-muted)", marginTop: 12 }}>No signal data for this period.</p>
              <p style={{ fontFamily: FONT, fontSize: 12, color: "var(--text-muted)", opacity: 0.5, marginTop: 4 }}>
                Signals appear as panels generate BUY/SELL decisions.
              </p>
            </div>
          )}

          {/* ── FAILURE BREAKDOWN ── */}
          {Object.keys(failBreak).length > 0 && (
            <div className="rounded-lg" style={{ background: `var(--accent-negative)05`, padding: 16, border: `1px solid var(--accent-negative)10` }}>
              <p className="flex items-center gap-1.5" style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: `var(--accent-negative)90`, letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 10 }}>
                <AlertTriangle className="w-3.5 h-3.5" style={{ color: "var(--accent-negative)" }} />
                Failure Breakdown
              </p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(failBreak).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                    style={{ background: `var(--accent-negative)08`, border: `1px solid var(--accent-negative)12` }}>
                    <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-secondary)" }}>{type.replace(/_/g, " ")}</span>
                    <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: "var(--accent-negative)" }}>{count}</span>
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

      {/* ── SIGNAL LIST MODAL ── */}
      {signalListFilter && (
        <SignalListModal
          title={signalListFilter.model
            ? `${MODEL_THEME[signalListFilter.model]?.label || signalListFilter.model} Signals`
            : signalListFilter.symbol
              ? `${symLabel(signalListFilter.symbol)} Signals`
              : "Signals"
          }
          filter={signalListFilter}
          onClose={() => setSignalListFilter(null)}
        />
      )}

      {/* ── HISTORICAL MODEL PERFORMANCE MODAL ── */}
      {selectedModelPerformance && (
        <ModelPerformanceModal
          isOpen={true}
          symbol={selectedModelPerformance.symbol}
          model={selectedModelPerformance.model}
          onClose={() => setSelectedModelPerformance(null)}
        />
      )}
    </div>
  );
}

// ── External Helper Components ──────────────────────────────────────────────

function ConfidenceRing({ rate, color, size = 56 }: { rate: number; color: string; size?: number }) {
  const r = size * 0.38;
  const circ = 2 * Math.PI * r;
  const dash = (rate / 100) * circ;
  const cx = size / 2;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={cx} cy={cx} r={r} fill="none" stroke={"var(--border-subtle)"} strokeWidth={size * 0.07} />
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

function TpBar({ name, rate }: { name: string; rate: number }) {
  const c = rate >= 50 ? "var(--accent-positive)" : rate >= 25 ? "var(--accent-warning)" : "var(--accent-negative)";
  return (
    <div className="flex items-center gap-2.5">
      <span
        className="w-7 shrink-0"
        style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-secondary)", letterSpacing: "0.02em" }}
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

function ActiveSignalCard({ signal, onSelect }: { signal: ActiveSignal; onSelect: (id: string) => void }) {
  const isBuy = signal.ml_direction === "BUY";
  const isSell = signal.ml_direction === "SELL";
  const dirColor = isBuy ? "var(--accent-positive)" : isSell ? "var(--accent-negative)" : "var(--accent-warning)";
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
        background: "var(--bg-card)",
        border: `1px solid var(--border-subtle)`,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)";
        e.currentTarget.style.transform = "translateY(-1px)";
        e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.3)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border-subtle)";
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <div className="flex items-center gap-0">
        <div className="w-1 self-stretch shrink-0 rounded-l-xl" style={{ background: dirColor, opacity: 0.7 }} />

        <div className="flex-1 px-4 py-3 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `${dirColor}10`, border: `1px solid ${dirColor}18` }}>
            {isBuy ? <ArrowUpRight className="w-4 h-4" style={{ color: dirColor }} />
              : isSell ? <ArrowDownRight className="w-4 h-4" style={{ color: dirColor }} />
                : <Minus className="w-4 h-4" style={{ color: dirColor }} />}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{symLabel(signal.symbol)}</span>
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
              <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>{age}m ago</span>
              <span style={{ color: "var(--text-muted)" }}>·</span>
              <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>Entry {signal.ml_entry_price?.toFixed(2)}</span>
              <span style={{ color: "var(--text-muted)" }}>·</span>
              <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: (signal.ml_confidence ?? 0) >= 60 ? "var(--accent-positive)" : "var(--accent-warning)" }}>
                {signal.ml_confidence?.toFixed(0)}% conf
              </span>
            </div>
          </div>

          <div className="shrink-0 flex flex-col items-end gap-1.5">
            <span style={{
              fontFamily: FONT, fontSize: 16, fontWeight: 700,
              color: profitPos ? "var(--accent-positive)" : "var(--text-muted)",
              letterSpacing: "-0.3px"
            }}>
              {profitPos ? "+" : ""}{(signal.highest_profit_pips ?? 0).toFixed(1)}p
            </span>
            <div className="flex items-center gap-1">
              {Array.from({ length: totalTargets }).map((_, i) => (
                <div key={i} className="rounded-sm" style={{
                  width: 10, height: 10,
                  background: i < targetsHit ? "var(--accent-positive)" : "rgba(255,255,255,0.06)",
                  border: i < targetsHit ? `1px solid ${"var(--accent-positive)"}50` : `1px solid var(--border-subtle)`,
                }} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}

// ── Modals ──────────────────────────────────────────────────────────────────

function SignalListModal({
  title,
  filter,
  onClose
}: {
  title: string;
  filter: { model?: string; symbol?: string };
  onClose: () => void;
}) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSignal, setSelectedSignal] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const params = new URLSearchParams();
        params.set("limit", "50");
        if (filter.symbol) params.set("symbol", filter.symbol);
        if (filter.model) params.set("model", filter.model);

        const API = getApiBase();
        const res = await fetch(`${API}/api/learning/signals/recent?${params}`);
        const data = await res.json();

        if (data.signals) {
          setSignals(data.signals);
        }
      } catch (e) {
        console.error("Failed to fetch signals:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSignals();
  }, [filter]);

  return (
    <div ref={overlayRef} className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}>
      <div className="w-full max-w-2xl rounded-xl overflow-hidden"
        style={{ background: "var(--bg-card)", border: `1px solid var(--border-subtle)`, maxHeight: "85vh", display: "flex", flexDirection: "column" }}>

        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: `1px solid var(--border-subtle)` }}>
          <div>
            <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: "var(--text-primary)" }}>{title}</p>
            <p style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{signals.length} signals found</p>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
            style={{ background: "rgba(255,255,255,0.03)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}>
            <XCircle className="w-4 h-4" style={{ color: "var(--text-muted)" }} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-6 h-6 animate-spin" style={{ color: "var(--accent-info)" }} />
            </div>
          ) : signals.length === 0 ? (
            <div className="text-center py-12">
              <p style={{ fontFamily: FONT, fontSize: 14, color: "var(--text-muted)" }}>No signals found</p>
            </div>
          ) : (
            signals.map((signal) => {
              const isBuy = signal.ml_direction === "BUY";
              const dirColor = isBuy ? "var(--accent-positive)" : "var(--accent-negative)";
              const age = Math.round((Date.now() - new Date(signal.created_at).getTime()) / 60000);

              return (
                <button
                  key={signal.id}
                  onClick={() => setSelectedSignal(signal.id)}
                  className="w-full text-left rounded-lg p-3 transition-all"
                  style={{ background: "var(--bg-surface)", border: `1px solid var(--border-subtle)` }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)")}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span style={{ color: dirColor, fontWeight: 600, fontSize: 12 }}>{isBuy ? "▲ BUY" : "▼ SELL"}</span>
                      <span style={{ fontFamily: FONT, fontSize: 13, color: "var(--text-primary)" }}>{symLabel(signal.symbol)}</span>
                      <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>{age}m ago</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: signal.pnl_pips > 0 ? "var(--accent-positive)" : signal.pnl_pips < 0 ? "var(--accent-negative)" : "var(--text-muted)" }}>
                        {signal.pnl_pips > 0 ? "+" : ""}{signal.pnl_pips?.toFixed(1) || "0"}p
                      </span>
                      <span style={{ fontFamily: FONT, fontSize: 11, color: signal.status === "completed" ? "var(--accent-positive)" : signal.status === "stopped" ? "var(--accent-negative)" : "var(--text-muted)", textTransform: "capitalize" }}>
                        {signal.status}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {selectedSignal && (
        <SignalDetailModal signalId={selectedSignal} onClose={() => setSelectedSignal(null)} />
      )}
    </div>
  );
}

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
      <RefreshCw className="w-6 h-6 animate-spin" style={{ color: "var(--accent-info)" }} />
    </div>
  );

  const sig = data.signal;
  if (!sig) return null;
  const isBuy = sig.ml_direction === "BUY";
  const dirColor = isBuy ? "var(--accent-positive)" : "var(--accent-negative)";
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
        style={{ background: "var(--bg-card)", border: `1px solid var(--border-subtle)`, maxHeight: "85vh", overflowY: "auto" }}>

        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: `1px solid var(--border-subtle)` }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ background: `${dirColor}10`, border: `1px solid ${dirColor}20` }}>
              {isBuy ? <ArrowUpRight className="w-5 h-5" style={{ color: dirColor }} />
                : <ArrowDownRight className="w-5 h-5" style={{ color: dirColor }} />}
            </div>
            <div>
              <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: "var(--text-primary)" }}>
                {symLabel(sig.symbol)} · {sig.ml_direction}
              </p>
              <p style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>
                {sig.model_type} · {sig.ml_confidence?.toFixed(0)}% confidence
              </p>
            </div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
            style={{ background: "rgba(255,255,255,0.03)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}>
            <XCircle className="w-4 h-4" style={{ color: "var(--text-muted)" }} />
          </button>
        </div>

        <div className="p-5 space-y-5">
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg" style={{ background: "var(--bg-surface)", padding: "12px", border: `1px solid var(--border-subtle)` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 4 }}>Entry</p>
              <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: "var(--text-primary)" }}>{sig.ml_entry_price?.toFixed(2)}</p>
            </div>
            <div className="rounded-lg" style={{ background: "var(--bg-surface)", padding: "12px", border: `1px solid var(--border-subtle)` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 4 }}>Best P/L</p>
              <p style={{ fontFamily: FONT, fontSize: 16, fontWeight: 600, color: (sig.highest_profit_pips ?? 0) > 0 ? "var(--accent-positive)" : "var(--text-muted)" }}>
                {(sig.highest_profit_pips ?? 0) > 0 ? "+" : ""}{(sig.highest_profit_pips ?? 0).toFixed(1)}p
              </p>
            </div>
            <div className="rounded-lg" style={{ background: "var(--bg-surface)", padding: "12px", border: `1px solid var(--border-subtle)` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 4 }}>Status</p>
              <p style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: sig.status === "completed" ? "var(--accent-positive)" : sig.status === "stopped" ? "var(--accent-negative)" : "var(--accent-warning)", textTransform: "capitalize" as const }}>{sig.status}</p>
            </div>
          </div>

          {failure && (
            <div className="rounded-lg" style={{ background: `var(--accent-negative)06`, padding: 14, border: `1px solid var(--accent-negative)15` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: "var(--accent-negative)", letterSpacing: "0.06em", textTransform: "uppercase" as const, marginBottom: 6 }}>Failure Autopsy</p>
              <p style={{ fontFamily: FONT, fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>{failure.reason || "Market moved against signal direction."}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
