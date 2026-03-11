import { describe, expect, it } from "vitest";
import { getTimeframeMs, normalizeCandles, toTimestampMs } from "../chart/normalizeCandles";

describe("normalizeCandles", () => {
  const alignedHourBaseMs = 1_800_000_000_000;

  it("normalizes second timestamps to milliseconds and sorts candles", () => {
    const candles = normalizeCandles(
      [
        { timestamp: 1710003600, open: 11, high: 12, low: 10, close: 11.5, volume: 20 },
        { timestamp: 1710000000, open: 10, high: 11, low: 9, close: 10.5, volume: 10 },
      ],
      "1h"
    );

    expect(candles.map((candle) => candle.timestamp)).toEqual([
      toTimestampMs(1710000000),
      toTimestampMs(1710003600),
    ]);
  });

  it("deduplicates equal timestamps without filling gaps by default", () => {
    const candles = normalizeCandles(
      [
        { timestamp: 1710000000000, open: 10, high: 11, low: 9, close: 10.5, volume: 10 },
        { timestamp: 1710000000000, open: 10.2, high: 11.2, low: 9.2, close: 10.8, volume: 12 },
        { timestamp: 1710007200000, open: 12, high: 13, low: 11, close: 12.5, volume: 20 },
      ],
      "1h"
    );

    expect(candles).toHaveLength(2);
    expect(candles[0].close).toBe(10.8);
    expect(candles[1]).toMatchObject({
      timestamp: 1710007200000,
      open: 12,
      close: 12.5,
    });
  });

  it("snaps drifted timestamps into dominant timeframe buckets and merges same-bucket candles", () => {
    const candles = normalizeCandles(
      [
        { timestamp: alignedHourBaseMs + 1_800_000, open: 10, high: 11, low: 9, close: 10.5, volume: 5 },
        { timestamp: alignedHourBaseMs + 3_152_000, open: 10.6, high: 12, low: 10.2, close: 11.8, volume: 7 },
        { timestamp: alignedHourBaseMs + 5_400_000, open: 11.8, high: 12.5, low: 11.4, close: 12.2, volume: 9 },
      ],
      "1h"
    );

    expect(candles).toHaveLength(2);
    expect(candles[0]).toMatchObject({
      timestamp: alignedHourBaseMs + 1_800_000,
      open: 10,
      high: 12,
      low: 9,
      close: 11.8,
      volume: 12,
    });
    expect(candles[1]).toMatchObject({
      timestamp: alignedHourBaseMs + 5_400_000,
      open: 11.8,
      close: 12.2,
      volume: 9,
    });
  });

  it("prefers non-zero-volume candles when inferring the timeframe offset", () => {
    const candles = normalizeCandles(
      [
        { timestamp: alignedHourBaseMs + 1_800_000, open: 10, high: 11, low: 9, close: 10.5, volume: 8 },
        { timestamp: alignedHourBaseMs + 3_600_000, open: 10.5, high: 10.5, low: 10.5, close: 10.5, volume: 0 },
        { timestamp: alignedHourBaseMs + 7_200_000, open: 10.7, high: 10.7, low: 10.7, close: 10.7, volume: 0 },
      ],
      "1h"
    );

    expect(candles.map((candle) => candle.timestamp)).toEqual([
      alignedHourBaseMs + 1_800_000,
      alignedHourBaseMs + 5_400_000,
    ]);
  });

  it("fills small gaps only when explicitly enabled", () => {
    const candles = normalizeCandles(
      [
        { timestamp: 1710000000000, open: 10, high: 11, low: 9, close: 10.5, volume: 10 },
        { timestamp: 1710007200000, open: 12, high: 13, low: 11, close: 12.5, volume: 20 },
      ],
      "1h",
      { fillSmallGaps: true }
    );

    expect(candles).toHaveLength(3);
    expect(candles[1]).toMatchObject({
      timestamp: 1710003600000,
      open: 10.5,
      close: 10.5,
      volume: 0,
    });
  });

  it("does not fill very large gaps such as weekend-scale jumps", () => {
    const candles = normalizeCandles(
      [
        { timestamp: 1710000000000, open: 10, high: 11, low: 9, close: 10.5, volume: 10 },
        { timestamp: 1710090000000, open: 12, high: 13, low: 11, close: 12.5, volume: 20 },
      ],
      "1h",
      { fillSmallGaps: true }
    );

    expect(candles).toHaveLength(2);
  });

  it("treats uppercase month timeframes distinctly from minutes", () => {
    expect(getTimeframeMs("1M")).toBe(30 * 24 * 60 * 60 * 1000);
    expect(getTimeframeMs("1m")).toBe(60 * 1000);
  });
});