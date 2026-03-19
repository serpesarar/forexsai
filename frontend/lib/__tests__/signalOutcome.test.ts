import { describe, expect, it } from "vitest";

import { deriveSignalExitPrice, deriveSignalPnlPips, deriveSummaryExitPrice } from "../signalOutcome";

describe("signalOutcome helpers", () => {
  it("derives completed target-hit pnl and exit from the highest hit target when raw exit is stale", () => {
    const signal = {
      symbol: "NDX.INDX",
      status: "completed",
      resolution_reason: "tp4_hit",
      ml_direction: "BUY",
      ml_entry_price: 24355.3,
      exit_price: 24355.3,
      highest_profit_pips: 0,
      targets: {
        TP1: 24370.2754,
        TP2: 24380.2754,
        TP3: 24390.2754,
        TP4: 24405.2754,
      },
      targets_hit: {
        TP1: true,
        TP2: true,
        TP3: true,
        TP4: true,
      },
    };

    expect(deriveSignalExitPrice(signal)).toBe(24405.2754);
    expect(deriveSignalPnlPips(signal)).toBe(49.9754);
  });

  it("derives stopped pnl from stop loss settings", () => {
    const signal = {
      symbol: "GDAXI.INDX",
      status: "stopped",
      ml_direction: "SELL",
      ml_entry_price: 22839.6,
      stop_loss_pips: 50,
      exit_price: 22889.6,
    };

    expect(deriveSignalPnlPips(signal)).toBe(-50);
    expect(deriveSignalExitPrice(signal)).toBe(22889.6);
  });

  it("derives recent summary exit from entry and pips when backend exit is stale", () => {
    const summary = {
      status: "completed",
      direction: "BUY",
      entry_price: 24355.3,
      exit_price: 24355.3,
      pips: 50.0,
    };

    expect(deriveSummaryExitPrice(summary)).toBe(24405.3);
  });
});
