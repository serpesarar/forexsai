"use client";

import { useMemo, useState } from "react";
import { RefreshCw, Settings } from "lucide-react";
import CandlestickChart, { LegendPoint } from "./CandlestickChart";
import ChartControls from "./ChartControls";
import ChartLegend from "./ChartLegend";
import IndicatorChart from "./IndicatorChart";
import { useChartData } from "./useChartData";
import { useChartStore } from "../lib/store";

interface AdvancedChartProps {
  symbol: string;
}

export default function AdvancedChart({ symbol }: AdvancedChartProps) {
  const { timeframe, setTimeframe } = useChartStore();
  const [legend, setLegend] = useState<LegendPoint | null>(null);

  const { ohlcvQuery, orderBlocksQuery, claudePatternsQuery, indicatorData, latestValues } = useChartData(
    symbol,
    timeframe
  );

  const patterns = useMemo(() => {
    const analysis = claudePatternsQuery.data?.analyses?.[timeframe];
    return analysis?.detected_patterns ?? [];
  }, [claudePatternsQuery.data, timeframe]);

  return (
    <div className="glass-card p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-textSecondary">Advanced Charting</p>
          <h2 className="text-xl font-semibold">{symbol} Trading View</h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => ohlcvQuery.refetch()}
            className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition"
            aria-label="Refresh chart"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition" aria-label="Settings">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <ChartControls timeframe={timeframe} onTimeframeChange={setTimeframe} />
        <ChartLegend
          symbol={symbol}
          timeframe={timeframe}
          legend={legend}
          latestPrice={latestValues?.candle?.close ?? null}
          emaValues={latestValues?.emaValues}
          rsi={latestValues?.rsi}
          macd={latestValues?.macd}
        />
      </div>

      {ohlcvQuery.isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-64 w-full" />
          <div className="skeleton h-10 w-full" />
        </div>
      ) : ohlcvQuery.error ? (
        <div className="text-sm text-danger">Chart data could not be loaded. Please retry.</div>
      ) : (
        <CandlestickChart
          data={indicatorData.candles}
          supportResistance={ohlcvQuery.data?.support_resistance ?? []}
          orderBlocks={orderBlocksQuery.data}
          patterns={patterns}
          emaData={indicatorData.ema}
          onLegendChange={setLegend}
        />
      )}

      {ohlcvQuery.isLoading ? (
        <div className="skeleton h-52 w-full" />
      ) : (
        <IndicatorChart candles={indicatorData.candles} rsi={indicatorData.rsi} macd={indicatorData.macd} />
      )}

      {patterns.length > 0 && (
        <div className="text-xs text-textSecondary">
          Active patterns: {patterns.map((pattern) => pattern.pattern_name).join(", ")}
        </div>
      )}
    </div>
  );
}
