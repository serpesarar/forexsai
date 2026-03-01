"use client";

import React, { memo, useCallback, useMemo, useRef, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import { 
  AlertTriangle, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Filter,
  ChevronDown,
  Sparkles,
  Zap,
  Activity,
  Calendar,
  Target
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ImpactBadgeRow } from "./ImpactBadge";
import type { 
  EnrichedNews, 
  SupportedSymbol, 
  ImpactDirection 
} from "@/types/news-correlation";

interface NewsSidebarProps {
  news: EnrichedNews[];
  selectedNewsIds: string[];
  hoveredNewsId: string | null;
  currentSymbol: SupportedSymbol;
  isLoading?: boolean;
  filters: {
    impactLevel: "all" | "high" | "medium" | "low";
    sentiment: "all" | "bullish" | "bearish" | "neutral";
  };
  onFilterChange: (key: string, value: any) => void;
  onNewsSelect: (newsId: string) => void;
  onNewsHover: (newsId: string | null) => void;
  onScrollToNews: (newsId: string) => void;
  className?: string;
}

// Sentiment icon mapping
const sentimentIcons = {
  risk_on: <TrendingUp className="w-4 h-4 text-green-400" />,
  risk_off: <TrendingDown className="w-4 h-4 text-red-400" />,
  neutral: <Minus className="w-4 h-4 text-yellow-400" />,
};

// Volatility indicator
const VolatilityIndicator = memo(function VolatilityIndicator({
  level,
}: {
  level: "high" | "medium" | "low";
}) {
  const colors = {
    high: "text-red-400 bg-red-500/10 border-red-500/30",
    medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    low: "text-green-400 bg-green-500/10 border-green-500/30",
  };
  
  const icons = {
    high: <Zap className="w-3 h-3" />,
    medium: <Activity className="w-3 h-3" />,
    low: <Minus className="w-3 h-3" />,
  };
  
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border",
        colors[level]
      )}
    >
      {icons[level]}
      <span className="capitalize">{level}</span>
    </span>
  );
});

// Confidence bar
const ConfidenceBar = memo(function ConfidenceBar({
  confidence,
}: {
  confidence: number;
}) {
  let colorClass = "bg-green-500";
  if (confidence < 60) colorClass = "bg-yellow-500";
  if (confidence < 40) colorClass = "bg-red-500";
  
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={cn("h-full transition-all duration-500", colorClass)}
          style={{ width: `${confidence}%` }}
        />
      </div>
      <span className="text-slate-400 w-9 text-right">{Math.round(confidence)}%</span>
    </div>
  );
});

// Individual news card
interface NewsCardProps {
  news: EnrichedNews;
  isSelected: boolean;
  isHighlighted: boolean;
  currentSymbol: SupportedSymbol;
  onSelect: () => void;
  onHover: () => void;
  onLeave: () => void;
}

const NewsCard = memo(function NewsCard({
  news,
  isSelected,
  isHighlighted,
  currentSymbol,
  onSelect,
  onHover,
  onLeave,
}: NewsCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  
  // Scroll into view if selected
  useEffect(() => {
    if (isSelected && cardRef.current) {
      cardRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [isSelected]);
  
  const maxImpact = useMemo(() => {
    return Math.max(...news.impacts.map((i) => i.score));
  }, [news.impacts]);
  
  const currentSymbolImpact = useMemo(() => {
    return news.impacts.find(
      (i) => i.symbol === currentSymbol || i.symbol === "*"
    );
  }, [news.impacts, currentSymbol]);
  
  const timeAgo = useMemo(() => {
    try {
      return formatDistanceToNow(new Date(news.timestamp), { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  }, [news.timestamp]);
  
  // Impact level badge
  const getImpactBadge = () => {
    if (maxImpact >= 8) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-500/20 text-red-400 text-xs font-semibold border border-red-500/30">
          <AlertTriangle className="w-3 h-3" />
          HIGH IMPACT
        </span>
      );
    }
    if (maxImpact >= 5) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 text-xs font-medium border border-yellow-500/30">
          <Activity className="w-3 h-3" />
          MEDIUM
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-700 text-slate-400 text-xs">
        <Minus className="w-3 h-3" />
        LOW
      </span>
    );
  };
  
  return (
    <div
      ref={cardRef}
      onClick={onSelect}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      className={cn(
        "relative p-4 rounded-xl border transition-all duration-300 cursor-pointer",
        "backdrop-blur-sm",
        
        // Selection state
        isSelected && [
          "border-l-4",
          currentSymbolImpact?.direction === "bullish" && "border-l-green-500 border-green-500/50 bg-green-500/5",
          currentSymbolImpact?.direction === "bearish" && "border-l-red-500 border-red-500/50 bg-red-500/5",
          currentSymbolImpact?.direction === "neutral" && "border-l-yellow-500 border-yellow-500/50 bg-yellow-500/5",
          !currentSymbolImpact && "border-l-blue-500 border-blue-500/50 bg-blue-500/5",
          "shadow-lg",
        ],
        
        // Highlight state (from chart hover)
        isHighlighted && !isSelected && [
          "border-slate-400 bg-slate-800/60",
          "ring-1 ring-slate-400/50",
        ],
        
        // Default state
        !isSelected && !isHighlighted && [
          "border-slate-800 bg-slate-900/50",
          "hover:border-slate-600 hover:bg-slate-800/50",
        ],
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {getImpactBadge()}
          <VolatilityIndicator level={news.volatilityExpectation} />
        </div>
        <div className="flex items-center gap-1 text-slate-400 text-xs">
          <Clock className="w-3 h-3" />
          {timeAgo}
        </div>
      </div>
      
      {/* Source */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          {news.source}
        </span>
        {sentimentIcons[news.sentiment]}
      </div>
      
      {/* Headline */}
      <h3 className={cn(
        "text-sm font-semibold leading-snug mb-3",
        isSelected ? "text-white" : "text-slate-200"
      )}>
        {news.headline}
      </h3>
      
      {/* Impact Badges */}
      <div className="mb-3">
        <ImpactBadgeRow
          impacts={news.impacts}
          currentSymbol={currentSymbol}
          maxVisible={5}
          size="sm"
          interactive={false}
        />
      </div>
      
      {/* Key Levels (if any) */}
      {news.keyLevels && (
        <div className="flex items-center gap-3 mb-3 text-xs">
          {news.keyLevels.support && news.keyLevels.support.length > 0 && (
            <div className="flex items-center gap-1 text-green-400">
              <Target className="w-3 h-3" />
              <span>Support: {news.keyLevels.support.slice(0, 2).join(", ")}</span>
            </div>
          )}
          {news.keyLevels.resistance && news.keyLevels.resistance.length > 0 && (
            <div className="flex items-center gap-1 text-red-400">
              <Target className="w-3 h-3" />
              <span>Resistance: {news.keyLevels.resistance.slice(0, 2).join(", ")}</span>
            </div>
          )}
        </div>
      )}
      
      {/* Footer: AI Confidence */}
      <div className="pt-3 border-t border-slate-800">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-slate-500 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            AI Confidence
          </span>
          {news.aiConfidence < 60 && (
            <span className="text-yellow-500 text-[10px]">Analysis Uncertain</span>
          )}
        </div>
        <ConfidenceBar confidence={news.aiConfidence} />
      </div>
      
      {/* Pulse animation for high impact breaking news */}
      {maxImpact >= 9 && (
        <div className="absolute top-2 right-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
          </span>
        </div>
      )}
    </div>
  );
});

// Filter bar component
interface FilterBarProps {
  filters: NewsSidebarProps["filters"];
  onFilterChange: (key: string, value: any) => void;
}

const FilterBar = memo(function FilterBar({
  filters,
  onFilterChange,
}: FilterBarProps) {
  return (
    <div className="p-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-3">
        <Filter className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-medium text-slate-300">Filters</span>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {/* Impact Filter */}
        <div className="relative">
          <select
            value={filters.impactLevel}
            onChange={(e) => onFilterChange("impactLevel", e.target.value)}
            className={cn(
              "appearance-none bg-slate-800 text-slate-300 text-xs px-3 py-1.5 pr-8 rounded-lg",
              "border border-slate-700 focus:border-blue-500 focus:outline-none",
              "cursor-pointer hover:bg-slate-750 transition-colors"
            )}
          >
            <option value="all">All Impact</option>
            <option value="high">High (7-10)</option>
            <option value="medium">Medium (4-6)</option>
            <option value="low">Low (1-3)</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500 pointer-events-none" />
        </div>
        
        {/* Sentiment Filter */}
        <div className="relative">
          <select
            value={filters.sentiment}
            onChange={(e) => onFilterChange("sentiment", e.target.value)}
            className={cn(
              "appearance-none bg-slate-800 text-slate-300 text-xs px-3 py-1.5 pr-8 rounded-lg",
              "border border-slate-700 focus:border-blue-500 focus:outline-none",
              "cursor-pointer hover:bg-slate-750 transition-colors"
            )}
          >
            <option value="all">All Sentiment</option>
            <option value="risk_on">Risk On</option>
            <option value="risk_off">Risk Off</option>
            <option value="neutral">Neutral</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-500 pointer-events-none" />
        </div>
      </div>
    </div>
  );
});

// Main sidebar component
export const NewsSidebar = memo(function NewsSidebar({
  news,
  selectedNewsIds,
  hoveredNewsId,
  currentSymbol,
  isLoading,
  filters,
  onFilterChange,
  onNewsSelect,
  onNewsHover,
  className,
}: NewsSidebarProps) {
  const newsListRef = useRef<HTMLDivElement>(null);
  
  // Filter news
  const filteredNews = useMemo(() => {
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
      
      return true;
    });
  }, [news, filters]);
  
  const handleSelect = useCallback((newsId: string) => {
    onNewsSelect(newsId);
  }, [onNewsSelect]);
  
  const handleHover = useCallback((newsId: string | null) => {
    onNewsHover(newsId);
  }, [onNewsHover]);
  
  return (
    <div className={cn(
      "flex flex-col h-full bg-slate-950/80 backdrop-blur-xl border-l border-slate-800",
      className
    )}>
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-400" />
              Live News
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              AI-analyzed market events
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-xs text-slate-500">Live</span>
          </div>
        </div>
      </div>
      
      {/* Filters */}
      <FilterBar filters={filters} onFilterChange={onFilterChange} />
      
      {/* Stats summary */}
      <div className="px-4 py-2 bg-slate-900/30 border-b border-slate-800">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500">
            {filteredNews.length} of {news.length} events
          </span>
          <span className="text-slate-500 flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            Last 24h
          </span>
        </div>
      </div>
      
      {/* News List */}
      <div 
        ref={newsListRef}
        className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent"
      >
        {isLoading ? (
          // Loading skeletons
          Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="p-4 rounded-xl border border-slate-800 bg-slate-900/30 animate-pulse"
            >
              <div className="h-4 bg-slate-800 rounded w-1/3 mb-3"></div>
              <div className="h-3 bg-slate-800 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-slate-800 rounded w-1/2"></div>
            </div>
          ))
        ) : filteredNews.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
              <Calendar className="w-8 h-8 text-slate-600" />
            </div>
            <p className="text-slate-400 text-sm">No news matching filters</p>
            <p className="text-slate-600 text-xs mt-1">
              Try adjusting your filter criteria
            </p>
          </div>
        ) : (
          // News cards
          filteredNews.map((item) => (
            <NewsCard
              key={item.id}
              news={item}
              isSelected={selectedNewsIds.includes(item.id)}
              isHighlighted={hoveredNewsId === item.id}
              currentSymbol={currentSymbol}
              onSelect={() => handleSelect(item.id)}
              onHover={() => handleHover(item.id)}
              onLeave={() => handleHover(null)}
            />
          ))
        )}
      </div>
      
      {/* Bottom actions */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/50">
        <button
          onClick={() => onFilterChange("impactLevel", "all")}
          className="w-full py-2 text-xs text-slate-400 hover:text-white transition-colors"
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
});

export default NewsSidebar;
