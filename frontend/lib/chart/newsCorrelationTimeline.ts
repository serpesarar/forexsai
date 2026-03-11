import { getTimeframeMs, type NormalizableCandle } from "./normalizeCandles";

export interface TimelineChartCandle extends NormalizableCandle {
  time: number;
  actualTimestamp: number;
  priceChange: number;
}

function toTimelineChartCandle(candle: NormalizableCandle, time: number): TimelineChartCandle {
  return {
    timestamp: candle.timestamp,
    time,
    actualTimestamp: Math.floor(candle.timestamp / 1000),
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: candle.volume,
    priceChange: candle.open !== 0 ? ((candle.close - candle.open) / candle.open) * 100 : 0,
  };
}

export interface TimelineMarkerInput {
  id: string;
  time: string | number;
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

export type TimelineRenderablePoint =
  Omit<TimelineChartCandle, "timestamp" | "actualTimestamp" | "priceChange" | "volume">;

export function buildTimelineChartCandles(candles: NormalizableCandle[], timeframe: string): TimelineChartCandle[] {
  if (!candles.length) {
    return [];
  }

  const stepSeconds = Math.max(60, Math.floor(getTimeframeMs(timeframe) / 1000));
  const firstActualTimestamp = Math.floor(candles[0].timestamp / 1000);

  return candles.map((candle, index) => toTimelineChartCandle(candle, firstActualTimestamp + index * stepSeconds));
}

export function buildActualTimeChartCandles(candles: NormalizableCandle[]): TimelineChartCandle[] {
  return candles.map((candle) => toTimelineChartCandle(candle, Math.floor(candle.timestamp / 1000)));
}

export function buildRenderableChartSeries(
  candles: TimelineChartCandle[],
  _timeframe: string,
  _symbol: string
): TimelineRenderablePoint[] {
  return candles.map((candle) => ({
    time: candle.time,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
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

  return candles.reduce((closest, candle) => {
    const currentDistance = Math.abs(candle.actualTimestamp - actualTimestamp);
    const closestDistance = Math.abs(closest.actualTimestamp - actualTimestamp);
    return currentDistance < closestDistance ? candle : closest;
  }).time;
}

export function findTimelineChartCandle<T extends Pick<TimelineChartCandle, "time" | "actualTimestamp">>(
  chartTime: number,
  candles: T[]
): T | undefined {
  return candles.find((candle) => candle.time === chartTime);
}

function toActualTimestampSeconds(timestamp: string | number): number | null {
  if (typeof timestamp === "number") {
    if (!Number.isFinite(timestamp)) {
      return null;
    }
    return timestamp > 1_000_000_000_000 ? Math.floor(timestamp / 1000) : Math.floor(timestamp);
  }

  const parsed = new Date(timestamp).getTime();
  if (!Number.isFinite(parsed)) {
    return null;
  }

  return Math.floor(parsed / 1000);
}

export function buildMappedChartMarkers(
  markers: TimelineMarkerInput[],
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
) {
  return markers.flatMap((marker) => {
    const actualTimestamp = toActualTimestampSeconds(marker.time);
    if (!Number.isFinite(actualTimestamp)) {
      return [];
    }
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

export const buildCompressedChartCandles = buildTimelineChartCandles;