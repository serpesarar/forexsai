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
    expect(await screen.findByText("Best Signal Quality")).toBeInTheDocument();
    expect(screen.getAllByText("Ham ML").length).toBeGreaterThan(0);
    expect(screen.getByText(/Ham\/orijinal ML akışı/)).toBeInTheDocument();
    expect(screen.getAllByText("Agresif").length).toBeGreaterThan(0);
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

    await screen.findByText("Best Signal Quality");

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