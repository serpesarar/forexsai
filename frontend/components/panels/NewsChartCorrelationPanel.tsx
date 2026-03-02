"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { createChart, CrosshairMode, type IChartApi, type ISeriesApi, type Time } from "lightweight-charts";
import { format, addSeconds, addMinutes, addHours, addDays, addMonths, addWeeks, subDays, subMonths } from "date-fns";
import { Filter, Newspaper, BarChart2, Maximize2 } from "lucide-react";
import { useNewsCorrelationStore } from "@/lib/stores/newsCorrelationStore";
import type { EnrichedNews } from "@/types/news-correlation";
import { fetcher } from "@/lib/api";

import { cn } from "@/lib/utils";
import Link from "next/link";



// Type definitions
interface ChartCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

// Backend /api/data/ohlcv actual response format
interface OHLCVResponse {
  symbol: string;
  timeframe: string;
  data: Array<{
    timestamp: number; // Unix ms
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  support_resistance: any[];
}

// Timeframe configuration
const timeframes = [
  { value: "1m", label: "1m", getLimit: () => 200 },
  { value: "5m", label: "5m", getLimit: () => 200 },
  { value: "15m", label: "15m", getLimit: () => 200 },
  { value: "30m", label: "30m", getLimit: () => 200 },
  { value: "1h", label: "1h", getLimit: () => 200 },
  { value: "4h", label: "4h", getLimit: () => 200 },
  { value: "1d", label: "1D", getLimit: () => 365 },
  { value: "1w", label: "1W", getLimit: () => 104 },
  { value: "1M", label: "1M", getLimit: () => 60 },
] as const;

type TimeframeValue = typeof timeframes[number]["value"];

// Main Component
export default function NewsChartCorrelationPanel() {
  const [mounted, setMounted] = useState(false);
  const [timeframe, setTimeframe] = useState<TimeframeValue>("1h");
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [events, setEvents] = useState<EnrichedNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"chart" | "feed">("chart");
  const { selectedSymbol, symbols, setSelectedSymbol } = useNewsCorrelationStore();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!mounted) return;

    try {
      setLoading(true);
      setError(null);

      // Symbol mapping for backend API
      const symbolMap: Record<string, string> = {
        XAUUSD: "XAUUSD",
        NASDAQ: "NDX.INDX",
        NDX: "NDX.INDX",
        DAX: "GDAXI.INDX",
        USOIL: "CL.COMM",
        VIX: "VIX.INDX",
        DXY: "DXY.INDX",
        EURUSD: "EURUSD",
        GBPUSD: "GBPUSD",
        BTCUSD: "BTCUSD",
      };
      const apiSymbol = symbolMap[selectedSymbol.replace("/", "")] || selectedSymbol.replace("/", "");
      const tf = timeframes.find((t) => t.value === timeframe);
      const limit = tf?.getLimit() || 200;

      // Fetch chart data - backend returns { data: [{ timestamp (ms), open, high, low, close, volume }] }
      const chartResponse = await fetcher<OHLCVResponse>(
        `/api/data/ohlcv?symbol=${apiSymbol}&timeframe=${timeframe}&limit=${limit}`
      );

      if (chartResponse?.data && Array.isArray(chartResponse.data) && chartResponse.data.length > 5) {
        const processedCandles: ChartCandle[] = chartResponse.data.map((row) => {
          // Convert timestamp from milliseconds to seconds for lightweight-charts
          const timeInSeconds = row.timestamp > 1e12 ? Math.floor(row.timestamp / 1000) : row.timestamp;
          return {
            time: timeInSeconds,
            open: row.open,
            high: row.high,
            low: row.low,
            close: row.close,
          };
        });
        setChartData(processedCandles);
      } else {
        setChartData([]);
      }

      // Fetch news events - use original symbol names for news impacts
      const newsSymbol = selectedSymbol.replace("/", "");

      // Helper: parse news response
      const parseRes = (r: any): any[] => {
        if (Array.isArray(r)) return r;
        if (r?.success && Array.isArray(r.data)) return r.data;
        if (r?.data && Array.isArray(r.data)) return r.data;
        return [];
      };

      // Strategy 1: Symbol-filtered news
      let newsItems: any[] = [];
      try {
        const r1 = await fetcher<any>(`/api/rss/news?symbol=${newsSymbol}&limit=50&hours=48`);
        newsItems = parseRes(r1);
      } catch { /* continue */ }

      // Strategy 2: All news if symbol-specific is empty
      if (newsItems.length === 0) {
        try {
          const r2 = await fetcher<any>(`/api/rss/news?limit=50&hours=72`);
          newsItems = parseRes(r2);
        } catch { /* continue */ }
      }

      // Strategy 3: Include low-priority news
      if (newsItems.length === 0) {
        try {
          const r3 = await fetcher<any>(`/api/rss/news?limit=50&hours=168&skip_ai_filtered=false`);
          newsItems = parseRes(r3);
        } catch { /* give up */ }
      }

      if (newsItems.length > 0) {
        const mapped: EnrichedNews[] = newsItems.map((item: any) => ({
          id: item.id,
          timestamp: item.timestamp,
          source: item.source,
          headline: item.headline,
          content: item.content || "",
          category: item.category,
          url: item.url,
          impacts: item.impacts || [],
          sentiment: item.sentiment || "neutral",
          volatilityExpectation: item.volatility_expectation || item.volatilityExpectation || "medium",
          urgency: item.urgency || "medium",
          eventDuration: item.event_duration || item.eventDuration || "short_term",
          affectedCandles: item.affected_candles || item.affectedCandles || [],
          aiConfidence: typeof item.ai_confidence === "number"
            ? (item.ai_confidence <= 1 ? item.ai_confidence * 100 : item.ai_confidence)
            : (item.aiConfidence || 70),
          analysisTimestamp: item.analysis_timestamp || item.analysisTimestamp || new Date().toISOString(),
        }));
        setEvents(mapped);
      } else {
        setEvents([]);
      }
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, timeframe, mounted]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!mounted) {
    return <div className="min-h-[600px] bg-slate-950 rounded-lg animate-pulse" />;
  }

  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
      {/* Header with Tabs */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-6">
          {/* Symbol Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 uppercase font-semibold">Symbol</span>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {symbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>
          </div>

          {/* Tabs */}
          <div className="flex items-center bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab("chart")}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all",
                activeTab === "chart"
                  ? "bg-blue-500 text-white"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <BarChart2 className="w-4 h-4" />
              Chart View
            </button>
            <button
              onClick={() => setActiveTab("feed")}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all",
                activeTab === "feed"
                  ? "bg-purple-500 text-white"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <Newspaper className="w-4 h-4" />
              News Feed
            </button>
          </div>
        </div>

        {/* Timeframe selector (only on chart tab) */}
        {activeTab === "chart" && (
          <div className="flex items-center gap-1 bg-slate-800 rounded-lg p-1">
            {timeframes.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setTimeframe(tf.value)}
                className={cn(
                  "px-3 py-1 rounded-md text-xs font-medium transition-all",
                  timeframe === tf.value
                    ? "bg-slate-600 text-white"
                    : "text-slate-400 hover:text-white hover:bg-slate-700"
                )}
              >
                {tf.label}
              </button>
            ))}
          </div>
        )}

        {/* Open Full News Feed Page */}
        {activeTab === "feed" && (
          <Link
            href="/news-feed"
            className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg text-sm font-medium hover:bg-purple-500/30 transition-colors"
          >
            <Maximize2 className="w-4 h-4" />
            Full Page View
          </Link>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === "chart" ? (
          <ChartView
            chartData={chartData}
            events={events}
            symbol={selectedSymbol}
            timeframe={timeframe}
            loading={loading}
            error={error}
            onRefresh={fetchData}
          />
        ) : (
          <NewsFeedView
            symbol={selectedSymbol}
            events={events}
            loading={loading}
            error={error}
          />
        )}
      </div>
    </div>
  );
}

// Chart View Component
interface ChartViewProps {
  chartData: ChartCandle[];
  events: EnrichedNews[];
  symbol: string;
  timeframe: TimeframeValue;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

function ChartView({ chartData, events, symbol, timeframe, loading, error, onRefresh }: ChartViewProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<any[]>([]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current || chartData.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "rgba(51, 65, 85, 0.3)" },
        horzLines: { color: "rgba(51, 65, 85, 0.3)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "#60a5fa",
          labelBackgroundColor: "#3b82f6",
        },
        horzLine: {
          color: "#60a5fa",
          labelBackgroundColor: "#3b82f6",
        },
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
        secondsVisible: false,
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

    // Format data
    const formattedData = chartData.map((candle) => ({
      time: candle.time as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    candlestickSeries.setData(formattedData);
    chart.timeScale().fitContent();

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [chartData]);

  // Add news markers
  useEffect(() => {
    if (!candlestickSeriesRef.current || events.length === 0 || chartData.length === 0) return;

    // Clear existing markers
    markersRef.current.forEach((marker) => {
      // Note: Lightweight Charts doesn't have a direct removeMarker method
      // We need to clear and reset all markers
    });

    const chartStartTime = chartData[0]?.time || 0;
    const chartEndTime = chartData[chartData.length - 1]?.time || 0;

    const markers = events
      .filter((event) => {
        const eventTime = Math.floor(new Date(event.timestamp).getTime() / 1000);
        return eventTime >= chartStartTime && eventTime <= chartEndTime;
      })
      .slice(0, 10) // Limit to 10 markers
      .map((event) => {
        const eventTime = Math.floor(new Date(event.timestamp).getTime() / 1000);
        const marker: any = {
          time: eventTime as Time,
          position: "aboveBar",
          color: event.urgency === "breaking" ? "#ef4444" : event.urgency === "high" ? "#f97316" : "#eab308",
          shape: event.urgency === "breaking" ? "arrowDown" : "circle",
          size: event.urgency === "breaking" ? 2 : 1,
          text: event.urgency === "breaking" ? "!" : "",
        };
        return marker;
      });

    candlestickSeriesRef.current.setMarkers(markers);
    markersRef.current = markers;
  }, [events, chartData]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-[500px] bg-slate-900/50 rounded-lg animate-pulse" />
        <div className="h-[500px] bg-slate-900/50 rounded-lg animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[500px] text-red-400">
        <div className="text-center">
          <p>{error}</p>
          <button
            onClick={onRefresh}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Chart */}
      <div className="lg:col-span-2">
        <div ref={chartContainerRef} className="w-full h-[500px]" />
      </div>

      {/* News Sidebar */}
      <div className="bg-slate-900/30 rounded-lg border border-slate-800 p-4 overflow-y-auto h-[500px]">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-purple-400" />
          News Events
        </h3>

        {events.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-8">No recent news events</p>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={cn(
                      "w-2 h-2 rounded-full",
                      event.urgency === "breaking" && "bg-red-500",
                      event.urgency === "high" && "bg-orange-500",
                      event.urgency === "medium" && "bg-yellow-500",
                      event.urgency === "low" && "bg-slate-500"
                    )}
                  />
                  <span className="text-xs text-slate-500">
                    {format(new Date(event.timestamp), "MMM d, HH:mm")}
                  </span>
                </div>
                <p className="text-sm text-slate-300 line-clamp-2">{event.headline}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {event.impacts.slice(0, 3).map((impact, idx) => (
                    <span
                      key={idx}
                      className={cn(
                        "text-xs px-2 py-0.5 rounded",
                        impact.direction === "bullish" && "bg-green-500/20 text-green-400",
                        impact.direction === "bearish" && "bg-red-500/20 text-red-400",
                        impact.direction !== "bullish" && impact.direction !== "bearish" && "bg-slate-700 text-slate-400"
                      )}
                    >
                      {impact.symbol}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// News Feed View Component
interface NewsFeedViewProps {
  symbol: string;
  events: EnrichedNews[];
  loading: boolean;
  error: string | null;
}

function NewsFeedView({ symbol, events, loading, error }: NewsFeedViewProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "breaking" | "high" | "medium">("all");

  const filteredEvents = events.filter((e) => {
    if (filter === "all") return true;
    return e.urgency === filter;
  });

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-48 bg-slate-900/50 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-400">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex items-center gap-2">
        {["all", "breaking", "high", "medium"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f as any)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
              filter === f
                ? "bg-purple-500 text-white"
                : "bg-slate-800 text-slate-400 hover:text-white"
            )}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">
          {filteredEvents.length} events for {symbol}
        </span>
      </div>

      {/* News Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredEvents.map((event) => (
          <NewsCard
            key={event.id}
            event={event}
            isExpanded={expandedId === event.id}
            onToggle={() => setExpandedId(expandedId === event.id ? null : event.id)}
          />
        ))}
      </div>

      {filteredEvents.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-500">No news matching your filters</p>
        </div>
      )}
    </div>
  );
}

// News Card Component
interface NewsCardProps {
  event: EnrichedNews;
  isExpanded: boolean;
  onToggle: () => void;
}

function NewsCard({ event, isExpanded, onToggle }: NewsCardProps) {
  const impactColors = {
    breaking: "bg-red-900/30 border-red-700/50 text-red-300",
    high: "bg-orange-900/30 border-orange-700/50 text-orange-300",
    medium: "bg-yellow-900/30 border-yellow-700/50 text-yellow-300",
    low: "bg-slate-800/50 border-slate-700/50 text-slate-400",
  };

  return (
    <div
      className={cn(
        "rounded-xl border p-4 transition-all cursor-pointer",
        impactColors[event.urgency as keyof typeof impactColors],
        isExpanded && "shadow-lg shadow-red-900/10"
      )}
      onClick={onToggle}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "w-2 h-2 rounded-full",
              event.urgency === "breaking" && "bg-red-500 animate-pulse",
              event.urgency === "high" && "bg-orange-500",
              event.urgency === "medium" && "bg-yellow-500",
              event.urgency === "low" && "bg-slate-500"
            )}
          />
          <span className="text-xs uppercase font-bold opacity-70">
            {event.urgency}
          </span>
        </div>
        <span className="text-xs opacity-50">
          {format(new Date(event.timestamp), "HH:mm")}
        </span>
      </div>

      {/* Title */}
      <h4 className="text-sm font-semibold mb-3 line-clamp-2">{event.headline}</h4>

      {/* Impact Badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {event.impacts.slice(0, 4).map((impact, idx) => (
          <span
            key={idx}
            className={cn(
              "text-xs px-2 py-0.5 rounded-full border",
              impact.direction === "bullish" && "bg-green-500/20 text-green-400 border-green-500/30",
              impact.direction === "bearish" && "bg-red-500/20 text-red-400 border-red-500/30",
              impact.direction !== "bullish" && impact.direction !== "bearish" && "bg-slate-700 text-slate-400 border-slate-600"
            )}
          >
            {impact.symbol} {impact.score}/10
          </span>
        ))}
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-white/10 space-y-3">
          <div>
            <span className="text-xs opacity-50">AI Analysis</span>
            <p className="text-sm mt-1 leading-relaxed">{event.content}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs opacity-50">Sentiment</span>
              <p className={cn(
                "text-sm font-medium capitalize",
                event.sentiment === "risk_on" && "text-green-400",
                event.sentiment === "risk_off" && "text-red-400",
                event.sentiment === "neutral" && "text-yellow-400"
              )}>
                {event.sentiment?.replace("_", " ")}
              </p>
            </div>
            <div>
              <span className="text-xs opacity-50">Source</span>
              <p className="text-sm">{event.source}</p>
            </div>
          </div>

          <div>
            <span className="text-xs opacity-50">AI Confidence</span>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-500 rounded-full"
                  style={{ width: `${event.aiConfidence}%` }}
                />
              </div>
              <span className="text-xs">{Math.round(event.aiConfidence)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
