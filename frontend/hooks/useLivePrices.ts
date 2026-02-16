"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { usePageVisibility } from "./usePageVisibility";

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
  { symbol: "GDAXI.INDX", label: "DAX" },
  { symbol: "CL.COMM", label: "US OIL" },
];

const previousCloseCache = new Map<string, { previousClose: number; fetchedAt: number }>();

function fetchWithTimeout(url: string, timeoutMs: number = 8000, externalSignal?: AbortSignal): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  // Abort on external signal too (e.g. component unmount)
  if (externalSignal) {
    externalSignal.addEventListener('abort', () => controller.abort());
  }
  return fetch(url, { cache: "no-store", signal: controller.signal }).finally(() => clearTimeout(id));
}

async function fetchPriceData(symbol: string, signal?: AbortSignal): Promise<{ price: number; previousClose: number } | null> {
  try {
    let currentPrice: number | null = null;
    let previousClose: number = 0;

    const cachedPrev = previousCloseCache.get(symbol);
    if (cachedPrev && Date.now() - cachedPrev.fetchedAt < 30 * 60 * 1000) {
      previousClose = cachedPrev.previousClose;
    }

    // Try cached endpoint first (lightweight - reads from DataHub memory)
    try {
      const cachedRes = await fetchWithTimeout(`${API_BASE}/api/data/cached/${encodeURIComponent(symbol)}`, 8000, signal);
      if (cachedRes.ok) {
        const cachedData = await cachedRes.json();
        currentPrice = cachedData?.data?.current_price
          ?? cachedData?.data?.ta_snapshot?.close
          ?? cachedData?.current_price
          ?? null;
      }
    } catch (e: any) {
      if (e?.name === 'AbortError') return null;
      console.warn(`Cached endpoint failed for ${symbol}:`, e);
    }

    // Only fetch OHLCV if we need previousClose (once per 30 min)
    if (!previousClose) {
      try {
        const ohlcvRes = await fetchWithTimeout(
          `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=1d&limit=3`,
          8000, signal
        );
        if (ohlcvRes.ok) {
          const ohlcvData = await ohlcvRes.json();
          const candles = ohlcvData?.data || [];
          if (candles.length >= 2) {
            previousClose = candles[candles.length - 2]?.close ?? 0;
            if (previousClose) previousCloseCache.set(symbol, { previousClose, fetchedAt: Date.now() });
            if (currentPrice === null) currentPrice = candles[candles.length - 1]?.close ?? null;
          } else if (candles.length === 1) {
            previousClose = candles[0]?.open ?? candles[0]?.close ?? 0;
            if (previousClose) previousCloseCache.set(symbol, { previousClose, fetchedAt: Date.now() });
            if (currentPrice === null) currentPrice = candles[0]?.close ?? null;
          }
        }
      } catch (e: any) {
        if (e?.name === 'AbortError') return null;
      }
    }

    if (currentPrice === null) return null;
    return { price: currentPrice, previousClose: previousClose || currentPrice };
  } catch (error: any) {
    if (error?.name === 'AbortError') return null;
    console.error(`Failed to fetch price for ${symbol}:`, error);
    return null;
  }
}

export function useLivePrices(refreshInterval: number = 30000): {
  prices: Map<string, LivePriceData>;
  tickers: MarketTicker[];
  isLoading: boolean;
  lastUpdate: Date | null;
  refresh: () => Promise<void>;
} {
  const [prices, setPrices] = useState<Map<string, LivePriceData>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    // Cancel any in-flight requests
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const newPrices = new Map<string, LivePriceData>();

    await Promise.all(
      SYMBOLS_CONFIG.map(async ({ symbol, label }) => {
        const data = await fetchPriceData(symbol, controller.signal);
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

    if (controller.signal.aborted) return;
    if (newPrices.size > 0) {
      setPrices(newPrices);
      setLastUpdate(new Date());
    }
    setIsLoading(false);
  }, []);

  const isTabVisible = usePageVisibility();

  // Initial fetch
  useEffect(() => {
    refresh();
    return () => { abortRef.current?.abort(); };
  }, [refresh]);

  // Periodic refresh - pauses when tab is hidden
  useEffect(() => {
    if (!isTabVisible) return;
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval, isTabVisible]);

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
