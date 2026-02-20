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
  { symbol: "CL.COMM", label: "US OIL" },
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

  // DEBUG: Log symbolData to see what's available
  console.log("[useLivePrices] symbolData keys:", Object.keys(symbolData));
  console.log("[useLivePrices] Full symbolData:", symbolData);

  const tickers: MarketTicker[] = useMemo(() => {
    return SYMBOLS_CONFIG.map(({ symbol, label }) => {
      const wsData = symbolData[symbol];
      
      // DEBUG: Detailed logging for each symbol
      console.log(`[useLivePrices] ${symbol} wsData:`, wsData);
      console.log(`[useLivePrices] ${symbol} wsData?.data:`, wsData?.data);
      console.log(`[useLivePrices] ${symbol} ta_snapshot:`, wsData?.data?.ta_snapshot);
      
      if (!wsData?.data?.ta_snapshot) {
        console.log(`[useLivePrices] ${symbol} NO ta_snapshot, returning --`);
        return { label, price: "--", change: "--%", trend: "up" as const };
      }

      const ta = wsData.data.ta_snapshot;
      const currentPrice = ta.current_price ?? wsData.data.current_price ?? null;
      const prevClose = ta.prev_close ?? ta.last_close ?? null;
      
      console.log(`[useLivePrices] ${symbol} currentPrice=${currentPrice}, prevClose=${prevClose}`);

      if (!currentPrice || !prevClose || currentPrice <= 0 || prevClose <= 0) {
        console.log(`[useLivePrices] ${symbol} INVALID prices, returning --`);
        return { label, price: "--", change: "--%", trend: "up" as const };
      }

      const change = currentPrice - prevClose;
      const changePercent = (change / prevClose) * 100;

      return {
        label,
        price: currentPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
        change: `${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(2)}%`,
        trend: change >= 0 ? "up" : "down",
      };
    });
  }, [symbolData]);

  const isLoading = status !== "connected" || !lastUpdate;

  return { tickers, isLoading, lastUpdate, refresh: () => {} };
}
