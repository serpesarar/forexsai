"use client";

import React, { memo, useCallback, useEffect, useState, useRef } from "react";
import { create } from "zustand";
import { 
  Newspaper, 
  CandlestickChart,
  Sparkles,
  RefreshCw,
  Settings2,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  AlertCircle
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetcher } from "@/lib/api";
import { useNewsCorrelation, useFilteredNews } from "@/lib/stores/useNewsCorrelation";
import { NewsCorrelationChart } from "@/components/NewsCorrelationChart";
import { NewsSidebar } from "@/components/NewsSidebar";
import type { 
  SupportedSymbol, 
  CandleData, 
  EnrichedNews,
  NewsMarker 
} from "@/types/news-correlation";

// Panel props
interface NewsChartCorrelationPanelProps {
  symbol?: SupportedSymbol;
  timeframe?: string;
  className?: string;
}

// API response type
interface ChartDataResponse {
  success: boolean;
  data?: {
    candles: CandleData[];
    symbol: string;
    timeframe: string;
  };
  error?: string;
}

// Symbol mapping
const symbolMap: Record<string, string> = {
  XAUUSD: "XAUUSD",
  NASDAQ: "NDX.INDX",
  DAX: "GDAXI.INDX",
  USOIL: "CL.COMM",
  VIX: "VIX.INDX",
  DXY: "DXY.INDX",
  EURUSD: "EURUSD",
  GBPUSD: "GBPUSD",
  BTCUSD: "BTCUSD",
};

// Main panel component
export const NewsChartCorrelationPanel = memo(function NewsChartCorrelationPanel({
  symbol: initialSymbol = "XAUUSD",
  timeframe: initialTimeframe = "1h",
  className,
}: NewsChartCorrelationPanelProps) {
  // Local state
  const [symbol, setSymbol] = useState<SupportedSymbol>(initialSymbol);
  const [timeframe, setTimeframe] = useState(initialTimeframe);
  const [candles, setCandles] = useState<CandleData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showGhostMarkers, setShowGhostMarkers] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // News correlation store
  const {
    news,
    selectedNewsIds,
    hoveredNewsId,
    markers,
    filters,
    setNews,
    setMarkers,
    selectCandle,
    selectNews,
    deselectNews,
    setHoveredNews,
    setFilter,
    clearSelection,
    setLoading: setStoreLoading,
    setError: setStoreError,
  } = useNewsCorrelation();
  
  // Refs
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  // Fetch chart data
  const fetchChartData = useCallback(async () => {
    try {
      setIsLoading(true);
      const apiSymbol = symbolMap[symbol] || symbol;
      
      const response = await fetcher<ChartDataResponse>(
        `/api/data/cached/${apiSymbol}?timeframe=${timeframe}&bars=200`
      );
      
      if (response.success && response.data) {
        // Transform to CandleData format
        const formattedCandles: CandleData[] = response.data.candles.map((c: any) => ({
          time: typeof c.time === "string" ? new Date(c.time).getTime() / 1000 : c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
          volume: c.volume,
        }));
        
        setCandles(formattedCandles);
      } else {
        setError("Failed to load chart data");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe]);
  
  // Fetch correlated news (try RSS first, fallback to old endpoint)
  const fetchCorrelatedNews = useCallback(async () => {
    try {
      setStoreLoading(true);
      const apiSymbol = symbolMap[symbol] || symbol;
      
      // Try new RSS endpoint first
      let response = await fetcher<{ success: boolean; data: EnrichedNews[] }>(
        `/api/rss/news?symbol=${apiSymbol}&hours=48&limit=100&skip_ai_filtered=true`
      );
      
      if (response.success && response.data && response.data.length > 0) {
        setNews(response.data);
      } else {
        // Fallback to old endpoint
        response = await fetcher<{ success: boolean; data: EnrichedNews[] }>(
          `/api/news-correlation/correlated/${apiSymbol}?timeframe=${timeframe}&impact_filter=${filters.impactLevel}`
        );
        
        if (response.success && response.data) {
          setNews(response.data);
        }
      }
    } catch (err) {
      setStoreError(err instanceof Error ? err.message : "Failed to fetch news");
    } finally {
      setStoreLoading(false);
    }
  }, [symbol, timeframe, filters.impactLevel, setNews, setStoreLoading, setStoreError]);
  
  // Initial data fetch
  useEffect(() => {
    fetchChartData();
    fetchCorrelatedNews();
  }, [fetchChartData, fetchCorrelatedNews]);
  
  // Auto-refresh setup
  useEffect(() => {
    refreshIntervalRef.current = setInterval(() => {
      fetchCorrelatedNews();
    }, 60000); // Refresh every minute
    
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [fetchCorrelatedNews]);
  
  // WebSocket connection for real-time news
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "wss://upbeat-flow-production.up.railway.app";
    const ws = new WebSocket(`${wsUrl}/api/news-correlation/ws/news`);
    
    ws.onopen = () => {
      console.log("News correlation WebSocket connected");
      // Subscribe to current symbol
      ws.send(JSON.stringify({ type: "subscribe", symbol }));
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === "news") {
          // Add new news to store
          useNewsCorrelation.getState().addNews(message.data);
        }
      } catch (err) {
        console.error("WebSocket message error:", err);
      }
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
    
    ws.onclose = () => {
      console.log("News correlation WebSocket disconnected");
    };
    
    wsRef.current = ws;
    
    return () => {
      ws.close();
    };
  }, [symbol]);
  
  // Generate markers from news when news or symbol changes
  useEffect(() => {
    const newMarkers: NewsMarker[] = [];
    const markerMap = new Map<number, NewsMarker>();
    
    news.forEach((item) => {
      const symbolImpact = item.impacts.find(
        (i) => i.symbol === symbol || i.symbol === "*"
      );
      
      const hasGhostImpact = item.impacts.some(
        (i) => i.symbol !== symbol && i.symbol !== "*"
      );
      
      if (!symbolImpact && !hasGhostImpact) return;
      
      const time = new Date(item.timestamp).getTime() / 1000;
      
      // Determine marker properties
      let color = "#eab308";
      let shape: NewsMarker["shape"] = "circle";
      let position: NewsMarker["position"] = "aboveBar";
      
      if (symbolImpact) {
        switch (symbolImpact.direction) {
          case "bullish":
            color = "#22c55e";
            shape = "arrowUp";
            position = "belowBar";
            break;
          case "bearish":
            color = "#ef4444";
            shape = "arrowDown";
            position = "aboveBar";
            break;
          case "neutral":
            color = "#eab308";
            shape = "square";
            break;
        }
      }
      
      // High volatility
      if (item.volatilityExpectation === "high") {
        color = "#f59e0b";
        shape = "square";
      }
      
      // Check existing marker
      const existing = markerMap.get(time);
      if (existing) {
        existing.newsIds.push(item.id);
        existing.impactCount += symbolImpact ? 1 : 0;
        existing.tooltip = `${existing.newsIds.length} news events`;
        if (symbolImpact && symbolImpact.score > 7) {
          existing.color = color;
        }
      } else {
        markerMap.set(time, {
          time,
          position,
          color,
          shape,
          size: symbolImpact?.score ? Math.min(8 + symbolImpact.score, 20) : 10,
          newsIds: [item.id],
          tooltip: item.headline.substring(0, 50) + "...",
          impactCount: symbolImpact ? 1 : 0,
          isGhost: !symbolImpact,
          symbol: !symbolImpact ? item.impacts[0]?.symbol : undefined,
        });
      }
    });
    
    setMarkers(Array.from(markerMap.values()).sort((a, b) => a.time - b.time));
  }, [news, symbol, setMarkers]);
  
  // Event handlers
  const handleCandleClick = useCallback((candle: CandleData | null) => {
    selectCandle(candle);
  }, [selectCandle]);
  
  const handleMarkerClick = useCallback((newsIds: string[]) => {
    // Select all related news
    clearSelection();
    newsIds.forEach((id) => selectNews(id));
  }, [clearSelection, selectNews]);
  
  const handleNewsSelect = useCallback((newsId: string) => {
    if (selectedNewsIds.includes(newsId)) {
      deselectNews(newsId);
    } else {
      clearSelection();
      selectNews(newsId);
    }
  }, [selectedNewsIds, deselectNews, clearSelection, selectNews]);
  
  const handleNewsHover = useCallback((newsId: string | null) => {
    setHoveredNews(newsId);
  }, [setHoveredNews]);
  
  const handleTimeRangeChange = useCallback((range: { from: number; to: number }) => {
    // Could use this to filter news based on visible chart range
  }, []);
  
  const handleRefresh = useCallback(() => {
    fetchChartData();
    fetchCorrelatedNews();
  }, [fetchChartData, fetchCorrelatedNews]);
  
  const handleSymbolChange = useCallback((newSymbol: SupportedSymbol) => {
    setSymbol(newSymbol);
    clearSelection();
  }, [clearSelection]);
  
  // Filtered news
  const filteredNews = useFilteredNews();
  
  return (
    <div 
      className={cn(
        "flex flex-col bg-slate-950 rounded-xl border border-slate-800 overflow-hidden",
        isFullscreen ? "fixed inset-0 z-50" : "h-[600px]",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Newspaper className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                News-Chart Correlation
                <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
              </h2>
              <p className="text-[10px] text-slate-400">
                AI-analyzed events on chart
              </p>
            </div>
          </div>
          
          {/* Symbol selector */}
          <div className="flex items-center gap-1 ml-4">
            {["XAUUSD", "NASDAQ", "DAX", "USOIL"].map((sym) => (
              <button
                key={sym}
                onClick={() => handleSymbolChange(sym as SupportedSymbol)}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-xs font-medium transition-all",
                  symbol === sym
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 border border-transparent"
                )}
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex items-center gap-2">
          {/* Ghost markers toggle */}
          <button
            onClick={() => setShowGhostMarkers(!showGhostMarkers)}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-all",
              showGhostMarkers
                ? "bg-slate-800 text-slate-300"
                : "bg-slate-800/50 text-slate-500"
            )}
            title="Toggle ghost markers (indirect impacts)"
          >
            {showGhostMarkers ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Ghost</span>
          </button>
          
          {/* Refresh */}
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 transition-all disabled:opacity-50"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isLoading && "animate-spin")} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          
          {/* Fullscreen */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 transition-all"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
      
      {/* Main content */}
      {error ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
            <p className="text-slate-400">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden">
          {/* Chart area */}
          <div className="flex-1 min-w-0">
            <NewsCorrelationChart
              symbol={symbol}
              timeframe={timeframe}
              candles={candles}
              markers={markers}
              selectedNewsIds={selectedNewsIds}
              hoveredNewsId={hoveredNewsId}
              news={news}
              showGhostMarkers={showGhostMarkers}
              onCandleClick={handleCandleClick}
              onMarkerClick={handleMarkerClick}
              onTimeRangeChange={handleTimeRangeChange}
            />
          </div>
          
          {/* Sidebar */}
          <NewsSidebar
            news={filteredNews}
            selectedNewsIds={selectedNewsIds}
            hoveredNewsId={hoveredNewsId}
            currentSymbol={symbol}
            isLoading={isLoading}
            filters={filters}
            onFilterChange={setFilter}
            onNewsSelect={handleNewsSelect}
            onNewsHover={handleNewsHover}
            onScrollToNews={() => {}}
            className="w-80 hidden lg:flex"
          />
        </div>
      )}
      
      {/* Mobile sidebar toggle (shown on small screens) */}
      <div className="lg:hidden p-3 border-t border-slate-800 bg-slate-900/50">
        <button
          className="w-full flex items-center justify-center gap-2 py-2 bg-slate-800 rounded-lg text-sm text-slate-300"
          onClick={() => {/* Toggle mobile drawer */}}
        >
          <Newspaper className="w-4 h-4" />
          View {filteredNews.length} News Events
        </button>
      </div>
    </div>
  );
});

export default NewsChartCorrelationPanel;
