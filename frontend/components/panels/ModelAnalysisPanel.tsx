"use client";
/**
 * MODEL ANALYSIS PANEL — Multi-Timeframe Signal Analysis
 * 
 * Features:
 * - Model selection (ML, EMEL, Pulse1, Pulse2, Pulse3)
 * - Timeframe selector (5m, 15m, 30m, 1h, 4h, 1d)
 * - Per-model, per-timeframe, per-symbol analysis
 */

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Target,
  Activity,
  ChevronDown,
  ChevronUp,
  Layers,
  Brain,
  Zap,
  Crosshair
} from "lucide-react";
import { ModelPerformanceModal } from "./ModelPerformanceModal";
import { getApiBase } from "../../lib/api/base";
import { useSignalCountdown } from "../../hooks/useSignalCountdown";

const API_BASE = getApiBase();

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
  { id: "emel_inverse", label: "EMEL Inverse", icon: Layers, color: "#D946EF", description: "Reverse signal strategy" },
  { id: "pulse1", label: "Pulse 1", icon: Zap, color: "#22D3EE", description: "Algorithmic scalping" },
  { id: "pulse2", label: "Pulse 2", icon: Activity, color: "#10B981", description: "ML-enhanced scalping" },
  { id: "pulse3", label: "Pulse 3", icon: Crosshair, color: "#F59E0B", description: "Multi-timeframe analysis" },
  { id: "smc", label: "Smart Money Zones", icon: Crosshair, color: "#A855F7", description: "Order block and liquidity-based signals" },
];

const TIMEFRAMES = [
  { id: "5m", label: "5M", description: "5 Minutes" },
  { id: "15m", label: "15M", description: "15 Minutes" },
  { id: "1h", label: "1H", description: "1 Hour" },
  { id: "4h", label: "4H", description: "4 Hours" },
];

const SYMBOLS = [
  { id: "XAUUSD", label: "XAU/USD", icon: "⭐" },
  { id: "NDX.INDX", label: "NASDAQ", icon: "📈" },
  { id: "GDAXI.INDX", label: "DAX", icon: "🏛" },
  { id: "USOIL.FOREX", label: "US Oil", icon: "🛢" },
];

// Model -> Available Timeframes mapping
const MODEL_TIMEFRAMES: Record<string, string[]> = {
  ml: ["1h"],
  emel: ["5m", "15m", "1h", "4h"],
  emel_inverse: ["5m", "15m", "1h", "4h"],
  pulse1: ["5m", "15m"],
  pulse2: ["5m", "15m", "1h"],
  pulse3: ["1h"],
  smc: ["5m", "15m", "1h", "4h"],
};

// ── API Functions ───────────────────────────────────────────────────────────

async function fetchModelAnalysis(
  model: string,
  symbol?: string,
  timeframe?: string,
  days: number = 0
): Promise<ModelStats> {
  const params = new URLSearchParams();
  params.set("model", model);
  params.set("days", days.toString());
  if (symbol) params.set("symbol", symbol);
  if (timeframe) params.set("timeframe", timeframe);

  const res = await fetch(`${API_BASE}/api/learning/model-analysis?${params}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch model analysis");
  return res.json();
}

async function fetchModelsSummary(days: number = 0, symbol?: string): Promise<Record<string, ModelSummary>> {
  const params = new URLSearchParams();
  params.set("days", days.toString());
  if (symbol) params.set("symbol", symbol);

  const res = await fetch(`${API_BASE}/api/learning/model-analysis/summary?${params}`, { cache: "no-store" });
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

const TRANSLATIONS: Record<string, Record<string, string>> = {
  en: {
    noSignals: "No active signals found for this model across timeframes.",
    symbol: "Symbol",
    consensus: "Consensus",
    mixed: "MIXED",
    strongBuy: "STRONG BUY",
    strongSell: "STRONG SELL",
    buy: "BUY",
    sell: "SELL",
    hold: "HOLD",
    matrixTitle: "Timeframe Matrix (Current)",
    matrixDesc: "Real-time active signals across all timeframes",
    updating: "Updating...",
    selectModel: "Select Model",
    timeframe: "Timeframe",
    available: "Available",
    totalSignals: "Total Signals",
    winRate: "Win Rate",
    completedTotal: "Completed / Total",
    netPips: "Net Pips",
    avg: "Avg",
    riskReward: "Risk/Reward",
    max: "Max",
    targetHitRates: "Target Hit Rates",
    noSignalsPeriod: "No signals found for {model} in the selected period.",
    tryDiff: "Try selecting a different timeframe or model",
    modelAnalysis: "Model Analysis",
    multiTf: "Multi-timeframe signal performance",
    days7: "7 Days",
    days14: "14 Days",
    days30: "30 Days",
    days60: "60 Days",
    days90: "90 Days",
    days365: "365 Days",
    allTime: "All Time",
    allSymbols: "All Symbols"
  },
  tr: {
    noSignals: "Bu model için zaman dilimlerinde aktif sinyal bulunamadı.",
    symbol: "Sembol",
    consensus: "Ortak Karar",
    mixed: "KARIŞIK",
    strongBuy: "GÜÇLÜ AL",
    strongSell: "GÜÇLÜ SAT",
    buy: "AL",
    sell: "SAT",
    hold: "BEKLE",
    matrixTitle: "Zaman Dilimi Matrisi (Anlık)",
    matrixDesc: "Tüm zaman dilimlerindeki gerçek zamanlı aktif sinyaller",
    updating: "Güncelleniyor...",
    selectModel: "Model Seçin",
    timeframe: "Zaman Dilimi",
    available: "Mevcut",
    totalSignals: "Toplam Sinyal",
    winRate: "Kazanma Oranı",
    completedTotal: "Tamamlanan / Toplam",
    netPips: "Net Pip",
    avg: "Ort",
    riskReward: "Risk/Ödül",
    max: "Maks",
    targetHitRates: "Hedef Vurma Oranları",
    noSignalsPeriod: "Seçili periyotta {model} için sinyal bulunamadı.",
    tryDiff: "Farklı bir model veya zaman dilimi seçmeyi deneyin",
    modelAnalysis: "Model Analizi",
    multiTf: "Çoklu zaman dilimi sinyal performansı",
    days7: "7 Gün",
    days14: "14 Gün",
    days30: "30 Gün",
    days60: "60 Gün",
    days90: "90 Gün",
    days365: "365 Gün",
    allTime: "Tüm Zamanlar",
    allSymbols: "Tüm Semboller"
  }
};

function useModelTranslations() {
  const [lang, setLang] = useState<string>("en");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("language");
      if (stored) {
        setLang(stored);
      } else if (navigator.language?.startsWith("tr")) {
        setLang("tr");
      }
    }
  }, []);

  return TRANSLATIONS[lang] || TRANSLATIONS["en"];
}

// ════════════════════════════════════════════════════════════════════════════
// TIMEFRAME MATRIX COMPONENT
// ════════════════════════════════════════════════════════════════════════════

function TimeframeMatrix({
  matrixData,
  timeframes,
  t,
  onRowClick,
}: {
  matrixData: any;
  timeframes: string[];
  t: Record<string, string>;
  onRowClick: (symbol: string) => void;
}) {
  if (!matrixData || Object.keys(matrixData).length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 border border-white/5 rounded-xl bg-white/5">
        {t.noSignals}
      </div>
    );
  }

  const tfs = timeframes;

  return (
    <div className="overflow-x-auto rounded-xl border border-white/5 bg-[#141C2B] shadow-[0_4px_24px_rgba(0,0,0,0.2)]">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr style={{ background: "rgba(11,15,23,0.6)" }}>
            <th className="py-4 px-5 text-[11px] font-semibold text-[#9AA4B2] uppercase tracking-[0.08em] border-b border-white/5">{t.symbol}</th>
            {tfs.map(tf => (
              <th key={tf} className="py-4 px-5 text-[11px] font-semibold text-[#9AA4B2] uppercase tracking-[0.08em] border-b border-white/5 text-center">{tf}</th>
            ))}
            <th className="py-4 px-5 text-[11px] font-semibold text-[#9AA4B2] uppercase tracking-[0.08em] border-b border-white/5 text-right">{t.consensus}</th>
          </tr>
        </thead>
        <tbody>
          {SYMBOLS.map(symbol => {
            const rowData = matrixData[symbol.id];
            if (!rowData) return null;

            // Calculate consensus
            let buyScore = 0;
            let sellScore = 0;
            let totalWeights = 0;

            tfs.forEach(tf => {
              const cell = rowData[tf];
              if (cell && cell.age_hours < 24) { // Only count if recent
                const weight = tf === "1d" ? 2 : tf === "4h" ? 1.5 : 1;
                if (cell.direction === "BUY") {
                  buyScore += cell.confidence * weight;
                  totalWeights += weight;
                } else if (cell.direction === "SELL") {
                  sellScore += cell.confidence * weight;
                  totalWeights += weight;
                }
              }
            });

            let consensus = t.mixed;
            let consColor = "text-yellow-400";
            let consScore = 0;

            if (totalWeights > 0) {
              const avgBuy = buyScore / totalWeights;
              const avgSell = sellScore / totalWeights;

              if (avgBuy > avgSell + 10) {
                consensus = avgBuy > 65 ? t.strongBuy : t.buy;
                consColor = "text-green-400";
                consScore = avgBuy;
              } else if (avgSell > avgBuy + 10) {
                consensus = avgSell > 65 ? t.strongSell : t.sell;
                consColor = "text-red-400";
                consScore = avgSell;
              } else {
                consensus = t.mixed;
                consColor = "text-yellow-400";
                consScore = Math.max(avgBuy, avgSell);
              }
            }

            return (
              <tr
                key={symbol.id}
                className="border-b border-white/5 hover:bg-[#1A2333] transition-colors cursor-pointer group"
                onClick={() => onRowClick(symbol.id)}
              >
                <td className="py-4 px-5 font-semibold text-[#E6EDF3] flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#0B0F17] flex items-center justify-center border border-white/5 group-hover:border-blue-500/30 transition-colors">
                    <span className="text-sm">{symbol.icon}</span>
                  </div>
                  {symbol.label}
                </td>
                {tfs.map(tf => {
                  const cell = rowData[tf];
                  if (!cell) return <td key={tf} className="py-4 px-5 text-center text-[#6B7280]">-</td>;

                  const isOld = cell.age_hours > 24;
                  const isHold = cell.direction === "HOLD";
                  const colorMatch = cell.direction === "BUY" ? "text-[#16C784]" : cell.direction === "SELL" ? "text-[#EA3943]" : "text-[#F5A623]";
                  const dotColor = cell.direction === "BUY" ? "bg-[#16C784]" : cell.direction === "SELL" ? "bg-[#EA3943]" : "bg-[#F5A623]";

                  return (
                    <td key={tf} className={`py-4 px-5 text-center ${isOld ? 'opacity-40' : ''}`} title={isOld ? 'Signal older than 24h' : ''}>
                      <div className="inline-flex items-center justify-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-lg border border-white/5">
                        <span className={`w-2 h-2 rounded-full ${isHold ? 'bg-transparent border border-[#6B7280]' : dotColor} ${!isHold ? 'shadow-[0_0_8px_currentColor] opacity-80' : ''}`}></span>
                        <span className={`font-semibold text-sm ${colorMatch}`}>{isHold ? '-' : cell.confidence.toFixed(0)}</span>
                      </div>
                    </td>
                  );
                })}
                <td className="py-4 px-5 text-right">
                  <div className={`font-bold text-[13px] tracking-wide ${consColor} bg-[#0B0F17] inline-block px-3 py-1.5 rounded-lg border border-white/5`}>
                    {consensus} <span className="text-[#6B7280] text-xs font-medium ml-1">({consScore.toFixed(0)})</span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════════════════════

export default function ModelAnalysisPanel() {
  const t = useModelTranslations();
  const { formattedTime: refreshAge, markRefreshed } = useSignalCountdown("model_analysis", 300);

  const [selectedModel, setSelectedModel] = useState<string>("emel");
  const [selectedSymbol, setSelectedSymbol] = useState<string | undefined>();
  const [days, setDays] = useState<number>(0);
  const [showSignals, setShowSignals] = useState(false);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalSymbol, setModalSymbol] = useState<string>("NDX.INDX");

  // Fetch models summary
  const { data: modelsSummary, isLoading: summaryLoading, dataUpdatedAt: summaryUpdatedAt } = useQuery({
    queryKey: ["models-summary", days, selectedSymbol],
    queryFn: () => fetchModelsSummary(days, selectedSymbol),
    staleTime: 60000,
    refetchInterval: 60000,
  });

  // Fetch matrix data (current cross-timeframe signals)
  const { data: matrixData, isLoading: matrixLoading, dataUpdatedAt: matrixUpdatedAt } = useQuery({
    queryKey: ["signals-matrix", selectedModel],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/learning/signals/matrix?model=${selectedModel}`);
      if (!res.ok) throw new Error("Failed to fetch matrix");
      const data = await res.json();
      return data.matrix;
    },
    staleTime: 30000,
    refetchInterval: 60000,
  });

  // Fetch detailed analysis for selected model (aggregated across all timeframes since matrix shows current state)
  const { data: analysis, isLoading: analysisLoading, dataUpdatedAt: analysisUpdatedAt } = useQuery({
    queryKey: ["model-analysis", selectedModel, selectedSymbol, undefined, days],
    queryFn: () => fetchModelAnalysis(selectedModel, selectedSymbol, undefined, days),
    staleTime: 60000,
    refetchInterval: 60000,
  });

  useEffect(() => {
    const latestRefreshAt = Math.max(summaryUpdatedAt || 0, matrixUpdatedAt || 0, analysisUpdatedAt || 0);
    if (latestRefreshAt > 0) {
      markRefreshed();
    }
  }, [summaryUpdatedAt, matrixUpdatedAt, analysisUpdatedAt, markRefreshed]);

  const isLoading = summaryLoading || analysisLoading;
  const matrixTimeframes = MODEL_TIMEFRAMES[selectedModel] || ["1h"];

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
              <h2 className="text-lg font-semibold text-white">{t.modelAnalysis}</h2>
              <p className="text-sm text-gray-400">{t.multiTf}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div
              className="flex items-center gap-2 rounded-xl border px-3.5 py-2 text-[12px] font-mono font-bold tracking-wide"
              style={{
                background: "color-mix(in srgb, var(--accent-info) 12%, rgba(255,255,255,0.04))",
                borderColor: "color-mix(in srgb, var(--accent-info) 35%, rgba(255,255,255,0.08))",
                color: "var(--text-primary)",
                boxShadow: "0 0 0 1px rgba(255,255,255,0.02) inset, 0 8px 18px rgba(0,0,0,0.22)",
              }}
            >
              <div className="w-2 h-2 rounded-full bg-success" style={{ boxShadow: "0 0 10px var(--accent-positive)" }} />
              {refreshAge}
            </div>
            {/* Period Selector */}
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg text-sm bg-white/5 border border-white/10 text-white"
            >
              <option value={7}>{t.days7}</option>
              <option value={14}>{t.days14}</option>
              <option value={30}>{t.days30}</option>
              <option value={60}>{t.days60}</option>
              <option value={90}>{t.days90}</option>
              <option value={365}>{t.days365}</option>
              <option value={0}>{t.allTime}</option>
            </select>

            {/* Symbol Filter */}
            <select
              value={selectedSymbol || ""}
              onChange={(e) => setSelectedSymbol(e.target.value || undefined)}
              className="px-3 py-1.5 rounded-lg text-sm bg-white/5 border border-white/10 text-white"
            >
              <option value="">{t.allSymbols}</option>
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
          <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">{t.selectModel}</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-7 gap-3">
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

        {/* ── Timeframe Heatmap Matrix ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                Timeframe Matrix (Current)
              </h3>
              <p className="text-xs text-gray-500 mt-1">
                Real-time active signals across all timeframes
              </p>
            </div>
            {matrixLoading && <div className="text-xs text-gray-500 animate-pulse">Updating...</div>}
          </div>

          <TimeframeMatrix
            matrixData={matrixData}
            timeframes={matrixTimeframes}
            t={t}
            onRowClick={(symbolId) => {
              setModalSymbol(symbolId);
              setIsModalOpen(true);
            }}
          />
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
                label={t.totalSignals}
                value={analysis.total_signals.toString()}
                subtext={`${analysis.completed}W / ${analysis.stopped}L`}
              />
              <StatCard
                label={t.winRate}
                value={`${analysis.win_rate.toFixed(1)}%`}
                subtext={t.completedTotal}
                color={analysis.win_rate >= 50 ? "#10B981" : analysis.win_rate >= 40 ? "#F59E0B" : "#EF4444"}
              />
              <StatCard
                label={t.netPips}
                value={`${analysis.net_pips > 0 ? "+" : ""}${analysis.net_pips.toFixed(1)}p`}
                subtext={`${t.avg}: ${analysis.avg_profit_pips.toFixed(1)}p`}
                color={analysis.net_pips >= 0 ? "#10B981" : "#EF4444"}
              />
              <StatCard
                label={t.riskReward}
                value={analysis.risk_reward.toFixed(2)}
                subtext={`${t.max}: ${analysis.max_profit_pips.toFixed(0)}p`}
                color={analysis.risk_reward >= 1.5 ? "#10B981" : "#F59E0B"}
              />
            </div>

            {/* Target Hit Rates */}
            {Object.keys(analysis.target_rates || {}).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">{t.targetHitRates}</h3>
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
            <p>{t.noSignalsPeriod.replace('{model}', MODELS.find(m => m.id === selectedModel)?.label || '')}</p>
            <p className="text-sm mt-1">{t.tryDiff}</p>
          </div>
        )}
      </div>

      {/* ── Detailed Analytics Modal ── */}
      <ModelPerformanceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        symbol={modalSymbol}
        model={selectedModel}
        days={days}
      />
    </div>
  );
}
