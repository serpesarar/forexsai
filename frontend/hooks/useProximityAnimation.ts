import { useMemo } from "react";

interface ProximityAlert {
  supportProximity: boolean;
  resistanceProximity: boolean;
  ema20Proximity: boolean;
  supportIntensity: number;   // 0-1
  resistanceIntensity: number; // 0-1
  ema20Intensity: number;      // 0-1
}

export function useProximityAnimation(
  currentPrice: number,
  nearestSupport: number | null,
  nearestResistance: number | null,
  ema20: number | null,
  threshold: number = 0.02 // 2% default
): ProximityAlert {
  return useMemo(() => {
    const result: ProximityAlert = {
      supportProximity: false,
      resistanceProximity: false,
      ema20Proximity: false,
      supportIntensity: 0,
      resistanceIntensity: 0,
      ema20Intensity: 0,
    };

    if (!currentPrice || currentPrice === 0) return result;

    if (nearestSupport && nearestSupport > 0) {
      const dist = Math.abs(currentPrice - nearestSupport) / currentPrice;
      if (dist < threshold) {
        result.supportProximity = true;
        result.supportIntensity = Math.max(0, 1 - dist / threshold);
      }
    }

    if (nearestResistance && nearestResistance > 0) {
      const dist = Math.abs(currentPrice - nearestResistance) / currentPrice;
      if (dist < threshold) {
        result.resistanceProximity = true;
        result.resistanceIntensity = Math.max(0, 1 - dist / threshold);
      }
    }

    if (ema20 && ema20 > 0) {
      const dist = Math.abs(currentPrice - ema20) / currentPrice;
      if (dist < threshold) {
        result.ema20Proximity = true;
        result.ema20Intensity = Math.max(0, 1 - dist / threshold);
      }
    }

    return result;
  }, [currentPrice, nearestSupport, nearestResistance, ema20, threshold]);
}
