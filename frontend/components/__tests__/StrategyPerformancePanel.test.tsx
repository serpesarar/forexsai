import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import StrategyPerformancePanel from "../StrategyPerformancePanel";

vi.mock("@/lib/api/base", () => ({ getApiBase: () => "" }));
vi.mock("../PanelInfoButton", () => ({ PanelInfoButton: () => <div data-testid="panel-info" /> }));
vi.mock("../panels/ModelPerformanceModal", () => ({ ModelPerformanceModal: () => null }));
vi.mock("../SignalDetailModal", () => ({ default: () => null }));

const payload = {
  period_days: 30,
  strategies: {
    "NDX.INDX": {
      ultra_safe: {
        total_predictions: 5,
        with_outcome: 4,
        correct: 3,
        accuracy: 75,
        target_hit_rate: 75,
        stop_hit_rate: 25,
        avg_confidence: 68,
        target_hits: 3,
        stop_hits: 1,
        tp_breakdown: { TP1: 3, TP2: 2, TP3: 1, TP4: 0 },
        tp_hit_rates: { TP1: 75, TP2: 50, TP3: 25, TP4: 0 },
      },
    },
    XAUUSD: {},
    "GDAXI.INDX": {},
    "USOIL.FOREX": {},
  },
  best_strategies: {
    "NDX.INDX": { strategy: "ultra_safe", accuracy: 75 },
    XAUUSD: { strategy: null, accuracy: null },
    "GDAXI.INDX": { strategy: null, accuracy: null },
    "USOIL.FOREX": { strategy: null, accuracy: null },
  },
  strategy_descriptions: {
    ultra_safe: "Güven ≥65%, düşük risk",
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
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: string | URL) => {
        const url = String(input);
        if (url.includes("/api/learning/strategy-performance")) {
          return Promise.resolve({ ok: true, json: async () => payload });
        }
        if (url.includes("/api/learning/signals/recent")) {
          return Promise.resolve({ ok: true, json: async () => ({ signals: [], count: 0 }) });
        }
        return Promise.resolve({ ok: false, json: async () => ({ error: "unexpected" }) });
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders per-strategy TP1..TP4 hit rates independently", async () => {
    renderPanel();

    await screen.findByText("Strategy Performance Analysis");
    expect(await screen.findByText((_, el) => el?.textContent === "TP175%(3)")).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent === "TP250%(2)")).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent === "TP325%(1)")).toBeInTheDocument();
    expect(screen.getByText((_, el) => el?.textContent === "TP40%(0)")).toBeInTheDocument();
  });
});