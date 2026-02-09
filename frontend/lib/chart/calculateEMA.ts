/**
 * EMA Calculation Utility with Proximity Detection
 * Used by NeonChart for cyberpunk-style EMA visualization
 */

export interface EMAResult {
  values: (number | null)[];
  period: number;
  latestValue: number | null;
}

export interface ProximityAlert {
  emaLabel: string;
  emaPeriod: number;
  emaValue: number;
  priceValue: number;
  distance: number;
  distancePercent: number;
  isCross: boolean;
  crossType: "golden" | "death" | null;
}

/**
 * Calculate EMA for given close prices
 */
export function calculateEMA(values: number[], period: number): (number | null)[] {
  if (values.length === 0) return [];
  const k = 2 / (period + 1);
  const ema: (number | null)[] = [];
  let previous: number | null = null;

  values.forEach((value, index) => {
    if (index < period - 1) {
      ema.push(null);
      return;
    }
    if (previous === null) {
      const slice = values.slice(index - period + 1, index + 1);
      const avg = slice.reduce((sum, val) => sum + val, 0) / period;
      previous = avg;
      ema.push(avg);
      return;
    }
    const next = (value - previous) * k + previous;
    previous = next;
    ema.push(next);
  });

  return ema;
}

/**
 * Calculate all EMAs (20, 50, 200) and return structured results
 */
export function calculateAllEMAs(
  closes: number[]
): Record<number, EMAResult> {
  const periods = [20, 50, 200];
  const result: Record<number, EMAResult> = {};

  for (const period of periods) {
    const values = calculateEMA(closes, period);
    result[period] = {
      values,
      period,
      latestValue: values.length > 0 ? values[values.length - 1] : null,
    };
  }

  return result;
}

/**
 * Detect proximity between current price and EMA values
 * Returns alerts for EMAs that are within threshold
 */
export function detectProximity(
  currentPrice: number,
  emaResults: Record<number, EMAResult>,
  prevCloses: number[],
  thresholdPercent: number = 0.15
): ProximityAlert[] {
  const alerts: ProximityAlert[] = [];
  const labels: Record<number, string> = { 20: "EMA20", 50: "EMA50", 200: "EMA200" };

  for (const [periodStr, ema] of Object.entries(emaResults)) {
    const period = Number(periodStr);
    if (ema.latestValue === null) continue;

    const distance = Math.abs(currentPrice - ema.latestValue);
    const distancePercent = (distance / currentPrice) * 100;

    // Check for cross (price crossed EMA between last two candles)
    let isCross = false;
    let crossType: "golden" | "death" | null = null;

    if (prevCloses.length >= 2 && ema.values.length >= 2) {
      const prevPrice = prevCloses[prevCloses.length - 2];
      const prevEma = ema.values[ema.values.length - 2];
      if (prevEma !== null) {
        const wasBelowEma = prevPrice < prevEma;
        const isAboveEma = currentPrice > ema.latestValue;
        if (wasBelowEma && isAboveEma) {
          isCross = true;
          crossType = "golden";
        } else if (!wasBelowEma && !isAboveEma) {
          isCross = true;
          crossType = "death";
        }
      }
    }

    if (distancePercent <= thresholdPercent || isCross) {
      alerts.push({
        emaLabel: labels[period] || `EMA${period}`,
        emaPeriod: period,
        emaValue: ema.latestValue,
        priceValue: currentPrice,
        distance,
        distancePercent,
        isCross,
        crossType,
      });
    }
  }

  return alerts;
}
