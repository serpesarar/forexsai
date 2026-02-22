"use client";

import { useState, useEffect, useCallback } from "react";
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
  TargetIcon as Crosshair,
} from "./ui/CustomIcons";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

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

const STRATEGY_CONFIG = {
  ultra_safe: {
    name: "Ultra Güvenli",
    nameEn: "Ultra Safe",
    icon: Shield,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/20",
    borderColor: "border-emerald-500/30",
  },
  balanced: {
    name: "Dengeli",
    nameEn: "Balanced",
    icon: Target,
    color: "text-blue-400",
    bgColor: "bg-blue-500/20",
    borderColor: "border-blue-500/30",
  },
  full_power: {
    name: "Full Power",
    nameEn: "Full Power",
    icon: Zap,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/20",
    borderColor: "border-yellow-500/30",
  },
  aggressive: {
    name: "Agresif",
    nameEn: "Aggressive",
    icon: Flame,
    color: "text-red-400",
    bgColor: "bg-red-500/20",
    borderColor: "border-red-500/30",
  },
  nasdaq_precision: {
    name: "NASDAQ Precision",
    nameEn: "NASDAQ Precision",
    icon: Crosshair,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/20",
    borderColor: "border-cyan-500/30",
  },
};

function AccuracyBar({ value, color }: { value: number | null; color: string }) {
  if (value === null) return <span className="text-textSecondary">-</span>;
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-[11px] font-mono font-bold w-10 text-right">{value}%</span>
    </div>
  );
}

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
  const config = STRATEGY_CONFIG[strategy as keyof typeof STRATEGY_CONFIG];
  if (!config) return null;

  const Icon = config.icon;
  const accColor = data.accuracy !== null && data.accuracy >= 60 ? "bg-success" : data.accuracy !== null && data.accuracy >= 50 ? "bg-yellow-400" : "bg-danger";

  return (
    <tr className={`border-b border-white/5 hover:bg-white/5 transition-colors ${isBest ? "bg-yellow-500/5" : ""}`}>
      <td className="px-2 py-2 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          <div className={`p-1 rounded-md ${config.bgColor} shrink-0`}>
            <Icon className={`w-3 h-3 ${config.color}`} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1">
              <span className={`font-semibold text-xs ${config.color} whitespace-nowrap`}>
                {locale === "en" ? config.nameEn : config.name}
              </span>
              {isBest && (
                <span className="bg-yellow-500 text-black text-[8px] font-bold px-1 py-0.5 rounded-full flex items-center gap-0.5 shrink-0">
                  <Trophy className="w-2 h-2" /> EN İYİ
                </span>
              )}
            </div>
            <span className="text-[9px] text-textSecondary whitespace-nowrap">{data.total_predictions} tahmin / {data.with_outcome} sonuç</span>
          </div>
        </div>
      </td>
      <td className="px-2 py-2 whitespace-nowrap">
        <AccuracyBar value={data.accuracy} color={accColor} />
      </td>
      <td className="px-2 py-2 whitespace-nowrap">
        <div className="flex items-center gap-1">
          <Target className="w-2.5 h-2.5 text-success shrink-0" />
          <span className="text-[11px] font-mono text-success">{data.target_hit_rate !== null ? `${data.target_hit_rate}%` : "-"}</span>
          <span className="text-[9px] text-textSecondary">({data.target_hits ?? 0})</span>
        </div>
      </td>
      <td className="px-2 py-2 whitespace-nowrap">
        <div className="flex items-center gap-1">
          <XCircle className="w-2.5 h-2.5 text-danger shrink-0" />
          <span className="text-[11px] font-mono text-danger">{data.stop_hit_rate !== null ? `${data.stop_hit_rate}%` : "-"}</span>
          <span className="text-[9px] text-textSecondary">({data.stop_hits ?? 0})</span>
        </div>
      </td>
      <td className="px-2 py-2 text-right whitespace-nowrap">
        <span className="text-[11px] font-mono">{data.avg_confidence}%</span>
      </td>
    </tr>
  );
}

export default function StrategyPerformancePanel() {
  const [days, setDays] = useState(30);
  const locale = "tr";

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["strategy-performance", days],
    queryFn: () => fetchStrategyPerformance(days),
    staleTime: 60000,
    refetchInterval: 300000,
  });

  const handleRefresh = useCallback(() => { refetch(); }, [refetch]);

  useEffect(() => {
    window.addEventListener("dashboard-refresh", handleRefresh);
    return () => window.removeEventListener("dashboard-refresh", handleRefresh);
  }, [handleRefresh]);

  if (error) {
    return (
      <div className="glass-premium p-6 rounded-2xl">
        <div className="flex items-center gap-3 text-danger">
          <AlertTriangle className="w-5 h-5" />
          <span>Strateji verileri yüklenemedi</span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-premium p-6 rounded-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500/30 to-pink-500/30">
            <BarChart3 className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="font-semibold">Strateji Performans Analizi</h3>
            <p className="text-xs text-textSecondary">
              Hangi filtre kombinasyonu daha başarılı?
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-xs"
          >
            <option value={7}>7 gün</option>
            <option value={14}>14 gün</option>
            <option value={30}>30 gün</option>
            <option value={60}>60 gün</option>
          </select>

          <button
            onClick={() => refetch()}
            className="p-2 hover:bg-white/10 rounded-lg transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
          <PanelInfoButton panelId="strategy-performance" />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="skeleton h-8 w-48 rounded-lg" />
          <div className="skeleton h-48 rounded-xl" />
          <div className="skeleton h-48 rounded-xl" />
        </div>
      ) : data && !data.error ? (
        <>
          {/* Symbol Tables */}
          {[
            { key: "NDX.INDX", label: "NASDAQ", iconColor: "text-emerald-400" },
            { key: "XAUUSD", label: "XAU/USD", iconColor: "text-yellow-400" },
            { key: "GDAXI.INDX", label: "DAX", iconColor: "text-blue-400" },
            { key: "CL.COMM", label: "US Oil", iconColor: "text-orange-400" },
          ].map(({ key: symKey, label, iconColor }) => (
            <div key={symKey}>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className={`w-4 h-4 ${iconColor}`} />
                <h4 className="font-medium">{label}</h4>
                {data.best_strategies[symKey]?.strategy && (
                  <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
                    En iyi: {STRATEGY_CONFIG[data.best_strategies[symKey].strategy as keyof typeof STRATEGY_CONFIG]?.name}
                    {data.best_strategies[symKey].accuracy !== null && ` (${data.best_strategies[symKey].accuracy}%)`}
                  </span>
                )}
              </div>
              <div className="overflow-x-auto rounded-lg border border-white/10 -mx-1">
                <table className="w-full text-xs" style={{ minWidth: 600 }}>
                  <thead>
                    <tr className="bg-white/5 text-xs text-textSecondary uppercase">
                      <th className="px-3 py-2 text-left whitespace-nowrap">Strateji</th>
                      <th className="px-3 py-2 text-left whitespace-nowrap">Doğruluk</th>
                      <th className="px-3 py-2 text-left whitespace-nowrap">Hedef</th>
                      <th className="px-3 py-2 text-left whitespace-nowrap">Stop</th>
                      <th className="px-3 py-2 text-right whitespace-nowrap">Güven</th>
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

          {/* Legend */}
          <div className="pt-3 border-t border-white/10">
            <p className="text-[10px] text-textSecondary mb-2 uppercase tracking-wide">Strateji Açıklamaları</p>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-[11px]">
              {Object.entries(data.strategy_descriptions || {}).map(([key, desc]) => (
                <div key={key} className="flex items-center gap-1.5">
                  <span className={STRATEGY_CONFIG[key as keyof typeof STRATEGY_CONFIG]?.color}>●</span>
                  <span className="text-textSecondary">{desc}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-8 text-textSecondary">
          Veri bulunamadı
        </div>
      )}
    </div>
  );
}
