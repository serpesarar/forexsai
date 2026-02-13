"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Brain, Target, TrendingUp, TrendingDown, RefreshCw, AlertTriangle,
  CheckCircle, XCircle, Activity, BarChart3, Zap, Shield, ChevronDown,
  ChevronUp, Eye, ArrowUpRight, ArrowDownRight, Minus, Clock,
} from "lucide-react";
import {
  useLifecycleDashboard, useActiveSignals, useSignalDetail,
  triggerLifecycleCheck, type ModelStats, type ActiveSignal, type SignalCheck,
} from "../../lib/api/learning";

const API = "https://upbeat-flow-production.up.railway.app";

const N = {
  g: { c: "#00ff88", bg: "rgba(0,255,136,0.06)", b: "rgba(0,255,136,0.18)" },
  r: { c: "#ff3366", bg: "rgba(255,51,102,0.06)", b: "rgba(255,51,102,0.18)" },
  y: { c: "#fbbf24", bg: "rgba(251,191,36,0.06)", b: "rgba(251,191,36,0.18)" },
  p: { c: "#c084fc", bg: "rgba(168,85,247,0.06)", b: "rgba(168,85,247,0.18)" },
  cyan: { c: "#22d3ee", bg: "rgba(34,211,238,0.06)", b: "rgba(34,211,238,0.18)" },
  blue: { c: "#60a5fa", bg: "rgba(96,165,250,0.06)", b: "rgba(96,165,250,0.18)" },
};

const MODEL_THEME: Record<string, { label: string; color: string; bg: string; border: string; Icon: any }> = {
  ml: { label: "ML Model", color: N.blue.c, bg: N.blue.bg, border: N.blue.b, Icon: Zap },
  pulse: { label: "Pulse Engine", color: N.cyan.c, bg: N.cyan.bg, border: N.cyan.b, Icon: Activity },
  pulse1: { label: "Pulse 1 — Algo", color: N.cyan.c, bg: N.cyan.bg, border: N.cyan.b, Icon: Activity },
  pulse2: { label: "Pulse 2 — ML Hybrid", color: "#a78bfa", bg: "rgba(167,139,250,0.06)", border: "rgba(167,139,250,0.18)", Icon: Brain },
  pulse3: { label: "Pulse 3 — MTF Hybrid", color: "#34d399", bg: "rgba(52,211,153,0.06)", border: "rgba(52,211,153,0.18)", Icon: TrendingUp },
  emel: { label: "EMEL 9-Check", color: N.p.c, bg: N.p.bg, border: N.p.b, Icon: Brain },
  hybrid: { label: "Hybrid", color: N.y.c, bg: N.y.bg, border: N.y.b, Icon: Shield },
};

function getTheme(model: string) {
  return MODEL_THEME[model] || MODEL_THEME.ml;
}

/* ── Small reusable components ── */

function Pill({ children, color, bg, border }: { children: React.ReactNode; color: string; bg: string; border: string }) {
  return (
    <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded-md inline-flex items-center gap-1"
      style={{ color, background: bg, border: `1px solid ${border}` }}>
      {children}
    </span>
  );
}

function StatBox({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="text-center">
      <p className="text-[8px] uppercase tracking-[0.2em] mb-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>{label}</p>
      <p className="text-lg font-black font-mono" style={{ color: color || "white" }}>{value}</p>
      {sub && <p className="text-[9px]" style={{ color: "rgba(255,255,255,0.25)" }}>{sub}</p>}
    </div>
  );
}

function TargetBar({ name, rate }: { name: string; rate: number }) {
  const c = rate >= 60 ? N.g : rate >= 35 ? N.y : N.r;
  return (
    <div>
      <div className="flex justify-between text-[10px] font-mono mb-0.5">
        <span style={{ color: c.c }}>{name}</span>
        <span className="text-white/60 font-bold">{rate.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
        <div className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(rate, 100)}%`, background: c.c, boxShadow: `0 0 6px ${c.c}40` }} />
      </div>
    </div>
  );
}

/* ── Model Performance Card ── */

function ModelCard({ model, stats }: { model: string; stats: ModelStats }) {
  const [open, setOpen] = useState(false);
  const theme = getTheme(model);
  const Icon = theme.Icon;
  const netColor = stats.net_pips >= 0 ? N.g.c : N.r.c;

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: theme.bg, border: `1px solid ${theme.border}` }}>
      {/* Header */}
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.02] transition-colors">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${theme.color}15`, border: `1px solid ${theme.color}30` }}>
            <Icon className="w-4 h-4" style={{ color: theme.color }} />
          </div>
          <div className="text-left">
            <p className="text-[12px] font-bold font-mono" style={{ color: theme.color }}>{theme.label}</p>
            <p className="text-[9px] text-white/30">{stats.total_signals} signals</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <StatBox label="Win Rate" value={`${stats.win_rate}%`} color={stats.win_rate >= 50 ? N.g.c : N.r.c} />
          <StatBox label="Net Pips" value={stats.net_pips > 0 ? `+${stats.net_pips}` : String(stats.net_pips)} color={netColor} />
          <StatBox label="R/R" value={stats.risk_reward.toFixed(1)} color={stats.risk_reward >= 1.5 ? N.g.c : N.y.c} />
          {open ? <ChevronUp className="w-4 h-4 text-white/30" /> : <ChevronDown className="w-4 h-4 text-white/30" />}
        </div>
      </button>

      {/* Expanded detail */}
      {open && (
        <div className="px-4 pb-4 space-y-3" style={{ borderTop: `1px solid ${theme.border}` }}>
          {/* Score strip */}
          <div className="flex gap-3 pt-3 flex-wrap">
            <Pill color={N.g.c} bg={N.g.bg} border={N.g.b}><CheckCircle className="w-3 h-3" /> {stats.completed} Completed</Pill>
            <Pill color={N.r.c} bg={N.r.bg} border={N.r.b}><XCircle className="w-3 h-3" /> {stats.stopped} Stopped</Pill>
            <Pill color={N.y.c} bg={N.y.bg} border={N.y.b}><Clock className="w-3 h-3" /> {stats.expired} Expired</Pill>
          </div>
          {/* Profit/Loss */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg p-2.5 text-center" style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.1)" }}>
              <p className="text-[8px] uppercase tracking-widest text-white/30 mb-0.5">Avg Profit</p>
              <p className="text-sm font-black font-mono" style={{ color: N.g.c }}>+{stats.avg_profit_pips} pips</p>
            </div>
            <div className="rounded-lg p-2.5 text-center" style={{ background: "rgba(255,51,102,0.04)", border: "1px solid rgba(255,51,102,0.1)" }}>
              <p className="text-[8px] uppercase tracking-widest text-white/30 mb-0.5">Avg Loss</p>
              <p className="text-sm font-black font-mono" style={{ color: N.r.c }}>-{stats.avg_loss_pips} pips</p>
            </div>
            <div className="rounded-lg p-2.5 text-center" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
              <p className="text-[8px] uppercase tracking-widest text-white/30 mb-0.5">Total Net</p>
              <p className="text-sm font-black font-mono" style={{ color: netColor }}>{stats.net_pips > 0 ? "+" : ""}{stats.net_pips} pips</p>
            </div>
          </div>
          {/* Target Hit Rates */}
          {Object.keys(stats.target_rates).length > 0 && (
            <div>
              <p className="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-2">Target Hit Rates</p>
              <div className="space-y-1.5">
                {Object.entries(stats.target_rates).sort().map(([tp, rate]) => (
                  <TargetBar key={tp} name={tp} rate={rate} />
                ))}
              </div>
            </div>
          )}
          {/* Per-symbol breakdown with targets */}
          {Object.keys(stats.symbols).length > 0 && (
            <div className="space-y-2">
              <p className="text-[9px] uppercase tracking-[0.2em] text-white/30">Per Symbol</p>
              {Object.entries(stats.symbols).map(([sym, d]) => {
                const symName = sym === "NDX.INDX" ? "NASDAQ" : sym;
                const symNetColor = (d.net_pips ?? 0) >= 0 ? N.g.c : N.r.c;
                return (
                  <div key={sym} className="rounded-lg p-3" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold font-mono text-white/80">{symName}</span>
                        <span className="text-[9px] text-white/30 font-mono">{d.total} signals</span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] font-mono">
                        <span style={{ color: N.g.c }}>{d.completed}W</span>
                        <span style={{ color: N.r.c }}>{d.stopped}L</span>
                        {d.win_rate !== undefined && <span className="font-bold" style={{ color: d.win_rate >= 50 ? N.g.c : N.r.c }}>{d.win_rate}%</span>}
                        {d.net_pips !== undefined && <span className="font-bold" style={{ color: symNetColor }}>{(d.net_pips ?? 0) >= 0 ? "+" : ""}{d.net_pips} pips</span>}
                      </div>
                    </div>
                    {d.target_rates && Object.keys(d.target_rates).length > 0 && (
                      <div className="space-y-1">
                        {Object.entries(d.target_rates).sort().map(([tp, rate]) => (
                          <TargetBar key={tp} name={tp} rate={rate as number} />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Active Signal Row ── */

function ActiveSignalRow({ signal, onSelect }: { signal: ActiveSignal; onSelect: (id: string) => void }) {
  const theme = getTheme(signal.model_type || "ml");
  const dirColor = signal.ml_direction === "BUY" ? N.g : signal.ml_direction === "SELL" ? N.r : N.y;
  const DirIcon = signal.ml_direction === "BUY" ? ArrowUpRight : signal.ml_direction === "SELL" ? ArrowDownRight : Minus;
  const profitColor = signal.highest_profit_pips > 0 ? N.g.c : N.y.c;

  const targetsHit = signal.targets_hit ? Object.values(signal.targets_hit).filter(Boolean).length : 0;
  const totalTargets = signal.targets ? Object.keys(signal.targets).length : 0;

  const age = Math.round((Date.now() - new Date(signal.created_at).getTime()) / 60000);

  return (
    <div className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/[0.02] transition-colors cursor-pointer"
      onClick={() => onSelect(signal.id)}
      style={{ background: "rgba(255,255,255,0.01)", border: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="flex items-center gap-2.5">
        <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: dirColor.bg, border: `1px solid ${dirColor.b}` }}>
          <DirIcon className="w-3.5 h-3.5" style={{ color: dirColor.c }} />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold font-mono text-white/80">{signal.symbol === "NDX.INDX" ? "NASDAQ" : signal.symbol}</span>
            <span className="text-[10px] font-bold font-mono" style={{ color: dirColor.c }}>{signal.ml_direction}</span>
            <span className="text-[9px] px-1.5 py-0 rounded" style={{ color: theme.color, background: `${theme.color}12` }}>{signal.model_type}</span>
          </div>
          <p className="text-[9px] text-white/25 font-mono">{age}m ago · Entry {signal.ml_entry_price?.toFixed(2)}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-[10px] font-mono font-bold" style={{ color: profitColor }}>
            +{signal.highest_profit_pips?.toFixed(1)} pips
          </p>
          <p className="text-[9px] font-mono" style={{ color: N.r.c }}>
            {signal.lowest_drawdown_pips?.toFixed(1)} pips
          </p>
        </div>
        <div className="text-[10px] font-mono font-bold" style={{ color: targetsHit > 0 ? N.g.c : "rgba(255,255,255,0.3)" }}>
          {targetsHit}/{totalTargets}
        </div>
        <Eye className="w-3.5 h-3.5 text-white/20" />
      </div>
    </div>
  );
}

/* ── Signal Detail Modal ── */

function SignalDetailModal({ signalId, onClose }: { signalId: string; onClose: () => void }) {
  const { data, isLoading } = useSignalDetail(signalId);

  if (isLoading) return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center" onClick={onClose}>
      <div className="rounded-2xl p-8" style={{ background: "rgba(8,10,25,0.95)", border: "1px solid rgba(168,85,247,0.2)" }}>
        <RefreshCw className="w-6 h-6 animate-spin" style={{ color: N.p.c }} />
      </div>
    </div>
  );

  if (!data || data.error) return null;

  const sig = data.signal;
  const checks = data.checks || [];
  const failure = data.failure;
  const dirColor = sig.ml_direction === "BUY" ? N.g : sig.ml_direction === "SELL" ? N.r : N.y;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div className="rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        style={{ background: "rgba(8,10,25,0.97)", border: "1px solid rgba(168,85,247,0.15)", boxShadow: "0 0 60px rgba(168,85,247,0.08)" }}>
        {/* Header */}
        <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: dirColor.bg, border: `1px solid ${dirColor.b}` }}>
              {sig.ml_direction === "BUY" ? <ArrowUpRight className="w-5 h-5" style={{ color: dirColor.c }} /> : <ArrowDownRight className="w-5 h-5" style={{ color: dirColor.c }} />}
            </div>
            <div>
              <p className="text-sm font-bold font-mono text-white">{sig.symbol === "NDX.INDX" ? "NASDAQ" : sig.symbol} {sig.ml_direction}</p>
              <p className="text-[10px] text-white/30 font-mono">
                {sig.model_type} · {sig.status} · {new Date(sig.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-white/30">Entry</p>
            <p className="text-sm font-bold font-mono text-white">{sig.ml_entry_price?.toFixed(2)}</p>
          </div>
        </div>

        {/* Stats row */}
        <div className="px-5 py-3 flex gap-4 flex-wrap" style={{ background: "rgba(0,0,0,0.2)" }}>
          <StatBox label="Max Profit" value={`+${(sig.highest_profit_pips || 0).toFixed(1)}`} color={N.g.c} />
          <StatBox label="Max Drawdown" value={(sig.lowest_drawdown_pips || 0).toFixed(1)} color={N.r.c} />
          <StatBox label="Confidence" value={`${(sig.ml_confidence || 0).toFixed(0)}%`} color={N.p.c} />
          <StatBox label="Status" value={sig.status} color={sig.status === "completed" ? N.g.c : sig.status === "stopped" ? N.r.c : N.y.c} />
        </div>

        {/* Target status */}
        {sig.targets_hit && (
          <div className="px-5 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <p className="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-2">Targets</p>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(sig.targets_hit).map(([tp, hit]) => (
                <div key={tp} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-mono font-bold"
                  style={{
                    background: hit ? N.g.bg : "rgba(255,255,255,0.02)",
                    border: `1px solid ${hit ? N.g.b : "rgba(255,255,255,0.06)"}`,
                    color: hit ? N.g.c : "rgba(255,255,255,0.3)",
                  }}>
                  {hit ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                  {tp} ({sig.targets?.[tp] || "?"} pips)
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5-min checks table */}
        {checks.length > 0 && (
          <div className="px-5 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <p className="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-2">Price Action (5-min checks)</p>
            <div className="max-h-48 overflow-y-auto">
              <table className="w-full text-[10px] font-mono">
                <thead>
                  <tr className="text-white/30">
                    <th className="text-left py-1 pr-2">Time</th>
                    <th className="text-right py-1 px-2">Price</th>
                    <th className="text-right py-1 px-2">High</th>
                    <th className="text-right py-1 px-2">Low</th>
                    <th className="text-right py-1 px-2">P/L</th>
                    <th className="text-right py-1 pl-2">Targets</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.map((ch: SignalCheck, i: number) => {
                    const plColor = ch.profit_pips >= 0 ? N.g.c : N.r.c;
                    const hitCount = ch.target_status ? Object.values(ch.target_status).filter(Boolean).length : 0;
                    return (
                      <tr key={ch.id || i} className="border-t" style={{ borderColor: "rgba(255,255,255,0.03)" }}>
                        <td className="py-1 pr-2 text-white/40">{new Date(ch.check_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                        <td className="py-1 px-2 text-right text-white/60">{ch.current_price?.toFixed(2)}</td>
                        <td className="py-1 px-2 text-right" style={{ color: N.g.c + "80" }}>{ch.session_high?.toFixed(2) || "—"}</td>
                        <td className="py-1 px-2 text-right" style={{ color: N.r.c + "80" }}>{ch.session_low?.toFixed(2) || "—"}</td>
                        <td className="py-1 px-2 text-right font-bold" style={{ color: plColor }}>{ch.profit_pips >= 0 ? "+" : ""}{ch.profit_pips?.toFixed(1)}</td>
                        <td className="py-1 pl-2 text-right" style={{ color: hitCount > 0 ? N.g.c : "rgba(255,255,255,0.2)" }}>{hitCount} hit</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Failure autopsy */}
        {failure && (
          <div className="px-5 py-3" style={{ background: "rgba(255,51,102,0.03)" }}>
            <p className="text-[9px] uppercase tracking-[0.2em] mb-2" style={{ color: N.r.c }}>Failure Autopsy</p>
            <div className="space-y-1.5 text-[10px] font-mono">
              <div className="flex justify-between"><span className="text-white/30">Type</span><span className="text-white/70 font-bold">{failure.failure_type}</span></div>
              <div className="flex justify-between"><span className="text-white/30">Market Regime</span><span className="text-white/70">{failure.market_regime}</span></div>
              <div className="flex justify-between"><span className="text-white/30">Confluence Score</span><span className="text-white/70">{failure.confluence_score}/5</span></div>
              {failure.contradiction_flags && Object.keys(failure.contradiction_flags).length > 0 && (
                <div>
                  <span className="text-white/30">Contradictions: </span>
                  {Object.entries(failure.contradiction_flags).map(([k, v]) => (
                    <span key={k} className="ml-1 px-1.5 py-0 rounded" style={{ background: N.r.bg, color: N.r.c, border: `1px solid ${N.r.b}` }}>{k}: {String(v)}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Close */}
        <div className="px-5 py-3 text-center">
          <button onClick={onClose} className="text-[11px] font-mono text-white/30 hover:text-white/60 transition-colors">Close</button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN COMPONENT: Learning Dashboard v2
   ═══════════════════════════════════════════════════════════════════════════ */

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
    try {
      await triggerLifecycleCheck();
      refetch();
      refetchActive();
    } catch (e) { console.error(e); }
    finally { setChecking(false); }
  };

  const models = dashboard?.model_stats || {};
  const failBreak = dashboard?.failure_breakdown || {};
  const activeSignals = activeData?.signals || [];

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(8,10,25,0.88)", backdropFilter: "blur(24px)", border: "1px solid rgba(168,85,247,0.1)", boxShadow: "0 0 60px rgba(168,85,247,0.04)" }}>

      {/* ── HEADER ── */}
      <div className="flex items-center justify-between px-5 py-3" style={{ background: "linear-gradient(180deg, rgba(168,85,247,0.07) 0%, transparent 100%)", borderBottom: "1px solid rgba(168,85,247,0.08)" }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: "linear-gradient(135deg, rgba(0,255,136,0.2), rgba(168,85,247,0.2))", border: "1px solid rgba(168,85,247,0.35)" }}>
            <BarChart3 className="w-5 h-5" style={{ color: N.p.c }} />
          </div>
          <div>
            <h2 className="text-[13px] font-extrabold font-mono tracking-wider" style={{ color: N.p.c }}>SIGNAL PERFORMANCE</h2>
            <p className="text-[8px] uppercase tracking-[0.3em]" style={{ color: "rgba(192,132,252,0.35)" }}>LEARNING ENGINE &middot; LIFECYCLE TRACKER</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {dashboard?.active_signals !== undefined && (
            <Pill color={N.g.c} bg={N.g.bg} border={N.g.b}>
              <Activity className="w-3 h-3" /> {dashboard.active_signals} active
            </Pill>
          )}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}
            className="text-[10px] font-mono font-bold px-2 py-1.5 rounded-lg appearance-none cursor-pointer"
            style={{ backgroundColor: "rgba(168,85,247,0.08)", color: "rgba(192,132,252,0.6)", border: "1px solid rgba(168,85,247,0.15)" }}>
            <option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option>
          </select>
          <button onClick={handleCheck} className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-bold font-mono transition-all hover:scale-105"
            style={{ background: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.2)", color: N.g.c }}>
            <RefreshCw className={`w-3 h-3 ${checking ? "animate-spin" : ""}`} />
            Check Now
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin" style={{ color: N.p.c }} />
        </div>
      ) : (
        <div className="p-4 space-y-4">

          {/* ── MODEL PERFORMANCE CARDS ── */}
          {Object.keys(models).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(models).map(([model, stats]) => (
                <ModelCard key={model} model={model} stats={stats} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Brain className="w-10 h-10 mx-auto mb-3" style={{ color: "rgba(255,255,255,0.1)" }} />
              <p className="text-white/30 text-sm">No signal data yet for this period.</p>
              <p className="text-white/15 text-[10px] mt-1">Signals will appear as EMEL, Pulse, and ML panels generate BUY/SELL signals.</p>
            </div>
          )}

          {/* ── FAILURE PATTERNS ── */}
          {Object.keys(failBreak).length > 0 && (
            <div className="rounded-xl p-4" style={{ background: N.r.bg, border: `1px solid ${N.r.b}` }}>
              <p className="text-[9px] uppercase tracking-[0.2em] mb-2.5" style={{ color: `${N.r.c}80` }}>Failure Pattern Breakdown</p>
              <div className="flex gap-3 flex-wrap">
                {Object.entries(failBreak).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[10px] font-mono"
                    style={{ background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.15)" }}>
                    <AlertTriangle className="w-3 h-3" style={{ color: N.r.c }} />
                    <span className="text-white/60">{type.replace(/_/g, " ")}</span>
                    <span className="font-bold" style={{ color: N.r.c }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── ACTIVE SIGNALS ── */}
          {activeSignals.length > 0 && (
            <div>
              <p className="text-[9px] uppercase tracking-[0.2em] text-white/30 mb-2 flex items-center gap-1.5">
                <Activity className="w-3 h-3" style={{ color: N.g.c }} />
                Active Signals ({activeSignals.length})
              </p>
              <div className="space-y-1.5">
                {activeSignals.map((sig) => (
                  <ActiveSignalRow key={sig.id} signal={sig} onSelect={setSelectedSignal} />
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
