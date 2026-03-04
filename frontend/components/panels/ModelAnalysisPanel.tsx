"use client";
/**
 * MODEL ANALYSIS PANEL — Multi-Timeframe Signal Analysis
 * 
 * Features:
 * - Model selection (ML, EMEL, Pulse1, Pulse2, Pulse3)
 * - Timeframe selector (5m, 15m, 30m, 1h, 4h, 1d)
 * - Per-model, per-timeframe, per-symbol analysis
 */

import { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Activity,
  ChevronDown,
  ChevronUp,
  Filter,
  Layers,
  Brain,
  Zap,
  Crosshair
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

// ── Types ───────────────────────────────────────────────────────────────────

interface ModelStats {
  total_signals: number;
  completed: number;
  stopped: number;
  expired: number;
  win_rate: number;
  target_rates: Record<string, number>;
  total_profit_pips: number;
  total_loss_pips: number;
  net_pips: number;
  avg_profit_pips: number;
  avg_loss_pips: number;
  max_profit_pips?: number;
  max_loss_pips?: number;
  risk_reward: number;
  by_symbol: Record<string, {
    total: number;
    completed: number;
    stopped: number;
    net_pips: number;
  }>;
  by_timeframe: Record<string, {
    total: number;
    completed: number;
    stopped: number;
    win_rate: number;
  }>;
  signals: any[];
  error?: string;
}

interface ModelSummary {
  total_signals: number;
  overall_win_rate: number;
  total_completed: number;
  total_stopped: number;
  by_timeframe: Record<string, {
    total: number;
    completed: number;
    stopped: number;
    win_rate: number;
  }>;
}

// ── Model Configuration ─────────────────────────────────────────────────────

const MODELS = [
  { id: "ml", label: "ML Model", icon: Brain, color: "#3B82F6", description: "Machine Learning predictions" },
  { id: "emel", label: "EMEL 9-Check", icon: Layers, color: "#8B5CF6", description: "9-Checkpoint validation" },
  { id: "pulse1", label: "Pulse 1", icon: Zap, color: "#22D3EE", description: "Algorithmic scalping" },
  { id: "pulse2", label: "Pulse 2", icon: Activity, color: "#10B981", description: "ML-enhanced scalping" },
  { id: "pulse3", label: "Pulse 3", icon: Crosshair, color: "#F59E0B", description: "Multi-timeframe analysis" },
];

const TIMEFRAMES = [
  { id: "5m", label: "5M", description: "5 Minutes" },
  { id: "15m", label: "15M", description: "15 Minutes" },
  { id: "30m", label: "30M", description: "30 Minutes" },
  { id: "1h", label: "1H", description: "1 Hour" },
  { id: "4h", label: "4H", description: "4 Hours" },
  { id: "1d", label: "1D", description: "1 Day" },
];

const SYMBOLS = [
  { id: "XAUUSD", label: "XAU/USD", icon: "⭐" },
  { id: "NDX.INDX", label: "NASDAQ", icon: "📈" },
  { id: "GDAXI.INDX", label: "DAX", icon: "🏛" },
  { id: "USOIL.FOREX", label: "US Oil", icon: "🛢" },
];

// Model -> Available Timeframes mapping
const MODEL_TIMEFRAMES: Record<string, string[]> = {
  ml: ["1h"],           // ML only on 1h
  emel: ["5m", "15m", "1h", "4h"],
  pulse1: ["5m", "15m"],
  pulse2: ["5m", "15m", "1h"],
  pulse3: ["1h"],       // Pulse3 only on 1h
};

// ── API Functions ───────────────────────────────────────────────────────────

async function fetchModelAnalysis(
  model: string,
  symbol?: string,
  timeframe?: string,
  days: number = 30
): Promise<ModelStats> {
  const params = new URLSearchParams();
  params.set("model", model);
  params.set("days", days.toString());
  if (symbol) params.set("symbol", symbol);
  if (timeframe) params.set("timeframe", timeframe);

  const res = await fetch(`${API_BASE}/api/learning/model-analysis?${params}`);
  if (!res.ok) throw new Error("Failed to fetch model analysis");
  return res.json();
}

async function fetchModelsSummary(days: number = 30, symbol?: string): Promise<Record<string, ModelSummary>> {
  const params = new URLSearchParams();
  params.set("days", days.toString());
  if (symbol) params.set("symbol", symbol);

  const res = await fetch(`${API_BASE}/api/learning/model-analysis/summary?${params}`);
  if (!res.ok) throw new Error("Failed to fetch models summary");
  const data = await res.json();
  return data.models;
}

// ── Components ──────────────────────────────────────────────────────────────

function TimeframeButton({
  tf,
  isActive,
  isAvailable,
  onClick
}: {
  tf: typeof TIMEFRAMES[0];
  isActive: boolean;
  isAvailable: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={!isAvailable}
      className="relative px-4 py-2 rounded-lg text-sm font-medium transition-all"
      style={{
        background: isActive ? "var(--accent-info)" : isAvailable ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.02)",
        color: isActive ? "#000" : isAvailable ? "var(--text-primary)" : "var(--text-muted)",
        opacity: isAvailable ? 1 : 0.4,
        cursor: isAvailable ? "pointer" : "not-allowed",
        border: `1px solid ${isActive ? "var(--accent-info)" : isAvailable ? "var(--border-subtle)" : "transparent"}`,
      }}
      title={isAvailable ? tf.description : "Not available for this model"}
    >
      {tf.label}
      {!isAvailable && (
        <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500/50" />
      )}
    </button>
  );
}

function ModelCard({
  model,
  isSelected,
  onClick,
  stats
}: {
  model: typeof MODELS[0];
  isSelected: boolean;
  onClick: () => void;
  stats?: ModelSummary;
}) {
  const Icon = model.icon;
  const winRate = stats?.overall_win_rate || 0;
  const totalSignals = stats?.total_signals || 0;

  return (
    <button
      onClick={onClick}
      className="flex flex-col p-4 rounded-xl transition-all text-left"
      style={{
        background: isSelected ? `${model.color}15` : "var(--bg-card)",
        border: `2px solid ${isSelected ? model.color : "var(--border-subtle)"}`,
      }}
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ background: `${model.color}20` }}
        >
          <Icon className="w-5 h-5" style={{ color: model.color }} />
        </div>
        <div>
          <p className="font-semibold text-white">{model.label}</p>
          <p className="text-xs text-gray-400">{model.description}</p>
        </div>
      </div>

      {stats && (
        <div className="mt-2 pt-2 border-t border-white/5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Win Rate</span>
            <span
              className="text-sm font-bold"
              style={{ color: winRate >= 50 ? "#10B981" : winRate >= 40 ? "#F59E0B" : "#EF4444" }}
            >
              {winRate.toFixed(1)}%
            </span>
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-gray-400">Signals</span>
            <span className="text-sm text-white">{totalSignals}</span>
          </div>
        </div>
      )}
    </button>
  );
}

function StatCard({ label, value, subtext, color = "white" }: { label: string; value: string; subtext?: string; color?: string }) {
  return (
    <div className="p-4 rounded-xl" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
      <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
      {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
    </div>
  );
}

function SymbolRow({ symbol, data }: { symbol: typeof SYMBOLS[0]; data: any }) {
  if (!data) return null;

  const winRate = data.total > 0 ? (data.completed / (data.completed + data.stopped)) * 100 : 0;
  const isProfit = data.net_pips > 0;

  return (
    <div className="flex items-center justify-between p-3 rounded-lg" style={{ background: "rgba(255,255,255,0.03)" }}>
      <div className="flex items-center gap-2">
        <span className="text-lg">{symbol.icon}</span>
        <span className="font-medium text-white">{symbol.label}</span>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <p className="text-xs text-gray-400">Signals</p>
          <p className="font-semibold text-white">{data.total}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Win Rate</p>
          <p className={`font-semibold ${winRate >= 50 ? "text-green-400" : "text-yellow-400"}`}>
            {winRate.toFixed(1)}%
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Net Pips</p>
          <p className={`font-semibold ${isProfit ? "text-green-400" : "text-red-400"}`}>
            {isProfit ? "+" : ""}{data.net_pips?.toFixed(1) || 0}p
          </p>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════════════════════

export default function ModelAnalysisPanel() {
  const [selectedModel, setSelectedModel] = useState<string>("emel");
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("1h");
  const [selectedSymbol, setSelectedSymbol] = useState<string | undefined>();
  const [days, setDays] = useState<number>(30);
  const [showSignals, setShowSignals] = useState(false);

  // Get available timeframes for selected model
  const availableTimeframes = MODEL_TIMEFRAMES[selectedModel] || ["1h"];

  // Auto-select first available timeframe when model changes
  useEffect(() => {
    if (!availableTimeframes.includes(selectedTimeframe)) {
      setSelectedTimeframe(availableTimeframes[0]);
    }
  }, [selectedModel, availableTimeframes, selectedTimeframe]);

  // Fetch models summary
  const { data: modelsSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ["models-summary", days, selectedSymbol],
    queryFn: () => fetchModelsSummary(days, selectedSymbol),
    staleTime: 60000,
  });

  // Fetch detailed analysis for selected model
  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ["model-analysis", selectedModel, selectedSymbol, selectedTimeframe, days],
    queryFn: () => fetchModelAnalysis(selectedModel, selectedSymbol, selectedTimeframe, days),
    staleTime: 60000,
  });

  const isLoading = summaryLoading || analysisLoading;

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "var(--bg-primary)", border: "1px solid var(--border-subtle)" }}>
      {/* ── Header ── */}
      <div className="px-6 py-4 border-b border-white/5" style={{ background: "var(--bg-surface)" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: "var(--accent-info)15" }}>
              <BarChart3 className="w-5 h-5" style={{ color: "var(--accent-info)" }} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Model Analysis</h2>
              <p className="text-sm text-gray-400">Multi-timeframe signal performance</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Period Selector */}
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg text-sm bg-white/5 border border-white/10 text-white"
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
              <option value={60}>60 Days</option>
            </select>

            {/* Symbol Filter */}
            <select
              value={selectedSymbol || ""}
              onChange={(e) => setSelectedSymbol(e.target.value || undefined)}
              className="px-3 py-1.5 rounded-lg text-sm bg-white/5 border border-white/10 text-white"
            >
              <option value="">All Symbols</option>
              {SYMBOLS.map(s => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* ── Model Selection ── */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">Select Model</h3>
          <div className="grid grid-cols-5 gap-3">
            {MODELS.map(model => (
              <ModelCard
                key={model.id}
                model={model}
                isSelected={selectedModel === model.id}
                onClick={() => setSelectedModel(model.id)}
                stats={modelsSummary?.[model.id]}
              />
            ))}
          </div>
        </div>

        {/* ── Timeframe Selector ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Timeframe</h3>
            <p className="text-xs text-gray-500">
              Available: {availableTimeframes.join(", ").toUpperCase()}
            </p>
          </div>
          <div className="flex gap-2">
            {TIMEFRAMES.map(tf => (
              <TimeframeButton
                key={tf.id}
                tf={tf}
                isActive={selectedTimeframe === tf.id}
                isAvailable={availableTimeframes.includes(tf.id)}
                onClick={() => setSelectedTimeframe(tf.id)}
              />
            ))}
          </div>
        </div>

        {/* ── Analysis Results ── */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : analysis?.error ? (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
            {analysis.error}
          </div>
        ) : analysis && analysis.total_signals > 0 ? (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4">
              <StatCard
                label="Total Signals"
                value={analysis.total_signals.toString()}
                subtext={`${analysis.completed}W / ${analysis.stopped}L`}
              />
              <StatCard
                label="Win Rate"
                value={`${analysis.win_rate.toFixed(1)}%`}
                subtext="Completed / Total"
                color={analysis.win_rate >= 50 ? "#10B981" : analysis.win_rate >= 40 ? "#F59E0B" : "#EF4444"}
              />
              <StatCard
                label="Net Pips"
                value={`${analysis.net_pips > 0 ? "+" : ""}${analysis.net_pips.toFixed(1)}p`}
                subtext={`Avg: ${analysis.avg_profit_pips.toFixed(1)}p`}
                color={analysis.net_pips >= 0 ? "#10B981" : "#EF4444"}
              />
              <StatCard
                label="Risk/Reward"
                value={analysis.risk_reward.toFixed(2)}
                subtext={`Max: ${analysis.max_profit_pips.toFixed(0)}p`}
                color={analysis.risk_reward >= 1.5 ? "#10B981" : "#F59E0B"}
              />
            </div>

            {/* Target Hit Rates */}
            {Object.keys(analysis.target_rates || {}).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">Target Hit Rates</h3>
                <div className="grid grid-cols-4 gap-3">
                  {Object.entries(analysis.target_rates).map(([tp, rate]) => (
                    <div key={tp} className="p-3 rounded-lg" style={{ background: "var(--bg-card)" }}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">{tp}</span>
                        <span className={`text-sm font-bold ${rate >= 40 ? "text-green-400" : rate >= 25 ? "text-yellow-400" : "text-red-400"}`}>
                          {rate.toFixed(0)}%
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${rate}%`,
                            background: rate >= 40 ? "#10B981" : rate >= 25 ? "#F59E0B" : "#EF4444"
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Per Symbol Performance */}
            {Object.keys(analysis.by_symbol || {}).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">Per Symbol Performance</h3>
                <div className="space-y-2">
                  {SYMBOLS.map(sym => {
                    const data = analysis.by_symbol[sym.id];
                    return data ? <SymbolRow key={sym.id} symbol={sym} data={data} /> : null;
                  })}
                </div>
              </div>
            )}

            {/* Recent Signals Toggle */}
            <div>
              <button
                onClick={() => setShowSignals(!showSignals)}
                className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                {showSignals ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                {showSignals ? "Hide" : "Show"} Recent Signals ({analysis.signals?.length || 0})
              </button>

              {showSignals && analysis.signals && (
                <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
                  {analysis.signals.map((sig: any) => (
                    <div
                      key={sig.id}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ background: "rgba(255,255,255,0.03)" }}
                    >
                      <div className="flex items-center gap-3">
                        <span className={sig.ml_direction === "BUY" ? "text-green-400" : "text-red-400"}>
                          {sig.ml_direction === "BUY" ? "▲" : "▼"} {sig.ml_direction}
                        </span>
                        <span className="text-white">{SYMBOLS.find(s => s.id === sig.symbol)?.label || sig.symbol}</span>
                        <span className="text-gray-500 text-sm">{sig.timeframe}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`text-sm ${sig.status === "completed" ? "text-green-400" : sig.status === "stopped" ? "text-red-400" : "text-gray-400"}`}>
                          {sig.status}
                        </span>
                        <span className="text-sm text-gray-400">
                          {new Date(sig.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Target className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No signals found for {MODELS.find(m => m.id === selectedModel)?.label} on {selectedTimeframe.toUpperCase()}</p>
            <p className="text-sm mt-1">Try selecting a different timeframe or model</p>
          </div>
        )}
      </div>
    </div>
  );
}
