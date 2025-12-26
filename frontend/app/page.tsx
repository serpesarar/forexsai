"use client";

 codex/redesign-trading-dashboard-ui-with-dark-theme-i27dom
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
=======
import { Activity, ArrowDownRight, ArrowUpRight, DollarSign } from "lucide-react";
import CircularChart from "../components/CircularChart";
import CumulativeChart from "../components/CumulativeChart";
import MetricCard from "../components/MetricCard";
import TradingCalendar from "../components/TradingCalendar";
main

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

codex/redesign-trading-dashboard-ui-with-dark-theme-i27dom
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

=======
main
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
codex/redesign-trading-dashboard-ui-with-dark-theme-i27dom

export default function HomePage() {
  const runAll = useRunAll();
  const { autoRefresh, setAutoRefresh, lastUpdated, setLastUpdated } = useDashboardStore();
=======
main

const calendarDays = [
  { date: 28, pnl: -120, isCurrentMonth: false },
  { date: 29, pnl: 240, isCurrentMonth: false },
  { date: 30, pnl: 0, isCurrentMonth: false },
  { date: 31, pnl: 80, isCurrentMonth: false },
  { date: 1, pnl: 140 },
  { date: 2, pnl: -90 },
  { date: 3, pnl: 0 },
  { date: 4, pnl: 240 },
  { date: 5, pnl: 180 },
  { date: 6, pnl: -140 },
  { date: 7, pnl: 0 },
  { date: 8, pnl: 80 },
  { date: 9, pnl: 120 },
  { date: 10, pnl: -40 },
  { date: 11, pnl: 220 },
  { date: 12, pnl: 0 },
  { date: 13, pnl: 60 },
  { date: 14, pnl: -120 },
  { date: 15, pnl: 80 },
  { date: 16, pnl: 200 },
  { date: 17, pnl: -60 },
  { date: 18, pnl: 120 },
  { date: 19, pnl: 0 },
  { date: 20, pnl: -100 },
  { date: 21, pnl: 160 },
  { date: 22, pnl: 90 },
  { date: 23, pnl: -30 },
  { date: 24, pnl: 200 },
  { date: 25, pnl: 0 },
  { date: 26, pnl: 180 },
  { date: 27, pnl: -40 },
  { date: 28, pnl: 110 },
  { date: 29, pnl: 0 },
  { date: 30, pnl: 90 },
  { date: 31, pnl: 70 },
  { date: 1, pnl: 0, isCurrentMonth: false },
  { date: 2, pnl: 140, isCurrentMonth: false },
  { date: 3, pnl: -60, isCurrentMonth: false }
];

export default function HomePage() {
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
codex/redesign-trading-dashboard-ui-with-dark-theme-i27dom
    <div className="min-h-screen bg-background">
      <header className="border-b border-white/10 bg-[#161925]/70 px-6 py-8 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-6">
=======
    <div className="min-h-screen bg-background text-textPrimary">
      <header className="border-b border-white/5 bg-[#161925]/70 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8">
 main
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.4em] text-textSecondary">Trade Dashboard</p>
              <h1 className="mt-2 text-3xl font-semibold">Performance Overview</h1>
              <p className="mt-2 max-w-2xl text-sm text-textSecondary">
                A modern dark theme dashboard inspired by TradeZella, highlighting the most important
                trading metrics and performance insights.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button className="rounded-full border border-white/10 px-4 py-2 text-sm text-textSecondary transition hover:border-white/30 hover:text-textPrimary">
                June 2022 - Aug 2022
              </button>
              <button className="rounded-full border border-white/10 px-4 py-2 text-sm text-textSecondary transition hover:border-white/30 hover:text-textPrimary">
                All Accounts
              </button>
            </div>
          </div>
        </div>
      </header>

 codex/redesign-trading-dashboard-ui-with-dark-theme-i27dom
      <main className="px-6 py-10 space-y-8">
        <section className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
=======
      <main className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10">
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
main
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
 codex/redesign-trading-dashboard-ui-with-dark-theme-i27dom
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
=======
 main
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-6">
            <CircularChart
              title="Winning % By Trades"
              winners={mockData.winningTrades}
              losers={mockData.losingTrades}
            />
            <CircularChart
              title="Winning % By Days"
              winners={mockData.winningDays}
              losers={mockData.losingDays}
            />
          </div>
          <div className="lg:col-span-2">
            <CumulativeChart data={chartData} />
          </div>
        </section>

        <section>
          <TradingCalendar monthLabel="August 2022" days={calendarDays} />
        </section>
      </main>
    </div>
  );
}
