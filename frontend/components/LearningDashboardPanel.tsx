"use client";

import { useState } from "react";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Database,
  BarChart3,
  Activity,
  Zap,
} from "lucide-react";
import {
  useLearningHealth,
  useLearningDashboard,
  usePredictions,
  useMultiTargetDashboard,
  triggerOutcomeCheck,
  trigger1hOutcomeCheck,
} from "../lib/api/learning";

interface LearningDashboardPanelProps {
  symbol?: string;
}

export default function LearningDashboardPanel({ symbol }: LearningDashboardPanelProps) {
  const [days, setDays] = useState(7);
  const [isCheckingOutcomes, setIsCheckingOutcomes] = useState(false);
  const [checkInterval, setCheckInterval] = useState<"1h" | "24h">("1h");

  const { data: health, isLoading: healthLoading } = useLearningHealth();
  const { data: dashboard, isLoading: dashboardLoading, refetch } = useLearningDashboard(symbol, days);
  const { data: multiTarget, refetch: refetchMulti } = useMultiTargetDashboard(symbol, days);
  const { data: predictions } = usePredictions(symbol, 10);

  const handleCheckOutcomes = async () => {
    setIsCheckingOutcomes(true);
    try {
      if (checkInterval === "1h") {
        await trigger1hOutcomeCheck();
      } else {
        await triggerOutcomeCheck("24h");
      }
      refetch();
      refetchMulti();
    } catch (e) {
      console.error("Failed to check outcomes:", e);
    } finally {
      setIsCheckingOutcomes(false);
    }
  };

  if (healthLoading) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-zinc-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span>Loading learning system...</span>
        </div>
      </div>
    );
  }

  if (!health?.db_available) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-amber-400">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-medium">Learning System Offline</span>
        </div>
        <p className="text-zinc-500 text-sm mt-2">
          Database not configured. Set SUPABASE_URL and SUPABASE_KEY in .env
        </p>
      </div>
    );
  }

  const accuracy = dashboard?.accuracy;
  const totalPredictions = accuracy?.total_predictions || 0;
  const mlAccuracy = accuracy?.ml_accuracy;
  const claudeAccuracy = accuracy?.claude_accuracy;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h2 className="font-semibold text-white">Learning Dashboard</h2>
          <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full flex items-center gap-1">
            <Database className="w-3 h-3" />
            Connected
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-white"
          >
            <option value={7}>7 gün</option>
            <option value={14}>14 gün</option>
            <option value={30}>30 gün</option>
          </select>
          <button
            onClick={handleCheckOutcomes}
            disabled={isCheckingOutcomes}
            className="p-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors disabled:opacity-50"
            title="Check outcomes"
          >
            <RefreshCw className={`w-4 h-4 ${isCheckingOutcomes ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {dashboardLoading ? (
        <div className="p-8 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-zinc-500" />
        </div>
      ) : (
        <div className="p-4 space-y-4">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Total Predictions */}
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <BarChart3 className="w-3.5 h-3.5" />
                Toplam Tahmin
              </div>
              <div className="text-2xl font-bold text-white">{totalPredictions}</div>
              <div className="text-xs text-zinc-500">Son {days} gün</div>
            </div>

            {/* ML Accuracy */}
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
                  <div className="text-xs text-zinc-500">
                    {accuracy?.ml_correct_count || 0} doğru
                  </div>
                </>
              ) : (
                <div className="text-lg text-zinc-500">—</div>
              )}
            </div>

            {/* Claude Accuracy */}
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <Brain className="w-3.5 h-3.5 text-purple-400" />
                Claude Accuracy
              </div>
              {claudeAccuracy !== null ? (
                <>
                  <div className={`text-2xl font-bold ${getAccuracyColor(claudeAccuracy)}`}>
                    {(claudeAccuracy * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-zinc-500">
                    {accuracy?.claude_correct_count || 0} doğru
                  </div>
                </>
              ) : (
                <div className="text-lg text-zinc-500">—</div>
              )}
            </div>

            {/* Both Correct Rate */}
            <div className="bg-zinc-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-zinc-400 text-xs mb-1">
                <Target className="w-3.5 h-3.5 text-green-400" />
                İkisi de Doğru
              </div>
              {accuracy?.both_correct_rate !== null ? (
                <>
                  <div className={`text-2xl font-bold ${getAccuracyColor(accuracy?.both_correct_rate || 0)}`}>
                    {((accuracy?.both_correct_rate || 0) * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-zinc-500">Konsensüs</div>
                </>
              ) : (
                <div className="text-lg text-zinc-500">—</div>
              )}
            </div>
          </div>

          {/* Accuracy Comparison Bar */}
          {mlAccuracy !== null && claudeAccuracy !== null && (
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3">Model Karşılaştırması</div>
              <div className="space-y-3">
                {/* ML Bar */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-blue-400 flex items-center gap-1">
                      <Zap className="w-3 h-3" /> ML Model
                    </span>
                    <span className="text-white">{(mlAccuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-500"
                      style={{ width: `${mlAccuracy * 100}%` }}
                    />
                  </div>
                </div>

                {/* Claude Bar */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-purple-400 flex items-center gap-1">
                      <Brain className="w-3 h-3" /> Claude AI
                    </span>
                    <span className="text-white">{(claudeAccuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 rounded-full transition-all duration-500"
                      style={{ width: `${claudeAccuracy * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Winner Badge */}
              <div className="mt-3 text-center">
                {mlAccuracy > claudeAccuracy ? (
                  <span className="inline-flex items-center gap-1 text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full">
                    <Zap className="w-3 h-3" /> ML Model önde (+{((mlAccuracy - claudeAccuracy) * 100).toFixed(1)}%)
                  </span>
                ) : claudeAccuracy > mlAccuracy ? (
                  <span className="inline-flex items-center gap-1 text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded-full">
                    <Brain className="w-3 h-3" /> Claude önde (+{((claudeAccuracy - mlAccuracy) * 100).toFixed(1)}%)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs bg-zinc-700 text-zinc-400 px-2 py-1 rounded-full">
                    Eşit performans
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Recent Predictions */}
          {predictions && predictions.predictions.length > 0 && (
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Son Tahminler
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {predictions.predictions.slice(0, 5).map((pred) => (
                  <div
                    key={pred.id}
                    className="flex items-center justify-between bg-zinc-800 rounded px-3 py-2 text-sm"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-zinc-400 text-xs">
                        {new Date(pred.created_at).toLocaleDateString("tr-TR", {
                          day: "2-digit",
                          month: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                      <DirectionBadge direction={pred.ml_direction} label="ML" color="blue" />
                      <DirectionBadge direction={pred.claude_direction} label="Claude" color="purple" />
                    </div>
                    <div className="flex items-center gap-2">
                      {pred.outcome_checked ? (
                        <span className="text-xs text-green-400 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" /> Kontrol edildi
                        </span>
                      ) : (
                        <span className="text-xs text-zinc-500 flex items-center gap-1">
                          <RefreshCw className="w-3 h-3" /> Bekliyor
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Multi-Target Accuracy Section */}
          {multiTarget?.config && (
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-cyan-400" />
                  Hedef Seviyeleri Başarı Oranı
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={checkInterval}
                    onChange={(e) => setCheckInterval(e.target.value as "1h" | "24h")}
                    className="bg-zinc-700 border border-zinc-600 rounded px-2 py-0.5 text-xs text-white"
                  >
                    <option value="1h">1 Saat</option>
                    <option value="24h">24 Saat</option>
                  </select>
                </div>
              </div>

              {/* Config Info */}
              <div className="text-xs text-zinc-500 mb-3">
                {symbol === "NDX.INDX" ? "NASDAQ" : symbol === "XAUUSD" ? "XAUUSD" : symbol}: 
                Hedefler {multiTarget.config.targets.map(t => `${t.name}: ${t.pips} pips`).join(", ")} | 
                SL: {multiTarget.config.stoploss_pips} pips
              </div>

              {/* Target Hit Rates */}
              {(() => {
                const accuracy = checkInterval === "1h" ? multiTarget.accuracy_1h : multiTarget.accuracy_24h;
                if (!accuracy || !accuracy.target_accuracy) return null;
                
                return (
                  <div className="space-y-3">
                    {Object.entries(accuracy.target_accuracy).map(([name, data]) => (
                      <div key={name}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-cyan-400">{name} ({multiTarget.config?.targets.find(t => t.name === name)?.pips || 0} pips)</span>
                          <span className={getAccuracyColor(data.hit_rate)}>
                            {(data.hit_rate * 100).toFixed(1)}% ({data.hit_count}/{data.total})
                          </span>
                        </div>
                        <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              data.hit_rate >= 0.5 ? "bg-green-500" : data.hit_rate >= 0.3 ? "bg-amber-500" : "bg-red-500"
                            }`}
                            style={{ width: `${Math.min(data.hit_rate * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}

                    {/* Stoploss Hit Rate */}
                    <div className="pt-2 border-t border-zinc-700">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-red-400">Stoploss ({multiTarget.config?.stoploss_pips} pips)</span>
                        <span className={accuracy.stoploss_hit_rate > 0.3 ? "text-red-400" : "text-green-400"}>
                          {(accuracy.stoploss_hit_rate * 100).toFixed(1)}% ({accuracy.stoploss_hits} kez)
                        </span>
                      </div>
                      <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(accuracy.stoploss_hit_rate * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Summary */}
                    <div className="pt-2 text-xs text-zinc-400 text-center">
                      Toplam {accuracy.analyzed_predictions} analiz | {checkInterval} kontrol
                    </div>
                  </div>
                );
              })()}

              {/* No multi-target data yet */}
              {(!multiTarget.accuracy_1h?.target_accuracy || Object.keys(multiTarget.accuracy_1h.target_accuracy).length === 0) && (
                <div className="text-xs text-zinc-500 text-center py-4">
                  Henüz hedef bazlı veri yok. Outcome kontrolü yapılınca burada görünecek.
                </div>
              )}
            </div>
          )}

          {/* No Data Message */}
          {totalPredictions === 0 && (
            <div className="text-center py-8">
              <Database className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
              <p className="text-zinc-400">Henüz yeterli veri yok</p>
              <p className="text-zinc-500 text-sm mt-1">
                Detaylı analiz yaptıkça veriler burada birikecek
              </p>
            </div>
          )}

          {/* Active Insights */}
          {dashboard?.active_insights && dashboard.active_insights.length > 0 && (
            <div className="bg-zinc-800/50 rounded-lg p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Öğrenme İçgörüleri
              </div>
              <div className="space-y-2">
                {dashboard.active_insights.slice(0, 3).map((insight: any, idx: number) => (
                  <div
                    key={idx}
                    className={`text-xs p-2 rounded ${
                      insight.data?.severity === "high"
                        ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : insight.data?.severity === "positive"
                        ? "bg-green-500/10 text-green-400 border border-green-500/20"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}
                  >
                    {insight.data?.recommendation || JSON.stringify(insight.data)}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DirectionBadge({
  direction,
  label,
  color,
}: {
  direction: string | null;
  label: string;
  color: "blue" | "purple";
}) {
  if (!direction) return null;

  const colorClasses = {
    blue: {
      BUY: "bg-green-500/20 text-green-400",
      SELL: "bg-red-500/20 text-red-400",
      HOLD: "bg-zinc-600/50 text-zinc-400",
    },
    purple: {
      BUY: "bg-green-500/20 text-green-400",
      SELL: "bg-red-500/20 text-red-400",
      HOLD: "bg-zinc-600/50 text-zinc-400",
    },
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
