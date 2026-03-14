import { getTimeframeMs, type NormalizableCandle } from "./normalizeCandles";

export interface TimelineChartCandle extends NormalizableCandle {
  time: number | string;
  actualTimestamp: number;
  priceChange: number;
}

interface BusinessDayLike {
  year: number;
  month: number;
  day: number;
}

function toTimelineChartCandle(candle: NormalizableCandle, time: number | string): TimelineChartCandle {
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
  catalyst_type?: "news" | "economic" | "earnings";
  is_economic_event?: boolean;
  is_earnings_event?: boolean;
  event_name?: string;
  event_id?: string | null;
  reasoning_tr?: string;
  importance_level?: string;
  importance_score?: number;
  importance_reason?: string;
  ai_confidence?: number;
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

export function buildActualTimeChartCandles(
  candles: NormalizableCandle[],
  timeframe?: string
): TimelineChartCandle[] {
  return candles.map((candle) => {
    const actualTimestamp = Math.floor(candle.timestamp / 1000);
    let time: number | string = actualTimestamp;
    
    // For daily, weekly, monthly timeframes, lightweight-charts requires a string like "2021-01-01"
    if (timeframe === "1d" || timeframe === "1w" || timeframe === "1M") {
      const date = new Date(candle.timestamp);
      const year = date.getUTCFullYear();
      const month = String(date.getUTCMonth() + 1).padStart(2, "0");
      const day = String(date.getUTCDate()).padStart(2, "0");
      time = `${year}-${month}-${day}`;
    }

    return toTimelineChartCandle(candle, time);
  });
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

function isBusinessDayLike(value: unknown): value is BusinessDayLike {
  return typeof value === "object"
    && value !== null
    && Number.isFinite((value as BusinessDayLike).year)
    && Number.isFinite((value as BusinessDayLike).month)
    && Number.isFinite((value as BusinessDayLike).day);
}

function toBusinessDayString(value: BusinessDayLike): string {
  return `${String(value.year).padStart(4, "0")}-${String(value.month).padStart(2, "0")}-${String(value.day).padStart(2, "0")}`;
}

function inferChartStepSeconds(candles: Array<Pick<TimelineChartCandle, "actualTimestamp">>): number {
  if (candles.length < 2) {
    return 0;
  }

  const counts = new Map<number, number>();

  for (let index = 1; index < candles.length; index += 1) {
    const diff = candles[index].actualTimestamp - candles[index - 1].actualTimestamp;
    if (Number.isFinite(diff) && diff > 0) {
      counts.set(diff, (counts.get(diff) ?? 0) + 1);
    }
  }

  let bestStep = 0;
  let bestCount = -1;
  counts.forEach((count, step) => {
    if (count > bestCount || (count === bestCount && step < bestStep)) {
      bestStep = step;
      bestCount = count;
    }
  });

  return bestStep;
}

function normalizeChartTimeValue(chartTime: number | string | BusinessDayLike): number | string {
  return isBusinessDayLike(chartTime) ? toBusinessDayString(chartTime) : chartTime;
}

export function mapActualTimestampToChartTime(
  actualTimestamp: number,
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
): number | string | null {
  if (!candles.length || !Number.isFinite(actualTimestamp)) {
    return null;
  }

  const firstTimestamp = candles[0].actualTimestamp;
  const lastTimestamp = candles[candles.length - 1].actualTimestamp;
  if (!Number.isFinite(firstTimestamp) || !Number.isFinite(lastTimestamp)) {
    return null;
  }

  const stepSeconds = inferChartStepSeconds(candles);
  const edgeToleranceSeconds = stepSeconds > 0 ? Math.max(60, stepSeconds) : 0;

  if (actualTimestamp < firstTimestamp) {
    return firstTimestamp - actualTimestamp <= edgeToleranceSeconds ? candles[0].time : null;
  }

  if (actualTimestamp > lastTimestamp) {
    return actualTimestamp - lastTimestamp <= edgeToleranceSeconds ? candles[candles.length - 1].time : null;
  }

  return candles.reduce((closest, candle) => {
    const currentDistance = Math.abs(candle.actualTimestamp - actualTimestamp);
    const closestDistance = Math.abs(closest.actualTimestamp - actualTimestamp);
    return currentDistance < closestDistance ? candle : closest;
  }).time;
}

export function chartTimeToTimestampSeconds(chartTime: number | string | BusinessDayLike): number | null {
  if (isBusinessDayLike(chartTime)) {
    return Math.floor(Date.UTC(chartTime.year, chartTime.month - 1, chartTime.day) / 1000);
  }

  if (typeof chartTime === "number") {
    if (!Number.isFinite(chartTime)) {
      return null;
    }
    return chartTime > 1_000_000_000_000 ? Math.floor(chartTime / 1000) : Math.floor(chartTime);
  }

  const parsed = new Date(chartTime).getTime();
  if (!Number.isFinite(parsed)) {
    return null;
  }

  return Math.floor(parsed / 1000);
}

export function findTimelineChartCandle<T extends Pick<TimelineChartCandle, "time" | "actualTimestamp">>(
  chartTime: number | string | BusinessDayLike,
  candles: T[]
): T | undefined {
  const normalizedChartTime = normalizeChartTimeValue(chartTime);
  return candles.find((candle) => candle.time === normalizedChartTime);
}

export function buildMappedChartMarkers(
  markers: TimelineMarkerInput[],
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
) {
  return markers.flatMap((marker) => {
    const actualTimestamp = chartTimeToTimestampSeconds(marker.time);
    if (!Number.isFinite(actualTimestamp)) {
      return [];
    }
    const mappedTime = mapActualTimestampToChartTime(actualTimestamp, candles);

    if (mappedTime === null) {
      return [];
    }

    return [{
      time: mappedTime,
      position: marker.position,
      color: marker.color,
      shape: marker.shape,
      text: marker.catalyst_type === "economic"
        ? "📊"
        : marker.catalyst_type === "earnings"
          ? "�"
          : marker.urgency === "breaking"
            ? "🚨"
            : "📰",
      size: marker.size,
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
    }];
  });
}

export const buildCompressedChartCandles = buildTimelineChartCandles;