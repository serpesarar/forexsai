import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import {
  useDashboardStore,
  useMLStrategyStore,
  useNewsStore,
  useDetailPanelStore,
} from "../store";

describe("Dashboard Store", () => {
  beforeEach(() => {
    // Reset store to initial state
    act(() => {
      useDashboardStore.setState({
        data: null,
        isLoading: false,
        autoRefresh: false,
        customAnalysis: null,
        customAnalysisLoading: false,
      });
    });
  });

  it("has correct default state", () => {
    const state = useDashboardStore.getState();
    
    expect(state.data).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.autoRefresh).toBe(false);
    expect(state.customAnalysis).toBeNull();
    expect(state.customAnalysisLoading).toBe(false);
  });

  it("toggleAutoRefresh updates state correctly", () => {
    act(() => {
      useDashboardStore.getState().toggleAutoRefresh(true);
    });
    
    expect(useDashboardStore.getState().autoRefresh).toBe(true);
  });

  it("fetchAll sets isLoading correctly", async () => {
    const fetchPromise = act(async () => {
      await useDashboardStore.getState().fetchAll();
    });
    
    // Should be loading during fetch
    expect(useDashboardStore.getState().isLoading).toBe(true);
    
    await fetchPromise;
    
    // Should not be loading after fetch
    expect(useDashboardStore.getState().isLoading).toBe(false);
    expect(useDashboardStore.getState().data).toEqual({});
  });
});

describe("ML Strategy Store", () => {
  beforeEach(() => {
    act(() => {
      useMLStrategyStore.setState({
        configs: {},
      });
    });
  });

  it("has correct default state", () => {
    const state = useMLStrategyStore.getState();
    
    expect(state.configs).toEqual({});
  });

  it("getConfig returns default config for unknown symbol", () => {
    const config = useMLStrategyStore.getState().getConfig("UNKNOWN");
    
    expect(config).toEqual({ strategy: "balanced", enabledFactors: null });
  });

  it("setPresetStrategy creates config with strategy", () => {
    act(() => {
      useMLStrategyStore.getState().setPresetStrategy("NDX.INDX", "aggressive");
    });
    
    const config = useMLStrategyStore.getState().getConfig("NDX.INDX");
    expect(config.strategy).toBe("aggressive");
    expect(config.enabledFactors).toBeNull();
  });

  it("setCustomFactors creates config with factors", () => {
    const factors = ["trend", "momentum", "volume"];
    
    act(() => {
      useMLStrategyStore.getState().setCustomFactors("XAUUSD", factors);
    });
    
    const config = useMLStrategyStore.getState().getConfig("XAUUSD");
    expect(config.strategy).toBeNull();
    expect(config.enabledFactors).toEqual(factors);
  });

  it("strategy toggle works correctly", () => {
    // Start with preset strategy
    act(() => {
      useMLStrategyStore.getState().setPresetStrategy("NDX.INDX", "balanced");
    });
    
    let config = useMLStrategyStore.getState().getConfig("NDX.INDX");
    expect(config.strategy).toBe("balanced");
    
    // Switch to custom factors
    act(() => {
      useMLStrategyStore.getState().setCustomFactors("NDX.INDX", ["rsi", "macd"]);
    });
    
    config = useMLStrategyStore.getState().getConfig("NDX.INDX");
    expect(config.strategy).toBeNull();
    expect(config.enabledFactors).toEqual(["rsi", "macd"]);
    
    // Switch back to preset
    act(() => {
      useMLStrategyStore.getState().setPresetStrategy("NDX.INDX", "conservative");
    });
    
    config = useMLStrategyStore.getState().getConfig("NDX.INDX");
    expect(config.strategy).toBe("conservative");
    expect(config.enabledFactors).toBeNull();
  });

  it("maintains separate configs for different symbols", () => {
    act(() => {
      useMLStrategyStore.getState().setPresetStrategy("NDX.INDX", "aggressive");
      useMLStrategyStore.getState().setPresetStrategy("XAUUSD", "conservative");
    });
    
    const ndxConfig = useMLStrategyStore.getState().getConfig("NDX.INDX");
    const xauConfig = useMLStrategyStore.getState().getConfig("XAUUSD");
    
    expect(ndxConfig.strategy).toBe("aggressive");
    expect(xauConfig.strategy).toBe("conservative");
  });
});

describe("News Store", () => {
  beforeEach(() => {
    act(() => {
      useNewsStore.setState({
        impactFilter: "all",
        categoryFilter: "all",
      });
    });
  });

  it("has correct default state", () => {
    const state = useNewsStore.getState();
    
    expect(state.impactFilter).toBe("all");
    expect(state.categoryFilter).toBe("all");
  });

  it("setImpactFilter updates correctly", () => {
    act(() => {
      useNewsStore.getState().setImpactFilter("high");
    });
    
    expect(useNewsStore.getState().impactFilter).toBe("high");
  });

  it("setCategoryFilter updates correctly", () => {
    act(() => {
      useNewsStore.getState().setCategoryFilter("fed");
    });
    
    expect(useNewsStore.getState().categoryFilter).toBe("fed");
  });
});

describe("Detail Panel Store", () => {
  beforeEach(() => {
    act(() => {
      useDetailPanelStore.setState({
        isOpen: false,
        type: null,
        symbol: null,
        title: "",
        data: null,
      });
    });
  });

  it("has correct default state", () => {
    const state = useDetailPanelStore.getState();
    
    expect(state.isOpen).toBe(false);
    expect(state.type).toBeNull();
    expect(state.symbol).toBeNull();
    expect(state.title).toBe("");
    expect(state.data).toBeNull();
  });

  it("open sets panel state correctly", () => {
    act(() => {
      useDetailPanelStore.getState().open(
        "support_resistance",
        { levels: [100, 200] },
        "NASDAQ",
        "Support/Resistance"
      );
    });
    
    const state = useDetailPanelStore.getState();
    expect(state.isOpen).toBe(true);
    expect(state.type).toBe("support_resistance");
    expect(state.symbol).toBe("NASDAQ");
    expect(state.title).toBe("Support/Resistance");
    expect(state.data).toEqual({ levels: [100, 200] });
  });

  it("close resets panel state", () => {
    // First open
    act(() => {
      useDetailPanelStore.getState().open(
        "ema_distance",
        { ema20: 100 },
        "XAUUSD",
        "EMA Distance"
      );
    });
    
    // Then close
    act(() => {
      useDetailPanelStore.getState().close();
    });
    
    const state = useDetailPanelStore.getState();
    expect(state.isOpen).toBe(false);
    expect(state.type).toBeNull();
    expect(state.symbol).toBeNull();
    expect(state.title).toBe("");
    expect(state.data).toBeNull();
  });
});

describe("Store Isolation", () => {
  it("stores do not cross-contaminate between test runs", () => {
    // Set values in different stores
    act(() => {
      useMLStrategyStore.getState().setPresetStrategy("TEST_SYMBOL", "aggressive");
      useNewsStore.getState().setImpactFilter("high");
    });
    
    // Verify each store has only its own data
    expect(useMLStrategyStore.getState().configs["TEST_SYMBOL"].strategy).toBe("aggressive");
    expect(useNewsStore.getState().impactFilter).toBe("high");

    // ML store should not have chart data
    expect((useMLStrategyStore.getState() as any).symbol).toBeUndefined();
  });

  it("reset between tests works correctly", () => {
    // First test simulation
    act(() => {
      useNewsStore.getState().setImpactFilter("low");
    });
    expect(useNewsStore.getState().impactFilter).toBe("low");
    
    // Reset (simulating beforeEach)
    act(() => {
      useNewsStore.setState({ impactFilter: "all", categoryFilter: "all" });
    });
    
    // Verify reset worked
    expect(useNewsStore.getState().impactFilter).toBe("all");
    expect(useNewsStore.getState().categoryFilter).toBe("all");
  });
});
