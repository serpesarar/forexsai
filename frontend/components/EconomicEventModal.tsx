"use client";

import { X, Calendar, Clock, TrendingUp, TrendingDown, AlertTriangle, Info, Target, BookOpen, Zap } from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

interface EconomicEvent {
  id: string;
  timestamp: string;
  title: string;
  title_tr: string;
  currency: string;
  impact: "High" | "Medium" | "Low";
  actual: string | null;
  forecast: string | null;
  previous: string | null;
  predicted_direction: "bullish" | "bearish" | "neutral" | "volatile";
  affected_symbols: string[];
  impact_analysis: string;
  impact_analysis_tr: string;
  description: string;
  description_tr: string;
  why_it_matters: string;
  why_it_matters_tr: string;
  typical_market_reaction: string;
  typical_market_reaction_tr: string;
  is_upcoming: boolean;
  minutes_until: number | null;
}

interface EconomicEventModalProps {
  event: EconomicEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

const impactConfig = {
  High: {
    color: "text-red-400",
    bg: "bg-red-500/20",
    border: "border-red-500/40",
    label: { en: "HIGH IMPACT", tr: "YÜKSEK ETKİ" }
  },
  Medium: {
    color: "text-yellow-400",
    bg: "bg-yellow-500/20",
    border: "border-yellow-500/40",
    label: { en: "MEDIUM IMPACT", tr: "ORTA ETKİ" }
  },
  Low: {
    color: "text-green-400",
    bg: "bg-green-500/20",
    border: "border-green-500/40",
    label: { en: "LOW IMPACT", tr: "DÜŞÜK ETKİ" }
  }
};

const directionConfig = {
  bullish: { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/20" },
  bearish: { icon: TrendingDown, color: "text-red-400", bg: "bg-red-500/20" },
  neutral: { icon: Info, color: "text-gray-400", bg: "bg-gray-500/20" },
  volatile: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-500/20" },
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

export default function EconomicEventModal({ event, isOpen, onClose }: EconomicEventModalProps) {
  const { locale } = useI18nStore();
  
  if (!isOpen || !event) return null;

  const impact = impactConfig[event.impact];
  const direction = directionConfig[event.predicted_direction];
  const DirectionIcon = direction.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-premium w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl animate-scaleIn">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b border-white/10 bg-background/80 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl ${impact.bg} ${impact.border} border`}>
              <Calendar className={`w-5 h-5 ${impact.color}`} />
            </div>
            <div>
              <span className={`text-[10px] font-bold uppercase tracking-wider ${impact.color}`}>
                {impact.label[locale]}
              </span>
              <h2 className="text-lg font-bold text-white">
                {locale === "en" ? event.title : event.title_tr}
              </h2>
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
          {/* Date & Time */}
          <div className="flex items-center gap-4 text-sm text-textSecondary">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>{formatDate(event.timestamp, locale)}</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-white/10 text-xs">
              {event.currency}
            </span>
          </div>

          {/* Expected Direction */}
          <div className={`p-4 rounded-xl ${direction.bg} border border-white/10`}>
            <div className="flex items-center gap-3">
              <DirectionIcon className={`w-6 h-6 ${direction.color}`} />
              <div>
                <p className="text-xs text-textSecondary uppercase">
                  {locale === "en" ? "AI Predicted Market Direction" : "AI Tahmini Piyasa Yönü"}
                </p>
                <p className={`text-lg font-bold ${direction.color}`}>
                  {event.predicted_direction === "bullish" && (locale === "en" ? "Bullish" : "Yükseliş")}
                  {event.predicted_direction === "bearish" && (locale === "en" ? "Bearish" : "Düşüş")}
                  {event.predicted_direction === "neutral" && (locale === "en" ? "Neutral" : "Nötr")}
                  {event.predicted_direction === "volatile" && (locale === "en" ? "High Volatility Expected" : "Yüksek Volatilite Bekleniyor")}
                </p>
              </div>
            </div>
          </div>

          {/* What is This? */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-emerald-400">
              <BookOpen className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "What is this data?" : "Bu veri nedir?"}
              </h3>
            </div>
            <p className="text-sm text-textSecondary leading-relaxed">
              {locale === "en" ? event.description : event.description_tr}
            </p>
          </section>

          {/* Why It Matters */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-amber-400">
              <Target className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "Why does it matter?" : "Neden önemli?"}
              </h3>
            </div>
            <p className="text-sm text-textSecondary leading-relaxed">
              {locale === "en" ? event.why_it_matters : event.why_it_matters_tr}
            </p>
          </section>

          {/* Typical Market Reaction */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-blue-400">
              <Zap className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "How do markets typically react?" : "Piyasalar genellikle nasıl tepki verir?"}
              </h3>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <p className="text-sm text-white leading-relaxed">
                {locale === "en" ? event.typical_market_reaction : event.typical_market_reaction_tr}
              </p>
            </div>
          </section>

          {/* AI Analysis */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-purple-400">
              <Info className="w-4 h-4" />
              <h3 className="text-sm font-semibold uppercase">
                {locale === "en" ? "AI Impact Analysis" : "AI Etki Analizi"}
              </h3>
            </div>
            <p className="text-sm text-textSecondary leading-relaxed">
              {locale === "en" ? event.impact_analysis : event.impact_analysis_tr}
            </p>
          </section>

          {/* Affected Symbols */}
          <section className="space-y-2">
            <h3 className="text-sm font-semibold text-white uppercase">
              {locale === "en" ? "Affected Markets" : "Etkilenen Piyasalar"}
            </h3>
            <div className="flex flex-wrap gap-2">
              {event.affected_symbols.map((symbol) => (
                <span
                  key={symbol}
                  className="px-3 py-1.5 rounded-lg bg-white/10 text-white text-sm font-medium"
                >
                  {symbol}
                </span>
              ))}
            </div>
          </section>

          {/* Data Table */}
          {event.is_upcoming && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-white uppercase">
                {locale === "en" ? "Expected Data" : "Beklenen Veriler"}
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-white/5 text-center">
                  <p className="text-[10px] text-textSecondary uppercase mb-1">
                    {locale === "en" ? "Previous" : "Önceki"}
                  </p>
                  <p className="text-lg font-bold text-white">{event.previous || "--"}</p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <p className="text-[10px] text-emerald-400 uppercase mb-1">
                    {locale === "en" ? "Forecast" : "Tahmin"}
                  </p>
                  <p className="text-lg font-bold text-emerald-400">{event.forecast || "--"}</p>
                </div>
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-center">
                  <p className="text-[10px] text-blue-400 uppercase mb-1">
                    {locale === "en" ? "Actual" : "Gerçekleşen"}
                  </p>
                  <p className="text-lg font-bold text-blue-400">{event.actual || "--"}</p>
                </div>
              </div>
            </section>
          )}
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
