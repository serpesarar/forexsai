"use client";

import { X, Building2, TrendingUp, TrendingDown, BarChart3, Target, BookOpen, Zap, DollarSign, PieChart, Users } from "lucide-react";
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

interface EarningsEventModalProps {
  earnings: EarningsEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

const directionConfig = {
  bullish: { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/20", label: { en: "Beat Expected", tr: "Tahmini Aşabilir" } },
  bearish: { icon: TrendingDown, color: "text-red-400", bg: "bg-red-500/20", label: { en: "Miss Expected", tr: "Tahmini Karşılamayabilir" } },
  neutral: { icon: BarChart3, color: "text-gray-400", bg: "bg-gray-500/20", label: { en: "Neutral", tr: "Nötr" } },
};

const sectorIcons: Record<string, string> = {
  Technology: "💻",
  "Consumer Cyclical": "🛒",
  Financials: "🏦",
  Healthcare: "🏥",
  Automotive: "🚗",
  Energy: "⚡",
};

function formatDate(dateStr: string, locale: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString(locale === "en" ? "en-US" : "tr-TR", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return "text-emerald-400";
  if (confidence >= 60) return "text-yellow-400";
  return "text-red-400";
}

export default function EarningsEventModal({ earnings, isOpen, onClose }: EarningsEventModalProps) {
  const { locale } = useI18nStore();
  
  if (!isOpen || !earnings) return null;

  const direction = directionConfig[earnings.predicted_direction];
  const DirectionIcon = direction.icon;
  const confidenceColor = getConfidenceColor(earnings.confidence);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-premium w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl animate-scaleIn">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b border-white/10 bg-background/80 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/30 to-indigo-500/30 flex items-center justify-center text-xl">
              {sectorIcons[earnings.sector] || "🏢"}
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {earnings.company}
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-emerald-400 font-mono">{earnings.ticker}</span>
                <span className="text-[10px] text-textSecondary bg-white/10 px-2 py-0.5 rounded">
                  {earnings.sector}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 transition"
          >
            <X className="w-5 h-5 text-textSecondary" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Date */}
          <div className="text-sm text-textSecondary">
            {formatDate(earnings.timestamp, locale)}
          </div>

          {/* AI Prediction */}
          <div className={`p-4 rounded-xl ${direction.bg} border border-white/10`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <DirectionIcon className={`w-6 h-6 ${direction.color}`} />
                <div>
                  <p className="text-xs text-textSecondary uppercase">
                    {locale === "en" ? "AI Prediction" : "AI Tahmini"}
                  </p>
                  <p className={`text-lg font-bold ${direction.color}`}>
                    {direction.label[locale]}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-textSecondary uppercase">
                  {locale === "en" ? "Confidence" : "Güven"}
                </p>
                <p className={`text-2xl font-bold ${confidenceColor}`}>
                  {earnings.confidence}%
                </p>
              </div>
            </div>
          </div>

          {/* Forecast vs Previous */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span className="text-xs text-emerald-400 uppercase font-semibold">
                  EPS {locale === "en" ? "Forecast" : "Tahmini"}
                </span>
              </div>
              <p className="text-2xl font-bold text-emerald-400 mb-1">
                {earnings.eps_forecast || "--"}
              </p>
              {earnings.previous_eps && (
                <p className="text-xs text-textSecondary">
                  {locale === "en" ? "Previous" : "Önceki"}: {earnings.previous_eps}
                </p>
              )}
            </div>
            
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center gap-2 mb-2">
                <PieChart className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-blue-400 uppercase font-semibold">
                  Revenue {locale === "en" ? "Forecast" : "Tahmini"}
                </span>
              </div>
              <p className="text-2xl font-bold text-blue-400 mb-1">
                {earnings.revenue_forecast || "--"}
              </p>
              {earnings.previous_revenue && (
                <p className="text-xs text-textSecondary">
                  {locale === "en" ? "Previous" : "Önceki"}: {earnings.previous_revenue}
                </p>
              )}
            </div>
          </div>

          {/* What to Watch */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-amber-400">
              <Target className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "Key Metrics to Watch" : "İzlenecek Kilit Metrikler"}
              </h3>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {(locale === "en" ? earnings.key_metrics_to_watch : earnings.key_metrics_to_watch_tr).map((metric, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-2 rounded-lg bg-white/5 text-sm text-white"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  {metric}
                </div>
              ))}
            </div>
          </section>

          {/* AI Analysis */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-purple-400">
              <BookOpen className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "AI Analysis" : "AI Analizi"}
              </h3>
            </div>
            <p className="text-sm text-textSecondary leading-relaxed">
              {locale === "en" ? earnings.analysis : earnings.analysis_tr}
            </p>
          </section>

          {/* Why It Matters */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-blue-400">
              <Zap className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "Why This Matters" : "Neden Önemli"}
              </h3>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <p className="text-sm text-white leading-relaxed">
                {locale === "en" 
                  ? `${earnings.company} is a major component of ${earnings.affected_symbols.join(", ")}. 
                     Earnings surprises can cause significant moves in these indices and related sectors.`
                  : `${earnings.company}, ${earnings.affected_symbols.join(", ")}'ın önemli bir bileşenidir. 
                     Kazanç sürprizleri bu endekslerde ve ilgili sektörlerde önemli hareketlere neden olabilir.`
                }
              </p>
            </div>
          </section>

          {/* Affected Indices */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-emerald-400">
              <Users className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "Affected Indices" : "Etkilenen Endeksler"}
              </h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {earnings.affected_symbols.map((symbol) => (
                <span
                  key={symbol}
                  className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium"
                >
                  {symbol}
                </span>
              ))}
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 p-4 border-t border-white/10 bg-background/80 backdrop-blur">
          <button
            onClick={onClose}
            className="w-full py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium transition"
          >
            {locale === "en" ? "Close" : "Kapat"}
          </button>
        </div>
      </div>
    </div>
  );
}
