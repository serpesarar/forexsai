"use client";
/**
 * Signal Detail Modal
 * Shows comprehensive information about a trading signal including:
 * - Signal source (which panel generated it)
 * - Entry price and timestamp
 * - TP/SL levels and results
 * - Duration until TP/SL
 * - PNL value
 */

import { useState, useEffect } from "react";
import { 
  X, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  StopCircle, 
  Clock, 
  DollarSign,
  BarChart3,
  Calendar,
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Zap,
  Brain,
  Layers
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

// ── Types ───────────────────────────────────────────────────────────────────

interface SignalCheck {
  id: string;
  check_time: string;
  current_price: number;
  session_high: number;
  session_low: number;
  profit_pips: number;
  cumulative_high_pips: number;
  cumulative_low_pips: number;
  target_status: Record<string, boolean>;
}

interface SignalDetail {
  signal: {
    id: string;
    symbol: string;
    ml_direction: "BUY" | "SELL" | "HOLD";
    ml_confidence: number;
    ml_entry_price: number;
    ml_target_price: number;
    ml_stop_price: number;
    claude_direction?: string;
    claude_confidence?: number;
    model_type?: string;
    strategy?: string;
    timeframe?: string;
    status: "active" | "completed" | "stopped" | "expired";
    targets_hit?: Record<string, boolean>;
    highest_profit_pips: number;
    lowest_drawdown_pips: number;
    exit_price?: number;
    exit_time?: string;
    created_at: string;
    factors?: Record<string, any>;
  };
  checks: SignalCheck[];
  failure?: {
    failure_type: string;
    market_regime: string;
    confluence_score: number;
    entry_indicators?: Record<string, any>;
    failure_indicators?: Record<string, any>;
    contradiction_flags?: Record<string, string>;
  };
}

// ── Helper Functions ────────────────────────────────────────────────────────

function formatDuration(minutes: number | null): string {
  if (minutes === null || minutes === undefined) return "—";
  if (minutes < 60) return `${Math.round(minutes)}m`;
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return `${hours}h ${mins}m`;
}

function formatDate(isoString: string): string {
  if (!isoString) return "—";
  const date = new Date(isoString);
  return date.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStatusConfig(status: string) {
  switch (status) {
    case "completed":
      return {
        label: "Completed (Target Hit)",
        color: "text-green-400",
        bg: "bg-green-400/10",
        border: "border-green-400/20",
        icon: CheckCircle2,
      };
    case "stopped":
      return {
        label: "Stopped (SL Hit)",
        color: "text-red-400",
        bg: "bg-red-400/10",
        border: "border-red-400/20",
        icon: XCircle,
      };
    case "expired":
      return {
        label: "Expired",
        color: "text-yellow-400",
        bg: "bg-yellow-400/10",
        border: "border-yellow-400/20",
        icon: AlertCircle,
      };
    case "active":
    default:
      return {
        label: "Active",
        color: "text-blue-400",
        bg: "bg-blue-400/10",
        border: "border-blue-400/20",
        icon: Activity,
      };
  }
}

function getSourceLabel(modelType?: string, strategy?: string): string {
  const source = modelType || strategy || "ML";
  const upper = source.toUpperCase();
  
  if (upper.includes("PULSE_V3") || upper.includes("PULSE3")) return "Pulse V3";
  if (upper.includes("PULSE_ML") || upper.includes("PULSE2")) return "Pulse ML";
  if (upper.includes("PULSE")) return "Pulse";
  if (upper.includes("EMEL")) return "EMEL";
  if (upper.includes("CLEAR")) return "Clear Trend";
  if (upper.includes("SMC")) return "SMC";
  if (upper.includes("MTF")) return "MTF Analysis";
  return upper;
}

function getSourceColor(source: string): string {
  const upper = source.toUpperCase();
  if (upper.includes("PULSE")) return "#3B82F6"; // blue
  if (upper.includes("EMEL")) return "#8B5CF6"; // purple
  if (upper.includes("CLEAR")) return "#10B981"; // green
  if (upper.includes("SMC")) return "#F59E0B"; // amber
  return "#6B7280"; // gray
}

// ── Components ──────────────────────────────────────────────────────────────

interface SignalDetailModalProps {
  signalId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function SignalDetailModal({ signalId, isOpen, onClose }: SignalDetailModalProps) {
  const [detail, setDetail] = useState<SignalDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "checks" | "analysis">("overview");

  useEffect(() => {
    if (isOpen && signalId) {
      fetchSignalDetail(signalId);
    }
  }, [isOpen, signalId]);

  const fetchSignalDetail = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/learning/signal/${id}`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setDetail(data);
      }
    } catch (e) {
      setError("Failed to load signal details");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const signal = detail?.signal;
  const statusConfig = signal ? getStatusConfig(signal.status) : null;
  const StatusIcon = statusConfig?.icon;

  // Calculate PNL
  let pnlPips: number | null = null;
  let pnlClass = "text-gray-400";
  if (signal?.exit_price && signal.ml_entry_price) {
    const diff = signal.status === "completed" 
      ? signal.highest_profit_pips 
      : signal.status === "stopped"
      ? -Math.abs(signal.lowest_drawdown_pips || 0)
      : null;
    if (diff !== null) {
      pnlPips = diff;
      pnlClass = diff > 0 ? "text-green-400" : diff < 0 ? "text-red-400" : "text-gray-400";
    }
  }

  // Calculate duration
  let duration: number | null = null;
  if (signal?.created_at && signal?.exit_time) {
    const created = new Date(signal.created_at).getTime();
    const exited = new Date(signal.exit_time).getTime();
    duration = (exited - created) / (1000 * 60); // minutes
  }

  // Parse targets hit
  const targetsHit = signal?.targets_hit || {};
  const hitTargetsList = Object.entries(targetsHit)
    .filter(([_, hit]) => hit)
    .map(([name]) => name);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div 
        className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border border-gray-700/50"
        style={{ background: "linear-gradient(180deg, #0F1419 0%, #1A1F2E 100%)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700/50">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ 
                background: signal?.ml_direction === "BUY" 
                  ? "rgba(34, 197, 94, 0.15)" 
                  : "rgba(239, 68, 68, 0.15)",
                border: `1px solid ${signal?.ml_direction === "BUY" ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)"}`
              }}
            >
              {signal?.ml_direction === "BUY" ? (
                <TrendingUp className="w-5 h-5 text-green-400" />
              ) : (
                <TrendingDown className="w-5 h-5 text-red-400" />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                {signal?.symbol || "Loading..."} {signal?.ml_direction}
              </h2>
              <p className="text-sm text-gray-400">
                {signal ? formatDate(signal.created_at) : "—"}
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4 border-b border-gray-700/50">
          {[
            { id: "overview", label: "Overview", icon: BarChart3 },
            { id: "checks", label: "Price Checks", icon: Activity },
            { id: "analysis", label: "Analysis", icon: Brain },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-all rounded-t-lg ${
                  isActive 
                    ? "text-blue-400 bg-blue-400/10 border-t border-x border-blue-400/20" 
                    : "text-gray-400 hover:text-gray-300"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12 text-red-400">
              <AlertCircle className="w-5 h-5 mr-2" />
              {error}
            </div>
          ) : !signal ? (
            <div className="text-center py-12 text-gray-400">
              Signal not found
            </div>
          ) : (
            <>
              {/* OVERVIEW TAB */}
              {activeTab === "overview" && (
                <div className="space-y-6">
                  {/* Status Banner */}
                  {statusConfig && StatusIcon && (
                    <div className={`flex items-center gap-3 p-4 rounded-xl ${statusConfig.bg} border ${statusConfig.border}`}>
                      <StatusIcon className={`w-6 h-6 ${statusConfig.color}`} />
                      <div>
                        <p className={`font-semibold ${statusConfig.color}`}>{statusConfig.label}</p>
                        {hitTargetsList.length > 0 && (
                          <p className="text-sm text-gray-400">
                            Targets hit: {hitTargetsList.join(", ")}
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Key Stats Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Source */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-2 text-gray-400 mb-2">
                        <Layers className="w-4 h-4" />
                        <span className="text-xs uppercase tracking-wider">Source</span>
                      </div>
                      <p className="text-white font-medium" style={{ color: getSourceColor(getSourceLabel(signal.model_type, signal.strategy)) }}>
                        {getSourceLabel(signal.model_type, signal.strategy)}
                      </p>
                    </div>

                    {/* Confidence */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-2 text-gray-400 mb-2">
                        <Zap className="w-4 h-4" />
                        <span className="text-xs uppercase tracking-wider">Confidence</span>
                      </div>
                      <p className="text-white font-medium">
                        {signal.ml_confidence ? `${(signal.ml_confidence * 100).toFixed(1)}%` : "—"}
                      </p>
                    </div>

                    {/* Duration */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-2 text-gray-400 mb-2">
                        <Clock className="w-4 h-4" />
                        <span className="text-xs uppercase tracking-wider">Duration</span>
                      </div>
                      <p className="text-white font-medium">{formatDuration(duration)}</p>
                    </div>

                    {/* PNL */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-2 text-gray-400 mb-2">
                        <DollarSign className="w-4 h-4" />
                        <span className="text-xs uppercase tracking-wider">Result</span>
                      </div>
                      <p className={`font-medium ${pnlClass}`}>
                        {pnlPips !== null ? `${pnlPips > 0 ? "+" : ""}${pnlPips.toFixed(1)} pips` : "—"}
                      </p>
                    </div>
                  </div>

                  {/* Price Levels */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Entry & Exit */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Entry & Exit
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Entry Price</span>
                          <span className="text-white font-mono">{signal.ml_entry_price?.toFixed(2) || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Exit Price</span>
                          <span className="text-white font-mono">{signal.exit_price?.toFixed(2) || "—"}</span>
                        </div>
                        {signal.exit_time && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Exit Time</span>
                            <span className="text-gray-300">{formatDate(signal.exit_time)}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Target Levels */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
                        <Target className="w-4 h-4" />
                        Target Levels
                      </h3>
                      <div className="space-y-2">
                        {signal.ml_target_price && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">ML Target</span>
                            <span className="text-green-400 font-mono">{signal.ml_target_price.toFixed(2)}</span>
                          </div>
                        )}
                        {signal.ml_stop_price && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Stop Loss</span>
                            <span className="text-red-400 font-mono">{signal.ml_stop_price.toFixed(2)}</span>
                          </div>
                        )}
                        <div className="pt-2 mt-2 border-t border-white/10">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-400">Highest Profit</span>
                            <span className="text-green-400 font-mono">+{signal.highest_profit_pips?.toFixed(1) || "0"} pips</span>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-gray-400">Max Drawdown</span>
                            <span className="text-red-400 font-mono">{signal.lowest_drawdown_pips?.toFixed(1) || "0"} pips</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Claude Info */}
                  {signal.claude_direction && (
                    <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                      <div className="flex items-center gap-2 mb-3">
                        <Brain className="w-4 h-4 text-purple-400" />
                        <span className="text-sm font-medium text-purple-300">Claude AI Analysis</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Direction</span>
                          <span className={signal.claude_direction === signal.ml_direction ? "text-green-400" : "text-yellow-400"}>
                            {signal.claude_direction}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Confidence</span>
                          <span className="text-white">
                            {signal.claude_confidence ? `${(signal.claude_confidence * 100).toFixed(1)}%` : "—"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* CHECKS TAB */}
              {activeTab === "checks" && (
                <div className="space-y-4">
                  {detail.checks.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">
                      No price check records available
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-gray-400 border-b border-gray-700">
                            <th className="text-left py-3 px-2">Time</th>
                            <th className="text-right py-3 px-2">Price</th>
                            <th className="text-right py-3 px-2">High</th>
                            <th className="text-right py-3 px-2">Low</th>
                            <th className="text-right py-3 px-2">Profit</th>
                            <th className="text-center py-3 px-2">Targets</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.checks.map((check, idx) => (
                            <tr key={check.id || idx} className="border-b border-gray-800/50 hover:bg-white/5">
                              <td className="py-3 px-2 text-gray-300">
                                {formatDate(check.check_time)}
                              </td>
                              <td className="py-3 px-2 text-right font-mono text-white">
                                {check.current_price?.toFixed(2)}
                              </td>
                              <td className="py-3 px-2 text-right font-mono text-green-400/70">
                                {check.session_high?.toFixed(2)}
                              </td>
                              <td className="py-3 px-2 text-right font-mono text-red-400/70">
                                {check.session_low?.toFixed(2)}
                              </td>
                              <td className={`py-3 px-2 text-right font-mono ${check.profit_pips >= 0 ? "text-green-400" : "text-red-400"}`}>
                                {check.profit_pips >= 0 ? "+" : ""}{check.profit_pips?.toFixed(1)}
                              </td>
                              <td className="py-3 px-2 text-center">
                                <div className="flex gap-1 justify-center">
                                  {Object.entries(check.target_status || {}).map(([name, hit]) => (
                                    <span 
                                      key={name}
                                      className={`text-xs px-1.5 py-0.5 rounded ${
                                        hit 
                                          ? "bg-green-500/20 text-green-400" 
                                          : "bg-gray-700/50 text-gray-500"
                                      }`}
                                    >
                                      {name.replace("TP", "")}
                                    </span>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ANALYSIS TAB */}
              {activeTab === "analysis" && (
                <div className="space-y-6">
                  {detail.failure ? (
                    <>
                      {/* Failure Analysis */}
                      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                        <h3 className="text-sm font-medium text-red-300 mb-4 flex items-center gap-2">
                          <AlertCircle className="w-4 h-4" />
                          Failure Analysis
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Failure Type</span>
                            <span className="text-white capitalize">{detail.failure.failure_type?.replace("_", " ")}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Market Regime</span>
                            <span className="text-white capitalize">{detail.failure.market_regime}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Confluence Score</span>
                            <span className="text-white">{detail.failure.confluence_score}/5</span>
                          </div>
                        </div>
                      </div>

                      {/* Contradictions */}
                      {detail.failure.contradiction_flags && Object.keys(detail.failure.contradiction_flags).length > 0 && (
                        <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                          <h3 className="text-sm font-medium text-yellow-300 mb-3">Contradicting Indicators at Entry</h3>
                          <div className="space-y-2">
                            {Object.entries(detail.failure.contradiction_flags).map(([key, value]) => (
                              <div key={key} className="flex items-center gap-2 text-sm">
                                <XCircle className="w-4 h-4 text-yellow-500" />
                                <span className="text-gray-300">{key.replace(/_/g, " ")}:</span>
                                <span className="text-yellow-400">{value}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-12 text-gray-400">
                      {signal.status === "completed" ? (
                        <div className="space-y-2">
                          <CheckCircle2 className="w-12 h-12 mx-auto text-green-500" />
                          <p>Signal completed successfully</p>
                          {hitTargetsList.length > 0 && (
                            <p className="text-sm text-gray-500">Hit {hitTargetsList.join(", ")}</p>
                          )}
                        </div>
                      ) : signal.status === "active" ? (
                        <div className="space-y-2">
                          <Activity className="w-12 h-12 mx-auto text-blue-500" />
                          <p>Signal is still active</p>
                          <p className="text-sm text-gray-500">Check back later for analysis</p>
                        </div>
                      ) : (
                        <p>No failure analysis available</p>
                      )}
                    </div>
                  )}

                  {/* Entry Factors */}
                  {signal.factors && Object.keys(signal.factors).length > 0 && (
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <h3 className="text-sm font-medium text-gray-300 mb-4">Entry Context (Factors)</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(signal.factors)
                          .filter(([key]) => !["strategy", "source"].includes(key))
                          .slice(0, 12)
                          .map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <span className="text-gray-500 block truncate">{key.replace(/_/g, " ")}</span>
                              <span className="text-gray-300 font-mono">
                                {typeof value === "number" ? value.toFixed(2) : String(value)}
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700/50 flex justify-between items-center">
          <div className="text-xs text-gray-500">
            Signal ID: {signalId?.slice(0, 8)}...
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-sm transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
