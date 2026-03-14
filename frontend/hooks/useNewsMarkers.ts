/**
 * Hook: useNewsMarkers
 * Chart üzerinde haber markerlarını göstermek için
 */

import { useEffect, useState, useCallback } from 'react';
import { getApiBase } from '../lib/api/base';

export interface NewsMarker {
  id: string;
  time: string;
  position: 'aboveBar' | 'belowBar' | 'inBar';
  color: string;
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
  text: string;
  size: number;
  headline: string;
  headline_en: string;
  direction: 'bullish' | 'bearish' | 'neutral';
  score: number;
  urgency: 'breaking' | 'high' | 'medium' | 'low';
  catalyst_type?: 'news' | 'economic' | 'earnings';
  is_economic_event: boolean;
  is_earnings_event?: boolean;
  event_name?: string;
  event_id?: string | null;
  reasoning_tr?: string;
  importance_level?: string;
  importance_score?: number;
  importance_reason?: string;
  ai_confidence?: number;
  url: string;
}

interface UseNewsMarkersReturn {
  markers: NewsMarker[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const API_URL = getApiBase();

export function useNewsMarkers(
  symbol: string,
  hours: number = 24,
  minImpactScore: number = 5,
  maxMarkers: number = 60
): UseNewsMarkersReturn {
  const [markers, setMarkers] = useState<NewsMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMarkers = useCallback(async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/rss/chart-markers/${symbol}?hours=${hours}&min_impact_score=${minImpactScore}&max_markers=${maxMarkers}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setMarkers(data.markers);
      } else {
        setMarkers([]);
        throw new Error(data.error || 'Failed to fetch markers');
      }
    } catch (err) {
      console.error('[useNewsMarkers] Error:', err);
      setMarkers([]);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [symbol, hours, minImpactScore, maxMarkers]);

  useEffect(() => {
    fetchMarkers();

    // Her 5 dakikada bir güncelle
    const interval = setInterval(fetchMarkers, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [fetchMarkers]);

  return {
    markers,
    loading,
    error,
    refetch: fetchMarkers
  };
}

// Lightweight Charts için marker formatına dönüştür
export function convertToChartMarkers(markers: NewsMarker[]) {
  return markers.map(marker => ({
    time: Math.floor(new Date(marker.time).getTime() / 1000),
    position: marker.position,
    color: marker.color,
    shape: marker.shape,
    text: marker.catalyst_type === 'economic'
      ? '�'
      : marker.catalyst_type === 'earnings'
        ? '💰'
        : marker.urgency === 'breaking'
          ? '🚨'
          : '📰',
    size: marker.size,
    // Custom data for tooltip
    id: marker.id,
    headline: marker.headline,
    headline_en: marker.headline_en,
    direction: marker.direction,
    score: marker.score,
    urgency: marker.urgency,
    catalyst_type: marker.catalyst_type,
    is_economic_event: marker.is_economic_event,
    is_earnings_event: marker.is_earnings_event,
    event_name: marker.event_name,
    event_id: marker.event_id,
    reasoning_tr: marker.reasoning_tr,
    importance_level: marker.importance_level,
    importance_score: marker.importance_score,
    importance_reason: marker.importance_reason,
    ai_confidence: marker.ai_confidence,
    url: marker.url,
  }));
}
