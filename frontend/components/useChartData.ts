"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetcher } from "../lib/api";
import type { ChartTimeframe } from "../lib/store";

export interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SupportResistanceLevel {
  type: "support" | "resistance";
  price: number;
  label: string;
}

export interface ChartDataResponse {
  symbol: string;
  timeframe: ChartTimeframe;
  data: CandleData[];
  support_resistance: SupportResistanceLevel[];
}

export interface OrderBlockZone {
  index: number;
  type: "bullish" | "bearish";
  zone_low: number;
  zone_high: number;
  score: number;
}

export interface OrderBlockResponse {
  order_blocks: OrderBlockZone[];
  active_signals: Array<{
    entry_type: string;
    entry_price: number;
    confidence: number;
    has_signal: boolean;
  }>;
}

export interface ClaudePatternResponse {
  analyses: Record<
    string,
    {
      detected_patterns: Array<{
        pattern_name: string;
        signal: "bullish" | "bearish" | "neutral";
        entry: number;
        stop_loss: number;
        target: number;
        confidence: number;
        reasoning: string;
      }>;
    }
  >;
}

const EMA_PERIODS = [20, 50, 200] as const;

function calculateEMA(values: number[], period: number): (number | null)[] {
  if (values.length === 0) return [];
  const k = 2 / (period + 1);
  const ema: (number | null)[] = [];
  let previous: number | null = null;
  values.forEach((value, index) => {
    if (index < period - 1) {
      ema.push(null);
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

function calculateRSI(values: number[], period = 14): (number | null)[] {
  if (values.length < period) return values.map(() => null);
  const rsi: (number | null)[] = [];
  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i += 1) {
    const change = values[i] - values[i - 1];
    if (change >= 0) gains += change;
    else losses -= change;
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;
  rsi.push(null);
  for (let i = 1; i < values.length; i += 1) {
    if (i < period) {
      rsi.push(null);
      continue;
    }
    const change = values[i] - values[i - 1];
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? -change : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    const rs = avgLoss === 0 ? 0 : avgGain / avgLoss;
    const value = avgLoss === 0 ? 100 : 100 - 100 / (1 + rs);
    rsi.push(value);
  }
  return rsi;
}

function calculateMACD(values: number[]) {
  const fast = calculateEMA(values, 12);
  const slow = calculateEMA(values, 26);
  const macdLine = values.map((_, idx) => {
    const fastValue = fast[idx];
    const slowValue = slow[idx];
    if (fastValue === null || slowValue === null) return null;
    return fastValue - slowValue;
  });
  const macdValues = macdLine.map((value) => value ?? 0);
  const signal = calculateEMA(macdValues, 9);
  const histogram = macdLine.map((value, idx) => {
    const signalValue = signal[idx];
    if (value === null || signalValue === null) return null;
    return value - signalValue;
  });
  return { macdLine, signal, histogram };
}

export function useChartData(symbol: string, timeframe: ChartTimeframe) {
  const ohlcvQuery = useQuery({
    queryKey: ["ohlcv", symbol, timeframe],
    queryFn: () =>
      fetcher<ChartDataResponse>(
        `/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=500`
      ),
    // IMPORTANT: avoid burning through EODHD quotas; charts don't need 5s polling.
    refetchInterval: 60000,
    refetchIntervalInBackground: true
  });

  const orderBlocksQuery = useQuery({
    queryKey: ["order-blocks", symbol, timeframe],
    queryFn: () =>
      fetcher<OrderBlockResponse>("/api/order-blocks/detect", {
        method: "POST",
        body: JSON.stringify({ symbol, timeframe, limit: 500 })
      }),
    refetchInterval: 15000,
    refetchIntervalInBackground: true
  });

  const claudePatternsQuery = useQuery({
    queryKey: ["claude-patterns", symbol, timeframe],
    queryFn: () =>
      fetcher<ClaudePatternResponse>("/api/claude/analyze-patterns", {
        method: "POST",
        body: JSON.stringify({ symbol, timeframes: [timeframe] })
      }),
    refetchInterval: 60000,
    refetchIntervalInBackground: true
  });

  const indicatorData = useMemo(() => {
    const candles = ohlcvQuery.data?.data ?? [];
    const closes = candles.map((candle) => candle.close);
    const ema = EMA_PERIODS.reduce((acc, period) => {
      acc[period] = calculateEMA(closes, period);
      return acc;
    }, {} as Record<number, (number | null)[]>);
    const rsi = calculateRSI(closes, 14);
    const macd = calculateMACD(closes);
    return { candles, ema, rsi, macd };
  }, [ohlcvQuery.data]);

  const latestValues = useMemo(() => {
    const candles = indicatorData.candles;
    const latest = candles[candles.length - 1];
    if (!latest) return null;
    const emaValues = EMA_PERIODS.reduce((acc, period) => {
      const value = indicatorData.ema[period][indicatorData.ema[period].length - 1];
      acc[period] = value ?? null;
      return acc;
    }, {} as Record<number, number | null>);
    const rsiValue = indicatorData.rsi[indicatorData.rsi.length - 1] ?? null;
    const macdValue = indicatorData.macd.macdLine[indicatorData.macd.macdLine.length - 1] ?? null;
    return { candle: latest, emaValues, rsi: rsiValue, macd: macdValue };
  }, [indicatorData]);

  return {
    ohlcvQuery,
    orderBlocksQuery,
    claudePatternsQuery,
    indicatorData,
    latestValues
  };
}
