import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { ReactNode } from "react";

// Mock React's useContext
const mockUseContext = vi.fn();

vi.mock("react", async () => {
  const actual = await vi.importActual("react");
  return {
    ...actual,
    useContext: () => mockUseContext(),
    createContext: (defaultValue: any) => ({
      Provider: ({ children }: { children: ReactNode }) => children,
      Consumer: ({ children }: { children: (value: any) => ReactNode }) => children(defaultValue),
      displayName: "MockContext",
      _currentValue: defaultValue,
    }),
  };
});

// Import after mocks
import { useWSPanelData, useWSData, useWSSymbolData } from "../../contexts/WebSocketContext";

describe("useWSPanelData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns null when WebSocket is not connected", () => {
    mockUseContext.mockReturnValue({
      symbolData: {},
      status: "disconnected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toBeNull();
    expect(result.current.wsConnected).toBe(false);
  });

  it("returns correct data when WS message received with matching panelKey", () => {
    const mockPanelData = {
      trend: { direction: "UP", strength: 75 },
      price: { current: 15000 },
    };

    mockUseContext.mockReturnValue({
      symbolData: {
        "NDX.INDX": {
          symbol: "NDX.INDX",
          panels: {
            clear_trend: mockPanelData,
          },
        },
      },
      status: "connected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toEqual(mockPanelData);
    expect(result.current.wsConnected).toBe(true);
  });

  it("does not update state for non-matching panelKey", () => {
    const mockPanelData = {
      trend: { direction: "UP", strength: 75 },
    };

    mockUseContext.mockReturnValue({
      symbolData: {
        "NDX.INDX": {
          symbol: "NDX.INDX",
          panels: {
            emel: mockPanelData,
            // clear_trend is missing
          },
        },
      },
      status: "connected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toBeNull();
    expect(result.current.wsConnected).toBe(true);
  });

  it("handles malformed JSON gracefully (no crash)", () => {
    // Even with malformed data structure, should not crash
    mockUseContext.mockReturnValue({
      symbolData: {
        "NDX.INDX": {
          symbol: "NDX.INDX",
          // panels is missing entirely
        },
      },
      status: "connected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toBeNull();
    expect(result.current.wsConnected).toBe(true);
  });

  it("handles symbol not in data", () => {
    mockUseContext.mockReturnValue({
      symbolData: {
        "XAUUSD": {
          symbol: "XAUUSD",
          panels: {
            clear_trend: { trend: "UP" },
          },
        },
      },
      status: "connected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toBeNull();
    expect(result.current.wsConnected).toBe(true);
  });

  it("handles empty symbolData", () => {
    mockUseContext.mockReturnValue({
      symbolData: {},
      status: "connected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toBeNull();
    expect(result.current.wsConnected).toBe(true);
  });

  it("handles null symbolData gracefully", () => {
    // Test null symbolData - should return null without crashing
    mockUseContext.mockReturnValue({
      symbolData: null,
      status: "connected",
    });

    const { result } = renderHook(() => useWSPanelData("NDX.INDX", "clear_trend"));

    expect(result.current.data).toBeNull();
    expect(result.current.wsConnected).toBe(true);
  });
});

describe("useWSData", () => {
  it("returns default context value when not in provider", () => {
    mockUseContext.mockReturnValue({
      status: "disconnected",
      symbolData: {},
      lastUpdate: null,
      reconnect: expect.any(Function),
    });

    const { result } = renderHook(() => useWSData());

    expect(result.current.status).toBe("disconnected");
    expect(result.current.symbolData).toEqual({});
    expect(result.current.lastUpdate).toBeNull();
  });
});

describe("useWSSymbolData", () => {
  it("returns null for unknown symbol", () => {
    mockUseContext.mockReturnValue({
      symbolData: {},
    });

    const { result } = renderHook(() => useWSSymbolData("UNKNOWN"));

    expect(result.current).toBeNull();
  });

  it("returns data for known symbol", () => {
    const symbolData = {
      symbol: "NDX.INDX",
      timestamp: new Date().toISOString(),
      data: {
        current_price: 15000,
      },
    };

    mockUseContext.mockReturnValue({
      symbolData: {
        "NDX.INDX": symbolData,
      },
    });

    const { result } = renderHook(() => useWSSymbolData("NDX.INDX"));

    expect(result.current).toEqual(symbolData);
  });
});
