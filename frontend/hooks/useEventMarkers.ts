/**
 * Hook: useEventMarkers
 * Grafik olay işaretçileri — takvim + haber + makro spike + volatilite anomalisi.
 * /api/market-events/markers endpoint'ini kullanır; başarısız olursa eski
 * /api/rss/chart-markers endpoint'ine düşer (geriye dönük uyumluluk).
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getApiBase } from "../lib/api/base";
import type { EventMarker } from "../lib/api/marketEvents";

interface UseEventMarkersReturn {
  markers: EventMarker[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const API_URL = getApiBase();
const REFRESH_MS = 5 * 60 * 1000;

export function useEventMarkers(
  symbol: string,
  hours: number = 168,
  timeframe: string = "1h",
  maxMarkers: number = 80,
  enabled: boolean = true
): UseEventMarkersReturn {
  const [markers, setMarkers] = useState<EventMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Bayat-yanıt koruması: hızlı sembol/timeframe geçişinde eski isteğin
  // yanıtı yeni sembolün marker'larını ezmesin
  const requestIdRef = useRef(0);

  const fetchMarkers = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    if (!enabled || !symbol) {
      setMarkers([]);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const endpoints = [
      `${API_URL}/api/market-events/markers/${encodeURIComponent(symbol)}?hours=${hours}&timeframe=${encodeURIComponent(timeframe)}&max_markers=${maxMarkers}`,
      `${API_URL}/api/rss/chart-markers/${encodeURIComponent(symbol)}?hours=${hours}&min_impact_score=5&max_markers=${maxMarkers}`,
    ];

    let lastError: string | null = null;
    for (const url of endpoints) {
      try {
        const response = await fetch(url, { headers: { Accept: "application/json" } });
        if (requestId !== requestIdRef.current) return; // bayat istek — sonucu atla
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (requestId !== requestIdRef.current) return;
        if (data.success && Array.isArray(data.markers)) {
          setMarkers(data.markers);
          setLoading(false);
          return;
        }
        throw new Error(data.error || "Invalid marker payload");
      } catch (err) {
        lastError = err instanceof Error ? err.message : "Unknown error";
      }
    }

    if (requestId !== requestIdRef.current) return;
    console.error("[useEventMarkers] All endpoints failed:", lastError);
    setMarkers([]);
    setError(lastError);
    setLoading(false);
  }, [symbol, hours, timeframe, maxMarkers, enabled]);

  useEffect(() => {
    if (!enabled) {
      setMarkers([]);
      setError(null);
      setLoading(false);
      return;
    }

    fetchMarkers();
    const interval = setInterval(fetchMarkers, REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchMarkers, enabled]);

  return { markers, loading, error, refetch: fetchMarkers };
}
