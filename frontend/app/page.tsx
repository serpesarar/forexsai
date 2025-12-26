"use client";

import { useEffect, useMemo } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  DollarSign,
  PlayCircle,
  RefreshCw
} from "lucide-react";
import NasdaqPanel from "../components/NasdaqPanel";
import XauusdPanel from "../components/XauusdPanel";
import PatternEnginePanel from "../components/PatternEnginePanel";
import ClaudePatternPanel from "../components/ClaudePatternPanel";
import SentimentPanel from "../components/SentimentPanel";
import OrderBlockPanel from "../components/OrderBlockPanel";
import RTYHIIMDetectorPanel from "../components/RTYHIIMDetectorPanel";
import AdvancedChart from "../components/AdvancedChart";
import NewsFeed from "../components/NewsFeed";
import CircularChart from "../components/CircularChart";
import CumulativeChart from "../components/CumulativeChart";
import MetricCard from "../components/MetricCard";
import { useRunAll } from "../lib/api";
import { useDashboardStore } from "../lib/store";

const tickerItems = [
  { label: "NASDAQ 100", value: "21,547.35" },
  { label: "XAU/USD", value: "2,163.20" }
];

const mockData = {
  totalPnL: 7674.45,
  profitFactor: 1.64,
  avgWin: 1036.45,
  avgLoss: -1092.56,
  totalTrades: 30,
  winningTrades: 19,
  losingTrades: 11,
  winningDays: 14,
  losingDays: 5
};

const chartData = [
  { date: "Jun 01", value: 0 },
  { date: "Jun 07", value: 420 },
  { date: "Jun 14", value: 1400 },
  { date: "Jun 21", value: 1850 },
  { date: "Jun 28", value: 2300 },
  { date: "Jul 05", value: -200 },
  { date: "Jul 12", value: 1200 },
  { date: "Jul 19", value: 2800 },
  { date: "Jul 26", value: 4300 },
  { date: "Aug 02", value: 5100 },
  { date: "Aug 09", value: 6200 },
  { date: "Aug 16", value: 7674 }
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

  const totalPnL = mockData.totalPnL.toLocaleString("en-US", {
    style: "currency",
    currency: "USD"
  });
  const avgWin = mockData.avgWin.toLocaleString("en-US", {
    style: "currency",
    currency: "USD"
  });
  const avgLoss = mockData.avgLoss.toLocaleString("en-US", {
    style: "currency",
    currency: "USD"
  });

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-white/10 bg-[#161925]/70 px-6 py-8 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-6">
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
              <button className="p-3 rounded-full bg-white/10" aria-label="Notifications">
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

      <main className="px-6 py-10 space-y-8">
        <section className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          <MetricCard
            label="Total Net P&L"
            value={totalPnL}
            meta={`Trades in total: ${mockData.totalTrades}`}
            trend={mockData.totalPnL >= 0 ? "positive" : "negative"}
            icon={<DollarSign className="h-4 w-4" />}
          />
          <MetricCard
            label="Profit Factor"
            value={mockData.profitFactor.toFixed(2)}
            meta="Risk-adjusted return"
            trend="positive"
            icon={<Activity className="h-4 w-4" />}
          />
          <MetricCard
            label="Average Winning Trade"
            value={avgWin}
            meta="Best performing setups"
            trend="positive"
            icon={<ArrowUpRight className="h-4 w-4" />}
          />
          <MetricCard
            label="Average Losing Trade"
            value={avgLoss}
            meta="Loss containment"
            trend="negative"
            icon={<ArrowDownRight className="h-4 w-4" />}
          />
        </section>

        <section className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6">
            <CircularChart title="NASDAQ 100 Winrate" winners={mockData.winningTrades} losers={mockData.losingTrades} />
            <CircularChart title="XAU/USD Winrate" winners={mockData.winningDays} losers={mockData.losingDays} />
          </div>
          <div className="lg:col-span-2">
            <CumulativeChart data={chartData} />
          </div>
        </section>

        <section className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <AdvancedChart symbol="NDX.INDX" />
          </div>
          <div>
            <NewsFeed />
          </div>
        </section>

        <section className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
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
        </section>
      </main>
    </div>
  );
}
