// @ts-nocheck
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../lib/api/orderBlocks", () => ({
  useOrderBlockDetect: () => ({
    data: { order_blocks: [], active_signals: [], total_order_blocks: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../lib/api/fvg", () => ({
  useFVGDetect: () => ({
    data: { fvgs: [], total_fvgs: 0, unfilled_count: 0, nearest_bullish: null, nearest_bearish: null },
    isLoading: false,
    refetch: vi.fn(),
  }),
}));

vi.mock("../components/OrderBlockChart", () => ({
  default: () => <div data-testid="order-block-chart" />,
}));

import OrderBlockPanel from "../components/OrderBlockPanel";

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <OrderBlockPanel />
    </QueryClientProvider>
  );
}

describe("OrderBlockPanel", () => {
  it("renders heading", () => {
    renderPanel();
    expect(screen.getByText(/Order Block Detector/i)).toBeInTheDocument();
    expect(screen.getByTestId("order-block-chart")).toBeInTheDocument();
  });
});
