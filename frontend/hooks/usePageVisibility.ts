"use client";

import { useState, useEffect } from "react";

/**
 * Returns true when the browser tab is visible, false when hidden.
 * Use this to pause polling/intervals when user switches tabs.
 */
export function usePageVisibility(): boolean {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const handleVisibility = () => {
      setIsVisible(document.visibilityState === "visible");
    };

    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  return isVisible;
}
