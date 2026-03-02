"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time } from "lightweight-charts";
import { format, formatDistanceToNow, isWithinInterval, subMinutes, addMinutes } from "date-fns";
import { 
  Bell, Star, Wallet, Calendar, FileText, MessageSquare, Newspaper,
  Building2, LineChart, BookOpen, Search, Filter, ChevronLeft, ChevronRight,
  Zap, TrendingUp, TrendingDown, Minus, ThumbsUp, Sparkles, Camera, Settings,
  Clock, AlertTriangle, RefreshCw, X, ArrowUp, ArrowDown
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
  newsCount?: number;
  priceChange?: number;
}

interface SymbolData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface ChartDataResponse {
  success: boolean;
  data: {
    symbol: string;
    timeframe: string;
    candles: ChartCandle[];
  };
}

interface CandleNews {
  candle: ChartCandle;
  news: EnrichedNews[];
  hasBigMove: boolean;
  moveType: 'up' | 'down' | 'none';
  movePercent: number;
}

// ==================== BIZIM SEMBOLLERIMIZ ====================
const SYMBOLS: SymbolData[] = [
  { symbol: "XAUUSD", name: "Gold", price: 4988.57, change: 42.30, changePercent: 0.85 },
  { symbol: "NDX", name: "NASDAQ", price: 22500.00, change: 125.50, changePercent: 0.56 },
  { symbol: "DAX", name: "DAX 40", price: 22500.00, change: -180.20, changePercent: -0.79 },
  { symbol: "USOIL", name: "WTI Crude", price: 75.80, change: 1.20, changePercent: 1.61 },
  { symbol: "VIX", name: "VIX", price: 18.50, change: -0.85, changePercent: -4.40 },
  { symbol: "DXY", name: "Dollar Index", price: 104.25, change: 0.12, changePercent: 0.12 },
];

const TIMEFRAMES = [
  { value: "1m", label: "1m", minutes: 1 },
  { value: "5m", label: "5m", minutes: 5 },
  { value: "15m", label: "15m", minutes: 15 },
  { value: "30m", label: "30m", minutes: 30 },
  { value: "1h", label: "1h", minutes: 60 },
  { value: "4h", label: "4h", minutes: 240 },
  { value: "1d", label: "1D", minutes: 1440 },
];

// ==================== SIDEBAR NAVIGATION ====================
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

// ==================== SYMBOL BAR ====================
const SymbolBar = ({ symbols, selectedSymbol, onSelect }: { symbols: SymbolData[], selectedSymbol: string, onSelect: (s: string) => void }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const scroll = (dir: "left" | "right") => scrollRef.current?.scrollBy({ left: dir === "left" ? -200 : 200, behavior: "smooth" });

  return (
    <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-[#0a0a0a]">
      <button onClick={() => scroll("left")} className="p-1 text-gray-500 hover:text-white flex-shrink-0"><ChevronLeft className="w-4 h-4" /></button>
      <div ref={scrollRef} className="flex-1 flex items-center gap-2 overflow-x-auto scrollbar-hide">
        {symbols.map((sym) => (
          <button key={sym.symbol} onClick={() => onSelect(sym.symbol)} className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all flex-shrink-0",
            selectedSymbol === sym.symbol ? "bg-gray-800 text-white border border-gray-700" : "bg-gray-900/50 text-gray-400 hover:bg-gray-800 hover:text-white border border-transparent"
          )}>
            <span className="font-semibold">{sym.symbol}</span>
            <span className={cn("text-xs font-mono", sym.change > 0 ? "text-green-400" : sym.change < 0 ? "text-red-400" : "text-gray-500")}>
              ${sym.price.toLocaleString()}
            </span>
          </button>
        ))}
      </div>
      <button onClick={() => scroll("right")} className="p-1 text-gray-500 hover:text-white flex-shrink-0"><ChevronRight className="w-4 h-4" /></button>
    </div>
  );
};

// ==================== ANALYSIS CARDS ====================
const AnalysisCard = ({ type, label, value, active = false }: { type: "swing" | "day" | "news", label: string, value: string, active?: boolean }) => {
  const styles = {
    swing: { bg: active ? "bg-green-500/10 border-green-500/30" : "bg-gray-900/50 border-gray-800", text: active ? "text-green-400" : "text-gray-400", icon: TrendingUp },
    day: { bg: active ? "bg-red-500/10 border-red-500/30" : "bg-gray-900/50 border-gray-800", text: active ? "text-red-400" : "text-gray-400", icon: TrendingDown },
    news: { bg: active ? "bg-purple-500/10 border-purple-500/30" : "bg-gray-900/50 border-gray-800", text: active ? "text-purple-400" : "text-gray-400", icon: Newspaper },
  };
  const style = styles[type];
  const Icon = style.icon;
  return (
    <div className={cn("flex items-center gap-3 px-4 py-3 rounded-xl border", style.bg)}>
      <div className="flex flex-col items-start">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</span>
        <span className={cn("text-sm font-semibold flex items-center gap-1.5", style.text)}>
          {type === "news" && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
          {value}
          <Icon className="w-4 h-4" />
        </span>
      </div>
    </div>
  );
};

// ==================== TIME AGO COMPONENT (CLIENT ONLY) ====================
const TimeAgo = ({ timestamp }: { timestamp: string }) => {
  const [timeAgo, setTimeAgo] = useState<string>("");
  
  useEffect(() => {
    setTimeAgo(formatDistanceToNow(new Date(timestamp), { addSuffix: true }));
    const interval = setInterval(() => {
      setTimeAgo(formatDistanceToNow(new Date(timestamp), { addSuffix: true }));
    }, 60000);
    return () => clearInterval(interval);
  }, [timestamp]);
  
  return <span className="text-xs text-gray-500">{timeAgo || "..."}</span>;
};

// ==================== NEWS CARD ====================
const NewsCard = ({ news, isExpanded, onToggle, onClick }: { news: EnrichedNews, isExpanded: boolean, onToggle: () => void, onClick: () => void }) => {
  const isHighImpact = news.urgency === "breaking" || news.urgency === "high";
  return (
    <div className={cn(
      "group relative p-4 rounded-xl border transition-all cursor-pointer",
      isHighImpact ? "bg-gradient-to-r from-red-950/30 to-transparent border-red-900/30 hover:border-red-700/50" : "bg-gray-900/30 border-gray-800 hover:border-gray-700"
    )} onClick={onClick}>
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
        <span className="text-xs text-gray-500 font-mono">{format(new Date(news.timestamp), "HH:mm")}</span>
        <span className="text-xs text-gray-600">•</span>
        <TimeAgo timestamp={news.timestamp} />
      </div>
      <h3 className="text-sm font-semibold text-white leading-snug mb-2 uppercase tracking-wide">{news.headline}</h3>
      <p className="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-2">{news.content || news.headline}</p>
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
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-800 animate-in slide-in-from-top-2">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-semibold text-purple-400">AI Analysis</span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed mb-4">{news.content || "AI analysis not available."}</p>
          {news.impacts && news.impacts.length > 0 && (
            <div className="space-y-2">
              {news.impacts.map((impact, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-950/50">
                  <span className={cn("text-xs font-medium", impact.direction === "bullish" ? "text-green-400" : impact.direction === "bearish" ? "text-red-400" : "text-gray-400")}>
                    {impact.symbol}
                  </span>
                  <span className="text-xs text-gray-500">{impact.reasoning}</span>
                  <span className="text-xs text-gray-400">{Math.round((impact.confidence || 0.5) * 100)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ==================== CANDLE INFO PANEL ====================
const CandleInfoPanel = ({ candleNews, onClose, symbol }: { candleNews: CandleNews | null, onClose: () => void, symbol: string }) => {
  if (!candleNews) return null;
  
  return (
    <div className="absolute top-20 left-4 z-20 w-80 bg-gray-900/95 backdrop-blur-xl border border-gray-700 rounded-xl shadow-2xl shadow-black/50 overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div>
          <h3 className="font-semibold flex items-center gap-2">
            {candleNews.candle.time && format(new Date(candleNews.candle.time * 1000), "MMM d, HH:mm")}
          </h3>
          <p className="text-xs text-gray-500">Candle Analysis</p>
        </div>
        <button onClick={onClose} className="p-1 text-gray-500 hover:text-white hover:bg-gray-800 rounded"><X className="w-4 h-4" /></button>
      </div>
      
      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-xs text-gray-500">Open</span>
            <p className="font-mono text-sm">${candleNews.candle.open.toFixed(2)}</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-xs text-gray-500">Close</span>
            <p className="font-mono text-sm">${candleNews.candle.close.toFixed(2)}</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-xs text-gray-500">High</span>
            <p className="font-mono text-sm text-green-400">${candleNews.candle.high.toFixed(2)}</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <span className="text-xs text-gray-500">Low</span>
            <p className="font-mono text-sm text-red-400">${candleNews.candle.low.toFixed(2)}</p>
          </div>
        </div>

        {candleNews.hasBigMove && (
          <div className={cn(
            "p-3 rounded-lg border",
            candleNews.moveType === "up" ? "bg-green-500/10 border-green-500/30" : "bg-red-500/10 border-red-500/30"
          )}>
            <div className="flex items-center gap-2 mb-2">
              {candleNews.moveType === "up" ? <ArrowUp className="w-4 h-4 text-green-400" /> : <ArrowDown className="w-4 h-4 text-red-400" />}
              <span className={cn("font-semibold", candleNews.moveType === "up" ? "text-green-400" : "text-red-400")}>
                Big {candleNews.moveType === "up" ? "Surge" : "Drop"}
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Price moved {candleNews.movePercent.toFixed(2)}% during this period. 
              {candleNews.moveType === "up" ? "Strong buying pressure detected." : "Significant selling pressure observed."}
            </p>
          </div>
        )}

        <div>
          <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-purple-400" />
            Related News ({candleNews.news.length})
          </h4>
          {candleNews.news.length === 0 ? (
            <p className="text-xs text-gray-500 italic">No major news events during this period.</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {candleNews.news.map((n, i) => (
                <div key={i} className="p-2 bg-gray-800/50 rounded-lg text-xs">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn(
                      "w-1.5 h-1.5 rounded-full",
                      n.urgency === "breaking" && "bg-red-500",
                      n.urgency === "high" && "bg-orange-500",
                      n.urgency === "medium" && "bg-yellow-500"
                    )} />
                    <span className="text-gray-400">{format(new Date(n.timestamp), "HH:mm")}</span>
                  </div>
                  <p className="text-gray-300 line-clamp-2">{n.headline}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {candleNews.news.length > 0 && (
          <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-semibold text-purple-400">AI Explanation</span>
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">
              {candleNews.moveType === "up" 
                ? `The ${candleNews.movePercent.toFixed(2)}% surge was likely driven by ${candleNews.news[0]?.headline?.toLowerCase() || "positive market sentiment"}. ${candleNews.news[0]?.impacts?.find(i => i.symbol === symbol)?.reasoning || "Technical buying pressure supported the move."}`
                : `The ${Math.abs(candleNews.movePercent).toFixed(2)}% decline was influenced by ${candleNews.news[0]?.headline?.toLowerCase() || "negative market sentiment"}. ${candleNews.news[0]?.impacts?.find(i => i.symbol === symbol)?.reasoning || "Technical selling pressure accelerated the drop."}`
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== MAIN COMPONENT ====================
export default function NewsCorrelationDashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState("XAUUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNewsId, setExpandedNewsId] = useState<string | null>(null);
  const [newsFilter, setNewsFilter] = useState<"all" | "popular" | "high">("high");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedCandleNews, setSelectedCandleNews] = useState<CandleNews | null>(null);
  const [selectedNewsForModal, setSelectedNewsForModal] = useState<EnrichedNews | null>(null);
  const [isNewsModalOpen, setIsNewsModalOpen] = useState(false);
  const [currentLocale, setCurrentLocale] = useState("tr");
  const [mounted, setMounted] = useState(false);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchChartData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const chartResponse = await fetcher<ChartDataResponse>(`/api/data/ohlcv?symbol=${selectedSymbol}&timeframe=${timeframe}&limit=200`);
      
      if (chartResponse.success && chartResponse.data?.candles) {
        const processedCandles = chartResponse.data.candles.map(candle => {
          const priceChange = ((candle.close - candle.open) / candle.open) * 100;
          return { ...candle, priceChange, hasBigMove: Math.abs(priceChange) > 1.5 };
        });
        setChartData(processedCandles);
      } else {
        setError("No chart data available");
      }
    } catch (error) {
      console.error("Error fetching chart:", error);
      setError("Failed to load chart data");
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, timeframe]);

  const fetchNews = useCallback(async () => {
    try {
      setNewsLoading(true);
      const newsResponse = await fetcher<{ success: boolean; data: EnrichedNews[] }>(`/api/rss/news?symbol=${selectedSymbol}&limit=50&hours=72`);
      
      if (newsResponse.success && newsResponse.data && newsResponse.data.length > 0) {
        setNews(newsResponse.data);
      } else {
        setNews([
          {
            id: "1",
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            source: "Reuters",
            headline: "Gold rallies to $4,993 as geopolitical tensions rise",
            content: "Gold prices surged to near $5,000 as Middle East tensions escalate. Safe haven demand increases amid uncertainty.",
            urgency: "high",
            impacts: [
              { symbol: "XAUUSD", direction: "bullish", score: 8, confidence: 0.85, reasoning: "Safe haven demand", emoji: "🚀" },
              { symbol: "USOIL", direction: "bullish", score: 7, confidence: 0.80, reasoning: "Supply concerns", emoji: "📈" },
              { symbol: "VIX", direction: "bullish", score: 6, confidence: 0.75, reasoning: "Volatility spike", emoji: "⚠️" },
            ],
            sentiment: "risk_off",
            volatilityExpectation: "high",
            eventDuration: "short_term",
            affectedCandles: [],
            aiConfidence: 85,
            analysisTimestamp: new Date().toISOString(),
          },
          {
            id: "2",
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            source: "Bloomberg",
            headline: "Fed signals potential rate cuts in coming months",
            content: "Federal Reserve officials hint at dovish shift in monetary policy. Markets pricing in 75bps of cuts this year.",
            urgency: "high",
            impacts: [
              { symbol: "NDX", direction: "bullish", score: 8, confidence: 0.88, reasoning: "Lower rates boost tech", emoji: "🚀" },
              { symbol: "XAUUSD", direction: "bullish", score: 7, confidence: 0.82, reasoning: "Weaker dollar helps gold", emoji: "📈" },
              { symbol: "DXY", direction: "bearish", score: 7, confidence: 0.85, reasoning: "Rate cuts weaken USD", emoji: "📉" },
            ],
            sentiment: "risk_on",
            volatilityExpectation: "high",
            eventDuration: "long_term",
            affectedCandles: [],
            aiConfidence: 82,
            analysisTimestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error fetching news:", error);
    } finally {
      setNewsLoading(false);
    }
  }, [selectedSymbol]);

  useEffect(() => {
    if (mounted) {
      fetchChartData();
      fetchNews();
    }
  }, [fetchChartData, fetchNews, mounted]);

  useEffect(() => {
    if (!chartContainerRef.current || !mounted) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: { background: { color: "transparent" }, textColor: "#6b7280", fontFamily: "Inter, system-ui, sans-serif" },
      grid: { vertLines: { color: "rgba(255, 255, 255, 0.03)" }, horzLines: { color: "rgba(255, 255, 255, 0.03)" } },
      crosshair: { mode: CrosshairMode.Normal, vertLine: { color: "rgba(255, 255, 255, 0.1)", labelBackgroundColor: "#374151" }, horzLine: { color: "rgba(255, 255, 255, 0.1)", labelBackgroundColor: "#374151" } },
      rightPriceScale: { borderColor: "rgba(255, 255, 255, 0.1)", scaleMargins: { top: 0.1, bottom: 0.1 } },
      timeScale: { borderColor: "rgba(255, 255, 255, 0.1)", timeVisible: true, secondsVisible: false },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e", downColor: "#ef4444", borderUpColor: "#22c55e", borderDownColor: "#ef4444",
      wickUpColor: "#22c55e", wickDownColor: "#ef4444",
    });

    chart.subscribeClick((param) => {
      if (param.time && param.point) {
        const time = param.time as number;
        const tf = TIMEFRAMES.find(t => t.value === timeframe);
        const minutes = tf?.minutes || 60;
        
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
    return () => { window.removeEventListener("resize", handleResize); chart.remove(); };
  }, [chartData, news, timeframe, mounted]);

  useEffect(() => {
    if (candlestickSeriesRef.current && chartData.length > 0) {
      const formattedData = chartData.map((candle) => ({
        time: candle.time as Time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      }));

      candlestickSeriesRef.current.setData(formattedData);
      
      const markers = chartData
        .filter(c => Math.abs(c.priceChange || 0) > 1.5)
        .map(candle => ({
          time: candle.time as Time,
          position: (candle.priceChange || 0) > 0 ? "belowBar" as const : "aboveBar" as const,
          color: (candle.priceChange || 0) > 0 ? "#22c55e" : "#ef4444",
          shape: (candle.priceChange || 0) > 0 ? "arrowUp" as const : "arrowDown" as const,
          text: `${Math.abs(candle.priceChange || 0).toFixed(1)}%`,
          size: 2,
        }));
      
      candlestickSeriesRef.current.setMarkers(markers);
      chartRef.current?.timeScale().fitContent();
    }
  }, [chartData]);

  const handleNewsClick = (newsItem: EnrichedNews) => {
    setSelectedNewsForModal(newsItem);
    setIsNewsModalOpen(true);
  };

  const filteredNews = news.filter((n) => {
    if (newsFilter === "all") return true;
    if (newsFilter === "high") return n.urgency === "breaking" || n.urgency === "high";
    return true;
  });

  const currentSymbol = SYMBOLS.find(s => s.symbol === selectedSymbol);

  if (!mounted) {
    return <div className="min-h-screen bg-[#0a0a0a]" />;
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex">
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

      <main className="flex-1 flex flex-col min-w-0">
        <SymbolBar symbols={SYMBOLS} selectedSymbol={selectedSymbol} onSelect={setSelectedSymbol} />

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0 relative">
            <div className="p-6 border-b border-gray-800">
              <h1 className="text-xl font-bold text-white mb-4 leading-tight">{selectedSymbol} - {currentSymbol?.name} Market Analysis</h1>
              <div className="flex items-center gap-3 flex-wrap">
                <AnalysisCard type="swing" label="SWING TRADING" value="Bullish" active />
                <AnalysisCard type="day" label="DAY TRADING" value="Slightly Bearish" active />
                <AnalysisCard type="news" label="NEWS FEED" value="High Impact" active />
              </div>
            </div>

            <div className="flex-1 relative min-h-0">
              <CandleInfoPanel candleNews={selectedCandleNews} onClose={() => setSelectedCandleNews(null)} symbol={selectedSymbol} />

              <div className="absolute top-4 left-4 z-10 flex items-center gap-1 bg-gray-900/80 backdrop-blur rounded-lg p-1 border border-gray-800">
                {TIMEFRAMES.map((tf) => (
                  <button key={tf.value} onClick={() => setTimeframe(tf.value)} className={cn(
                    "px-3 py-1.5 rounded text-xs font-medium transition-all",
                    timeframe === tf.value ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"
                  )}>{tf.label}</button>
                ))}
              </div>

              <button onClick={fetchChartData} className="absolute top-4 left-64 z-10 p-2 bg-gray-900/80 backdrop-blur rounded-lg border border-gray-800 text-gray-400 hover:text-white transition-colors">
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              <div className="absolute top-4 right-4 z-10 space-y-2">
                <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                  <span className="text-xs text-gray-400">Pullback Area:</span>
                  <span className="text-sm text-white ml-2 font-mono">${((currentSymbol?.price || 0) * 1.02).toFixed(2)}</span>
                </div>
                <div className="bg-gray-900/90 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                  <span className="text-xs text-gray-400">Target Level:</span>
                  <span className="text-sm text-red-400 ml-2 font-mono">${((currentSymbol?.price || 0) * 0.98).toFixed(2)}</span>
                </div>
              </div>

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
                    <button onClick={fetchChartData} className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors">Retry</button>
                  </div>
                </div>
              )}

              <div ref={chartContainerRef} className="w-full h-full" style={{ visibility: loading || error ? 'hidden' : 'visible' }} />

              {!loading && !error && !selectedCandleNews && (
                <div className="absolute bottom-16 left-4 z-10 bg-gray-900/80 backdrop-blur px-3 py-2 rounded-lg border border-gray-800 text-xs text-gray-400">
                  💡 Click on any candle to see related news and AI analysis
                </div>
              )}

              <div className="absolute bottom-0 left-0 right-0 flex justify-between px-16 py-2 text-xs text-gray-500 border-t border-gray-800 bg-[#0a0a0a]">
                <span>Monday</span><span>Tuesday</span><span>Wednesday</span><span>Thursday</span><span>Friday</span>
              </div>
            </div>

            <div className="border-t border-gray-800 bg-gray-900/30 p-4">
              <p className="text-sm text-gray-400">
                The day trading bias on <span className="text-white font-semibold">{selectedSymbol}</span> is <span className="text-red-400 font-semibold bg-red-500/10 px-2 py-0.5 rounded">slightly bearish</span>
              </p>
              <p className="text-xs text-gray-500 mt-1">Updated {formatDistanceToNow(new Date(), { addSuffix: true })}</p>
            </div>
          </div>

          <aside className="w-[420px] border-l border-gray-800 bg-[#0a0a0a] flex flex-col">
            <div className="h-14 flex items-center justify-between px-4 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <h2 className="font-semibold">News Feed</h2>
                <Clock className="w-4 h-4 text-gray-500" />
              </div>
              <div className="flex items-center gap-2">
                <select value={currentLocale} onChange={(e) => setCurrentLocale(e.target.value)} className="bg-gray-900 border border-gray-800 rounded-lg px-2 py-1 text-xs text-gray-400 focus:outline-none focus:border-purple-500">
                  <option value="tr">🇹🇷 TR</option>
                  <option value="en">🇬🇧 EN</option>
                  <option value="de">🇩🇪 DE</option>
                  <option value="es">🇪🇸 ES</option>
                  <option value="fr">🇫🇷 FR</option>
                  <option value="ar">🇸🇦 AR</option>
                </select>
                <button onClick={fetchNews} className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <RefreshCw className={cn("w-4 h-4", newsLoading && "animate-spin")} />
                </button>
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"><Filter className="w-4 h-4" /></button>
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"><Search className="w-4 h-4" /></button>
              </div>
            </div>

            <div className="flex items-center gap-1 px-4 py-3 border-b border-gray-800">
              {["all", "popular", "high"].map((filter) => (
                <button key={filter} onClick={() => setNewsFilter(filter as any)} className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2",
                  newsFilter === filter ? "text-white" : "text-gray-500 hover:text-gray-300"
                )}>
                  {filter === "high" && newsFilter === "high" && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {newsLoading ? (
                Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-32 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />)
              ) : filteredNews.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Newspaper className="w-6 h-6 text-gray-500" />
                  </div>
                  <p className="text-gray-500 text-sm">No news available</p>
                </div>
              ) : (
                filteredNews.map((item) => (
                  <NewsCard 
                    key={item.id} 
                    news={item} 
                    isExpanded={expandedNewsId === item.id} 
                    onToggle={() => setExpandedNewsId(expandedNewsId === item.id ? null : item.id)}
                    onClick={() => handleNewsClick(item)}
                  />
                ))
              )}
            </div>
          </aside>
        </div>
      </main>

      <NewsDetailModal
        news={selectedNewsForModal}
        isOpen={isNewsModalOpen}
        onClose={() => setIsNewsModalOpen(false)}
        locale={currentLocale as any}
      />
    </div>
  );
}
