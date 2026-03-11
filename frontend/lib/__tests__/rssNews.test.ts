import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchNewsForCandle } from "../api/rssNews";

describe("fetchNewsForCandle", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses POST against the RSS candle-news endpoint and returns the top-level payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        symbol: "XAUUSD",
        candle: {
          timestamp: "2026-03-10T19:00:00Z",
          change_pct: 1.1,
          range_pct: 1.6,
          is_significant: true,
        },
        news_count: 1,
        news: [{ id: "n1", headline: "Altın yükseldi", headline_en: "Gold rose", timestamp: "2026-03-10T18:55:00Z", source: "Reuters", urgency: "high", score: 8, direction: "bullish", reasoning_tr: "Dolar zayıfladı", relevance_score: 0.9, url: "https://example.com" }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await fetchNewsForCandle("XAUUSD", "2026-03-10T19:00:00Z", 2900, 2910, 2915, 2898, "1h");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/rss/candle-news/XAUUSD?"),
      expect.objectContaining({ method: "POST" })
    );
    expect(response.news[0].headline).toBe("Altın yükseldi");
  });

  it("passes the selected locale through to the candle-news endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        symbol: "XAUUSD",
        candle: {
          timestamp: "2026-03-10T19:00:00Z",
          change_pct: 1.1,
          range_pct: 1.6,
          is_significant: true,
        },
        news_count: 0,
        news: [],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchNewsForCandle("XAUUSD", "2026-03-10T19:00:00Z", 2900, 2910, 2915, 2898, "1h", "de");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("lang=de"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("normalizes the legacy nested candle-news payload shape", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          symbol: "XAUUSD",
          candle_time: "2026-03-10T19:00:00Z",
          news_count: 1,
          news: [{ id: "n1", headline: "Legacy", headline_en: "Legacy", timestamp: "2026-03-10T18:55:00Z", source: "Reuters", urgency: "high", score: 8, direction: "bullish", reasoning_tr: "Legacy", relevance_score: 0.9, url: "https://example.com" }],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await fetchNewsForCandle("XAUUSD", "2026-03-10T19:00:00Z", 2900, 2910, 2915, 2898, "1h");

    expect(response.symbol).toBe("XAUUSD");
    expect(response.news_count).toBe(1);
    expect(response.news[0].headline_en).toBe("Legacy");
  });
});