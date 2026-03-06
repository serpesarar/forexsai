"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { PanelInfoButton } from "./PanelInfoButton";
import {
  BrainIcon as Brain,
  ArrowUpIcon as TrendingUp,
  ArrowDownIcon as TrendingDown,
  TargetIcon as Target,
  AlertIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle,
  CloseIcon as XCircle,
  RotateIcon as RefreshCw,
  DatabaseIcon as Database,
  ChartsIcon as BarChart3,
  ActivityIcon as Activity,
  ZapIcon as Zap,
  ChevronDownIcon as ChevronDown,
  ChevronUpIcon as ChevronUp,
} from "./ui/CustomIcons";
import {
  useLearningHealth,
  useLearningDashboard,
  usePredictions,
  useMultiTargetDashboard,
  useAccuracyByModel,
  triggerOutcomeCheck,
  trigger1hOutcomeCheck,
} from "../lib/api/learning";
import { getApiBase } from "../lib/api/base";
import { useI18nStore } from "../lib/i18n/store";
import { ModelPerformanceModal } from "./panels/ModelPerformanceModal";

const API_BASE = getApiBase();

/* ═══════════════════════════════════════════════════════════════════
   TYPES & CONSTANTS
   ═══════════════════════════════════════════════════════════════════ */

interface LearningDashboardPanelProps {
  symbol?: string;
}

const MODEL_CONFIG: Record<string, {
  label: string; labelEn: string; color: string; barColor: string; textColor: string;
  timeframes: string[];
}> = {
  ml: { label: "ML Model", labelEn: "ML Model", color: "#3B82F6", barColor: "bg-blue-500", textColor: "text-blue-400", timeframes: ["1h"] },
  pulse1: { label: "Pulse 1 — Algo", labelEn: "Pulse 1 — Algo", color: "#22D3EE", barColor: "bg-cyan-500", textColor: "text-cyan-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  pulse2: { label: "Pulse 2 — ML", labelEn: "Pulse 2 — ML", color: "#A855F7", barColor: "bg-purple-500", textColor: "text-purple-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  pulse3: { label: "Pulse 3 — Scalp", labelEn: "Pulse 3 — Scalp", color: "#10B981", barColor: "bg-green-500", textColor: "text-green-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  emel: { label: "EMEL 9-Check", labelEn: "EMEL 9-Check", color: "#F59E0B", barColor: "bg-amber-500", textColor: "text-amber-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  emel_inverse: { label: "EMEL Ters", labelEn: "EMEL Inverse", color: "#D946EF", barColor: "bg-fuchsia-500", textColor: "text-fuchsia-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  EMEL: { label: "EMEL 9-Check", labelEn: "EMEL 9-Check", color: "#F59E0B", barColor: "bg-amber-500", textColor: "text-amber-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  PULSE: { label: "Pulse 1 — Algo", labelEn: "Pulse 1 — Algo", color: "#22D3EE", barColor: "bg-cyan-500", textColor: "text-cyan-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  PULSE_ML: { label: "Pulse 2 — ML", labelEn: "Pulse 2 — ML", color: "#A855F7", barColor: "bg-purple-500", textColor: "text-purple-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
  PULSE_V3: { label: "Pulse 3 — Scalp", labelEn: "Pulse 3 — Scalp", color: "#10B981", barColor: "bg-green-500", textColor: "text-green-400", timeframes: ["15m", "30m", "1h", "4h", "1d"] },
};

const SYMBOLS = [
  { id: "NDX.INDX", label: "NASDAQ", icon: "📈" },
  { id: "XAUUSD", label: "XAUUSD", icon: "⭐" },
  { id: "GDAXI.INDX", label: "DAX", icon: "🏛" },
  { id: "USOIL.FOREX", label: "US OIL", icon: "🛢" },
];

function getModelKey(strategy: string): string {
  const map: Record<string, string> = {
    EMEL: "emel", PULSE: "pulse1", PULSE_ML: "pulse2", PULSE_V3: "pulse3",
    EMEL_INVERSE: "emel_inverse",
  };
  return map[strategy] || strategy.toLowerCase();
}

function wrColor(wr: number): string {
  if (wr >= 70) return "text-cyan-400";
  if (wr >= 55) return "text-green-400";
  if (wr >= 40) return "text-amber-400";
  return "text-red-400";
}

function wrBgClass(wr: number): string {
  if (wr >= 70) return "bg-cyan-500/10 border-cyan-500/20";
  if (wr >= 55) return "bg-green-500/10 border-green-500/20";
  if (wr >= 40) return "bg-amber-500/10 border-amber-500/20";
  return "bg-red-500/10 border-red-500/20";
}

/* ═══════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════ */

export default function LearningDashboardPanel({ symbol }: LearningDashboardPanelProps) {
  const { t, locale } = useI18nStore();
  const [days, setDays] = useState(30);
  const [isCheckingOutcomes, setIsCheckingOutcomes] = useState(false);
  const [checkInterval, setCheckInterval] = useState<"1h" | "24h">("1h");
  const [expandedModels, setExpandedModels] = useState<Record<string, boolean>>({});
  const [selectedModal, setSelectedModal] = useState<{ symbol: string; model: string } | null>(null);

  const { data: health, isLoading: healthLoading } = useLearningHealth();
  const { data: dashboard, isLoading: dashboardLoading, refetch } = useLearningDashboard(symbol, days);
  const { data: multiTarget, refetch: refetchMulti } = useMultiTargetDashboard(symbol, days);
  const { data: predictions } = usePredictions(symbol, 10);
  const { data: modelAccuracy } = useAccuracyByModel(symbol, days);

  // Auto-check outcomes on mount and every 5 minutes
  useEffect(() => {
    if (!health?.db_available) return;
    const checkOutcomes = async () => {
      try { await trigger1hOutcomeCheck(); refetch(); refetchMulti(); }
      catch (e) { console.error("Auto outcome check failed:", e); }
    };
    checkOutcomes();
    const interval = setInterval(checkOutcomes, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [health?.db_available, refetch, refetchMulti]);

  const handleCheckOutcomes = async () => {
    setIsCheckingOutcomes(true);
    try {
      if (checkInterval === "1h") { await trigger1hOutcomeCheck(); }
      else { await triggerOutcomeCheck("24h"); }
      refetch(); refetchMulti();
    } catch (e) { console.error("Failed to check outcomes:", e); }
    finally { setIsCheckingOutcomes(false); }
  };

  const toggleModel = (key: string) => {
    setExpandedModels(prev => ({ ...prev, [key]: !prev[key] }));
  };

  if (healthLoading) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-zinc-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>{t("learningDashboard.loading")}</span>
        </div>
      </div>
    );
  }

  if (!health?.db_available) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-amber-400">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-medium">{t("learningDashboard.offline")}</span>
        </div>
        <p className="text-zinc-500 text-sm mt-2">{t("learningDashboard.dbNotConfigured")}</p>
      </div>
    );
  }

  const accuracy = dashboard?.accuracy;
  const totalPredictions = accuracy?.total_predictions || 0;
  const mlAccuracy = accuracy?.ml_accuracy;
  const claudeAccuracy = accuracy?.claude_accuracy;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
      {/* ── HEADER ── */}
      <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h2 className="font-semibold text-white">{t("learningDashboard.title")}</h2>
          <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full flex items-center gap-1">
            <Database className="w-3 h-3" />
            {t("learningDashboard.connected")}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}
            className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-white">
            <option value={7}>7 {t("learningDashboard.days")}</option>
            <option value={14}>14 {t("learningDashboard.days")}</option>
            <option value={30}>30 {t("learningDashboard.days")}</option>
            <option value={90}>90 {t("learningDashboard.days")}</option>
            <option value={0}>{locale === "tr" ? "Tüm Zamanlar" : "All Time"}</option>
          </select>
          <button onClick={handleCheckOutcomes} disabled={isCheckingOutcomes}
            className="p-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors disabled:opacity-50"
            title="Check outcomes">
            <RefreshCw className={`w-4 h-4 ${isCheckingOutcomes ? "animate-spin" : ""}`} />
          </button>
          <PanelInfoButton panelId="learning-dashboard" />
        </div>
      </div>

      {dashboardLoading ? (
        <div className="p-8 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-zinc-500" />
        </div>
      ) : (
        <div className="p-4 space-y-4">
          {/* ── KPI Cards ── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <BarChart3 className="w-3.5 h-3.5" />
                {t("learningDashboard.totalPredictions")}
              </div>
              <div className="text-2xl font-bold text-white">{totalPredictions}</div>
              <div className="text-xs text-zinc-500">{t("learningDashboard.lastUpdate")}: {days || "∞"} {t("learningDashboard.days")}</div>
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <Zap className="w-3.5 h-3.5 text-blue-400" />
                ML Accuracy
              </div>
              {mlAccuracy !== null ? (
                <>
                  <div className={`text-2xl font-bold ${getAccuracyColor(mlAccuracy)}`}>
                    {(mlAccuracy * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-zinc-500">{accuracy?.ml_correct_count || 0} {t("learningDashboard.correct")}</div>
                </>
              ) : (<div className="text-lg text-zinc-500">—</div>)}
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <Brain className="w-3.5 h-3.5 text-purple-400" />
                Claude AI
              </div>
              {claudeAccuracy !== null ? (
                <>
                  <div className={`text-2xl font-bold ${getAccuracyColor(claudeAccuracy)}`}>
                    {(claudeAccuracy * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-zinc-500">{accuracy?.claude_correct_count || 0} {t("learningDashboard.correct")}</div>
                </>
              ) : (<div className="text-lg text-zinc-500">—</div>)}
            </div>
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <Target className="w-3.5 h-3.5 text-green-400" />
                {t("learningDashboard.bothCorrect")}
              </div>
              {accuracy?.both_correct_rate !== null ? (
                <>
                  <div className={`text-2xl font-bold ${getAccuracyColor(accuracy?.both_correct_rate || 0)}`}>
                    {((accuracy?.both_correct_rate || 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-zinc-500">{t("learningDashboard.consensus")}</div>
                </>
              ) : (<div className="text-lg text-zinc-500">—</div>)}
            </div>
          </div>

          {/* ── MODEL COMPARISON BAR ── */}
          {mlAccuracy !== null && claudeAccuracy !== null && (
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3">{t("learningDashboard.modelComparison")}</div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-blue-400 flex items-center gap-1"><Zap className="w-3 h-3" /> ML Model</span>
                    <span className="text-white">{(mlAccuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${mlAccuracy * 100}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-purple-400 flex items-center gap-1"><Brain className="w-3 h-3" /> Claude AI</span>
                    <span className="text-white">{(claudeAccuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 rounded-full transition-all duration-500" style={{ width: `${claudeAccuracy * 100}%` }} />
                  </div>
                </div>
              </div>
              <div className="mt-3 text-center">
                {mlAccuracy > claudeAccuracy ? (
                  <span className="inline-flex items-center gap-1 text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full">
                    <Zap className="w-3 h-3" /> {t("learningDashboard.mlAhead")} (+{((mlAccuracy - claudeAccuracy) * 100).toFixed(1)}%)
                  </span>
                ) : claudeAccuracy > mlAccuracy ? (
                  <span className="inline-flex items-center gap-1 text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded-full">
                    <Brain className="w-3 h-3" /> {t("learningDashboard.claudeAhead")} (+{((claudeAccuracy - mlAccuracy) * 100).toFixed(1)}%)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs bg-zinc-700 text-zinc-400 px-2 py-1 rounded-full">
                    {t("learningDashboard.equalPerformance")}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════════════
             ██ MODEL PERFORMANCE — EXPANDABLE CARDS WITH PER-SYMBOL DATA
             ═══════════════════════════════════════════════════════════════ */}
          {modelAccuracy?.models && modelAccuracy.models.length > 0 && (
            <div>
              <div className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                {t("learningDashboard.modelBreakdown")}
              </div>
              <div className="space-y-2">
                {modelAccuracy.models.map((model: any) => {
                  const modelKey = getModelKey(model.strategy);
                  const config = MODEL_CONFIG[model.strategy] || MODEL_CONFIG[modelKey] || {
                    label: model.strategy, labelEn: model.strategy, color: "#6B7280",
                    barColor: "bg-zinc-500", textColor: "text-zinc-400", timeframes: ["1h"],
                  };
                  const isExpanded = expandedModels[modelKey] || false;
                  const mlAcc = model.ml_accuracy !== null ? (model.ml_accuracy * 100) : 0;
                  const tgtAcc = model.target_hit_rate !== null ? (model.target_hit_rate * 100) : 0;

                  return (
                    <div key={model.strategy} className="bg-zinc-800/60 rounded-xl border border-zinc-700/50 overflow-hidden">
                      {/* ── Model Header (Click to Expand) ── */}
                      <button
                        className="w-full flex items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-zinc-700/30"
                        onClick={() => toggleModel(modelKey)}
                      >
                        {/* Color Dot */}
                        <div className="w-3 h-3 rounded-full shrink-0" style={{ background: config.color, boxShadow: `0 0 8px ${config.color}50` }} />

                        {/* Name + Count */}
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-semibold ${config.textColor}`}>
                            {locale === "tr" ? config.label : config.labelEn}
                          </p>
                          <p className="text-[10px] text-zinc-500">
                            {model.total_predictions} {t("learningDashboard.predictions")} · {config.timeframes.join(", ")}
                          </p>
                        </div>

                        {/* Win Rate Badge */}
                        <div className="flex items-center gap-2 shrink-0">
                          <div className={`px-2.5 py-1 rounded-lg text-xs font-bold ${wrBgClass(mlAcc)} border`}>
                            <span className={wrColor(mlAcc)}>{mlAcc.toFixed(1)}%</span>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-zinc-500" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-zinc-500" />
                          )}
                        </div>
                      </button>

                      {/* ── Expanded: Per-Symbol Cards + TF Breakdown ── */}
                      {isExpanded && (
                        <ExpandedModelContent
                          modelKey={modelKey}
                          config={config}
                          model={model}
                          days={days}
                          locale={locale}
                          t={t}
                          onSelectSymbol={(sym) => setSelectedModal({ symbol: sym, model: modelKey })}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Multi-Target Accuracy Section ── */}
          {multiTarget?.config && (
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-cyan-400" />
                  {t("learningDashboard.targetLevels")}
                </div>
                <div className="flex items-center gap-2">
                  <select value={checkInterval} onChange={(e) => setCheckInterval(e.target.value as "1h" | "24h")}
                    className="bg-zinc-700 border border-zinc-600 rounded px-2 py-0.5 text-xs text-white">
                    <option value="1h">1 {t("learningDashboard.hour")}</option>
                    <option value="24h">24 {t("learningDashboard.hours")}</option>
                  </select>
                </div>
              </div>
              <div className="text-xs text-zinc-500 mb-3">
                {symbol === "NDX.INDX" ? "NASDAQ" : symbol === "XAUUSD" ? "XAUUSD" : symbol}:
                {t("learningDashboard.targets")} {multiTarget.config.targets.map((tgt: any) => `${tgt.name}: ${tgt.pips} pips`).join(", ")} |
                SL: {multiTarget.config.stoploss_pips} pips
              </div>
              {(() => {
                const acc = checkInterval === "1h" ? multiTarget.accuracy_1h : multiTarget.accuracy_24h;
                if (!acc || !acc.target_accuracy) return null;
                return (
                  <div className="space-y-3">
                    {Object.entries(acc.target_accuracy).map(([name, data]: [string, any]) => (
                      <div key={name}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-cyan-400">{name} ({multiTarget.config?.targets.find((t: any) => t.name === name)?.pips || 0} pips)</span>
                          <span className={getAccuracyColor(data.hit_rate || 0)}>
                            {isNaN(data.hit_rate) ? "0.0" : (data.hit_rate * 100).toFixed(1)}% ({data.hit_count}/{data.total})
                          </span>
                        </div>
                        <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full transition-all duration-500 ${data.hit_rate >= 0.5 ? "bg-green-500" : data.hit_rate >= 0.3 ? "bg-amber-500" : "bg-red-500"}`}
                            style={{ width: `${Math.min(data.hit_rate * 100, 100)}%` }} />
                        </div>
                      </div>
                    ))}
                    <div className="pt-2 border-t border-zinc-700">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-red-400">Stoploss ({multiTarget.config?.stoploss_pips} pips)</span>
                        <span className={(acc.stoploss_hit_rate || 0) > 0.3 ? "text-red-400" : "text-green-400"}>
                          {isNaN(acc.stoploss_hit_rate) ? "0.0" : (acc.stoploss_hit_rate * 100).toFixed(1)}% ({acc.stoploss_hits || 0} {t("learningDashboard.times")})
                        </span>
                      </div>
                      <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min((acc.stoploss_hit_rate || 0) * 100, 100)}%` }} />
                      </div>
                    </div>
                    <div className="pt-2 text-xs text-zinc-400 text-center">
                      {t("learningDashboard.totalAnalysis")} {acc.analyzed_predictions} | {checkInterval} {t("learningDashboard.check")}
                    </div>
                  </div>
                );
              })()}
              {(!multiTarget.accuracy_1h?.target_accuracy || Object.keys(multiTarget.accuracy_1h.target_accuracy).length === 0) && (
                <div className="text-xs text-zinc-500 text-center py-4">{t("learningDashboard.noTargetData")}</div>
              )}
            </div>
          )}

          {/* No Data */}
          {totalPredictions === 0 && (
            <div className="text-center py-8">
              <Database className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
              <p className="text-zinc-400">{t("learningDashboard.noDataYet")}</p>
              <p className="text-zinc-500 text-sm mt-1">{t("learningDashboard.dataWillAccumulate")}</p>
            </div>
          )}
        </div>
      )}

      {/* ── CYBERPUNK PERFORMANCE MODAL ── */}
      {selectedModal && (
        <ModelPerformanceModal
          isOpen={true}
          symbol={selectedModal.symbol}
          model={selectedModal.model}
          onClose={() => setSelectedModal(null)}
        />
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   EXPANDED MODEL CONTENT — Per-Symbol Cards + TF Matrix
   ═══════════════════════════════════════════════════════════════════ */

function ExpandedModelContent({ modelKey, config, model, days, locale, t, onSelectSymbol }: {
  modelKey: string; config: any; model: any; days: number; locale: string;
  t: (k: string) => string; onSelectSymbol: (sym: string) => void;
}) {
  // Fetch per-symbol data for this model from model-detail-analytics
  const symbolQueries = SYMBOLS.map(sym => {
    const { data, isLoading } = useQuery({
      queryKey: ["model-detail-analytics", modelKey, sym.id, days],
      queryFn: async () => {
        const params = new URLSearchParams({ model: modelKey, symbol: sym.id });
        if (days > 0) params.append("days", String(days));
        const res = await fetch(`${API_BASE}/api/learning/model-detail-analytics?${params}`);
        if (!res.ok) return null;
        return res.json();
      },
      staleTime: 60000,
    });
    return { sym, data, isLoading };
  });

  return (
    <div className="px-4 pb-4 space-y-3" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
      {/* Overall accuracy bars */}
      <div className="grid grid-cols-2 gap-2 pt-3">
        <div className="bg-zinc-800 rounded-lg p-2.5">
          <div className="flex justify-between text-[10px] mb-1">
            <span className="text-zinc-400">ML {locale === "tr" ? "Doğruluk" : "Accuracy"}</span>
            <span className={model.ml_accuracy !== null ? getAccuracyColor(model.ml_accuracy) : "text-zinc-500"}>
              {model.ml_accuracy !== null ? `${(model.ml_accuracy * 100).toFixed(1)}%` : "—"}
              {model.ml_accuracy !== null && ` (${model.ml_correct}/${model.with_outcome})`}
            </span>
          </div>
          <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
            <div className={`h-full ${config.barColor} rounded-full transition-all duration-500`} style={{ width: `${(model.ml_accuracy || 0) * 100}%` }} />
          </div>
        </div>
        {model.target_hit_rate !== null && (
          <div className="bg-zinc-800 rounded-lg p-2.5">
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-zinc-400">{t("learningDashboard.targetHit")}</span>
              <span className={getAccuracyColor(model.target_hit_rate || 0)}>
                {(model.target_hit_rate * 100).toFixed(1)}% ({model.target_hits}/{model.with_outcome})
              </span>
            </div>
            <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
              <div className="h-full bg-green-500 rounded-full transition-all duration-500" style={{ width: `${(model.target_hit_rate || 0) * 100}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Per-Symbol Cards */}
      <div className="space-y-2">
        <p className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">
          {locale === "tr" ? "Varlık Bazlı Performans" : "Per Asset Performance"} — {locale === "tr" ? "Tıkla → Detaylı Analiz" : "Click → Detail"}
        </p>
        <div className="grid grid-cols-2 gap-2">
          {symbolQueries.map(({ sym, data, isLoading }) => {
            const ov = data?.overview;
            const hasData = ov && ov.total_signals > 0;
            const tfData = data?.timeframe_comparison || [];

            return (
              <button
                key={sym.id}
                className="text-left bg-zinc-800/80 rounded-xl p-3 border border-zinc-700/40 transition-all duration-200 hover:border-cyan-500/30 hover:bg-zinc-700/50 cursor-pointer"
                onClick={() => onSelectSymbol(sym.id)}
              >
                {isLoading ? (
                  <div className="flex items-center gap-2 py-2">
                    <RefreshCw className="w-3 h-3 animate-spin text-zinc-500" />
                    <span className="text-[10px] text-zinc-500">Loading...</span>
                  </div>
                ) : !hasData ? (
                  <div className="py-1">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-sm">{sym.icon}</span>
                      <span className="text-xs font-semibold text-zinc-400">{sym.label}</span>
                    </div>
                    <p className="text-[10px] text-zinc-600">{locale === "tr" ? "Veri yok" : "No data"}</p>
                  </div>
                ) : (
                  <>
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm">{sym.icon}</span>
                        <span className="text-xs font-bold text-white">{sym.label}</span>
                      </div>
                      <span className={`text-xs font-bold ${wrColor(ov.win_rate)}`}>
                        {ov.win_rate}%
                      </span>
                    </div>

                    {/* Net Pips */}
                    <div className={`text-lg font-bold mb-1.5 ${ov.net_pips >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {ov.net_pips >= 0 ? "+" : ""}{ov.net_pips}p
                    </div>

                    {/* Mini stats */}
                    <div className="flex gap-2 text-[10px] mb-2">
                      <span className="text-green-400">{ov.completed}W</span>
                      <span className="text-red-400">{ov.stopped}L</span>
                      <span className="text-zinc-500">{ov.total_signals} {locale === "tr" ? "sinyal" : "signals"}</span>
                    </div>

                    {/* TF Mini Breakdown */}
                    {tfData.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {tfData.map((tf: any) => (
                          <span key={tf.tf} className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${wrBgClass(tf.win_rate)} border`}>
                            <span className="text-zinc-400">{tf.tf}</span>{" "}
                            <span className={wrColor(tf.win_rate)}>{tf.win_rate}%</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════════════ */

function DirectionBadge({ direction, label, color }: { direction: string | null; label: string; color: "blue" | "purple" }) {
  if (!direction) return null;
  const colorClasses = {
    blue: { BUY: "bg-green-500/20 text-green-400", SELL: "bg-red-500/20 text-red-400", HOLD: "bg-zinc-600/50 text-zinc-400" },
    purple: { BUY: "bg-green-500/20 text-green-400", SELL: "bg-red-500/20 text-red-400", HOLD: "bg-zinc-600/50 text-zinc-400" },
  };
  const classes = colorClasses[color][direction as keyof typeof colorClasses.blue] || "bg-zinc-600/50 text-zinc-400";
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded ${classes}`}>
      {direction === "BUY" && <TrendingUp className="w-3 h-3" />}
      {direction === "SELL" && <TrendingDown className="w-3 h-3" />}
      {label}: {direction}
    </span>
  );
}

function getAccuracyColor(accuracy: number): string {
  if (accuracy >= 0.7) return "text-green-400";
  if (accuracy >= 0.5) return "text-amber-400";
  return "text-red-400";
}
