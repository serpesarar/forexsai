"use client";

import { useCallback, useEffect, useState } from "react";

function formatRefreshAge(diffSeconds: number): string {
  const safeSeconds = Math.max(0, diffSeconds);
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;

  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function useRefreshAge(initialAt?: Date | null) {
  const [lastRefreshAt, setLastRefreshAt] = useState<number>(() => (initialAt ?? new Date()).getTime());
  const [refreshAge, setRefreshAge] = useState<string>("00:00");

  const markRefreshed = useCallback((at?: Date | string | number | null) => {
    if (at instanceof Date) {
      setLastRefreshAt(at.getTime());
      return;
    }

    if (typeof at === "string" || typeof at === "number") {
      const parsedAt = new Date(at).getTime();
      if (!Number.isNaN(parsedAt)) {
        setLastRefreshAt(parsedAt);
        return;
      }
    }

    setLastRefreshAt(Date.now());
  }, []);

  useEffect(() => {
    const tick = () => {
      const diffSeconds = Math.floor((Date.now() - lastRefreshAt) / 1000);
      setRefreshAge(formatRefreshAge(diffSeconds));
    };

    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [lastRefreshAt]);

  return {
    refreshAge,
    markRefreshed,
    lastRefreshAt,
  };
}
