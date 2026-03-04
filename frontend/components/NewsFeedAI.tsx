"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Newspaper,
  Calendar,
  Building2,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  Clock,
  Filter,
  Brain,
} from "lucide-react";
import {
  fetchEconomicCalendar,
  getUrgencyColor,
  getUrgencyLabel,
  getImpactColor,
  getSymbolEmoji,
  RSSNewsItem,
} from "../lib/api/rssNews";
import { useI18nStore } from "../lib/i18n/store";

// Types
interface EconomicEvent {
  id: string;
  timestamp: string;
  currency: string;
  event_name: string;
  impact: "High" | "Medium" | "Low";
  actual?: string;
  forecast?: string;
  previous?: string;
  affected_symbols: string[];
  is_earnings?: boolean;
  company?: string;
}

type NewsTab = "news" | "economic" | "earnings";

interface NewsFeedAIProps {
  className?: string;
}

export default function NewsFeedAI({ className = "" }: NewsFeedAIProps) {
  const [activeTab, setActiveTab] = useState<NewsTab>("news");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const { currentLocale } = useI18nStore();
  
  // MANUAL FETCH STATE
  const [newsItems, setNewsItems] = useState<RSSNewsItem[] | null>(null);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState<Error | null>(null);
  
  // Determine if we should show Turkish content
  const isTurkish = currentLocale === 'tr';
  const isSpanish = currentLocale === 'es';

  // DEBUG: Component mount
  useEffect(() => {
    console.log("[NewsFeedAI] Component MOUNTED");
  }, []);

  // MANUAL FETCH - Get news from last 72 hours to ensure we don't miss high impact news
  const fetchNews = async () => {
    console.log("[NewsFeedAI] fetchNews called");
    setNewsLoading(true);
    setNewsError(null);
    
    try {
      const url = `https://upbeat-flow-production.up.railway.app/api/rss/news?hours=72&limit=100&skip_ai_filtered=true`;
      console.log("[NewsFeedAI] Fetching:", url);
      
      const response = await fetch(url);
      console.log("[NewsFeedAI] Response status:", response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("[NewsFeedAI] Data received:", data.length, "items");
      setNewsItems(data);
    } catch (err) {
      console.error("[NewsFeedAI] Fetch error:", err);
      setNewsError(err as Error);
    } finally {
      setNewsLoading(false);
    }
  };

  // Fetch on mount
  useEffect(() => {
    fetchNews();
  }, []);

  // Refetch function
  const refetchNews = () => fetchNews();

  // MANUAL ECONOMIC FETCH
  const [economicEvents, setEconomicEvents] = useState<any[] | null>(null);
  const [economicLoading, setEconomicLoading] = useState(true);

  useEffect(() => {
    const fetchEconomic = async () => {
      try {
        const res = await fetch("https://upbeat-flow-production.up.railway.app/api/calendar/economic?days=30");
        if (res.ok) {
          const data = await res.json();
          setEconomicEvents(data.events || []);
        }
      } catch (e) {
        console.error("[NewsFeedAI] Economic fetch error:", e);
      } finally {
        setEconomicLoading(false);
      }
    };
    fetchEconomic();
  }, []);

  // Filter earnings events
  const earningsEvents = economicEvents?.filter((e) => e.is_earnings) || [];

  const handleRefresh = useCallback(() => {
    if (activeTab === "news") refetchNews();
  }, [activeTab, refetchNews]);

  const impactColors = {
    High: "bg-red-500/20 text-red-300 border-red-500/40",
    Medium: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
    Low: "bg-green-500/20 text-green-300 border-green-500/40",
  };

  const directionIcons = {
    bullish: <TrendingUp className="w-3 h-3 text-emerald-400" />,
    bearish: <TrendingDown className="w-3 h-3 text-red-400" />,
    neutral: <Minus className="w-3 h-3 text-gray-400" />,
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 5) return "Şimdi";
    if (diffMins < 60) return `${diffMins}d ago`;
    if (diffHours < 24) return `${diffHours}s ago`;
    return `${diffDays}g ago`;
  };

  const formatTimeFuture = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHrs < 0) return "Başladı";
    if (diffHrs < 24) return `${diffHrs}s ${diffMins}d`;
    return `${Math.floor(diffHrs / 24)}g`;
  };

  // Render News Tab
  const renderNewsTab = () => {
    if (newsLoading) {
      return (
        <div className="flex flex-col items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full mb-2" />
          <span className="text-xs text-slate-500">Haberler yükleniyor...</span>
        </div>
      );
    }

    if (newsError) {
      return (
        <div className="text-center py-8 text-slate-400 text-sm">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-red-400" />
          <div className="mb-2">Haberler yüklenirken hata oluştu</div>
          <div className="text-xs text-red-500/70 mb-3">{String(newsError)}</div>
          <button 
            onClick={() => refetchNews()}
            className="px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 text-xs rounded-lg transition"
          >
            Tekrar Dene
          </button>
        </div>
      );
    }

    if (!newsItems || newsItems.length === 0) {
      return (
        <div className="text-center py-8 text-slate-400 text-sm">
          <Newspaper className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <div>Son 24 saatte haber bulunamadı</div>
          <button 
            onClick={() => refetchNews()}
            className="mt-3 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-400 text-xs rounded-lg transition"
          >
            Yenile
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {newsItems.map((item) => (
          <NewsCard key={item.id} item={item} formatTime={formatTime} isTurkish={isTurkish} />
        ))}
      </div>
    );
  };

  // Render Economic Tab
  const renderEconomicTab = () => {
    if (economicLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full" />
        </div>
      );
    }

    const regularEvents = economicEvents?.filter((e) => !e.is_earnings) || [];

    if (regularEvents.length === 0) {
      return (
        <div className="text-center py-8 text-slate-400 text-sm">
          <Calendar className="w-8 h-8 mx-auto mb-2 opacity-30" />
          Yaklaşan ekonomik veri yok
        </div>
      );
    }

    return (
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {regularEvents.slice(0, 15).map((event) => (
          <div
            key={event.id}
            className="rounded-xl border border-white/5 bg-white/5 p-3 hover:bg-white/10 transition"
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${impactColors[event.impact]}`}
              >
                {event.impact}
              </span>
              <span className="text-[10px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTimeFuture(event.timestamp)}
              </span>
            </div>
            <p className="text-sm font-semibold text-white mb-1">{event.event_name}</p>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">{event.currency}</span>
              <span className="text-xs text-slate-500">
                {event.affected_symbols?.slice(0, 3).join(", ")}
              </span>
            </div>
            {(event.actual || event.forecast) && (
              <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                <div className="bg-white/5 rounded p-1">
                  <span className="text-slate-500">Gerçekleşen:</span>{" "}
                  <span className="text-white">{event.actual || "-"}</span>
                </div>
                <div className="bg-white/5 rounded p-1">
                  <span className="text-slate-500">Beklenti:</span>{" "}
                  <span className="text-white">{event.forecast || "-"}</span>
                </div>
                <div className="bg-white/5 rounded p-1">
                  <span className="text-slate-500">Önceki:</span>{" "}
                  <span className="text-white">{event.previous || "-"}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  // Render Earnings Tab
  const renderEarningsTab = () => {
    if (economicLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full" />
        </div>
      );
    }

    if (earningsEvents.length === 0) {
      return (
        <div className="text-center py-8 text-slate-400 text-sm">
          <Building2 className="w-8 h-8 mx-auto mb-2 opacity-30" />
          Yaklaşan kazanç açıklaması yok
        </div>
      );
    }

    return (
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {earningsEvents.slice(0, 15).map((event) => (
          <div
            key={event.id}
            className="rounded-xl border border-white/5 bg-white/5 p-3 hover:bg-white/10 transition"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-gradient-to-br from-blue-500/30 to-indigo-500/30 flex items-center justify-center text-xs font-bold text-blue-400">
                  {event.company?.slice(0, 2) || "??"}
                </span>
                <span className="text-sm font-semibold">{event.company}</span>
              </div>
              <span className="text-[10px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatTimeFuture(event.timestamp)}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="bg-white/5 rounded px-2 py-0.5">EPS: {event.actual || "-"}</span>
              <span className="bg-white/5 rounded px-2 py-0.5">
                Beklenti: {event.forecast || "-"}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">{event.event_name}</p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`glass-premium rounded-2xl p-5 transition-all duration-300 hover:shadow-glow-sm ${className}`}>
      {/* Header with Tabs */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-400" />
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">
              AI-Analizli Haberler
            </p>
          </div>
          <h3 className="text-lg font-semibold mt-1">
            {activeTab === "news" && "Haber Akışı"}
            {activeTab === "economic" && "Ekonomik Takvim"}
            {activeTab === "earnings" && "Kazanç Takvimi"}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition text-[10px] text-slate-400"
            title="Sayfa başına dön"
          >
            ↑ Yukarı
          </button>
          <button
            onClick={handleRefresh}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition"
            disabled={newsLoading || economicLoading}
          >
            <RefreshCw
              className={`w-4 h-4 ${newsLoading || economicLoading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1 mb-4">
        <button
          onClick={() => setActiveTab("news")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            activeTab === "news"
              ? "bg-slate-700 text-white"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Newspaper className="w-3.5 h-3.5" />
          Haberler
          {newsItems && newsItems.length > 0 && (
            <span className="bg-white/20 px-1.5 py-0 rounded-full text-[9px]">
              {newsItems.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("economic")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            activeTab === "economic"
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          Ekonomik
        </button>
        <button
          onClick={() => setActiveTab("earnings")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            activeTab === "earnings"
              ? "bg-blue-500/20 text-blue-400 border border-blue-500/40"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          Kazançlar
        </button>
      </div>

      {/* Symbol Filter */}
      {activeTab === "news" && (
        <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1">
          <Filter className="w-3 h-3 text-slate-400 flex-shrink-0" />
          <button
            onClick={() => setSelectedSymbol(null)}
            className={`px-2 py-1 rounded text-[10px] font-medium transition ${
              !selectedSymbol ? "bg-accent text-white" : "bg-white/5 text-slate-400 hover:bg-white/10"
            }`}
          >
            Tümü
          </button>
          {["XAUUSD", "NDX", "DAX", "USOIL", "VIX", "DXY"].map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`px-2 py-1 rounded text-[10px] font-medium transition whitespace-nowrap ${
                selectedSymbol === sym
                  ? "bg-accent text-white"
                  : "bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              {getSymbolEmoji(sym)} {sym}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {activeTab === "news" && renderNewsTab()}
      {activeTab === "economic" && renderEconomicTab()}
      {activeTab === "earnings" && renderEarningsTab()}
    </div>
  );
}

// Individual News Card Component
function NewsCard({
  item,
  formatTime,
  isTurkish = false,
}: {
  item: RSSNewsItem;
  formatTime: (dateStr: string) => string;
  isTurkish?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  const getUrgencyIcon = (urgency: string) => {
    if (urgency === "breaking") return "🚨";
    if (urgency === "high") return "🔴";
    if (urgency === "medium") return "🟡";
    return "🟢";
  };
  
  // Determine headline based on locale
  const displayHeadline = isTurkish && item.headline_tr 
    ? item.headline_tr 
    : item.headline;
  
  // Show original as subtitle if translated
  const showOriginal = isTurkish && item.headline_tr && item.headline_tr !== item.headline;

  return (
    <div
      className={`rounded-xl border p-3 transition hover:shadow-md ${
        item.urgency === "breaking"
          ? "border-red-500/30 bg-red-500/5"
          : item.urgency === "high"
          ? "border-orange-500/30 bg-orange-500/5"
          : "border-white/5 bg-white/5 hover:bg-white/10"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm">{getUrgencyIcon(item.urgency)}</span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${getUrgencyColor(item.urgency)}`}>
              {getUrgencyLabel(item.urgency)}
            </span>
            <span className="text-[10px] text-slate-400">{item.source}</span>
            <span className="text-[10px] text-slate-500">{formatTime(item.timestamp)}</span>
          </div>
          <p className="text-sm font-medium text-white leading-tight line-clamp-2">
            {displayHeadline}
          </p>
          {showOriginal && (
            <p className="text-xs text-slate-400 mt-1 line-clamp-1">{item.headline}</p>
          )}
        </div>
        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition flex-shrink-0"
          >
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </a>
        )}
      </div>

      {/* AI Analysis Badge */}
      {item.ai_confidence > 70 && (
        <div className="flex items-center gap-1 mt-2 text-[10px] text-purple-400">
          <Brain className="w-3 h-3" />
          <span>AI Analizi ({item.ai_confidence}% güven)</span>
        </div>
      )}

      {/* Impacts */}
      {item.impacts && item.impacts.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {item.impacts.slice(0, expanded ? undefined : 3).map((impact, idx) => (
            <div
              key={idx}
              className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/10 text-[10px]"
            >
              <span>{getSymbolEmoji(impact.symbol)}</span>
              <span className="text-slate-300">{impact.symbol}</span>
              {directionIcons[impact.direction]}
              <span className={getImpactColor(impact.direction)}>{impact.score}/10</span>
            </div>
          ))}
          {!expanded && item.impacts.length > 3 && (
            <button
              onClick={() => setExpanded(true)}
              className="px-2 py-0.5 rounded-full bg-white/5 text-[10px] text-slate-400 hover:bg-white/10"
            >
              +{item.impacts.length - 3}
            </button>
          )}
        </div>
      )}

      {/* Reasoning */}
      {expanded && item.impacts.some((i) => i.reasoning_tr) && (
        <div className="mt-2 pt-2 border-t border-white/10">
          <p className="text-[10px] text-slate-400">AI Yorumu:</p>
          <p className="text-[10px] text-slate-300 mt-0.5">
            {item.impacts.find((i) => i.reasoning_tr)?.reasoning_tr}
          </p>
        </div>
      )}
    </div>
  );
}
