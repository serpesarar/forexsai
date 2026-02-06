"use client";

import React, { useRef, useState, useEffect, Suspense, memo } from "react";
import { Loader2 } from "lucide-react";

interface LazyPanelProps {
  children: React.ReactNode;
  fallbackHeight?: number;
  rootMargin?: string;
}

/**
 * LazyPanel - Only renders children when the panel is near the viewport.
 * When scrolled away, it unmounts children to free memory and stop polling.
 * Uses IntersectionObserver with a generous rootMargin so panels pre-load
 * before they're visible (no flash of loading state during normal scroll).
 */
function LazyPanelInner({ children, fallbackHeight = 200, rootMargin = "600px" }: LazyPanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [hasBeenVisible, setHasBeenVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        const nowVisible = entry.isIntersecting;
        setIsVisible(nowVisible);
        if (nowVisible) setHasBeenVisible(true);
      },
      { rootMargin }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin]);

  // Keep panel mounted for 30s after scrolling away (avoids re-fetch on quick scroll back)
  const [shouldRender, setShouldRender] = useState(false);
  const unmountTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (isVisible) {
      if (unmountTimer.current) {
        clearTimeout(unmountTimer.current);
        unmountTimer.current = null;
      }
      setShouldRender(true);
    } else if (hasBeenVisible) {
      // Delay unmount by 30s so quick scroll-backs don't cause re-render
      unmountTimer.current = setTimeout(() => {
        setShouldRender(false);
      }, 30000);
    }
    return () => {
      if (unmountTimer.current) clearTimeout(unmountTimer.current);
    };
  }, [isVisible, hasBeenVisible]);

  return (
    <div ref={ref}>
      {shouldRender ? (
        <Suspense
          fallback={
            <div
              className="flex items-center justify-center rounded-xl border border-white/5 bg-white/[0.02]"
              style={{ minHeight: fallbackHeight }}
            >
              <Loader2 className="h-6 w-6 animate-spin text-white/20" />
            </div>
          }
        >
          {children}
        </Suspense>
      ) : (
        <div
          className="rounded-xl border border-white/5 bg-white/[0.02]"
          style={{ minHeight: hasBeenVisible ? fallbackHeight : 100 }}
        />
      )}
    </div>
  );
}

export const LazyPanel = memo(LazyPanelInner);
