import { describe, expect, it } from "vitest";

import {
  buildMappedChartMarkers,
  buildRenderableChartSeries,
  buildTimelineChartCandles,
  mapActualTimestampToChartTime,
} from "../chart/newsCorrelationTimeline";

const candles = buildTimelineChartCandles([
  { timestamp: Date.UTC(2026, 2, 6, 20, 0), open: 100, high: 102, low: 99, close: 101 },
  { timestamp: Date.UTC(2026, 2, 6, 21, 0), open: 101, high: 103, low: 100, close: 102 },
  { timestamp: Date.UTC(2026, 2, 9, 13, 0), open: 103, high: 105, low: 102, close: 104 },
]);

describe("newsCorrelationTimeline", () => {
  it("keeps actual timestamps on chart candles", () => {
    expect(candles[0].time).toBe(Math.floor(Date.UTC(2026, 2, 6, 20, 0) / 1000));
    expect(candles[2].actualTimestamp).toBe(Math.floor(Date.UTC(2026, 2, 9, 13, 0) / 1000));
  });

  it("preserves valid session gaps with whitespace points for index symbols", () => {
    const series = buildRenderableChartSeries(candles, "1h", "NDX");
    const whitespacePoints = series.filter((point) => !("open" in point));

    expect(whitespacePoints.length).toBeGreaterThan(0);
    expect(series[0]).toMatchObject({ time: candles[0].time, open: 100, close: 101 });
  });

  it("does not inject whitespace for small broken gaps on continuous symbols", () => {
    const continuousCandles = buildTimelineChartCandles([
      { timestamp: Date.UTC(2026, 2, 10, 10, 0), open: 100, high: 101, low: 99, close: 100.5 },
      { timestamp: Date.UTC(2026, 2, 10, 12, 0), open: 100.5, high: 101.5, low: 100, close: 101 },
    ]);
    const series = buildRenderableChartSeries(continuousCandles, "1h", "XAUUSD");
    expect(series.filter((point) => !("open" in point))).toHaveLength(0);
  });

  it("maps markers to the nearest actual candle time", () => {
    const mapped = buildMappedChartMarkers([
      {
        id: "news-1",
        time: new Date(Date.UTC(2026, 2, 6, 20, 20)).toISOString(),
        position: "aboveBar",
        color: "#fff",
        shape: "circle",
        size: 1,
      },
    ], candles);

    expect(mapped).toHaveLength(1);
    expect(mapped[0].time).toBe(candles[0].time);
  });

  it("returns null for timestamps outside the loaded candle range", () => {
    const mapped = mapActualTimestampToChartTime(Math.floor(Date.UTC(2026, 2, 10, 0, 0) / 1000), candles);
    expect(mapped).toBeNull();
  });
});