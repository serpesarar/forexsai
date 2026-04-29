"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, BarChart3, BrainCircuit, RefreshCw, ShieldCheck, Target } from "lucide-react";
import { buildApiUrl } from "../../lib/api/base";
import { triggerLifecycleCheck, useActiveSignals, useLifecycleDashboard } from "../../lib/api/learning";
import SignalDetailModal from "../SignalDetailModal";
import { ModelPerformanceModal } from "./ModelPerformanceModal";

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
const SYMBOL_LABELS: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "XAUUSD": "XAU/USD",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL",
};

interface MetaLiveSignal {
  symbol: string;
  direction: string;
  confidence: number;
  strength: string;
  source_combo: string;
  regime: string;
  agreement_ratio: number;
  technical_score: number;
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  risk_reward: number;
  passed_conditions: string[];
}

interface MetaDashboardResponse {
  success?: boolean;
  data?: Record<string, MetaLiveSignal>;
  error?: string;
}

function dirColor(direction?: string) {
  if (direction === "BUY") return "var(--accent-positive)";
  if (direction === "SELL") return "var(--accent-negative)";
  return "var(--accent-info)";
}

function formatSymbol(symbol: string) {
  return SYMBOL_LABELS[symbol] || symbol;
}

function formatDate(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatCard({ label, value, subtext, color }: { label: string; value: string; subtext?: string; color?: string }) {
  return (
    <div
      className="rounded-xl p-4"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      <div style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </div>
      <div style={{ fontFamily: FONT, fontSize: 28, fontWeight: 700, color: color || "var(--text-primary)", marginTop: 10, lineHeight: 1 }}>
        {value}
      </div>
      {subtext && (
        <div style={{ fontFamily: FONT, fontSize: 12, color: "var(--text-secondary)", marginTop: 8 }}>
          {subtext}
        </div>
      )}
    </div>
  );
}

function RateBar({ label, value }: { label: string; value: number }) {
  const color = value >= 50 ? "var(--accent-positive)" : value >= 25 ? "var(--accent-warning)" : "var(--accent-negative)";
  return (
    <div className="flex items-center gap-3">
      <span style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-secondary)", width: 32 }}>{label}</span>
      <div className="flex-1 rounded-full overflow-hidden" style={{ height: 7, background: "rgba(255,255,255,0.06)" }}>
        <div style={{ width: `${Math.max(0, Math.min(100, value))}%`, height: "100%", background: color, borderRadius: 999 }} />
      </div>
      <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color, width: 42, textAlign: "right" }}>{value.toFixed(0)}%</span>
    </div>
  );
}

export default function MetaSignalAnalysisPanel() {
  const [days, setDays] = useState(0);
  const [checking, setChecking] = useState(false);
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  const {
    data: liveMeta,
    isLoading: metaLoading,
    error: metaError,
    refetch: refetchMeta,
  } = useQuery<MetaDashboardResponse>({
    queryKey: ["meta", "dashboard", "signals-view"],
    queryFn: async () => {
      const response = await fetch(buildApiUrl("/api/meta/dashboard"), { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to fetch meta dashboard");
      }
      return response.json();
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });

  const {
    data: lifecycleDashboard,
    isLoading: lifecycleLoading,
    refetch: refetchLifecycle,
  } = useLifecycleDashboard(days);

  const {
    data: activeData,
    refetch: refetchActive,
  } = useActiveSignals();

  const handleRefresh = useCallback(() => {
    refetchMeta();
    refetchLifecycle();
    refetchActive();
  }, [refetchActive, refetchLifecycle, refetchMeta]);

  useEffect(() => {
    window.addEventListener("dashboard-refresh", handleRefresh);
    return () => window.removeEventListener("dashboard-refresh", handleRefresh);
  }, [handleRefresh]);

  const handleCheck = useCallback(async () => {
    setChecking(true);
    try {
      await triggerLifecycleCheck();
      await Promise.all([refetchMeta(), refetchLifecycle(), refetchActive()]);
    } finally {
      setChecking(false);
    }
  }, [refetchActive, refetchLifecycle, refetchMeta]);

  const metaStats = lifecycleDashboard?.model_stats?.meta;
  const metaActiveSignals = useMemo(
    () => (activeData?.signals || []).filter((signal) => signal.model_type === "meta"),
    [activeData?.signals]
  );
  const liveSignals = useMemo(() => Object.values(liveMeta?.data || {}), [liveMeta?.data]);

  const resolvedSignals = (metaStats?.completed || 0) + (metaStats?.stopped || 0);
  const netPips = metaStats?.net_pips || 0;
  const winRate = metaStats?.win_rate || 0;
  const rr = metaStats?.risk_reward || 0;
  const isLoading = metaLoading || lifecycleLoading;

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        fontFamily: FONT,
        background: "var(--bg-primary)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      <div
        className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
        style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border-subtle)" }}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(79,140,255,0.14)", border: "1px solid rgba(79,140,255,0.2)" }}>
            <BrainCircuit className="w-5 h-5" style={{ color: "#4F8CFF" }} />
          </div>
          <div>
            <h2 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
              Meta Signal Analysis
            </h2>
            <p style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>
              Meta Engine · Same lifecycle evaluation layer as other signal models
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg" style={{ background: "rgba(79,140,255,0.08)", border: "1px solid rgba(79,140,255,0.15)", color: "#4F8CFF", fontSize: 11, fontWeight: 500 }}>
            <ClockBadge /> Meta snapshot 20m
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg" style={{ background: "rgba(22,199,132,0.08)", border: "1px solid rgba(22,199,132,0.15)", color: "var(--accent-positive)", fontSize: 11, fontWeight: 500 }}>
            <ShieldCheck className="w-3.5 h-3.5" /> Lifecycle eval 60s
          </span>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg appearance-none cursor-pointer"
            style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, padding: "6px 10px", backgroundColor: "var(--bg-surface)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)" }}
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>365 days</option>
            <option value={0}>All Time</option>
          </select>
          <button
            onClick={handleCheck}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all duration-150"
            style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, background: "rgba(79,140,255,0.10)", border: "1px solid rgba(79,140,255,0.18)", color: "#4F8CFF" }}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
            Check
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-16 flex items-center justify-center">
          <RefreshCw className="w-5 h-5 animate-spin" style={{ color: "#4F8CFF" }} />
        </div>
      ) : (
        <div className="p-5 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard label="Active Meta Signals" value={String(metaActiveSignals.length)} subtext="Tracked by shared lifecycle engine" color="#4F8CFF" />
            <StatCard label="Resolved Signals" value={String(resolvedSignals)} subtext={`${metaStats?.completed || 0} wins / ${metaStats?.stopped || 0} losses`} color="var(--text-primary)" />
            <StatCard label="Win Rate" value={`${winRate.toFixed(1)}%`} subtext="Meta model outcomes" color={winRate >= 50 ? "var(--accent-positive)" : "var(--accent-negative)"} />
            <StatCard label="Net Pips" value={`${netPips >= 0 ? "+" : ""}${netPips.toFixed(1)}p`} subtext={`R/R ${rr.toFixed(2)}`} color={netPips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)"} />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-5">
            <div className="rounded-xl p-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4" style={{ color: "#4F8CFF" }} />
                <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Live Meta Signals
                </p>
              </div>
              {metaError ? (
                <div style={{ fontFamily: FONT, fontSize: 13, color: "var(--accent-negative)" }}>Failed to load live Meta Engine signals.</div>
              ) : liveSignals.length === 0 ? (
                <div style={{ fontFamily: FONT, fontSize: 13, color: "var(--text-muted)" }}>No live Meta Engine signals available.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {liveSignals.map((signal) => (
                    <button
                      key={signal.symbol}
                      onClick={() => setSelectedSymbol(signal.symbol)}
                      className="text-left rounded-xl p-4 transition-colors hover:bg-white/5"
                      style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.06)" }}
                    >
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <div>
                          <div style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>{formatSymbol(signal.symbol)}</div>
                          <div style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>{signal.regime || "UNKNOWN"}</div>
                        </div>
                        <div className="px-2.5 py-1 rounded-lg" style={{ color: dirColor(signal.direction), background: "rgba(255,255,255,0.04)", fontSize: 12, fontWeight: 700 }}>
                          {signal.direction} · {Math.round(signal.confidence || 0)}%
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mb-3">
                        <MiniMetric label="Agreement" value={`${Math.round((signal.agreement_ratio || 0) * 100)}%`} />
                        <MiniMetric label="Tech" value={`${Math.round((signal.technical_score || 0) * 100)}%`} />
                        <MiniMetric label="Combo" value={signal.source_combo || "—"} mono />
                        <MiniMetric label="R:R" value={`${(signal.risk_reward || 0).toFixed(2)}x`} />
                      </div>
                      <div style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-secondary)" }}>
                        Entry {signal.entry_price?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || "—"} · TP1 {signal.take_profit_1?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || "—"} · SL {signal.stop_loss?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || "—"}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-xl p-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-4 h-4" style={{ color: "var(--accent-positive)" }} />
                <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Meta Target Hit Rates
                </p>
              </div>
              <div className="space-y-3">
                {Object.keys(metaStats?.target_rates || {}).length > 0 ? (
                  Object.entries(metaStats?.target_rates || {}).map(([label, value]) => (
                    <RateBar key={label} label={label} value={Number(value || 0)} />
                  ))
                ) : (
                  <div style={{ fontFamily: FONT, fontSize: 13, color: "var(--text-muted)" }}>
                    Meta outcome history is still building.
                  </div>
                )}
              </div>
            </div>
          </div>

          {metaActiveSignals.length > 0 && (
            <div className="rounded-xl p-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--accent-positive)" }} />
                <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Active Meta Lifecycle Signals ({metaActiveSignals.length})
                </p>
              </div>
              <div className="space-y-2">
                {metaActiveSignals.map((signal) => (
                  <button
                    key={signal.id}
                    onClick={() => setSelectedSignalId(signal.id)}
                    className="w-full text-left flex flex-wrap items-center justify-between gap-3 rounded-xl px-4 py-3 transition-colors hover:bg-white/5"
                    style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.05)" }}
                  >
                    <div className="flex items-center gap-3">
                      <span style={{ color: dirColor(signal.ml_direction), fontWeight: 700, fontSize: 13 }}>{signal.ml_direction}</span>
                      <span style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{formatSymbol(signal.symbol)}</span>
                      <span style={{ fontFamily: FONT, fontSize: 12, color: "var(--text-secondary)" }}>{signal.timeframe}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-4" style={{ fontFamily: FONT, fontSize: 12, color: "var(--text-secondary)" }}>
                      <span>{Math.round(signal.ml_confidence || 0)}%</span>
                      <span>Entry {signal.ml_entry_price?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || "—"}</span>
                      <span>{formatDate(signal.created_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {Object.keys(metaStats?.symbols || {}).length > 0 && (
            <div className="rounded-xl p-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-4 h-4" style={{ color: "#4F8CFF" }} />
                <p style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                  Symbol Performance
                </p>
              </div>
              <div className="space-y-2">
                {Object.entries(metaStats?.symbols || {}).map(([symbol, stats]) => (
                  <button
                    key={symbol}
                    onClick={() => setSelectedSymbol(symbol)}
                    className="w-full text-left flex flex-wrap items-center justify-between gap-3 rounded-xl px-4 py-3 transition-colors hover:bg-white/5"
                    style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}
                  >
                    <div>
                      <div style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{formatSymbol(symbol)}</div>
                      <div style={{ fontFamily: FONT, fontSize: 11, color: "var(--text-muted)" }}>{stats.total} signals · {stats.completed} wins · {stats.stopped} losses</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: Number(stats.win_rate || 0) >= 50 ? "var(--accent-positive)" : "var(--accent-negative)" }}>
                        {Number(stats.win_rate || 0).toFixed(1)}% WR
                      </span>
                      <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: Number(stats.net_pips || 0) >= 0 ? "var(--accent-positive)" : "var(--accent-negative)" }}>
                        {Number(stats.net_pips || 0) >= 0 ? "+" : ""}{Number(stats.net_pips || 0).toFixed(1)}p
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {selectedSignalId && <SignalDetailModal signalId={selectedSignalId} isOpen={true} onClose={() => setSelectedSignalId(null)} />}
      {selectedSymbol && (
        <ModelPerformanceModal
          isOpen={true}
          symbol={selectedSymbol}
          model="meta"
          onClose={() => setSelectedSymbol(null)}
          days={days}
        />
      )}
    </div>
  );
}

function MiniMetric({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div style={{ fontFamily: FONT, fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontFamily: mono ? "ui-monospace, SFMono-Regular, Menlo, monospace" : FONT, fontSize: 12, fontWeight: 600, color: "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

function ClockBadge() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
