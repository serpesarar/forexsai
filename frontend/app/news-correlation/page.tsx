"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time, type CandlestickData } from "lightweight-charts";
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
  Globe,
  Search,
  Filter,
  MoreHorizontal,
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
  ChevronDown,
  X
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
  price: number;
  change?: number;
}

interface ChartDataResponse {
  success: boolean;
  data: {
    symbol: string;
    timeframe: string;
    candles: ChartCandle[];
  };
}

// ==================== MOCK DATA ====================
const SYMBOLS: SymbolData[] = [
  { symbol: "XAUUSD", price: 4988.57, change: 0.85 },
  { symbol: "ESUSD", price: 6869.00, change: -0.32 },
  { symbol: "BTCUSD", price: 67020.65, change: 2.15 },
  { symbol: "DXUSD", price: 97.78, change: 0.12 },
  { symbol: "GBPJPY", price: 208.53, change: -0.45 },
  { symbol: "USDCAD", price: 1.37, change: 0.08 },
  { symbol: "^DJI", price: 49350.00, change: 0.56 },
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
  { value: "1M", label: "1M" },
];

// ==================== SIDEBAR NAVIGATION ====================
const SidebarItem = ({ 
  icon: Icon, 
  label, 
  active = false,
  badge,
  onClick 
}: { 
  icon: React.ElementType; 
  label: string; 
  active?: boolean;
  badge?: number;
  onClick?: () => void;
}) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-3 px-4 py-3 text-sm transition-all",
      active 
        ? "text-white bg-white/5 border-l-2 border-red-500" 
        : "text-gray-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent"
    )}
  >
    <Icon className={cn("w-5 h-5", active && "text-red-500")} />
    <span className="hidden lg:block">{label}</span>
    {badge && (
      <span className="ml-auto bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
        {badge}
      </span>
    )}
  </button>
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
        className="p-1 text-gray-500 hover:text-white transition-colors"
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
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all",
              selectedSymbol === sym.symbol
                ? "bg-gray-800 text-white"
                : "bg-gray-900/50 text-gray-400 hover:bg-gray-800 hover:text-white"
            )}
          >
            <span className="font-semibold">{sym.symbol}</span>
            <span className={cn(
              "text-xs",
              sym.change && sym.change > 0 ? "text-green-400" : sym.change && sym.change < 0 ? "text-red-400" : "text-gray-500"
            )}>
              ${sym.price.toLocaleString()}
            </span>
          </button>
        ))}
      </div>
      
      <button 
        onClick={() => scroll("right")}
        className="p-1 text-gray-500 hover:text-white transition-colors"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
      
      <button className="p-2 text-gray-500 hover:text-white transition-colors">
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
  active = false 
}: { 
  type: "swing" | "day" | "news";
  label: string;
  value: string;
  active?: boolean;
}) => {
  const styles = {
    swing: {
      bg: active ? "bg-green-500/10" : "bg-gray-900/50",
      border: active ? "border-green-500/50" : "border-gray-800",
      text: active ? "text-green-400" : "text-gray-400",
      icon: TrendingUp,
    },
    day: {
      bg: active ? "bg-red-500/10" : "bg-gray-900/50",
      border: active ? "border-red-500/50" : "border-gray-800",
      text: active ? "text-red-400" : "text-gray-400",
      icon: TrendingDown,
    },
    news: {
      bg: active ? "bg-gray-800" : "bg-gray-900/50",
      border: active ? "border-gray-600" : "border-gray-800",
      text: active ? "text-white" : "text-gray-400",
      icon: Newspaper,
    },
  };

  const style = styles[type];
  const Icon = style.icon;

  return (
    <button
      className={cn(
        "flex items-center gap-3 px-4 py-3 rounded-xl border transition-all",
        style.bg,
        style.border,
        "hover:border-gray-600"
      )}
    >
      <div className={cn("flex flex-col items-start")}>
        <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
        <span className={cn("text-sm font-semibold flex items-center gap-1", style.text)}>
          {type === "news" && <span className="w-1.5 h-1.5 rounded-full bg-red-500" />}
          {value}
          {type !== "news" && <Icon className="w-4 h-4" />}
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
          {news.urgency === "breaking" ? "BREAKING" : `${news.urgency} IMPACT`}
        </span>
        <span className="text-xs text-gray-500">
          {new Date(news.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </span>
        <span className="text-xs text-gray-600">•</span>
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(news.timestamp), { addSuffix: true })}
        </span>
        
        {/* Right actions */}
        <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1.5 text-gray-500 hover:text-white hover:bg-gray-800 rounded">
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>
          <span className="text-xs text-gray-500">11</span>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-white leading-snug mb-2 uppercase tracking-wide">
        {news.headline}
      </h3>

      {/* Description */}
      <p className="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-2">
        {news.content}
      </p>

      {/* Impact Badges */}
      <div className="flex flex-wrap gap-1.5">
        {news.impacts.slice(0, 6).map((impact, idx) => (
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
            {news.content}
          </p>
          
          {/* Market Impact Details */}
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
                <span className="text-xs text-gray-400">{Math.round(impact.confidence * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Right side icons */}
      <div className="absolute right-4 top-1/2 -translate-y-1/2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button className="p-2 text-gray-500 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition-colors">
          <Sparkles className="w-4 h-4" />
        </button>
        <button className="p-2 text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors">
          <Camera className="w-4 h-4" />
        </button>
      </div>
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
  const [expandedNewsId, setExpandedNewsId] = useState<string | null>(null);
  const [newsFilter, setNewsFilter] = useState<"all" | "popular" | "high">("high");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch chart data
        const chartResponse = await fetcher<ChartDataResponse>(
          `/api/data/ohlcv?symbol=${selectedSymbol}&timeframe=${timeframe}&limit=200`
        );
        
        if (chartResponse.success && chartResponse.data?.candles) {
          setChartData(chartResponse.data.candles);
        }

        // Fetch news
        const newsResponse = await fetcher<{ success: boolean; data: EnrichedNews[] }>(
          `/api/rss/news?symbol=${selectedSymbol}&limit=50&hours=48`
        );
        
        if (newsResponse.success && newsResponse.data) {
          setNews(newsResponse.data);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedSymbol, timeframe]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current || chartData.length === 0) return;

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
        tickMarkFormatter: (time: number) => {
          const date = new Date(time * 1000);
          return format(date, "HH:mm");
        },
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

    const formattedData = chartData.map((candle) => ({
      time: candle.time as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    candlestickSeries.setData(formattedData);
    chart.timeScale().fitContent();

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [chartData]);

  const filteredNews = news.filter((n) => {
    if (newsFilter === "all") return true;
    if (newsFilter === "high") return n.urgency === "breaking" || n.urgency === "high";
    return true;
  });

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex">
      {/* Left Sidebar */}
      <aside 
        className={cn(
          "flex-shrink-0 border-r border-gray-800 bg-[#0a0a0a] transition-all duration-300",
          sidebarCollapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-gray-800">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
            <span className="text-white font-bold text-sm">F</span>
          </div>
          {!sidebarCollapsed && (
            <span className="ml-3 font-bold text-lg">ForexSAI</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="py-4 space-y-1">
          <SidebarItem icon={Bell} label="Alerts" badge={3} />
          <SidebarItem icon={Star} label="Watchlist" />
          <SidebarItem icon={Wallet} label="Smart Trades" active />
          <SidebarItem icon={Calendar} label="Economic Calendar" />
          <SidebarItem icon={FileText} label="News Analysis" />
          <SidebarItem icon={MessageSquare} label="Chat AI" />
          <SidebarItem icon={Newspaper} label="Research Reports" />
          <SidebarItem icon={Building2} label="Brokers" />
          <SidebarItem icon={LineChart} label="My Trades" />
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
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
              <h1 className="text-2xl font-bold text-white mb-4">
                Gold slips to $4,993 as Philly Fed beat, trade deficit widen; Trump Iran threats support
              </h1>
              
              {/* Analysis Cards Row */}
              <div className="flex items-center gap-3">
                <AnalysisCard 
                  type="swing" 
                  label="SWING TRADING" 
                  value="Bullish" 
                  active 
                />
                <AnalysisCard 
                  type="day" 
                  label="DAY TRADING" 
                  value="Slightly Bearish" 
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
            <div className="flex-1 relative">
              {/* Timeframe Selector */}
              <div className="absolute top-4 left-4 z-10 flex items-center gap-1 bg-gray-900/80 backdrop-blur rounded-lg p-1">
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

              {/* Chart Annotations Overlay */}
              <div className="absolute top-4 right-4 z-10 space-y-2">
                <div className="bg-gray-900/80 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                  <span className="text-xs text-gray-400">Pullback Area:</span>
                  <span className="text-sm text-white ml-2 font-mono">$5080.00</span>
                </div>
                <div className="bg-gray-900/80 backdrop-blur px-3 py-2 rounded-lg border border-gray-800">
                  <span className="text-xs text-gray-400">Target Level:</span>
                  <span className="text-sm text-red-400 ml-2 font-mono">$4900.00</span>
                </div>
              </div>

              {/* Chart */}
              <div 
                ref={chartContainerRef} 
                className="w-full h-full"
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
                <span className="text-red-400 font-semibold bg-red-500/10 px-2 py-0.5 rounded">
                  slightly bearish
                </span>
              </p>
              <p className="text-xs text-gray-500 mt-1">Updated 1 hour ago</p>
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
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Filter className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Search className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Settings className="w-4 h-4" />
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
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                  )}
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                </button>
              ))}
            </div>

            {/* News List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-32 bg-gray-900/50 rounded-xl animate-pulse" />
                ))
              ) : filteredNews.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-sm">No news available</p>
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
