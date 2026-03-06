import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ReactNode } from "react";

// Mock WebSocketContext
const mockUseWSPanelData = vi.fn();

vi.mock("../../../contexts/WebSocketContext", () => ({
  useWSPanelData: (...args: any[]) => mockUseWSPanelData(...args),
}));

// Mock i18n store
vi.mock("../../../lib/i18n/store", () => ({
  useI18nStore: () => ({ t: (key: string) => key }),
}));

// Mock CustomIcons
vi.mock("../../ui/CustomIcons", () => ({
  TrendingUpIcon: () => <span data-testid="trending-up">↗</span>,
  ArrowUpIcon: () => <span data-testid="arrow-up">↑</span>,
  ArrowDownIcon: () => <span data-testid="arrow-down">↓</span>,
  MinusIcon: () => <span data-testid="minus">−</span>,
  TargetIcon: () => <span data-testid="target">🎯</span>,
  InfoIcon: () => <span data-testid="info">ℹ</span>,
  CloseIcon: () => <span data-testid="close">✕</span>,
  RotateIcon: () => <span data-testid="refresh">↻</span>,
}));

// Mock TrendChannelChart
vi.mock("../TrendChannelChart", () => ({
  default: () => <div data-testid="trend-channel-chart">Chart</div>,
}));

// Import component after mocks
import ClearTrendPanelV3 from "../ClearTrendPanelV3";

describe("ClearTrendPanelV3", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseWSPanelData.mockReturnValue({ data: null, wsConnected: false });
  });

  it("renders loading state when data is undefined", () => {
    mockUseWSPanelData.mockReturnValue({ data: null, wsConnected: false });
    
    render(<ClearTrendPanelV3 symbol="NDX.INDX" />);
    
    // Should show loading skeleton
    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeTruthy();
  });

  it("renders BUY signal correctly with green color", async () => {
    const buyData = {
      symbol: "NDX.INDX",
      timeframe: "1H",
      timestamp: new Date().toISOString(),
      price: {
        current: 15000,
        display: "15000.00",
        decimals: 2,
      },
      trend: {
        direction: "UP" as const,
        strength: 75,
        strength_percent: 75,
        description: "Strong uptrend",
        ema_20: 14950,
        ema_50: 14900,
      },
      levels: {
        all_levels: [],
        nearest_resistance: null,
        nearest_support: null,
        pivot: 15000,
        range_high: 15100,
        range_low: 14900,
      },
      trade_zones: {
        suggestion: "BUY",
      },
      pip_value: 1,
      chart_data: {
        closes: [14900, 14950, 15000, 15050, 15100],
        trend_channel: {
          upper: [15100, 15150, 15200],
          lower: [14900, 14850, 14800],
          middle: [15000, 15000, 15000],
        },
      },
      explanations: {
        trend: "Price is above EMA 20 and EMA 50",
      },
    };

    mockUseWSPanelData.mockReturnValue({ data: buyData, wsConnected: true });
    
    render(<ClearTrendPanelV3 symbol="NDX.INDX" />);
    
    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText("15000.00")).toBeTruthy();
    });

    expect(screen.getByTestId("trending-up")).toBeTruthy();
    expect(screen.getByText("BUY")).toBeTruthy();
    expect(screen.queryByTestId("trend-channel-chart")).toBeNull();
  });

  it("renders SELL signal correctly with red color", async () => {
    const sellData = {
      symbol: "XAUUSD",
      timeframe: "1H",
      timestamp: new Date().toISOString(),
      price: {
        current: 2000,
        display: "2000.00",
        decimals: 2,
      },
      trend: {
        direction: "DOWN" as const,
        strength: 65,
        strength_percent: 65,
        description: "Strong downtrend",
        ema_20: 2010,
        ema_50: 2020,
      },
      levels: {
        all_levels: [],
        nearest_resistance: null,
        nearest_support: null,
        pivot: 2000,
        range_high: 2050,
        range_low: 1950,
      },
      trade_zones: {
        suggestion: "SELL",
      },
      pip_value: 0.1,
      chart_data: {
        closes: [2050, 2040, 2030, 2020, 2010, 2000],
        trend_channel: {
          upper: [2050, 2060, 2070],
          lower: [1950, 1940, 1930],
          middle: [2000, 2000, 2000],
        },
      },
      explanations: {
        trend: "Price is below EMA 20 and EMA 50",
      },
    };

    mockUseWSPanelData.mockReturnValue({ data: sellData, wsConnected: true });
    
    render(<ClearTrendPanelV3 symbol="XAUUSD" />);
    
    await waitFor(() => {
      expect(screen.getByText("2000.00")).toBeTruthy();
    });

    expect(screen.getByTestId("arrow-down")).toBeTruthy();
    expect(screen.getByText("SELL")).toBeTruthy();
    expect(screen.getByTestId("trend-channel-chart")).toBeTruthy();
  });

  it("never crashes when chart_data is undefined", () => {
    const dataWithoutChart = {
      symbol: "NDX.INDX",
      timeframe: "1H",
      timestamp: new Date().toISOString(),
      price: {
        current: 15000,
        display: "15000.00",
        decimals: 2,
      },
      trend: {
        direction: "NEUTRAL" as const,
        strength: 50,
        strength_percent: 50,
        description: "Sideways",
        ema_20: 15000,
        ema_50: 15000,
      },
      levels: {
        all_levels: [],
        nearest_resistance: null,
        nearest_support: null,
        pivot: 15000,
        range_high: 15100,
        range_low: 14900,
      },
      trade_zones: {
        suggestion: "HOLD",
      },
      pip_value: 1,
      // chart_data is missing
      explanations: {},
    };

    mockUseWSPanelData.mockReturnValue({ data: dataWithoutChart, wsConnected: true });
    
    // Should not throw
    expect(() => render(<ClearTrendPanelV3 symbol="NDX.INDX" />)).not.toThrow();

    expect(screen.getByText("15000.00")).toBeTruthy();
    expect(screen.getByText("HOLD")).toBeTruthy();
    expect(screen.queryByTestId("trend-channel-chart")).toBeNull();
  });

  it("handles chart_data.closes.length > 5 check correctly", async () => {
    const dataWithManyCloses = {
      symbol: "NDX.INDX",
      timeframe: "1H",
      timestamp: new Date().toISOString(),
      price: {
        current: 15000,
        display: "15000.00",
        decimals: 2,
      },
      trend: {
        direction: "UP" as const,
        strength: 75,
        strength_percent: 75,
        description: "Strong uptrend",
        ema_20: 14950,
        ema_50: 14900,
      },
      levels: {
        all_levels: [],
        nearest_resistance: null,
        nearest_support: null,
        pivot: 15000,
        range_high: 15100,
        range_low: 14900,
      },
      trade_zones: {
        suggestion: "BUY",
      },
      pip_value: 1,
      chart_data: {
        closes: [14900, 14920, 14940, 14960, 14980, 15000, 15020, 15040, 15060, 15080],
        trend_channel: {
          upper: [15100, 15120, 15140],
          lower: [14900, 14880, 14860],
          middle: [15000, 15000, 15000],
        },
      },
      explanations: {},
    };

    mockUseWSPanelData.mockReturnValue({ data: dataWithManyCloses, wsConnected: true });
    
    render(<ClearTrendPanelV3 symbol="NDX.INDX" />);
    
    await waitFor(() => {
      expect(screen.getByText("15000.00")).toBeTruthy();
    });

    expect(screen.getByText("BUY")).toBeTruthy();
    // Should render chart when closes.length > 5
    expect(screen.getByTestId("trend-channel-chart")).toBeTruthy();
  });

  it("renders error state gracefully when API fails", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockRejectedValue(new Error("Network error"));
    
    mockUseWSPanelData.mockReturnValue({ data: null, wsConnected: false });
    
    render(<ClearTrendPanelV3 symbol="NDX.INDX" />);
    
    expect(document.querySelector(".animate-pulse")).toBeTruthy();

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(document.querySelector(".animate-pulse")).toBeNull();
    });

    expect(screen.getByText("CLEAR TREND V3")).toBeTruthy();
  });
});
