"use client";

import React, { useRef, useState, useEffect, Suspense, memo, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { PanelErrorBoundary } from "./ErrorBoundary";

interface LazyPanelProps {
  children: React.ReactNode;
  fallbackHeight?: number;
  rootMargin?: string;
}

/**
 * LazyPanel - Mounts children when the panel enters the viewport,
 * UNMOUNTS them after they leave the viewport for `unmountDelay` seconds.
 * This frees memory (timers, queries, chart instances) for invisible panels.
 *
 * - rootMargin controls how far before viewport the panel starts loading.
 * - unmountDelay prevents flickering during quick scroll (default 30s).
 * - Once rendered, shows a lightweight skeleton placeholder when unmounted.
 */
function LazyPanelInner({
  children,
  fallbackHeight = 200,
  rootMargin = "200px",
}: LazyPanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  // Track whether panel was ever rendered (to show nicer skeleton on unmount)
  const wasRendered = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { rootMargin }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin]);

  // Mount immediately when visible, and stay mounted forever to prevent layout shift
  useEffect(() => {
    if (isVisible) {
      setShouldRender(true);
      wasRendered.current = true;
    }
  }, [isVisible]);

  return (
    <div ref={ref}>
      {shouldRender ? (
        <PanelErrorBoundary>
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
        </PanelErrorBoundary>
      ) : (
        <div
          className="rounded-xl border border-white/5 bg-white/[0.02]"
          style={{ minHeight: wasRendered.current ? fallbackHeight : 100 }}
        />
      )}
    </div>
  );
}

export const LazyPanel = memo(LazyPanelInner);
