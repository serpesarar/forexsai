"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ColorType,
  createChart,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  LineStyle,
  Time,
} from "lightweight-charts";
import type { CandleData, OrderBlockResponse, SupportResistanceLevel } from "./useChartData";
import ChartOverlays from "./ChartOverlays";

export interface LegendPoint {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface CandlestickChartProps {
  data: CandleData[];
  supportResistance: SupportResistanceLevel[];
  orderBlocks?: OrderBlockResponse;
  patterns?: Array<{
    pattern_name: string;
    signal: "bullish" | "bearish" | "neutral";
    entry: number;
    stop_loss: number;
    target: number;
    confidence: number;
  }>;
  emaData: Record<number, (number | null)[]>;
  onLegendChange?: (value: LegendPoint | null) => void;
  height?: number;
}

const EMA_COLORS: Record<number, string> = {
  20: "#2196f3",
  50: "#ff9800",
  200: "#f44336",
};

export default function CandlestickChart({
  data,
  supportResistance,
  orderBlocks,
  patterns,
  emaData,
  onLegendChange,
  height = 520,
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [chart, setChart] = useState<IChartApi | null>(null);
  const [candleSeries, setCandleSeries] = useState<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const emaSeriesRef = useRef<Record<number, ISeriesApi<"Line">>>({});
  const supportLinesRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]>[]>([]);

  const formattedData = useMemo(
    () =>
      data.map((candle) => ({
        time: (candle.timestamp / 1000) as Time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      })),
    [data]
  );

  useEffect(() => {
    if (!containerRef.current || chart) return;

    const chartInstance = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#0a0e27" },
        textColor: "#d1d4dc",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.05)" },
        horzLines: { color: "rgba(255,255,255,0.05)" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderVisible: false },
      handleScroll: true,
      handleScale: true,
    });

    const candle = chartInstance.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    const volumeSeries = chartInstance.addHistogramSeries({
      color: "rgba(255,255,255,0.2)",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chartInstance.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    Object.entries(EMA_COLORS).forEach(([period, color]) => {
      const lineSeries = chartInstance.addLineSeries({
        color,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      emaSeriesRef.current[Number(period)] = lineSeries;
    });

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chartInstance.applyOptions({ width: entry.contentRect.width });
      }
    });

    resizeObserver.observe(containerRef.current);

    chartInstance.subscribeCrosshairMove((param) => {
      if (!onLegendChange) return;
      if (!param.time || !param.seriesData) {
        onLegendChange(null);
        return;
      }
      const candleData = param.seriesData.get(candle) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      const volumeData = param.seriesData.get(volumeSeries) as { value: number } | undefined;
      if (!candleData) return;
      onLegendChange({
        time: Number(param.time),
        open: candleData.open,
        high: candleData.high,
        low: candleData.low,
        close: candleData.close,
        volume: volumeData?.value ?? 0,
      });
    });

    setChart(chartInstance);
    setCandleSeries(candle);

    return () => {
      resizeObserver.disconnect();
      chartInstance.remove();
    };
  }, [chart, onLegendChange]);

  useEffect(() => {
    if (!candleSeries || !volumeSeriesRef.current) return;
    candleSeries.setData(formattedData);
    volumeSeriesRef.current.setData(
      data.map((candle) => ({
        time: (candle.timestamp / 1000) as Time,
        value: candle.volume,
        color: candle.close >= candle.open ? "rgba(38,166,154,0.6)" : "rgba(239,83,80,0.6)",
      }))
    );
  }, [formattedData, data, candleSeries]);

  useEffect(() => {
    if (!candleSeries) return;
    supportLinesRef.current.forEach((line) => candleSeries.removePriceLine(line));
    supportLinesRef.current = [];

    supportResistance.forEach((level) => {
      const line = candleSeries.createPriceLine({
        price: level.price,
        color: level.type === "support" ? "#2196f3" : "#f44336",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: level.label,
      });
      supportLinesRef.current.push(line);
    });
  }, [supportResistance, candleSeries]);

  useEffect(() => {
    Object.entries(emaSeriesRef.current).forEach(([period, series]) => {
      const values = emaData[Number(period)] || [];
      series.setData(
        values.map((value, index) => ({
          time: ((data[index]?.timestamp ?? 0) / 1000) as Time,
          value: value ?? data[index]?.close ?? 0,
        }))
      );
    });
  }, [emaData, data]);

  return (
    <div className="space-y-2">
      <div ref={containerRef} className="w-full" />
      {chart && candleSeries && (
        <ChartOverlays
          chart={chart}
          candleSeries={candleSeries}
          candles={data}
          orderBlocks={orderBlocks}
          patterns={patterns}
        />
      )}
    </div>
  );
}
