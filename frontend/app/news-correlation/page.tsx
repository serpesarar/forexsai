"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
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

  return value <= 1 ? Math.round(value * 100) : value;
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

function isTurkishLocale(locale: string): boolean {
  return locale === "tr";
}

function isEnglishLocale(locale: string): boolean {
  return locale === "en";
}

function usesRuntimeLocale(locale: string): boolean {
  return !isTurkishLocale(locale) && !isEnglishLocale(locale);
}

function getLocalizedHeadline(item: EnrichedNews, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.headline_tr || item.summary_tr || item.analysis_tr || item.content_tr || item.headline || item.summary_en || "";
  }

  if (usesRuntimeLocale(locale)) {
    return item.headline_locale || item.summary_locale || item.analysis_locale || item.headline || item.summary_en || item.headline_tr || item.summary_tr || "";
  }

  return item.headline || item.summary_en || item.headline_tr || item.summary_tr || "";
}

function getLocalizedSummary(item: EnrichedNews, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.summary_tr || item.analysis_tr || item.content_tr || item.headline_tr || item.summary_en || item.headline || "";
  }

  if (usesRuntimeLocale(locale)) {
    return item.summary_locale || item.analysis_locale || item.headline_locale || item.summary_en || item.headline || item.summary_tr || item.headline_tr || "";
  }

  return item.summary_en || item.headline || item.analysis_en || item.summary_tr || item.headline_tr || "";
}

function getLocalizedAnalysis(item: EnrichedNews, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.analysis_tr || item.content_tr || item.summary_tr || item.analysis_en || item.content || item.headline || "";
  }

  if (usesRuntimeLocale(locale)) {
    return item.analysis_locale || item.summary_locale || item.headline_locale || item.analysis_en || item.content || item.summary_en || item.analysis_tr || item.content_tr || item.headline || "";
  }

  return item.analysis_en || item.content || item.summary_en || item.analysis_tr || item.content_tr || item.headline || "";
}

function getLocalizedMatchedHeadline(item: MatchedNewsItem, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.headline || item.summary_tr || item.analysis_tr || item.headline_en || "";
  }

  if (usesRuntimeLocale(locale)) {
    return item.headline_locale || item.summary_locale || item.analysis_locale || item.headline || item.headline_en || item.summary_en || "";
  }

  return item.headline_en || item.summary_en || item.headline || item.summary_tr || "";
}

function getLocalizedMatchedSummary(item: MatchedNewsItem, locale: string): string {
  if (isTurkishLocale(locale)) {
    return item.summary_tr || item.analysis_tr || item.reasoning_tr || item.headline || item.headline_en || "";
  }

  if (usesRuntimeLocale(locale)) {
    return item.summary_locale || item.analysis_locale || item.reasoning_locale || item.headline_locale || item.summary_en || item.analysis_en || item.headline || item.headline_en || "";
  }

  return item.summary_en || item.analysis_en || item.headline_en || item.reasoning_tr || item.headline || "";
}

function getCatalystBadge(item: MatchedNewsItem, locale: string): string {
  const labels = {
    en: { news: "News", economic: "Economic", earnings: "Earnings", context: "Context" },
    tr: { news: "Haber", economic: "Ekonomik", earnings: "Bilanço", context: "Bağlam" },
  };

  const language = isTurkishLocale(locale) ? "tr" : "en";
  const labelSet = labels[language];
  const catalystLabel = labelSet[item.catalyst_type || "news"] || labelSet.news;
  return item.match_quality === "context" ? `${catalystLabel} · ${labelSet.context}` : catalystLabel;
}

function normalizeNewsItem(item: any): EnrichedNews {
  return {
    id: String(item.id ?? ""),
    timestamp: item.timestamp || item.published_at || new Date().toISOString(),
    source: item.source || "Unknown",
    headline: item.headline || item.headline_en || "",
    headline_tr: item.headline_tr || item.summary_tr || item.analysis_tr || item.content_tr || item.headline || item.headline_en || "",
    content: item.content || item.analysis_en || item.analysis || item.summary_en || item.summary || item.headline || "",
    content_tr: item.content_tr || item.analysis_tr || item.summary_tr || item.headline_tr || item.headline || item.headline_en || "",
    summary_en: item.summary_en || item.summary || item.headline || item.headline_en || "",
    summary_tr: item.summary_tr || item.analysis_tr || item.content_tr || item.headline_tr || item.headline || item.headline_en || "",
    analysis_en: item.analysis_en || item.analysis || item.content || item.summary_en || item.summary || item.headline || item.headline_en || "",
    analysis_tr: item.analysis_tr || item.content_tr || item.summary_tr || item.headline_tr || item.analysis_en || item.analysis || item.content || item.headline || item.headline_en || "",
    headline_locale: item.headline_locale || undefined,
    summary_locale: item.summary_locale || undefined,
    analysis_locale: item.analysis_locale || item.summary_locale || undefined,
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
  { symbol: "VIX", name: "VIX", price: 0, change: 0, changePercent: 0 },
  { symbol: "DXY", name: "Dollar Index", price: 0, change: 0, changePercent: 0 },
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

const sidebarItems = [
  { icon: Bell, label: "Alerts", href: "/alerts", badge: 3 },
  { icon: Star, label: "Watchlist", href: "/watchlist", badge: null },
  { icon: Wallet, label: "Smart Trades", href: "/news-correlation", badge: null, active: true },
  { icon: Calendar, label: "Economic Calendar", href: "/calendar", badge: null },
  { icon: MessageSquare, label: "Chat AI", href: "/chat", badge: null },
  { icon: Newspaper, label: "Research Reports", href: "/research", badge: null },
  { icon: BookOpen, label: "Docs", href: "/docs", badge: null },
  { icon: Building2, label: "Brokers", href: "/brokers", badge: null },
  { icon: LineChart, label: "My Trades", href: "/trades", badge: null },
];

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

const formatImportanceLabel = (level?: ImportanceLevel | null) => {
  if (!level) return "Scored";
  return `${level.charAt(0).toUpperCase()}${level.slice(1)}`;
};

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

const EventAIMetadata = ({ event, compact = false }: { event: AIAnnotatedEvent; compact?: boolean }) => {
  const hasImportance = !!event.importance_level || typeof event.importance_score === "number";

  return (
    <div className={cn("space-y-2", compact && "mt-3")}>
      <div className="flex flex-wrap gap-2">
        {hasImportance && (
          <span className={getImportanceBadgeClass(event.importance_level)}>
            {formatImportanceLabel(event.importance_level)} Importance
            {typeof event.importance_score === "number" ? ` • ${event.importance_score}/100` : ""}
          </span>
        )}
        <span className={cn(
          "text-[10px] px-2 py-0.5 rounded-full border font-medium",
          event.ai_analyzed
            ? "bg-cyan-500/10 text-cyan-300 border-cyan-500/20"
            : "bg-gray-700/50 text-gray-400 border-gray-600"
        )}>
          {event.ai_analyzed ? `${formatAIModelLabel(event.ai_model)} AI` : "Fallback Analysis"}
        </span>
        {typeof event.confidence === "number" && (
          <span className="text-[10px] px-2 py-0.5 rounded-full border font-medium bg-blue-500/10 text-blue-300 border-blue-500/20">
            Confidence • {event.confidence}%
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

const TimeAgo = ({ timestamp }: { timestamp: string }) => {
  const [timeAgo, setTimeAgo] = useState<string>("");

  useEffect(() => {
    const update = () => {
      const date = new Date(timestamp);
      const now = new Date();
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (diffInSeconds < 60) setTimeAgo(`${diffInSeconds}s ago`);
      else if (diffInSeconds < 3600) setTimeAgo(`${Math.floor(diffInSeconds / 60)}m ago`);
      else if (diffInSeconds < 86400) setTimeAgo(`${Math.floor(diffInSeconds / 3600)}h ago`);
      else setTimeAgo(`${Math.floor(diffInSeconds / 86400)}d ago`);
    };

    update();
    const interval = setInterval(update, 60000);
    return () => clearInterval(interval);
  }, [timestamp]);

  return <span className="text-xs text-gray-500">{timeAgo || "..."}</span>;
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
          {news.urgency === "breaking" ? "BREAKING" : `${news.urgency.toUpperCase()} IMPACT`}
        </span>
        <span className="text-xs text-gray-500 font-mono">
          {format(new Date(news.timestamp), "HH:mm")}
        </span>
        <span className="text-xs text-gray-600">•</span>
        <TimeAgo timestamp={news.timestamp} />
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
  const { markers: newsMarkers } = useNewsMarkers(selectedSymbol, 72, 5);
  const [isEconomicModalOpen, setIsEconomicModalOpen] = useState(false);
  const [isEarningsModalOpen, setIsEarningsModalOpen] = useState(false);
  const [loadingEventDetail, setLoadingEventDetail] = useState(false);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const chartDataRef = useRef<ChartCandle[]>([]);
  const newsRef = useRef<EnrichedNews[]>([]);
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

  // Initialize chart
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
        new Date(timestamp * 1000),
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
        new Date(realTimestamp * 1000),
        timeframeRef.current === "1d" ? "MMM d" : "MMM d, HH:mm"
      );
    };

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight || 420,
      layout: {
        background: { color: "#0a0a0a" },
        textColor: "#6b7280",
        fontFamily: "Inter, system-ui, sans-serif"
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.03)" },
        horzLines: { color: "rgba(255, 255, 255, 0.03)" }
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "rgba(255, 255, 255, 0.1)", labelBackgroundColor: "#374151" },
        horzLine: { color: "rgba(255, 255, 255, 0.1)", labelBackgroundColor: "#374151" }
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        scaleMargins: { top: 0.1, bottom: 0.1 }
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

    // Click handler for candles - AKILLI HABER EŞLEŞTİRME
    chart.subscribeClick((param) => {
      if (!param.time) {
        return;
      }

      const candle = findTimelineChartCandle(param.time as number | string, chartDataRef.current);

      if (candle) {
        const priceChange = ((candle.close - candle.open) / candle.open) * 100;

        // Önce temel bilgileri göster (haberler loading olacak)
        setSelectedCandleNews({
          candle,
          news: [],
          hasBigMove: Math.abs(priceChange) > 1.5,
          moveType: priceChange > 0 ? 'up' : priceChange < 0 ? 'down' : 'none',
          movePercent: priceChange,
          isLoadingNews: true,
        });

        // Fetch AI explanation for big moves
        if (Math.abs(priceChange) > 1.0) {
          fetchAIExplanationRef.current(candle);
        } else {
          setAiExplanation(null);
        }

        const currentSymbol = selectedSymbolRef.current;
        const currentTimeframe = timeframeRef.current;

        // AKILLI HABER EŞLEŞTİRME - Backend API'sini çağır
        fetchNewsForCandle(
          currentSymbol,
          new Date(candle.actualTimestamp * 1000).toISOString(),
          candle.open,
          candle.close,
          candle.high,
          candle.low,
          currentTimeframe,
          currentLocaleRef.current
        ).then(response => {
          setSelectedCandleNews(prev => prev ? {
            ...prev,
            news: response.news || [],
            isLoadingNews: false,
          } : null);
        }).catch(error => {
          console.error("[CandleClick] Error fetching matched news:", error);
          // Fallback: Basit zaman bazlı eşleştirme
          const minutes = TIMEFRAME_TO_MINUTES[currentTimeframe] || 60;
          const candleStart = subMinutes(new Date(candle.actualTimestamp * 1000), minutes / 2);
          const candleEnd = addMinutes(new Date(candle.actualTimestamp * 1000), minutes / 2);

          const relatedNews = newsRef.current.filter(n => {
            const newsTime = new Date(n.timestamp);
            return isWithinInterval(newsTime, { start: candleStart, end: candleEnd });
          }).slice(0, 5); // Max 5

          setSelectedCandleNews(prev => prev ? {
            ...prev,
            news: relatedNews as any,
            isLoadingNews: false,
          } : null);
        });
      }
    });

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
      candlestickSeriesRef.current = null;
      chartRef.current = null;
      chart.remove();
    };
  }, [mounted]);

  // Update chart data
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
      return;
    }

    candlestickSeriesRef.current.setMarkers(buildMappedChartMarkers(newsMarkers, chartData) as any);
  }, [chartData, newsMarkers]);

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
          headline: newsItem.headline_en || newsItem.headline || '',
          headline_tr: newsItem.summary_tr || newsItem.analysis_tr || newsItem.headline || newsItem.headline_en || '',
          content: newsItem.analysis_en || newsItem.summary_en || newsItem.headline_en || newsItem.headline || '',
          content_tr: newsItem.analysis_tr || newsItem.summary_tr || newsItem.reasoning_tr || newsItem.headline || newsItem.headline_en || '',
          summary_en: newsItem.summary_en || newsItem.headline_en || newsItem.headline || '',
          summary_tr: newsItem.summary_tr || newsItem.analysis_tr || newsItem.reasoning_tr || newsItem.headline || newsItem.headline_en || '',
          analysis_en: newsItem.analysis_en || newsItem.summary_en || newsItem.headline_en || newsItem.headline || '',
          analysis_tr: newsItem.analysis_tr || newsItem.reasoning_tr || newsItem.summary_tr || newsItem.headline || newsItem.headline_en || '',
          category: 'matched_news',
          url: newsItem.url || '',
          impacts: [{
            symbol: selectedSymbol,
            direction: normalizeImpactDirection(newsItem.direction),
            score: newsItem.score || 0,
            confidence: newsItem.ai_match_confidence ?? newsItem.relevance_score ?? 0.5,
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
          aiConfidence: Math.round((newsItem.ai_match_confidence ?? newsItem.relevance_score ?? 0.5) * 100),
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
                {selectedSymbol} - {currentSymbol?.name} Market Analysis
              </h1>
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-green-500/10 border-green-500/30">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-500 uppercase">Swing Trading</span>
                    <span className="text-sm font-semibold text-green-400 flex items-center gap-1">
                      Bullish <TrendingUp className="w-4 h-4" />
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-red-500/10 border-red-500/30">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-500 uppercase">Day Trading</span>
                    <span className="text-sm font-semibold text-red-400 flex items-center gap-1">
                      Slightly Bearish <TrendingDown className="w-4 h-4" />
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-purple-500/10 border-purple-500/30">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-gray-500 uppercase">News Feed</span>
                    <span className="text-sm font-semibold text-purple-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                      High Impact
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
                    <span className="text-xs text-gray-400">Current:</span>
                    <span className="text-sm text-white ml-2 font-mono">${currentSymbol.price.toFixed(2)}</span>
                  </div>
                  <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                    <span className="text-xs text-gray-400">Pullback:</span>
                    <span className="text-sm text-white ml-2 font-mono">${(currentSymbol.price * 1.02).toFixed(2)}</span>
                  </div>
                  <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                    <span className="text-xs text-gray-400">Target:</span>
                    <span className="text-sm text-red-400 ml-2 font-mono">${(currentSymbol.price * 0.98).toFixed(2)}</span>
                  </div>
                </div>
              )}

              {/* Loading / Error */}
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                    <span className="text-sm text-gray-500">Loading chart...</span>
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
                      Retry
                    </button>
                  </div>
                </div>
              )}

              {/* Chart container */}
              <div
                ref={chartContainerRef}
                className="w-full h-full"
                style={{ visibility: loading || error ? 'hidden' : 'visible' }}
              />

              {/* Candle click tip */}
              {!loading && !error && !selectedCandleNews && chartData.length > 0 && (
                <div className="absolute bottom-16 left-4 z-10 bg-gray-900/80 backdrop-blur px-3 py-2 rounded-lg border border-gray-800 text-xs text-gray-400">
                  💡 Click any candle to inspect related catalysts
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
                      <p className="text-xs text-gray-500">Candle Analysis</p>
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
                        <span className="text-xs text-gray-500">Open</span>
                        <p className="font-mono text-sm">${selectedCandleNews.candle.open.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">Close</span>
                        <p className="font-mono text-sm">${selectedCandleNews.candle.close.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">High</span>
                        <p className="font-mono text-sm text-green-400">${selectedCandleNews.candle.high.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-3">
                        <span className="text-xs text-gray-500">Low</span>
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
                            Big {selectedCandleNews.moveType === "up" ? "Surge" : "Drop"}: {selectedCandleNews.movePercent.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* AI Explanation */}
                    {(loadingExplanation || aiExplanation) && (
                      <div className="p-3 rounded-lg border bg-purple-500/10 border-purple-500/30">
                        <div className="flex items-center gap-2 mb-2">
                          <Brain className="w-4 h-4 text-purple-400" />
                          <span className="font-semibold text-purple-400">AI Analysis</span>
                        </div>
                        {loadingExplanation ? (
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                            <span className="text-xs text-gray-400">Analyzing price movement...</span>
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
                            Related Catalysts
                            <span className="w-3 h-3 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                          </span>
                        ) : (
                          <>
                            Related Catalysts
                            <span className="text-xs font-normal text-gray-400">
                              ({selectedCandleNews.news.length}
                              {selectedCandleNews.news.some(n => n.match_quality !== 'context') && ' matched'})
                            </span>
                          </>
                        )}
                      </h4>

                      {selectedCandleNews.isLoadingNews ? (
                        <div className="flex items-center justify-center py-4">
                          <span className="text-xs text-gray-500">Finding relevant catalysts...</span>
                        </div>
                      ) : selectedCandleNews.news.length === 0 ? (
                        <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
                          <p className="text-xs text-gray-500">
                            {selectedCandleNews.hasBigMove
                              ? "No strong catalyst was found for this significant price move."
                              : "No nearby catalyst was matched to this candle."
                            }
                          </p>
                          {selectedCandleNews.hasBigMove && (
                            <p className="text-[10px] text-gray-600 mt-1">
                              This move may have been driven by positioning, liquidity, or purely technical flow.
                            </p>
                          )}
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {selectedCandleNews.news.map((n, i) => (
                            <div
                              key={i}
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
                              <div className="flex items-center gap-2 mt-1.5">
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300">
                                  {getCatalystBadge(n, currentLocale)}
                                </span>
                                <span className={cn(
                                  "text-[10px] px-1.5 py-0.5 rounded",
                                  n.urgency === 'breaking' ? "bg-red-500/20 text-red-400" :
                                    n.urgency === 'high' ? "bg-orange-500/20 text-orange-400" :
                                      "bg-gray-500/20 text-gray-400"
                                )}>
                                  {n.urgency}
                                </span>
                                <span className={cn(
                                  "text-[10px] px-1.5 py-0.5 rounded",
                                  n.direction === 'bullish' ? "bg-green-500/20 text-green-400" :
                                    n.direction === 'bearish' ? "bg-red-500/20 text-red-400" :
                                      "bg-gray-500/20 text-gray-400"
                                )}>
                                  {n.direction} {n.score}/10
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
                <span>News</span>
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
                <span>Economic</span>
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
                <span>Earnings</span>
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
                          ? "News feed fresh"
                          : newsStatus === "mock"
                            ? "Showing manual test news"
                            : newsStatus === "error"
                              ? "News feed unavailable"
                              : "News feed stale or empty"
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
                          {filter.charAt(0).toUpperCase() + filter.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {news.length === 0 && !newsLoading && (
                      <button
                        onClick={() => { fetchNews(true); }}
                        className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-md text-[10px] hover:bg-purple-500/30 transition-colors"
                        title="Load test news data"
                      >
                        🧪 Test
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
                    <button onClick={() => fetchNews(false)} className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-md">
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
                    {newsStatusMessage || (newsStatus === "empty" ? "No news found." : "News feed status changed.")}
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
                        {hasHiddenNewsByFilter ? "No news matches the current filter" : "No news available"}
                      </p>
                      <p className="text-gray-600 text-xs mb-4 px-4">
                        {hasHiddenNewsByFilter
                          ? "DeepSeek-analyzed news exists, but the current filter is hiding it. Switch to All to see the full feed."
                          : "Supabase enriched_news table may be empty or API is not responding"}
                      </p>
                      {hasHiddenNewsByFilter ? (
                        <button
                          onClick={() => setNewsFilter("all")}
                          className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                        >
                          Show all news
                        </button>
                      ) : (
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => { fetchNews(false); }}
                            className="px-4 py-2 bg-gray-800 text-white rounded-lg text-sm hover:bg-gray-700 transition-colors"
                          >
                            Retry API
                          </button>
                          <button
                            onClick={() => { fetchNews(true); }}
                            className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                          >
                            🧪 Load Test News
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
                    Economic Events
                  </h3>
                  <button
                    onClick={() => fetchEconomicCalendar()}
                    className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-md"
                    title="Refresh"
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
                      <p className="text-gray-500 text-sm">No economic events scheduled</p>
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
                                {event.impact}
                              </span>
                              <span className="text-xs text-gray-500 font-mono">
                                {format(new Date(event.timestamp), "MMM d, HH:mm")}
                              </span>
                            </div>
                            <span className={getDirectionBadgeClass(event.predicted_direction)}>
                              {event.predicted_direction === "bullish" && "📈 Bullish"}
                              {event.predicted_direction === "bearish" && "📉 Bearish"}
                              {event.predicted_direction === "neutral" && "➖ Neutral"}
                              {event.predicted_direction === "volatile" && "⚡ Volatile"}
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
                                <span className="text-gray-500">Prev: <span className="text-gray-300 font-mono">{event.previous}</span></span>
                              )}
                              {event.forecast && (
                                <span className="text-gray-500">Exp: <span className="text-amber-400 font-mono">{event.forecast}</span></span>
                              )}
                            </div>
                          )}
                          <EventAIMetadata event={event} compact />
                          {/* Click hint */}
                          <div className="absolute bottom-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="text-[10px] text-gray-600">Click for details →</span>
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
                    Earnings Reports
                  </h3>
                  <button
                    onClick={() => fetchEarningsCalendar()}
                    className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded-md"
                    title="Refresh"
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
                      <p className="text-gray-500 text-sm">No earnings reports scheduled</p>
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
                                {event.time === "after_market" ? "After" : "Pre"}
                              </span>
                            </div>
                            <span className={getDirectionBadgeClass(event.predicted_direction)}>
                              {event.predicted_direction === "bullish" && "📈 Bull"}
                              {event.predicted_direction === "bearish" && "📉 Bear"}
                              {event.predicted_direction === "neutral" && "➖ Neutral"}
                              {event.predicted_direction === "volatile" && "⚡ Volatile"}
                            </span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-2 tracking-wide">
                            {event.company}
                          </h4>
                          <div className="flex items-center gap-4 text-[11px]">
                            {event.eps_forecast && (
                              <span className="text-gray-500">
                                EPS: <span className="text-gray-300 font-mono">{event.eps_forecast}</span>
                              </span>
                            )}
                            {event.revenue_forecast && (
                              <span className="text-gray-500">
                                Rev: <span className="text-gray-300 font-mono">{event.revenue_forecast}</span>
                              </span>
                            )}
                          </div>
                          <EventAIMetadata event={event} compact />
                          <p className="text-[10px] text-gray-600 mt-2 uppercase tracking-wider">{event.sector}</p>
                          {/* Click hint */}
                          <div className="absolute bottom-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="text-[10px] text-gray-600">Click for details →</span>
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
                  <h3 className="font-semibold text-white">Economic Event</h3>
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
                  {selectedEconomicEvent.impact} Impact
                </span>
                <span className="text-xs text-gray-500">{selectedEconomicEvent.currency}</span>
              </div>
              <h2 className="text-xl font-bold text-white mb-4">
                {currentLocale === "tr" && selectedEconomicEvent.title_tr ? selectedEconomicEvent.title_tr : selectedEconomicEvent.title}
              </h2>

              <EventAIMetadata event={selectedEconomicEvent} />

              {(selectedEconomicEvent.previous || selectedEconomicEvent.forecast) && (
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {selectedEconomicEvent.previous && (
                    <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Previous</p>
                      <p className="text-lg font-mono text-gray-300">{selectedEconomicEvent.previous}</p>
                    </div>
                  )}
                  {selectedEconomicEvent.forecast && (
                    <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-900/40">
                      <p className="text-[10px] uppercase tracking-wider text-amber-500/70 mb-1">Forecast</p>
                      <p className="text-lg font-mono text-amber-400">{selectedEconomicEvent.forecast}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-amber-500" />
                    Expected Direction
                  </h4>
                  <p className={cn("text-sm p-3 rounded-xl border", getDirectionBadgeClass(selectedEconomicEvent.predicted_direction))}>
                    {selectedEconomicEvent.predicted_direction === "bullish" && "📈 Bullish - Expected positive market reaction"}
                    {selectedEconomicEvent.predicted_direction === "bearish" && "📉 Bearish - Expected negative market reaction"}
                    {selectedEconomicEvent.predicted_direction === "neutral" && "➖ Neutral - Limited market impact expected"}
                    {selectedEconomicEvent.predicted_direction === "volatile" && "⚡ Volatile - Expect sharp two-way price swings"}
                  </p>
                </div>

                {selectedEconomicEvent.impact_analysis && (
                  <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/20 to-transparent border border-cyan-900/30">
                    <h4 className="text-sm font-semibold text-cyan-300 mb-2 flex items-center gap-2">
                      <Brain className="w-4 h-4" />
                      DeepSeek Analysis
                    </h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {currentLocale === "tr" && selectedEconomicEvent.impact_analysis_tr
                        ? selectedEconomicEvent.impact_analysis_tr
                        : selectedEconomicEvent.impact_analysis}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">Description</h4>
                  <p className="text-sm text-gray-400 leading-relaxed">
                    {currentLocale === "tr" && selectedEconomicEvent.description_tr ? selectedEconomicEvent.description_tr : selectedEconomicEvent.description}
                  </p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">Affected Symbols</h4>
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
                    <h4 className="text-sm font-semibold text-amber-400 mb-2">Why It Matters</h4>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {currentLocale === "tr" && selectedEconomicEvent.why_it_matters_tr ? selectedEconomicEvent.why_it_matters_tr : selectedEconomicEvent.why_it_matters}
                    </p>
                  </div>
                )}

                {/* SCENARIO VARIATIONS */}
                <div className="mt-6 border-t border-gray-800 pt-6">
                  <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    Scenario Variations
                    {loadingEventDetail && (
                      <span className="ml-2 text-[10px] text-amber-400 animate-pulse">Analyzing with AI...</span>
                    )}
                  </h4>
                  {loadingEventDetail && !selectedEconomicEvent.scenarios && (
                    <div className="space-y-3">
                      <div className="h-24 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                      <div className="h-24 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                    </div>
                  )}
                  {!loadingEventDetail && !selectedEconomicEvent.scenarios && (
                    <p className="text-xs text-gray-500 italic">Scenario analysis unavailable. Check API key or try again later.</p>
                  )}


                  {/* Better Than Expected */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-green-950/40 to-transparent border border-green-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs">🟢</span>
                      <h5 className="text-sm font-semibold text-green-400">Better Than Expected</h5>
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
                        <span className="text-gray-500 w-20">First 5 min</span>
                        <span className="text-green-400">{selectedEconomicEvent.scenarios?.better_than_expected?.first_5min || "Sharp initial move"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-green-400">{selectedEconomicEvent.scenarios?.better_than_expected?.first_hour || "Momentum continues"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Day close</span>
                        <span className="text-amber-400">{selectedEconomicEvent.scenarios?.better_than_expected?.day_close || "Watch for profit taking"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Next day</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.better_than_expected?.next_day || "Follow-through or reversal"}</span>
                      </div>
                    </div>
                  </div>

                  {/* Worse Than Expected */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-transparent border border-red-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs">🔴</span>
                      <h5 className="text-sm font-semibold text-red-400">Worse Than Expected</h5>
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
                        <span className="text-gray-500 w-20">First 5 min</span>
                        <span className="text-red-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.first_5min || "Sharp initial move"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-red-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.first_hour || "Momentum continues"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Day close</span>
                        <span className="text-amber-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.day_close || "Watch for reversals"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Next day</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.worse_than_expected?.next_day || "Mean reversion possible"}</span>
                      </div>
                    </div>
                  </div>

                  {/* As Expected */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-gray-900/50 to-transparent border border-gray-700/50">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 text-xs">⚪</span>
                      <h5 className="text-sm font-semibold text-gray-400">As Expected</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First 5 min</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.as_expected?.first_5min || "Minimal movement ±0.1%"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.as_expected?.first_hour || "Range-bound, look for other catalysts"}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Rest of day</span>
                        <span className="text-gray-400">{selectedEconomicEvent.scenarios?.as_expected?.day_close || "Focus shifts to technicals and other news"}</span>
                      </div>
                    </div>
                  </div>

                  {/* Trading Tips */}
                  <div className="mt-4 p-3 rounded-lg bg-blue-950/30 border border-blue-900/30">
                    <p className="text-[11px] text-blue-400">
                      <span className="font-semibold">💡 Pro Tip:</span> {selectedEconomicEvent.trading_tips || "Wait 5 minutes after release for initial volatility to settle. Use limit orders, not market orders. Watch for reversals after the first hour."}
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
                    <h3 className="font-semibold text-white">Earnings Report</h3>
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
                    {selectedEarningsEvent.time === "after_market" ? "After Market" : "Pre Market"}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-white mb-2">{selectedEarningsEvent.company}</h2>
                <p className="text-sm text-gray-500 mb-6">{selectedEarningsEvent.sector}</p>

                <EventAIMetadata event={selectedEarningsEvent} />

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                    <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">EPS Estimate</p>
                    <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.eps_forecast || "N/A"}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                    <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Revenue Estimate</p>
                    <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.revenue_forecast || "N/A"}</p>
                  </div>
                  {selectedEarningsEvent.previous_eps && (
                    <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Previous EPS</p>
                      <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.previous_eps}</p>
                    </div>
                  )}
                  {selectedEarningsEvent.previous_revenue && (
                    <div className="p-3 rounded-xl bg-gray-900/50 border border-gray-800">
                      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Previous Revenue</p>
                      <p className="text-lg font-mono text-gray-300">{selectedEarningsEvent.previous_revenue}</p>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-blue-500" />
                      AI Prediction
                    </h4>
                    <div className="flex items-center gap-4">
                      <p className={cn("text-sm px-4 py-2 rounded-xl border flex-1", getDirectionBadgeClass(selectedEarningsEvent.predicted_direction))}>
                        {selectedEarningsEvent.predicted_direction === "bullish" && "📈 Beat Expected"}
                        {selectedEarningsEvent.predicted_direction === "bearish" && "📉 Miss Expected"}
                        {selectedEarningsEvent.predicted_direction === "neutral" && "➖ In Line Expected"}
                        {selectedEarningsEvent.predicted_direction === "volatile" && "⚡ High Volatility Expected"}
                      </p>
                      <div className="text-center">
                        <p className="text-2xl font-mono text-blue-400">{selectedEarningsEvent.confidence}%</p>
                        <p className="text-[10px] text-gray-500">Confidence</p>
                      </div>
                    </div>
                  </div>

                  {selectedEarningsEvent.affected_symbols.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Affected Symbols</h4>
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
                      <h4 className="text-sm font-semibold text-blue-400 mb-2">AI Analysis</h4>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        {currentLocale === "tr" && selectedEarningsEvent.analysis_tr ? selectedEarningsEvent.analysis_tr : selectedEarningsEvent.analysis}
                      </p>
                    </div>
                  )}

                  {selectedEarningsEvent.key_metrics.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Key Metrics to Watch</h4>
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
                      Scenario Variations
                    </h4>

                    {/* Beat Scenario */}
                    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-green-950/40 to-transparent border border-green-900/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs">✅</span>
                        <h5 className="text-sm font-semibold text-green-400">Beat (EPS & Revenue)</h5>
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
                          <span className="text-gray-500 w-20">Pre-market</span>
                          <span className="text-green-400">{selectedEarningsEvent.scenarios?.beat?.pre_market || `Stock +3-5% • ${selectedEarningsEvent.ticker} calls spike`}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">Open</span>
                          <span className="text-green-400">{selectedEarningsEvent.scenarios?.beat?.open || "Gap up, momentum buyers enter"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">First hour</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.beat?.first_hour || "Watch for profit taking at highs"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">Sector</span>
                          <span className="text-blue-400">{selectedEarningsEvent.scenarios?.beat?.sector_effect || `${selectedEarningsEvent.sector} peers likely rally`}</span>
                        </div>
                      </div>
                    </div>

                    {/* Miss Scenario */}
                    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-transparent border border-red-900/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs">❌</span>
                        <h5 className="text-sm font-semibold text-red-400">Miss (EPS or Revenue)</h5>
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
                          <span className="text-gray-500 w-20">Pre-market</span>
                          <span className="text-red-400">{selectedEarningsEvent.scenarios?.miss?.pre_market || `Stock -4-7% • Put volume surges`}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">Open</span>
                          <span className="text-red-400">{selectedEarningsEvent.scenarios?.miss?.open || "Gap down, stop losses trigger"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">First hour</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.miss?.first_hour || "Dead cat bounce possible, then fade"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">Sector</span>
                          <span className="text-red-400">{selectedEarningsEvent.scenarios?.miss?.sector_effect || `${selectedEarningsEvent.sector} peers may decline`}</span>
                        </div>
                      </div>
                    </div>

                    {/* Mixed Scenario */}
                    <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-transparent border border-amber-900/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-400 text-xs">⚠️</span>
                        <h5 className="text-sm font-semibold text-amber-400">Mixed (Beat EPS, Miss Revenue or vice versa)</h5>
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
                          <span className="text-gray-500 w-20">Pre-market</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.mixed?.pre_market || "Volatile ±2% • Direction unclear"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">Guidance</span>
                          <span className="text-amber-400">{selectedEarningsEvent.scenarios?.mixed?.guidance_importance || "Forward guidance becomes key driver"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">First hour</span>
                          <span className="text-gray-400">{selectedEarningsEvent.scenarios?.mixed?.trading_approach || "Wait for conference call clarity"}</span>
                        </div>
                      </div>
                    </div>

                    {/* In Line */}
                    <div className="p-4 rounded-xl bg-gradient-to-r from-gray-900/50 to-transparent border border-gray-700/50">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 text-xs">➖</span>
                        <h5 className="text-sm font-semibold text-gray-400">In Line (Meets Expectations)</h5>
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
                          <span className="text-gray-500 w-20">Pre-market</span>
                          <span className="text-gray-400">{selectedEarningsEvent.scenarios?.inline?.pre_market || "±1% move • Options IV crush likely"}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="text-gray-500 w-20">Guidance</span>
                          <span className="text-gray-400">{selectedEarningsEvent.scenarios?.inline?.guidance_focus || "Stock direction depends on forward outlook"}</span>
                        </div>
                      </div>
                    </div>

                    {/* Trading Tips */}
                    <div className="mt-4 p-3 rounded-lg bg-purple-950/30 border border-purple-900/30">
                      <p className="text-[11px] text-purple-400">
                        <span className="font-semibold">💡 Pro Tip:</span> {selectedEarningsEvent.trading_tips || `For ${selectedEarningsEvent.time === "after_market" ? "after-hours" : "pre-market"} earnings, liquidity is lower and spreads wider. Consider waiting for regular session open for better fills. Watch for post-earnings drift in following days.`}
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
