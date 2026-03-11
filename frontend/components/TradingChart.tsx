"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ColorType,
  createChart,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  Time,
} from "lightweight-charts";
import { Maximize2, RefreshCw, Activity, X, TrendingUp } from "lucide-react";
import { normalizeCandles } from "../lib/chart/normalizeCandles";
import {
  buildCompressedChartCandles,
  findTimelineChartCandle,
  mapActualTimestampToChartTime,
} from "../lib/chart/newsCorrelationTimeline";

interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface NewsMarkerData {
  time: number;
  position: 'aboveBar' | 'belowBar' | 'inBar';
  color: string;
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
  text: string;
  size: number;
  // Custom data for tooltip
  id?: string;
  headline?: string;
  headline_en?: string;
  direction?: string;
  score?: number;
  urgency?: string;
  is_economic_event?: boolean;
  event_name?: string;
  reasoning_tr?: string;
  url?: string;
}

interface TradingChartProps {
  symbol: string;
  symbolLabel: string;
  data: CandleData[];
  height?: number;
  onRefresh?: () => void;
  isLoading?: boolean;
  currentTimeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  newsMarkers?: NewsMarkerData[];
  onMarkerClick?: (marker: NewsMarkerData) => void;
}

// EMA calculation helper
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

export default function TradingChart({
  symbol,
  symbolLabel,
  data,
  height = 400,
  onRefresh,
  isLoading = false,
  currentTimeframe = "1d",
  onTimeframeChange,
  newsMarkers = [],
  onMarkerClick,
}: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const ema20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [windowSize, setWindowSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });
  const [chartReady, setChartReady] = useState(false);
  const [ohlcLegend, setOhlcLegend] = useState<{
    o: number;
    h: number;
    l: number;
    c: number;
    time: string;
  } | null>(null);
  const normalizedData = useMemo(() => normalizeCandles(data, currentTimeframe), [data, currentTimeframe]);
  const compressedData = useMemo(
    () => buildCompressedChartCandles(normalizedData, currentTimeframe),
    [normalizedData, currentTimeframe]
  );
  const compressedDataRef = useRef(compressedData);
  const mappedNewsMarkers = useMemo(
    () =>
      newsMarkers.flatMap((marker) => {
        const mappedTime = mapActualTimestampToChartTime(marker.time, compressedData);
        if (!Number.isFinite(mappedTime)) {
          return [];
        }

        return [{ ...marker, time: mappedTime as number }];
      }),
    [newsMarkers, compressedData]
  );

  useEffect(() => {
    compressedDataRef.current = compressedData;
  }, [compressedData]);

  useEffect(() => {
    const onResize = () => {
      setWindowSize({ w: window.innerWidth, h: window.innerHeight });
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const chartHeight = useMemo(() => {
    if (!isFullscreen) return height;
    // Header + legend area reserve
    const reserved = 120;
    return Math.max(280, (windowSize.h || window.innerHeight) - reserved);
  }, [height, isFullscreen, windowSize.h]);

  // Initialize chart once on mount (do NOT recreate on fullscreen toggle)
  useEffect(() => {
    if (!chartContainerRef.current) return;
    if (chartInstanceRef.current) return;

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: chartHeight,
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
        secondsVisible: false,
        borderColor: "rgba(255,255,255,0.1)",
        fixLeftEdge: true,
        fixRightEdge: false,
        rightOffset: 12,
        barSpacing: 6,
        tickMarkFormatter: (time: Time) => {
          const numericTime = typeof time === "number" ? time : Number(time);
          const candle = findTimelineChartCandle(numericTime, compressedDataRef.current);
          const labelTimestamp = candle?.actualTimestamp ?? numericTime;

          if (!Number.isFinite(labelTimestamp)) {
            return "";
          }

          return new Date(labelTimestamp * 1000).toLocaleString("tr-TR", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          });
        },
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.1)",
      },
    });

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: "rgba(100,100,100,0.5)",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    // EMA lines
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

    // Crosshair handler
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData) {
        setOhlcLegend(null);
        return;
      }
      const candle = param.seriesData.get(candleSeries) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      if (candle) {
        const numericTime = typeof param.time === "number" ? param.time : Number(param.time);
        const timelineCandle = findTimelineChartCandle(numericTime, compressedDataRef.current);
        const displayTimestamp = timelineCandle?.actualTimestamp ?? numericTime;

        setOhlcLegend({
          o: candle.open,
          h: candle.high,
          l: candle.low,
          c: candle.close,
          time: new Date(displayTimestamp * 1000).toLocaleDateString("tr-TR"),
        });
      }
    });

    // Resize handler (ONLY width here; height is controlled by chartHeight effect)
    const resizeObserver = new ResizeObserver(() => {
      try {
        chart.applyOptions({ width: container.clientWidth });
      } catch {
        // noop
      }
    });
    resizeObserver.observe(container);

    // Store refs
    chartInstanceRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    ema20SeriesRef.current = ema20Series;
    ema50SeriesRef.current = ema50Series;
    setChartReady(true);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartInstanceRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      ema20SeriesRef.current = null;
      ema50SeriesRef.current = null;
      setChartReady(false);
    };
  }, [chartHeight]);

  // Resize chart when fullscreen toggles / height changes
  // Use rAF to avoid measuring width=0 during layout transitions.
  useEffect(() => {
    const chart = chartInstanceRef.current;
    const container = chartContainerRef.current;
    if (!chart || !container) return;

    const raf1 = requestAnimationFrame(() => {
      const raf2 = requestAnimationFrame(() => {
        try {
          const width = container.clientWidth || window.innerWidth;
          chart.applyOptions({ width, height: chartHeight });
          chart.timeScale().fitContent();
        } catch {
          // noop
        }
      });

      return () => cancelAnimationFrame(raf2);
    });

    return () => cancelAnimationFrame(raf1);
  }, [chartHeight, isFullscreen]);

  // Update data when it changes
  useEffect(() => {
    const chart = chartInstanceRef.current;
    const candleSeries = candleSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    const ema20Series = ema20SeriesRef.current;
    const ema50Series = ema50SeriesRef.current;

    if (!chart || !candleSeries || !volumeSeries || !compressedData.length) return;

    try {
      // Format candle data
      const candles = compressedData.map((d) => ({
        time: d.time as Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

      // Format volume data
      const volumes = compressedData.map((d) => ({
        time: d.time as Time,
        value: d.volume,
        color: d.close >= d.open ? "rgba(34,197,94,0.4)" : "rgba(239,68,68,0.4)",
      }));

      // Calculate EMAs
      const closes = compressedData.map((d) => d.close);
      const ema20Values = calculateEMA(closes, 20);
      const ema50Values = calculateEMA(closes, 50);

      const ema20Data = compressedData.map((d, i) => ({
        time: d.time as Time,
        value: ema20Values[i],
      }));

      const ema50Data = compressedData.map((d, i) => ({
        time: d.time as Time,
        value: ema50Values[i],
      }));

      // Set data
      candleSeries.setData(candles);
      volumeSeries.setData(volumes);
      if (ema20Series) ema20Series.setData(ema20Data);
      if (ema50Series) ema50Series.setData(ema50Data);

      // Fit content
      chart.timeScale().fitContent();
    } catch (err) {
      console.error("Chart data update error:", err);
    }
  }, [chartReady, compressedData]);

  // Apply news markers when they change
  useEffect(() => {
    const candleSeries = candleSeriesRef.current;
    const chart = chartInstanceRef.current;
    if (!candleSeries || !chart) return;

    try {
      // Clear existing markers if none provided
      if (!mappedNewsMarkers.length) {
        candleSeries.setMarkers([]);
        return;
      }

      // Format markers for lightweight-charts
      const formattedMarkers = mappedNewsMarkers.map(m => ({
        time: m.time as Time,
        position: m.position,
        color: m.color,
        shape: m.shape,
        text: m.text,
        size: m.size,
      }));

      candleSeries.setMarkers(formattedMarkers);
      
      console.log(`[TradingChart] Applied ${formattedMarkers.length} news markers for ${symbol}`);
    } catch (err) {
      console.error("[TradingChart] Marker update error:", err);
    }
  }, [mappedNewsMarkers, symbol]);

  // Handle marker clicks
  useEffect(() => {
    const chart = chartInstanceRef.current;
    if (!chart || !onMarkerClick) return;

    const handleClick = (param: any) => {
      if (!param.point || !param.time || !mappedNewsMarkers.length) return;
      
      const clickedTime = param.time as number;
      const timeWindow = Math.max(1, Math.floor((Number(compressedData[1]?.time) || clickedTime) - (Number(compressedData[0]?.time) || clickedTime)));
      
      // Find marker near click time
      const clickedMarker = mappedNewsMarkers.find(m => 
        Math.abs(Number(m.time) - clickedTime) < timeWindow
      );
      
      if (clickedMarker) {
        onMarkerClick(clickedMarker);
      }
    };

    chart.subscribeClick(handleClick);
    
    return () => {
      chart.unsubscribeClick(handleClick);
    };
  }, [mappedNewsMarkers, onMarkerClick, compressedData]);

  // Calculate price info
  const latestCandle = normalizedData[normalizedData.length - 1];
  const prevCandle = normalizedData[normalizedData.length - 2];
  const priceChange = latestCandle && prevCandle ? latestCandle.close - prevCandle.close : 0;
  const priceChangePercent = prevCandle ? (priceChange / prevCandle.close) * 100 : 0;

  return (
    <div
      className={
        isFullscreen
          ? "fixed inset-0 z-50 bg-background flex flex-col"
          : "glass-premium rounded-2xl overflow-hidden"
      }
    >
      {/* Header */}
      <div className={isFullscreen ? "flex items-center justify-between px-6 py-4 border-b border-white/10" : "flex items-center justify-between p-4 border-b border-white/5"}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/30 to-cyan-500/30">
            <Activity className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h3 className={isFullscreen ? "text-xl font-bold" : "font-bold"}>{symbolLabel}</h3>
            {latestCandle && (
              <div className="flex items-center gap-2 text-sm">
                <span className="font-mono">
                  {latestCandle.close.toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                </span>
                <span className={`text-xs ${priceChange >= 0 ? "text-success" : "text-danger"}`}>
                  {priceChange >= 0 ? "+" : ""}
                  {priceChangePercent.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Timeframe buttons */}
          <div className="flex gap-1 bg-white/5 rounded-lg p-1">
            {["1h", "4h", "1d"].map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange?.(tf)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  currentTimeframe === tf ? "bg-accent text-white" : "text-textSecondary hover:text-white"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          )}

          {isFullscreen ? (
            <button onClick={() => setIsFullscreen(false)} className="p-2 rounded-lg bg-white/5 hover:bg-white/10">
              <X className="h-4 w-4" />
            </button>
          ) : (
            <button onClick={() => setIsFullscreen(true)} className="p-2 rounded-lg bg-white/5 hover:bg-white/10">
              <Maximize2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* OHLC Legend */}
      {ohlcLegend && (
        <div className="flex gap-4 px-4 py-2 text-xs border-b border-white/5 bg-white/[0.02]">
          <span className="text-textSecondary">{ohlcLegend.time}</span>
          <span>O: <span className="font-mono">{ohlcLegend.o.toFixed(2)}</span></span>
          <span>H: <span className="font-mono text-success">{ohlcLegend.h.toFixed(2)}</span></span>
          <span>L: <span className="font-mono text-danger">{ohlcLegend.l.toFixed(2)}</span></span>
          <span>C: <span className="font-mono">{ohlcLegend.c.toFixed(2)}</span></span>
        </div>
      )}

      {/* Chart */}
      <div className={isFullscreen ? "flex-1 p-4" : "p-2"}>
        <div className="relative" style={{ height: chartHeight, width: "100%" }}>
          <div ref={chartContainerRef} style={{ height: "100%", width: "100%" }} />

          {(isLoading || data.length === 0) && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm">
              <div className="text-center">
                <Activity className="h-12 w-12 mx-auto mb-3 opacity-30 animate-pulse" />
                <p className="text-textSecondary">
                  {isLoading ? "Grafik verisi yükleniyor..." : "Grafik verisi yok"}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* EMA Legend */}
      {!isFullscreen && (
        <div className="flex gap-4 px-4 py-2 border-t border-white/5 text-xs">
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-4 bg-blue-500 rounded" />
          <span className="text-textSecondary">EMA 20</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-4 bg-amber-500 rounded" />
          <span className="text-textSecondary">EMA 50</span>
        </div>
        </div>
      )}
    </div>
  );
}
