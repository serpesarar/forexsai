export interface NormalizableCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface NormalizeCandleOptions {
  fillSmallGaps?: boolean;
  maxSyntheticCandles?: number;
  syntheticWickRatio?: number;
}

const REMAINDER_GRANULARITY_MS = 60 * 1000;

const DEFAULT_OPTIONS: Required<NormalizeCandleOptions> = {
  fillSmallGaps: false,
  maxSyntheticCandles: 10,
  syntheticWickRatio: 0.0001,
};

export function getTimeframeMs(timeframe: string): number {
  const rawUnit = timeframe.slice(-1);
  const unit = rawUnit.toLowerCase();
  const value = Number.parseInt(timeframe.slice(0, -1), 10) || 1;

  if (rawUnit === "M") {
    return value * 30 * 24 * 60 * 60 * 1000;
  }

  switch (unit) {
    case "m":
      return value * 60 * 1000;
    case "h":
      return value * 60 * 60 * 1000;
    case "d":
      return value * 24 * 60 * 60 * 1000;
    case "w":
      return value * 7 * 24 * 60 * 60 * 1000;
    default:
      return 60 * 60 * 1000;
  }
}

export function toTimestampMs(timestamp: number): number {
  return timestamp > 1_000_000_000_000 ? Math.floor(timestamp) : Math.floor(timestamp * 1000);
}

function normalizeRemainderMs(timestampMs: number, timeframeMs: number): number {
  return ((timestampMs % timeframeMs) + timeframeMs) % timeframeMs;
}

function roundRemainderMs(remainderMs: number, timeframeMs: number): number {
  const rounded = Math.round(remainderMs / REMAINDER_GRANULARITY_MS) * REMAINDER_GRANULARITY_MS;
  return rounded >= timeframeMs ? 0 : rounded;
}

function sumVolumes(left?: number, right?: number): number | undefined {
  const safeLeft = Number.isFinite(left) ? left : undefined;
  const safeRight = Number.isFinite(right) ? right : undefined;

  if (safeLeft === undefined && safeRight === undefined) {
    return undefined;
  }

  return (safeLeft ?? 0) + (safeRight ?? 0);
}

function inferTimeframeOffsetMs<T extends NormalizableCandle>(candles: T[], timeframeMs: number): number {
  if (candles.length === 0) {
    return 0;
  }

  const nonZeroVolumeCandles = candles.filter((candle) => (candle.volume ?? 0) > 0);
  const source = nonZeroVolumeCandles.length > 0 ? nonZeroVolumeCandles : candles;
  const counts = new Map<number, number>();

  source.forEach((candle) => {
    const roundedRemainder = roundRemainderMs(normalizeRemainderMs(candle.timestamp, timeframeMs), timeframeMs);
    counts.set(roundedRemainder, (counts.get(roundedRemainder) ?? 0) + 1);
  });

  let bestOffset = roundRemainderMs(normalizeRemainderMs(source[0].timestamp, timeframeMs), timeframeMs);
  let bestCount = -1;

  counts.forEach((count, offset) => {
    if (count > bestCount || (count === bestCount && offset < bestOffset)) {
      bestOffset = offset;
      bestCount = count;
    }
  });

  return bestOffset;
}

function snapTimestampToTimeframe(timestampMs: number, timeframeMs: number, offsetMs: number): number {
  const remainder = normalizeRemainderMs(timestampMs - offsetMs, timeframeMs);
  return timestampMs - remainder;
}

export function normalizeCandles<T extends NormalizableCandle>(
  candles: T[],
  timeframe: string,
  options: NormalizeCandleOptions = {}
): T[] {
  if (!Array.isArray(candles) || candles.length === 0) {
    return [];
  }

  const config = { ...DEFAULT_OPTIONS, ...options };
  const timeframeMs = getTimeframeMs(timeframe);
  const deduped: T[] = [];
  const preparedCandles = [...candles]
    .filter((candle) => Number.isFinite(candle.timestamp))
    .map((candle) => ({ ...candle, timestamp: toTimestampMs(candle.timestamp) } as T))
    .sort((left, right) => left.timestamp - right.timestamp);
  const inferredOffsetMs = inferTimeframeOffsetMs(preparedCandles, timeframeMs);

  preparedCandles.forEach((candle) => {
      const snappedCandle = {
        ...candle,
        timestamp: snapTimestampToTimeframe(candle.timestamp, timeframeMs, inferredOffsetMs),
      } as T;

      if (deduped.length > 0 && deduped[deduped.length - 1].timestamp === snappedCandle.timestamp) {
        const previous = deduped[deduped.length - 1];
        deduped[deduped.length - 1] = {
          ...snappedCandle,
          open: previous.open,
          high: Math.max(previous.high, snappedCandle.high),
          low: Math.min(previous.low, snappedCandle.low),
          close: snappedCandle.close,
          volume: sumVolumes(previous.volume, snappedCandle.volume),
        } as T;
        return;
      }
      deduped.push(snappedCandle);
    });

  if (!config.fillSmallGaps || deduped.length < 2) {
    return deduped;
  }

  const filled: T[] = [deduped[0]];

  for (let index = 1; index < deduped.length; index += 1) {
    const previous = deduped[index - 1];
    const current = deduped[index];
    const gapMs = current.timestamp - previous.timestamp;
    const missingCandles = Math.round(gapMs / timeframeMs) - 1;

    if (gapMs > timeframeMs * 1.5 && missingCandles > 0 && missingCandles <= config.maxSyntheticCandles) {
      for (let fillIndex = 1; fillIndex <= missingCandles; fillIndex += 1) {
        const syntheticTimestamp = previous.timestamp + timeframeMs * fillIndex;
        if (syntheticTimestamp >= current.timestamp) {
          break;
        }

        const anchorPrice = previous.close;
        filled.push({
          ...previous,
          timestamp: syntheticTimestamp,
          open: anchorPrice,
          high: anchorPrice * (1 + config.syntheticWickRatio),
          low: anchorPrice * (1 - config.syntheticWickRatio),
          close: anchorPrice,
          volume: 0,
        } as T);
      }
    }

    filled.push(current);
  }

  return filled;
}