"use client";

import React, { useState, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Filter,
  Search
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetcher } from "@/lib/api";
import type { EnrichedNews, NewsUrgency } from "@/types/news-correlation";

interface NewsFeedListProps {
  onNewsClick?: (news: EnrichedNews) => void;
  className?: string;
}

// Impact badge colors
const impactColors = {
  breaking: {
    bg: "bg-red-500/20",
    border: "border-red-500/50",
    text: "text-red-400",
    label: "BREAKING",
    dot: "bg-red-500",
  },
  high: {
    bg: "bg-red-900/30",
    border: "border-red-700/50",
    text: "text-red-300",
    label: "HIGH IMPACT",
    dot: "bg-red-400",
  },
  medium: {
    bg: "bg-yellow-900/30",
    border: "border-yellow-700/50",
    text: "text-yellow-300",
    label: "MEDIUM",
    dot: "bg-yellow-400",
  },
  low: {
    bg: "bg-slate-800/50",
    border: "border-slate-700/50",
    text: "text-slate-400",
    label: "LOW",
    dot: "bg-slate-500",
  },
};

// Symbol impact badge
const SymbolImpactBadge = ({ 
  symbol, 
  direction, 
  score 
}: { 
  symbol: string; 
  direction: string; 
  score: number;
}) => {
  const isBullish = direction === "bullish";
  const isBearish = direction === "bearish";
  
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border",
        isBullish && "bg-green-500/20 text-green-400 border-green-500/30",
        isBearish && "bg-red-500/20 text-red-400 border-red-500/30",
        !isBullish && !isBearish && "bg-slate-700 text-slate-400 border-slate-600"
      )}
    >
      {isBullish && <TrendingUp className="w-3 h-3" />}
      {isBearish && <TrendingDown className="w-3 h-3" />}
      {!isBullish && !isBearish && <Minus className="w-3 h-3" />}
      <span>{symbol}</span>
      <span className="opacity-70">{score}/10</span>
    </span>
  );
};

// News Card Component
const NewsCard = ({ 
  news, 
  isExpanded, 
  onToggle 
}: { 
  news: EnrichedNews; 
  isExpanded: boolean;
  onToggle: () => void;
}) => {
  const impactStyle = impactColors[news.urgency as keyof typeof impactColors] || impactColors.low;
  const maxImpact = Math.max(...news.impacts.map(i => i.score), 0);
  
  // Get primary symbol impact
  const primaryImpact = news.impacts[0];
  
  return (
    <div
      className={cn(
        "relative rounded-xl border overflow-hidden transition-all duration-300",
        "backdrop-blur-sm",
        impactStyle.bg,
        impactStyle.border,
        isExpanded ? "shadow-2xl shadow-red-900/20" : "hover:shadow-lg hover:shadow-red-900/10"
      )}
    >
      {/* Top bar with impact indicator */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <span className={cn("w-2 h-2 rounded-full animate-pulse", impactStyle.dot)} />
          <span className={cn("text-xs font-bold tracking-wider", impactStyle.text)}>
            {impactStyle.label}
          </span>
          <span className="text-slate-500 text-xs">
            {formatDistanceToNow(new Date(news.timestamp), { addSuffix: true })}
          </span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <Clock className="w-3 h-3" />
          <span className="text-xs">
            {new Date(news.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>
      </div>

      {/* Main content */}
      <div className="p-4">
        {/* Headline */}
        <h3 
          className="text-sm font-semibold text-white leading-relaxed mb-2 cursor-pointer hover:text-blue-400 transition-colors"
          onClick={onToggle}
        >
          {news.headline}
        </h3>
        
        {/* Summary (when not expanded) */}
        {!isExpanded && (
          <p className="text-xs text-slate-400 line-clamp-2 mb-3">
            {news.content?.substring(0, 150)}...
          </p>
        )}

        {/* Impact badges row */}
        <div className="flex flex-wrap gap-2 mb-3">
          {news.impacts.slice(0, 5).map((impact, idx) => (
            <SymbolImpactBadge
              key={idx}
              symbol={impact.symbol}
              direction={impact.direction}
              score={impact.score}
            />
          ))}
          {news.impacts.length > 5 && (
            <span className="text-xs text-slate-500 self-center">
              +{news.impacts.length - 5} more
            </span>
          )}
        </div>

        {/* Expanded AI Analysis */}
        {isExpanded && (
          <div className="mt-4 space-y-4 animate-in slide-in-from-top-2 duration-300">
            {/* AI Analysis Box */}
            <div className="bg-slate-900/60 rounded-lg p-4 border border-slate-700/50">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span className="text-sm font-semibold text-purple-300">AI Analysis</span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed mb-4">
                {news.content}
              </p>
              
              {/* Detailed impacts */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Market Impact Forecast
                </h4>
                {news.impacts.map((impact, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-800/50"
                  >
                    <div className="flex items-center gap-3">
                      <SymbolImpactBadge
                        symbol={impact.symbol}
                        direction={impact.direction}
                        score={impact.score}
                      />
                      <span className="text-xs text-slate-400">{impact.reasoning}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className={cn(
                        "text-xs font-bold",
                        impact.confidence > 0.7 ? "text-green-400" : 
                        impact.confidence > 0.4 ? "text-yellow-400" : "text-slate-400"
                      )}>
                        {Math.round(impact.confidence * 100)}%
                      </span>
                      <span className="text-xs text-slate-600">confidence</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Sentiment & Volatility */}
              <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-700/50">
                <div>
                  <span className="text-xs text-slate-500">Market Sentiment</span>
                  <p className={cn(
                    "text-sm font-semibold capitalize",
                    news.sentiment === "risk_on" ? "text-green-400" :
                    news.sentiment === "risk_off" ? "text-red-400" : "text-yellow-400"
                  )}>
                    {news.sentiment?.replace("_", " ")}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Volatility Expected</span>
                  <p className={cn(
                    "text-sm font-semibold capitalize",
                    news.volatilityExpectation === "high" ? "text-red-400" :
                    news.volatilityExpectation === "medium" ? "text-yellow-400" : "text-green-400"
                  )}>
                    {news.volatilityExpectation}
                  </p>
                </div>
              </div>
            </div>

            {/* Source */}
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Source: {news.source}</span>
              <span>AI Confidence: {Math.round(news.aiConfidence)}%</span>
            </div>
          </div>
        )}

        {/* Expand/Collapse button */}
        <button
          onClick={onToggle}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors mt-2"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              <span>Show Less</span>
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              <span>View AI Analysis</span>
            </>
          )}
        </button>
      </div>

      {/* Pulse animation for breaking news */}
      {news.urgency === "breaking" && (
        <div className="absolute top-0 right-0 p-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>
      )}
    </div>
  );
};

// Filter Bar Component
const FilterBar = ({ 
  activeFilter, 
  onFilterChange,
  searchQuery,
  onSearchChange
}: { 
  activeFilter: string;
  onFilterChange: (filter: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}) => {
  const filters = [
    { key: "all", label: "All", color: "text-white" },
    { key: "breaking", label: "Breaking", color: "text-red-400" },
    { key: "high", label: "High Impact", color: "text-orange-400" },
    { key: "medium", label: "Medium", color: "text-yellow-400" },
  ];

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      {/* Filter tabs */}
      <div className="flex items-center gap-1 bg-slate-900/50 rounded-lg p-1">
        {filters.map((filter) => (
          <button
            key={filter.key}
            onClick={() => onFilterChange(filter.key)}
            className={cn(
              "px-3 py-1.5 rounded-md text-xs font-medium transition-all",
              activeFilter === filter.key
                ? "bg-slate-700 text-white"
                : "text-slate-400 hover:text-white hover:bg-slate-800"
            )}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative w-full sm:w-auto">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search news..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full sm:w-64 pl-9 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-slate-600"
        />
      </div>
    </div>
  );
};

// Main Component
export const NewsFeedList = ({ onNewsClick, className }: NewsFeedListProps) => {
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [filteredNews, setFilteredNews] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Fetch news
  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        const response = await fetcher<{ success: boolean; data: EnrichedNews[] }>(
          "/api/rss/news?limit=50&hours=48"
        );
        
        if (response.success && response.data) {
          setNews(response.data);
          setFilteredNews(response.data);
        }
      } catch (err) {
        setError("Failed to load news");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
    // Refresh every 2 minutes
    const interval = setInterval(fetchNews, 120000);
    return () => clearInterval(interval);
  }, []);

  // Filter logic
  useEffect(() => {
    let filtered = news;

    // Filter by urgency
    if (activeFilter !== "all") {
      filtered = filtered.filter((n) => n.urgency === activeFilter);
    }

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (n) =>
          n.headline.toLowerCase().includes(query) ||
          n.content?.toLowerCase().includes(query) ||
          n.impacts.some((i) => i.symbol.toLowerCase().includes(query))
      );
    }

    setFilteredNews(filtered);
  }, [news, activeFilter, searchQuery]);

  const handleToggle = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-32 bg-slate-900/50 rounded-xl border border-slate-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-slate-400">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            Live News Feed
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            AI-analyzed market events • {filteredNews.length} items
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            <span className="text-xs text-slate-500">Live</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <FilterBar
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* News List */}
      <div className="space-y-4">
        {filteredNews.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Filter className="w-8 h-8 text-slate-600" />
            </div>
            <p className="text-slate-400">No news matching your filters</p>
            <button
              onClick={() => {
                setActiveFilter("all");
                setSearchQuery("");
              }}
              className="mt-4 text-sm text-blue-400 hover:text-blue-300"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          filteredNews.map((item) => (
            <NewsCard
              key={item.id}
              news={item}
              isExpanded={expandedId === item.id}
              onToggle={() => handleToggle(item.id)}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default NewsFeedList;
