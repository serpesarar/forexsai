"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  RefreshCw,
  Trophy,
  Target,
  XCircle,
  Shield,
  Zap,
  Flame,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";

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
};

function StrategyCard({
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

  return (
    <div
      className={`relative p-4 rounded-xl border ${config.borderColor} ${config.bgColor} transition-all hover:scale-[1.02]`}
    >
      {isBest && (
        <div className="absolute -top-2 -right-2 bg-yellow-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
          <Trophy className="w-3 h-3" />
          EN İYİ
        </div>
      )}

      <div className="flex items-center gap-2 mb-3">
        <div className={`p-2 rounded-lg ${config.bgColor}`}>
          <Icon className={`w-4 h-4 ${config.color}`} />
        </div>
        <div>
          <p className={`font-semibold ${config.color}`}>
            {locale === "en" ? config.nameEn : config.name}
          </p>
          <p className="text-[10px] text-textSecondary">
            {data.total_predictions} tahmin
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {/* Accuracy */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-textSecondary">Doğruluk</span>
          <span className={`text-sm font-bold ${data.accuracy !== null && data.accuracy >= 60 ? "text-success" : data.accuracy !== null && data.accuracy >= 50 ? "text-yellow-400" : "text-danger"}`}>
            {data.accuracy !== null ? `${data.accuracy}%` : "-"}
          </span>
        </div>

        {/* Target Hit Rate */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-textSecondary flex items-center gap-1">
            <Target className="w-3 h-3 text-success" />
            Hedef
          </span>
          <span className="text-xs text-success">
            {data.target_hit_rate !== null ? `${data.target_hit_rate}%` : "-"}
            <span className="text-textSecondary ml-1">({data.target_hits})</span>
          </span>
        </div>

        {/* Stop Hit Rate */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-textSecondary flex items-center gap-1">
            <XCircle className="w-3 h-3 text-danger" />
            Stop
          </span>
          <span className="text-xs text-danger">
            {data.stop_hit_rate !== null ? `${data.stop_hit_rate}%` : "-"}
            <span className="text-textSecondary ml-1">({data.stop_hits})</span>
          </span>
        </div>

        {/* Avg Confidence */}
        <div className="flex justify-between items-center pt-1 border-t border-white/10">
          <span className="text-xs text-textSecondary">Ort. Güven</span>
          <span className="text-xs font-mono">{data.avg_confidence}%</span>
        </div>
      </div>
    </div>
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

  if (error) {
    return (
      <div className="glass-card p-6 rounded-2xl">
        <div className="flex items-center gap-3 text-danger">
          <AlertTriangle className="w-5 h-5" />
          <span>Strateji verileri yüklenemedi</span>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 rounded-2xl space-y-6">
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
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="skeleton h-8 w-32 rounded-lg" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton h-40 rounded-xl" />
            ))}
          </div>
        </div>
      ) : data && !data.error ? (
        <>
          {/* NASDAQ Section */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <h4 className="font-medium">NASDAQ</h4>
              {data.best_strategies["NDX.INDX"]?.strategy && (
                <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
                  En iyi: {STRATEGY_CONFIG[data.best_strategies["NDX.INDX"].strategy as keyof typeof STRATEGY_CONFIG]?.name}
                  {data.best_strategies["NDX.INDX"].accuracy !== null && ` (${data.best_strategies["NDX.INDX"].accuracy}%)`}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(data.strategies["NDX.INDX"] || {}).map(([strategy, strategyData]) => (
                <StrategyCard
                  key={strategy}
                  strategy={strategy}
                  data={strategyData}
                  isBest={data.best_strategies["NDX.INDX"]?.strategy === strategy}
                  locale={locale}
                />
              ))}
            </div>
          </div>

          {/* XAUUSD Section */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-yellow-400" />
              <h4 className="font-medium">XAUUSD</h4>
              {data.best_strategies["XAUUSD"]?.strategy && (
                <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
                  En iyi: {STRATEGY_CONFIG[data.best_strategies["XAUUSD"].strategy as keyof typeof STRATEGY_CONFIG]?.name}
                  {data.best_strategies["XAUUSD"].accuracy !== null && ` (${data.best_strategies["XAUUSD"].accuracy}%)`}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(data.strategies["XAUUSD"] || {}).map(([strategy, strategyData]) => (
                <StrategyCard
                  key={strategy}
                  strategy={strategy}
                  data={strategyData}
                  isBest={data.best_strategies["XAUUSD"]?.strategy === strategy}
                  locale={locale}
                />
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="pt-4 border-t border-white/10">
            <p className="text-[10px] text-textSecondary mb-2">STRATEJİ AÇIKLAMALARI</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
              {Object.entries(data.strategy_descriptions || {}).map(([key, desc]) => (
                <div key={key} className="flex items-center gap-1">
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
