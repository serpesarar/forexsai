"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time } from "lightweight-charts";
import { format, formatDistanceToNow } from "date-fns";
import { 
  Bell, 
  Star, 
  Wallet, 
  Calendar, 
  FileText, 
  MessageSquare, 
  Newspaper,
  Building2,
  LineChart,
  BookOpen,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Zap,
  TrendingUp,
  TrendingDown,
  Minus,
  ThumbsUp,
  Sparkles,
  Camera,
  Settings,
  Clock,
  AlertTriangle,
  RefreshCw,
  BookMarked,
  HelpCircle,
  LayoutDashboard,
  Activity,
  BarChart3,
  PieChart,
  Globe2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetcher } from "@/lib/api";
import Link from "next/link";
import type { EnrichedNews } from "@/types/news-correlation";

// ==================== TYPES ====================
interface ChartCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
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
  { value: "1m", label: "1m" },
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "30m", label: "30m" },
  { value: "1h", label: "1h" },
  { value: "4h", label: "4h" },
  { value: "1d", label: "1D" },
  { value: "1w", label: "1W" },
];

// ==================== DYNAMIC HEADLINES ====================
const getDynamicHeadline = (symbol: string, news: EnrichedNews[]): string => {
  const latestNews = news[0];
  if (latestNews) {
    return latestNews.headline;
  }
  
  const headlines: Record<string, string> = {
    XAUUSD: "Gold rallies to $4,993 as geopolitical tensions rise; Fed rate cut expectations support",
    NDX: "NASDAQ extends gains as tech earnings beat expectations; AI optimism drives momentum",
    DAX: "DAX slides on German economic data miss; ECB policy uncertainty weighs",
    USOIL: "WTI Crude surges to $75.80 on supply concerns; Middle East tensions escalate",
    VIX: "VIX drops to 18.50 as market volatility subsides; risk-on sentiment prevails",
    DXY: "Dollar Index steady at 104.25 ahead of Fed speeches; inflation data awaited",
  };
  
  return headlines[symbol] || `${symbol} Market Analysis - Latest Updates`;
};

// ==================== SIDEBAR NAVIGATION ====================
const sidebarItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/", badge: null },
  { icon: Bell, label: "Alerts", href: "/alerts", badge: 3 },
  { icon: Star, label: "Watchlist", href: "/watchlist", badge: null },
  { icon: Activity, label: "Smart Trades", href: "/news-correlation", badge: null, active: true },
  { icon: Calendar, label: "Economic Calendar", href: "/calendar", badge: null },
  { icon: BarChart3, label: "News Analysis", href: "/news-analysis", badge: null },
  { icon: MessageSquare, label: "Chat AI", href: "/chat", badge: null },
  { icon: FileText, label: "Research Reports", href: "/research", badge: null },
  { icon: BookMarked, label: "Docs", href: "/docs", badge: null },
  { icon: Building2, label: "Brokers", href: "/brokers", badge: null },
  { icon: LineChart, label: "My Trades", href: "/trades", badge: null },
];

const SidebarItem = ({ 
  icon: Icon, 
  label, 
  href,
  active = false,
  badge,
  collapsed
}: { 
  icon: React.ElementType; 
  label: string; 
  href: string;
  active?: boolean;
  badge?: number | null;
  collapsed?: boolean;
}) => (
  <Link
    href={href}
    className={cn(
      "flex items-center gap-3 px-4 py-3 text-sm transition-all relative",
      active 
        ? "text-white bg-gradient-to-r from-purple-500/10 to-transparent border-l-2 border-purple-500" 
        : "text-gray-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent"
    )}
  >
    <Icon className={cn("w-5 h-5 flex-shrink-0", active && "text-purple-400")} />
    {!collapsed && <span className="truncate">{label}</span>}
    {!collapsed && badge && (
      <span className="ml-auto bg-red-500 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">
        {badge}
      </span>
    )}
    {collapsed && badge && (
      <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full" />
    )}
  </Link>
);

// ==================== SYMBOL BAR ====================
const SymbolBar = ({ 
  symbols, 
  selectedSymbol, 
  onSelect 
}: { 
  symbols: SymbolData[]; 
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: direction === "left" ? -200 : 200, behavior: "smooth" });
    }
  };

  return (
    <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-[#0a0a0a]">
      <button 
        onClick={() => scroll("left")}
        className="p-1 text-gray-500 hover:text-white transition-colors flex-shrink-0"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      
      <div 
        ref={scrollRef}
        className="flex-1 flex items-center gap-2 overflow-x-auto scrollbar-hide"
      >
        {symbols.map((sym) => (
          <button
            key={sym.symbol}
            onClick={() => onSelect(sym.symbol)}
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
              ${sym.price.toLocaleString()}
            </span>
          </button>
        ))}
      </div>
      
      <button 
        onClick={() => scroll("right")}
        className="p-1 text-gray-500 hover:text-white transition-colors flex-shrink-0"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
      
      <button className="p-2 text-gray-500 hover:text-white transition-colors flex-shrink-0">
        <PlusIcon className="w-4 h-4" />
      </button>
    </div>
  );
};

const PlusIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 5v14M5 12h14" />
  </svg>
);

// ==================== ANALYSIS CARDS ====================
const AnalysisCard = ({ 
  type, 
  label, 
  value,
  active = false,
  onClick
}: { 
  type: "swing" | "day" | "news";
  label: string;
  value: string;
  active?: boolean;
  onClick?: () => void;
}) => {
  const styles = {
    swing: {
      bg: active ? "bg-green-500/10 border-green-500/30" : "bg-gray-900/50 border-gray-800",
      text: active ? "text-green-400" : "text-gray-400",
      icon: TrendingUp,
      iconColor: "text-green-400",
    },
    day: {
      bg: active ? "bg-red-500/10 border-red-500/30" : "bg-gray-900/50 border-gray-800",
      text: active ? "text-red-400" : "text-gray-400",
      icon: TrendingDown,
      iconColor: "text-red-400",
    },
    news: {
      bg: active ? "bg-purple-500/10 border-purple-500/30" : "bg-gray-900/50 border-gray-800",
      text: active ? "text-purple-400" : "text-gray-400",
      icon: Newspaper,
      iconColor: "text-purple-400",
    },
  };

  const style = styles[type];
  const Icon = style.icon;

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 px-4 py-3 rounded-xl border transition-all hover:border-gray-600",
        style.bg
      )}
    >
      <div className="flex flex-col items-start">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</span>
        <span className={cn("text-sm font-semibold flex items-center gap-1.5", style.text)}>
          {type === "news" && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
          {value}
          <Icon className={cn("w-4 h-4", style.iconColor)} />
        </span>
      </div>
    </button>
  );
};

// ==================== NEWS CARD ====================
const NewsCard = ({ 
  news, 
  isExpanded, 
  onToggle 
}: { 
  news: EnrichedNews; 
  isExpanded: boolean;
  onToggle: () => void;
}) => {
  const isHighImpact = news.urgency === "breaking" || news.urgency === "high";
  
  return (
    <div 
      className={cn(
        "group relative p-4 rounded-xl border transition-all cursor-pointer",
        isHighImpact 
          ? "bg-gradient-to-r from-red-950/30 to-transparent border-red-900/30 hover:border-red-700/50" 
          : "bg-gray-900/30 border-gray-800 hover:border-gray-700"
      )}
      onClick={onToggle}
    >
      {/* Header */}
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
          {new Date(news.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </span>
        <span className="text-xs text-gray-600">•</span>
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(news.timestamp), { addSuffix: true })}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-white leading-snug mb-2 uppercase tracking-wide">
        {news.headline}
      </h3>

      {/* Description */}
      <p className="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-2">
        {news.content || news.headline}
      </p>

      {/* Impact Badges */}
      <div className="flex flex-wrap gap-1.5">
        {news.impacts?.slice(0, 6).map((impact, idx) => (
          <span
            key={idx}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium border",
              impact.direction === "bullish" && "bg-green-500/10 text-green-400 border-green-500/20",
              impact.direction === "bearish" && "bg-red-500/10 text-red-400 border-red-500/20",
              impact.direction === "neutral" && "bg-gray-700/50 text-gray-400 border-gray-600"
            )}
          >
            {impact.direction === "bullish" && <TrendingUp className="w-3 h-3" />}
            {impact.direction === "bearish" && <TrendingDown className="w-3 h-3" />}
            {impact.symbol}
            {impact.direction === "bullish" ? "↑" : impact.direction === "bearish" ? "↓" : "→"}
          </span>
        ))}
      </div>

      {/* Expanded AI Analysis */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-800 animate-in slide-in-from-top-2">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-semibold text-purple-400">AI Analysis</span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed mb-4">
            {news.content || "AI analysis not available for this news item."}
          </p>
          
          {news.impacts && news.impacts.length > 0 && (
            <div className="space-y-2">
              {news.impacts.map((impact, idx) => (
                <div 
                  key={idx}
                  className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-950/50"
                >
                  <span className={cn(
                    "text-xs font-medium",
                    impact.direction === "bullish" ? "text-green-400" : 
                    impact.direction === "bearish" ? "text-red-400" : "text-gray-400"
                  )}>
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

// ==================== MAIN COMPONENT ====================
export default function MRKTAIStyleDashboard() {
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
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // Fetch chart data
  const fetchChartData = useCallback(async () => {
    try {
      setLoading(true);
      const chartResponse = await fetcher<ChartDataResponse>(
        `/api/data/ohlcv?symbol=${selectedSymbol}&timeframe=${timeframe}&limit=200`
      );
      
      if (chartResponse.success && chartResponse.data?.candles) {
        setChartData(chartResponse.data.candles);
        setError(null);
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

  // Fetch news data
  const fetchNews = useCallback(async () => {
    try {
      setNewsLoading(true);
      const newsResponse = await fetcher<{ success: boolean; data: EnrichedNews[] }>(
        `/api/rss/news?symbol=${selectedSymbol}&limit=50&hours=72`
      );
      
      if (newsResponse.success && newsResponse.data && newsResponse.data.length > 0) {
        setNews(newsResponse.data);
      } else {
        // Mock news for demo
        setNews([
          {
            id: "1",
            timestamp: new Date().toISOString(),
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
            timestamp: new Date(Date.now() - 3600000).toISOString(),
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
    fetchChartData();
    fetchNews();
  }, [fetchChartData, fetchNews]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { color: "transparent" },
        textColor: "#6b7280",
        fontFamily: "Inter, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.03)" },
        horzLines: { color: "rgba(255, 255, 255, 0.03)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(255, 255, 255, 0.1)",
          labelBackgroundColor: "#374151",
        },
        horzLine: {
          color: "rgba(255, 255, 255, 0.1)",
          labelBackgroundColor: "#374151",
        },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        timeVisible: true,
        secondsVisible: false,
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
  }, []);

  // Update chart data
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
      chartRef.current?.timeScale().fitContent();
    }
  }, [chartData]);

  const filteredNews = news.filter((n) => {
    if (newsFilter === "all") return true;
    if (newsFilter === "high") return n.urgency === "breaking" || n.urgency === "high";
    return true;
  });

  const currentSymbol = SYMBOLS.find(s => s.symbol === selectedSymbol);
  const headline = getDynamicHeadline(selectedSymbol, news);

  // Get bias based on latest news
  const getBias = () => {
    const latestHighImpact = news.find(n => n.urgency === "high" || n.urgency === "breaking");
    if (latestHighImpact?.impacts) {
      const symbolImpact = latestHighImpact.impacts.find(i => i.symbol === selectedSymbol);
      if (symbolImpact?.direction === "bullish") return { text: "Bullish", color: "green" };
      if (symbolImpact?.direction === "bearish") return { text: "Slightly Bearish", color: "red" };
    }
    return { text: "Neutral", color: "gray" };
  };

  const bias = getBias();

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex">
      {/* Left Sidebar */}
      <aside 
        className={cn(
          "flex-shrink-0 border-r border-gray-800 bg-[#0a0a0a] flex flex-col transition-all duration-300",
          sidebarCollapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-gray-800">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">F</span>
          </div>
          {!sidebarCollapsed && (
            <span className="ml-3 font-bold text-lg">ForexSAI</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="py-4 space-y-1 flex-1">
          {sidebarItems.map((item) => (
            <SidebarItem
              key={item.label}
              icon={item.icon}
              label={item.label}
              href={item.href}
              active={item.active}
              badge={item.badge}
              collapsed={sidebarCollapsed}
            />
          ))}
        </nav>

        {/* Bottom section */}
        <div className="p-4 border-t border-gray-800">
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center justify-center p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ChevronLeft className={cn("w-5 h-5 transition-transform", sidebarCollapsed && "rotate-180")} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Symbol Bar */}
        <SymbolBar 
          symbols={SYMBOLS} 
          selectedSymbol={selectedSymbol}
          onSelect={setSelectedSymbol}
        />

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chart Section */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Title & Analysis Cards */}
            <div className="p-6 border-b border-gray-800">
              <h1 className="text-xl font-bold text-white mb-4 leading-tight">
                {headline}
              </h1>
              
              {/* Analysis Cards Row */}
              <div className="flex items-center gap-3 flex-wrap">
                <AnalysisCard 
                  type="swing" 
                  label="SWING TRADING" 
                  value="Bullish" 
                  active 
                />
                <AnalysisCard 
                  type="day" 
                  label="DAY TRADING" 
                  value={bias.text} 
                  active 
                />
                <AnalysisCard 
                  type="news" 
                  label="NEWS FEED" 
                  value="High Impact" 
                  active 
                />
              </div>
            </div>

            {/* Chart Container */}
            <div className="flex-1 relative min-h-0">
              {/* Timeframe Selector */}
              <div className="absolute top-4 left-4 z-10 flex items-center gap-1 bg-gray-900/80 backdrop-blur rounded-lg p-1 border border-gray-800">
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf.value}
                    onClick={() => setTimeframe(tf.value)}
                    className={cn(
                      "px-3 py-1.5 rounded text-xs font-medium transition-all",
                      timeframe === tf.value
                        ? "bg-gray-700 text-white"
                        : "text-gray-400 hover:text-white hover:bg-gray-800"
                    )}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>

              {/* Refresh Button */}
              <button
                onClick={fetchChartData}
                className="absolute top-4 left-64 z-10 p-2 bg-gray-900/80 backdrop-blur rounded-lg border border-gray-800 text-gray-400 hover:text-white transition-colors"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </button>

              {/* Chart Annotations Overlay */}
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

              {/* Chart Loading State */}
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                    <span className="text-sm text-gray-500">Loading chart...</span>
                  </div>
                </div>
              )}

              {/* Error State */}
              {error && !loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]">
                  <div className="flex flex-col items-center gap-3">
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                    <span className="text-sm text-gray-400">{error}</span>
                    <button
                      onClick={fetchChartData}
                      className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              )}

              {/* Chart */}
              <div 
                ref={chartContainerRef} 
                className="w-full h-full"
                style={{ visibility: loading || error ? 'hidden' : 'visible' }}
              />

              {/* Bottom Time Labels */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-between px-16 py-2 text-xs text-gray-500 border-t border-gray-800 bg-[#0a0a0a]">
                <span>Monday</span>
                <span>Tuesday</span>
                <span>Wednesday</span>
                <span>Thursday</span>
                <span>Friday</span>
              </div>
            </div>

            {/* Bottom Bias Section */}
            <div className="border-t border-gray-800 bg-gray-900/30 p-4">
              <p className="text-sm text-gray-400">
                The day trading bias on <span className="text-white font-semibold">{selectedSymbol}</span> is{" "}
                <span className={cn(
                  "px-2 py-0.5 rounded font-semibold",
                  bias.color === "green" && "text-green-400 bg-green-500/10",
                  bias.color === "red" && "text-red-400 bg-red-500/10",
                  bias.color === "gray" && "text-gray-400 bg-gray-500/10"
                )}>
                  {bias.text.toLowerCase()}
                </span>
              </p>
              <p className="text-xs text-gray-500 mt-1">Updated {formatDistanceToNow(new Date(), { addSuffix: true })}</p>
            </div>
          </div>

          {/* Right News Panel */}
          <aside className="w-[420px] border-l border-gray-800 bg-[#0a0a0a] flex flex-col">
            {/* News Header */}
            <div className="h-14 flex items-center justify-between px-4 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <h2 className="font-semibold">News Feed</h2>
                <button className="text-gray-500 hover:text-white">
                  <Clock className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={fetchNews}
                  className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <RefreshCw className={cn("w-4 h-4", newsLoading && "animate-spin")} />
                </button>
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Filter className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Search className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* News Filter Tabs */}
            <div className="flex items-center gap-1 px-4 py-3 border-b border-gray-800">
              {["all", "popular", "high"].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setNewsFilter(filter as any)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2",
                    newsFilter === filter
                      ? "text-white"
                      : "text-gray-500 hover:text-gray-300"
                  )}
                >
                  {filter === "high" && newsFilter === "high" && (
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                  )}
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                </button>
              ))}
            </div>

            {/* News List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {newsLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-32 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                ))
              ) : filteredNews.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Newspaper className="w-6 h-6 text-gray-500" />
                  </div>
                  <p className="text-gray-500 text-sm">No news available</p>
                  <p className="text-gray-600 text-xs mt-1">Try selecting a different symbol</p>
                </div>
              ) : (
                filteredNews.map((item) => (
                  <NewsCard
                    key={item.id}
                    news={item}
                    isExpanded={expandedNewsId === item.id}
                    onToggle={() => setExpandedNewsId(expandedNewsId === item.id ? null : item.id)}
                  />
                ))
              )}
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
