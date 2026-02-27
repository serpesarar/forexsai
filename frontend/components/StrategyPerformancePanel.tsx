"use client";
/**
 * STRATEGY PERFORMANCE ANALYSIS — Premium Institutional Fintech Panel
 * Bloomberg Terminal meets modern AI startup aesthetic.
 * Design: #0B0F17 dark base, #141C2B cards, #4F8CFF AI accent
 */

import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import { PanelInfoButton } from "./PanelInfoButton";
import { useQuery } from "@tanstack/react-query";
import {
  ChartsIcon as BarChart3,
  RotateIcon as RefreshCw,
  TrophyIcon as Trophy,
  TargetIcon as Target,
  CloseIcon as XCircle,
  SecurityShieldIcon as Shield,
  ZapIcon as Zap,
  AggressiveIcon as Flame,
  ArrowUpIcon as TrendingUp,
  AlertIcon as AlertTriangle,
} from "./ui/CustomIcons";
import { List, Crosshair } from "lucide-react";

// Lazy load SignalDetailModal
const SignalDetailModal = lazy(() => import("./SignalDetailModal"));

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

// ── Theme-aware Color Palette (CSS Variables) ───────────────────────────────
// All colors now use CSS variables from theme.tokens.css

const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  textSec: "var(--text-secondary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
};

interface StrategyData {
  total_predictions: number;
  with_outcome: number;
  correct: number;
  accuracy: number | null;
  target_hit_rate: number | null;
  stop_hit_rate: number | null;
  avg_confidence: number;
  target_hits: number;
  stop_hits: number;
}

interface StrategyPerformanceResponse {
  period_days: number;
  strategies: {
    [symbol: string]: {
      [strategy: string]: StrategyData;
    };
  };
  best_strategies: {
    [symbol: string]: {
      strategy: string | null;
      accuracy: number | null;
    };
  };
  strategy_descriptions: {
    [strategy: string]: string;
  };
  error?: string;
}

async function fetchStrategyPerformance(days: number): Promise<StrategyPerformanceResponse> {
  const res = await fetch(`${API_BASE}/api/learning/strategy-performance?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch strategy performance");
  return res.json();
}

const STRATEGY_CONFIG: Record<string, {
  name: string; nameEn: string; icon: any; color: string;
}> = {
  ultra_safe: { name: "Ultra Güvenli", nameEn: "Ultra Safe", icon: Shield, color: P.green },
  balanced: { name: "Dengeli", nameEn: "Balanced", icon: Target, color: P.accent },
  full_power: { name: "Full Power", nameEn: "Full Power", icon: Zap, color: P.warn },
  aggressive: { name: "Agresif", nameEn: "Aggressive", icon: Flame, color: P.red },
  nasdaq_precision: { name: "NASDAQ Precision", nameEn: "NASDAQ Precision", icon: Crosshair, color: "#22D3EE" },
};

// ── Premium Progress Bar (6px, Rounded) ─────────────────────────────────────
function AccuracyBar({ value, color }: { value: number | null; color: string }) {
  if (value === null) return <span style={{ fontFamily: FONT, fontSize: 12, color: P.muted }}>—</span>;
  return (
    <div className="flex items-center gap-2.5" style={{ minWidth: 120 }}>
      <div className="flex-1 rounded-full overflow-hidden" style={{ height: 6, background: "rgba(255,255,255,0.06)" }}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(value, 100)}%`, background: color, opacity: 0.85 }} />
      </div>
      <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color, width: 40, textAlign: "right" as const }}>{value}%</span>
    </div>
  );
}

// ── Strategy Row (Institutional Table) ──────────────────────────────────────
function StrategyRow({
  strategy,
  data,
  isBest,
  locale,
}: {
  strategy: string;
  data: StrategyData;
  isBest: boolean;
  locale: string;
}) {
  const config = STRATEGY_CONFIG[strategy];
  if (!config) return null;

  const Icon = config.icon;
  const accColor = data.accuracy !== null && data.accuracy >= 60 ? P.green : data.accuracy !== null && data.accuracy >= 50 ? P.warn : P.red;

  return (
    <tr
      style={{
        borderBottom: `1px solid ${P.border}`,
        background: isBest ? `${P.warn}04` : "transparent",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = isBest ? `${P.warn}06` : "rgba(255,255,255,0.015)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = isBest ? `${P.warn}04` : "transparent")}
    >
      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" as const }}>
        <div className="flex items-center gap-2.5">
          <div className="rounded-md flex items-center justify-center shrink-0"
            style={{ width: 28, height: 28, background: `${config.color}10`, border: `1px solid ${config.color}18` }}>
            <Icon className="w-3.5 h-3.5" style={{ color: config.color }} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.text }}>
                {locale === "en" ? config.nameEn : config.name}
              </span>
              {isBest && (
                <span className="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5"
                  style={{ background: `${P.warn}15`, border: `1px solid ${P.warn}25` }}>
                  <Trophy className="w-2.5 h-2.5" style={{ color: P.warn }} />
                  <span style={{ fontFamily: FONT, fontSize: 9, fontWeight: 700, color: P.warn }}>BEST</span>
                </span>
              )}
            </div>
            <span style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>
              {data.total_predictions} predictions · {data.with_outcome} outcomes
            </span>
          </div>
        </div>
      </td>
      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" as const }}>
        <AccuracyBar value={data.accuracy} color={accColor} />
      </td>
      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" as const }}>
        <div className="flex items-center gap-1.5">
          <Target className="w-3 h-3 shrink-0" style={{ color: P.green }} />
          <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.green }}>{data.target_hit_rate !== null ? `${data.target_hit_rate}%` : "—"}</span>
          <span style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>({data.target_hits ?? 0})</span>
        </div>
      </td>
      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" as const }}>
        <div className="flex items-center gap-1.5">
          <XCircle className="w-3 h-3 shrink-0" style={{ color: P.red }} />
          <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.red }}>{data.stop_hit_rate !== null ? `${data.stop_hit_rate}%` : "—"}</span>
          <span style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>({data.stop_hits ?? 0})</span>
        </div>
      </td>
      <td style={{ padding: "10px 14px", textAlign: "right" as const, whiteSpace: "nowrap" as const }}>
        <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.textSec }}>{data.avg_confidence}%</span>
      </td>
    </tr>
  );
}

// ── Symbol Section Config ───────────────────────────────────────────────────
const SYMBOL_META = [
  { key: "NDX.INDX", label: "NASDAQ", icon: "📈", color: P.green },
  { key: "XAUUSD", label: "XAU/USD", icon: "⭐", color: P.warn },
  { key: "GDAXI.INDX", label: "DAX", icon: "🏛", color: P.accent },
  { key: "CL.COMM", label: "US Oil", icon: "🛢", color: "#FB923C" },
];

// ── Signal List Row ──────────────────────────────────────────────────────────
interface Signal {
  id: string;
  symbol: string;
  ml_direction: string;
  ml_confidence: number;
  status: string;
  created_at: string;
  pnl_pips?: number;
  duration_minutes?: number;
  model_type?: string;
  strategy?: string;
}

async function fetchRecentSignals(days: number, symbol?: string): Promise<Signal[]> {
  const url = new URL(`${API_BASE}/api/learning/signals/recent`);
  url.searchParams.set("limit", "20");
  url.searchParams.set("include_active", "true");
  if (symbol) url.searchParams.set("symbol", symbol);
  
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch signals");
  const data = await res.json();
  return data.signals || [];
}

function SignalRow({ signal, onClick }: { signal: Signal; onClick: () => void }) {
  const isBuy = signal.ml_direction === "BUY";
  const statusColor = 
    signal.status === "completed" ? P.green :
    signal.status === "stopped" ? P.red :
    signal.status === "active" ? P.accent :
    P.muted;
  
  const pnlColor = 
    signal.pnl_pips === undefined ? P.muted :
    signal.pnl_pips > 0 ? P.green :
    signal.pnl_pips < 0 ? P.red :
    P.muted;

  return (
    <tr 
      onClick={onClick}
      className="cursor-pointer hover:bg-white/5 transition-colors"
      style={{ borderBottom: `1px solid ${P.border}` }}
    >
      <td style={{ padding: "10px 14px" }}>
        <div className="flex items-center gap-2">
          <span style={{ 
            color: isBuy ? P.green : P.red,
            fontWeight: 600,
            fontSize: 12,
          }}>
            {isBuy ? "▲" : "▼"} {signal.ml_direction}
          </span>
          <span style={{ fontFamily: FONT, fontSize: 12, color: P.text }}>
            {signal.symbol}
          </span>
        </div>
      </td>
      <td style={{ padding: "10px 14px" }}>
        <span style={{ 
          fontFamily: FONT, 
          fontSize: 11, 
          color: statusColor,
          textTransform: "capitalize" 
        }}>
          {signal.status}
        </span>
      </td>
      <td style={{ padding: "10px 14px", textAlign: "right" }}>
        <span style={{ 
          fontFamily: FONT, 
          fontSize: 12, 
          color: pnlColor,
          fontWeight: signal.pnl_pips !== undefined ? 600 : 400,
        }}>
          {signal.pnl_pips !== undefined 
            ? `${signal.pnl_pips > 0 ? "+" : ""}${signal.pnl_pips.toFixed(1)} pips`
            : "—"
          }
        </span>
      </td>
      <td style={{ padding: "10px 14px", textAlign: "right" }}>
        <span style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>
          {new Date(signal.created_at).toLocaleDateString("tr-TR", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </td>
    </tr>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════════════════════
export default function StrategyPerformancePanel() {
  const [days, setDays] = useState(30);
  const [selectedSymbol, setSelectedSymbol] = useState<string | undefined>();
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"performance" | "signals">("performance");
  const locale = "tr";

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["strategy-performance", days],
    queryFn: () => fetchStrategyPerformance(days),
    staleTime: 60000,
    refetchInterval: 300000,
  });

  const { data: signalsData, isLoading: signalsLoading } = useQuery({
    queryKey: ["recent-signals", days, selectedSymbol],
    queryFn: () => fetchRecentSignals(days, selectedSymbol),
    staleTime: 30000,
    refetchInterval: 60000,
  });

  const handleRefresh = useCallback(() => { refetch(); }, [refetch]);

  useEffect(() => {
    window.addEventListener("dashboard-refresh", handleRefresh);
    return () => window.removeEventListener("dashboard-refresh", handleRefresh);
  }, [handleRefresh]);

  const handleSignalClick = (signalId: string) => {
    setSelectedSignalId(signalId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedSignalId(null);
  };

  if (error) {
    return (
      <div className="rounded-xl" style={{ background: P.card, border: `1px solid ${P.border}`, padding: 24 }}>
        <div className="flex items-center gap-3" style={{ color: P.red }}>
          <AlertTriangle className="w-5 h-5" />
          <span style={{ fontFamily: FONT, fontSize: 14, color: P.red }}>Strategy data unavailable</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        className="rounded-xl overflow-hidden"
        style={{ fontFamily: FONT, background: P.bg, border: `1px solid ${P.border}` }}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between px-5 py-4"
          style={{ background: P.surface, borderBottom: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: `${P.accent}12`, border: `1px solid ${P.accent}20` }}>
              <BarChart3 className="w-4.5 h-4.5" style={{ color: P.accent, width: 18, height: 18 }} />
            </div>
            <div>
              <h3 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text, letterSpacing: "-0.01em" }}>
                Strategy Performance Analysis
              </h3>
              <p style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>
                Which filter combination performs best?
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Tab Switcher */}
            <div className="flex items-center gap-1 mr-2" style={{ background: P.bg, borderRadius: 8, padding: 2 }}>
              <button
                onClick={() => setActiveTab("performance")}
                className="px-3 py-1.5 rounded-md text-xs font-medium transition-all"
                style={{
                  background: activeTab === "performance" ? `${P.accent}20` : "transparent",
                  color: activeTab === "performance" ? P.accent : P.muted,
                }}
              >
                <BarChart3 className="w-3.5 h-3.5 inline mr-1" />
                Performance
              </button>
              <button
                onClick={() => setActiveTab("signals")}
                className="px-3 py-1.5 rounded-md text-xs font-medium transition-all"
                style={{
                  background: activeTab === "signals" ? `${P.accent}20` : "transparent",
                  color: activeTab === "signals" ? P.accent : P.muted,
                }}
              >
                <List className="w-3.5 h-3.5 inline mr-1" />
                Signals
              </button>
            </div>

            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="rounded-lg appearance-none cursor-pointer"
              style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, padding: "6px 10px", background: P.surface, color: P.textSec, border: `1px solid ${P.border}` }}
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
            </select>

            <button
              onClick={() => refetch()}
              className="rounded-lg flex items-center justify-center transition-all duration-150"
              style={{ width: 32, height: 32, background: `${P.accent}08`, border: `1px solid ${P.accent}15` }}
              onMouseEnter={(e) => (e.currentTarget.style.background = `${P.accent}15`)}
              onMouseLeave={(e) => (e.currentTarget.style.background = `${P.accent}08`)}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} style={{ color: P.accent }} />
            </button>
            <PanelInfoButton panelId="strategy-performance" />
          </div>
        </div>

        {/* ── Content ── */}
        {isLoading && activeTab === "performance" ? (
          <div className="p-16 flex items-center justify-center" style={{ background: P.bg }}>
            <RefreshCw className="w-5 h-5 animate-spin" style={{ color: P.accent }} />
          </div>
        ) : activeTab === "performance" && data && !data.error ? (
          <div className="p-5 space-y-6" style={{ background: P.bg }}>
            {/* Symbol Sections */}
            {SYMBOL_META.map(({ key: symKey, label, icon, color }) => (
              <div key={symKey}>
                {/* Symbol Header */}
                <div className="flex items-center gap-2.5 mb-3">
                  <span style={{ fontSize: 16 }}>{icon}</span>
                  <h4 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text }}>{label}</h4>
                  {data.best_strategies[symKey]?.strategy && (
                    <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 ml-2"
                      style={{ background: `${P.warn}10`, border: `1px solid ${P.warn}18` }}>
                      <Trophy className="w-3 h-3" style={{ color: P.warn }} />
                      <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, color: P.warn }}>
                        Best: {STRATEGY_CONFIG[data.best_strategies[symKey].strategy as keyof typeof STRATEGY_CONFIG]?.nameEn ?? data.best_strategies[symKey].strategy}
                        {data.best_strategies[symKey].accuracy !== null && ` (${data.best_strategies[symKey].accuracy}%)`}
                      </span>
                    </span>
                  )}
                </div>

                {/* Table */}
                <div className="overflow-x-auto rounded-lg" style={{ border: `1px solid ${P.border}` }}>
                  <table className="w-full" style={{ minWidth: 640 }}>
                    <thead>
                      <tr style={{ background: P.surface }}>
                        {["Strategy", "Accuracy", "Target Hit", "Stop Hit", "Confidence"].map((h, i) => (
                          <th key={h} style={{
                            padding: "10px 14px",
                            textAlign: i === 4 ? "right" as const : "left" as const,
                            fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted,
                            letterSpacing: "0.08em", textTransform: "uppercase" as const,
                            borderBottom: `1px solid ${P.border}`,
                          }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(data.strategies[symKey] || {}).map(([strategy, strategyData]) => (
                        <StrategyRow
                          key={strategy}
                          strategy={strategy}
                          data={strategyData}
                          isBest={data.best_strategies[symKey]?.strategy === strategy}
                          locale={locale}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}

            {/* Strategy Descriptions */}
            <div style={{ paddingTop: 12, borderTop: `1px solid ${P.border}` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" as const, marginBottom: 8 }}>
                Strategy Descriptions
              </p>
              <div className="flex flex-wrap gap-x-6 gap-y-2">
                {Object.entries(data.strategy_descriptions || {}).map(([key, desc]) => {
                  const config = STRATEGY_CONFIG[key];
                  return (
                    <div key={key} className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full" style={{ background: config?.color || P.muted }} />
                      <span style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>{desc}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : activeTab === "signals" ? (
          <div className="p-5" style={{ background: P.bg }}>
            {/* Symbol Filter */}
            <div className="flex items-center gap-2 mb-4">
              <span style={{ fontFamily: FONT, fontSize: 12, color: P.muted }}>Symbol:</span>
              <select
                value={selectedSymbol || ""}
                onChange={(e) => setSelectedSymbol(e.target.value || undefined)}
                className="rounded-lg appearance-none cursor-pointer"
                style={{ fontFamily: FONT, fontSize: 11, padding: "6px 10px", background: P.surface, color: P.textSec, border: `1px solid ${P.border}` }}
              >
                <option value="">All Symbols</option>
                {SYMBOL_META.map(({ key, label }) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            {/* Signals Table */}
            <div className="overflow-x-auto rounded-lg" style={{ border: `1px solid ${P.border}` }}>
              <table className="w-full">
                <thead>
                  <tr style={{ background: P.surface }}>
                    {["Signal", "Status", "Result", "Time"].map((h, i) => (
                      <th key={h} style={{
                        padding: "10px 14px",
                        textAlign: i >= 2 ? "right" as const : "left" as const,
                        fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted,
                        letterSpacing: "0.08em", textTransform: "uppercase" as const,
                        borderBottom: `1px solid ${P.border}`,
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {signalsLoading ? (
                    <tr>
                      <td colSpan={4} className="text-center py-8">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto" style={{ color: P.accent }} />
                      </td>
                    </tr>
                  ) : signalsData && signalsData.length > 0 ? (
                    signalsData.map((signal) => (
                      <SignalRow 
                        key={signal.id} 
                        signal={signal} 
                        onClick={() => handleSignalClick(signal.id)}
                      />
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="text-center py-8" style={{ color: P.muted, fontFamily: FONT, fontSize: 13 }}>
                        No signals found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <p className="mt-3 text-xs" style={{ color: P.muted, fontFamily: FONT }}>
              Click on any signal to view detailed information including entry/exit prices, TP/SL levels, and failure analysis.
            </p>
          </div>
        ) : (
          <div className="text-center py-12" style={{ background: P.bg }}>
            <p style={{ fontFamily: FONT, fontSize: 14, color: P.muted }}>No data available</p>
          </div>
        )}
      </div>

      {/* Signal Detail Modal */}
      <Suspense fallback={null}>
        <SignalDetailModal
          signalId={selectedSignalId}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        />
      </Suspense>
    </>
  );
}
