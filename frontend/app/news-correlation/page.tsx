"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time, type CandlestickData } from "lightweight-charts";
import { format, isWithinInterval, subMinutes, addMinutes } from "date-fns";
import { 
  Bell, Star, Wallet, Calendar, FileText, MessageSquare, Newspaper,
  Building2, LineChart, BookOpen, Filter, ChevronLeft, ChevronRight,
  TrendingUp, TrendingDown, Sparkles, Camera, Settings,
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

const NewsCard = ({ news, onClick }: { news: EnrichedNews, onClick: () => void }) => {
  const isHighImpact = news.urgency === "breaking" || news.urgency === "high";
  
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
        {news.headline}
      </h3>
      
      <p className="text-xs text-gray-400 leading-relaxed mb-3 line-clamp-2">
        {news.content || news.headline}
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
        USOIL: "CL.COMM",
        VIX: "VIX.INDX",
        DXY: "DXY.INDX",
      };
      const apiSymbol = symbolMap[selectedSymbol] || selectedSymbol;

      const response = await fetcher<OHLCVResponse>(
        `/api/data/ohlcv?symbol=${apiSymbol}&timeframe=${timeframe}&limit=200`
      );

      if (response?.data && Array.isArray(response.data) && response.data.length > 0) {
        const processedCandles: ChartCandle[] = response.data.map((row) => {
          // Convert ms to seconds for lightweight-charts
          const timeInSeconds = Math.floor(row.timestamp / 1000);
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

  // Fetch news
  const fetchNews = useCallback(async () => {
    try {
      setNewsLoading(true);
      
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
      
      // Filter news for selected symbol if we have news
      if (newsData.length > 0 && selectedSymbol) {
        const symbolMappings: Record<string, string[]> = {
          'XAUUSD': ['XAUUSD', 'XAU/USD', 'GOLD', 'GC'],
          'NDX': ['NDX', 'NASDAQ', 'IXIC', 'NDX.INDX'],
          'DAX': ['DAX', 'GDAXI', 'GDAXI.INDX', 'DE40'],
          'USOIL': ['USOIL', 'WTI', 'CL', 'CL.COMM', 'OIL'],
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
      setNews([]);
    } finally {
      setNewsLoading(false);
    }
  }, [selectedSymbol]);

  // WebSocket connection for live prices
  useEffect(() => {
    if (!mounted) return;

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
                // Map backend symbol names to frontend
                const backendToFrontend: Record<string, string> = {
                  "XAUUSD": "XAUUSD",
                  "NDX.INDX": "NDX",
                  "GDAXI.INDX": "DAX",
                  "CL.COMM": "USOIL",
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
          // Reconnect after 5 seconds
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
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [mounted]);

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

  const currentSymbol = symbols.find(s => s.symbol === selectedSymbol);

  if (!mounted) {
    return <div className="min-h-screen bg-[#0a0a0a]" />;
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex">
      {/* Sidebar */}
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

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
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

        <div className="flex-1 flex overflow-hidden" style={{ height: 'calc(100vh - 140px)' }}>
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

          {/* News Panel */}
          <aside className="w-[420px] border-l border-gray-800 bg-[#0a0a0a] flex flex-col">
            <div className="h-14 flex items-center justify-between px-4 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <h2 className="font-semibold">News Feed</h2>
                {wsConnected && <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
              </div>
              <div className="flex items-center gap-2">
                <select 
                  value={currentLocale} 
                  onChange={(e) => setCurrentLocale(e.target.value)}
                  className="bg-gray-900 border border-gray-800 rounded-lg px-2 py-1 text-xs text-gray-400"
                >
                  <option value="tr">🇹🇷 TR</option>
                  <option value="en">🇬🇧 EN</option>
                  <option value="de">🇩🇪 DE</option>
                  <option value="es">🇪🇸 ES</option>
                  <option value="fr">🇫🇷 FR</option>
                  <option value="ar">🇸🇦 AR</option>
                </select>
                <button onClick={fetchNews} className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg">
                  <RefreshCw className={cn("w-4 h-4", newsLoading && "animate-spin")} />
                </button>
              </div>
            </div>

            <div className="flex items-center gap-1 px-4 py-3 border-b border-gray-800">
              {["all", "popular", "high"].map((filter) => (
                <button 
                  key={filter} 
                  onClick={() => setNewsFilter(filter as any)} 
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                    newsFilter === filter ? "text-white" : "text-gray-500 hover:text-gray-300"
                  )}
                >
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {newsLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-32 bg-gray-900/50 rounded-xl animate-pulse border border-gray-800" />
                ))
              ) : filteredNews.length === 0 ? (
                <div className="text-center py-12">
                  <Newspaper className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-500 text-sm">No news available</p>
                </div>
              ) : (
                filteredNews.map((item) => (
                  <NewsCard 
                    key={item.id} 
                    news={item} 
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
