"use client";

import React, { useState, useEffect, Suspense } from "react";
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
  Search,
  ArrowLeft,
  RefreshCw,
  Zap,
  BarChart2,
  Globe,
  Newspaper,
  Bell,
  Settings
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetcher } from "@/lib/api";
import Link from "next/link";
import type { EnrichedNews } from "@/types/news-correlation";

// Impact badge colors
const impactColors = {
  breaking: {
    bg: "bg-red-950/40",
    border: "border-red-500/60",
    text: "text-red-300",
    label: "BREAKING",
    dot: "bg-red-500",
    glow: "shadow-red-500/30",
  },
  high: {
    bg: "bg-rose-950/30",
    border: "border-rose-600/50",
    text: "text-rose-300",
    label: "HIGH IMPACT",
    dot: "bg-rose-500",
    glow: "shadow-rose-500/20",
  },
  medium: {
    bg: "bg-amber-950/30",
    border: "border-amber-600/50",
    text: "text-amber-300",
    label: "MEDIUM",
    dot: "bg-amber-500",
    glow: "shadow-amber-500/20",
  },
  low: {
    bg: "bg-slate-900/50",
    border: "border-slate-700/50",
    text: "text-slate-400",
    label: "LOW",
    dot: "bg-slate-500",
    glow: "",
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
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold border backdrop-blur-sm",
        isBullish && "bg-green-500/20 text-green-300 border-green-500/40",
        isBearish && "bg-red-500/20 text-red-300 border-red-500/40",
        !isBullish && !isBearish && "bg-slate-800 text-slate-400 border-slate-600"
      )}
    >
      {isBullish && <TrendingUp className="w-3 h-3" />}
      {isBearish && <TrendingDown className="w-3 h-3" />}
      {!isBullish && !isBearish && <Minus className="w-3 h-3" />}
      <span>{symbol}</span>
      <span className="opacity-60">{score}/10</span>
    </span>
  );
};

// Main Page Component
export default function NewsFeedPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <NewsFeedContent />
    </Suspense>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
        <span className="text-slate-400 text-sm">Loading News Feed...</span>
      </div>
    </div>
  );
}

// News Feed Content
function NewsFeedContent() {
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [filteredNews, setFilteredNews] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [symbolFilter, setSymbolFilter] = useState<string>("all");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Available symbols from data
  const availableSymbols = React.useMemo(() => {
    const symbols = new Set<string>();
    news.forEach((n) => n.impacts.forEach((i) => symbols.add(i.symbol)));
    return Array.from(symbols).sort();
  }, [news]);

  // Fetch news
  const fetchNews = async () => {
    try {
      setLoading(true);
      const response = await fetcher<{ success: boolean; data: EnrichedNews[] }>(
        "/api/rss/news?limit=100&hours=72"
      );
      
      if (response.success && response.data) {
        setNews(response.data);
        setLastUpdated(new Date());
      }
    } catch (err) {
      setError("Failed to load news");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 120000);
    return () => clearInterval(interval);
  }, []);

  // Filter logic
  useEffect(() => {
    let filtered = news;

    if (activeFilter !== "all") {
      filtered = filtered.filter((n) => n.urgency === activeFilter);
    }

    if (symbolFilter !== "all") {
      filtered = filtered.filter((n) => 
        n.impacts.some((i) => i.symbol === symbolFilter)
      );
    }

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
  }, [news, activeFilter, symbolFilter, searchQuery]);

  const handleToggle = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const breakingCount = news.filter((n) => n.urgency === "breaking").length;
  const highCount = news.filter((n) => n.urgency === "high").length;

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Back button & Title */}
            <div className="flex items-center gap-4">
              <Link
                href="/news-correlation"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline text-sm">Back</span>
              </Link>
              
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center justify-center">
                  <Newspaper className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-white">Live News Feed</h1>
                  <p className="text-xs text-slate-400">
                    AI-powered market intelligence
                  </p>
                </div>
              </div>
            </div>

            {/* Right: Stats & Actions */}
            <div className="flex items-center gap-3">
              {/* Quick Stats */}
              <div className="hidden md:flex items-center gap-3 mr-4">
                {breakingCount > 0 && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                    </span>
                    <span className="text-sm font-semibold text-red-400">{breakingCount}</span>
                    <span className="text-xs text-red-400/70">Breaking</span>
                  </div>
                )}
                {highCount > 0 && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                    <Zap className="w-3 h-3 text-orange-400" />
                    <span className="text-sm font-semibold text-orange-400">{highCount}</span>
                    <span className="text-xs text-orange-400/70">High Impact</span>
                  </div>
                )}
              </div>

              {/* Refresh Button */}
              <button
                onClick={fetchNews}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                <span className="hidden sm:inline">Refresh</span>
              </button>

              {/* Link to Chart View */}
              <Link
                href="/news-correlation"
                className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded-lg text-sm font-medium hover:bg-blue-500/20 transition-colors"
              >
                <BarChart2 className="w-4 h-4" />
                <span className="hidden sm:inline">Chart View</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Filters Bar */}
        <div className="border-t border-slate-800/50 bg-slate-900/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              {/* Impact Filter */}
              <div className="flex items-center gap-1 bg-slate-900/50 rounded-lg p-1">
                {[
                  { key: "all", label: "All", count: news.length },
                  { key: "breaking", label: "Breaking", count: breakingCount, color: "text-red-400" },
                  { key: "high", label: "High Impact", count: highCount, color: "text-orange-400" },
                  { key: "medium", label: "Medium", count: news.filter((n) => n.urgency === "medium").length },
                  { key: "low", label: "Low", count: news.filter((n) => n.urgency === "low").length },
                ].map((filter) => (
                  <button
                    key={filter.key}
                    onClick={() => setActiveFilter(filter.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2",
                      activeFilter === filter.key
                        ? "bg-slate-700 text-white"
                        : "text-slate-400 hover:text-white hover:bg-slate-800",
                      activeFilter !== filter.key && filter.color
                    )}
                  >
                    {filter.label}
                    <span className="text-slate-500">{filter.count}</span>
                  </button>
                ))}
              </div>

              {/* Symbol Filter */}
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-slate-500" />
                <select
                  value={symbolFilter}
                  onChange={(e) => setSymbolFilter(e.target.value)}
                  className="bg-slate-900/50 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-slate-600"
                >
                  <option value="all">All Symbols</option>
                  {availableSymbols.map((sym) => (
                    <option key={sym} value={sym}>{sym}</option>
                  ))}
                </select>
              </div>

              {/* Search */}
              <div className="relative flex-1 w-full sm:w-auto sm:max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search news, symbols, events..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-slate-600"
                />
              </div>

              {/* Last Updated */}
              {lastUpdated && (
                <span className="text-xs text-slate-500 ml-auto">
                  Updated {formatDistanceToNow(lastUpdated, { addSuffix: true })}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Status */}
        {loading && news.length === 0 ? (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-40 bg-slate-900/50 rounded-xl border border-slate-800 animate-pulse"
              />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Failed to Load News</h3>
            <p className="text-slate-400 text-sm max-w-md mb-6">{error}</p>
            <button
              onClick={fetchNews}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        ) : filteredNews.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
              <Filter className="w-8 h-8 text-slate-600" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">No News Found</h3>
            <p className="text-slate-400 text-sm max-w-md">
              No news matching your current filters. Try adjusting your search or filters.
            </p>
            <button
              onClick={() => {
                setActiveFilter("all");
                setSymbolFilter("all");
                setSearchQuery("");
              }}
              className="mt-6 px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors"
            >
              Reset All Filters
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredNews.map((item) => (
              <NewsCard
                key={item.id}
                news={item}
                isExpanded={expandedId === item.id}
                onToggle={() => handleToggle(item.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

// News Card Component
function NewsCard({ 
  news, 
  isExpanded, 
  onToggle 
}: { 
  news: EnrichedNews; 
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const impact = impactColors[news.urgency as keyof typeof impactColors] || impactColors.low;
  
  return (
    <div
      className={cn(
        "relative rounded-xl border overflow-hidden transition-all duration-300",
        "backdrop-blur-sm",
        impact.bg,
        impact.border,
        isExpanded ? cn("shadow-2xl", impact.glow) : "hover:shadow-lg hover:shadow-black/20"
      )}
    >
      {/* Top bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/5">
        <div className="flex items-center gap-3">
          <span className={cn("w-2.5 h-2.5 rounded-full", impact.dot, news.urgency === "breaking" && "animate-pulse")} />
          <span className={cn("text-xs font-bold tracking-wider", impact.text)}>
            {impact.label}
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

      {/* Content */}
      <div className="p-5">
        {/* Headline */}
        <h3 
          className="text-base font-semibold text-white leading-relaxed mb-3 cursor-pointer hover:text-blue-400 transition-colors"
          onClick={onToggle}
        >
          {news.headline}
        </h3>
        
        {/* Summary preview */}
        {!isExpanded && (
          <p className="text-sm text-slate-400 line-clamp-2 mb-4">
            {news.content?.substring(0, 200)}...
          </p>
        )}

        {/* Impact badges */}
        <div className="flex flex-wrap gap-2 mb-4">
          {news.impacts.slice(0, 6).map((impact, idx) => (
            <SymbolImpactBadge
              key={idx}
              symbol={impact.symbol}
              direction={impact.direction}
              score={impact.score}
            />
          ))}
          {news.impacts.length > 6 && (
            <span className="text-xs text-slate-500 self-center px-2">
              +{news.impacts.length - 6} more
            </span>
          )}
        </div>

        {/* Expanded AI Analysis */}
        {isExpanded && (
          <div className="mt-5 space-y-5 animate-in slide-in-from-top-2 duration-300">
            {/* AI Analysis */}
            <div className="bg-slate-950/60 rounded-lg p-5 border border-slate-800/50">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                </div>
                <span className="text-sm font-semibold text-purple-300">AI Analysis</span>
              </div>
              
              <p className="text-sm text-slate-300 leading-relaxed mb-5">
                {news.content}
              </p>
              
              {/* Market Impact Forecast */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  Market Impact Forecast
                </h4>
                <div className="grid gap-2">
                  {news.impacts.map((impact, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center justify-between py-3 px-4 rounded-lg bg-slate-900/50 border border-slate-800/50"
                    >
                      <div className="flex items-center gap-4">
                        <SymbolImpactBadge
                          symbol={impact.symbol}
                          direction={impact.direction}
                          score={impact.score}
                        />
                        <span className="text-sm text-slate-400 hidden sm:inline">
                          {impact.reasoning}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "text-sm font-bold",
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
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-5 border-t border-slate-800/50">
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
                  <span className="text-xs text-slate-500">Volatility</span>
                  <p className={cn(
                    "text-sm font-semibold capitalize",
                    news.volatilityExpectation === "high" ? "text-red-400" :
                    news.volatilityExpectation === "medium" ? "text-yellow-400" : "text-green-400"
                  )}>
                    {news.volatilityExpectation}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Source</span>
                  <p className="text-sm font-semibold text-slate-300">{news.source}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-500">AI Confidence</span>
                  <p className="text-sm font-semibold text-purple-400">{Math.round(news.aiConfidence)}%</p>
                </div>
              </div>
            </div>

            {/* Source */}
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Source: {news.source}</span>
              <span>{new Date(news.timestamp).toLocaleString()}</span>
            </div>
          </div>
        )}

        {/* Expand/Collapse */}
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

      {/* Breaking news indicator */}
      {news.urgency === "breaking" && (
        <div className="absolute top-3 right-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>
      )}
    </div>
  );
}
