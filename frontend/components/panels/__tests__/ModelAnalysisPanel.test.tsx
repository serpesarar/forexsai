import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import ModelAnalysisPanel from "../ModelAnalysisPanel";

vi.mock("@/lib/api/base", () => ({ getApiBase: () => "" }));
vi.mock("../ModelPerformanceModal", () => ({ ModelPerformanceModal: () => null }));

const summaryPayload = {
  ml: {
    total_signals: 5,
    overall_win_rate: 60,
    total_completed: 3,
    total_stopped: 2,
    by_timeframe: {
      "5m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "15m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 5, completed: 3, stopped: 2, expired: 0, win_rate: 60 },
      "4h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
  emel: {
    total_signals: 4,
    overall_win_rate: 50,
    total_completed: 2,
    total_stopped: 2,
    by_timeframe: {
      "5m": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "15m": { total: 1, completed: 0, stopped: 1, expired: 0, win_rate: 0 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "4h": { total: 1, completed: 0, stopped: 1, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
  emel_inverse: {
    total_signals: 3,
    overall_win_rate: 66.7,
    total_completed: 2,
    total_stopped: 1,
    by_timeframe: {
      "5m": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "15m": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 1, completed: 0, stopped: 1, expired: 0, win_rate: 0 },
      "4h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
  pulse1: {
    total_signals: 2,
    overall_win_rate: 50,
    total_completed: 1,
    total_stopped: 1,
    by_timeframe: {
      "5m": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "15m": { total: 1, completed: 0, stopped: 1, expired: 0, win_rate: 0 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "4h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
  pulse2: {
    total_signals: 2,
    overall_win_rate: 50,
    total_completed: 1,
    total_stopped: 1,
    by_timeframe: {
      "5m": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "15m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 1, completed: 0, stopped: 1, expired: 0, win_rate: 0 },
      "4h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
  pulse3: {
    total_signals: 1,
    overall_win_rate: 100,
    total_completed: 1,
    total_stopped: 0,
    by_timeframe: {
      "5m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "15m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "4h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
  smc: {
    total_signals: 3,
    overall_win_rate: 50,
    total_completed: 1,
    total_stopped: 1,
    by_timeframe: {
      "5m": { total: 1, completed: 1, stopped: 0, expired: 0, win_rate: 100 },
      "15m": { total: 1, completed: 0, stopped: 1, expired: 0, win_rate: 0 },
      "30m": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1h": { total: 1, completed: 0, stopped: 0, expired: 1, win_rate: 0 },
      "4h": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
      "1d": { total: 0, completed: 0, stopped: 0, expired: 0, win_rate: 0 },
    },
  },
};

const matrixPayload = {
  matrix: {
    "NDX.INDX": {
      "5m": { direction: "BUY", confidence: 72, status: "active", age_hours: 1 },
      "15m": { direction: "SELL", confidence: 61, status: "active", age_hours: 2 },
      "1h": { direction: "BUY", confidence: 68, status: "active", age_hours: 3 },
      "4h": { direction: "BUY", confidence: 74, status: "active", age_hours: 4 },
    },
  },
};

const analysisPayload = {
  total_signals: 3,
  completed: 1,
  stopped: 1,
  expired: 1,
  win_rate: 50,
  target_rates: { TP1: 50, TP2: 0, TP3: 0, TP4: 0 },
  total_profit_pips: 8,
  total_loss_pips: 4,
  net_pips: 4,
  avg_profit_pips: 8,
  avg_loss_pips: 4,
  max_profit_pips: 8,
  max_loss_pips: 4,
  risk_reward: 2,
  by_symbol: {
    "NDX.INDX": { total: 3, completed: 1, stopped: 1, net_pips: 4 },
  },
  by_timeframe: {
    "5m": { total: 1, completed: 1, stopped: 0, win_rate: 100 },
    "15m": { total: 1, completed: 0, stopped: 1, win_rate: 0 },
    "1h": { total: 1, completed: 0, stopped: 0, win_rate: 0 },
  },
  signals: [],
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ModelAnalysisPanel />
    </QueryClientProvider>
  );
}

describe("ModelAnalysisPanel", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockImplementation((input: string | URL) => {
      const url = String(input);
      if (url.includes("/api/learning/model-analysis/summary")) {
        return Promise.resolve({ ok: true, json: async () => ({ models: summaryPayload }) });
      }
      if (url.includes("/api/learning/signals/matrix")) {
        return Promise.resolve({ ok: true, json: async () => matrixPayload });
      }
      if (url.includes("/api/learning/model-analysis?")) {
        return Promise.resolve({ ok: true, json: async () => analysisPayload });
      }
      return Promise.resolve({ ok: false, json: async () => ({ error: "unexpected" }) });
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("includes Smart Money Zones in the model selector and requests smc analytics when selected", async () => {
    renderPanel();

    expect(await screen.findByText("Model Analysis")).toBeInTheDocument();
    const smcCard = await screen.findByRole("button", { name: /Smart Money Zones/i });
    expect(smcCard).toBeInTheDocument();

    fireEvent.click(smcCard);

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(calls.some((url) => url.includes("/api/learning/signals/matrix?model=smc"))).toBe(true);
      expect(calls.some((url) => url.includes("/api/learning/model-analysis?model=smc"))).toBe(true);
    });
  });
});
