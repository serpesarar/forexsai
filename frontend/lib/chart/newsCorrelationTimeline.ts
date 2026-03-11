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

export type TimelineRenderablePoint =
  | Omit<TimelineChartCandle, "timestamp" | "actualTimestamp" | "priceChange" | "volume">
  | { time: number };

function isWeekendGap(previousTimestampMs: number, currentTimestampMs: number): boolean {
  const previous = new Date(previousTimestampMs);
  const current = new Date(currentTimestampMs);
  const gapHours = (currentTimestampMs - previousTimestampMs) / (60 * 60 * 1000);
  return gapHours >= 36 || previous.getUTCDay() > current.getUTCDay();
}

function usesSessionGaps(symbol: string): boolean {
  return ["NDX", "DAX", "VIX"].includes(symbol.toUpperCase());
}

function shouldPreserveGap(symbol: string, previousTimestampMs: number, currentTimestampMs: number, timeframeMs: number): boolean {
  const gapMs = currentTimestampMs - previousTimestampMs;
  if (gapMs <= timeframeMs * 1.5) {
    return false;
  }
  if (isWeekendGap(previousTimestampMs, currentTimestampMs)) {
    return true;
  }
  if (!usesSessionGaps(symbol)) {
    return false;
  }
  return gapMs >= Math.max(timeframeMs * 4, 8 * 60 * 60 * 1000);
}

export function buildTimelineChartCandles(candles: NormalizableCandle[]): TimelineChartCandle[] {
  return candles.map((candle) => {
    const actualTimestamp = Math.floor(candle.timestamp / 1000);
    return {
      timestamp: candle.timestamp,
      time: actualTimestamp,
      actualTimestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume,
      priceChange: candle.open !== 0 ? ((candle.close - candle.open) / candle.open) * 100 : 0,
    };
  });
}

export function buildRenderableChartSeries(
  candles: TimelineChartCandle[],
  timeframe: string,
  symbol: string
): TimelineRenderablePoint[] {
  if (!candles.length) {
    return [];
  }

  const timeframeMs = getTimeframeMs(timeframe);
  const series: TimelineRenderablePoint[] = [];

  for (let index = 0; index < candles.length; index += 1) {
    const candle = candles[index];
    series.push({
      time: candle.time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    });

    const next = candles[index + 1];
    if (!next) {
      continue;
    }

    if (!shouldPreserveGap(symbol, candle.timestamp, next.timestamp, timeframeMs)) {
      continue;
    }

    const gapBars = Math.min(96, Math.max(0, Math.round((next.timestamp - candle.timestamp) / timeframeMs) - 1));
    for (let gapIndex = 1; gapIndex <= gapBars; gapIndex += 1) {
      series.push({ time: Math.floor((candle.timestamp + gapIndex * timeframeMs) / 1000) });
    }
  }

  return series;
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

export const buildCompressedChartCandles = buildTimelineChartCandles;