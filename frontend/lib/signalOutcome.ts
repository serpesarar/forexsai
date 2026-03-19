type SignalLike = {
  symbol?: string | null;
  status?: string | null;
  normalized_status?: string | null;
  resolution_reason?: string | null;
  ml_direction?: string | null;
  ml_entry_price?: number | null;
  ml_stop_price?: number | null;
  exit_price?: number | null;
  calculated_pnl_pips?: number | null;
  highest_profit_pips?: number | null;
  lowest_drawdown_pips?: number | null;
  stop_loss_pips?: number | null;
  targets?: Record<string, number> | null;
  targets_hit?: Record<string, boolean> | null;
};

type SummarySignalLike = {
  status?: string | null;
  direction?: string | null;
  entry_price?: number | null;
  exit_price?: number | null;
  pips?: number | null;
};

const TP_LEVELS = ["TP4", "TP3", "TP2", "TP1"] as const;
const TARGET_RESOLUTION_REASONS = new Set(["tp4_hit", "tp1_3_hit_then_sl", "all_targets_hit"]);

function coerceNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function roundPrice(value: number | null): number | null {
  if (value === null) {
    return null;
  }
  return Math.round(value * 10000) / 10000;
}

function getDisplayStatus(signal: SignalLike): string {
  return String(signal.normalized_status || signal.status || "").toLowerCase().trim();
}

function getResolutionReason(signal: SignalLike): string {
  return String(signal.resolution_reason || "").toLowerCase().trim();
}

function getDirection(signal: SignalLike | SummarySignalLike): "BUY" | "SELL" | null {
  const rawDirection = "ml_direction" in signal
    ? signal.ml_direction
    : "direction" in signal
      ? signal.direction
      : null;
  const value = String(rawDirection || "").toUpperCase().trim();
  return value === "BUY" || value === "SELL" ? value : null;
}

function getHighestHitTargetPrice(signal: SignalLike): number | null {
  const targets = signal.targets || {};
  const targetsHit = signal.targets_hit || {};
  const resolutionReason = getResolutionReason(signal);

  for (const level of TP_LEVELS) {
    const targetPrice = coerceNumber(targets[level]);
    if (targetPrice === null) {
      continue;
    }
    if (targetsHit[level]) {
      return targetPrice;
    }
    if (level === "TP4" && (resolutionReason === "tp4_hit" || resolutionReason === "all_targets_hit")) {
      return targetPrice;
    }
  }

  return null;
}

function derivePnlFromExit(entryPrice: number, exitPrice: number, direction: "BUY" | "SELL"): number {
  const delta = direction === "BUY" ? exitPrice - entryPrice : entryPrice - exitPrice;
  return Math.round(delta * 10000) / 10000;
}

export function deriveSignalPnlPips(signal: SignalLike): number | null {
  const calculated = coerceNumber(signal.calculated_pnl_pips);
  if (calculated !== null) {
    return calculated;
  }

  const displayStatus = getDisplayStatus(signal);
  const direction = getDirection(signal);
  const entryPrice = coerceNumber(signal.ml_entry_price);
  const targetExitPrice = getHighestHitTargetPrice(signal);
  const rawExitPrice = coerceNumber(signal.exit_price);

  if (displayStatus === "completed") {
    if (entryPrice !== null && direction && targetExitPrice !== null) {
      return derivePnlFromExit(entryPrice, targetExitPrice, direction);
    }
    if (entryPrice !== null && direction && rawExitPrice !== null) {
      return derivePnlFromExit(entryPrice, rawExitPrice, direction);
    }
    const highestProfit = coerceNumber(signal.highest_profit_pips);
    return highestProfit !== null ? Math.max(highestProfit, 0) : 0;
  }

  if (displayStatus === "stopped") {
    const stopLossPips = coerceNumber(signal.stop_loss_pips);
    if (stopLossPips !== null) {
      return -Math.abs(stopLossPips);
    }
    if (entryPrice !== null && direction && rawExitPrice !== null) {
      return derivePnlFromExit(entryPrice, rawExitPrice, direction);
    }
    const drawdown = coerceNumber(signal.lowest_drawdown_pips);
    return drawdown !== null ? -Math.abs(drawdown) : 0;
  }

  if (displayStatus === "expired") {
    return 0;
  }

  return null;
}

export function deriveSignalExitPrice(signal: SignalLike): number | null {
  const displayStatus = getDisplayStatus(signal);
  const targetExitPrice = getHighestHitTargetPrice(signal);
  const rawExitPrice = coerceNumber(signal.exit_price);
  const entryPrice = coerceNumber(signal.ml_entry_price);
  const pnlPips = deriveSignalPnlPips(signal);
  const direction = getDirection(signal);
  const stopPrice = coerceNumber(signal.ml_stop_price);

  if (displayStatus === "completed" && targetExitPrice !== null) {
    return roundPrice(targetExitPrice);
  }

  if (displayStatus === "stopped" && stopPrice !== null) {
    return roundPrice(stopPrice);
  }

  if (rawExitPrice !== null && (!TARGET_RESOLUTION_REASONS.has(getResolutionReason(signal)) || displayStatus !== "completed")) {
    return roundPrice(rawExitPrice);
  }

  if (entryPrice !== null && pnlPips !== null && direction) {
    const derivedExitPrice = direction === "BUY" ? entryPrice + pnlPips : entryPrice - pnlPips;
    return roundPrice(derivedExitPrice);
  }

  return roundPrice(rawExitPrice);
}

export function deriveSummaryExitPrice(signal: SummarySignalLike): number | null {
  const entryPrice = coerceNumber(signal.entry_price);
  const rawExitPrice = coerceNumber(signal.exit_price);
  const pnlPips = coerceNumber(signal.pips);
  const direction = getDirection(signal);
  const status = String(signal.status || "").toLowerCase().trim();

  if (entryPrice !== null && pnlPips !== null && direction && status !== "active") {
    const derivedExitPrice = direction === "BUY" ? entryPrice + pnlPips : entryPrice - pnlPips;
    return roundPrice(derivedExitPrice);
  }

  return roundPrice(rawExitPrice);
}
