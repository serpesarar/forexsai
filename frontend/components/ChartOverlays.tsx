"use client";

import { useEffect, useRef } from "react";
import { IChartApi, ISeriesApi, Time } from "lightweight-charts";
import type { CandleData, OrderBlockResponse } from "./useChartData";

interface PatternOverlay {
  pattern_name: string;
  signal: "bullish" | "bearish" | "neutral";
  entry: number;
  stop_loss: number;
  target: number;
  confidence: number;
}

interface ChartOverlaysProps {
  chart: IChartApi;
  candleSeries: ISeriesApi<"Candlestick">;
  candles: CandleData[];
  orderBlocks?: OrderBlockResponse;
  patterns?: PatternOverlay[];
}

export default function ChartOverlays({ chart, candleSeries, candles, orderBlocks, patterns }: ChartOverlaysProps) {
  const overlaySeriesRef = useRef<ISeriesApi<"Baseline">[]>([]);

  useEffect(() => {
    overlaySeriesRef.current.forEach((series) => chart.removeSeries(series));
    overlaySeriesRef.current = [];

    const lastCandle = candles[candles.length - 1];
    if (!lastCandle) return;

    const markers: Parameters<ISeriesApi<"Candlestick">["setMarkers"]>[0] = [];

    orderBlocks?.order_blocks?.forEach((block) => {
      const start = candles[block.index]?.timestamp ?? candles[0]?.timestamp;
      const end = lastCandle.timestamp;
      if (!start) return;
      const series = chart.addBaselineSeries({
        baseValue: { type: "price", price: block.zone_low },
        topFillColor1: block.type === "bullish" ? "rgba(38,166,154,0.2)" : "rgba(239,83,80,0.2)",
        topFillColor2: block.type === "bullish" ? "rgba(38,166,154,0.2)" : "rgba(239,83,80,0.2)",
        bottomFillColor1: block.type === "bullish" ? "rgba(38,166,154,0.2)" : "rgba(239,83,80,0.2)",
        bottomFillColor2: block.type === "bullish" ? "rgba(38,166,154,0.2)" : "rgba(239,83,80,0.2)",
        lineWidth: 1,
        topLineColor: "transparent",
        bottomLineColor: "transparent",
        priceLineVisible: false,
        lastValueVisible: false,
      });
      series.setData([
        { time: (start / 1000) as Time, value: block.zone_high },
        { time: (end / 1000) as Time, value: block.zone_high },
      ]);
      overlaySeriesRef.current.push(series);

      markers.push({
        time: (start / 1000) as Time,
        position: "aboveBar",
        color: block.type === "bullish" ? "#26a69a" : "#ef5350",
        shape: "circle",
        text: `OB ${Math.round(block.score)}/100`,
      });
    });

    patterns?.forEach((pattern, index) => {
      const startIndex = Math.max(0, candles.length - 80 - index * 5);
      const start = candles[startIndex]?.timestamp;
      const end = lastCandle.timestamp;
      if (!start) return;
      const series = chart.addBaselineSeries({
        baseValue: { type: "price", price: pattern.stop_loss },
        topFillColor1: "rgba(255,167,38,0.15)",
        topFillColor2: "rgba(255,167,38,0.15)",
        bottomFillColor1: "rgba(255,167,38,0.15)",
        bottomFillColor2: "rgba(255,167,38,0.15)",
        lineWidth: 1,
        topLineColor: "#ffa726",
        bottomLineColor: "#ffa726",
        priceLineVisible: false,
        lastValueVisible: false,
      });
      series.setData([
        { time: (start / 1000) as Time, value: pattern.target },
        { time: (end / 1000) as Time, value: pattern.target },
      ]);
      overlaySeriesRef.current.push(series);

      markers.push({
        time: (end / 1000) as Time,
        position: "aboveBar",
        color: "#ffa726",
        shape: "arrowUp",
        text: `${pattern.pattern_name} (${Math.round(pattern.confidence * 100)}%)`,
      });
    });

    orderBlocks?.active_signals?.forEach((signal) => {
      if (!signal.has_signal) return;
      markers.push({
        time: (lastCandle.timestamp / 1000) as Time,
        position: signal.entry_type.toLowerCase().includes("buy") ? "belowBar" : "aboveBar",
        color: signal.entry_type.toLowerCase().includes("buy") ? "#26a69a" : "#ef5350",
        shape: signal.entry_type.toLowerCase().includes("buy") ? "arrowUp" : "arrowDown",
        text: `${signal.entry_type} @ ${signal.entry_price.toFixed(2)}`,
      });
    });

    candleSeries.setMarkers(markers);
  }, [chart, candleSeries, candles, orderBlocks, patterns]);

  return null;
}
