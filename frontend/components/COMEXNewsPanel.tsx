"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Clock,
  Zap,
  Shield,
  DollarSign,
  Building2,
} from "lucide-react";

interface COMEXNewsItem {
  id: string;
  title: string;
  content: string;
  source: string;
  published_at: string;
  impact_score: number;
  direction: string;
  direction_numeric: number;
  confidence: number;
  reasoning: string;
  is_margin_related: boolean;
  is_rate_related: boolean;
  is_fed_related: boolean;
}

interface COMEXImpact {
  overall_impact: number;
  impact_score: number;
  confidence: number;
  direction: string;
  news_count: number;
  should_block_trading: boolean;
  block_reason: string;
  recent_news: COMEXNewsItem[];
  high_impact_news: COMEXNewsItem[];
  last_update: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function COMEXNewsPanel() {
  const [data, setData] = useState<COMEXImpact | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchCOMEXNews = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/news/comex?use_ai=false`);
      if (!response.ok) throw new Error("Failed to fetch COMEX news");
      const result = await response.json();
      setData(result);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCOMEXNews();
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchCOMEXNews, 120000);
    return () => clearInterval(interval);
  }, []);

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case "bullish":
      case "BUY":
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case "bearish":
      case "SELL":
        return <TrendingDown className="w-4 h-4 text-red-400" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case "bullish":
      case "BUY":
        return "text-emerald-400";
      case "bearish":
      case "SELL":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  const getImpactBadge = (score: number) => {
    if (score >= 80) return { text: "Critical", color: "bg-red-500/20 text-red-400 border-red-500/30" };
    if (score >= 60) return { text: "High", color: "bg-orange-500/20 text-orange-400 border-orange-500/30" };
    if (score >= 40) return { text: "Medium", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" };
    return { text: "Low", color: "bg-gray-500/20 text-gray-400 border-gray-500/30" };
  };

  const formatTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  const getCategoryIcon = (news: COMEXNewsItem) => {
    if (news.is_margin_related) return <DollarSign className="w-3.5 h-3.5" />;
    if (news.is_fed_related) return <Building2 className="w-3.5 h-3.5" />;
    if (news.is_rate_related) return <Zap className="w-3.5 h-3.5" />;
    return <Shield className="w-3.5 h-3.5" />;
  };

  return (
    <div className="glass-card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/20">
            <Zap className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">COMEX News</h2>
            <p className="text-xs text-gray-400">
              {lastRefresh ? `Updated ${formatTimeAgo(lastRefresh.toISOString())}` : "Loading..."}
            </p>
          </div>
        </div>
        <button
          onClick={fetchCOMEXNews}
          disabled={isLoading}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
          aria-label="Refresh COMEX news"
        >
          <RefreshCw className={`w-4 h-4 text-gray-400 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Trading Block Alert */}
      <AnimatePresence>
        {data?.should_block_trading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-3"
          >
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-400">Trading Paused</p>
              <p className="text-xs text-red-400/70 mt-0.5">{data.block_reason}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overall Impact Summary */}
      {data && !isLoading && (
        <div className="p-4 rounded-xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-400">Overall Impact</span>
            <div className="flex items-center gap-2">
              {getDirectionIcon(data.direction)}
              <span className={`text-sm font-medium ${getDirectionColor(data.direction)}`}>
                {data.direction}
              </span>
            </div>
          </div>
          
          {/* Impact Bar */}
          <div className="relative h-2 bg-gray-700/50 rounded-full overflow-hidden mb-3">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.abs(data.overall_impact) * 50 + 50}%` }}
              className={`absolute h-full rounded-full ${
                data.overall_impact > 0
                  ? "bg-gradient-to-r from-gray-500 to-emerald-500"
                  : "bg-gradient-to-r from-red-500 to-gray-500"
              }`}
            />
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/30" />
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-lg font-bold text-white">{data.impact_score}</p>
              <p className="text-xs text-gray-500">Impact</p>
            </div>
            <div>
              <p className="text-lg font-bold text-white">{data.confidence}%</p>
              <p className="text-xs text-gray-500">Confidence</p>
            </div>
            <div>
              <p className="text-lg font-bold text-white">{data.news_count}</p>
              <p className="text-xs text-gray-500">News</p>
            </div>
          </div>
        </div>
      )}

      {/* High Impact News */}
      {data?.high_impact_news && data.high_impact_news.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-amber-400 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            High Impact
          </h3>
          {data.high_impact_news.slice(0, 3).map((news) => (
            <motion.div
              key={news.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 hover:border-amber-500/40 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium line-clamp-2">{news.title}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${getImpactBadge(news.impact_score).color}`}>
                      {getCategoryIcon(news)}
                      {getImpactBadge(news.impact_score).text}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimeAgo(news.published_at)}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  {getDirectionIcon(news.direction)}
                  <span className="text-xs text-gray-500 mt-1">{news.impact_score}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Recent News */}
      {data?.recent_news && data.recent_news.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400">Recent News</h3>
          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
            {data.recent_news
              .filter((n) => !data.high_impact_news.some((h) => h.id === n.id))
              .slice(0, 5)
              .map((news) => (
                <motion.div
                  key={news.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-3 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-300 line-clamp-2">{news.title}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-xs text-gray-500">{news.source}</span>
                        <span className="text-xs text-gray-600">•</span>
                        <span className="text-xs text-gray-500">{formatTimeAgo(news.published_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {getDirectionIcon(news.direction)}
                    </div>
                  </div>
                </motion.div>
              ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && !data && (
        <div className="space-y-3">
          <div className="h-24 rounded-xl bg-white/5 animate-pulse" />
          <div className="h-16 rounded-lg bg-white/5 animate-pulse" />
          <div className="h-16 rounded-lg bg-white/5 animate-pulse" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-center">
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={fetchCOMEXNews}
            className="mt-2 text-xs text-red-400/70 hover:text-red-400 underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && data?.news_count === 0 && (
        <div className="p-6 text-center">
          <Shield className="w-10 h-10 text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-500">No COMEX news at the moment</p>
        </div>
      )}
    </div>
  );
}
