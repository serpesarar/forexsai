import { useState, useCallback, useEffect } from "react";

/**
 * Hook for toggling a panel into fullscreen mode.
 * When active, the panel covers the entire viewport.
 */
export function useFullscreen() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(async (target?: unknown) => {
    const element = target instanceof HTMLElement ? target : null;

    try {
      if (typeof document !== "undefined" && document.fullscreenElement) {
        await document.exitFullscreen();
        setIsFullscreen(false);
        return;
      }

      if (element && element.requestFullscreen) {
        await element.requestFullscreen();
        setIsFullscreen(true);
        return;
      }
    } catch {
      // Fall back to CSS-based fullscreen state below.
    }

    setIsFullscreen((prev) => !prev);
  }, []);

  const exitFullscreen = useCallback(async () => {
    try {
      if (typeof document !== "undefined" && document.fullscreenElement) {
        await document.exitFullscreen();
      }
    } catch {
      // Fall back to local state below.
    }
    setIsFullscreen(false);
  }, []);

  // Sync with native browser fullscreen state.
  useEffect(() => {
    if (typeof document === "undefined") return;

    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  // ESC key support for CSS fallback mode and body scroll lock.
  useEffect(() => {
    if (!isFullscreen) return;

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        void exitFullscreen();
      }
    };

    window.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [exitFullscreen, isFullscreen]);

  return { isFullscreen, toggleFullscreen, exitFullscreen };
}
