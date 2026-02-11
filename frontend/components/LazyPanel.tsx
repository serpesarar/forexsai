"use client";

import React, { useRef, useState, useEffect, Suspense, memo } from "react";
import { Loader2 } from "lucide-react";
import { PanelErrorBoundary } from "./ErrorBoundary";

interface LazyPanelProps {
  children: React.ReactNode;
  fallbackHeight?: number;
  rootMargin?: string;
}

/**
 * LazyPanel - Only renders children when the panel first enters the viewport.
 * Once rendered, panels stay mounted PERMANENTLY to avoid expensive re-renders
 * and data re-fetches on scroll. Uses IntersectionObserver for initial load only.
 */
function LazyPanelInner({ children, fallbackHeight = 200, rootMargin = "800px" }: LazyPanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShouldRender(true);
          observer.disconnect(); // Once triggered, never observe again
        }
      },
      { rootMargin }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin]);

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
          style={{ minHeight: 100 }}
        />
      )}
    </div>
  );
}

export const LazyPanel = memo(LazyPanelInner);
