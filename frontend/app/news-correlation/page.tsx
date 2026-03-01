"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";

// Dynamic import for heavy panel component
const NewsChartCorrelationPanel = dynamic(
  () => import("@/components/panels/NewsChartCorrelationPanel"),
  {
    ssr: false,
    loading: () => (
      <div className="h-[600px] w-full bg-slate-950 rounded-xl border border-slate-800 p-4">
        <Skeleton className="h-full w-full bg-slate-900" />
      </div>
    ),
  }
);

export default function NewsCorrelationPage() {
  return (
    <div className="min-h-screen bg-slate-950 p-4 md:p-6">
      <div className="max-w-[1600px] mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
          <span className="bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            News-Chart Correlation
          </span>
          <span className="text-sm font-normal text-slate-400">
            AI-powered news analysis on charts
          </span>
        </h1>
        
        <Suspense
          fallback={
            <div className="h-[600px] w-full bg-slate-950 rounded-xl border border-slate-800 p-4">
              <Skeleton className="h-full w-full bg-slate-900" />
            </div>
          }
        >
          <NewsChartCorrelationPanel />
        </Suspense>
      </div>
    </div>
  );
}
