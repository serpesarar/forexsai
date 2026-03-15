import { getTimeframeMs, type NormalizableCandle } from "./normalizeCandles";

export interface TimelineChartCandle extends NormalizableCandle {
  time: number | string;
  actualTimestamp: number;
  priceChange: number;
  displayIndex: number;
}

interface BusinessDayLike {
  year: number;
  month: number;
  day: number;
}

export interface TimelineMarkerInput {
  id: string;
  time: string | number;
  position: "aboveBar" | "belowBar" | "inBar";
  color: string;
  shape: "circle" | "square" | "arrowUp" | "arrowDown";
  size: number;
  text?: string;
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
  source_time?: string;
  url?: string;
}

export type TimelineRenderablePoint = Pick<TimelineChartCandle, "time" | "open" | "high" | "low" | "close">;

export interface TimelineMappedMarker {
  time: number | string;
  position: "aboveBar" | "belowBar" | "inBar";
  color: string;
  shape: "circle" | "square" | "arrowUp" | "arrowDown";
  text?: string;
  size: number;
  id: string;
  actualTimestamp: number;
  source_time: string;
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

const DISPLAY_TIME_ORIGIN_SECONDS = 946684800;
const URGENCY_WEIGHT: Record<string, number> = {
  breaking: 4,
  high: 3,
  medium: 2,
  low: 1,
};

function toTimelineChartCandle(candle: NormalizableCandle, time: number | string, displayIndex: number): TimelineChartCandle {
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
    displayIndex,
  };
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

function normalizeChartTimeValue(chartTime: number | string | BusinessDayLike): number | string {
  return isBusinessDayLike(chartTime) ? toBusinessDayString(chartTime) : chartTime;
}

function chartTimeToKey(chartTime: number | string | BusinessDayLike): string {
  const normalizedValue = normalizeChartTimeValue(chartTime);
  return typeof normalizedValue === "number" ? `n:${normalizedValue}` : `s:${normalizedValue}`;
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

function resolveActualTimestampToCandle<T extends Pick<TimelineChartCandle, "time" | "actualTimestamp">>(
  actualTimestamp: number,
  candles: T[]
): T | null {
  if (!candles.length || !Number.isFinite(actualTimestamp)) {
    return null;
  }

  const firstTimestamp = candles[0].actualTimestamp;
  const lastTimestamp = candles[candles.length - 1].actualTimestamp;
  if (!Number.isFinite(firstTimestamp) || !Number.isFinite(lastTimestamp)) {
    return null;
  }

  const stepSeconds = inferChartStepSeconds(candles);
  const edgeToleranceSeconds = stepSeconds > 0
    ? Math.max(60, Math.min(48 * 60 * 60, stepSeconds * 48))
    : 0;

  if (actualTimestamp < firstTimestamp) {
    return firstTimestamp - actualTimestamp <= edgeToleranceSeconds ? candles[0] : null;
  }

  if (stepSeconds <= 0) {
    return candles.reduce((closest, candle) => {
      const currentDistance = Math.abs(candle.actualTimestamp - actualTimestamp);
      const closestDistance = Math.abs(closest.actualTimestamp - actualTimestamp);
      return currentDistance < closestDistance ? candle : closest;
    });
  }

  for (let index = 0; index < candles.length; index += 1) {
    const candle = candles[index];
    const nextCandle = candles[index + 1];
    const candleEnd = candle.actualTimestamp + stepSeconds;

    if (actualTimestamp >= candle.actualTimestamp && actualTimestamp < candleEnd) {
      return candle;
    }

    if (nextCandle && actualTimestamp >= candleEnd && actualTimestamp < nextCandle.actualTimestamp) {
      const distanceToCurrent = actualTimestamp - candleEnd;
      const distanceToNext = nextCandle.actualTimestamp - actualTimestamp;
      return distanceToNext < distanceToCurrent ? nextCandle : candle;
    }
  }

  if (actualTimestamp >= lastTimestamp && actualTimestamp < lastTimestamp + stepSeconds) {
    return candles[candles.length - 1];
  }

  if (actualTimestamp > lastTimestamp) {
    return actualTimestamp - lastTimestamp <= edgeToleranceSeconds ? candles[candles.length - 1] : null;
  }

  return candles.reduce((closest, candle) => {
    const currentDistance = Math.abs(candle.actualTimestamp - actualTimestamp);
    const closestDistance = Math.abs(closest.actualTimestamp - actualTimestamp);
    return currentDistance < closestDistance ? candle : closest;
  });
}

export function buildTimelineChartCandles(candles: NormalizableCandle[], timeframe: string): TimelineChartCandle[] {
  if (!candles.length) {
    return [];
  }

  const stepSeconds = Math.max(60, Math.floor(getTimeframeMs(timeframe) / 1000));

  return candles.map((candle, index) => toTimelineChartCandle(
    candle,
    DISPLAY_TIME_ORIGIN_SECONDS + index * stepSeconds,
    index
  ));
}

export function buildActualTimeChartCandles(
  candles: NormalizableCandle[],
  timeframe?: string
): TimelineChartCandle[] {
  return candles.map((candle, index) => {
    const actualTimestamp = Math.floor(candle.timestamp / 1000);
    let time: number | string = actualTimestamp;

    if (timeframe === "1d" || timeframe === "1w" || timeframe === "1M") {
      const date = new Date(candle.timestamp);
      const year = date.getUTCFullYear();
      const month = String(date.getUTCMonth() + 1).padStart(2, "0");
      const day = String(date.getUTCDate()).padStart(2, "0");
      time = `${year}-${month}-${day}`;
    }

    return toTimelineChartCandle(candle, time, index);
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

export function mapActualTimestampToChartTime(
  actualTimestamp: number,
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
): number | string | null {
  const candle = resolveActualTimestampToCandle(actualTimestamp, candles);
  return candle?.time ?? null;
}

export function findTimelineChartCandle<T extends Pick<TimelineChartCandle, "time" | "actualTimestamp">>(
  chartTime: number | string | BusinessDayLike,
  candles: T[]
): T | undefined {
  const targetKey = chartTimeToKey(chartTime);
  return candles.find((candle) => chartTimeToKey(candle.time) === targetKey);
}

export function resolveTimelineChartCandle<T extends Pick<TimelineChartCandle, "time" | "actualTimestamp">>(
  chartTime: number | string | BusinessDayLike,
  candles: T[]
): T | undefined {
  const exactMatch = findTimelineChartCandle(chartTime, candles);
  if (exactMatch) {
    return exactMatch;
  }

  const normalizedValue = normalizeChartTimeValue(chartTime);
  if (typeof normalizedValue === "number") {
    const numericCandles = candles.filter((candle) => typeof candle.time === "number");
    if (numericCandles.length) {
      return numericCandles.reduce((closest, candle) => {
        const currentDistance = Math.abs(Number(candle.time) - normalizedValue);
        const closestDistance = Math.abs(Number(closest.time) - normalizedValue);
        return currentDistance < closestDistance ? candle : closest;
      });
    }
  }

  const actualTimestamp = chartTimeToTimestampSeconds(chartTime);
  if (Number.isFinite(actualTimestamp)) {
    return resolveActualTimestampToCandle(Number(actualTimestamp), candles) ?? undefined;
  }

  return undefined;
}

export function resolveTimelineActualTimestamp(
  chartTime: number | string | BusinessDayLike,
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
): number | null {
  const candle = resolveTimelineChartCandle(chartTime, candles);
  if (candle) {
    return candle.actualTimestamp;
  }

  return chartTimeToTimestampSeconds(chartTime);
}

export function buildMappedChartMarkers(
  markers: TimelineMarkerInput[],
  candles: Array<Pick<TimelineChartCandle, "time" | "actualTimestamp">>
): TimelineMappedMarker[] {
  return markers.flatMap((marker) => {
    const actualTimestamp = chartTimeToTimestampSeconds(marker.time);
    if (!Number.isFinite(actualTimestamp)) {
      return [];
    }

    const mappedCandle = resolveActualTimestampToCandle(Number(actualTimestamp), candles);
    if (!mappedCandle) {
      return [];
    }

    return [{
      time: mappedCandle.time,
      position: marker.position,
      color: marker.color,
      shape: marker.shape,
      text: marker.text || (marker.catalyst_type === "economic"
        ? "📅"
        : marker.catalyst_type === "earnings"
          ? "💼"
          : marker.urgency === "breaking"
            ? "🚨"
            : "📰"),
      size: marker.size,
      id: marker.id,
      actualTimestamp: Number(actualTimestamp),
      source_time: typeof marker.time === "string" ? marker.time : String(marker.time),
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

export function buildRenderableChartMarkers(markers: TimelineMappedMarker[]): TimelineMappedMarker[] {
  const grouped = new Map<string, TimelineMappedMarker[]>();

  markers.forEach((marker) => {
    const key = `${chartTimeToKey(marker.time)}:${marker.position}`;
    const group = grouped.get(key);
    if (group) {
      group.push(marker);
      return;
    }
    grouped.set(key, [marker]);
  });

  return Array.from(grouped.values()).map((group) => {
    const topMarker = [...group].sort((left, right) => {
      const urgencyDelta = (URGENCY_WEIGHT[right.urgency || ""] ?? 0) - (URGENCY_WEIGHT[left.urgency || ""] ?? 0);
      if (urgencyDelta !== 0) {
        return urgencyDelta;
      }

      const scoreDelta = (right.score ?? 0) - (left.score ?? 0);
      if (scoreDelta !== 0) {
        return scoreDelta;
      }

      return left.actualTimestamp - right.actualTimestamp;
    })[0];

    return {
      ...topMarker,
      text: group.length > 1 ? `${topMarker.text || "📰"}${group.length}` : topMarker.text,
    };
  });
}

export const buildCompressedChartCandles = buildTimelineChartCandles;