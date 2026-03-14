"use client";

import React, { useEffect } from "react";
import { X, Sparkles, Camera, TrendingUp, TrendingDown, Clock, ExternalLink, Brain } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EnrichedNews } from "@/types/news-correlation";

// Translation keys for news modal
const translations = {
  en: {
    aiAnalysis: "ForexSAI AI Analysis",
    marketImpact: "Market Impact",
    affectedAssets: "Affected Assets",
    confidence: "AI Confidence",
    sentiment: "Market Sentiment",
    volatility: "Volatility Expected",
    reasoning: "Reasoning",
    source: "Source",
    close: "Close",
    bullish: "Bullish",
    bearish: "Bearish",
    neutral: "Neutral",
    high: "High",
    medium: "Medium",
    low: "Low",
    riskOn: "Risk On",
    riskOff: "Risk Off",
    translate: "Translate",
    original: "Original",
    newsContent: "News content is provided in English from international sources.",
  },
  tr: {
    aiAnalysis: "ForexSAI Yapay Zeka Analizi",
    marketImpact: "Piyasa Etkisi",
    affectedAssets: "Etkilenen Varlıklar",
    confidence: "YZ Güven Skoru",
    sentiment: "Piyasa Hissiyatı",
    volatility: "Beklenen Volatilite",
    reasoning: "Açıklama",
    source: "Kaynak",
    close: "Kapat",
    bullish: "Yükseliş",
    bearish: "Düşüş",
    neutral: "Nötr",
    high: "Yüksek",
    medium: "Orta",
    low: "Düşük",
    riskOn: "Risk Al",
    riskOff: "Risk Kaçın",
    translate: "Çevir",
    original: "Orijinal",
    newsContent: "Haber içeriği uluslararası kaynaklardan İngilizce olarak sağlanmaktadır.",
  },
  de: {
    aiAnalysis: "ForexSAI KI-Analyse",
    marketImpact: "Marktimpact",
    affectedAssets: "Betroffene Vermögenswerte",
    confidence: "KI-Vertrauen",
    sentiment: "Marktstimmung",
    volatility: "Erwartete Volatilität",
    reasoning: "Begründung",
    source: "Quelle",
    close: "Schließen",
    bullish: "Steigend",
    bearish: "Fallend",
    neutral: "Neutral",
    high: "Hoch",
    medium: "Mittel",
    low: "Niedrig",
    riskOn: "Risiko An",
    riskOff: "Risiko Aus",
    newsContent: "Nachrichten werden auf Englisch von internationalen Quellen bereitgestellt.",
  },
  es: {
    aiAnalysis: "Análisis IA ForexSAI",
    marketImpact: "Impacto del Mercado",
    affectedAssets: "Activos Afectados",
    confidence: "Confianza IA",
    sentiment: "Sentimiento del Mercado",
    volatility: "Volatilidad Esperada",
    reasoning: "Razonamiento",
    source: "Fuente",
    close: "Cerrar",
    bullish: "Alcista",
    bearish: "Bajista",
    neutral: "Neutral",
    high: "Alto",
    medium: "Medio",
    low: "Bajo",
    riskOn: "Riesgo Activado",
    riskOff: "Riesgo Desactivado",
    newsContent: "Las noticias se proporcionan en inglés desde fuentes internacionales.",
  },
  fr: {
    aiAnalysis: "Analyse IA ForexSAI",
    marketImpact: "Impact sur le Marché",
    affectedAssets: "Actifs Concernés",
    confidence: "Confiance IA",
    sentiment: "Sentiment du Marché",
    volatility: "Volatilité Attendue",
    reasoning: "Raisonnement",
    source: "Source",
    close: "Fermer",
    bullish: "Haussier",
    bearish: "Baissier",
    neutral: "Neutre",
    high: "Élevé",
    medium: "Moyen",
    low: "Faible",
    riskOn: "Prise de Risque",
    riskOff: "Évitement du Risque",
    newsContent: "Les actualités sont fournies en anglais par des sources internationales.",
  },
  ar: {
    aiAnalysis: "تحليل الذكاء الاصطناعي",
    marketImpact: "تأثير السوق",
    affectedAssets: "الأصول المتأثرة",
    confidence: "ثقة الذكاء الاصطناعي",
    sentiment: "مشاعر السوق",
    volatility: "التقلب المتوقع",
    reasoning: "التفسير",
    source: "المصدر",
    close: "إغلاق",
    bullish: "صاعد",
    bearish: "هابط",
    neutral: "محايد",
    high: "عالي",
    medium: "متوسط",
    low: "منخفض",
    riskOn: "تقبل المخاطرة",
    riskOff: "تجنب المخاطرة",
    newsContent: "يتم توفير الأخبار باللغة الإنجليزية من مصادر دولية.",
  },
};

interface NewsDetailModalProps {
  news: EnrichedNews | null;
  isOpen: boolean;
  onClose: () => void;
  locale?: keyof typeof translations;
}

function formatRelativeTime(timestamp: string, locale: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInSeconds = Math.max(0, Math.floor((now.getTime() - date.getTime()) / 1000));

  if (locale === "tr") {
    if (diffInSeconds < 60) return `${diffInSeconds} sn önce`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} dk önce`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} sa önce`;
    return `${Math.floor(diffInSeconds / 86400)} g önce`;
  }

  if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
}

function normalizeImpactConfidence(value: unknown): number {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  const normalized = value <= 1 ? value : value / 100;
  return Math.max(0, Math.min(1, normalized));
}

export default function NewsDetailModal({ news, isOpen, onClose, locale = "en" }: NewsDetailModalProps) {
  const t = translations[locale] || translations.en;

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen || !news) return null;

  // Semantic boundaries: headline/summary/analysis are NOT interchangeable.
  // Fall back only within the same semantic field across languages.
  const isTurkish = locale === "tr";
  const isEnglish = locale === "en";
  const localizedHeadline = isTurkish
    ? news.headline_tr || news.headline || ""
    : !isEnglish
      ? news.headline_locale || news.headline || ""
      : news.headline || "";
  const localizedSummary = isTurkish
    ? news.summary_tr || news.summary_en || ""
    : !isEnglish
      ? news.summary_locale || news.summary_en || ""
      : news.summary_en || "";
  const localizedAnalysis = isTurkish
    ? news.analysis_tr || news.analysis_en || ""
    : !isEnglish
      ? news.analysis_locale || news.analysis_en || ""
      : news.analysis_en || "";

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "breaking": return "text-red-400";
      case "high": return "text-orange-400";
      case "medium": return "text-yellow-400";
      default: return "text-gray-400";
    }
  };

  const getUrgencyLabel = (urgency: string) => {
    switch (urgency) {
      case "breaking":
        return locale === "tr" ? "SON DAKİKA" : "BREAKING";
      case "high":
        return t.high;
      case "medium":
        return t.medium;
      default:
        return t.low;
    }
  };

  const getSentimentLabel = (sentiment: string) => {
    switch (sentiment) {
      case "risk_on": return t.riskOn;
      case "risk_off": return t.riskOff;
      default: return t.neutral;
    }
  };

  const getDirectionIcon = (direction: string) => {
    if (direction === "bullish") return <TrendingUp className="w-3 h-3" />;
    if (direction === "bearish") return <TrendingDown className="w-3 h-3" />;
    return null;
  };

  const getDirectionColor = (direction: string) => {
    if (direction === "bullish") return "text-green-400 bg-green-500/10 border-green-500/30";
    if (direction === "bearish") return "text-red-400 bg-red-500/10 border-red-500/30";
    return "text-gray-400 bg-gray-700/50 border-gray-600";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-2xl mx-4 bg-[#0f0f0f] border border-gray-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="p-6">
          {/* Time */}
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500">
              {formatRelativeTime(news.timestamp, locale)}
            </span>
            <span className={cn("text-xs font-bold uppercase tracking-wider ml-2", getUrgencyColor(news.urgency))}>
              {getUrgencyLabel(news.urgency)}
            </span>
          </div>

          {/* Headline - Localized */}
          <h2 className="text-xl font-bold text-white mb-4 leading-tight pr-8">
            {localizedHeadline}
          </h2>

          {/* AI Analysis Section */}
          <div className="bg-gradient-to-br from-purple-500/5 to-blue-500/5 border border-purple-500/20 rounded-xl p-5 mb-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center">
                <Brain className="w-4 h-4 text-purple-400" />
              </div>
              <span className="font-semibold text-purple-400">{t.aiAnalysis}</span>
            </div>

            <div className="space-y-4 mb-4">
              <div>
                <span className="text-[11px] text-purple-300 uppercase tracking-wider block mb-2">
                  {isTurkish ? "Özet" : "Summary"}
                </span>
                <p className="text-gray-200 text-sm leading-relaxed">
                  {localizedSummary}
                </p>
              </div>

              <div>
                <span className="text-[11px] text-blue-300 uppercase tracking-wider block mb-2">
                  {isTurkish ? "Analiz" : "Analysis"}
                </span>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {localizedAnalysis}
                </p>
              </div>
            </div>

            {/* Affected Assets */}
            <div className="mb-4">
              <span className="text-xs text-gray-500 uppercase tracking-wider mb-2 block">{t.affectedAssets}</span>
              <div className="flex flex-wrap gap-2">
                {news.impacts?.map((impact, idx) => (
                  <span
                    key={idx}
                    className={cn(
                      "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border",
                      getDirectionColor(impact.direction)
                    )}
                  >
                    {getDirectionIcon(impact.direction)}
                    {impact.symbol}
                    <span className="opacity-60">{impact.score}/10</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Analysis Details Grid */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-purple-500/20">
              <div>
                <span className="text-xs text-gray-500 block mb-1">{t.confidence}</span>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-purple-500 rounded-full"
                      style={{ width: `${news.aiConfidence || 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">{news.aiConfidence ? Math.round(news.aiConfidence) : 0}%</span>
                </div>
              </div>
              <div>
                <span className="text-xs text-gray-500 block mb-1">{t.sentiment}</span>
                <span className={cn(
                  "text-sm font-medium",
                  news.sentiment === "risk_on" ? "text-green-400" : 
                  news.sentiment === "risk_off" ? "text-red-400" : "text-yellow-400"
                )}>
                  {getSentimentLabel(news.sentiment)}
                </span>
              </div>
              <div>
                <span className="text-xs text-gray-500 block mb-1">{t.volatility}</span>
                <span className={cn(
                  "text-sm font-medium capitalize",
                  news.volatilityExpectation === "high" ? "text-red-400" :
                  news.volatilityExpectation === "medium" ? "text-yellow-400" : "text-green-400"
                )}>
                  {t[news.volatilityExpectation] || news.volatilityExpectation}
                </span>
              </div>
            </div>
          </div>

          {/* Impact Details */}
          {news.impacts && news.impacts.length > 0 && (
            <div className="mb-5">
              <span className="text-xs text-gray-500 uppercase tracking-wider mb-3 block">{t.marketImpact}</span>
              <div className="space-y-2">
                {news.impacts.map((impact, idx) => {
                  const impactConfidence = normalizeImpactConfidence(impact.confidence);
                  return (
                    <div key={idx} className="flex items-center justify-between py-2 px-3 bg-gray-900/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className={cn(
                          "text-sm font-semibold",
                          impact.direction === "bullish" ? "text-green-400" :
                            impact.direction === "bearish" ? "text-red-400" : "text-gray-400"
                        )}>
                          {impact.symbol}
                        </span>
                        <span className="text-xs text-gray-500">
                          {locale === "tr"
                            ? impact.reasoning_tr || impact.reasoning
                            : impact.reasoning_locale || impact.reasoning}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="flex gap-0.5">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <div
                              key={i}
                              className={cn(
                                "w-1.5 h-1.5 rounded-full",
                                i < Math.round(impactConfidence * 5) ? "bg-purple-500" : "bg-gray-700"
                              )}
                            />
                          ))}
                        </div>
                        <span className="text-xs text-gray-400 ml-2">{Math.round(impactConfidence * 100)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-800">
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500">{t.source}: {news.source}</span>
              <span className="text-xs text-gray-600">
                {new Date(news.timestamp).toLocaleString(locale === "tr" ? "tr-TR" : locale === "de" ? "de-DE" : "en-US")}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-2 text-gray-500 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition-colors">
                <Sparkles className="w-4 h-4" />
              </button>
              <button className="p-2 text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors">
                <Camera className="w-4 h-4" />
              </button>
              <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
