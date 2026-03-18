import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import StrategyPerformancePanel from "../StrategyPerformancePanel";

vi.mock("@/lib/api/base", () => ({ getApiBase: () => "" }));
vi.mock("../PanelInfoButton", () => ({ PanelInfoButton: () => <div data-testid="panel-info" /> }));
vi.mock("../panels/ModelPerformanceModal", () => ({ ModelPerformanceModal: () => null }));
vi.mock("../SignalDetailModal", () => ({ default: () => null }));

const payload = {
  period_days: 30,
  predictions_count: 8,
  ml_predictions_count: 7,
  outcomes_count: 6,
  eligible_outcomes_count: 5,
  strategies: {
    "NDX.INDX": {
      main: {
        scope: "main",
        total_predictions: 4,
        scored_signals: 3,
        resolved_signals: 3,
        with_outcome: 3,
        correct: 2,
        completed: 2,
        stopped: 1,
        expired: 1,
        active: 0,
        accuracy: 66.7,
        win_rate: 66.7,
        target_hits: 2,
        stop_hits: 1,
        target_hit_rate: 66.7,
        stop_hit_rate: 33.3,
        avg_confidence: 61.2,
        net_pips: 18.5,
        avg_pips: 6.2,
        tp_breakdown: { TP1: 2, TP2: 1, TP3: 1, TP4: 0 },
        tp_hit_rates: { TP1: 66.7, TP2: 33.3, TP3: 33.3, TP4: 0 },
        avg_duration_minutes: 46,
        avg_win_duration_minutes: 40,
        avg_loss_duration_minutes: 58,
        quality_score: 58.1,
        scalp_score: 61.3,
        long_term_score: 54.9,
      },
      aggressive: {
        scope: "aggressive",
        total_predictions: 3,
        scored_signals: 2,
        resolved_signals: 2,
        with_outcome: 2,
        correct: 2,
        completed: 2,
        stopped: 0,
        expired: 0,
        active: 1,
        accuracy: 100,
        win_rate: 100,
        target_hits: 2,
        stop_hits: 0,
        target_hit_rate: 100,
        stop_hit_rate: 0,
        avg_confidence: 48.3,
        net_pips: 24,
        avg_pips: 12,
        tp_breakdown: { TP1: 2, TP2: 1, TP3: 0, TP4: 0 },
        tp_hit_rates: { TP1: 100, TP2: 50, TP3: 0, TP4: 0 },
        avg_duration_minutes: 18,
        avg_win_duration_minutes: 18,
        avg_loss_duration_minutes: null,
        quality_score: 63.4,
        scalp_score: 72.2,
        long_term_score: 57.1,
      },
    },
    XAUUSD: {},
    "GDAXI.INDX": {},
    "USOIL.FOREX": {},
  },
  best_strategies: {
    "NDX.INDX": { strategy: "aggressive", accuracy: 100 },
    XAUUSD: { strategy: null, accuracy: null },
    "GDAXI.INDX": { strategy: null, accuracy: null },
    "USOIL.FOREX": { strategy: null, accuracy: null },
  },
  strategy_order: ["main", "ultra_safe", "balanced", "full_power", "aggressive", "nasdaq_precision"],
  strategy_descriptions: {
    main: "Ham/orijinal ML akışı; preset filtre uygulanmadan loglanan ana model.",
    aggressive: "En esnek preset; daha hızlı ve daha fazla sinyal arar.",
  },
  symbols: {
    "NDX.INDX": {
      available_scopes: ["main", "aggressive"],
      total_predictions: 7,
      resolved_signals: 5,
      leaders: {
        quality: { scope: "aggressive", score: 63.4, resolved_signals: 2, win_rate: 100, net_pips: 24, avg_duration_minutes: 18 },
        scalping: { scope: "aggressive", score: 72.2, resolved_signals: 2, win_rate: 100, net_pips: 24, avg_duration_minutes: 18 },
        long_term: { scope: "main", score: 54.9, resolved_signals: 3, win_rate: 66.7, net_pips: 18.5, avg_duration_minutes: 46 },
      },
    },
    XAUUSD: { available_scopes: [], total_predictions: 0, resolved_signals: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
    "GDAXI.INDX": { available_scopes: [], total_predictions: 0, resolved_signals: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
    "USOIL.FOREX": { available_scopes: [], total_predictions: 0, resolved_signals: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
  },
  overall_summary: {
    total_predictions: 7,
    resolved_signals: 5,
    leaders: {
      quality: { scope: "aggressive", score: 63.4, resolved_signals: 2, win_rate: 100, net_pips: 24, avg_duration_minutes: 18 },
      scalping: { scope: "aggressive", score: 72.2, resolved_signals: 2, win_rate: 100, net_pips: 24, avg_duration_minutes: 18 },
      long_term: { scope: "main", score: 54.9, resolved_signals: 3, win_rate: 66.7, net_pips: 18.5, avg_duration_minutes: 46 },
    },
  },
};

const aiPanelPayload = {
  period_days: 30,
  ai_panel_predictions_count: 4,
  ai_panel_snapshots_count: 16,
  outcomes_count: 3,
  eligible_outcomes_count: 3,
  strategies: {
    "NDX.INDX": {
      hourly_panel: {
        scope: "hourly_panel",
        total_predictions: 4,
        scored_signals: 3,
        resolved_signals: 3,
        with_outcome: 3,
        correct: 2,
        completed: 2,
        stopped: 1,
        expired: 0,
        active: 1,
        accuracy: 66.7,
        win_rate: 66.7,
        target_hits: 2,
        stop_hits: 1,
        target_hit_rate: 66.7,
        stop_hit_rate: 33.3,
        avg_confidence: 64.5,
        net_pips: 14.2,
        avg_pips: 4.7,
        tp_breakdown: { TP1: 2, TP2: 1, TP3: 0, TP4: 0 },
        tp_hit_rates: { TP1: 66.7, TP2: 33.3, TP3: 0, TP4: 0 },
        avg_duration_minutes: 74,
        avg_win_duration_minutes: 62,
        avg_loss_duration_minutes: 98,
        quality_score: 52.4,
        scalp_score: 47.1,
        long_term_score: 55.8,
      },
    },
    XAUUSD: {},
    "GDAXI.INDX": {},
    "USOIL.FOREX": {},
  },
  symbols: {
    "NDX.INDX": {
      available_scopes: ["hourly_panel"],
      total_predictions: 4,
      resolved_signals: 3,
      snapshot_count: 16,
      leaders: {
        quality: { scope: "hourly_panel", score: 52.4, resolved_signals: 3, win_rate: 66.7, net_pips: 14.2, avg_duration_minutes: 74 },
        scalping: { scope: "hourly_panel", score: 47.1, resolved_signals: 3, win_rate: 66.7, net_pips: 14.2, avg_duration_minutes: 74 },
        long_term: { scope: "hourly_panel", score: 55.8, resolved_signals: 3, win_rate: 66.7, net_pips: 14.2, avg_duration_minutes: 74 },
      },
    },
    XAUUSD: { available_scopes: [], total_predictions: 0, resolved_signals: 0, snapshot_count: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
    "GDAXI.INDX": { available_scopes: [], total_predictions: 0, resolved_signals: 0, snapshot_count: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
    "USOIL.FOREX": { available_scopes: [], total_predictions: 0, resolved_signals: 0, snapshot_count: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
  },
  panel_scope_order: ["hourly_panel"],
  panel_descriptions: {
    hourly_panel: "CLAUDE AI ANALYSIS panelinden her saat force-refresh ile alınan actionable sinyaller.",
  },
  overall_summary: {
    total_predictions: 4,
    resolved_signals: 3,
    leaders: {
      quality: { scope: "hourly_panel", score: 52.4, resolved_signals: 3, win_rate: 66.7, net_pips: 14.2, avg_duration_minutes: 74 },
      scalping: { scope: "hourly_panel", score: 47.1, resolved_signals: 3, win_rate: 66.7, net_pips: 14.2, avg_duration_minutes: 74 },
      long_term: { scope: "hourly_panel", score: 55.8, resolved_signals: 3, win_rate: 66.7, net_pips: 14.2, avg_duration_minutes: 74 },
    },
  },
};

const signalsPayload = {
  signals: [
    {
      id: "signal-001",
      symbol: "NDX.INDX",
      timeframe: "30m",
      ml_direction: "BUY",
      ml_confidence: 67,
      status: "completed",
      created_at: "2026-03-07T05:00:00Z",
      pnl_pips: 5,
      duration_minutes: 30,
      normalized_model: "ml",
      strategy_scope: "main",
    },
  ],
  count: 1,
};

const smcPayload = {
  period_days: 30,
  smc_predictions_count: 3,
  outcomes_count: 2,
  eligible_outcomes_count: 2,
  timeframes: {
    "NDX.INDX": {
      "5m": {
        scope: "5m",
        total_predictions: 2,
        scored_signals: 2,
        resolved_signals: 2,
        with_outcome: 2,
        correct: 1,
        completed: 1,
        stopped: 1,
        expired: 0,
        active: 0,
        accuracy: 50,
        win_rate: 50,
        target_hits: 1,
        stop_hits: 1,
        target_hit_rate: 50,
        stop_hit_rate: 50,
        avg_confidence: 71,
        net_pips: 4,
        avg_pips: 2,
        tp_breakdown: { TP1: 1, TP2: 0, TP3: 0, TP4: 0 },
        tp_hit_rates: { TP1: 50, TP2: 0, TP3: 0, TP4: 0 },
        avg_duration_minutes: 35,
        avg_win_duration_minutes: 20,
        avg_loss_duration_minutes: 50,
        quality_score: 51,
        scalp_score: 49,
        long_term_score: 40,
      },
      "15m": {
        scope: "15m",
        total_predictions: 1,
        scored_signals: 0,
        resolved_signals: 0,
        with_outcome: 0,
        correct: 0,
        completed: 0,
        stopped: 0,
        expired: 0,
        active: 1,
        accuracy: 0,
        win_rate: 0,
        target_hits: 0,
        stop_hits: 0,
        target_hit_rate: null,
        stop_hit_rate: null,
        avg_confidence: 69,
        net_pips: 0,
        avg_pips: 0,
        tp_breakdown: { TP1: 0, TP2: 0, TP3: 0, TP4: 0 },
        tp_hit_rates: { TP1: null, TP2: null, TP3: null, TP4: null },
        avg_duration_minutes: null,
        avg_win_duration_minutes: null,
        avg_loss_duration_minutes: null,
        quality_score: 0,
        scalp_score: 0,
        long_term_score: 0,
      },
      "1h": {
        scope: "1h",
        total_predictions: 0,
        scored_signals: 0,
        resolved_signals: 0,
        with_outcome: 0,
        correct: 0,
        completed: 0,
        stopped: 0,
        expired: 0,
        active: 0,
        accuracy: 0,
        win_rate: 0,
        target_hits: 0,
        stop_hits: 0,
        target_hit_rate: null,
        stop_hit_rate: null,
        avg_confidence: 0,
        net_pips: 0,
        avg_pips: 0,
        tp_breakdown: { TP1: 0, TP2: 0, TP3: 0, TP4: 0 },
        tp_hit_rates: { TP1: null, TP2: null, TP3: null, TP4: null },
        avg_duration_minutes: null,
        avg_win_duration_minutes: null,
        avg_loss_duration_minutes: null,
        quality_score: 0,
        scalp_score: 0,
        long_term_score: 0,
      },
      "4h": {
        scope: "4h",
        total_predictions: 0,
        scored_signals: 0,
        resolved_signals: 0,
        with_outcome: 0,
        correct: 0,
        completed: 0,
        stopped: 0,
        expired: 0,
        active: 0,
        accuracy: 0,
        win_rate: 0,
        target_hits: 0,
        stop_hits: 0,
        target_hit_rate: null,
        stop_hit_rate: null,
        avg_confidence: 0,
        net_pips: 0,
        avg_pips: 0,
        tp_breakdown: { TP1: 0, TP2: 0, TP3: 0, TP4: 0 },
        tp_hit_rates: { TP1: null, TP2: null, TP3: null, TP4: null },
        avg_duration_minutes: null,
        avg_win_duration_minutes: null,
        avg_loss_duration_minutes: null,
        quality_score: 0,
        scalp_score: 0,
        long_term_score: 0,
      },
    },
    XAUUSD: {},
    "GDAXI.INDX": {},
    "USOIL.FOREX": {},
  },
  symbols: {
    "NDX.INDX": {
      available_scopes: ["5m", "15m"],
      total_predictions: 3,
      resolved_signals: 2,
      leaders: {
        quality: { scope: "5m", score: 51, resolved_signals: 2, win_rate: 50, net_pips: 4, avg_duration_minutes: 35 },
        scalping: { scope: "5m", score: 49, resolved_signals: 2, win_rate: 50, net_pips: 4, avg_duration_minutes: 35 },
        long_term: { scope: "5m", score: 40, resolved_signals: 2, win_rate: 50, net_pips: 4, avg_duration_minutes: 35 },
      },
    },
    XAUUSD: { available_scopes: [], total_predictions: 0, resolved_signals: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
    "GDAXI.INDX": { available_scopes: [], total_predictions: 0, resolved_signals: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
    "USOIL.FOREX": { available_scopes: [], total_predictions: 0, resolved_signals: 0, leaders: { quality: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, scalping: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null }, long_term: { scope: null, score: null, resolved_signals: 0, win_rate: null, net_pips: null, avg_duration_minutes: null } } },
  },
  timeframe_order: ["5m", "15m", "1h", "4h"],
  timeframe_descriptions: {
    "5m": "Fast Smart Money Zones flow.",
    "15m": "Balanced Smart Money Zones flow.",
    "1h": "Primary intraday Smart Money Zones flow.",
    "4h": "Slow Smart Money Zones flow.",
  },
  overall_summary: {
    total_predictions: 3,
    resolved_signals: 2,
    leaders: {
      quality: { scope: "5m", score: 51, resolved_signals: 2, win_rate: 50, net_pips: 4, avg_duration_minutes: 35 },
      scalping: { scope: "5m", score: 49, resolved_signals: 2, win_rate: 50, net_pips: 4, avg_duration_minutes: 35 },
      long_term: { scope: "5m", score: 40, resolved_signals: 2, win_rate: 50, net_pips: 4, avg_duration_minutes: 35 },
    },
  },
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <StrategyPerformancePanel />
    </QueryClientProvider>
  );
}

describe("StrategyPerformancePanel", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockImplementation((input: string | URL) => {
      const url = String(input);
      if (url.includes("/api/learning/strategy-performance")) {
        return Promise.resolve({ ok: true, json: async () => payload });
      }
      if (url.includes("/api/learning/smc-performance")) {
        return Promise.resolve({ ok: true, json: async () => smcPayload });
      }
      if (url.includes("/api/learning/ai-panel-performance")) {
        return Promise.resolve({ ok: true, json: async () => aiPanelPayload });
      }
      if (url.includes("/api/learning/signals/recent")) {
        return Promise.resolve({ ok: true, json: async () => signalsPayload });
      }
      return Promise.resolve({ ok: false, json: async () => ({ error: "unexpected" }) });
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders main ML scope plus overall leader cards from the new strategy contract", async () => {
    renderPanel();

    await screen.findByText("Strategy Performance Analysis");
    expect((await screen.findAllByText("Best Signal Quality")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Ham ML").length).toBeGreaterThan(0);
    expect(screen.getByText(/Ham\/orijinal ML akışı/)).toBeInTheDocument();
    expect(screen.getAllByText("Agresif").length).toBeGreaterThan(0);
  });

  it("renders Smart Money Zones performance from the dedicated analytics endpoint", async () => {
    renderPanel();

    expect(await screen.findByText("Smart Money Zones Performance")).toBeInTheDocument();
    expect(screen.getByText("SMC Predictions")).toBeInTheDocument();
    expect(screen.getAllByText("5m").length).toBeGreaterThan(0);

    await waitFor(() => {
      const smcCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/smc-performance"));
      expect(smcCalls.length).toBeGreaterThan(0);
    });
  });

  it("renders AI panel performance from the hourly lifecycle endpoint", async () => {
    renderPanel();

    expect(await screen.findByText("AI Panel Signal Performance")).toBeInTheDocument();
    expect(screen.getByText("Hourly Snapshots")).toBeInTheDocument();
    expect(screen.getAllByText("Saatlik Panel").length).toBeGreaterThan(0);

    await waitFor(() => {
      const aiCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/ai-panel-performance"));
      expect(aiCalls.length).toBeGreaterThan(0);
    });
  });

  it("shows the main scope tab before ultra safe and applies scope filters to recent signals", async () => {
    renderPanel();

    await screen.findByText("Strategy Performance Analysis");
    fireEvent.click(screen.getByRole("button", { name: "Signals Tab" }));

    const scopeTabs = await screen.findByTestId("signal-scope-tabs");
    const scopeText = scopeTabs.textContent || "";
    expect(scopeText.indexOf("Ham ML")).toBeGreaterThanOrEqual(0);
    expect(scopeText.indexOf("Ultra Güvenli")).toBeGreaterThanOrEqual(0);
    expect(scopeText.indexOf("Ham ML")).toBeLessThan(scopeText.indexOf("Ultra Güvenli"));

    await waitFor(() => {
      const recentCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/signals/recent"));
      expect(recentCalls.some((url) => url.includes("model=ml"))).toBe(true);
    });

    fireEvent.click(screen.getByRole("button", { name: "Ham ML Scope Tab" }));

    await waitFor(() => {
      const recentCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/signals/recent"));
      expect(recentCalls.some((url) => url.includes("strategy_scope=main"))).toBe(true);
    });

    fireEvent.change(screen.getByLabelText("Strategy Scope Filter"), { target: { value: "balanced" } });

    await waitFor(() => {
      const recentCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/signals/recent"));
      expect(recentCalls.some((url) => url.includes("strategy_scope=balanced"))).toBe(true);
    });
  });

  it("renders the full ordered scope stack for symbols even when no scopes are marked available", async () => {
    const { container } = renderPanel();

    expect((await screen.findAllByText("Best Signal Quality")).length).toBeGreaterThan(0);

    const daxHeading = Array.from(container.querySelectorAll("h4")).find((node) => node.textContent === "DAX");
    expect(daxHeading).toBeTruthy();

    const daxSection = daxHeading?.closest(".space-y-3") as HTMLElement | null;
    expect(daxSection).toBeTruthy();

    const daxText = daxSection?.textContent || "";
    expect(daxText.indexOf("Ham ML")).toBeGreaterThanOrEqual(0);
    expect(daxText.indexOf("Ultra Güvenli")).toBeGreaterThan(daxText.indexOf("Ham ML"));
    expect(daxText.indexOf("Dengeli")).toBeGreaterThan(daxText.indexOf("Ultra Güvenli"));
    expect(daxText.indexOf("Full Power")).toBeGreaterThan(daxText.indexOf("Dengeli"));
    expect(daxText.indexOf("Agresif")).toBeGreaterThan(daxText.indexOf("Full Power"));
    expect(daxText.indexOf("NASDAQ Precision")).toBeGreaterThan(daxText.indexOf("Agresif"));

    expect(within(daxSection as HTMLElement).getAllByText("0 signals · 0 resolved · 0 expired · 0 active").length).toBe(6);
  });

  it("applies symbol and day filters to recent signal requests", async () => {
    renderPanel();

    await screen.findByText("Strategy Performance Analysis");
    fireEvent.click(screen.getByRole("button", { name: "Signals Tab" }));

    fireEvent.change(screen.getByLabelText("Signal Symbol Filter"), { target: { value: "NDX.INDX" } });

    await waitFor(() => {
      const recentCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/signals/recent"));
      expect(recentCalls.some((url) => url.includes("symbol=NDX.INDX"))).toBe(true);
    });

    fireEvent.change(screen.getByLabelText("Days Filter"), { target: { value: "60" } });

    await waitFor(() => {
      const recentCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/learning/signals/recent"));
      expect(recentCalls.some((url) => url.includes("days=60"))).toBe(true);
    });
  });
});