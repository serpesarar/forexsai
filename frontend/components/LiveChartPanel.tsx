"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import {
  ColorType,
  createChart,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  Time,
} from "lightweight-charts";
import { Activity, RefreshCw, TrendingUp, TrendingDown } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

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
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"] as const;
type TimeframeType = (typeof TIMEFRAMES)[number];

async function fetchChartData(symbol: string, timeframe: string): Promise<CandleData[]> {
  const res = await fetch(
    `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=200`
  );
  if (!res.ok) throw new Error("Failed to fetch chart data");
  const data = await res.json();
  return data.data || [];
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

export default function LiveChartPanel({
  symbol,
  symbolLabel,
  height = 400,
}: LiveChartPanelProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const ema20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  const [timeframe, setTimeframe] = useState<TimeframeType>("15m");
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Fetch chart data
  const { data: chartData, isLoading, refetch } = useQuery({
    queryKey: ["live-chart", symbol, timeframe],
    queryFn: () => fetchChartData(symbol, timeframe),
    refetchInterval: 10000, // Refresh every 10 seconds
    staleTime: 5000,
  });

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
    const interval = setInterval(fetchPrice, 2000);
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
  }, [height]);

  // Update data
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

      chart.timeScale().fitContent();
    } catch (err) {
      console.error("Chart data update error:", err);
    }
  }, [chartData]);

  // Calculate price change
  const firstCandle = chartData?.[0];
  const lastCandle = chartData?.[chartData.length - 1];
  const displayPrice = livePrice ?? lastCandle?.close ?? 0;
  const openPrice = firstCandle?.open ?? displayPrice;
  const priceChange = displayPrice - openPrice;
  const priceChangePercent = openPrice > 0 ? (priceChange / openPrice) * 100 : 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
            symbol.includes("XAU") 
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
              <span className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded ${
                isPositive ? "bg-success/20 text-success" : "bg-danger/20 text-danger"
              }`}>
                {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {isPositive ? "+" : ""}{priceChangePercent.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Live indicator */}
          <div className="flex items-center gap-2 text-xs text-textSecondary">
            <div className="relative">
              <div className="h-2 w-2 rounded-full bg-success" />
              <div className="absolute inset-0 h-2 w-2 rounded-full bg-success animate-ping" />
            </div>
            <span className="font-mono">{lastUpdate.toLocaleTimeString("tr-TR")}</span>
          </div>

          {/* Timeframe buttons */}
          <div className="flex gap-1 bg-white/5 rounded-lg p-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1.5 rounded-md text-xs font-bold uppercase transition ${
                  timeframe === tf 
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
      </div>
    </div>
  );
}
