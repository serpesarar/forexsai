"use client";

import { useState, useEffect } from "react";
import { TrendingUp, Building2, Clock, DollarSign, BarChart3, AlertCircle, Filter, Info } from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

interface EarningsEvent {
  id: string;
  timestamp: string;
  company: string;
  ticker: string;
  sector: string;
  eps_forecast: string | null;
  revenue_forecast: string | null;
  previous_eps: string | null;
  previous_revenue: string | null;
  predicted_direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  affected_symbols: string[];
  analysis: string;
  analysis_tr: string;
  key_metrics_to_watch: string[];
  key_metrics_to_watch_tr: string[];
  is_upcoming: boolean;
  minutes_until: number | null;
}

interface EarningsCalendarProps {
  onEarningsClick?: (earnings: EarningsEvent) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://upbeat-flow-production.up.railway.app";

const sectorColors: Record<string, string> = {
  Technology: "from-blue-500/30 to-cyan-500/30 text-blue-400",
  "Consumer Cyclical": "from-purple-500/30 to-pink-500/30 text-purple-400",
  Financials: "from-emerald-500/30 to-green-500/30 text-emerald-400",
  Healthcare: "from-red-500/30 to-rose-500/30 text-red-400",
  Automotive: "from-orange-500/30 to-amber-500/30 text-orange-400",
  Energy: "from-yellow-500/30 to-amber-500/30 text-yellow-400",
};

const directionIcons = {
  bullish: <TrendingUp className="w-4 h-4 text-emerald-400" />,
  bearish: <TrendingUp className="w-4 h-4 text-red-400 rotate-180" />,
  neutral: <BarChart3 className="w-4 h-4 text-gray-400" />,
};

function formatTimeUntil(minutes: number | null, locale: string): string {
  if (!minutes) return locale === "en" ? "Soon" : "Yakında";
  
  if (minutes < 60) {
    return `${minutes} ${locale === "en" ? "min" : "dk"}`;
  }
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} ${locale === "en" ? "hours" : "saat"}`;
  }
  
  const days = Math.floor(hours / 24);
  return `${days} ${locale === "en" ? "days" : "gün"}`;
}

function formatDate(dateStr: string, locale: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(locale === "en" ? "en-US" : "tr-TR", {
    month: "short",
    day: "numeric",
  });
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return "bg-emerald-500/30 text-emerald-400";
  if (confidence >= 60) return "bg-yellow-500/30 text-yellow-400";
  return "bg-red-500/30 text-red-400";
}

export default function EarningsCalendar({ onEarningsClick }: EarningsCalendarProps) {
  const { locale } = useI18nStore();
  const [earnings, setEarnings] = useState<EarningsEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "Technology" | "Financials" | "Consumer Cyclical">("all");

  useEffect(() => {
    fetchEarnings();
  }, []);

  const fetchEarnings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/calendar/earnings?days=30`);
      
      if (!response.ok) {
        throw new Error("Failed to fetch");
      }
      
      const data = await response.json();
      if (data.success) {
        setEarnings(data.earnings);
      }
    } catch (err) {
      setError(locale === "en" ? "Failed to load earnings" : "Kazançlar yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const filteredEarnings = filter === "all" 
    ? earnings 
    : earnings.filter(e => e.sector === filter);

  if (loading) {
    return (
      <div className="glass-premium p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Building2 className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-semibold">
            {locale === "en" ? "Earnings Calendar" : "Kazanç Takvimi"}
          </h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-24 w-full rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-premium p-6">
        <div className="flex items-center gap-3 mb-4">
          <Building2 className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-semibold">
            {locale === "en" ? "Earnings Calendar" : "Kazanç Takvimi"}
          </h2>
        </div>
        <div className="flex flex-col items-center py-8 text-center">
          <AlertCircle className="w-10 h-10 text-danger/50 mb-3" />
          <p className="text-sm text-danger">{error}</p>
          <button
            onClick={fetchEarnings}
            className="mt-4 text-xs text-blue-400 hover:underline"
          >
            {locale === "en" ? "Try again" : "Tekrar dene"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-premium p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/30 to-indigo-500/30">
            <Building2 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-xs text-textSecondary uppercase tracking-wider">
              {locale === "en" ? "Major Companies" : "Büyük Şirketler"}
            </p>
            <h2 className="text-base font-semibold">
              {locale === "en" ? "Earnings Calendar" : "Kazanç Takvimi"}
            </h2>
          </div>
        </div>
        
        {/* Filter */}
        <div className="flex items-center gap-1">
          <Filter className="w-3 h-3 text-textSecondary mr-1" />
          {(["all", "Technology", "Financials"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-1 text-[10px] rounded-md transition ${
                filter === f 
                  ? "bg-blue-500/30 text-blue-300" 
                  : "bg-white/5 text-textSecondary hover:bg-white/10"
              }`}
            >
              {f === "all" 
                ? (locale === "en" ? "All" : "Tümü")
                : f
              }
            </button>
          ))}
        </div>
      </div>

      {/* Earnings List */}
      {filteredEarnings.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Building2 className="w-12 h-12 text-textSecondary/30 mb-4" />
          <p className="text-sm text-textSecondary">
            {locale === "en" ? "No upcoming earnings" : "Yaklaşan kazanç açıklaması yok"}
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
          {filteredEarnings.map((item, index) => (
            <div
              key={item.id}
              className="border border-white/10 rounded-xl p-4 bg-white/5 hover:bg-white/10 transition cursor-pointer group animate-fadeIn"
              style={{ animationDelay: `${index * 0.05}s` }}
              onClick={() => onEarningsClick?.(item)}
            >
              {/* Top Row */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {/* Company Logo Placeholder */}
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${sectorColors[item.sector] || "from-gray-500/30 to-gray-400/30 text-gray-400"} flex items-center justify-center text-xs font-bold`}>
                    {item.ticker.slice(0, 2)}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white group-hover:text-blue-400 transition">
                      {item.company}
                    </h3>
                    <span className="text-[10px] text-textSecondary">{item.ticker}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-1 text-[10px] text-textSecondary">
                  <Clock className="w-3 h-3" />
                  {item.is_upcoming && item.minutes_until !== null && item.minutes_until < 1440 ? (
                    <span className="text-blue-400 font-medium">
                      {formatTimeUntil(item.minutes_until, locale)}
                    </span>
                  ) : (
                    <span>{formatDate(item.timestamp, locale)}</span>
                  )}
                </div>
              </div>

              {/* Forecast vs Previous */}
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-white/5 rounded-lg p-2">
                  <p className="text-[10px] text-textSecondary uppercase flex items-center gap-1">
                    <DollarSign className="w-3 h-3" />
                    EPS {locale === "en" ? "Forecast" : "Tahmini"}
                  </p>
                  <p className="text-sm font-semibold text-white">
                    {item.eps_forecast || "--"}
                  </p>
                  {item.previous_eps && (
                    <p className="text-[10px] text-textSecondary">
                      vs {locale === "en" ? "Prev" : "Önceki"}: {item.previous_eps}
                    </p>
                  )}
                </div>
                
                <div className="bg-white/5 rounded-lg p-2">
                  <p className="text-[10px] text-textSecondary uppercase flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    Revenue {locale === "en" ? "Forecast" : "Tahmini"}
                  </p>
                  <p className="text-sm font-semibold text-white">
                    {item.revenue_forecast || "--"}
                  </p>
                  {item.previous_revenue && (
                    <p className="text-[10px] text-textSecondary">
                      vs {locale === "en" ? "Prev" : "Önceki"}: {item.previous_revenue}
                    </p>
                  )}
                </div>
              </div>

              {/* AI Prediction */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {directionIcons[item.predicted_direction]}
                  <span className={`text-xs ${
                    item.predicted_direction === "bullish" ? "text-emerald-400" :
                    item.predicted_direction === "bearish" ? "text-red-400" :
                    "text-gray-400"
                  }`}>
                    {locale === "en" 
                      ? (item.predicted_direction === "bullish" ? "Beat Expected" : item.predicted_direction === "bearish" ? "Miss Expected" : "Neutral")
                      : (item.predicted_direction === "bullish" ? "Tahmini Aşabilir" : item.predicted_direction === "bearish" ? "Tahmini Karşılamayabilir" : "Nötr")
                    }
                  </span>
                </div>
                
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${getConfidenceColor(item.confidence)}`}>
                  {locale === "en" ? "AI Confidence" : "AI Güveni"}: {item.confidence}%
                </span>
              </div>

              {/* Affected Indices */}
              <div className="flex flex-wrap gap-1 mt-3">
                {item.affected_symbols.slice(0, 3).map((symbol) => (
                  <span
                    key={symbol}
                    className="text-[10px] bg-white/10 text-textSecondary px-2 py-0.5 rounded"
                  >
                    {symbol}
                  </span>
                ))}
              </div>

              {/* View Details Hint */}
              <div className="flex items-center justify-end mt-2 pt-2 border-t border-white/5">
                <span className="text-[10px] text-blue-400/70 flex items-center gap-1 group-hover:text-blue-400 transition">
                  <Info className="w-3 h-3" />
                  {locale === "en" ? "Click for analysis" : "Analiz için tıkla"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-textSecondary pt-2 border-t border-white/10">
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
          {locale === "en" ? "AI-powered predictions" : "AI destekli tahminler"}
        </span>
        <span>{filteredEarnings.length} {locale === "en" ? "reports" : "rapor"}</span>
      </div>
    </div>
  );
}
