"use client";

import { useEffect, useMemo } from "react";
import { Bell, PlayCircle, RefreshCw } from "lucide-react";
import NasdaqPanel from "../components/NasdaqPanel";
import XauusdPanel from "../components/XauusdPanel";
import PatternEnginePanel from "../components/PatternEnginePanel";
import ClaudePatternPanel from "../components/ClaudePatternPanel";
import SentimentPanel from "../components/SentimentPanel";
import OrderBlockPanel from "../components/OrderBlockPanel";
import RTYHIIMDetectorPanel from "../components/RTYHIIMDetectorPanel";
import { useRunAll } from "../lib/api";
import { useDashboardStore } from "../lib/store";

const tickerItems = [
  { label: "NASDAQ 100", value: "21,547.35" },
  { label: "XAU/USD", value: "2,163.20" }
];

export default function HomePage() {
  const runAll = useRunAll();
  const { autoRefresh, setAutoRefresh, lastUpdated, setLastUpdated } = useDashboardStore();

  const refreshInterval = useMemo(() => {
    if (autoRefresh === "30s") return 30000;
    if (autoRefresh === "60s") return 60000;
    return null;
  }, [autoRefresh]);

  useEffect(() => {
    if (!refreshInterval) return;
    const interval = setInterval(() => {
      runAll.mutate(undefined, {
        onSuccess: () => setLastUpdated(new Date().toISOString())
      });
    }, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, runAll, setLastUpdated]);

  return (
    <div className="min-h-screen bg-background">
      <header className="px-6 py-8 border-b border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col gap-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold">AI Trading Dashboard</h1>
              <p className="text-sm text-textSecondary">FULL STACK AI TRADING DASHBOARD - GÜNCEL</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() =>
                  runAll.mutate(undefined, {
                    onSuccess: () => setLastUpdated(new Date().toISOString())
                  })
                }
                className="gradient-button flex items-center gap-2"
              >
                <PlayCircle className="w-4 h-4" />
                {runAll.isPending ? "Analyzing... 45s" : "Run All Analysis"}
              </button>
              <button className="p-3 rounded-full bg-white/10">
                <Bell className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap gap-4">
              {tickerItems.map((item) => (
                <div key={item.label} className="bg-white/5 px-4 py-2 rounded-full text-sm">
                  <span className="text-textSecondary">{item.label}:</span> {item.value}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-textSecondary">Auto-refresh</span>
              {(["off", "30s", "60s"] as const).map((value) => (
                <button
                  key={value}
                  onClick={() => setAutoRefresh(value)}
                  className={`px-3 py-1 rounded-full ${
                    autoRefresh === value ? "bg-white text-background" : "bg-white/10"
                  }`}
                >
                  {value.toUpperCase()}
                </button>
              ))}
              <div className="flex items-center gap-2 text-textSecondary">
                <RefreshCw className="w-4 h-4" />
                <span>{lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : "Not updated"}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="px-6 py-10">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6">
            <NasdaqPanel />
            <XauusdPanel />
          </div>
          <div className="space-y-6">
            <PatternEnginePanel />
            <ClaudePatternPanel />
          </div>
          <div className="space-y-6">
            <SentimentPanel />
            <OrderBlockPanel />
            <RTYHIIMDetectorPanel />
            <div className="glass-card p-6 space-y-2 text-sm text-textSecondary">
              <p>Powered by Claude AI + Custom ML Models</p>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-success" /> API Health
                <span className="w-2 h-2 rounded-full bg-warning" /> Model Status
              </div>
              <div className="text-xs">Settings coming soon</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
