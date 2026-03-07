import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ModelPerformanceModal } from "../ModelPerformanceModal";

vi.mock("framer-motion", () => {
  const Div = ({ children, ...props }: any) => <div {...props}>{children}</div>;
  return { AnimatePresence: ({ children }: any) => <>{children}</>, motion: { div: Div } };
});

vi.mock("recharts", () => {
  const Box = ({ children }: any) => <div>{children}</div>;
  return {
    Bar: Box,
    BarChart: Box,
    CartesianGrid: Box,
    Cell: Box,
    Line: Box,
    LineChart: Box,
    ResponsiveContainer: Box,
    Tooltip: Box,
    XAxis: Box,
    YAxis: Box,
  };
});

const basePayload = {
  model: "all",
  symbol: "NDX.INDX",
  overview: {
    total_signals: 12,
    win_rate: 58.3,
    completed: 7,
    stopped: 5,
    expired: 0,
    active: 1,
    net_pips: 42.5,
    avg_profit_pips: 12,
    avg_loss_pips: -7,
    risk_reward: 1.7,
    sharpe_ratio: 1.2,
    max_drawdown_pips: 18,
    profit_factor: 1.9,
  },
  hourly_heatmap: [
    { hour: 8, total: 4, wins: 3, win_rate: 75, avg_pips: 6.5 },
    { hour: 12, total: 3, wins: 1, win_rate: 33.3, avg_pips: -2.1 },
  ],
  timeframe_comparison: [
    { tf: "5m", total: 6, active: 0, win_rate: 50, net_pips: 12, avg_pips: 2 },
    { tf: "15m", total: 4, active: 0, win_rate: 75, net_pips: 18, avg_pips: 4.5 },
  ],
  daily_accuracy: [],
  day_of_week: [
    { day: "Monday", day_short: "Mon", total: 5, wins: 3, win_rate: 60, avg_pips: 3.1 },
    { day: "Tuesday", day_short: "Tue", total: 4, wins: 3, win_rate: 75, avg_pips: 5.4 },
  ],
  tp_hit_rates: { TP1: 70 },
  recent_signals: [],
  selected_timeframe: "all",
  available_timeframes: ["5m", "15m"],
  available_models: ["ml", "pulse1"],
  model_comparison: [{ model: "ml", total: 12, win_rate: 58.3, net_pips: 42.5, avg_pips: 3.5 }],
  meta: {
    selected_model: "all",
    selected_timeframe: "all",
    all_time: true,
    filtered_total_signals: 12,
    scope_total_signals: 12,
    date_from: "2026-01-01T00:00:00Z",
    date_to: "2026-02-01T00:00:00Z",
    hourly_visible_hours: [8, 9, 10, 11, 12, 13],
    hourly_window_label: "08:00–13:00 UTC",
  },
};

function renderModal(props?: Partial<React.ComponentProps<typeof ModelPerformanceModal>>) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ModelPerformanceModal isOpen onClose={vi.fn()} symbol="NDX.INDX" model="all" {...props} />
    </QueryClientProvider>
  );
}

describe("ModelPerformanceModal", () => {
  beforeEach(() => {
    localStorage.setItem("language", "en");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => basePayload })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("adds selected timeframe and days scope to analytics requests", async () => {
    renderModal({ days: 30 });

    await screen.findByText("Performance analytics");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("model=all")
    );
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("days=30")
    );

    fireEvent.click(await screen.findByRole("button", { name: "15M" }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("timeframe=15m")
      );
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("days=30")
      );
    });
  });

  it("shows retryable error state when analytics request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: "Failed analytics" }) })
    );

    renderModal();

    expect(await screen.findByText("Failed analytics")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Retry" }).length).toBeGreaterThan(0);
    expect(screen.queryByText("No resolved signal history was found for this scope.")).not.toBeInTheDocument();
  });

  it("keeps warning payloads visible when analytics data still exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...basePayload, error: "Partial analytics warning" }) })
    );

    renderModal();

    expect(await screen.findByText("Partial analytics warning")).toBeInTheDocument();
    expect(screen.getByText("Insight pulse")).toBeInTheDocument();
  });

  it("renders premium insight summary tiles", async () => {
    renderModal();

    expect(await screen.findByText("Insight pulse")).toBeInTheDocument();
    expect(screen.getByText("Strong edge")).toBeInTheDocument();
    expect(screen.getByText("Best hour")).toBeInTheDocument();
    expect(screen.getByText("Best day")).toBeInTheDocument();
  });

  it("uses backend session-hour visibility contract in the hourly tab", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...basePayload,
          hourly_heatmap: [
            { hour: 0, total: 3, wins: 1, win_rate: 33.3, avg_pips: -1 },
            { hour: 9, total: 2, wins: 1, win_rate: 50, avg_pips: 4 },
            { hour: 10, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
            { hour: 11, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
            { hour: 12, total: 2, wins: 1, win_rate: 50, avg_pips: 6 },
            { hour: 13, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
            { hour: 14, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
            { hour: 15, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
            { hour: 16, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
            { hour: 17, total: 0, wins: 0, win_rate: 0, avg_pips: 0 },
          ],
          meta: {
            ...basePayload.meta,
            hourly_visible_hours: [9, 10, 11, 12, 13, 14, 15, 16, 17],
            hourly_window_label: "09:00–17:00",
          },
        }),
      })
    );

    renderModal();

    await screen.findByText("Performance analytics");
    fireEvent.click(screen.getByRole("button", { name: "Hourly" }));

    expect(await screen.findByText("Session window: 09:00–17:00")).toBeInTheDocument();
    expect(screen.getAllByText("09:00").length).toBeGreaterThan(0);
    expect(screen.getAllByText("17:00").length).toBeGreaterThan(0);
    expect(screen.queryByText("00:00")).not.toBeInTheDocument();
  });

  it("closes when escape is pressed", async () => {
    const onClose = vi.fn();
    renderModal({ onClose });

    await screen.findByText("Performance analytics");
    fireEvent.keyDown(window, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});