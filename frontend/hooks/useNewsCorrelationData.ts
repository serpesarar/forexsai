"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { fetcher } from "@/lib/api";
import { mockNewsCorrelationAPI } from "@/lib/mock/newsCorrelationMock";
import type { 
  EnrichedNews, 
  CandleData, 
  SupportedSymbol,
  NewsMarker 
} from "@/types/news-correlation";

// Feature flag to use mock data
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_NEWS === "true" || false;

interface UseNewsCorrelationDataOptions {
  symbol: SupportedSymbol;
  timeframe: string;
  bars?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseNewsCorrelationDataReturn {
  news: EnrichedNews[];
  candles: CandleData[];
  markers: NewsMarker[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastUpdated: Date | null;
}

function mapRssNewsToEnrichedNews(item: any): EnrichedNews {
  const sentiment = String(item.sentiment || "neutral").toLowerCase();
  return {
    id: item.id,
    timestamp: item.timestamp,
    source: item.source,
    headline: item.headline,
    content: item.content,
    category: item.category,
    url: item.url,
    impacts: Array.isArray(item.impacts) ? item.impacts : [],
    urgency: item.urgency || "medium",
    sentiment: sentiment === "bullish" ? "risk_on" : sentiment === "bearish" ? "risk_off" : "neutral",
    volatilityExpectation: item.volatility_expectation || "medium",
    eventDuration: item.event_duration || "short_term",
    affectedCandles: [],
    aiConfidence: Number(item.ai_confidence || 0),
    analysisTimestamp: item.analysis_timestamp || item.timestamp,
    headline_tr: item.headline_tr,
    content_tr: item.content_tr,
    summary_en: item.summary_en,
    summary_tr: item.summary_tr,
    analysis_en: item.analysis_en,
    analysis_tr: item.analysis_tr,
  };
}

export function useNewsCorrelationData({
  symbol,
  timeframe,
  bars = 200,
  autoRefresh = true,
  refreshInterval = 60000,
}: UseNewsCorrelationDataOptions): UseNewsCorrelationDataReturn {
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [candles, setCandles] = useState<CandleData[]>([]);
  const [markers, setMarkers] = useState<NewsMarker[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Generate markers from news
  const generateMarkers = useCallback((newsItems: EnrichedNews[], sym: SupportedSymbol): NewsMarker[] => {
    const markerMap = new Map<number, NewsMarker>();
    
    newsItems.forEach((item) => {
      const symbolImpact = item.impacts.find(
        (i) => i.symbol === sym || i.symbol === "*"
      );
      
      const hasGhostImpact = item.impacts.some(
        (i) => i.symbol !== sym && i.symbol !== "*"
      );
      
      if (!symbolImpact && !hasGhostImpact) return;
      
      const time = new Date(item.timestamp).getTime() / 1000;
      
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
      
      if (item.volatilityExpectation === "high") {
        color = "#f59e0b";
        shape = "square";
      }
      
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
    
    return Array.from(markerMap.values()).sort((a, b) => a.time - b.time);
  }, []);
  
  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      let newsData: EnrichedNews[];
      let candleData: CandleData[];
      
      if (USE_MOCK_DATA) {
        // Use mock data
        [newsData, candleData] = await Promise.all([
          mockNewsCorrelationAPI.getCorrelatedNews(symbol, timeframe),
          mockNewsCorrelationAPI.getChartData(symbol, timeframe, bars),
        ]);
      } else {
        // Use real API
        const symbolMap: Record<string, string> = {
          XAUUSD: "XAUUSD",
          NASDAQ: "NDX.INDX",
          DAX: "GDAXI.INDX",
          USOIL: "USOIL.FOREX",
          VIX: "VIX.INDX",
          DXY: "DXY.INDX",
          EURUSD: "EURUSD",
          GBPUSD: "GBPUSD",
          BTCUSD: "BTCUSD",
        };
        
        const apiSymbol = symbolMap[symbol] || symbol;
        
        const [newsResponse, chartResponse] = await Promise.all([
          fetcher<any[]>(
            `/api/rss/news?symbol=${encodeURIComponent(apiSymbol)}&hours=48&limit=50&show_on_chart=true`
          ),
          fetcher<{ success: boolean; data: { candles: CandleData[] } }>(
            `/api/data/cached/${apiSymbol}?timeframe=${timeframe}&bars=${bars}`
          ),
        ]);

        newsData = Array.isArray(newsResponse) ? newsResponse.map(mapRssNewsToEnrichedNews) : [];
        candleData = chartResponse.success && chartResponse.data 
          ? chartResponse.data.candles.map((c: any) => ({
              time: typeof c.time === "string" ? new Date(c.time).getTime() / 1000 : c.time,
              open: c.open,
              high: c.high,
              low: c.low,
              close: c.close,
              volume: c.volume,
            }))
          : [];
      }
      
      setNews(newsData);
      setCandles(candleData);
      setMarkers(generateMarkers(newsData, symbol));
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
      console.error("News correlation data error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe, bars, generateMarkers]);
  
  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, fetchData]);
  
  return {
    news,
    candles,
    markers,
    isLoading,
    error,
    refresh: fetchData,
    lastUpdated,
  };
}

export default useNewsCorrelationData;
