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
  Calendar,
  Building2,
  TrendingUp as TrendingUpIcon,
  DollarSign,
  PieChart,
  Info
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getApiBase } from "@/lib/api/base";
import { fetcher } from "@/lib/api";
import Link from "next/link";
import type { EnrichedNews } from "@/types/news-correlation";

const API_URL = getApiBase();

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

// Types
interface EconomicEvent {
  id: string;
  timestamp: string;
  title: string;
  title_tr: string;
  currency: string;
  impact: "High" | "Medium" | "Low";
  actual: string | null;
  forecast: string | null;
  previous: string | null;
  predicted_direction: "bullish" | "bearish" | "neutral" | "volatile";
  affected_symbols: string[];
  impact_analysis: string;
  impact_analysis_tr: string;
  description: string;
  description_tr: string;
  why_it_matters: string;
  why_it_matters_tr: string;
  typical_market_reaction: string;
  typical_market_reaction_tr: string;
  is_upcoming: boolean;
  minutes_until: number | null;
}

interface EarningsEvent {
  id: string;
  timestamp: string;
  company: string;
  ticker: string;
  sector: string;
  eps_forecast: string | null;
  revenue_forecast: string | null;
  previous_eps: string | null;
  previous_revenue: string | null;
  predicted_direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  affected_symbols: string[];
  analysis: string;
  analysis_tr: string;
  key_metrics_to_watch: string[];
  key_metrics_to_watch_tr: string[];
  is_upcoming: boolean;
  minutes_until: number | null;
}

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
        <span className="text-slate-400 text-sm">Loading...</span>
      </div>
    </div>
  );
}

// News Feed Content with Tabs
function NewsFeedContent() {
  const [activeTab, setActiveTab] = useState<"news" | "economic" | "earnings">("news");
  
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
                  <h1 className="text-lg font-bold text-white">Market Intelligence</h1>
                  <p className="text-xs text-slate-400">
                    News, Economic Calendar & Earnings
                  </p>
                </div>
              </div>
            </div>

            {/* Right: Link to Chart View */}
            <Link
              href="/news-correlation"
              className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded-lg text-sm font-medium hover:bg-blue-500/20 transition-colors"
            >
              <BarChart2 className="w-4 h-4" />
              <span className="hidden sm:inline">Chart View</span>
            </Link>
          </div>
        </div>

        {/* TABS */}
        <div className="border-t border-slate-800/50 bg-slate-900/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-1 py-2">
              <TabButton
                active={activeTab === "news"}
                onClick={() => setActiveTab("news")}
                icon={<Newspaper className="w-4 h-4" />}
                label="News Feed"
                badge={null}
              />
              <TabButton
                active={activeTab === "economic"}
                onClick={() => setActiveTab("economic")}
                icon={<Calendar className="w-4 h-4" />}
                label="Economic Calendar"
                badge={null}
              />
              <TabButton
                active={activeTab === "earnings"}
                onClick={() => setActiveTab("earnings")}
                icon={<Building2 className="w-4 h-4" />}
                label="Earnings Calendar"
                badge={null}
              />
            </div>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT BASED ON TAB */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "news" && <NewsTab />}
        {activeTab === "economic" && <EconomicCalendarTab />}
        {activeTab === "earnings" && <EarningsCalendarTab />}
      </main>
    </div>
  );
}

// TAB BUTTON COMPONENT
function TabButton({ 
  active, 
  onClick, 
  icon, 
  label,
  badge 
}: { 
  active: boolean; 
  onClick: () => void; 
  icon: React.ReactNode; 
  label: string;
  badge: number | null;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
        active 
          ? "bg-slate-700 text-white" 
          : "text-slate-400 hover:text-white hover:bg-slate-800"
      )}
    >
      {icon}
      <span>{label}</span>
      {badge !== null && badge > 0 && (
        <span className={cn(
          "px-1.5 py-0.5 rounded text-xs",
          active ? "bg-slate-600" : "bg-slate-700"
        )}>
          {badge}
        </span>
      )}
    </button>
  );
}

// ==========================================
// NEWS TAB CONTENT
// ==========================================
function NewsTab() {
  const [news, setNews] = useState<EnrichedNews[]>([]);
  const [filteredNews, setFilteredNews] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [symbolFilter, setSymbolFilter] = useState<string>("all");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const availableSymbols = React.useMemo(() => {
    const symbols = new Set<string>();
    news.forEach((n) => n.impacts.forEach((i) => symbols.add(i.symbol)));
    return Array.from(symbols).sort();
  }, [news]);

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
    <div className="space-y-4">
      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 pb-4 border-b border-slate-800">
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

        {/* Refresh */}
        <button
          onClick={fetchNews}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50 ml-auto"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          <span>Refresh</span>
        </button>

        {/* Last Updated */}
        {lastUpdated && (
          <span className="text-xs text-slate-500">
            {formatDistanceToNow(lastUpdated, { addSuffix: true })}
          </span>
        )}
      </div>

      {/* News List */}
      {loading && news.length === 0 ? (
        <LoadingState />
      ) : error ? (
        <ErrorState error={error} onRetry={fetchNews} />
      ) : filteredNews.length === 0 ? (
        <EmptyState onReset={() => {
          setActiveFilter("all");
          setSymbolFilter("all");
          setSearchQuery("");
        }} />
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
    </div>
  );
}

// ==========================================
// ECONOMIC CALENDAR TAB
// ==========================================
function EconomicCalendarTab() {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "High" | "Medium" | "Low">("all");
  const [selectedEvent, setSelectedEvent] = useState<EconomicEvent | null>(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/calendar/economic?days=30`);
      const data = await response.json();
      if (data.success) {
        setEvents(data.events);
      }
    } catch (err) {
      setError("Failed to load economic calendar");
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = filter === "all" 
    ? events 
    : events.filter(e => e.impact === filter);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={fetchEvents} />;

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex items-center gap-2 pb-4 border-b border-slate-800">
        <span className="text-sm text-slate-400">Filter:</span>
        {(["all", "High", "Medium", "Low"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
              filter === f 
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" 
                : "text-slate-400 hover:text-white hover:bg-slate-800"
            )}
          >
            {f === "all" ? "All Events" : f}
          </button>
        ))}
      </div>

      {/* Events List */}
      {filteredEvents.length === 0 ? (
        <EmptyState onReset={() => setFilter("all")} />
      ) : (
        <div className="space-y-3">
          {filteredEvents.map((event) => (
            <EconomicEventCard 
              key={event.id} 
              event={event} 
              onClick={() => setSelectedEvent(event)}
            />
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedEvent && (
        <EconomicEventModal 
          event={selectedEvent} 
          onClose={() => setSelectedEvent(null)} 
        />
      )}
    </div>
  );
}

// ==========================================
// EARNINGS CALENDAR TAB
// ==========================================
function EarningsCalendarTab() {
  const [earnings, setEarnings] = useState<EarningsEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEarnings, setSelectedEarnings] = useState<EarningsEvent | null>(null);

  useEffect(() => {
    fetchEarnings();
  }, []);

  const fetchEarnings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/calendar/earnings?days=30`);
      const data = await response.json();
      if (data.success) {
        setEarnings(data.earnings);
      }
    } catch (err) {
      setError("Failed to load earnings calendar");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={fetchEarnings} />;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <p className="text-sm text-slate-400">
          Major companies earnings reports with AI predictions
        </p>
      </div>

      {/* Earnings List */}
      {earnings.length === 0 ? (
        <EmptyState onReset={() => {}} />
      ) : (
        <div className="space-y-3">
          {earnings.map((item) => (
            <EarningsEventCard 
              key={item.id} 
              earnings={item} 
              onClick={() => setSelectedEarnings(item)}
            />
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedEarnings && (
        <EarningsEventModal 
          earnings={selectedEarnings} 
          onClose={() => setSelectedEarnings(null)} 
        />
      )}
    </div>
  );
}

// ==========================================
// SHARED COMPONENTS
// ==========================================
function LoadingState() {
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

function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
        <AlertTriangle className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">Error</h3>
      <p className="text-slate-400 text-sm max-w-md mb-6">{error}</p>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Retry
      </button>
    </div>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
        <Filter className="w-8 h-8 text-slate-600" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">No Results</h3>
      <p className="text-slate-400 text-sm max-w-md">
        No items matching your current filters.
      </p>
      <button
        onClick={onReset}
        className="mt-6 px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors"
      >
        Reset Filters
      </button>
    </div>
  );
}

// ==========================================
// CARD COMPONENTS
// ==========================================
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
        <h3 
          className="text-base font-semibold text-white leading-relaxed mb-3 cursor-pointer hover:text-blue-400 transition-colors"
          onClick={onToggle}
        >
          {news.headline}
        </h3>
        
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
            </div>
          </div>
        )}

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
    </div>
  );
}

// Economic Event Card
function EconomicEventCard({ event, onClick }: { event: EconomicEvent; onClick: () => void }) {
  const impactColors = {
    High: "bg-red-500/20 text-red-300 border-red-500/40",
    Medium: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
    Low: "bg-green-500/20 text-green-300 border-green-500/40",
  };

  const directionIcons = {
    bullish: <TrendingUp className="w-4 h-4 text-emerald-400" />,
    bearish: <TrendingDown className="w-4 h-4 text-red-400" />,
    neutral: <Minus className="w-4 h-4 text-gray-400" />,
    volatile: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      onClick={onClick}
      className="border border-slate-800 rounded-xl p-5 bg-slate-900/50 hover:bg-slate-800/50 transition cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded-lg text-xs font-semibold border ${impactColors[event.impact]}`}>
            {event.impact}
          </span>
          <span className="text-xs text-slate-400 bg-white/5 px-2 py-1 rounded">
            {event.currency}
          </span>
        </div>
        <span className="text-xs text-slate-400">
          {event.minutes_until && event.minutes_until < 1440 ? (
            <span className="text-emerald-400 font-medium">
              {Math.floor(event.minutes_until / 60)}h {event.minutes_until % 60}m
            </span>
          ) : (
            formatTime(event.timestamp)
          )}
        </span>
      </div>

      <h3 className="text-base font-semibold text-white mb-2 group-hover:text-emerald-400 transition">
        {event.title}
      </h3>

      <div className="flex items-center gap-2 mb-3">
        {directionIcons[event.predicted_direction]}
        <span className="text-xs text-slate-400">
          Expected: <span className={
            event.predicted_direction === "bullish" ? "text-emerald-400" :
            event.predicted_direction === "bearish" ? "text-red-400" :
            event.predicted_direction === "volatile" ? "text-yellow-400" :
            "text-gray-400"
          }>{event.predicted_direction}</span>
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {event.affected_symbols.map((symbol) => (
          <span key={symbol} className="text-[10px] bg-white/10 text-slate-400 px-2 py-0.5 rounded">
            {symbol}
          </span>
        ))}
      </div>
    </div>
  );
}

// Earnings Event Card
function EarningsEventCard({ earnings, onClick }: { earnings: EarningsEvent; onClick: () => void }) {
  const sectorIcons: Record<string, string> = {
    Technology: "💻",
    "Consumer Cyclical": "🛒",
    Financials: "🏦",
    Healthcare: "🏥",
    Automotive: "🚗",
    Energy: "⚡",
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "text-emerald-400";
    if (confidence >= 60) return "text-yellow-400";
    return "text-red-400";
  };

  return (
    <div
      onClick={onClick}
      className="border border-slate-800 rounded-xl p-5 bg-slate-900/50 hover:bg-slate-800/50 transition cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/30 to-indigo-500/30 flex items-center justify-center text-lg">
            {sectorIcons[earnings.sector] || "🏢"}
          </div>
          <div>
            <h3 className="text-base font-semibold text-white group-hover:text-blue-400 transition">
              {earnings.company}
            </h3>
            <span className="text-xs text-slate-400">{earnings.ticker}</span>
          </div>
        </div>
        <span className="text-xs text-slate-400">
          {formatTime(earnings.timestamp)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-white/5 rounded-lg p-2">
          <span className="text-[10px] text-slate-400 uppercase">EPS Forecast</span>
          <p className="text-sm font-semibold text-white">{earnings.eps_forecast || "--"}</p>
        </div>
        <div className="bg-white/5 rounded-lg p-2">
          <span className="text-[10px] text-slate-400 uppercase">Revenue Forecast</span>
          <p className="text-sm font-semibold text-white">{earnings.revenue_forecast || "--"}</p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className={`text-xs ${getConfidenceColor(earnings.confidence)}`}>
          AI Confidence: {earnings.confidence}%
        </span>
        <span className={`text-xs ${
          earnings.predicted_direction === "bullish" ? "text-emerald-400" :
          earnings.predicted_direction === "bearish" ? "text-red-400" :
          "text-gray-400"
        }`}>
          {earnings.predicted_direction === "bullish" ? "Beat Expected" :
           earnings.predicted_direction === "bearish" ? "Miss Expected" : "Neutral"}
        </span>
      </div>
    </div>
  );
}

// Economic Event Modal
function EconomicEventModal({ event, onClose }: { event: EconomicEvent; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-premium w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-slate-900 border border-slate-800">
        <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/95 backdrop-blur">
          <div className="flex items-center gap-3">
            <Calendar className="w-6 h-6 text-emerald-400" />
            <div>
              <span className="text-xs text-emerald-400 font-bold uppercase">{event.impact} IMPACT</span>
              <h2 className="text-lg font-bold text-white">{event.title}</h2>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full">
            <Minus className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Clock className="w-4 h-4" />
            {new Date(event.timestamp).toLocaleString()}
          </div>

          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <h3 className="text-sm font-semibold text-emerald-400 mb-2">What is this data?</h3>
            <p className="text-sm text-slate-300">{event.description}</p>
          </div>

          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <h3 className="text-sm font-semibold text-amber-400 mb-2">Why does it matter?</h3>
            <p className="text-sm text-slate-300">{event.why_it_matters}</p>
          </div>

          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <h3 className="text-sm font-semibold text-blue-400 mb-2">Typical Market Reaction</h3>
            <p className="text-sm text-white">{event.typical_market_reaction}</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Affected Markets</h3>
            <div className="flex flex-wrap gap-2">
              {event.affected_symbols.map((symbol) => (
                <span key={symbol} className="px-3 py-1.5 bg-slate-800 rounded-lg text-white text-sm">
                  {symbol}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 p-4 border-t border-slate-800 bg-slate-900/95">
          <button onClick={onClose} className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// Earnings Event Modal
function EarningsEventModal({ earnings, onClose }: { earnings: EarningsEvent; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-premium w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-slate-900 border border-slate-800">
        <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/95 backdrop-blur">
          <div className="flex items-center gap-3">
            <Building2 className="w-6 h-6 text-blue-400" />
            <div>
              <h2 className="text-lg font-bold text-white">{earnings.company}</h2>
              <span className="text-sm text-blue-400">{earnings.ticker}</span>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full">
            <Minus className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
              <span className="text-xs text-emerald-400 uppercase">EPS Forecast</span>
              <p className="text-xl font-bold text-white">{earnings.eps_forecast || "--"}</p>
            </div>
            <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
              <span className="text-xs text-blue-400 uppercase">Revenue Forecast</span>
              <p className="text-xl font-bold text-white">{earnings.revenue_forecast || "--"}</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
            <h3 className="text-sm font-semibold text-purple-400 mb-2">AI Analysis</h3>
            <p className="text-sm text-slate-300">{earnings.analysis}</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Key Metrics to Watch</h3>
            <div className="grid grid-cols-2 gap-2">
              {earnings.key_metrics_to_watch.map((metric, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 bg-slate-800 rounded-lg text-sm text-white">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  {metric}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Affected Indices</h3>
            <div className="flex flex-wrap gap-2">
              {earnings.affected_symbols.map((symbol) => (
                <span key={symbol} className="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg text-sm">
                  {symbol}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 p-4 border-t border-slate-800 bg-slate-900/95">
          <button onClick={onClose} className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
