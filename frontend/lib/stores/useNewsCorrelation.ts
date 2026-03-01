"use client";

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import type {
  CorrelationState,
  EnrichedNews,
  CandleData,
  SupportedSymbol,
  NewsMarker,
} from "@/types/news-correlation";

// Helper to generate markers from news
const generateMarkersFromNews = (
  news: EnrichedNews[],
  currentSymbol: SupportedSymbol
): NewsMarker[] => {
  const markerMap = new Map<number, NewsMarker>();

  news.forEach((item) => {
    // Check if this news affects the current symbol
    const symbolImpact = item.impacts.find(
      (i) => i.symbol === currentSymbol || i.symbol === "*"
    );
    
    // Also check for ghost markers (other symbols)
    const hasGhostImpact = item.impacts.some(
      (i) => i.symbol !== currentSymbol && i.symbol !== "*"
    );

    if (!symbolImpact && !hasGhostImpact) return;

    const time = new Date(item.timestamp).getTime() / 1000;
    
    // Determine marker properties
    let color = "#eab308"; // Default yellow for mixed/neutral
    let shape: NewsMarker["shape"] = "circle";
    let position: NewsMarker["position"] = "aboveBar";

    if (symbolImpact) {
      switch (symbolImpact.direction) {
        case "bullish":
          color = "#22c55e"; // Green
          shape = "arrowUp";
          position = "belowBar";
          break;
        case "bearish":
          color = "#ef4444"; // Red
          shape = "arrowDown";
          position = "aboveBar";
          break;
        case "neutral":
          color = "#eab308"; // Yellow
          shape = "square";
          break;
      }
    }

    // High volatility events get yellow diamond
    if (item.volatilityExpectation === "high") {
      color = "#f59e0b";
      shape = "square";
    }

    // Check if marker already exists at this time
    const existing = markerMap.get(time);
    if (existing) {
      existing.newsIds.push(item.id);
      existing.impactCount += symbolImpact ? 1 : 0;
      existing.tooltip = `${existing.newsIds.length} news events`;
      // Upgrade color if higher impact
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
};

// Create the store
export const useNewsCorrelation = create<CorrelationState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        selectedCandle: null,
        selectedNewsIds: [],
        highlightedTimeRange: null,
        hoveredNewsId: null,
        news: [],
        markers: [],
        isLoading: false,
        error: null,
        filters: {
          impactLevel: "all",
          affectedSymbols: [],
          sentiment: "all",
          timeRange: null,
        },

        // Actions
        selectCandle: (candle) => {
          set({ selectedCandle: candle });
          
          // If candle selected, find related news
          if (candle) {
            const { news } = get();
            const candleTime = candle.time;
            const windowSeconds = 300; // 5 minute window
            
            const relatedNews = news.filter((n) => {
              const newsTime = new Date(n.timestamp).getTime() / 1000;
              return Math.abs(newsTime - candleTime) <= windowSeconds;
            });
            
            set({ selectedNewsIds: relatedNews.map((n) => n.id) });
          }
        },

        selectNews: (newsId) => {
          const { selectedNewsIds } = get();
          if (!selectedNewsIds.includes(newsId)) {
            set({ selectedNewsIds: [...selectedNewsIds, newsId] });
          }
        },

        deselectNews: (newsId) => {
          const { selectedNewsIds } = get();
          set({
            selectedNewsIds: selectedNewsIds.filter((id) => id !== newsId),
          });
        },

        clearSelection: () => {
          set({
            selectedCandle: null,
            selectedNewsIds: [],
            highlightedTimeRange: null,
          });
        },

        highlightTimeRange: (range) => {
          set({ highlightedTimeRange: range });
        },

        setHoveredNews: (newsId) => {
          set({ hoveredNewsId: newsId });
        },

        setNews: (news) => {
          set({ news });
          // Regenerate markers
          const currentSymbol = "XAUUSD"; // This should come from chart store
          const markers = generateMarkersFromNews(news, currentSymbol);
          set({ markers });
        },

        setMarkers: (markers) => {
          set({ markers });
        },

        setLoading: (loading) => {
          set({ isLoading: loading });
        },

        setError: (error) => {
          set({ error });
        },

        setFilter: (key, value) => {
          set((state) => ({
            filters: {
              ...state.filters,
              [key]: value,
            },
          }));
        },

        addNews: (newsItem) => {
          const { news, filters } = get();
          
          // Check if news matches current filters
          const matchesFilters = (() => {
            if (filters.impactLevel !== "all") {
              const maxImpact = Math.max(...newsItem.impacts.map((i) => i.score));
              if (filters.impactLevel === "high" && maxImpact < 7) return false;
              if (filters.impactLevel === "medium" && (maxImpact < 4 || maxImpact >= 7)) return false;
              if (filters.impactLevel === "low" && maxImpact >= 4) return false;
            }
            
            if (filters.sentiment !== "all" && newsItem.sentiment !== filters.sentiment) {
              return false;
            }
            
            if (filters.affectedSymbols.length > 0) {
              const hasMatchingSymbol = newsItem.impacts.some((i) =>
                filters.affectedSymbols.includes(i.symbol)
              );
              if (!hasMatchingSymbol) return false;
            }
            
            return true;
          })();
          
          if (!matchesFilters) return;
          
          const updatedNews = [newsItem, ...news].sort(
            (a, b) =>
              new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          );
          
          set({ news: updatedNews });
          
          // Regenerate markers
          const currentSymbol = "XAUUSD"; // Should come from chart store
          const markers = generateMarkersFromNews(updatedNews, currentSymbol);
          set({ markers });
        },

        removeNews: (newsId) => {
          const { news } = get();
          const updatedNews = news.filter((n) => n.id !== newsId);
          set({ news: updatedNews });
          
          // Regenerate markers
          const currentSymbol = "XAUUSD"; // Should come from chart store
          const markers = generateMarkersFromNews(updatedNews, currentSymbol);
          set({ markers });
        },
      }),
      {
        name: "news-correlation-store",
        partialize: (state) => ({
          filters: state.filters,
        }),
      }
    ),
    { name: "NewsCorrelationStore" }
  )
);

// Selector hooks for performance
export const useNewsById = (id: string) => {
  return useNewsCorrelation((state) =>
    state.news.find((n) => n.id === id)
  );
};

export const useNewsForSymbol = (symbol: SupportedSymbol) => {
  return useNewsCorrelation((state) =>
    state.news.filter((n) =>
      n.impacts.some((i) => i.symbol === symbol || i.symbol === "*")
    )
  );
};

export const useSelectedNews = () => {
  return useNewsCorrelation((state) =>
    state.news.filter((n) => state.selectedNewsIds.includes(n.id))
  );
};

export const useFilteredNews = () => {
  return useNewsCorrelation((state) => {
    const { news, filters } = state;
    
    return news.filter((item) => {
      // Impact filter
      if (filters.impactLevel !== "all") {
        const maxImpact = Math.max(...item.impacts.map((i) => i.score));
        if (filters.impactLevel === "high" && maxImpact < 7) return false;
        if (filters.impactLevel === "medium" && (maxImpact < 4 || maxImpact >= 7)) return false;
        if (filters.impactLevel === "low" && maxImpact >= 4) return false;
      }
      
      // Sentiment filter
      if (filters.sentiment !== "all" && item.sentiment !== filters.sentiment) {
        return false;
      }
      
      // Symbol filter
      if (filters.affectedSymbols.length > 0) {
        const hasMatchingSymbol = item.impacts.some((i) =>
          filters.affectedSymbols.includes(i.symbol)
        );
        if (!hasMatchingSymbol) return false;
      }
      
      // Time range filter
      if (filters.timeRange) {
        const newsTime = new Date(item.timestamp).getTime();
        if (newsTime < filters.timeRange.start || newsTime > filters.timeRange.end) {
          return false;
        }
      }
      
      return true;
    });
  });
};

export default useNewsCorrelation;
