"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time, type CandlestickData } from "lightweight-charts";
import { format, isWithinInterval, subMinutes, addMinutes } from "date-fns";
import { useRouter } from "next/navigation";
import {
  Bell, Star, Wallet, Calendar, MessageSquare, Newspaper,
  Building2, LineChart, BookOpen, ChevronLeft,
  TrendingUp, TrendingDown, Sparkles,
  AlertTriangle, RefreshCw, X, ArrowUp, ArrowDown, Brain
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetcher } from "@/lib/api";
import { buildWebSocketUrl } from "@/lib/api/base";
import { fetchNewsForCandle, MatchedNewsItem } from "@/lib/api/rssNews";
import { normalizeCandles } from "@/lib/chart/normalizeCandles";
import { buildActualTimeChartCandles, buildRenderableChartSeries, buildMappedChartMarkers, chartTimeToTimestampSeconds, findTimelineChartCandle } from "@/lib/chart/newsCorrelationTimeline";
import { useNewsMarkers } from "@/hooks/useNewsMarkers";
import Link from "next/link";
import type { EnrichedNews } from "@/types/news-correlation";
import NewsDetailModal from "@/components/NewsDetailModal";

// ==================== TYPES ====================
interface ChartCandle {
  timestamp: number;
  time: number | string;
  actualTimestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  priceChange: number;
}

interface SymbolData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface OHLCVResponse {
  symbol: string;
  timeframe: string;
  data: Array<{
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

const NEWS_SYMBOL_FAMILIES: Record<string, string[]> = {
  XAUUSD: ["XAUUSD", "XAU/USD", "XAU", "GOLD", "GC"],
  NDX: ["NDX", "NDX.INDX", "NASDAQ", "IXIC", "QQQ"],
  DAX: ["DAX", "GDAXI", "GDAXI.INDX", "DE40"],
  USOIL: ["USOIL", "USOIL.FOREX", "WTI", "CL", "CL.COMM", "OIL"],
  VIX: ["VIX", "VIX.INDX", "VOLATILITY"],
  DXY: ["DXY", "DXY.INDX", "DOLLAR", "USD"],
};

const WS_BACKED_SYMBOLS = new Set(["XAUUSD", "NDX", "DAX", "USOIL"]);

function normalizeImpactSymbol(symbol?: string | null): string {
  return (symbol ?? "").toUpperCase().replace(/[^A-Z0-9.]/g, "");
}

function matchesSelectedSymbol(impactSymbol: string | undefined, selectedSymbol: string): boolean {
  if (impactSymbol === "*") {
    return true;
  }

  const normalizedImpact = normalizeImpactSymbol(impactSymbol);
  const aliases = NEWS_SYMBOL_FAMILIES[selectedSymbol] ?? [selectedSymbol];

  return aliases.some((alias) => normalizeImpactSymbol(alias) === normalizedImpact);
}

function sortNewsByTimestamp(items: EnrichedNews[]): EnrichedNews[] {
  return [...items].sort(
    (left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime()
  );
}

function normalizeAiConfidence(value: unknown): number {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, normalized));
}

function normalizeImpactDirection(value: unknown): EnrichedNews["impacts"][number]["direction"] {
  return value === "bullish" || value === "bearish" || value === "neutral"
    ? value
    : "neutral";
}

function normalizeUrgency(value: unknown): EnrichedNews["urgency"] {
  return value === "breaking" || value === "high" || value === "medium" || value === "low"
    ? value
    : "low";
}

// --- Page-level UI translations ---
const PAGE_T: Record<string, Record<string, string>> = {
  en: {
    marketAnalysis: "Market Analysis",
    swingTrading: "Swing Trading",
    dayTrading: "Day Trading",
    newsFeed: "News Feed",
    highImpact: "High Impact",
    bullish: "Bullish",
    slightlyBearish: "Slightly Bearish",
    breaking: "BREAKING",
    impactSuffix: "IMPACT",
    loadingChart: "Loading chart...",
    retry: "Retry",
    clickCandle: "💡 Click any candle to inspect related catalysts",
    candleAnalysis: "Candle Analysis",
    open: "Open",
    close: "Close",
    high: "High",
    low: "Low",
    bigSurge: "Big Surge",
    bigDrop: "Big Drop",
    aiAnalysis: "AI Analysis",
    analyzingMove: "Analyzing price movement...",
    news: "News",
    economic: "Economic",
    earnings: "Earnings",
    all: "All",
    popular: "Popular",
    noNewsFilter: "No news matches the current filter",
    noNewsAvailable: "No news available",
    noNewsFilterDetail: "DeepSeek-analyzed news exists, but the current filter is hiding it. Switch to All to see the full feed.",
    noNewsDetail: "Supabase enriched_news table may be empty or API is not responding",
    showAllNews: "Show all news",
    retryApi: "Retry API",
    loadTestNews: "🧪 Load Test News",
    importance: "Importance",
    confidence: "Confidence",
    fallbackAnalysis: "Fallback Analysis",
    noStrongCatalyst: "No strong catalyst was found for this significant price move.",
    noCatalyst: "No known news catalyst during this candle's timeframe.",
    affectedSymbols: "Affected Symbols",
    scenarioVariations: "Scenario Variations",
    deepseekAnalysis: "DeepSeek Analysis",
    scenarioUnavailable: "Scenario analysis unavailable. Check API key or try again later.",
    analyzingAI: "Analyzing with AI...",
    afterMarket: "After Market",
    preMarket: "Pre Market",
    preMarketShort: "After",
    preMarketShortPre: "Pre",
    proTip: "💡 Pro Tip:",
    impact: "Impact",
    matched: "matched",
    relatedCatalysts: "Related Catalysts",
    findingCatalysts: "Finding relevant catalysts...",
    technicalFlow: "This move may have been driven by positioning, liquidity, or purely technical flow.",
    economicEvents: "Economic Events",
    earningsReports: "Earnings Reports",
    noEconomicEvents: "No economic events scheduled",
    noEarningsReports: "No earnings reports scheduled",
    economicEvent: "Economic Event",
    earningsReport: "Earnings Report",
    previous: "Previous",
    forecast: "Forecast",
    prev: "Prev",
    exp: "Exp",
    expectedDirection: "Expected Direction",
    bullishDirection: "📈 Bullish - Expected positive market reaction",
    bearishDirection: "📉 Bearish - Expected negative market reaction",
    neutralDirection: "➖ Neutral - Limited market impact expected",
    volatileDirection: "⚡ Volatile - Expect sharp two-way price swings",
    description: "Description",
    whyItMatters: "Why It Matters",
    clickDetails: "Click for details →",
    betterThanExpected: "Better Than Expected",
    worseThanExpected: "Worse Than Expected",
    asExpected: "As Expected",
    first5min: "First 5 min",
    firstHour: "First hour",
    dayClose: "Day close",
    nextDay: "Next day",
    restOfDay: "Rest of day",
    epsEstimate: "EPS Estimate",
    revenueEstimate: "Revenue Estimate",
    previousEps: "Previous EPS",
    previousRevenue: "Previous Revenue",
    aiPrediction: "AI Prediction",
    beatExpected: "📈 Beat Expected",
    missExpected: "📉 Miss Expected",
    inLineExpected: "➖ In Line Expected",
    highVolExpected: "⚡ High Volatility Expected",
    beatScenario: "Beat (EPS & Revenue)",
    missScenario: "Miss (EPS or Revenue)",
    mixedScenario: "Mixed (Beat EPS, Miss Revenue or vice versa)",
    inLineScenario: "In Line (Meets Expectations)",
    preMarketLabel: "Pre-market",
    openLabel: "Open",
    sectorLabel: "Sector",
    guidanceLabel: "Guidance",
    keyMetrics: "Key Metrics to Watch",
    newsFeedFresh: "News feed fresh",
    newsFeedMock: "Showing manual test news",
    newsFeedError: "News feed unavailable",
    newsFeedStale: "News feed stale or empty",
    summaryLabel: "Summary",
    analysisLabel: "Analysis",
    labelHigh: "High",
    labelMedium: "Medium",
    labelLow: "Low",
    labelCritical: "Critical",
    labelNeutral: "Neutral",
    labelVolatile: "Volatile",
    currentPrice: "Current",
    pullbackPrice: "Pullback",
    targetPrice: "Target",
    noNearbyCatalyst: "No nearby catalyst was matched to this candle.",
    noNewsFound: "No news found.",
    newsStatusChanged: "News feed status changed.",
    loadTestNewsTitle: "Load test news data",
    testLabel: "🧪 Test",
    refreshLabel: "Refresh",
    mon: "Mon",
    tue: "Tue",
    wed: "Wed",
    thu: "Thu",
    fri: "Fri",
    alerts: "Alerts",
    watchlist: "Watchlist",
    smartTrades: "Smart Trades",
    economicCalendar: "Economic Calendar",
    chatAi: "Chat AI",
    researchReports: "Research Reports",
    docs: "Docs",
    brokers: "Brokers",
    myTrades: "My Trades",
    secondsAgoSuffix: "s ago",
    minutesAgoSuffix: "m ago",
    hoursAgoSuffix: "h ago",
    daysAgoSuffix: "d ago",
    unknownTime: "...",
  },
  tr: {
    marketAnalysis: "Piyasa Analizi",
    swingTrading: "Swing Trading",
    dayTrading: "Gün İçi Trading",
    newsFeed: "Haber Akışı",
    highImpact: "Yüksek Etki",
    bullish: "Yükseliş",
    slightlyBearish: "Hafif Düşüş",
    breaking: "SON DAKİKA",
    impactSuffix: "ETKİ",
    loadingChart: "Grafik yükleniyor...",
    retry: "Tekrar Dene",
    clickCandle: "💡 Katalizör analizi için muma tıklayın",
    candleAnalysis: "Mum Analizi",
    open: "Açılış",
    close: "Kapanış",
    high: "Yüksek",
    low: "Düşük",
    bigSurge: "Büyük Yükseliş",
    bigDrop: "Büyük Düşüş",
    aiAnalysis: "AI Analizi",
    analyzingMove: "Fiyat hareketi analiz ediliyor...",
    news: "Haberler",
    economic: "Ekonomik",
    earnings: "Bilanço",
    all: "Tümü",
    popular: "Popüler",
    noNewsFilter: "Mevcut filtreye uyan haber yok",
    noNewsAvailable: "Haber bulunamadı",
    noNewsFilterDetail: "DeepSeek analiz edilmiş haberler mevcut, ancak filtre bunları gizliyor. Tüm haberleri görmek için Tümü'ne geçin.",
    noNewsDetail: "Supabase enriched_news tablosu boş olabilir veya API yanıt vermiyor",
    showAllNews: "Tüm haberleri göster",
    retryApi: "API Tekrar Dene",
    loadTestNews: "🧪 Test Haberleri Yükle",
    importance: "Önem",
    confidence: "Güven",
    fallbackAnalysis: "Yedek Analiz",
    noStrongCatalyst: "Bu önemli fiyat hareketi için güçlü bir katalizör bulunamadı.",
    noCatalyst: "Bu mumun zaman diliminde bilinen bir haber katalizörü yok.",
    affectedSymbols: "Etkilenen Semboller",
    scenarioVariations: "Senaryo Varyasyonları",
    deepseekAnalysis: "DeepSeek Analizi",
    scenarioUnavailable: "Senaryo analizi mevcut değil. API anahtarını kontrol edin veya tekrar deneyin.",
    analyzingAI: "AI ile analiz ediliyor...",
    afterMarket: "Piyasa Sonrası",
    preMarket: "Piyasa Öncesi",
    preMarketShort: "Sonra",
    preMarketShortPre: "Önce",
    proTip: "💡 İpucu:",
    impact: "Etki",
    matched: "eşleşen",
    relatedCatalysts: "İlgili Katalizörler",
    findingCatalysts: "İlgili katalizörler aranıyor...",
    technicalFlow: "Bu hareket pozisyonlama, likidite veya tamamen teknik akıştan kaynaklanmış olabilir.",
    economicEvents: "Ekonomik Olaylar",
    earningsReports: "Bilanço Raporları",
    noEconomicEvents: "Planlanmış ekonomik olay yok",
    noEarningsReports: "Planlanmış bilanço raporu yok",
    economicEvent: "Ekonomik Olay",
    earningsReport: "Bilanço Raporu",
    previous: "Önceki",
    forecast: "Tahmin",
    prev: "Önceki",
    exp: "Bkl",
    expectedDirection: "Beklenen Yön",
    bullishDirection: "📈 Yükseliş - Pozitif piyasa tepkisi bekleniyor",
    bearishDirection: "📉 Düşüş - Negatif piyasa tepkisi bekleniyor",
    neutralDirection: "➖ Nötr - Sınırlı piyasa etkisi bekleniyor",
    volatileDirection: "⚡ Volatil - İki yönlü sert fiyat hareketleri bekleniyor",
    description: "Açıklama",
    whyItMatters: "Neden Önemli",
    clickDetails: "Detaylar için tıklayın →",
    betterThanExpected: "Beklentiden İyi",
    worseThanExpected: "Beklentiden Kötü",
    asExpected: "Beklenen",
    first5min: "İlk 5 dk",
    firstHour: "İlk saat",
    dayClose: "Gün kapanış",
    nextDay: "Ertesi gün",
    restOfDay: "Günün geri kalanı",
    epsEstimate: "HBK Tahmini",
    revenueEstimate: "Gelir Tahmini",
    previousEps: "Önceki HBK",
    previousRevenue: "Önceki Gelir",
    aiPrediction: "AI Tahmini",
    beatExpected: "📈 Beklentiyi Aşması Bekleniyor",
    missExpected: "📉 Beklentinin Altı Bekleniyor",
    inLineExpected: "➖ Beklentiye Uygun",
    highVolExpected: "⚡ Yüksek Volatilite Bekleniyor",
    beatScenario: "Beklentiyi Aşma (HBK & Gelir)",
    missScenario: "Beklentinin Altı (HBK veya Gelir)",
    mixedScenario: "Karışık (HBK iyi, Gelir kötü veya tersi)",
    inLineScenario: "Beklentiye Uygun",
    preMarketLabel: "Piyasa öncesi",
    openLabel: "Açılış",
    sectorLabel: "Sektör",
    guidanceLabel: "Rehberlik",
    keyMetrics: "İzlenecek Temel Metrikler",
    newsFeedFresh: "Haber akışı güncel",
    newsFeedMock: "Manuel test haberleri gösteriliyor",
    newsFeedError: "Haber akışı kullanılamıyor",
    newsFeedStale: "Haber akışı eski veya boş",
    summaryLabel: "Özet",
    analysisLabel: "Analiz",
    labelHigh: "Yüksek",
    labelMedium: "Orta",
    labelLow: "Düşük",
    labelCritical: "Kritik",
    labelNeutral: "Nötr",
    labelVolatile: "Volatil",
    currentPrice: "Güncel",
    pullbackPrice: "Geri Çekilme",
    targetPrice: "Hedef",
    noNearbyCatalyst: "Bu mum için yakın bir katalizör eşleşmedi.",
    noNewsFound: "Haber bulunamadı.",
    newsStatusChanged: "Haber akışı durumu değişti.",
    loadTestNewsTitle: "Test haber verisini yükle",
    testLabel: "🧪 Test",
    refreshLabel: "Yenile",
    mon: "Pzt",
    tue: "Sal",
    wed: "Çar",
    thu: "Per",
    fri: "Cum",
    alerts: "Uyarılar",
    watchlist: "İzleme Listesi",
    smartTrades: "Akıllı İşlemler",
    economicCalendar: "Ekonomik Takvim",
    chatAi: "AI Sohbet",
    researchReports: "Araştırma Raporları",
    docs: "Dokümanlar",
    brokers: "Brokerler",
    myTrades: "İşlemlerim",
    secondsAgoSuffix: " sn önce",
    minutesAgoSuffix: " dk önce",
    hoursAgoSuffix: " sa önce",
    daysAgoSuffix: " g önce",
    unknownTime: "...",
  },
};

function getT(locale: string): Record<string, string> {
  return PAGE_T[locale] || PAGE_T.en;
}

function formatImportanceLabel(level: ImportanceLevel | null | undefined, locale: string): string {
  const t = getT(locale);
  if (!level) return t.importance;
  if (level === "critical") return t.labelCritical;
  if (level === "high") return t.labelHigh;
  if (level === "medium") return t.labelMedium;
  return t.labelLow;
}

function formatUrgencyLabel(urgency: string | undefined, locale: string): string {
  const t = getT(locale);
  if (urgency === "breaking") return t.breaking;
  if (urgency === "high") return t.labelHigh;
  if (urgency === "medium") return t.labelMedium;
  return t.labelLow;
}

function formatDirectionLabel(direction: EventDirection | undefined | null, locale: string): string {
  const t = getT(locale);
  if (direction === "bullish") return t.bullish;
  if (direction === "bearish") return locale === "tr" ? "Düşüş" : "Bearish";
  if (direction === "volatile") return t.labelVolatile;
  return t.labelNeutral;
}

function formatImpactLevelLabel(impact: string | undefined, locale: string): string {
  const normalized = String(impact || "").toLowerCase();
  const t = getT(locale);
  if (normalized === "high") return t.labelHigh;
  if (normalized === "medium") return t.labelMedium;
  if (normalized === "low") return t.labelLow;
  return impact || "";
}

function formatDirectionSummary(direction: EventDirection | undefined | null, locale: string): string {
  const t = getT(locale);
  if (direction === "bullish") return t.bullishDirection;
  if (direction === "bearish") return t.bearishDirection;
  if (direction === "volatile") return t.volatileDirection;
  return t.neutralDirection;
}

function formatSessionShort(time: string | undefined, locale: string): string {
  const t = getT(locale);
  return time === "after_market" ? t.preMarketShort : t.preMarketShortPre;
}

function formatSessionLabel(time: string | undefined, locale: string): string {
  const t = getT(locale);
  return time === "after_market" ? t.afterMarket : t.preMarket;
}

function normalizeDisplayConfidence(value: unknown): number {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, normalized));
}

function localeCopy(locale: string, english: string, turkish: string): string {
  return locale === "tr" ? turkish : english;
}

function isTurkishLocale(locale: string): boolean {
  return locale === "tr";
}

function isEnglishLocale(locale: string): boolean {
  return locale === "en";
}

function usesRuntimeLocale(locale: string): boolean {
  return !isTurkishLocale(locale) && !isEnglishLocale(locale);
}

// --- Localization helpers ---
// RULE: Each getter falls back ONLY to the same semantic field in another language.
// headline → headline_tr → headline_locale → headline (EN) → ""
// summary  → summary_tr  → summary_locale  → summary_en  → ""
// analysis → analysis_tr → analysis_locale  → analysis_en → ""
// NEVER cross headline↔summary↔analysis boundaries.
function getLocalizedHeadline(item: EnrichedNews, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.headline_tr || item.headline || "";
  }
  if (usesRuntimeLocale(locale)) {
    return item.headline_locale || item.headline || "";
  }
  return item.headline || "";
}

function getLocalizedSummary(item: EnrichedNews, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.summary_tr || item.summary_en || "";
  }
  if (usesRuntimeLocale(locale)) {
    return item.summary_locale || item.summary_en || "";
  }
  return item.summary_en || "";
}

function getLocalizedAnalysis(item: EnrichedNews, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.analysis_tr || item.analysis_en || "";
  }
  if (usesRuntimeLocale(locale)) {
    return item.analysis_locale || item.analysis_en || "";
  }
  return item.analysis_en || "";
}

function getLocalizedMatchedHeadline(item: MatchedNewsItem | EnrichedNews, locale: string): string {
  if (!isMatchedNewsItem(item)) {
    return getLocalizedHeadline(item, locale);
  }
  if (isTurkishLocale(locale)) {
    return item.headline || item.headline_en || "";
  }
  if (usesRuntimeLocale(locale)) {
    return item.headline_locale || item.headline_en || item.headline || "";
  }
  return item.headline_en || item.headline || "";
}

function getLocalizedMatchedSummary(item: MatchedNewsItem | EnrichedNews, locale: string): string {
  if (!isMatchedNewsItem(item)) {
    return getLocalizedSummary(item, locale);
  }
  if (isTurkishLocale(locale)) {
    return item.summary_tr || item.summary_en || "";
  }
  if (usesRuntimeLocale(locale)) {
    return item.summary_locale || item.summary_en || "";
  }
  return item.summary_en || "";
}

function getMatchedCatalystType(item: MatchedNewsItem | EnrichedNews): "news" | "economic" | "earnings" {
  return isMatchedNewsItem(item) ? item.catalyst_type || "news" : "news";
}

function getCatalystBadge(item: MatchedNewsItem | EnrichedNews, locale: string): string {
  const labels = {
    en: { news: "News", economic: "Economic", earnings: "Earnings", context: "Context" },
    tr: { news: "Haber", economic: "Ekonomik", earnings: "Bilanço", context: "Bağlam" },
  };

  const language = isTurkishLocale(locale) ? "tr" : "en";
  const labelSet = labels[language];
  const catalystLabel = labelSet[getMatchedCatalystType(item)] || labelSet.news;
  return isMatchedNewsItem(item) && item.match_quality === "context" ? `${catalystLabel} · ${labelSet.context}` : catalystLabel;
}

function normalizeNewsItem(item: any): EnrichedNews {
  return {
    id: String(item.id ?? ""),
    timestamp: item.timestamp || item.published_at || new Date().toISOString(),
    source: item.source || "Unknown",
    // Semantic boundaries: each field falls back ONLY within its own semantic category.
    // headline → headline_en → ""  (NEVER summary or analysis)
    // summary  → summary_en → ""  (NEVER headline or analysis)
    // analysis → analysis_en → "" (NEVER headline or summary)
    headline: item.headline || item.headline_en || "",
    headline_tr: item.headline_tr || "",
    content: item.content || "",
    content_tr: item.content_tr || "",
    summary_en: item.summary_en || "",
    summary_tr: item.summary_tr || "",
    analysis_en: item.analysis_en || item.analysis || "",
    analysis_tr: item.analysis_tr || "",
    headline_locale: item.headline_locale || undefined,
    summary_locale: item.summary_locale || undefined,
    analysis_locale: item.analysis_locale || undefined,
    category: item.category || "general",
    url: item.url || item.source_url || "",
    impacts: Array.isArray(item.impacts)
      ? item.impacts.map((impact: any) => ({
          ...impact,
          reasoning_locale: impact?.reasoning_locale || undefined,
        }))
      : [],
    sentiment: item.sentiment || "neutral",
    volatilityExpectation: item.volatilityExpectation || item.volatility_expectation || "medium",
    urgency: normalizeUrgency(item.urgency),
    eventDuration: item.eventDuration || item.event_duration || "short_term",
    affectedCandles: Array.isArray(item.affectedCandles)
      ? item.affectedCandles
      : Array.isArray(item.affected_candles)
        ? item.affected_candles
        : [],
    aiConfidence: normalizeAiConfidence(item.aiConfidence ?? item.ai_confidence),
    analysisTimestamp: item.analysisTimestamp || item.analysis_timestamp || item.timestamp || new Date().toISOString(),
  };
}

function isMatchedNewsItem(item: EnrichedNews | MatchedNewsItem): item is MatchedNewsItem {
  return "relevance_score" in item || "headline_en" in item;
}

type EventDirection = "bullish" | "bearish" | "neutral" | "volatile";
type ImportanceLevel = "critical" | "high" | "medium" | "low";
type EarningsTime = "after_market" | "before_market";

interface CandleNews {
  candle: ChartCandle;
  news: MatchedNewsItem[];
  hasBigMove: boolean;
  moveType: "up" | "down" | "none";
  movePercent: number;
  isLoadingNews?: boolean;
}

interface ScenarioImpact {
  symbol: string;
  direction: EventDirection;
  magnitude: string;
}

interface Scenario {
  direction: string;
  first_5min?: string;
  first_hour?: string;
  day_close?: string;
  next_day?: string;
  pre_market?: string;
  open?: string;
  sector_effect?: string;
  guidance_importance?: string;
  guidance_focus?: string;
  trading_approach?: string;
  impacts?: ScenarioImpact[];
}

interface Scenarios {
  better_than_expected?: Scenario;
  worse_than_expected?: Scenario;
  as_expected?: Scenario;
  beat?: Scenario;
  miss?: Scenario;
  mixed?: Scenario;
  inline?: Scenario;
}

function getMarkerLookbackHours(timeframe: string): number {
  if (timeframe === "1d") return 24 * 90;
  if (timeframe === "4h") return 24 * 45;
  if (timeframe === "1h") return 24 * 21;
  return 72;
}

function getCatalystSectionMeta(
  catalystType: "news" | "economic" | "earnings",
  locale: string
): { icon: string; title: string; accentClass: string } {
  const t = getT(locale);
  if (catalystType === "economic") {
    return {
      icon: "📊",
      title: t.economicEvents,
      accentClass: "bg-amber-500/15 text-amber-300 border-amber-500/20",
    };
  }
  if (catalystType === "earnings") {
    return {
      icon: "💼",
      title: t.earningsReports,
      accentClass: "bg-blue-500/15 text-blue-300 border-blue-500/20",
    };
  }
  return {
    icon: "📰",
    title: t.news,
    accentClass: "bg-purple-500/15 text-purple-300 border-purple-500/20",
  };
}

function groupCatalystsByType(items: MatchedNewsItem[]) {
  return {
    news: items.filter((item) => getMatchedCatalystType(item) === "news"),
    economic: items.filter((item) => getMatchedCatalystType(item) === "economic"),
    earnings: items.filter((item) => getMatchedCatalystType(item) === "earnings"),
  };
}

function toFallbackMatchedItem(item: EnrichedNews, selectedSymbol: string): MatchedNewsItem {
  const primaryImpact = item.impacts.find((impact) => matchesSelectedSymbol(impact.symbol, selectedSymbol)) || item.impacts[0];
  return {
    id: item.id,
    headline: item.headline || "",
    headline_en: item.headline || "",
    summary_en: item.summary_en || "",
    summary_tr: item.summary_tr || "",
    analysis_en: item.analysis_en || "",
    analysis_tr: item.analysis_tr || "",
    headline_locale: item.headline_locale,
    summary_locale: item.summary_locale,
    analysis_locale: item.analysis_locale,
    timestamp: item.timestamp,
    source: item.source,
    catalyst_type: "news",
    match_quality: "context",
    urgency: item.urgency,
    score: primaryImpact?.score || 0,
    direction: primaryImpact?.direction || "neutral",
    reasoning: primaryImpact?.reasoning || "",
    reasoning_tr: primaryImpact?.reasoning_tr || "",
    reasoning_locale: primaryImpact?.reasoning_locale,
    affected_symbols: item.impacts.map((impact) => impact.symbol),
    relevance_score: 0.25,
    importance_level: item.importanceLevel,
    importance_score: item.importanceScore,
    importance_reason: item.importanceReason,
    ai_model: item.aiModel,
    ai_match_confidence: item.aiConfidence ? item.aiConfidence / 100 : 0,
    url: item.url || "",
  };
}

function markerToMatchedItem(
  marker: {
    id?: string;
    headline?: string;
    headline_en?: string;
    event_name?: string;
    reasoning_tr?: string;
    source_time?: string;
    time?: string;
    catalyst_type?: "news" | "economic" | "earnings";
    urgency?: string;
    score?: number;
    direction?: string;
    event_id?: string | null;
    ai_confidence?: number;
    importance_level?: string;
    importance_score?: number;
    importance_reason?: string;
    url?: string;
  },
  selectedSymbol: string
): MatchedNewsItem {
  return {
    id: String(marker.id || ""),
    headline: marker.headline || marker.headline_en || "",
    headline_en: marker.headline_en || marker.headline || "",
    summary_en: marker.event_name || marker.headline_en || marker.headline || "",
    summary_tr: marker.headline || "",
    analysis_en: marker.reasoning_tr || "",
    analysis_tr: marker.reasoning_tr || "",
    timestamp: marker.source_time || marker.time || new Date().toISOString(),
    source: marker.catalyst_type || "marker",
    catalyst_type: marker.catalyst_type || "news",
    match_quality: "matched",
    urgency: marker.urgency || "medium",
    score: marker.score || 0,
    direction: marker.direction || "neutral",
    reasoning: marker.reasoning_tr || "",
    reasoning_tr: marker.reasoning_tr || "",
    event_id: marker.event_id || undefined,
    affected_symbols: [selectedSymbol],
    relevance_score: typeof marker.ai_confidence === "number" ? Math.max(0.3, Math.min(0.95, marker.ai_confidence / 100)) : 0.75,
    importance_level: marker.importance_level,
    importance_score: marker.importance_score,
    importance_reason: marker.importance_reason,
    ai_match_confidence: typeof marker.ai_confidence === "number" ? marker.ai_confidence / 100 : undefined,
    url: marker.url || "",
  };
}

interface AIAnnotatedEvent {
  ai_analyzed?: boolean;
  ai_model?: string | null;
  importance_level?: ImportanceLevel | null;
  importance_score?: number | null;
  importance_reason?: string | null;
  confidence?: number | null;
}

interface EconomicEvent extends AIAnnotatedEvent {
  id: string;
  timestamp: string;
  title: string;
  title_tr: string;
  currency: string;
  impact: "High" | "Medium" | "Low";
  actual?: string;
  forecast?: string;
  previous?: string;
  predicted_direction: EventDirection;
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
  minutes_until?: number;
  scenarios?: Scenarios;
  trading_tips?: string;
}

interface EarningsEvent extends AIAnnotatedEvent {
  id: string;
  company: string;
  company_tr?: string;
  ticker: string;
  sector: string;
  date: string;
  time: EarningsTime;
  eps_forecast?: string;
  revenue_forecast?: string;
  previous_eps?: string;
  previous_revenue?: string;
  affected_symbols: string[];
  analysis: string;
  analysis_tr: string;
  key_metrics: string[];
  key_metrics_tr: string[];
  timestamp: string;
  is_upcoming: boolean;
  minutes_until: number;
  predicted_direction: EventDirection;
  scenarios?: Scenarios;
  trading_tips?: string;
}

type CalendarEventDetail = Partial<EconomicEvent & EarningsEvent>;

interface WSPriceData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  timestamp: number;
}

// ==================== SYMBOLS ====================
const INITIAL_SYMBOLS: SymbolData[] = [
  { symbol: "XAUUSD", name: "Gold", price: 0, change: 0, changePercent: 0 },
  { symbol: "NDX", name: "NASDAQ", price: 0, change: 0, changePercent: 0 },
  { symbol: "DAX", name: "DAX 40", price: 0, change: 0, changePercent: 0 },
  { symbol: "USOIL", name: "WTI Crude", price: 0, change: 0, changePercent: 0 },
];

const TIMEFRAMES = [
  { value: "5m", label: "5m", limit: 1000 },
  { value: "15m", label: "15m", limit: 800 },
  { value: "30m", label: "30m", limit: 800 },
  { value: "1h", label: "1h", limit: 720 },
  { value: "4h", label: "4h", limit: 360 },
  { value: "1d", label: "1D", limit: 365 },
];

const TIMEFRAME_TO_MINUTES: Record<string, number> = {
  "5m": 5,
  "15m": 15,
  "30m": 30,
  "1h": 60,
  "4h": 240,
  "1d": 1440,
};

function getSidebarItems(locale: string) {
  const t = getT(locale);
  return [
    { icon: Bell, label: t.alerts, href: "/alerts", badge: 3 },
    { icon: Star, label: t.watchlist, href: "/watchlist", badge: null },
    { icon: Wallet, label: t.smartTrades, href: "/news-correlation", badge: null, active: true },
    { icon: Calendar, label: t.economicCalendar, href: "/calendar", badge: null },
    { icon: MessageSquare, label: t.chatAi, href: "/chat", badge: null },
    { icon: Newspaper, label: t.researchReports, href: "/research", badge: null },
    { icon: BookOpen, label: t.docs, href: "/docs", badge: null },
    { icon: Building2, label: t.brokers, href: "/brokers", badge: null },
    { icon: LineChart, label: t.myTrades, href: "/trades", badge: null },
  ];
}

const getDirectionBadgeClass = (direction?: EventDirection | null) => cn(
  "text-[10px] px-2 py-0.5 rounded-full border font-medium",
  direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
  direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
  direction === "volatile" && "bg-purple-500/10 text-purple-300 border-purple-500/20",
  (!direction || direction === "neutral") && "bg-gray-700/50 text-gray-400 border-gray-600"
);

const getDirectionArrow = (direction?: EventDirection | null) => {
  if (direction === "bullish") return "↗";
  if (direction === "bearish") return "↘";
  if (direction === "volatile") return "⚡";
  return "→";
};

const getImportanceBadgeClass = (level?: ImportanceLevel | null) => cn(
  "text-[10px] px-2 py-0.5 rounded-full border font-medium uppercase tracking-wide",
  level === "critical" && "bg-red-500/10 text-red-300 border-red-500/20",
  level === "high" && "bg-amber-500/10 text-amber-300 border-amber-500/20",
  level === "medium" && "bg-yellow-500/10 text-yellow-300 border-yellow-500/20",
  (!level || level === "low") && "bg-gray-700/50 text-gray-400 border-gray-600"
);

const formatAIModelLabel = (aiModel?: string | null) =>
  aiModel?.replace(/[_-]/g, " ") || "DeepSeek";

const ImpactChip = ({ impact }: { impact: { symbol: string; direction?: EventDirection | null; magnitude?: string } }) => (
  <span className={cn(
    "inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border",
    impact.direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
    impact.direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
    impact.direction === "volatile" && "bg-purple-500/10 text-purple-300 border-purple-500/20",
    (!impact.direction || impact.direction === "neutral") && "bg-gray-700/50 text-gray-400 border-gray-600"
  )}>
    {getDirectionArrow(impact.direction)}
    {impact.symbol}
    {impact.magnitude ? ` ${impact.magnitude}` : ""}
  </span>
);

const EventAIMetadata = ({ event, compact = false, locale = "en" }: { event: AIAnnotatedEvent; compact?: boolean; locale?: string }) => {
  const hasImportance = !!event.importance_level || typeof event.importance_score === "number";
  const t = getT(locale);

  return (
    <div className={cn("space-y-2", compact && "mt-3")}>
      <div className="flex flex-wrap gap-2">
        {hasImportance && (
          <span className={getImportanceBadgeClass(event.importance_level)}>
            {formatImportanceLabel(event.importance_level, locale)} {t.importance}
            {typeof event.importance_score === "number" ? ` • ${event.importance_score}/100` : ""}
          </span>
        )}
        <span className={cn(
          "text-[10px] px-2 py-0.5 rounded-full border font-medium",
          event.ai_analyzed
            ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/20"
            : "bg-gray-700/50 text-gray-400 border-gray-600"
        )}>
          {event.ai_analyzed ? `${formatAIModelLabel(event.ai_model)} AI` : t.fallbackAnalysis}
        </span>
        {typeof event.confidence === "number" && (
          <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium bg-blue-500/10 text-blue-300 border-blue-500/20">
            {t.confidence} • {Math.round(normalizeDisplayConfidence(event.confidence))}%
          </span>
        )}
      </div>
      {event.importance_reason && (
        <p className={cn(
          "text-gray-500 leading-relaxed",
          compact ? "text-[11px] line-clamp-2" : "text-xs"
        )}>
          {event.importance_reason}
        </p>
      )}
    </div>
  );
};

// ==================== COMPONENTS ====================
const SidebarItem = ({ icon: Icon, label, href, active = false, badge, collapsed }: any) => (
  <Link href={href} className={cn(
    "flex items-center gap-3 px-4 py-3 text-sm transition-all relative",
    active ? "text-white bg-gradient-to-r from-purple-500/10 to-transparent border-l-2 border-purple-500" : "text-gray-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent"
  )}>
    <Icon className={cn("w-5 h-5 flex-shrink-0", active && "text-purple-400")} />
    {!collapsed && <span className="truncate">{label}</span>}
    {!collapsed && badge && <span className="ml-auto bg-red-500 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">{badge}</span>}
    {collapsed && badge && <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full" />}
  </Link>
);

const TimeAgo = ({ timestamp, locale }: { timestamp: string; locale: string }) => {
  const [timeAgo, setTimeAgo] = useState<string>("");

  useEffect(() => {
    const update = () => {
      const t = getT(locale);
      const date = new Date(timestamp);
      const now = new Date();
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (diffInSeconds < 60) setTimeAgo(`${diffInSeconds}${t.secondsAgoSuffix}`);
      else if (diffInSeconds < 3600) setTimeAgo(`${Math.floor(diffInSeconds / 60)}${t.minutesAgoSuffix}`);
      else if (diffInSeconds < 86400) setTimeAgo(`${Math.floor(diffInSeconds / 3600)}${t.hoursAgoSuffix}`);
      else setTimeAgo(`${Math.floor(diffInSeconds / 86400)}${t.daysAgoSuffix}`);
    };

    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [timestamp, locale]);

  return <span className="text-xs text-gray-500">{timeAgo || getT(locale).unknownTime}</span>;
};

const NewsCard = ({ news, onClick, locale }: { news: EnrichedNews, onClick: () => void, locale: string }) => {
  const isHighImpact = news.urgency === "breaking" || news.urgency === "high";

  const displayHeadline = getLocalizedHeadline(news, locale);
  const displayContent = getLocalizedSummary(news, locale) || getLocalizedAnalysis(news, locale);

  return (
    <div
      onClick={onClick}
      className={cn(
        "group relative p-4 rounded-xl border transition-all cursor-pointer",
        isHighImpact
          ? "bg-gradient-to-r from-red-950/30 to-transparent border-red-900/30 hover:border-red-700/50"
          : "bg-gray-900/30 border-gray-800 hover:border-gray-700"
      )}
    >
      <div className="flex items-center gap-3 mb-3">
        <span className={cn(
          "px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase",
          news.urgency === "breaking" && "bg-red-500 text-white",
          news.urgency === "high" && "bg-red-500/20 text-red-400 border border-red-500/30",
          news.urgency === "medium" && "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
          news.urgency === "low" && "bg-gray-700 text-gray-400"
        )}>
          {news.urgency === "breaking" ? getT(locale).breaking : `${formatUrgencyLabel(news.urgency, locale).toUpperCase()} ${getT(locale).impactSuffix}`}
        </span>
        <span className="text-xs text-gray-500 font-mono">
          {format(new Date(news.timestamp), "HH:mm")}
        </span>
        <span className="text-xs text-gray-600">•</span>
        <TimeAgo timestamp={news.timestamp} locale={locale} />
      </div>

      <h3 className="text-sm font-semibold text-white leading-snug mb-2 uppercase tracking-wide line-clamp-2">
        {displayHeadline}
      </h3>

      <p className="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-2">
        {displayContent}
      </p>

      <div className="flex flex-wrap gap-1.5">
        {news.impacts?.slice(0, 6).map((impact, idx) => (
          <ImpactChip key={idx} impact={impact} />
        ))}
      </div>
    </div>
  );
};

// ==================== MAIN COMPONENT ====================
interface NewsCorrelationDashboardProps {
  embedded?: boolean;
}

export default function NewsCorrelationDashboard({ embedded = false }: NewsCorrelationDashboardProps) {
  const router = useRouter();
  const [selectedSymbol, setSelectedSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [symbols, setSymbols] = useState<SymbolData[]>(INITIAL_SYMBOLS);
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsStatus, setNewsStatus] = useState<"idle" | "api" | "empty" | "mock" | "error">("idle");
  const [newsStatusMessage, setNewsStatusMessage] = useState<string | null>(null);
  const [newsLastUpdatedAt, setNewsLastUpdatedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newsFilter, setNewsFilter] = useState<"all" | "popular" | "high">("all");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedCandleNews, setSelectedCandleNews] = useState<CandleNews | null>(null);
  const [selectedNewsForModal, setSelectedNewsForModal] = useState<EnrichedNews | null>(null);
  const [isNewsModalOpen, setIsNewsModalOpen] = useState(false);
  const [currentLocale, setCurrentLocale] = useState("tr");
  const [mounted, setMounted] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // AI Explanation states
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  // Calendar tab states
  const [activeTab, setActiveTab] = useState<"news" | "economic" | "earnings">("news");
  const [economicEvents, setEconomicEvents] = useState<EconomicEvent[]>([]);
  const [earningsEvents, setEarningsEvents] = useState<EarningsEvent[]>([]);
  const [economicLoading, setEconomicLoading] = useState(false);
  const [earningsLoading, setEarningsLoading] = useState(false);

  // Selected event modals
  const [selectedEconomicEvent, setSelectedEconomicEvent] = useState<EconomicEvent | null>(null);
  const [selectedEarningsEvent, setSelectedEarningsEvent] = useState<EarningsEvent | null>(null);
  const markerLookbackHours = getMarkerLookbackHours(timeframe);
  const markerLimit = timeframe === "1d" ? 120 : timeframe === "4h" ? 90 : timeframe === "1h" ? 72 : 60;
  const { markers: newsMarkers, error: newsMarkersError } = useNewsMarkers(selectedSymbol, markerLookbackHours, 5, markerLimit);
  const mappedChartMarkers = useMemo(() => buildMappedChartMarkers(newsMarkers, chartData), [newsMarkers, chartData]);
  const [isEconomicModalOpen, setIsEconomicModalOpen] = useState(false);
  const [isEarningsModalOpen, setIsEarningsModalOpen] = useState(false);
  const [loadingEventDetail, setLoadingEventDetail] = useState(false);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const chartDataRef = useRef<ChartCandle[]>([]);
  const newsRef = useRef<EnrichedNews[]>([]);
  const mappedMarkersRef = useRef<any[]>([]);
  const selectedSymbolRef = useRef(selectedSymbol);
  const timeframeRef = useRef(timeframe);
  const currentLocaleRef = useRef(currentLocale);
  const chartRequestIdRef = useRef(0);
  const lastAutoFitKeyRef = useRef("");
  const economicDetailLocaleRef = useRef<string | null>(null);
  const earningsDetailLocaleRef = useRef<string | null>(null);
  const fetchAIExplanationRef = useRef<(candle: ChartCandle) => Promise<void> | void>(() => undefined);

  // Mount effect
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!embedded) {
      router.replace("/");
    }
  }, [embedded, router]);

  useEffect(() => {
    chartDataRef.current = chartData;
  }, [chartData]);

  useEffect(() => {
    newsRef.current = news;
  }, [news]);

  useEffect(() => {
    selectedSymbolRef.current = selectedSymbol;
  }, [selectedSymbol]);

  useEffect(() => {
    timeframeRef.current = timeframe;
  }, [timeframe]);

  useEffect(() => {
    currentLocaleRef.current = currentLocale;
  }, [currentLocale]);

  useEffect(() => {
    setSelectedCandleNews(null);
    setAiExplanation(null);
  }, [selectedSymbol, timeframe, currentLocale]);

  // Fetch chart data
  const fetchChartData = useCallback(async () => {
    const requestId = ++chartRequestIdRef.current;
    const requestedSymbol = selectedSymbol;
    const requestedTimeframe = timeframe;

    try {
      setLoading(true);
      setError(null);

      const symbolMap: Record<string, string> = {
        XAUUSD: "XAUUSD",
        NDX: "NDX.INDX",
        DAX: "GDAXI.INDX",
        USOIL: "USOIL.FOREX",
        VIX: "VIX.INDX",
        DXY: "DXY.INDX",
      };
      const apiSymbol = symbolMap[requestedSymbol] || requestedSymbol;

      const tfConfig = TIMEFRAMES.find(t => t.value === requestedTimeframe);
      const fetchLimit = tfConfig?.limit ?? 720;

      const response = await fetcher<OHLCVResponse>(
        `/api/data/ohlcv?symbol=${apiSymbol}&timeframe=${requestedTimeframe}&limit=${fetchLimit}`
      );

      const isStaleRequest =
        requestId !== chartRequestIdRef.current
        || requestedSymbol !== selectedSymbolRef.current
        || requestedTimeframe !== timeframeRef.current;

      if (isStaleRequest) {
        return;
      }

      if (response?.data && Array.isArray(response.data) && response.data.length > 0) {
        const normalizedCandles = normalizeCandles(response.data, requestedTimeframe);
        const processedCandles: ChartCandle[] = buildActualTimeChartCandles(normalizedCandles, requestedTimeframe) as unknown as ChartCandle[];

        console.log(`[Chart] Loaded ${processedCandles.length} candles for ${requestedSymbol}`);
        setChartData(processedCandles);
      } else {
        setError("No chart data available");
        setChartData([]);
      }
    } catch (err) {
      console.error("Error fetching chart:", err);
      setError("Failed to load chart data");
      setChartData([]);
    } finally {
      if (requestId === chartRequestIdRef.current) {
        setLoading(false);
      }
    }
  }, [selectedSymbol, timeframe]);

  // Mock news for testing when API returns empty
  const getMockNews = useCallback((): EnrichedNews[] => {
    const now = new Date();
    return [
      {
        id: "mock-1",
        timestamp: new Date(now.getTime() - 30 * 60000).toISOString(),
        source: "Reuters",
        headline: "Gold prices surge as Fed signals potential rate cuts",
        content: "Gold prices jumped 1.5% after Federal Reserve Chair Jerome Powell hinted at possible interest rate cuts in the coming months. The precious metal is trading at $2,450, approaching key resistance levels.",
        category: "markets",
        url: "#",
        impacts: [
          { symbol: "XAUUSD", direction: "bullish", score: 8, confidence: 0.85, reasoning: "Rate cuts typically weaken USD and boost gold", emoji: "🟡" },
          { symbol: "DXY", direction: "bearish", score: 7, confidence: 0.80, reasoning: "Fed dovish stance weakens dollar", emoji: "💵" }
        ],
        sentiment: "risk_on",
        volatilityExpectation: "high",
        urgency: "high",
        eventDuration: "short_term",
        affectedCandles: [],
        aiConfidence: 85,
        analysisTimestamp: now.toISOString()
      },
      {
        id: "mock-2",
        timestamp: new Date(now.getTime() - 2 * 60 * 60000).toISOString(),
        source: "Bloomberg",
        headline: "Oil prices climb on Middle East tensions",
        content: "Crude oil prices rose 2% amid escalating geopolitical tensions in the Middle East. Supply concerns are driving WTI above $85 per barrel.",
        category: "commodities",
        url: "#",
        impacts: [
          { symbol: "USOIL", direction: "bullish", score: 9, confidence: 0.92, reasoning: "Supply disruption fears drive oil prices", emoji: "🛢️" },
          { symbol: "XAUUSD", direction: "bullish", score: 6, confidence: 0.70, reasoning: "Geopolitical risk increases safe haven demand", emoji: "🟡" }
        ],
        sentiment: "risk_off",
        volatilityExpectation: "high",
        urgency: "breaking",
        eventDuration: "long_term",
        affectedCandles: [],
        aiConfidence: 92,
        analysisTimestamp: now.toISOString()
      },
      {
        id: "mock-3",
        timestamp: new Date(now.getTime() - 4 * 60 * 60000).toISOString(),
        source: "CNBC",
        headline: "NASDAQ reaches new highs on tech earnings",
        content: "Technology stocks led the NASDAQ to record levels as major companies reported better-than-expected quarterly results. AI-related stocks showing strong momentum.",
        category: "markets",
        url: "#",
        impacts: [
          { symbol: "NDX", direction: "bullish", score: 8, confidence: 0.78, reasoning: "Strong tech earnings drive index higher", emoji: "📈" },
          { symbol: "VIX", direction: "bearish", score: 7, confidence: 0.75, reasoning: "Positive sentiment reduces volatility", emoji: "📉" }
        ],
        sentiment: "risk_on",
        volatilityExpectation: "medium",
        urgency: "high",
        eventDuration: "short_term",
        affectedCandles: [],
        aiConfidence: 78,
        analysisTimestamp: now.toISOString()
      },
      {
        id: "mock-4",
        timestamp: new Date(now.getTime() - 6 * 60 * 60000).toISOString(),
        source: "ForexLive",
        headline: "DAX falls on German manufacturing data disappointment",
        content: "German DAX index declined 0.8% after PMI data showed manufacturing sector contraction continuing. ECB policy expectations shifting.",
        category: "markets",
        url: "#",
        impacts: [
          { symbol: "DAX", direction: "bearish", score: 7, confidence: 0.72, reasoning: "Weak manufacturing data hurts German equities", emoji: "🇩🇪" },
          { symbol: "EURUSD", direction: "bearish", score: 6, confidence: 0.68, reasoning: "Economic weakness pressures Euro", emoji: "💶" }
        ],
        sentiment: "risk_off",
        volatilityExpectation: "medium",
        urgency: "medium",
        eventDuration: "short_term",
        affectedCandles: [],
        aiConfidence: 72,
        analysisTimestamp: now.toISOString()
      }
    ];
  }, []);

  // Fetch news
  const fetchNews = useCallback(async (useMock = false) => {
    try {
      setNewsLoading(true);

      // Use mock data only when explicitly requested
      if (useMock) {
        console.log("[News] Using mock data for testing");
        setNews(sortNewsByTimestamp(getMockNews()));
        setNewsStatus("mock");
        setNewsStatusMessage("Showing manual test news data.");
        setNewsLastUpdatedAt(new Date());
        setNewsLoading(false);
        return;
      }

      // Try multiple strategies to fetch news
      let newsData: any[] = [];

      // Strategy 1: Fetch all news (no symbol filter for maximum results)
      try {
        const response = await fetcher<any[] | { success: boolean; data: any[] }>(
          `/api/rss/news?limit=100&hours=72&skip_ai_filtered=false&lang=${encodeURIComponent(currentLocale)}`
        );

        if (Array.isArray(response)) {
          newsData = response;
        } else if (response && typeof response === 'object' && 'data' in response) {
          newsData = response.data;
        }
      } catch (e) {
        console.log("Primary news fetch failed, trying fallback...");
      }

      // Strategy 2: If no news, try with longer time window
      if (newsData.length === 0) {
        try {
          const response = await fetcher<any[] | { success: boolean; data: any[] }>(
            `/api/rss/news?limit=100&hours=168&skip_ai_filtered=false&lang=${encodeURIComponent(currentLocale)}`
          );

          if (Array.isArray(response)) {
            newsData = response;
          } else if (response && typeof response === 'object' && 'data' in response) {
            newsData = response.data;
          }
        } catch (e) {
          console.log("Fallback news fetch also failed");
        }
      }

      if (newsData.length === 0) {
        console.log("[News] API returned no news for the current selection");
        setNews([]);
        setNewsStatus("empty");
        setNewsStatusMessage("No API news returned for the selected symbol/time window.");
        setNewsLastUpdatedAt(null);
        return;
      }

      const normalizedNews = newsData.map((item) => normalizeNewsItem(item));

      // Filter news for selected symbol if we have news
      if (normalizedNews.length > 0 && selectedSymbol) {
        const filtered = normalizedNews.filter((item: EnrichedNews) => {
          if (item.impacts && item.impacts.length > 0) {
            return item.impacts.some((impact: any) =>
              matchesSelectedSymbol(impact.symbol, selectedSymbol)
            );
          }
          return true;
        });

        setNews(sortNewsByTimestamp(filtered.length > 0 ? filtered : normalizedNews));
      } else {
        setNews(sortNewsByTimestamp(normalizedNews));
      }

      setNewsStatus("api");
      setNewsStatusMessage(null);
      setNewsLastUpdatedAt(new Date());
    } catch (err) {
      console.error("Error fetching news:", err);
      setNews([]);
      setNewsStatus("error");
      setNewsStatusMessage(err instanceof Error ? err.message : "Unable to load news feed.");
      setNewsLastUpdatedAt(null);
    } finally {
      setNewsLoading(false);
    }
  }, [selectedSymbol, getMockNews, currentLocale]);

  // Fetch economic calendar
  const fetchEconomicCalendar = useCallback(async () => {
    try {
      setEconomicLoading(true);
      const response = await fetcher<{ success: boolean; events: EconomicEvent[] }>(
        `/api/calendar/economic?days=14&lang=${encodeURIComponent(currentLocale)}`
      );
      if (response.success) {
        setEconomicEvents(response.events);
      }
    } catch (err) {
      console.error("Error fetching economic calendar:", err);
      setEconomicEvents([]);
    } finally {
      setEconomicLoading(false);
    }
  }, [currentLocale]);

  // Fetch earnings calendar
  const fetchEarningsCalendar = useCallback(async () => {
    try {
      setEarningsLoading(true);
      const response = await fetcher<{ success: boolean; earnings: EarningsEvent[] }>(
        `/api/calendar/earnings?days=14&lang=${encodeURIComponent(currentLocale)}`
      );
      if (response.success) {
        setEarningsEvents(response.earnings);
      }
    } catch (err) {
      console.error("Error fetching earnings calendar:", err);
      setEarningsEvents([]);
    } finally {
      setEarningsLoading(false);
    }
  }, [currentLocale]);

  // Fetch live prices via REST API
  const fetchLivePrices = useCallback(async () => {
    try {
      const response = await fetcher<{
        success: boolean;
        data: {
          [key: string]: {
            price: number;
            change: number;
            changePercent: number;
            available: boolean;
          }
        }
      }>(`/api/prices`);

      if (response?.success && response.data) {
        setSymbols(prev => prev.map(sym => {
          const data = response.data[sym.symbol];
          if (data && data.available) {
            return {
              ...sym,
              price: data.price,
              change: data.change,
              changePercent: data.changePercent,
            };
          }

          return sym;
        }));
      }
    } catch (err) {
      console.error("[Prices] REST fetch failed:", err);
    }
  }, []);

  // WebSocket connection for live prices
  useEffect(() => {
    if (!mounted) return;

    // First fetch via REST
    fetchLivePrices();

    const connectWebSocket = () => {
      try {
        const wsUrl = buildWebSocketUrl("/ws/all");
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log("[WS] Connected");
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "price_update" && data.payload) {
              const payload: WSPriceData = data.payload;

              setSymbols(prev => prev.map(sym => {
                const backendToFrontend: Record<string, string> = {
                  "XAUUSD": "XAUUSD",
                  "NDX.INDX": "NDX",
                  "GDAXI.INDX": "DAX",
                  "USOIL.FOREX": "USOIL",
                  "VIX.INDX": "VIX",
                  "DXY.INDX": "DXY",
                };

                if (backendToFrontend[payload.symbol] === sym.symbol) {
                  return {
                    ...sym,
                    price: payload.price,
                    change: payload.change,
                    changePercent: payload.changePercent,
                  };
                }
                return sym;
              }));
            }
          } catch (e) {
            console.error("[WS] Parse error:", e);
          }
        };

        ws.onclose = () => {
          console.log("[WS] Disconnected");
          setWsConnected(false);
          setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = (err) => {
          console.error("[WS] Error:", err);
          ws.close();
        };

        wsRef.current = ws;
      } catch (err) {
        console.error("[WS] Connection failed:", err);
      }
    };

    connectWebSocket();

    // Periodic REST fallback every 10 seconds
    const interval = setInterval(fetchLivePrices, 10000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [mounted, fetchLivePrices]);

  // Initial data fetch
  useEffect(() => {
    if (mounted) {
      fetchChartData();
      fetchNews();
    }
  }, [fetchChartData, fetchNews, mounted]);

  // Fetch AI explanation for price move
  const fetchAIExplanation = useCallback(async (candle: ChartCandle) => {
    try {
      setLoadingExplanation(true);
      const symbolMap: Record<string, string> = {
        XAUUSD: "XAUUSD",
        NDX: "NDX.INDX",
        DAX: "GDAXI.INDX",
        USOIL: "USOIL.FOREX",
        VIX: "VIX.INDX",
        DXY: "DXY.INDX",
      };
      const apiSymbol = symbolMap[selectedSymbol] || selectedSymbol;

      const response = await fetcher<{
        success: boolean;
        data?: {
          explanation?: string | null;
          ai_explanation?: string | null;
          related_news: any[];
          confidence: number;
        };
        error?: string;
      }>(`/api/news-correlation/explain-move?symbol=${apiSymbol}&timestamp=${candle.actualTimestamp}&timeframe=${encodeURIComponent(timeframe)}&ai_explain=true&lang=${encodeURIComponent(currentLocale)}`);

      if (response?.success && response.data) {
        setAiExplanation(response.data.explanation || response.data.ai_explanation || null);
      } else {
        setAiExplanation(null);
      }
    } catch (err) {
      console.error("Error fetching AI explanation:", err);
      setAiExplanation(null);
    } finally {
      setLoadingExplanation(false);
    }
  }, [selectedSymbol, timeframe, currentLocale]);

  useEffect(() => {
    fetchAIExplanationRef.current = fetchAIExplanation;
  }, [fetchAIExplanation]);

  const handleChartCandleSelect = useCallback((selectedTimestampSeconds: number) => {
    if (!Number.isFinite(selectedTimestampSeconds) || chartDataRef.current.length === 0) {
      return;
    }

    const currentTimeframe = timeframeRef.current;
    const timeframeSeconds = (TIMEFRAME_TO_MINUTES[currentTimeframe] || 60) * 60;
    const candle = chartDataRef.current.reduce<ChartCandle | null>((closest, candidate) => {
      if (!closest) {
        return candidate;
      }
      return Math.abs(candidate.actualTimestamp - selectedTimestampSeconds) < Math.abs(closest.actualTimestamp - selectedTimestampSeconds)
        ? candidate
        : closest;
    }, null);

    if (!candle || Math.abs(candle.actualTimestamp - selectedTimestampSeconds) > Math.max(60, Math.floor(timeframeSeconds / 2))) {
      return;
    }

    const priceChange = ((candle.close - candle.open) / candle.open) * 100;
    setSelectedCandleNews({
      candle,
      news: [],
      hasBigMove: Math.abs(priceChange) > 1.5,
      moveType: priceChange > 0 ? "up" : priceChange < 0 ? "down" : "none",
      movePercent: priceChange,
      isLoadingNews: true,
    });

    if (Math.abs(priceChange) > 1.0) {
      fetchAIExplanationRef.current(candle);
    } else {
      setAiExplanation(null);
    }

    const currentSymbol = selectedSymbolRef.current;
    const buildNearbyNewsFallback = () => {
      const minutes = TIMEFRAME_TO_MINUTES[currentTimeframe] || 60;
      const candleStart = subMinutes(new Date(candle.actualTimestamp * 1000), minutes / 2);
      const candleEnd = addMinutes(new Date(candle.actualTimestamp * 1000), minutes / 2);

      return newsRef.current.filter((item) => {
        const newsTime = new Date(item.timestamp);
        return isWithinInterval(newsTime, { start: candleStart, end: candleEnd });
      }).slice(0, 5).map((item) => toFallbackMatchedItem(item, currentSymbol));
    };

    const buildMarkerFallback = () => {
      return mappedMarkersRef.current
        .filter((marker) => String(marker.time) === String(candle.time))
        .map((marker) => markerToMatchedItem(marker, currentSymbol));
    };

    const mergeMatchedItems = (...lists: MatchedNewsItem[][]) => {
      const merged: MatchedNewsItem[] = [];
      const seen = new Set<string>();

      for (const list of lists) {
        for (const item of list) {
          const key = `${item.catalyst_type || "news"}:${item.event_id || item.id}:${item.timestamp}`;
          if (seen.has(key)) {
            continue;
          }
          seen.add(key);
          merged.push(item);
        }
      }

      return merged;
    };

    fetchNewsForCandle(
      currentSymbol,
      new Date(candle.actualTimestamp * 1000).toISOString(),
      candle.open,
      candle.close,
      candle.high,
      candle.low,
      currentTimeframe,
      currentLocaleRef.current
    ).then((response) => {
      const matchedNews = Array.isArray(response.news) ? response.news : [];
      const fallbackNews = mergeMatchedItems(
        matchedNews,
        buildMarkerFallback(),
        matchedNews.length === 0 ? buildNearbyNewsFallback() : []
      );
      setSelectedCandleNews((prev) => prev ? {
        ...prev,
        news: fallbackNews,
        isLoadingNews: false,
      } : null);
    }).catch((error) => {
      console.error("[CandleClick] Error fetching matched news:", error);
      setSelectedCandleNews((prev) => prev ? {
        ...prev,
        news: mergeMatchedItems(buildMarkerFallback(), buildNearbyNewsFallback()),
        isLoadingNews: false,
      } : null);
    });
  }, []);

  useEffect(() => {
    if (!chartContainerRef.current || !mounted || chartRef.current) return;

    const container = chartContainerRef.current;
    const formatActualChartDisplayTime = (time: Time, includeYear = false) => {
      const candle = findTimelineChartCandle(time as number | string, chartDataRef.current);
      const timestamp = candle?.actualTimestamp ?? chartTimeToTimestampSeconds(time as number | string);

      if (!Number.isFinite(timestamp)) {
        return "";
      }

      return format(
        new Date(Number(timestamp) * 1000),
        timeframeRef.current === "1d"
          ? (includeYear ? "MMM d, yyyy" : "MMM d")
          : (includeYear ? "MMM d, yyyy HH:mm" : "MMM d, HH:mm")
      );
    };

    const formatCompressedAxisTime = (time: Time) => {
      const candle = findTimelineChartCandle(time as number | string, chartDataRef.current);
      const realTimestamp = candle?.actualTimestamp ?? chartTimeToTimestampSeconds(time as number | string);

      if (!Number.isFinite(realTimestamp)) {
        return "";
      }

      return format(
        new Date(Number(realTimestamp) * 1000),
        timeframeRef.current === "1d" ? "MMM d" : "MMM d, HH:mm"
      );
    };

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 420,
      layout: {
        background: { color: "#0a0a0a" },
        textColor: "#6b7280",
        fontFamily: "Inter, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.03)" },
        horzLines: { color: "rgba(255, 255, 255, 0.03)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "rgba(255, 255, 255, 0.1)", labelBackgroundColor: "#374151" },
        horzLine: { color: "rgba(255, 255, 255, 0.1)", labelBackgroundColor: "#374151" },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      localization: {
        timeFormatter: (time: Time) => formatActualChartDisplayTime(time, true),
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        timeVisible: true,
        secondsVisible: false,
        fixLeftEdge: false,
        fixRightEdge: false,
        rightOffset: 2,
        barSpacing: 8,
        minBarSpacing: 3,
        tickMarkFormatter: (time: Time) => formatCompressedAxisTime(time),
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const handleChartClick = (param: { time?: Time }) => {
      if (!param.time) {
        return;
      }

      const candle = findTimelineChartCandle(param.time as number | string, chartDataRef.current);
      if (candle) {
        handleChartCandleSelect(candle.actualTimestamp);
      }
    };

    chart.subscribeClick(handleChartClick);

    candlestickSeriesRef.current = candlestickSeries;
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      if (chartRef.current) {
        chartRef.current.applyOptions({ width: container.clientWidth, height: container.clientHeight || 420 });
      }
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.unsubscribeClick(handleChartClick);
      candlestickSeriesRef.current = null;
      chartRef.current = null;
      chart.remove();
    };
  }, [handleChartCandleSelect, mounted]);

  useEffect(() => {
    if (!candlestickSeriesRef.current || !chartRef.current) {
      return;
    }

    if (chartData.length === 0) {
      candlestickSeriesRef.current.setData([]);
      lastAutoFitKeyRef.current = "";
      return;
    }

    const formattedData = buildRenderableChartSeries(chartData, timeframe, selectedSymbol).map((point) => ({
      time: point.time as Time,
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
    }));
    candlestickSeriesRef.current.setData(formattedData as CandlestickData<Time>[]);

    const firstCandleTime = chartData[0]?.time ?? 0;
    const lastCandleTime = chartData[chartData.length - 1]?.time ?? 0;
    const fitKey = `${selectedSymbol}:${timeframe}:${chartData.length}:${firstCandleTime}:${lastCandleTime}`;
    if (lastAutoFitKeyRef.current !== fitKey) {
      chartRef.current.timeScale().fitContent();
      lastAutoFitKeyRef.current = fitKey;
    }
  }, [chartData, selectedSymbol, timeframe]);

  useEffect(() => {
    if (!candlestickSeriesRef.current) {
      return;
    }

    if (chartData.length === 0) {
      candlestickSeriesRef.current.setMarkers([] as any);
      mappedMarkersRef.current = [];
      return;
    }

    mappedMarkersRef.current = mappedChartMarkers;
    candlestickSeriesRef.current.setMarkers(mappedChartMarkers as any);
  }, [chartData, mappedChartMarkers]);

  const openEconomicEvent = useCallback(async (event: EconomicEvent) => {
    setSelectedEconomicEvent(event);
    setIsEconomicModalOpen(true);
    setLoadingEventDetail(true);
    economicDetailLocaleRef.current = currentLocale;

    try {
      const detailRes = await fetcher<{ success: boolean; event: CalendarEventDetail }>(
        `/api/calendar/event/${event.id}?lang=${encodeURIComponent(currentLocale)}`
      );

      if (detailRes.success && detailRes.event) {
        setSelectedEconomicEvent((prev) => prev ? {
          ...prev,
          ...detailRes.event,
          scenarios: detailRes.event.scenarios ?? prev.scenarios,
          trading_tips: detailRes.event.trading_tips ?? prev.trading_tips,
        } : prev);
      }
    } catch (err) {
      console.error("Error fetching economic detail:", err);
    } finally {
      setLoadingEventDetail(false);
    }
  }, [currentLocale]);

  const openEarningsEvent = useCallback(async (event: EarningsEvent) => {
    setSelectedEarningsEvent(event);
    setIsEarningsModalOpen(true);
    setLoadingEventDetail(true);
    earningsDetailLocaleRef.current = currentLocale;

    try {
      const detailRes = await fetcher<{ success: boolean; event: CalendarEventDetail }>(
        `/api/calendar/event/${event.id}?lang=${encodeURIComponent(currentLocale)}`
      );

      if (detailRes.success && detailRes.event) {
        setSelectedEarningsEvent((prev) => prev ? {
          ...prev,
          ...detailRes.event,
          scenarios: detailRes.event.scenarios ?? prev.scenarios,
          trading_tips: detailRes.event.trading_tips ?? prev.trading_tips,
        } : prev);
      }
    } catch (err) {
      console.error("Error fetching earnings detail:", err);
    } finally {
      setLoadingEventDetail(false);
    }
  }, [currentLocale]);

  const handleNewsClick = (newsItem: EnrichedNews | MatchedNewsItem) => {
    if (isMatchedNewsItem(newsItem) && newsItem.catalyst_type === "economic") {
      const matchedEvent = economicEvents.find((event) => event.id === newsItem.event_id || event.id === newsItem.id);
      if (matchedEvent || newsItem.event_id) {
        void openEconomicEvent(matchedEvent || {
          id: newsItem.event_id || newsItem.id,
          timestamp: newsItem.timestamp,
          title: newsItem.headline_en || newsItem.headline,
          title_tr: newsItem.headline,
          impact: newsItem.urgency === "breaking" ? "High" : newsItem.urgency === "high" ? "Medium" : "Low",
          currency: "GLOBAL",
          predicted_direction: normalizeImpactDirection(newsItem.direction),
          affected_symbols: newsItem.affected_symbols || [selectedSymbol],
        } as EconomicEvent);
        return;
      }
    }

    if (isMatchedNewsItem(newsItem) && newsItem.catalyst_type === "earnings") {
      const matchedEvent = earningsEvents.find((event) => event.id === newsItem.event_id || event.id === newsItem.id);
      if (matchedEvent || newsItem.event_id) {
        void openEarningsEvent(matchedEvent || {
          id: newsItem.event_id || newsItem.id,
          timestamp: newsItem.timestamp,
          ticker: selectedSymbol,
          company: newsItem.headline_en || newsItem.headline,
          time: "after_market",
          predicted_direction: normalizeImpactDirection(newsItem.direction),
          affected_symbols: newsItem.affected_symbols || [selectedSymbol],
        } as EarningsEvent);
        return;
      }
    }

    const enrichedItem: EnrichedNews = isMatchedNewsItem(newsItem)
      ? news.find((item) => item.id === newsItem.id) || {
          id: newsItem.id || '',
          timestamp: newsItem.timestamp || new Date().toISOString(),
          source: newsItem.source || 'news',
          // Semantic boundaries: each field stays in its own lane.
          // headline → headline_en → "" (NEVER summary or analysis)
          headline: newsItem.headline_en || newsItem.headline || '',
          headline_tr: '',
          content: '',
          content_tr: '',
          summary_en: newsItem.summary_en || '',
          summary_tr: newsItem.summary_tr || '',
          analysis_en: newsItem.analysis_en || '',
          analysis_tr: newsItem.analysis_tr || '',
          category: 'matched_news',
          url: newsItem.url || '',
          impacts: [{
            symbol: selectedSymbol,
            direction: normalizeImpactDirection(newsItem.direction),
            score: newsItem.score || 0,
            confidence: newsItem.ai_match_confidence ?? newsItem.relevance_score ?? 0,
            reasoning: newsItem.reasoning || newsItem.reasoning_tr || '',
            reasoning_tr: newsItem.reasoning_tr || '',
            reasoning_locale: newsItem.reasoning_locale || undefined,
            emoji: '📰',
          }],
          sentiment: 'neutral',
          volatilityExpectation: 'medium',
          urgency: normalizeUrgency(newsItem.urgency),
          eventDuration: 'short_term',
          affectedCandles: [],
          aiConfidence: Math.round((newsItem.ai_match_confidence ?? newsItem.relevance_score ?? 0) * 100),
          analysisTimestamp: newsItem.timestamp || new Date().toISOString(),
        }
      : newsItem;

    setSelectedNewsForModal(enrichedItem);
    setIsNewsModalOpen(true);
  };

  // Fetch calendar data when tabs change
  useEffect(() => {
    if (activeTab === "economic" && economicEvents.length === 0) {
      fetchEconomicCalendar();
    }
  }, [activeTab, economicEvents.length, fetchEconomicCalendar]);

  useEffect(() => {
    if (activeTab === "earnings" && earningsEvents.length === 0) {
      fetchEarningsCalendar();
    }
  }, [activeTab, earningsEvents.length, fetchEarningsCalendar]);

  useEffect(() => {
    if (activeTab === "economic" && economicEvents.length > 0) {
      fetchEconomicCalendar();
    }
    if (activeTab === "earnings" && earningsEvents.length > 0) {
      fetchEarningsCalendar();
    }
  }, [activeTab, currentLocale, economicEvents.length, earningsEvents.length, fetchEconomicCalendar, fetchEarningsCalendar]);

  useEffect(() => {
    if (
      isEconomicModalOpen &&
      selectedEconomicEvent &&
      economicDetailLocaleRef.current !== currentLocale
    ) {
      void openEconomicEvent(selectedEconomicEvent);
    }
  }, [currentLocale, isEconomicModalOpen, openEconomicEvent, selectedEconomicEvent?.id]);

  useEffect(() => {
    if (
      isEarningsModalOpen &&
      selectedEarningsEvent &&
      earningsDetailLocaleRef.current !== currentLocale
    ) {
      void openEarningsEvent(selectedEarningsEvent);
    }
  }, [currentLocale, isEarningsModalOpen, openEarningsEvent, selectedEarningsEvent?.id]);

  const filteredNews = news.filter((n) => {
    if (newsFilter === "all") return true;
    if (newsFilter === "high") return n.urgency === "breaking" || n.urgency === "high";
    if (newsFilter === "popular") return n.aiConfidence >= 70 || n.urgency === "breaking" || n.urgency === "high";
    return true;
  });
  const hasHiddenNewsByFilter = news.length > 0 && filteredNews.length === 0;
  const newsFeedIsFresh = newsStatus === "api"
    && !!newsLastUpdatedAt
    && Date.now() - newsLastUpdatedAt.getTime() <= 15 * 60 * 1000;

  const currentSymbol = symbols.find(s => s.symbol === selectedSymbol);
  const sidebarItems = getSidebarItems(currentLocale);
  const groupedSelectedCatalysts = selectedCandleNews ? groupCatalystsByType(selectedCandleNews.news) : null;

  if (!mounted) {
    return <div className="min-h-screen bg-[#0a0a0a]" />;
  }

  return !embedded ? null : (
    <div className={cn("bg-[#0a0a0a] text-white flex", embedded ? "h-full" : "min-h-screen")}>
      {/* Sidebar - Hidden in embedded mode */}
      {!embedded && (
        <aside className={cn("flex-shrink-0 border-r border-gray-800 bg-[#0a0a0a] flex flex-col transition-all duration-300", sidebarCollapsed ? "w-16" : "w-60")}>
          <div className="h-16 flex items-center px-4 border-b border-gray-800">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-sm">F</span>
            </div>
            {!sidebarCollapsed && <span className="ml-3 font-bold text-lg">ForexSAI</span>}
          </div>
          <nav className="py-4 space-y-1 flex-1">
            {sidebarItems.map((item) => <SidebarItem key={item.label} {...item} collapsed={sidebarCollapsed} />)}
          </nav>
          <div className="p-4 border-t border-gray-800">
            <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="w-full flex items-center justify-center p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
              <ChevronLeft className={cn("w-5 h-5 transition-transform", sidebarCollapsed && "rotate-180")} />
            </button>
          </div>
        </aside>
      )}

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Symbol Bar */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-[#0a0a0a]">
          <div className="flex-1 flex items-center gap-2 overflow-x-auto scrollbar-hide">
            {symbols.map((sym) => (
              <button
                key={sym.symbol}
                onClick={() => setSelectedSymbol(sym.symbol)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all flex-shrink-0",
                  selectedSymbol === sym.symbol
                    ? "bg-gray-800 text-white border border-gray-700"
                    : "bg-gray-900/50 text-gray-400 hover:bg-gray-800 hover:text-white border border-transparent"
                )}
              >
                <span className="font-semibold">{sym.symbol}</span>
                <span className={cn(
                  "text-xs font-mono",
                  sym.change > 0 ? "text-green-400" : sym.change < 0 ? "text-red-400" : "text-gray-500"
                )}>
                  ${sym.price > 0 ? sym.price.toLocaleString() : "-.--"}
                </span>
                {WS_BACKED_SYMBOLS.has(sym.symbol) && wsConnected && selectedSymbol === sym.symbol && (
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden" style={{ height: embedded ? '100%' : 'calc(100vh - 140px)' }}>
          {/* Chart Section */}
          <div className="flex-1 flex flex-col min-w-0 relative h-full">
            {/* Header */}
            <div className="p-6 border-b border-gray-800">
              <h1 className="text-xl font-bold text-white mb-4">
                {selectedSymbol} - {currentSymbol?.name} {getT(currentLocale).marketAnalysis}
              </h1>
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-green-500/10 border-green-500/30">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-500 uppercase">{getT(currentLocale).swingTrading}</span>
                    <span className="text-sm font-semibold text-green-400 flex items-center gap-1">
                      {getT(currentLocale).bullish} <TrendingUp className="w-4 h-4" />
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-red-500/10 border-red-500/30">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-500 uppercase">{getT(currentLocale).dayTrading}</span>
                    <span className="text-sm font-semibold text-red-400 flex items-center gap-1">
                      {getT(currentLocale).slightlyBearish} <TrendingDown className="w-4 h-4" />
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-purple-500/10 border-purple-500/30">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-500 uppercase">{getT(currentLocale).newsFeed}</span>
                    <span className="text-sm font-semibold text-purple-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                      {getT(currentLocale).highImpact}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="flex-1 relative min-h-0">
              {/* Timeframe selector */}
              <div className="absolute top-4 left-4 z-10 flex items-center gap-1 bg-gray-900/80 backdrop-blur rounded-lg p-1 border border-gray-800">
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf.value}
                    onClick={() => setTimeframe(tf.value)}
                    className={cn(
                      "px-3 py-1.5 rounded text-xs font-medium transition-all",
                      timeframe === tf.value ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"
                    )}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>

              {/* Refresh */}
              <button
                onClick={() => { fetchChartData(); fetchNews(); }}
                className="absolute top-4 left-64 z-10 p-2 bg-gray-900/80 backdrop-blur rounded-lg border border-gray-800 text-gray-400 hover:text-white transition-colors"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              {/* Price levels */}
              {currentSymbol && currentSymbol.price > 0 && (
                <div className="absolute top-4 right-4 z-10 space-y-2">
                  <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                    <span className="text-xs text-gray-400">{getT(currentLocale).currentPrice}:</span>
                    <span className="text-sm text-white ml-2 font-mono">${currentSymbol.price.toFixed(2)}</span>
                  </div>
                  <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                    <span className="text-xs text-gray-400">{getT(currentLocale).pullbackPrice}:</span>
                    <span className="text-sm text-white ml-2 font-mono">${(currentSymbol.price * 1.02).toFixed(2)}</span>
                  </div>
                  <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                    <span className="text-xs text-gray-400">{getT(currentLocale).targetPrice}:</span>
                    <span className="text-sm text-red-400 ml-2 font-mono">${(currentSymbol.price * 0.98).toFixed(2)}</span>
                  </div>
                </div>
              )}

              {/* Loading / Error */}
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                    <span className="text-sm text-gray-500">{getT(currentLocale).loadingChart}</span>
                  </div>
                </div>
              )}

              {error && !loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
                  <div className="flex flex-col items-center gap-3">
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                    <span className="text-sm text-gray-400">{error}</span>
                    <button
                      onClick={fetchChartData}
                      className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600"
                    >
                      {getT(currentLocale).retry}
                    </button>
                  </div>
                </div>
              )}

              {/* Chart container */}
              <div
                ref={chartContainerRef}
                className="w-full h-full"
                style={{ visibility: loading || error ? "hidden" : "visible" }}
              />

              {/* Candle click tip */}
              {!loading && !error && !selectedCandleNews && chartData.length > 0 && (
                <div className="absolute bottom-16 left-4 z-10 bg-gray-900/80 backdrop-blur px-3 py-2 rounded-lg border border-gray-800 text-xs text-gray-400">
                  {getT(currentLocale).clickCandle}
                </div>
              )}

              {!!newsMarkersError && !loading && !error && (
                <div className="absolute top-4 right-4 z-10 max-w-xs bg-amber-500/10 backdrop-blur px-3 py-2 rounded-lg border border-amber-500/30 text-xs text-amber-200">
                  {currentLocale === "tr"
                    ? "Haber işaretçileri yüklenemedi. Grafik işaretleri geçici olarak devre dışı."
                    : "News markers failed to load. Chart markers are temporarily unavailable."}
                </div>
              )}

              {/* Candle info panel */}
              {selectedCandleNews && (
                <div className="absolute top-20 left-4 z-20 w-80 bg-gray-900/95 backdrop-blur-xl border border-gray-700 rounded-xl shadow-2xl overflow-hidden">
                  <div className="flex items-center justify-between p-4 border-b border-gray-800">
                    <div>
                      <h3 className="font-semibold">
                        {format(new Date(selectedCandleNews.candle.actualTimestamp * 1000), "MMM d, HH:mm")}
                      </h3>
                      <p className="text-xs text-gray-500">{getT(currentLocale).candleAnalysis}</p>
                    </div>
                    <button
                      onClick={() => setSelectedCandleNews(null)}
                      className="p-1 text-gray-500 hover:text-white hover:bg-gray-800 rounded"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="p-4 space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">{getT(currentLocale).open}</span>
                        <p className="font-mono text-sm">${selectedCandleNews.candle.open.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">{getT(currentLocale).close}</span>
                        <p className="font-mono text-sm">${selectedCandleNews.candle.close.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">{getT(currentLocale).high}</span>
                        <p className="font-mono text-sm text-green-400">${selectedCandleNews.candle.high.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">{getT(currentLocale).low}</span>
                        <p className="font-mono text-sm text-red-400">${selectedCandleNews.candle.low.toFixed(2)}</p>
                      </div>
                    </div>

                    {selectedCandleNews.hasBigMove && (
                      <div className={cn(
                        "p-3 rounded-lg border",
                        selectedCandleNews.moveType === "up" ? "bg-green-500/10 border-green-500/30" : "bg-red-500/10 border-red-500/30"
                      )}>
                        <div className="flex items-center gap-2 mb-2">
                          {selectedCandleNews.moveType === "up" ?
                            <ArrowUp className="w-4 h-4 text-green-400" /> :
                            <ArrowDown className="w-4 h-4 text-red-400" />
                          }
                          <span className={cn("font-semibold", selectedCandleNews.moveType === "up" ? "text-green-400" : "text-red-400")}>
                            {selectedCandleNews.moveType === "up" ? getT(currentLocale).bigSurge : getT(currentLocale).bigDrop}: {selectedCandleNews.movePercent.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* AI Explanation */}
                    {(loadingExplanation || aiExplanation) && (
                      <div className="p-3 rounded-lg border bg-purple-500/10 border-purple-500/30">
                        <div className="flex items-center gap-2 mb-2">
                          <Brain className="w-4 h-4 text-purple-400" />
                          <span className="font-semibold text-purple-400">{getT(currentLocale).aiAnalysis}</span>
                        </div>
                        {loadingExplanation ? (
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                            <span className="text-xs text-gray-400">{getT(currentLocale).analyzingMove}</span>
                          </div>
                        ) : aiExplanation ? (
                          <p className="text-xs text-gray-300 leading-relaxed">{aiExplanation}</p>
                        ) : null}
                      </div>
                    )}

                    <div>
                      <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Newspaper className="w-4 h-4 text-purple-400" />
                        {selectedCandleNews.isLoadingNews ? (
                          <span className="flex items-center gap-2">
                            {getT(currentLocale).relatedCatalysts}
                            <span className="w-3 h-3 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                          </span>
                        ) : (
                          <>
                            {getT(currentLocale).relatedCatalysts}
                            <span className="text-xs font-normal text-gray-400">
                              ({selectedCandleNews.news.length}
                              {selectedCandleNews.news.some(n => n.match_quality !== 'context') && ` ${getT(currentLocale).matched}`})
                            </span>
                          </>
                        )}
                      </h4>

                      {selectedCandleNews.isLoadingNews ? (
                        <div className="flex items-center justify-center py-4">
                          <span className="text-xs text-gray-500">{getT(currentLocale).findingCatalysts}</span>
                        </div>
                      ) : selectedCandleNews.news.length === 0 ? (
                        <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
                          <p className="text-xs text-gray-500">
                            {selectedCandleNews.hasBigMove
                              ? getT(currentLocale).noStrongCatalyst
                              : getT(currentLocale).noNearbyCatalyst
                            }
                          </p>
                          {selectedCandleNews.hasBigMove && (
                            <p className="text-[10px] text-gray-600 mt-1">
                              {getT(currentLocale).technicalFlow}
                            </p>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-3 max-h-56 overflow-y-auto">
                          {(["news", "economic", "earnings"] as const).map((sectionType) => {
                            const sectionItems = groupedSelectedCatalysts?.[sectionType] || [];
                            if (sectionItems.length === 0) {
                              return null;
                            }
                            const sectionMeta = getCatalystSectionMeta(sectionType, currentLocale);
                            return (
                              <div key={sectionType} className="space-y-2">
                                <div className="flex items-center gap-2">
                                  <span className={cn("text-[10px] px-2 py-1 rounded-md border", sectionMeta.accentClass)}>
                                    {sectionMeta.icon} {sectionMeta.title}
                                  </span>
                                  <span className="text-[10px] text-gray-500">{sectionItems.length}</span>
                                </div>
                                {sectionItems.map((n, i) => (
                                  <div
                                    key={`${sectionType}-${n.id}-${i}`}
                                    className="p-2.5 bg-gray-800/50 rounded-lg text-xs cursor-pointer hover:bg-gray-800 border border-transparent hover:border-gray-700 transition-all"
                                    onClick={() => handleNewsClick(n)}
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex-1 min-w-0">
                                        <p className="text-gray-300 line-clamp-2">{getLocalizedMatchedHeadline(n, currentLocale)}</p>
                                        <p className="text-[10px] text-gray-500 mt-1 line-clamp-2">{getLocalizedMatchedSummary(n, currentLocale)}</p>
                                      </div>
                                      {n.relevance_score > 0 && (
                                        <span className={cn(
                                          "text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0",
                                          n.relevance_score >= 0.7 ? "bg-green-500/20 text-green-400" :
                                            n.relevance_score >= 0.5 ? "bg-yellow-500/20 text-yellow-400" :
                                              "bg-gray-500/20 text-gray-400"
                                        )}>
                                          {Math.round(n.relevance_score * 100)}%
                                        </span>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300">
                                        {getCatalystBadge(n, currentLocale)}
                                      </span>
                                      <span className={cn(
                                        "text-[10px] px-1.5 py-0.5 rounded",
                                        n.urgency === 'breaking' ? "bg-red-500/20 text-red-400" :
                                          n.urgency === 'high' ? "bg-orange-500/20 text-orange-400" :
                                            "bg-gray-500/20 text-gray-400"
                                      )}>
                                        {formatUrgencyLabel(n.urgency, currentLocale)}
                                      </span>
                                      <span className={cn(
                                        "text-[10px] px-1.5 py-0.5 rounded",
                                        n.direction === 'bullish' ? "bg-green-500/20 text-green-400" :
                                          n.direction === 'bearish' ? "bg-red-500/20 text-red-400" :
                                            "bg-gray-500/20 text-gray-400"
                                      )}>
                                        {formatDirectionLabel((n.direction as EventDirection) || "neutral", currentLocale)} {n.score}/10
                                      </span>
                                      <span className="text-[10px] text-gray-500">
                                        {format(new Date(n.timestamp), "HH:mm")}
                                      </span>
                                    </div>
                                    {(n.reasoning_locale || n.reasoning_tr) && (
                                      <p className="text-[10px] text-gray-500 mt-1.5 line-clamp-1">
                                        💡 {currentLocale === 'tr' ? n.reasoning_tr : n.reasoning_locale || n.reasoning_tr}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Days */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-between px-16 py-2 text-xs text-gray-500 border-t border-gray-800 bg-[#0a0a0a]">
                <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span>
              </div>
            </div>

            {/* Bottom bias */}
            <div className="border-t border-gray-800 bg-gray-900/30 p-4">
              <p className="text-sm text-gray-400">
                Day trading bias on <span className="text-white font-semibold">{selectedSymbol}</span> is{" "}
                <span className="text-red-400 font-semibold bg-red-500/10 px-2 py-0.5 rounded">slightly bearish</span>
              </p>
            </div>
          </div>

          {/* News Panel with Tabs */}
          <aside className="w-[420px] border-l border-gray-800 bg-[#0a0a0a] flex flex-col">
            {/* Tabs Header */}
            <div className="flex border-b border-gray-800">
              <button
                onClick={() => setActiveTab("news")}
                className={cn(
                  "flex-1 h-12 flex items-center justify-center gap-2 text-sm font-medium transition-all relative",
                  activeTab === "news" ? "text-white" : "text-gray-500 hover:text-gray-300"
                )}
              >
                <Newspaper className="w-4 h-4" />
                <span>{getT(currentLocale).news}</span>
                {!newsLoading && news.length > 0 && activeTab === "news" && (
                  <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 text-[10px] rounded-full">
                    {news.length}
                  </span>
                )}
                {activeTab === "news" && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-500" />
                )}
              </button>
              <button
                onClick={() => setActiveTab("economic")}
                className={cn(
                  "flex-1 h-12 flex items-center justify-center gap-2 text-sm font-medium transition-all relative",
                  activeTab === "economic" ? "text-white" : "text-gray-500 hover:text-gray-300"
                )}
              >
                <Calendar className="w-4 h-4" />
                <span>{getT(currentLocale).economic}</span>
                {activeTab === "economic" && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-500" />
                )}
              </button>
              <button
                onClick={() => setActiveTab("earnings")}
                className={cn(
                  "flex-1 h-12 flex items-center justify-center gap-2 text-sm font-medium transition-all relative",
                  activeTab === "earnings" ? "text-white" : "text-gray-500 hover:text-gray-300"
                )}
              >
                <Building2 className="w-4 h-4" />
                <span>{getT(currentLocale).earnings}</span>
                {activeTab === "earnings" && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
                )}
              </button>
            </div>

            {/* News Tab Content */}
            {activeTab === "news" && (
              <>
                {/* News Toolbar */}
                <div className="h-12 flex items-center justify-between px-4 border-b border-gray-800 bg-[#0a0a0a]">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "w-2 h-2 rounded-full",
                        newsFeedIsFresh
                          ? "bg-green-500 animate-pulse"
                          : newsStatus === "mock"
                            ? "bg-amber-500"
                            : newsStatus === "error"
                              ? "bg-red-500"
                              : "bg-gray-600"
                      )}
                      title={
                        newsFeedIsFresh
                          ? getT(currentLocale).newsFeedFresh
                          : newsStatus === "mock"
                            ? getT(currentLocale).newsFeedMock
                            : newsStatus === "error"
                              ? getT(currentLocale).newsFeedError
                              : getT(currentLocale).newsFeedStale
                      }
                    />
                    <div className="flex items-center gap-1">
                      {["all", "popular", "high"].map((filter) => (
                        <button
                          key={filter}
                          onClick={() => setNewsFilter(filter as any)}
                          className={cn(
                            "px-2.5 py-1 rounded-md text-[11px] font-medium transition-all",
                            newsFilter === filter
                              ? "bg-purple-500/20 text-purple-400"
                              : "text-gray-500 hover:text-gray-300 hover:bg-gray-800"
                          )}
                        >
                          {getT(currentLocale)[filter] || (filter.charAt(0).toUpperCase() + filter.slice(1))}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {news.length === 0 && !newsLoading && (
                      <button
                        onClick={() => { fetchNews(true); }}
                        className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-md text-[10px] hover:bg-purple-500/30 transition-colors"
                        title={getT(currentLocale).loadTestNewsTitle}
                      >
                        {getT(currentLocale).testLabel}
                      </button>
                    )}
                    <select
                      value={currentLocale}
                      onChange={(e) => setCurrentLocale(e.target.value)}
                      className="bg-gray-900 border border-gray-800 rounded-md px-2 py-1 text-[11px] text-gray-400"
                    >
                      <option value="tr">🇹🇷 TR</option>
                      <option value="en">🇬🇧 EN</option>
                      <option value="de">🇩🇪 DE</option>
                      <option value="es">🇪🇸 ES</option>
                      <option value="fr">🇫🇷 FR</option>
                    </select>
                    <button onClick={() => fetchNews(false)} title={getT(currentLocale).refreshLabel} className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-md">
                      <RefreshCw className={cn("w-3.5 h-3.5", newsLoading && "animate-spin")} />
                    </button>
                  </div>
                </div>

                {newsStatus !== "api" && newsStatus !== "idle" && !newsLoading && (
                  <div
                    className={cn(
                      "px-4 py-2 text-[11px] border-b",
                      newsStatus === "error"
                        ? "bg-red-500/10 text-red-300 border-red-500/20"
                        : newsStatus === "mock"
                          ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                          : "bg-gray-900/70 text-gray-400 border-gray-800"
                    )}
                  >
                    {newsStatusMessage || (newsStatus === "empty" ? getT(currentLocale).noNewsFound : getT(currentLocale).newsStatusChanged)}
                  </div>
                )}

                {/* News List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {newsLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className="h-32 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                    ))
                  ) : filteredNews.length === 0 ? (
                    <div className="text-center py-12">
                      <Newspaper className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm mb-2">
                        {hasHiddenNewsByFilter ? getT(currentLocale).noNewsFilter : getT(currentLocale).noNewsAvailable}
                      </p>
                      <p className="text-gray-600 text-xs mb-4 px-4">
                        {hasHiddenNewsByFilter
                          ? getT(currentLocale).noNewsFilterDetail
                          : getT(currentLocale).noNewsDetail}
                      </p>
                      {hasHiddenNewsByFilter ? (
                        <button
                          onClick={() => setNewsFilter("all")}
                          className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                        >
                          {getT(currentLocale).showAllNews}
                        </button>
                      ) : (
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => { fetchNews(false); }}
                            className="px-4 py-2 bg-gray-800 text-white rounded-lg text-sm hover:bg-gray-700 transition-colors"
                          >
                            {getT(currentLocale).retryApi}
                          </button>
                          <button
                            onClick={() => { fetchNews(true); }}
                            className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                          >
                            {getT(currentLocale).loadTestNews}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    filteredNews.map((item) => (
                      <NewsCard
                        key={item.id}
                        news={item}
                        onClick={() => handleNewsClick(item)}
                        locale={currentLocale}
                      />
                    ))
                  )}
                </div>
              </>
            )}

            {/* Economic Calendar Tab Content */}
            {activeTab === "economic" && (
              <>
                <div className="h-12 flex items-center justify-between px-4 border-b border-gray-800 bg-[#0a0a0a]">
                  <h3 className="text-sm font-medium flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-amber-500" />
                    {getT(currentLocale).economicEvents}
                  </h3>
                  <button
                    onClick={() => fetchEconomicCalendar()}
                    className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-md"
                    title={getT(currentLocale).refreshLabel}
                  >
                    <RefreshCw className={cn("w-3.5 h-3.5", economicLoading && "animate-spin")} />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {economicLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="h-28 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                    ))
                  ) : economicEvents.length === 0 ? (
                    <div className="text-center py-12">
                      <Calendar className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm">{getT(currentLocale).noEconomicEvents}</p>
                    </div>
                  ) : (
                    economicEvents.slice(0, 20).map((event) => (
                      <div
                        key={event.id}
                        onClick={() => void openEconomicEvent(event)}
                        className={cn(
                          "group relative p-4 rounded-xl border transition-all cursor-pointer overflow-hidden",
                          event.impact === "High"
                            ? "bg-gradient-to-r from-red-950/40 via-amber-950/20 to-transparent border-red-900/40 hover:border-red-500/50"
                            : event.impact === "Medium"
                              ? "bg-gradient-to-r from-amber-950/40 to-transparent border-amber-900/40 hover:border-amber-500/50"
                              : "bg-gradient-to-r from-gray-900/50 to-transparent border-gray-800 hover:border-gray-600"
                        )}
                      >
                        {/* Impact glow effect */}
                        <div className={cn(
                          "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500",
                          event.impact === "High" && "bg-gradient-to-br from-red-500/5 to-transparent",
                          event.impact === "Medium" && "bg-gradient-to-br from-amber-500/5 to-transparent"
                        )} />

                        <div className="relative">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className={cn(
                                "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider",
                                event.impact === "High" && "bg-red-500/20 text-red-400 border border-red-500/30 shadow-[0_0_10px_rgba(239,68,68,0.2)]",
                                event.impact === "Medium" && "bg-amber-500/20 text-amber-400 border border-amber-500/30",
                                event.impact === "Low" && "bg-gray-700/50 text-gray-400 border border-gray-600"
                              )}>
                                {formatImpactLevelLabel(event.impact, currentLocale)}
                              </span>
                              <span className="text-xs text-gray-500 font-mono">
                                {format(new Date(event.timestamp), "MMM d, HH:mm")}
                              </span>
                            </div>
                            <span className={getDirectionBadgeClass(event.predicted_direction)}>
                              {getDirectionArrow(event.predicted_direction)} {formatDirectionLabel(event.predicted_direction, currentLocale)}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-2 tracking-wide">
                            {currentLocale === "tr" && event.title_tr ? event.title_tr : event.title}
                          </h4>
                          <p className="text-xs text-gray-500 line-clamp-1 mb-3">
                            {event.currency} • {event.affected_symbols.slice(0, 4).join(", ")}
                          </p>
                          {(event.previous || event.forecast) && (
                            <div className="flex items-center gap-4 text-[11px]">
                              {event.previous && (
                                <span className="text-gray-500">{getT(currentLocale).prev}: <span className="text-gray-300 font-mono">{event.previous}</span></span>
                              )}
                              {event.forecast && (
                                <span className="text-gray-500">{getT(currentLocale).exp}: <span className="text-amber-400 font-mono">{event.forecast}</span></span>
                              )}
                            </div>
                          )}
                          <EventAIMetadata event={event} compact locale={currentLocale} />
                          {/* Click hint */}
                          <div className="absolute bottom-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="text-[10px] text-gray-600">{getT(currentLocale).clickDetails}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}

            {/* Earnings Calendar Tab Content */}
            {activeTab === "earnings" && (
              <>
                <div className="h-12 flex items-center justify-between px-4 border-b border-gray-800 bg-[#0a0a0a]">
                  <h3 className="text-sm font-medium flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-blue-500" />
                    {getT(currentLocale).earningsReports}
                  </h3>
                  <button
                    onClick={() => fetchEarningsCalendar()}
                    className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-md"
                    title={getT(currentLocale).refreshLabel}
                  >
                    <RefreshCw className={cn("w-3.5 h-3.5", earningsLoading && "animate-spin")} />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {earningsLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="h-28 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                    ))
                  ) : earningsEvents.length === 0 ? (
                    <div className="text-center py-12">
                      <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm">{getT(currentLocale).noEarningsReports}</p>
                    </div>
                  ) : (
                    earningsEvents.slice(0, 20).map((event) => (
                      <div
                        key={event.id}
                        onClick={() => void openEarningsEvent(event)}
                        className="group relative p-4 rounded-xl border border-gray-800 bg-gradient-to-r from-blue-950/30 via-indigo-950/20 to-transparent hover:border-blue-500/50 transition-all cursor-pointer overflow-hidden"
                      >
                        {/* Glow effect */}
                        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-blue-500/5 to-transparent" />

                        <div className="relative">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 text-blue-400 rounded text-xs font-bold border border-blue-500/30">
                                {event.ticker}
                              </span>
                              <span className="text-xs text-gray-500 font-mono">
                                {format(new Date(event.timestamp), "MMM d")}
                              </span>
                              <span className={cn(
                                "text-[10px] px-1.5 py-0.5 rounded font-medium",
                                event.time === "after_market" ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                              )}>
                                {formatSessionShort(event.time, currentLocale)}
                              </span>
                            </div>
                            <span className={getDirectionBadgeClass(event.predicted_direction)}>
                              {getDirectionArrow(event.predicted_direction)} {formatDirectionLabel(event.predicted_direction, currentLocale)}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-2 tracking-wide">
                            {event.company}
                          </h4>
                          <div className="flex items-center gap-4 text-[11px]">
                            {event.eps_forecast && (
                              <span className="text-gray-500">
                                {getT(currentLocale).epsEstimate}: <span className="text-gray-300 font-mono">{event.eps_forecast}</span>
                              </span>
                            )}
                            {event.revenue_forecast && (
                              <span className="text-gray-500">
                                {getT(currentLocale).revenueEstimate}: <span className="text-gray-300 font-mono">{event.revenue_forecast}</span>
                              </span>
                            )}
                          </div>
                          <EventAIMetadata event={event} compact locale={currentLocale} />
                          <p className="text-[10px] text-gray-600 mt-2 uppercase tracking-wider">{event.sector}</p>
                          {/* Click hint */}
                          <div className="absolute bottom-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="text-[10px] text-gray-600">{getT(currentLocale).clickDetails}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}
          </aside>
        </div>
      </main>

      <NewsDetailModal
        news={selectedNewsForModal}
        isOpen={isNewsModalOpen}
        onClose={() => setIsNewsModalOpen(false)}
        locale={currentLocale as any}
      />

      {/* Economic Event Detail Modal */}
      {isEconomicModalOpen && selectedEconomicEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0f0f0f] border border-gray-800 rounded-2xl max-w-lg w-full max-h-[80vh] overflow-hidden shadow-2xl">
            <div className="h-16 flex items-center justify-between px-6 border-b border-gray-800 bg-gradient-to-r from-amber-950/30 to-transparent">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center border border-amber-500/30">
                  <Calendar className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">{getT(currentLocale).economicEvent}</h3>
                  <p className="text-xs text-gray-500">{format(new Date(selectedEconomicEvent.timestamp), "MMM d, yyyy HH:mm")}</p>
                </div>
              </div>
              <button
                onClick={() => setIsEconomicModalOpen(false)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="flex items-center gap-2 mb-4">
                <span className={cn(
                  "px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider",
                  selectedEconomicEvent.impact === "High" && "bg-red-500/20 text-red-400 border border-red-500/30",
                  selectedEconomicEvent.impact === "Medium" && "bg-amber-500/20 text-amber-400 border border-amber-500/30",
                  selectedEconomicEvent.impact === "Low" && "bg-gray-700/50 text-gray-400 border border-gray-600"
                )}>
                  {formatImpactLevelLabel(selectedEconomicEvent.impact, currentLocale)} {getT(currentLocale).impact}
                </span>
                <span className="text-xs text-gray-500">{selectedEconomicEvent.currency}</span>
              </div>
              <h2 className="text-xl font-bold text-white mb-4">
                {currentLocale === "tr" && selectedEconomicEvent.title_tr ? selectedEconomicEvent.title_tr : selectedEconomicEvent.title}
              </h2>

              <EventAIMetadata event={selectedEconomicEvent} locale={currentLocale} />

              {(selectedEconomicEvent.previous || selectedEconomicEvent.forecast) && (
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {selectedEconomicEvent.previous && (
                    <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{getT(currentLocale).previous}</p>
                      <p className="text-lg font-mono text-gray-300">{selectedEconomicEvent.previous}</p>
                    </div>
                  )}
                  {selectedEconomicEvent.forecast && (
                    <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-900/40">
                      <p className="text-[10px] uppercase tracking-wider text-amber-500/70 mb-1">{getT(currentLocale).forecast}</p>
                      <p className="text-lg font-mono text-amber-400">{selectedEconomicEvent.forecast}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-amber-500" />
                    {getT(currentLocale).expectedDirection}
                  </h4>
                  <p className={cn("text-sm p-3 rounded-xl border", getDirectionBadgeClass(selectedEconomicEvent.predicted_direction))}>
                    {formatDirectionSummary(selectedEconomicEvent.predicted_direction, currentLocale)}
                  </p>
                </div>

                {selectedEconomicEvent.impact_analysis && (
                  <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/20 to-transparent border border-cyan-900/30">
                    <h4 className="text-sm font-semibold text-cyan-300 mb-2 flex items-center gap-2">
                      <Brain className="w-4 h-4" />
                      {getT(currentLocale).deepseekAnalysis}
                    </h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {currentLocale === "tr" && selectedEconomicEvent.impact_analysis_tr
                        ? selectedEconomicEvent.impact_analysis_tr
                        : selectedEconomicEvent.impact_analysis}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">{getT(currentLocale).description}</h4>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    {currentLocale === "tr" && selectedEconomicEvent.description_tr ? selectedEconomicEvent.description_tr : selectedEconomicEvent.description}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">{getT(currentLocale).affectedSymbols}</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedEconomicEvent.affected_symbols.map((symbol) => (
                      <span key={symbol} className="px-2 py-1 bg-gray-800 text-gray-400 rounded text-xs font-mono">
                        {symbol}
                      </span>
                    ))}
                  </div>
                </div>

                {selectedEconomicEvent.why_it_matters && (
                  <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/20 to-transparent border border-amber-900/30">
                    <h4 className="text-sm font-semibold text-amber-400 mb-2">{getT(currentLocale).whyItMatters}</h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {currentLocale === "tr" && selectedEconomicEvent.why_it_matters_tr ? selectedEconomicEvent.why_it_matters_tr : selectedEconomicEvent.why_it_matters}
                    </p>
                  </div>
                )}

                {/* SCENARIO VARIATIONS */}
                <div className="mt-6 border-t border-gray-800 pt-6">
                  <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    {getT(currentLocale).scenarioVariations}
                    {loadingEventDetail && (
                      <span className="ml-2 text-[10px] text-amber-400 animate-pulse">{getT(currentLocale).analyzingAI}</span>
                    )}
                  </h4>
                  {loadingEventDetail && !selectedEconomicEvent.scenarios && (
                    <div className="space-y-3">
                      <div className="h-24 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                      <div className="h-24 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                    </div>
                  )}
                  {!loadingEventDetail && !selectedEconomicEvent.scenarios && (
                    <p className="text-xs text-gray-500 italic">{getT(currentLocale).scenarioUnavailable}</p>
                  )}


                  {/* Better Than Expected */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-green-950/40 to-transparent border border-green-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs">🟢</span>
                      <h5 className="text-sm font-semibold text-green-400">{getT(currentLocale).betterThanExpected}</h5>
                    </div>
                    {/* Impacts - News Card Style */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {selectedEconomicEvent.scenarios?.better_than_expected?.impacts?.map((impact: any, idx: number) => (
                        <ImpactChip key={idx} impact={impact} />
                      )) || (
                          <>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-green-500/10 text-green-400 border-green-500/20">
                              ↗ DXY +0.3%
                            </span>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-red-500/10 text-red-400 border-red-500/20">
                              ↘ XAUUSD -$8
                            </span>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-red-500/10 text-red-400 border-red-500/20">
                              ↘ NDX -0.4%
                            </span>
                          </>
                        )}
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).first5min}</span>
                        <span className="text-green-400">{selectedEconomicEvent.scenarios?.better_than_expected?.first_5min || localeCopy(currentLocale, "Sharp initial move", "İlk sert hareket")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).firstHour}</span>
                        <span className="text-green-400">{selectedEconomicEvent.scenarios?.better_than_expected?.first_hour || localeCopy(currentLocale, "Momentum continues", "Momentum devam eder")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).dayClose}</span>
                        <span className="text-amber-400">{selectedEconomicEvent.scenarios?.better_than_expected?.day_close || localeCopy(currentLocale, "Watch for profit taking", "Kâr satışlarına dikkat edin")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).nextDay}</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.better_than_expected?.next_day || localeCopy(currentLocale, "Follow-through or reversal", "Devam hareketi veya tersine dönüş")}</span>
                      </div>
                    </div>
                  </div>

                  {/* Worse Than Expected */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-transparent border border-red-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs">🔴</span>
                      <h5 className="text-sm font-semibold text-red-400">{getT(currentLocale).worseThanExpected}</h5>
                    </div>
                    {/* Impacts - News Card Style */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {selectedEconomicEvent.scenarios?.worse_than_expected?.impacts?.map((impact: any, idx: number) => (
                        <ImpactChip key={idx} impact={impact} />
                      )) || (
                          <>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-red-500/10 text-red-400 border-red-500/20">
                              ↘ DXY -0.3%
                            </span>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-green-500/10 text-green-400 border-green-500/20">
                              ↗ XAUUSD +$10
                            </span>
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-green-500/10 text-green-400 border-green-500/20">
                              ↗ NDX +0.5%
                            </span>
                          </>
                        )}
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).first5min}</span>
                        <span className="text-red-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.first_5min || localeCopy(currentLocale, "Sharp initial move", "İlk sert hareket")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).firstHour}</span>
                        <span className="text-red-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.first_hour || localeCopy(currentLocale, "Momentum continues", "Momentum devam eder")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).dayClose}</span>
                        <span className="text-amber-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.day_close || localeCopy(currentLocale, "Watch for reversals", "Tersine dönüşlere dikkat edin")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).nextDay}</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.next_day || localeCopy(currentLocale, "Mean reversion possible", "Ortalamaya dönüş mümkün")}</span>
                      </div>
                    </div>
                  </div>

                  {/* As Expected */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-gray-900/50 to-transparent border border-gray-700/50">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 text-xs">⚪</span>
                      <h5 className="text-sm font-semibold text-gray-400">{getT(currentLocale).asExpected}</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).first5min}</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.as_expected?.first_5min || localeCopy(currentLocale, "Minimal movement ±0.1%", "Sınırlı hareket ±0.1%")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).firstHour}</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.as_expected?.first_hour || localeCopy(currentLocale, "Range-bound, look for other catalysts", "Yatay seyir, diğer katalizörlere bakın")}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">{getT(currentLocale).restOfDay}</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.as_expected?.day_close || localeCopy(currentLocale, "Focus shifts to technicals and other news", "Odak teknikler ve diğer haberlere kayar")}</span>
                      </div>
                    </div>
                  </div>

                  {/* Trading Tips */}
                  <div className="mt-4 p-3 rounded-lg bg-blue-950/30 border border-blue-900/30">
                    <p className="text-[11px] text-blue-400">
                      <span className="font-semibold">{getT(currentLocale).proTip}</span> {selectedEconomicEvent.trading_tips || localeCopy(currentLocale, "Wait 5 minutes after release for initial volatility to settle. Use limit orders, not market orders. Watch for reversals after the first hour.", "İlk volatilitenin oturması için veri sonrası 5 dakika bekleyin. Piyasa emri yerine limit emir kullanın. İlk saatin ardından olası tersine dönüşleri izleyin.")}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )
      }

      {/* Earnings Event Detail Modal */}
      {
        isEarningsModalOpen && selectedEarningsEvent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#0f0f0f] border border-gray-800 rounded-2xl max-w-lg w-full max-h-[80vh] overflow-hidden shadow-2xl">
              <div className="h-16 flex items-center justify-between px-6 border-b border-gray-800 bg-gradient-to-r from-blue-950/30 to-transparent">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 flex items-center justify-center border border-blue-500/30">
                    <Building2 className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{getT(currentLocale).earningsReport}</h3>
                    <p className="text-xs text-gray-500">{format(new Date(selectedEarningsEvent.timestamp), "MMM d, yyyy")}</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsEarningsModalOpen(false)}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="flex items-center gap-2 mb-4">
                  <span className="px-3 py-1 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 text-blue-400 rounded-lg text-[10px] font-bold border border-blue-500/30">
                    {selectedEarningsEvent.ticker}
                  </span>
                  <span className={cn(
                    "text-[10px] px-2 py-0.5 rounded font-medium",
                    selectedEarningsEvent.time === "after_market" ? "bg-purple-500/20 text-purple-400" : "bg-amber-500/20 text-amber-400"
                  )}>
                    {formatSessionLabel(selectedEarningsEvent.time, currentLocale)}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-white mb-2">{selectedEarningsEvent.company}</h2>
                <p className="text-sm text-gray-500 mb-6">{selectedEarningsEvent.sector}</p>

                <EventAIMetadata event={selectedEarningsEvent} locale={currentLocale} />

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                    <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{getT(currentLocale).epsEstimate}</p>
                    <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.eps_forecast || "N/A"}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                    <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{getT(currentLocale).revenueEstimate}</p>
                    <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.revenue_forecast || "N/A"}</p>
                  </div>
                  {selectedEarningsEvent.previous_eps && (
                    <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{getT(currentLocale).previousEps}</p>
                      <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.previous_eps}</p>
                    </div>
                  )}
                  {selectedEarningsEvent.previous_revenue && (
                    <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{getT(currentLocale).previousRevenue}</p>
                      <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.previous_revenue}</p>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                      {getT(currentLocale).aiPrediction}
                    </h4>
                    <div className="flex items-center gap-4">
                      <p className={cn("text-sm px-4 py-2 rounded-xl border flex-1", getDirectionBadgeClass(selectedEarningsEvent.predicted_direction))}>
                        {selectedEarningsEvent.predicted_direction === "bullish" && getT(currentLocale).beatExpected}
                        {selectedEarningsEvent.predicted_direction === "bearish" && getT(currentLocale).missExpected}
                        {selectedEarningsEvent.predicted_direction === "neutral" && getT(currentLocale).inLineExpected}
                        {selectedEarningsEvent.predicted_direction === "volatile" && getT(currentLocale).highVolExpected}
                      </p>
                      <div className="text-center">
                        <p className="text-2xl font-mono text-blue-400">{Math.round(normalizeDisplayConfidence(selectedEarningsEvent.confidence))}%</p>
                        <p className="text-[10px] text-gray-500">{getT(currentLocale).confidence}</p>
                      </div>
                    </div>
                  </div>

                  {selectedEarningsEvent.affected_symbols.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">{getT(currentLocale).affectedSymbols}</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedEarningsEvent.affected_symbols.map((symbol) => (
                          <span key={symbol} className="px-2 py-1 bg-gray-800 text-gray-400 rounded text-xs font-mono">
                            {symbol}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedEarningsEvent.analysis && (
                    <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/20 to-transparent border border-blue-900/30">
                      <h4 className="text-sm font-semibold text-blue-400 mb-2">{getT(currentLocale).aiAnalysis}</h4>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        {currentLocale === "tr" && selectedEarningsEvent.analysis_tr ? selectedEarningsEvent.analysis_tr : selectedEarningsEvent.analysis}
                      </p>
                    </div>
                  )}

                  {selectedEarningsEvent.key_metrics.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">{getT(currentLocale).keyMetrics}</h4>
                      <div className="flex flex-wrap gap-2">
                        {(currentLocale === "tr" && selectedEarningsEvent.key_metrics_tr ? selectedEarningsEvent.key_metrics_tr : selectedEarningsEvent.key_metrics).map((metric) => (
                          <span key={metric} className="px-3 py-1.5 bg-blue-950/30 text-blue-400 rounded-lg text-xs border border-blue-900/30">
                            {metric}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* SCENARIO VARIATIONS */}
                  <div className="mt-6 border-t border-gray-800 pt-6">
                    <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-blue-500" />
                      {getT(currentLocale).scenarioVariations}
                    </h4>

                    {/* Beat Scenario */}
                    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-green-950/40 to-transparent border border-green-900/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs">✅</span>
                        <h5 className="text-sm font-semibold text-green-400">{getT(currentLocale).beatScenario}</h5>
                      </div>
                      {/* Impacts - News Card Style */}
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {selectedEarningsEvent.scenarios?.beat?.impacts?.map((impact: any, idx: number) => (
                          <ImpactChip key={idx} impact={impact} />
                        )) || (
                            <>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-green-500/10 text-green-400 border-green-500/20">
                                ↗ {selectedEarningsEvent.ticker} +4%
                              </span>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-green-500/10 text-green-400 border-green-500/20">
                                ↗ NDX +0.5%
                              </span>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-red-500/10 text-red-400 border-red-500/20">
                                ↘ VIX -5%
                              </span>
                            </>
                          )}
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).preMarketLabel}</span>
                          <span className="text-green-400">{selectedEarningsEvent.scenarios?.beat?.pre_market || localeCopy(currentLocale, `Stock +3-5% • ${selectedEarningsEvent.ticker} calls spike`, `Hisse +3-5% • ${selectedEarningsEvent.ticker} call hacmi artar`)}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).openLabel}</span>
                          <span className="text-green-400">{selectedEarningsEvent.scenarios?.beat?.open || localeCopy(currentLocale, "Gap up, momentum buyers enter", "Gap yukarı açılır, momentum alıcıları devreye girer")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).firstHour}</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.beat?.first_hour || localeCopy(currentLocale, "Watch for profit taking at highs", "Zirvelerde kâr satışlarına dikkat edin")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).sectorLabel}</span>
                          <span className="text-blue-400">{selectedEarningsEvent.scenarios?.beat?.sector_effect || localeCopy(currentLocale, `${selectedEarningsEvent.sector} peers likely rally`, `${selectedEarningsEvent.sector} benzerleri yükseliş gösterebilir`)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Miss Scenario */}
                    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-transparent border border-red-900/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs">❌</span>
                        <h5 className="text-sm font-semibold text-red-400">{getT(currentLocale).missScenario}</h5>
                      </div>
                      {/* Impacts - News Card Style */}
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {selectedEarningsEvent.scenarios?.miss?.impacts?.map((impact: any, idx: number) => (
                          <ImpactChip key={idx} impact={impact} />
                        )) || (
                            <>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-red-500/10 text-red-400 border-red-500/20">
                                ↘ {selectedEarningsEvent.ticker} -6%
                              </span>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-red-500/10 text-red-400 border-red-500/20">
                                ↘ NDX -0.4%
                              </span>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-green-500/10 text-green-400 border-green-500/20">
                                ↗ VIX +8%
                              </span>
                            </>
                          )}
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).preMarketLabel}</span>
                          <span className="text-red-400">{selectedEarningsEvent.scenarios?.miss?.pre_market || localeCopy(currentLocale, `Stock -4-7% • Put volume surges`, "Hisse -4-7% • Put hacmi yükselir")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).openLabel}</span>
                          <span className="text-red-400">{selectedEarningsEvent.scenarios?.miss?.open || localeCopy(currentLocale, "Gap down, stop losses trigger", "Gap aşağı açılır, stoplar çalışır")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).firstHour}</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.miss?.first_hour || localeCopy(currentLocale, "Dead cat bounce possible, then fade", "Kısa tepki yükselişi görülebilir, ardından zayıflama")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).sectorLabel}</span>
                          <span className="text-red-400">{selectedEarningsEvent.scenarios?.miss?.sector_effect || localeCopy(currentLocale, `${selectedEarningsEvent.sector} peers may decline`, `${selectedEarningsEvent.sector} benzerleri düşebilir`)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Mixed Scenario */}
                    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-transparent border border-amber-900/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-400 text-xs">⚠️</span>
                        <h5 className="text-sm font-semibold text-amber-400">{getT(currentLocale).mixedScenario}</h5>
                      </div>
                      {/* Impacts - News Card Style */}
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {selectedEarningsEvent.scenarios?.mixed?.impacts?.map((impact: any, idx: number) => (
                          <ImpactChip key={idx} impact={impact} />
                        )) || (
                            <>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-amber-500/10 text-amber-400 border-amber-500/20">
                                → {selectedEarningsEvent.ticker} ±2%
                              </span>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-gray-700/50 text-gray-400 border-gray-600">
                                → NDX ±0.2%
                              </span>
                            </>
                          )}
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).preMarketLabel}</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.mixed?.pre_market || localeCopy(currentLocale, "Volatile ±2% • Direction unclear", "Volatil ±2% • Yön belirsiz")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).guidanceLabel}</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.mixed?.guidance_importance || localeCopy(currentLocale, "Forward guidance becomes key driver", "İleriye dönük rehberlik ana belirleyici olur")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).firstHour}</span>
                          <span className="text-gray-400">{selectedEarningsEvent.scenarios?.mixed?.trading_approach || localeCopy(currentLocale, "Wait for conference call clarity", "Konferans görüşmesindeki netliği bekleyin")}</span>
                        </div>
                      </div>
                    </div>

                    {/* In Line */}
                    <div className="p-4 rounded-xl bg-gradient-to-r from-gray-900/50 to-transparent border border-gray-700/50">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 text-xs">➖</span>
                        <h5 className="text-sm font-semibold text-gray-400">{getT(currentLocale).inLineScenario}</h5>
                      </div>
                      {/* Impacts - News Card Style */}
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {selectedEarningsEvent.scenarios?.inline?.impacts?.map((impact: any, idx: number) => (
                          <ImpactChip key={idx} impact={impact} />
                        )) || (
                            <>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-gray-700/50 text-gray-400 border-gray-600">
                                → {selectedEarningsEvent.ticker} ±1%
                              </span>
                              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border bg-gray-700/50 text-gray-400 border-gray-600">
                                → NDX ±0.1%
                              </span>
                            </>
                          )}
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).preMarketLabel}</span>
                          <span className="text-gray-400">{selectedEarningsEvent.scenarios?.inline?.pre_market || localeCopy(currentLocale, "±1% move • Options IV crush likely", "±1% hareket • Opsiyon IV düşüşü olası")}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">{getT(currentLocale).guidanceLabel}</span>
                          <span className="text-gray-400">{selectedEarningsEvent.scenarios?.inline?.guidance_focus || localeCopy(currentLocale, "Stock direction depends on forward outlook", "Hissenin yönü ileriye dönük rehberliğe bağlıdır")}</span>
                        </div>
                      </div>
                    </div>

                    {/* Trading Tips */}
                    <div className="mt-4 p-3 rounded-lg bg-purple-950/30 border border-purple-900/30">
                      <p className="text-[11px] text-purple-400">
                        <span className="font-semibold">{getT(currentLocale).proTip}</span> {selectedEarningsEvent.trading_tips || localeCopy(currentLocale, `For ${selectedEarningsEvent.time === "after_market" ? "after-hours" : "pre-market"} earnings, liquidity is lower and spreads wider. Consider waiting for regular session open for better fills. Watch for post-earnings drift in following days.`, `${formatSessionLabel(selectedEarningsEvent.time, currentLocale)} açıklanan bilançolarda likidite daha düşüktür ve spreadler daha geniştir. Daha iyi dolum için normal seans açılışını beklemeyi değerlendirin. Sonraki günlerde bilanço sonrası sürüklenmeyi izleyin.`)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      }
    </div >
  );
}
