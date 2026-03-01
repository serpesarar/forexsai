"use client";

import dynamic from "next/dynamic";

// Dynamic import with simple loading
const NewsChartCorrelationPanel = dynamic(
  () => import("@/components/panels/NewsChartCorrelationPanel"),
  {
    ssr: false,
    loading: () => <div className="text-white p-8">Loading News Panel...</div>,
  }
);

export default function NewsCorrelationPage() {
  return (
    <div className="min-h-screen bg-slate-950 p-4">
      <h1 className="text-2xl font-bold text-white mb-4">News-Chart Correlation</h1>
      <NewsChartCorrelationPanel />
    </div>
  );
}
