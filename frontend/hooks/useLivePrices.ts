"use client";

import { useMemo } from "react";
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
  { symbol: "USOIL.FOREX", label: "US OIL" },
];

/**
 * useLivePrices - Header price ticker using WebSocket only
 * Reads real-time data from WebSocketContext. No HTTP polling.
 */
export function useLivePrices(_refreshInterval?: number): {
  tickers: MarketTicker[];
  isLoading: boolean;
  lastUpdate: Date | null;
  refresh: () => void;
} {
  const { symbolData, lastUpdate, status } = useWSData();

  const tickers: MarketTicker[] = useMemo(() => {
    return SYMBOLS_CONFIG.map(({ symbol, label }) => {
      const wsData = symbolData[symbol];

      const ta = wsData?.data?.ta_snapshot;
      // Get current price from TA snapshot or directly from base data
      const currentPrice = ta?.current_price ?? wsData?.data?.current_price ?? null;

      // If we don't even have a current price, return placeholder
      if (!currentPrice || currentPrice <= 0) {
        return { label, price: "--", change: "--%", trend: "up" as const };
      }

      // Calculate % change from prev_close + live current_price.
      // This ensures the percentage updates in real-time as price_update ticks arrive,
      // rather than staying stale from the last full backend update.
      const prevClose = ta?.prev_close ?? ta?.last_close ?? null;
      const changePctBackend = ta?.change_pct ?? null;

      let changeValue = 0;
      let changePercent = 0;

      if (prevClose && prevClose > 0) {
        // Best path: recalculate from prev_close + live price
        changeValue = currentPrice - prevClose;
        changePercent = (changeValue / prevClose) * 100;
      } else if (changePctBackend !== null) {
        // Fallback: use backend-computed change_pct (won't update with ticks)
        changePercent = changePctBackend;
        changeValue = currentPrice * (changePercent / 100);
      } else {
        // We have price but no history: display price with 0% change
        return {
          label,
          price: currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
          change: "0.00%",
          trend: "up" as const,
        };
      }

      return {
        label,
        price: currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
        change: `${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(2)}%`,
        trend: changePercent >= 0 ? "up" : "down",
      };
    });
  }, [symbolData]);

  const isLoading = status !== "connected" || !lastUpdate;

  return { tickers, isLoading, lastUpdate, refresh: () => { } };
}
