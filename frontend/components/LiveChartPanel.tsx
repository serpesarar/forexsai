"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import {
  ColorType,
  createChart,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  Time,
  MouseEventParams,
} from "lightweight-charts";
import { Activity, RefreshCw, TrendingUp, TrendingDown, Newspaper, X, ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useNewsMarkers, NewsMarker, convertToChartMarkers } from "../hooks/useNewsMarkers";
import { normalizeCandles } from "../lib/chart/normalizeCandles";

interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface LiveChartPanelProps {
  symbol: string;
  symbolLabel: string;
  height?: number;
  showNewsMarkers?: boolean;
}

const API_BASE = "https://upbeat-flow-production.up.railway.app";

const TIMEFRAMES = ["5m", "15m", "1h", "4h"] as const;
type TimeframeType = (typeof TIMEFRAMES)[number];

async function fetchChartData(symbol: string, timeframe: string): Promise<CandleData[]> {
  const res = await fetch(
    `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=200`
  );
  if (!res.ok) throw new Error("Failed to fetch chart data");
  const data = await res.json();
  return normalizeCandles(data.data || [], timeframe);
}

async function fetchLivePrice(symbol: string): Promise<number | null> {
  try {
    const res = await fetch(`${API_BASE}/api/data/cached/${encodeURIComponent(symbol)}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data?.data?.current_price ?? null;
  } catch {
    return null;
  }
}

function calculateEMA(values: number[], period: number): number[] {
  if (values.length === 0) return [];
  const k = 2 / (period + 1);
  const ema: number[] = [];
  let previous: number | null = null;

  values.forEach((value, index) => {
    if (index < period - 1) {
      ema.push(value);
      return;
    }
    if (previous === null) {
      const slice = values.slice(index - period + 1, index + 1);
      const avg = slice.reduce((sum, val) => sum + val, 0) / period;
      previous = avg;
      ema.push(avg);
      return;
    }
    const next = (value - previous) * k + previous;
    previous = next;
    ema.push(next);
  });

  return ema;
}

// Haber detay tooltip component
function NewsTooltip({ marker, onClose, position }: { marker: NewsMarker; onClose: () => void; position: { x: number; y: number } }) {
  const getDirectionColor = (dir: string) => {
    if (dir === "bullish") return "text-green-400";
    if (dir === "bearish") return "text-red-400";
    return "text-gray-400";
  };

  const getUrgencyIcon = (urgency: string) => {
    if (urgency === "breaking") return "🚨";
    if (urgency === "high") return "🔴";
    if (urgency === "medium") return "🟡";
    return "🟢";
  };

  return (
    <div
      className="fixed z-50 w-80 bg-slate-900/95 backdrop-blur-md border border-white/10 rounded-xl shadow-2xl p-4 animate-in fade-in zoom-in-95 duration-200"
      style={{
        left: Math.min(position.x, window.innerWidth - 340),
        top: Math.min(position.y, window.innerHeight - 300),
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{getUrgencyIcon(marker.urgency)}</span>
          <span className={`text-xs font-bold uppercase tracking-wider ${getDirectionColor(marker.direction)}`}>
            {marker.direction}
          </span>
          <span className="text-xs text-slate-400">Score: {marker.score}/10</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-white/10 rounded-lg transition"
        >
          <X className="w-4 h-4 text-slate-400" />
        </button>
      </div>

      <h4 className="text-sm font-semibold text-white mb-2 leading-tight">
        {marker.headline}
      </h4>

      {marker.headline_en && marker.headline_en !== marker.headline && (
        <p className="text-xs text-slate-400 mb-2 italic">{marker.headline_en}</p>
      )}

      {marker.reasoning_tr && (
        <p className="text-xs text-slate-300 mb-3 bg-white/5 p-2 rounded-lg">
          💡 {marker.reasoning_tr}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>{new Date(marker.time).toLocaleString("tr-TR")}</span>
        {marker.url && (
          <a
            href={marker.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition"
          >
            Haber <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
}

export default function LiveChartPanel({
  symbol,
  symbolLabel,
  height = 400,
  showNewsMarkers = true,
}: LiveChartPanelProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const ema20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  const [timeframe, setTimeframe] = useState<TimeframeType>("15m");
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [selectedMarker, setSelectedMarker] = useState<NewsMarker | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [showMarkers, setShowMarkers] = useState(true);

  // Fetch chart data
  const { data: chartData, isLoading, refetch } = useQuery({
    queryKey: ["live-chart", symbol, timeframe],
    queryFn: () => fetchChartData(symbol, timeframe),
    refetchInterval: 60000,
    staleTime: 30000,
  });

  // Fetch news markers
  const { markers: newsMarkers, loading: markersLoading } = useNewsMarkers(
    symbol,
    24,
    5
  );

  // Fetch live price every 2 seconds
  useEffect(() => {
    const fetchPrice = async () => {
      const price = await fetchLivePrice(symbol);
      if (price !== null) {
        setLivePrice(price);
        setLastUpdate(new Date());
      }
    };

    fetchPrice();
    const interval = setInterval(fetchPrice, 5000);
    return () => clearInterval(interval);
  }, [symbol]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;
    if (chartInstanceRef.current) return;

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
        fontSize: 12,
      },
      watermark: { visible: false },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.03)" },
        horzLines: { color: "rgba(255,255,255,0.03)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "rgba(255,255,255,0.2)", labelBackgroundColor: "#1e293b" },
        horzLine: { color: "rgba(255,255,255,0.2)", labelBackgroundColor: "#1e293b" },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
        borderColor: "rgba(255,255,255,0.1)",
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.1)",
      },
      handleScroll: { vertTouchDrag: false },
      handleScale: { axisPressedMouseMove: false },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const volumeSeries = chart.addHistogramSeries({
      color: "rgba(100,100,100,0.5)",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    const ema20Series = chart.addLineSeries({
      color: "#3b82f6",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const ema50Series = chart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const resizeObserver = new ResizeObserver(() => {
      try {
        chart.applyOptions({ width: container.clientWidth });
      } catch {
        // noop
      }
    });
    resizeObserver.observe(container);

    // Click handler for markers
    chart.subscribeClick((param: MouseEventParams) => {
      if (param.point && param.time) {
        const clickedTime = new Date((param.time as number) * 1000);
        const timeWindow = 5 * 60 * 1000; // 5 minutes window

        const clickedMarker = newsMarkers.find((m) => {
          const markerTime = new Date(m.time).getTime();
          const clickTimeMs = clickedTime.getTime();
          return Math.abs(markerTime - clickTimeMs) < timeWindow;
        });

        if (clickedMarker) {
          setSelectedMarker(clickedMarker);
          setTooltipPosition({ x: param.point.x, y: param.point.y });
        } else {
          setSelectedMarker(null);
        }
      }
    });

    chartInstanceRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    ema20SeriesRef.current = ema20Series;
    ema50SeriesRef.current = ema50Series;

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartInstanceRef.current = null;
    };
  }, [height, newsMarkers]);

  // Update chart data
  useEffect(() => {
    const chart = chartInstanceRef.current;
    const candleSeries = candleSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    const ema20Series = ema20SeriesRef.current;
    const ema50Series = ema50SeriesRef.current;

    if (!chart || !candleSeries || !volumeSeries || !chartData?.length) return;

    try {
      const candles = chartData.map((d) => ({
        time: (d.timestamp / 1000) as Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

      const volumes = chartData.map((d) => ({
        time: (d.timestamp / 1000) as Time,
        value: d.volume,
        color: d.close >= d.open ? "rgba(34,197,94,0.4)" : "rgba(239,68,68,0.4)",
      }));

      const closes = chartData.map((d) => d.close);
      const ema20Values = calculateEMA(closes, 20);
      const ema50Values = calculateEMA(closes, 50);

      const ema20Data = chartData.map((d, i) => ({
        time: (d.timestamp / 1000) as Time,
        value: ema20Values[i],
      }));

      const ema50Data = chartData.map((d, i) => ({
        time: (d.timestamp / 1000) as Time,
        value: ema50Values[i],
      }));

      candleSeries.setData(candles);
      volumeSeries.setData(volumes);
      if (ema20Series) ema20Series.setData(ema20Data);
      if (ema50Series) ema50Series.setData(ema50Data);

      // Add news markers
      if (candleSeries && showMarkers && newsMarkers.length > 0) {
        const chartStartTime = chartData[0].timestamp;
        const chartEndTime = chartData[chartData.length - 1].timestamp;

        const visibleMarkers = newsMarkers
          .filter((m) => {
            const markerTime = new Date(m.time).getTime();
            return markerTime >= chartStartTime && markerTime <= chartEndTime;
          })
          .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

        candleSeries.setMarkers(convertToChartMarkers(visibleMarkers) as any[]);
      } else if (candleSeries) {
        candleSeries.setMarkers([]);
      }

      chart.timeScale().fitContent();
    } catch (err) {
      console.error("Chart data update error:", err);
    }
  }, [chartData, newsMarkers, showMarkers]);

  // Calculate price change
  const firstCandle = chartData?.[0];
  const lastCandle = chartData?.[chartData.length - 1];
  const displayPrice = livePrice ?? lastCandle?.close ?? 0;
  const openPrice = firstCandle?.open ?? displayPrice;
  const priceChange = displayPrice - openPrice;
  const priceChangePercent = openPrice > 0 ? (priceChange / openPrice) * 100 : 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="glass-premium rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${symbol.includes("XAU")
            ? "bg-gradient-to-br from-amber-500/30 to-yellow-500/30"
            : "bg-gradient-to-br from-emerald-500/30 to-teal-500/30"
            }`}>
            <Activity className={`h-5 w-5 ${symbol.includes("XAU") ? "text-amber-400" : "text-emerald-400"}`} />
          </div>
          <div>
            <h3 className="font-bold text-lg">{symbolLabel}</h3>
            <div className="flex items-center gap-2 text-sm">
              <span className="font-mono text-lg font-semibold">
                {displayPrice.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded ${isPositive ? "bg-success/20 text-success" : "bg-danger/20 text-danger"
                }`}>
                {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {isPositive ? "+" : ""}{priceChangePercent.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* News toggle */}
          {showNewsMarkers && (
            <button
              onClick={() => setShowMarkers(!showMarkers)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${showMarkers
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
                }`}
            >
              <Newspaper className="w-3.5 h-3.5" />
              Haberler {showMarkers ? "Açık" : "Kapalı"}
              {newsMarkers.length > 0 && (
                <span className="bg-white/20 px-1.5 py-0.5 rounded-full text-[10px]">
                  {newsMarkers.length}
                </span>
              )}
            </button>
          )}

          {/* Live indicator */}
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <div className="relative">
              <div className="h-2 w-2 rounded-full bg-success" />
              <div className="absolute inset-0 h-2 w-2 rounded-full bg-success animate-ping" />
            </div>
            <span className="font-mono" suppressHydrationWarning>
              {lastUpdate ? lastUpdate.toLocaleTimeString("tr-TR") : "--:--"}
            </span>
          </div>

          {/* Timeframe buttons */}
          <div className="flex gap-1 bg-white/5 rounded-lg p-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1.5 rounded-md text-xs font-bold uppercase transition ${timeframe === tf
                  ? "bg-accent text-white"
                  : "text-textSecondary hover:text-white hover:bg-white/10"
                  }`}
              >
                {tf}
              </button>
            ))}
          </div>

          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="p-2">
        <div className="relative" style={{ height, width: "100%" }}>
          <div ref={chartContainerRef} style={{ height: "100%", width: "100%" }} />

          {(isLoading || !chartData?.length) && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm">
              <div className="text-center">
                <Activity className="h-12 w-12 mx-auto mb-3 opacity-30 animate-pulse" />
                <p className="text-textSecondary">
                  {isLoading ? "Grafik verisi yükleniyor..." : "Grafik verisi yok"}
                </p>
              </div>
            </div>
          )}

          {/* Marker Legend */}
          {showMarkers && newsMarkers.length > 0 && (
            <div className="absolute top-2 left-2 bg-slate-900/80 backdrop-blur-sm rounded-lg p-2 border border-white/10">
              <div className="flex items-center gap-3 text-[10px] text-slate-300">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  <span>Pozitif</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500"></span>
                  <span>Negatif</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span>Nötr</span>
                </div>
              </div>
              <p className="text-[9px] text-slate-400 mt-1">Mum üzerindeki noktalara tıklayın</p>
            </div>
          )}
        </div>
      </div>

      {/* EMA Legend */}
      <div className="flex gap-4 px-4 py-2 border-t border-white/5 text-xs">
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-4 bg-blue-500 rounded" />
          <span className="text-textSecondary">EMA 20</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-4 bg-amber-500 rounded" />
          <span className="text-textSecondary">EMA 50</span>
        </div>
        {newsMarkers.length > 0 && (
          <div className="flex items-center gap-2 ml-auto">
            <Newspaper className="w-3 h-3 text-slate-400" />
            <span className="text-textSecondary">{newsMarkers.length} haber işaretlendi</span>
          </div>
        )}
      </div>

      {/* News Tooltip */}
      {selectedMarker && (
        <NewsTooltip
          marker={selectedMarker}
          onClose={() => setSelectedMarker(null)}
          position={tooltipPosition}
        />
      )}
    </div>
  );
}
