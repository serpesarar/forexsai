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

const DEFAULT_OPTIONS: Required<NormalizeCandleOptions> = {
  fillSmallGaps: true,
  maxSyntheticCandles: 10,
  syntheticWickRatio: 0.0001,
};

export function getTimeframeMs(timeframe: string): number {
  const unit = timeframe.slice(-1).toLowerCase();
  const value = Number.parseInt(timeframe.slice(0, -1), 10) || 1;

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

export function normalizeCandles<T extends NormalizableCandle>(
  candles: T[],
  timeframe: string,
  options: NormalizeCandleOptions = {}
): T[] {
  if (!Array.isArray(candles) || candles.length === 0) {
    return [];
  }

  const config = { ...DEFAULT_OPTIONS, ...options };
  const deduped: T[] = [];

  [...candles]
    .filter((candle) => Number.isFinite(candle.timestamp))
    .map((candle) => ({ ...candle, timestamp: toTimestampMs(candle.timestamp) } as T))
    .sort((left, right) => left.timestamp - right.timestamp)
    .forEach((candle) => {
      if (deduped.length > 0 && deduped[deduped.length - 1].timestamp === candle.timestamp) {
        deduped[deduped.length - 1] = candle;
        return;
      }
      deduped.push(candle);
    });

  if (!config.fillSmallGaps || deduped.length < 2) {
    return deduped;
  }

  const timeframeMs = getTimeframeMs(timeframe);
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