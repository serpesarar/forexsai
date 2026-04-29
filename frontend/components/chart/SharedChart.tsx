"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, type IChartApi, type ISeriesApi, CrosshairMode } from "lightweight-charts";
import { fetcher } from "../../lib/api";

type Timeframe = "5m" | "15m" | "1h" | "4h" | "1d";

interface CandleDTO {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface Props {
  symbol: string;
  defaultTimeframe?: Timeframe;
  height?: number;
}

const TF_BARS: Record<Timeframe, number> = {
  "5m": 200,
  "15m": 200,
  "1h": 300,
  "4h": 300,
  "1d": 365,
};

const TF_OPTIONS: Timeframe[] = ["5m", "15m", "1h", "4h", "1d"];

export function SharedChart({ symbol, defaultTimeframe = "1h", height = 420 }: Props) {
  const [tf, setTf] = useState<Timeframe>(defaultTimeframe);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // Create chart once
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        fontFamily: "'Inter', sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(148,163,184,0.06)" },
        horzLines: { color: "rgba(148,163,184,0.06)" },
      },
      rightPriceScale: { borderColor: "rgba(148,163,184,0.15)" },
      timeScale: { borderColor: "rgba(148,163,184,0.15)", timeVisible: true, secondsVisible: false },
      crosshair: { mode: CrosshairMode.Normal },
      autoSize: true,
    });

    const series = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#f43f5e",
      borderUpColor: "#10b981",
      borderDownColor: "#f43f5e",
      wickUpColor: "#10b981",
      wickDownColor: "#f43f5e",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver(() => chart.applyOptions({}));
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Fetch candles when symbol or tf changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const bars = TF_BARS[tf];
    const url = `/api/data/cached/${encodeURIComponent(symbol)}?timeframe=${tf}&bars=${bars}`;

    fetcher<{ success: boolean; data: { candles: CandleDTO[] } }>(url)
      .then((res) => {
        if (cancelled) return;
        if (!res?.success || !res?.data?.candles) {
          setError("No candle data");
          setLoading(false);
          return;
        }
        const candles = res.data.candles
          .map((c) => ({
            time: (typeof c.time === "string" ? new Date(c.time).getTime() / 1000 : c.time) as any,
            open: Number(c.open),
            high: Number(c.high),
            low: Number(c.low),
            close: Number(c.close),
          }))
          .filter((c) => Number.isFinite(c.open) && Number.isFinite(c.close))
          .sort((a, b) => (a.time as number) - (b.time as number));

        if (seriesRef.current) {
          seriesRef.current.setData(candles as any);
          chartRef.current?.timeScale().fitContent();
        }
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.message || "Failed to load");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [symbol, tf]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/60 p-1">
          {TF_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setTf(opt)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                tf === opt ? "bg-slate-700 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
        <div className="text-xs text-slate-500">
          {loading ? "Loading…" : error ? <span className="text-rose-400">{error}</span> : `${symbol} · ${tf}`}
        </div>
      </div>
      <div
        ref={containerRef}
        className="w-full rounded-xl border border-slate-800 bg-slate-950/60"
        style={{ height }}
      />
    </div>
  );
}

export default SharedChart;
