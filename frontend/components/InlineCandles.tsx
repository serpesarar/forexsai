"use client";

import { useMemo } from "react";
import { useChartData } from "./useChartData";
import CandlestickChart from "./CandlestickChart";
import type { ChartTimeframe } from "../lib/store";

export default function InlineCandles({
  symbol,
  timeframe = "1d",
  height = 300,
}: {
  symbol: string;
  timeframe?: ChartTimeframe;
  height?: number;
}) {
  const { ohlcvQuery, indicatorData } = useChartData(symbol, timeframe);

  const supportResistance = useMemo(() => ohlcvQuery.data?.support_resistance ?? [], [ohlcvQuery.data]);

  if (ohlcvQuery.isLoading) {
    return <div className="skeleton h-[300px] w-full" />;
  }

  if (ohlcvQuery.error) {
    return <div className="text-xs text-danger">Chart data could not be loaded.</div>;
  }

  if (!indicatorData.candles.length) {
    return <div className="text-xs text-textSecondary">No candle data available (data source quota/limit).</div>;
  }

  return (
    <CandlestickChart
      data={indicatorData.candles}
      supportResistance={supportResistance}
      emaData={indicatorData.ema}
      height={height}
    />
  );
}



