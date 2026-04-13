"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

// Refresh intervals per model type (in seconds)
const DEFAULT_REFRESH_INTERVALS: Record<string, number> = {
  clear_trend: 120,    // 2 minutes
  pulse_v3: 300,       // 5 minutes
  emel: 300,           // 5 minutes
  mtf: 300,            // 5 minutes
  pulse1: 300,         // 5 minutes
  pulse2: 300,         // 5 minutes
  default: 120,        // 2 minutes default
};

interface CountdownState {
  /** Time remaining in seconds */
  remainingSeconds: number;
  /** Percentage of time elapsed (0-100) */
  progressPercent: number;
  /** Whether countdown is in "warning" phase (< 30% remaining) */
  isWarning: boolean;
  /** Whether countdown is in "critical" phase (< 10% remaining) */
  isCritical: boolean;
  /** Formatted time string MM:SS */
  formattedTime: string;
  /** Whether the countdown is active */
  isActive: boolean;
}

function formatTime(totalSeconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/**
 * Hook that provides a countdown timer for signal refresh
 * Counts down from the refresh interval to 0, then resets on signal refresh
 */
export function useSignalCountdown(
  modelKey: string,
  refreshIntervalSeconds?: number,
  signalTimestamp?: string | Date | null
): CountdownState & { markRefreshed: () => void } {
  const interval = useMemo(() => {
    if (refreshIntervalSeconds && refreshIntervalSeconds > 0) {
      return refreshIntervalSeconds;
    }
    return DEFAULT_REFRESH_INTERVALS[modelKey] || DEFAULT_REFRESH_INTERVALS.default;
  }, [modelKey, refreshIntervalSeconds]);

  const [nextRefreshAt, setNextRefreshAt] = useState<number>(() => {
    // If we have a signal timestamp, calculate next refresh from that
    if (signalTimestamp) {
      const signalTime = new Date(signalTimestamp).getTime();
      if (!Number.isNaN(signalTime)) {
        return signalTime + interval * 1000;
      }
    }
    return Date.now() + interval * 1000;
  });

  const [now, setNow] = useState<number>(Date.now());

  // Update countdown every second
  useEffect(() => {
    const tick = () => setNow(Date.now());
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, []);

  // Calculate countdown state
  const remainingMs = Math.max(0, nextRefreshAt - now);
  const remainingSeconds = Math.floor(remainingMs / 1000);
  const elapsedSeconds = interval - remainingSeconds;
  const progressPercent = Math.min(100, Math.max(0, (elapsedSeconds / interval) * 100));
  const isWarning = remainingSeconds <= interval * 0.3 && remainingSeconds > interval * 0.1;
  const isCritical = remainingSeconds <= interval * 0.1;
  const isActive = remainingSeconds > 0;

  const markRefreshed = useCallback(() => {
    setNextRefreshAt(Date.now() + interval * 1000);
  }, [interval]);

  // Auto-reset when countdown reaches 0 (signal should have refreshed)
  useEffect(() => {
    if (remainingSeconds === 0) {
      // Add small delay before resetting to show "REFRESHING" state briefly
      const timeout = setTimeout(() => {
        setNextRefreshAt(Date.now() + interval * 1000);
      }, 2000);
      return () => clearTimeout(timeout);
    }
  }, [remainingSeconds, interval]);

  return {
    remainingSeconds,
    progressPercent,
    isWarning,
    isCritical,
    formattedTime: remainingSeconds === 0 ? "YENİLENİYOR" : formatTime(remainingSeconds),
    isActive,
    markRefreshed,
  };
}

/**
 * Hook that manages countdowns for multiple models simultaneously
 * Useful for panels that display data from multiple sources
 */
export function useMultiSignalCountdown(
  configs: Array<{
    modelKey: string;
    refreshIntervalSeconds?: number;
    signalTimestamp?: string | Date | null;
  }>
): Record<string, CountdownState & { markRefreshed: () => void }> {
  const [modelStates, setModelStates] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    const now = Date.now();
    configs.forEach((config) => {
      const interval = config.refreshIntervalSeconds || 
        DEFAULT_REFRESH_INTERVALS[config.modelKey] || 
        DEFAULT_REFRESH_INTERVALS.default;
      if (config.signalTimestamp) {
        const signalTime = new Date(config.signalTimestamp).getTime();
        if (!Number.isNaN(signalTime)) {
          initial[config.modelKey] = signalTime + interval * 1000;
          return;
        }
      }
      initial[config.modelKey] = now + interval * 1000;
    });
    return initial;
  });

  const [now, setNow] = useState<number>(Date.now());

  useEffect(() => {
    const tick = () => setNow(Date.now());
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const markRefreshed = useCallback((modelKey: string) => {
    const config = configs.find((c) => c.modelKey === modelKey);
    const interval = config?.refreshIntervalSeconds || 
      DEFAULT_REFRESH_INTERVALS[modelKey] || 
      DEFAULT_REFRESH_INTERVALS.default;
    setModelStates((prev) => ({
      ...prev,
      [modelKey]: Date.now() + interval * 1000,
    }));
  }, [configs]);

  // Auto-reset expired countdowns
  useEffect(() => {
    const expiredModels = Object.entries(modelStates)
      .filter(([_, nextRefresh]) => nextRefresh <= now)
      .map(([key]) => key);

    if (expiredModels.length > 0) {
      const timeout = setTimeout(() => {
        setModelStates((prev) => {
          const next = { ...prev };
          expiredModels.forEach((key) => {
            const config = configs.find((c) => c.modelKey === key);
            const interval = config?.refreshIntervalSeconds || 
              DEFAULT_REFRESH_INTERVALS[key] || 
              DEFAULT_REFRESH_INTERVALS.default;
            next[key] = Date.now() + interval * 1000;
          });
          return next;
        });
      }, 2000);
      return () => clearTimeout(timeout);
    }
  }, [modelStates, now, configs]);

  // Build result object
  return useMemo(() => {
    const result: Record<string, CountdownState & { markRefreshed: () => void }> = {};
    
    configs.forEach((config) => {
      const interval = config.refreshIntervalSeconds || 
        DEFAULT_REFRESH_INTERVALS[config.modelKey] || 
        DEFAULT_REFRESH_INTERVALS.default;
      const nextRefreshAt = modelStates[config.modelKey] || Date.now() + interval * 1000;
      const remainingMs = Math.max(0, nextRefreshAt - now);
      const remainingSeconds = Math.floor(remainingMs / 1000);
      const elapsedSeconds = interval - remainingSeconds;
      const progressPercent = Math.min(100, Math.max(0, (elapsedSeconds / interval) * 100));
      const isWarning = remainingSeconds <= interval * 0.3 && remainingSeconds > interval * 0.1;
      const isCritical = remainingSeconds <= interval * 0.1;
      const isActive = remainingSeconds > 0;

      result[config.modelKey] = {
        remainingSeconds,
        progressPercent,
        isWarning,
        isCritical,
        formattedTime: remainingSeconds === 0 ? "YENİLENİYOR" : formatTime(remainingSeconds),
        isActive,
        markRefreshed: () => markRefreshed(config.modelKey),
      };
    });

    return result;
  }, [configs, modelStates, now, markRefreshed]);
}
