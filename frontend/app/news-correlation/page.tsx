"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time, type CandlestickData } from "lightweight-charts";
import { format, isWithinInterval, subMinutes, addMinutes } from "date-fns";
import { 
  Bell, Star, Wallet, Calendar, FileText, MessageSquare, Newspaper,
  Building2, LineChart, BookOpen, Filter, ChevronLeft, ChevronRight,
  TrendingUp, TrendingDown, Sparkles, Camera, Settings,
  Clock, AlertTriangle, RefreshCw, X, ArrowUp, ArrowDown, Brain,
  Minus, Zap
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetcher } from "@/lib/api";
import Link from "next/link";
import type { EnrichedNews } from "@/types/news-correlation";
import NewsDetailModal from "@/components/NewsDetailModal";

// ==================== TYPES ====================
interface ChartCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  priceChange?: number;
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

interface CandleNews {
  candle: ChartCandle;
  news: EnrichedNews[];
  hasBigMove: boolean;
  moveType: 'up' | 'down' | 'none';
  movePercent: number;
}

// Economic Calendar types (matching backend API)
interface EconomicEvent {
  id: string;
  timestamp: string;
  title: string;
  title_tr: string;
  currency: string;
  impact: "High" | "Medium" | "Low";
  actual?: string;
  forecast?: string;
  previous?: string;
  predicted_direction: "bullish" | "bearish" | "neutral";
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
}

interface EarningsEvent {
  id: string;
  company: string;
  company_tr?: string;
  ticker: string;
  sector: string;
  date: string;
  time: "after_market" | "before_market";
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
  confidence: number;
  predicted_direction: "bullish" | "bearish" | "neutral";
}

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

// Big move thresholds by symbol AND timeframe (percentage)
// Lower thresholds for shorter timeframes
const BIG_MOVE_THRESHOLDS: Record<string, Record<string, number>> = {
  XAUUSD: { "1m": 0.05, "5m": 0.08, "15m": 0.10, "30m": 0.15, "1h": 0.20, "4h": 0.30, "1d": 0.50 },
  NDX:    { "1m": 0.05, "5m": 0.08, "15m": 0.10, "30m": 0.15, "1h": 0.20, "4h": 0.30, "1d": 0.50 },
  DAX:    { "1m": 0.05, "5m": 0.08, "15m": 0.10, "30m": 0.15, "1h": 0.20, "4h": 0.30, "1d": 0.50 },
  USOIL:  { "1m": 0.08, "5m": 0.12, "15m": 0.15, "30m": 0.20, "1h": 0.30, "4h": 0.50, "1d": 1.00 },
  VIX:    { "1m": 0.50, "5m": 0.80, "15m": 1.00, "30m": 1.50, "1h": 2.00, "4h": 3.00, "1d": 5.00 },
  DXY:    { "1m": 0.03, "5m": 0.05, "15m": 0.08, "30m": 0.10, "1h": 0.15, "4h": 0.20, "1d": 0.30 },
};

const TIMEFRAMES = [
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "30m", label: "30m" },
  { value: "1h", label: "1h" },
  { value: "4h", label: "4h" },
  { value: "1d", label: "1D" },
];

const sidebarItems = [
  { icon: Bell, label: "Alerts", href: "/alerts", badge: 3 },
  { icon: Star, label: "Watchlist", href: "/watchlist", badge: null },
  { icon: Wallet, label: "Smart Trades", href: "/news-correlation", badge: null, active: true },
  { icon: Calendar, label: "Economic Calendar", href: "/calendar", badge: null },
  { icon: FileText, label: "News Analysis", href: "/news-analysis", badge: null },
  { icon: MessageSquare, label: "Chat AI", href: "/chat", badge: null },
  { icon: Newspaper, label: "Research Reports", href: "/research", badge: null },
  { icon: BookOpen, label: "Docs", href: "/docs", badge: null },
  { icon: Building2, label: "Brokers", href: "/brokers", badge: null },
  { icon: LineChart, label: "My Trades", href: "/trades", badge: null },
];

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
  
  // Get localized content
  const displayHeadline = locale === "tr" && news.headline_tr ? news.headline_tr : news.headline;
  const displayContent = locale === "tr" && news.content_tr ? news.content_tr : (news.content || news.headline);
  
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
          <span key={idx} className={cn(
            "inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border",
            impact.direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
            impact.direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
            impact.direction === "neutral" && "bg-gray-700/50 text-gray-400 border-gray-600"
          )}>
            {impact.direction === "bullish" && <TrendingUp className="w-3 h-3" />}
            {impact.direction === "bearish" && <TrendingDown className="w-3 h-3" />}
            {impact.symbol} {impact.direction === "bullish" ? "↑" : impact.direction === "bearish" ? "↓" : "→"}
          </span>
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
  const [selectedSymbol, setSelectedSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [symbols, setSymbols] = useState<SymbolData[]>(INITIAL_SYMBOLS);
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsFilter, setNewsFilter] = useState<"all" | "popular" | "high">("high");
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
  const [isEconomicModalOpen, setIsEconomicModalOpen] = useState(false);
  const [isEarningsModalOpen, setIsEarningsModalOpen] = useState(false);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Mount effect
  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch chart data
  const fetchChartData = useCallback(async () => {
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
      const apiSymbol = symbolMap[selectedSymbol] || selectedSymbol;

      const response = await fetcher<OHLCVResponse>(
        `/api/data/ohlcv?symbol=${apiSymbol}&timeframe=${timeframe}&limit=200`
      );

      if (response?.data && Array.isArray(response.data) && response.data.length > 0) {
        // Sort candles by timestamp (ascending) and remove duplicates
        const sortedData = [...response.data].sort((a, b) => a.timestamp - b.timestamp);
        
        // Remove duplicates by timestamp
        const uniqueData = sortedData.filter((row, index, self) => 
          index === self.findIndex(r => r.timestamp === row.timestamp)
        );
        
        const processedCandles: ChartCandle[] = uniqueData.map((row) => {
          // Handle both ms and seconds timestamp formats
          const timestamp = row.timestamp;
          // If timestamp is in milliseconds (13 digits), convert to seconds (10 digits)
          const timeInSeconds = timestamp > 1_000_000_000_000 ? Math.floor(timestamp / 1000) : timestamp;
          const priceChange = ((row.close - row.open) / row.open) * 100;
          return {
            time: timeInSeconds,
            open: row.open,
            high: row.high,
            low: row.low,
            close: row.close,
            volume: row.volume,
            priceChange,
          };
        });
        
        console.log(`[Chart] Loaded ${processedCandles.length} candles for ${selectedSymbol}`);
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
      setLoading(false);
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
      
      // Use mock data if requested or if API fails
      if (useMock) {
        console.log("[News] Using mock data for testing");
        setNews(getMockNews());
        setNewsLoading(false);
        return;
      }
      
      // Try multiple strategies to fetch news
      let newsData: EnrichedNews[] = [];
      
      // Strategy 1: Fetch all news (no symbol filter for maximum results)
      try {
        const response = await fetcher<EnrichedNews[] | { success: boolean; data: EnrichedNews[] }>(
          `/api/rss/news?limit=100&hours=72&skip_ai_filtered=false`
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
          const response = await fetcher<EnrichedNews[] | { success: boolean; data: EnrichedNews[] }>(
            `/api/rss/news?limit=100&hours=168&skip_ai_filtered=false`
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
      
      // If still no news, use mock data automatically
      if (newsData.length === 0) {
        console.log("[News] API returned empty, falling back to mock data");
        newsData = getMockNews();
      }
      
      // Filter news for selected symbol if we have news
      if (newsData.length > 0 && selectedSymbol) {
        const symbolMappings: Record<string, string[]> = {
          'XAUUSD': ['XAUUSD', 'XAU/USD', 'GOLD', 'GC'],
          'NDX': ['NDX', 'NASDAQ', 'IXIC', 'NDX.INDX'],
          'DAX': ['DAX', 'GDAXI', 'GDAXI.INDX', 'DE40'],
          'USOIL': ['USOIL', 'WTI', 'CL', 'USOIL.FOREX', 'OIL'],
          'VIX': ['VIX', 'VIX.INDX', 'VOLATILITY'],
          'DXY': ['DXY', 'DXY.INDX', 'DOLLAR', 'USD'],
        };
        
        const relevantSymbols = symbolMappings[selectedSymbol] || [selectedSymbol];
        
        const filtered = newsData.filter((item: EnrichedNews) => {
          // Check if news impacts contain relevant symbol
          if (item.impacts && item.impacts.length > 0) {
            return item.impacts.some((impact: any) => 
              relevantSymbols.some(sym => 
                impact.symbol?.toUpperCase() === sym.toUpperCase() ||
                impact.symbol === '*'
              )
            );
          }
          // If no impacts, include all news (show everything)
          return true;
        });
        
        // If filtered is empty but we have news, show all news
        setNews(filtered.length > 0 ? filtered : newsData);
      } else {
        setNews(newsData);
      }
    } catch (err) {
      console.error("Error fetching news:", err);
      // On error, use mock data
      setNews(getMockNews());
    } finally {
      setNewsLoading(false);
    }
  }, [selectedSymbol, getMockNews]);

  // Fetch economic calendar
  const fetchEconomicCalendar = useCallback(async () => {
    try {
      setEconomicLoading(true);
      const response = await fetcher<{ success: boolean; events: EconomicEvent[] }>(
        `/api/calendar/economic?days=14`
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
  }, []);

  // Fetch earnings calendar
  const fetchEarningsCalendar = useCallback(async () => {
    try {
      setEarningsLoading(true);
      const response = await fetcher<{ success: boolean; earnings: EarningsEvent[] }>(
        `/api/calendar/earnings?days=14`
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
  }, []);

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
        const wsUrl = `wss://upbeat-flow-production.up.railway.app/ws/all`;
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

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current || !mounted) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
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
      timeScale: { 
        borderColor: "rgba(255, 255, 255, 0.1)",
        timeVisible: true,
        secondsVisible: false 
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

    // Click handler for candles
    chart.subscribeClick((param) => {
      if (param.time && candlestickSeries) {
        const time = param.time as number;
        const tf = TIMEFRAMES.find(t => t.value === timeframe);
        const minutes = tf ? { "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440 }[tf.value] || 60 : 60;
        
        const candle = chartData.find(c => c.time === time);
        if (candle) {
          const candleStart = subMinutes(new Date(candle.time * 1000), minutes / 2);
          const candleEnd = addMinutes(new Date(candle.time * 1000), minutes / 2);
          
          const relatedNews = news.filter(n => {
            const newsTime = new Date(n.timestamp);
            return isWithinInterval(newsTime, { start: candleStart, end: candleEnd });
          });

          const priceChange = ((candle.close - candle.open) / candle.open) * 100;
          
          setSelectedCandleNews({
            candle,
            news: relatedNews,
            hasBigMove: Math.abs(priceChange) > 1.5,
            moveType: priceChange > 0 ? 'up' : priceChange < 0 ? 'down' : 'none',
            movePercent: priceChange,
          });
          
          // Fetch AI explanation for big moves
          if (Math.abs(priceChange) > 1.0) {
            fetchAIExplanation(candle);
          } else {
            setAiExplanation(null);
          }
        }
      }
    });

    candlestickSeriesRef.current = candlestickSeries;
    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);
    return () => { 
      window.removeEventListener("resize", handleResize); 
      chart.remove(); 
    };
  }, [chartData, news, timeframe, mounted]);

  // Update chart data
  useEffect(() => {
    if (candlestickSeriesRef.current && chartData.length > 0) {
      const formattedData: CandlestickData<Time>[] = chartData.map(c => ({
        time: c.time as Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }));
      candlestickSeriesRef.current.setData(formattedData);
      
      // NEW ALGORITHM: Only show markers for BIG MOVES with related HIGH/BREAKING news
      const markers: any[] = [];
      const symbolThresholds = BIG_MOVE_THRESHOLDS[selectedSymbol] || BIG_MOVE_THRESHOLDS["NDX"];
      const threshold = symbolThresholds[timeframe as string] || 0.1;
      
      // Find candles with big moves
      const bigMoveCandles = chartData.filter(c => Math.abs(c.priceChange || 0) >= threshold);
      
      bigMoveCandles.forEach(candle => {
        const candleTime = candle.time;
        const candleDate = new Date(candleTime * 1000);
        
        // Look for HIGH/BREAKING news within ±15 minutes of this candle
        const timeWindowMinutes = 15;
        const windowStart = new Date(candleDate.getTime() - timeWindowMinutes * 60000);
        const windowEnd = new Date(candleDate.getTime() + timeWindowMinutes * 60000);
        
        // Find significant news that likely caused this move
        const significantNews = news.filter(n => {
          const newsDate = new Date(n.timestamp);
          const isInTimeWindow = newsDate >= windowStart && newsDate <= windowEnd;
          const isHighImpact = n.urgency === "breaking" || n.urgency === "high";
          const affectsSymbol = n.impacts?.some(imp => {
            const sym = imp.symbol?.toUpperCase();
            return sym === selectedSymbol || 
                   (selectedSymbol === "NDX" && (sym === "NDX" || sym === "NASDAQ")) ||
                   (selectedSymbol === "XAUUSD" && (sym === "XAUUSD" || sym === "XAU" || sym === "GOLD")) ||
                   (selectedSymbol === "DAX" && (sym === "DAX" || sym === "GDAXI")) ||
                   (selectedSymbol === "USOIL" && (sym === "USOIL" || sym === "WTI" || sym === "CL" || sym === "OIL")) ||
                   (selectedSymbol === "VIX" && sym === "VIX") ||
                   (selectedSymbol === "DXY" && (sym === "DXY" || sym === "DOLLAR"));
          });
          
          return isInTimeWindow && isHighImpact && affectsSymbol;
        });
        
        // If we found significant news related to this big move, show the news marker
        if (significantNews.length > 0) {
          const topNews = significantNews[0]; // Show the most significant one
          
          // Add news marker ABOVE the candle
          markers.push({
            time: candleTime as Time,
            position: "aboveBar" as const,
            color: topNews.urgency === "breaking" ? "#ef4444" : "#f97316",
            shape: "arrowDown" as const,
            size: 2,
            text: topNews.urgency === "breaking" ? "!" : "N",
          });
        }
        
        // Always show big move marker BELOW the candle
        markers.push({
          time: candleTime as Time,
          position: (candle.priceChange || 0) > 0 ? "belowBar" as const : "aboveBar" as const,
          color: (candle.priceChange || 0) > 0 ? "#22c55e" : "#ef4444",
          shape: (candle.priceChange || 0) > 0 ? "arrowUp" as const : "arrowDown" as const,
          text: `${Math.abs(candle.priceChange || 0).toFixed(1)}%`,
          size: 2,
        });
      });
      
      candlestickSeriesRef.current.setMarkers(markers);
      chartRef.current?.timeScale().fitContent();
    }
  }, [chartData, news, selectedSymbol]);

  const handleNewsClick = (newsItem: EnrichedNews) => {
    setSelectedNewsForModal(newsItem);
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
          explanation: string;
          related_news: any[];
          confidence: number;
        };
        error?: string;
      }>(`/api/news-correlation/explain-move?symbol=${apiSymbol}&timestamp=${candle.time}&ai_explain=true`);
      
      if (response?.success && response.data) {
        setAiExplanation(response.data.explanation);
      } else {
        setAiExplanation(null);
      }
    } catch (err) {
      console.error("Error fetching AI explanation:", err);
      setAiExplanation(null);
    } finally {
      setLoadingExplanation(false);
    }
  }, [selectedSymbol]);

  const filteredNews = news.filter((n) => {
    if (newsFilter === "all") return true;
    if (newsFilter === "high") return n.urgency === "breaking" || n.urgency === "high";
    return true;
  });

  const currentSymbol = symbols.find(s => s.symbol === selectedSymbol);

  if (!mounted) {
    return <div className="min-h-screen bg-[#0a0a0a]" />;
  }

  return (
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
                {wsConnected && selectedSymbol === sym.symbol && (
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
                  💡 Click any candle to see related news
                </div>
              )}

              {/* Candle info panel */}
              {selectedCandleNews && (
                <div className="absolute top-20 left-4 z-20 w-80 bg-gray-900/95 backdrop-blur-xl border border-gray-700 rounded-xl shadow-2xl overflow-hidden">
                  <div className="flex items-center justify-between p-4 border-b border-gray-800">
                    <div>
                      <h3 className="font-semibold">
                        {format(new Date(selectedCandleNews.candle.time * 1000), "MMM d, HH:mm")}
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
                        Related News ({selectedCandleNews.news.length})
                      </h4>
                      {selectedCandleNews.news.length === 0 ? (
                        <p className="text-xs text-gray-500 italic">No news for this period.</p>
                      ) : (
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {selectedCandleNews.news.map((n, i) => (
                            <div key={i} className="p-2 bg-gray-800/50 rounded-lg text-xs cursor-pointer hover:bg-gray-800" onClick={() => handleNewsClick(n)}>
                              <p className="text-gray-300 line-clamp-2">{n.headline}</p>
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
                    {wsConnected && <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Live connected" />}
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

                {/* News List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {newsLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className="h-32 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                    ))
                  ) : filteredNews.length === 0 ? (
                    <div className="text-center py-12">
                      <Newspaper className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm mb-2">No news available</p>
                      <p className="text-gray-600 text-xs mb-4 px-4">
                        Supabase enriched_news table may be empty or API is not responding
                      </p>
                      <button
                        onClick={() => { fetchNews(true); }}
                        className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                      >
                        🧪 Load Test News
                      </button>
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
                        onClick={() => {
                          setSelectedEconomicEvent(event);
                          setIsEconomicModalOpen(true);
                        }}
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
                            <span className={cn(
                              "text-[10px] px-2 py-0.5 rounded-full border font-medium",
                              event.predicted_direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
                              event.predicted_direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
                              event.predicted_direction === "neutral" && "bg-gray-700/50 text-gray-400 border-gray-600"
                            )}>
                              {event.predicted_direction === "bullish" && "📈 Bullish"}
                              {event.predicted_direction === "bearish" && "📉 Bearish"}
                              {event.predicted_direction === "neutral" && "➖ Neutral"}
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
                        onClick={() => {
                          setSelectedEarningsEvent(event);
                          setIsEarningsModalOpen(true);
                        }}
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
                            <span className={cn(
                              "text-[10px] px-2 py-0.5 rounded-full border font-medium",
                              event.predicted_direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
                              event.predicted_direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
                              event.predicted_direction === "neutral" && "bg-gray-700/50 text-gray-400 border-gray-600"
                            )}>
                              {event.predicted_direction === "bullish" && "📈 Bull"}
                              {event.predicted_direction === "bearish" && "📉 Bear"}
                              {event.predicted_direction === "neutral" && "➖ Neutral"}
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
                            <span className="text-gray-500">
                              AI: <span className="text-blue-400 font-mono">{event.confidence}%</span>
                            </span>
                          </div>
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
                  <p className={cn(
                    "text-sm p-3 rounded-xl border",
                    selectedEconomicEvent.predicted_direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
                    selectedEconomicEvent.predicted_direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
                    selectedEconomicEvent.predicted_direction === "neutral" && "bg-gray-700/30 text-gray-400 border-gray-600"
                  )}>
                    {selectedEconomicEvent.predicted_direction === "bullish" && "📈 Bullish - Expected positive market reaction"}
                    {selectedEconomicEvent.predicted_direction === "bearish" && "📉 Bearish - Expected negative market reaction"}
                    {selectedEconomicEvent.predicted_direction === "neutral" && "➖ Neutral - Limited market impact expected"}
                  </p>
                </div>
                
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
                  </h4>
                  
                  {/* Better Than Expected */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-green-950/40 to-transparent border border-green-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-xs">🟢</span>
                      <h5 className="text-sm font-semibold text-green-400">Better Than Expected</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First 5 min</span>
                        <span className="text-green-400">DXY ↑ 0.3% • XAUUSD ↓ $8</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-green-400">DXY ↑ 0.5% • NDX ↓ 0.4%</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Day close</span>
                        <span className="text-amber-400">Trend continues or reverses based on Fed outlook</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Next day</span>
                        <span className="text-gray-400">Profit taking likely, watch for follow-through</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Worse Than Expected */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-transparent border border-red-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs">🔴</span>
                      <h5 className="text-sm font-semibold text-red-400">Worse Than Expected</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First 5 min</span>
                        <span className="text-red-400">DXY ↓ 0.3% • XAUUSD ↑ $10</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-red-400">DXY ↓ 0.6% • NDX ↑ 0.5%</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Day close</span>
                        <span className="text-amber-400">Dovish Fed expectations boost risk assets</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Next day</span>
                        <span className="text-gray-400">Momentum may fade, watch for reversal signals</span>
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
                        <span className="text-gray-400">Minimal movement ±0.1%</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-gray-400">Range-bound, look for other catalysts</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Rest of day</span>
                        <span className="text-gray-400">Focus shifts to technicals and other news</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Trading Tips */}
                  <div className="mt-4 p-3 rounded-lg bg-blue-950/30 border border-blue-900/30">
                    <p className="text-[11px] text-blue-400">
                      <span className="font-semibold">💡 Pro Tip:</span> Wait 5 minutes after release for initial volatility to settle. Use limit orders, not market orders. Watch for reversals after the first hour.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Earnings Event Detail Modal */}
      {isEarningsModalOpen && selectedEarningsEvent && (
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
                    <p className={cn(
                      "text-sm px-4 py-2 rounded-xl border flex-1",
                      selectedEarningsEvent.predicted_direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
                      selectedEarningsEvent.predicted_direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
                      selectedEarningsEvent.predicted_direction === "neutral" && "bg-gray-700/30 text-gray-400 border-gray-600"
                    )}>
                      {selectedEarningsEvent.predicted_direction === "bullish" && "📈 Beat Expected"}
                      {selectedEarningsEvent.predicted_direction === "bearish" && "📉 Miss Expected"}
                      {selectedEarningsEvent.predicted_direction === "neutral" && "➖ In Line Expected"}
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
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Pre-market</span>
                        <span className="text-green-400">Stock +3-5% • {selectedEarningsEvent.ticker} calls spike</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Open</span>
                        <span className="text-green-400">Gap up, momentum buyers enter</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-amber-400">Watch for profit taking at highs</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Sector effect</span>
                        <span className="text-blue-400">{selectedEarningsEvent.sector} peers likely rally</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Miss Scenario */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-transparent border border-red-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-xs">❌</span>
                      <h5 className="text-sm font-semibold text-red-400">Miss (EPS or Revenue)</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Pre-market</span>
                        <span className="text-red-400">Stock -4-7% • Put volume surges</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Open</span>
                        <span className="text-red-400">Gap down, stop losses trigger</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-amber-400">Dead cat bounce possible, then fade</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Sector effect</span>
                        <span className="text-red-400">{selectedEarningsEvent.sector} peers may decline</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Mixed Scenario */}
                  <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-transparent border border-amber-900/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center text-amber-400 text-xs">⚠️</span>
                      <h5 className="text-sm font-semibold text-amber-400">Mixed (Beat EPS, Miss Revenue or vice versa)</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Pre-market</span>
                        <span className="text-amber-400">Volatile ±2% • Direction unclear</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Guidance</span>
                        <span className="text-amber-400">Forward guidance becomes key driver</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">First hour</span>
                        <span className="text-gray-400">Wait for conference call clarity</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* In Line */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-gray-900/50 to-transparent border border-gray-700/50">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-gray-400 text-xs">➖</span>
                      <h5 className="text-sm font-semibold text-gray-400">In Line (Meets Expectations)</h5>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Pre-market</span>
                        <span className="text-gray-400">±1% move • Options IV crush likely</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500 w-20">Guidance</span>
                        <span className="text-gray-400">Stock direction depends on forward outlook</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Trading Tips */}
                  <div className="mt-4 p-3 rounded-lg bg-purple-950/30 border border-purple-900/30">
                    <p className="text-[11px] text-purple-400">
                      <span className="font-semibold">💡 Pro Tip:</span> For {selectedEarningsEvent.time === "after_market" ? "after-hours" : "pre-market"} earnings, liquidity is lower and spreads wider. Consider waiting for regular session open for better fills. Watch for post-earnings drift in following days.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
