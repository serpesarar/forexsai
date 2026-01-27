"use client";

import { useState, useEffect, useCallback } from "react";

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SYMBOLS_CONFIG = [
  { symbol: "NDX.INDX", label: "NASDAQ" },
  { symbol: "XAUUSD", label: "XAU/USD" },
];

async function fetchPriceData(symbol: string): Promise<{ price: number; previousClose: number } | null> {
  try {
    // Fetch current price from cached endpoint
    const cachedRes = await fetch(`${API_BASE}/api/data/cached/${encodeURIComponent(symbol)}`);
    let currentPrice: number | null = null;
    
    if (cachedRes.ok) {
      const cachedData = await cachedRes.json();
      currentPrice = cachedData?.data?.current_price ?? null;
    }

    // Fetch previous close from OHLCV data
    const ohlcvRes = await fetch(
      `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=1d&limit=2`
    );
    
    let previousClose = currentPrice ?? 0;
    
    if (ohlcvRes.ok) {
      const ohlcvData = await ohlcvRes.json();
      const candles = ohlcvData?.data || [];
      
      if (candles.length >= 2) {
        // Get previous day's close
        previousClose = candles[candles.length - 2]?.close ?? previousClose;
      } else if (candles.length === 1) {
        // Use open as previous close if only one candle
        previousClose = candles[0]?.open ?? previousClose;
      }
      
      // If no cached price, use latest candle close
      if (currentPrice === null && candles.length > 0) {
        currentPrice = candles[candles.length - 1]?.close ?? 0;
      }
    }

    if (currentPrice === null) return null;

    return { price: currentPrice, previousClose };
  } catch (error) {
    console.error(`Failed to fetch price for ${symbol}:`, error);
    return null;
  }
}

export function useLivePrices(refreshInterval: number = 3000): {
  prices: Map<string, LivePriceData>;
  tickers: MarketTicker[];
  isLoading: boolean;
  lastUpdate: Date | null;
  refresh: () => Promise<void>;
} {
  const [prices, setPrices] = useState<Map<string, LivePriceData>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    const newPrices = new Map<string, LivePriceData>();

    await Promise.all(
      SYMBOLS_CONFIG.map(async ({ symbol, label }) => {
        const data = await fetchPriceData(symbol);
        if (data) {
          const change = data.price - data.previousClose;
          const changePercent = data.previousClose > 0 
            ? (change / data.previousClose) * 100 
            : 0;

          newPrices.set(symbol, {
            symbol,
            label,
            price: data.price,
            previousClose: data.previousClose,
            change,
            changePercent,
            trend: change >= 0 ? "up" : "down",
            lastUpdate: new Date(),
          });
        }
      })
    );

    if (newPrices.size > 0) {
      setPrices(newPrices);
      setLastUpdate(new Date());
    }
    setIsLoading(false);
  }, []);

  // Initial fetch
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Periodic refresh
  useEffect(() => {
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  // Convert to MarketTicker format for header
  const tickers: MarketTicker[] = SYMBOLS_CONFIG.map(({ symbol, label }) => {
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
        maximumFractionDigits: 2 
      }),
      change: `${data.changePercent >= 0 ? "+" : ""}${data.changePercent.toFixed(2)}%`,
      trend: data.trend,
    };
  });

  return { prices, tickers, isLoading, lastUpdate, refresh };
}
