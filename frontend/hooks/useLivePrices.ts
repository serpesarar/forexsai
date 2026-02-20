"use client";

import { useState, useEffect, useMemo } from "react";
import { useWSData } from "../contexts/WebSocketContext";

interface LivePriceData {
  symbol: string;
  label: string;
  price: number;
  previousClose: number;
  change: number;
  changePercent: number;
  trend: "up" | "down";
  lastUpdate: Date;
}

interface MarketTicker {
  label: string;
  price: string;
  change: string;
  trend: "up" | "down";
}

const SYMBOLS_CONFIG = [
  { symbol: "NDX.INDX", label: "NASDAQ" },
  { symbol: "XAUUSD", label: "XAU/USD" },
  { symbol: "GDAXI.INDX", label: "DAX" },
  { symbol: "CL.COMM", label: "US OIL" },
];

/**
 * useLivePrices - Real-time price ticker using WebSocket
 * 
 * Uses WebSocket data from backend instead of HTTP polling.
 * Backend broadcasts every 60 seconds via /ws/all endpoint.
 * 
 * % Change calculation: (current_price - previous_close) / previous_close * 100
 * This matches TradingView's real-time intraday change formula.
 */

export function useLivePrices(_refreshInterval?: number): {
  prices: Map<string, LivePriceData>;
  tickers: MarketTicker[];
  isLoading: boolean;
  lastUpdate: Date | null;
  refresh: () => void;
} {
  const { symbolData, lastUpdate: wsLastUpdate } = useWSData();
  const [isLoading, setIsLoading] = useState(true);

  // Process WebSocket data into price map
  const prices = useMemo(() => {
    const priceMap = new Map<string, LivePriceData>();

    for (const { symbol, label } of SYMBOLS_CONFIG) {
      const wsData = symbolData[symbol];
      if (!wsData?.data) continue;

      const ta = wsData.data.ta_snapshot;
      if (!ta) continue;

      // Extract current price - prefer live current_price, fallback to ta data
      const currentPrice = ta.current_price ?? wsData.data.current_price ?? null;
      if (!currentPrice || currentPrice <= 0) continue;

      // Get previous close for % change calculation
      const prevClose = ta.prev_close ?? ta.last_close ?? null;
      if (!prevClose || prevClose <= 0) continue;

      // Calculate change (TradingView formula: current vs previous close)
      const change = currentPrice - prevClose;
      const changePercent = (change / prevClose) * 100;

      priceMap.set(symbol, {
        symbol,
        label,
        price: currentPrice,
        previousClose: prevClose,
        change,
        changePercent,
        trend: change >= 0 ? "up" : "down",
        lastUpdate: wsLastUpdate ? new Date(wsLastUpdate) : new Date(),
      });
    }

    return priceMap;
  }, [symbolData, wsLastUpdate]);

  // Loading state - false once we have at least one price
  useEffect(() => {
    if (prices.size > 0) {
      setIsLoading(false);
    }
  }, [prices]);

  // Convert to MarketTicker format for header display
  const tickers: MarketTicker[] = useMemo(() => {
    return SYMBOLS_CONFIG.map(({ symbol, label }) => {
      const data = prices.get(symbol);
      if (!data) {
        return {
          label,
          price: "--",
          change: "--%",
          trend: "up" as const,
        };
      }

      return {
        label,
        price: data.price.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }),
        change: `${data.changePercent >= 0 ? "+" : ""}${data.changePercent.toFixed(2)}%`,
        trend: data.trend,
      };
    });
  }, [prices]);

  // Refresh is no-op for WebSocket - data flows automatically
  const refresh = () => {
    // WebSocket data flows automatically from backend
  };

  return {
    prices,
    tickers,
    isLoading,
    lastUpdate: wsLastUpdate,
    refresh,
  };
}
