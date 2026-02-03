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

const API_BASE = "https://upbeat-flow-production.up.railway.app";

const SYMBOLS_CONFIG = [
  { symbol: "NDX.INDX", label: "NASDAQ" },
  { symbol: "XAUUSD", label: "XAU/USD" },
];

const previousCloseCache = new Map<string, { previousClose: number; fetchedAt: number }>();

async function fetchPriceData(symbol: string): Promise<{ price: number; previousClose: number } | null> {
  try {
    let currentPrice: number | null = null;
    let previousClose: number = 0;

    const cachedPrev = previousCloseCache.get(symbol);
    if (cachedPrev && Date.now() - cachedPrev.fetchedAt < 30 * 60 * 1000) {
      previousClose = cachedPrev.previousClose;
    }

    // Try cached endpoint first
    try {
      const cachedRes = await fetch(`${API_BASE}/api/data/cached/${encodeURIComponent(symbol)}`, { cache: "no-store" });
      if (cachedRes.ok) {
        const cachedData = await cachedRes.json();
        // Handle both response formats
        currentPrice = cachedData?.data?.current_price 
          ?? cachedData?.data?.ta_snapshot?.close 
          ?? cachedData?.current_price 
          ?? null;
      }
    } catch (e) {
      console.warn(`Cached endpoint failed for ${symbol}:`, e);
    }

    // Fetch OHLCV data for previous close and fallback current price
    try {
      const ohlcvRes = await fetch(
        `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=1d&limit=50`,
        { cache: "no-store" }
      );
      
      if (ohlcvRes.ok) {
        const ohlcvData = await ohlcvRes.json();
        const candles = ohlcvData?.data || [];
        
        if (candles.length >= 2) {
          // Get previous day's close
          if (!previousClose) {
            previousClose = candles[candles.length - 2]?.close ?? 0;
            if (previousClose) {
              previousCloseCache.set(symbol, { previousClose, fetchedAt: Date.now() });
            }
          }
          // Use latest candle close if no cached price
          if (currentPrice === null) {
            currentPrice = candles[candles.length - 1]?.close ?? null;
          }
        } else if (candles.length === 1) {
          if (!previousClose) {
            previousClose = candles[0]?.open ?? candles[0]?.close ?? 0;
            if (previousClose) {
              previousCloseCache.set(symbol, { previousClose, fetchedAt: Date.now() });
            }
          }
          if (currentPrice === null) {
            currentPrice = candles[0]?.close ?? null;
          }
        }
      }
    } catch (e) {
      console.warn(`OHLCV endpoint failed for ${symbol}:`, e);
    }

    // Try prediction endpoint as last fallback
    if (currentPrice === null) {
      try {
        const predRes = await fetch(`${API_BASE}/api/prediction/${encodeURIComponent(symbol)}`, { cache: "no-store" });
        if (predRes.ok) {
          const predData = await predRes.json();
          currentPrice = predData?.entry_price ?? predData?.current_price ?? null;
          if (previousClose === 0 && currentPrice) {
            previousClose = currentPrice; // No change if we only have one price
          }
        }
      } catch (e) {
        console.warn(`Prediction endpoint failed for ${symbol}:`, e);
      }
    }

    if (currentPrice === null) return null;

    return { price: currentPrice, previousClose: previousClose || currentPrice };
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
