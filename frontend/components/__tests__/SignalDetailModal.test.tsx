import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";

import SignalDetailModal from "../SignalDetailModal";

const detailPayload = {
  signal: {
    id: "sig-1",
    symbol: "NDX.INDX",
    ml_direction: "BUY",
    ml_confidence: 48,
    ml_entry_price: 100,
    ml_target_price: 110,
    ml_stop_price: 95,
    stop_loss_pips: 50,
    status: "stopped",
    targets_hit: {},
    highest_profit_pips: 0,
    lowest_drawdown_pips: -50,
    created_at: "2026-03-07T10:00:00Z",
    exit_time: "2026-03-07T10:30:00Z",
  },
  checks: [],
};

describe("SignalDetailModal", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => detailPayload })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows stopped losses as negative result even without exit price", async () => {
    render(<SignalDetailModal signalId="sig-1" isOpen onClose={vi.fn()} />);

    await screen.findByText("Stopped (SL Hit)");
    expect(screen.getAllByText("-50.0 pips").length).toBeGreaterThan(0);
  });
});