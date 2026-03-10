import { getTimeframeMs, type NormalizableCandle } from "./normalizeCandles";

export interface TimelineChartCandle extends NormalizableCandle {
  time: number;
  actualTimestamp: number;
  priceChange: number;
}

export interface TimelineMarkerInput {
  id: string;
  time: string;
  position: "aboveBar" | "belowBar" | "inBar";
  color: string;
  shape: "circle" | "square" | "arrowUp" | "arrowDown";
  size: number;
  headline?: string;
  headline_en?: string;
  direction?: string;
  score?: number;
  urgency?: string;
  is_economic_event?: boolean;
  event_name?: string;
  reasoning_tr?: string;
  url?: string;
}

export function buildCompressedChartCandles(
  candles: NormalizableCandle[],
  timeframe: string
): TimelineChartCandle[] {
  if (!candles.length) {
    return [];
  }

  const stepSeconds = Math.max(60, Math.floor(getTimeframeMs(timeframe) / 1000));
  const firstActualTimestamp = Math.floor(candles[0].timestamp / 1000);

  return candles.map((candle, index) => ({
    timestamp: candle.timestamp,
    time: firstActualTimestamp + index * stepSeconds,
    actualTimestamp: Math.floor(candle.timestamp / 1000),
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: candle.volume,
    priceChange: candle.open !== 0 ? ((candle.close - candle.open) / candle.open) * 100 : 0,
  }));
}

export function mapActualTimestampToChartTime(
  actualTimestamp: number,
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
): number | null {
  if (!candles.length || !Number.isFinite(actualTimestamp)) {
    return null;
  }

  const firstTimestamp = candles[0].actualTimestamp;
  const lastTimestamp = candles[candles.length - 1].actualTimestamp;
  if (actualTimestamp < firstTimestamp || actualTimestamp > lastTimestamp) {
    return null;
  }

  let closestCandle = candles[0];
  let closestDistance = Math.abs(candles[0].actualTimestamp - actualTimestamp);

  for (const candle of candles) {
    const distance = Math.abs(candle.actualTimestamp - actualTimestamp);
    if (distance < closestDistance) {
      closestCandle = candle;
      closestDistance = distance;
    }
  }

  return closestCandle.time;
}

export function buildMappedChartMarkers(
  markers: TimelineMarkerInput[],
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
) {
  return markers.flatMap((marker) => {
    const actualTimestamp = Math.floor(new Date(marker.time).getTime() / 1000);
    const mappedTime = mapActualTimestampToChartTime(actualTimestamp, candles);

    if (!Number.isFinite(mappedTime)) {
      return [];
    }

    return [{
      time: mappedTime,
      position: marker.position,
      color: marker.color,
      shape: marker.shape,
      text: marker.is_economic_event ? "📊" : marker.urgency === "breaking" ? "🚨" : "📰",
      size: marker.size,
      id: marker.id,
      headline: marker.headline,
      headline_en: marker.headline_en,
      direction: marker.direction,
      score: marker.score,
      urgency: marker.urgency,
      is_economic_event: marker.is_economic_event,
      event_name: marker.event_name,
      reasoning_tr: marker.reasoning_tr,
      url: marker.url,
    }];
  });
}