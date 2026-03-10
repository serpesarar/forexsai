import { describe, expect, it } from "vitest";
import { buildCompressedChartCandles, buildMappedChartMarkers } from "../chart/newsCorrelationTimeline";

describe("newsCorrelationTimeline", () => {
  it("compresses irregular candle timestamps into evenly spaced render times", () => {
    const candles = buildCompressedChartCandles([
      { timestamp: 1710000000000, open: 10, high: 11, low: 9, close: 10.5, volume: 100 },
      { timestamp: 1710005400000, open: 10.5, high: 11.5, low: 10, close: 11, volume: 120 },
      { timestamp: 1710016200000, open: 11, high: 12, low: 10.8, close: 11.8, volume: 140 },
    ], "1h");

    expect(candles.map((candle) => candle.actualTimestamp)).toEqual([
      1710000000,
      1710005400,
      1710016200,
    ]);
    expect(candles.map((candle) => candle.time)).toEqual([
      1710000000,
      1710003600,
      1710007200,
    ]);
  });

  it("maps markers to the nearest compressed chart candle and drops out-of-range items", () => {
    const candles = buildCompressedChartCandles([
      { timestamp: 1710000000000, open: 10, high: 11, low: 9, close: 10.5, volume: 100 },
      { timestamp: 1710005400000, open: 10.5, high: 11.5, low: 10, close: 11, volume: 120 },
      { timestamp: 1710016200000, open: 11, high: 12, low: 10.8, close: 11.8, volume: 140 },
    ], "1h");

    const markers = buildMappedChartMarkers([
      {
        id: "m1",
        time: "2024-03-09T17:20:00Z",
        position: "aboveBar",
        color: "#fff",
        shape: "circle",
        size: 1,
        urgency: "breaking",
      },
      {
        id: "m2",
        time: "2024-03-09T10:00:00Z",
        position: "belowBar",
        color: "#aaa",
        shape: "square",
        size: 1,
        urgency: "low",
      },
    ], candles);

    expect(markers).toHaveLength(1);
    expect(markers[0]).toMatchObject({
      id: "m1",
      time: candles[1].time,
      text: "🚨",
    });
  });
});