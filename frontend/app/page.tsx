"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Brain,
  Clock,
  Moon,
  PlayCircle,
  RefreshCw,
  Sun,
} from "lucide-react";
import CircularProgress from "../components/CircularProgress";
import DetailPanel from "../components/DetailPanel";
import { useDashboardStore, useDetailPanelStore } from "../lib/store";

const marketTickers = [
  { label: "NASDAQ", price: "21,547.35", change: "+1.2%", trend: "up" },
  { label: "XAU/USD", price: "2,048.50", change: "-0.3%", trend: "down" },
];

const signalCards = [
  {
    symbol: "NASDAQ",
    currentPrice: 21547.35,
    signal: "BUY",
    confidence: 75,
    metrics: [
      { label: "RSI", value: "45 (Neutral)" },
      { label: "Trend", value: "Bullish" },
      { label: "Support", value: "21,300 (8/10)" },
      { label: "Volatility", value: "Low" },
    ],
    liveMetrics: {
      supportResistance: [
        {
          price: 21300,
          type: "support",
          strength: 0.8,
          reliability: 0.85,
          hits: 8,
          lastTouched: "2025-01-20T09:15:00Z",
          distance: 247,
          distancePct: 1.15,
        },
        {
          price: 21350,
          type: "support",
          strength: 0.6,
          reliability: 0.7,
          hits: 6,
          lastTouched: "2025-01-20T07:45:00Z",
          distance: 197,
          distancePct: 0.92,
        },
        {
          price: 21450,
          type: "resistance",
          strength: 0.7,
          reliability: 0.78,
          hits: 7,
          lastTouched: "2025-01-20T08:05:00Z",
          distance: -97,
          distancePct: -0.45,
        },
        {
          price: 21500,
          type: "resistance",
          strength: 0.9,
          reliability: 0.92,
          hits: 9,
          lastTouched: "2025-01-20T08:35:00Z",
          distance: -47,
          distancePct: -0.22,
        },
      ],
      nearestSupport: { price: 21300, distance: 247, distancePct: 1.15 },
      nearestResistance: { price: 21500, distance: -47, distancePct: -0.22 },
      trendChannel: {
        distanceToUpper: 125,
        distanceToLower: -175,
        trendStrength: 0.72,
        channelWidth: 125,
        rSquared: 0.82,
        slope: 0.45,
        trendQuality: "strong",
      },
      emaDistances: {
        ema20: { distance: 97, distancePct: 0.45, emaValue: 21450, period: 20 },
        ema50: { distance: 167, distancePct: 0.78, emaValue: 21380, period: 50 },
        ema200: { distance: 347, distancePct: 1.64, emaValue: 21200, period: 200 },
      },
    },
    reasons: ["Breakout above 20DMA", "Institutional flow positive"],
  },
  {
    symbol: "XAUUSD",
    currentPrice: 2048.5,
    signal: "HOLD",
    confidence: 62,
    metrics: [
      { label: "RSI", value: "51 (Neutral)" },
      { label: "Trend", value: "Sideways" },
      { label: "Support", value: "2,010 (6/10)" },
      { label: "Volatility", value: "Medium" },
    ],
    liveMetrics: {
      supportResistance: [
        {
          price: 2040,
          type: "support",
          strength: 0.85,
          reliability: 0.88,
          hits: 9,
          lastTouched: "2025-01-20T06:40:00Z",
          distance: 8.5,
          distancePct: 0.42,
        },
        {
          price: 2050,
          type: "support",
          strength: 0.7,
          reliability: 0.72,
          hits: 7,
          lastTouched: "2025-01-20T07:10:00Z",
          distance: -1.5,
          distancePct: -0.07,
        },
        {
          price: 2055,
          type: "resistance",
          strength: 0.65,
          reliability: 0.68,
          hits: 6,
          lastTouched: "2025-01-20T08:15:00Z",
          distance: -6.5,
          distancePct: -0.32,
        },
        {
          price: 2060,
          type: "resistance",
          strength: 0.8,
          reliability: 0.8,
          hits: 8,
          lastTouched: "2025-01-20T08:40:00Z",
          distance: -11.5,
          distancePct: -0.56,
        },
      ],
      nearestSupport: { price: 2040, distance: 8.5, distancePct: 0.42 },
      nearestResistance: { price: 2055, distance: -6.5, distancePct: -0.32 },
      trendChannel: {
        distanceToUpper: 52,
        distanceToLower: -44,
        trendStrength: 0.58,
        channelWidth: 70,
        rSquared: 0.64,
        slope: 0.18,
        trendQuality: "moderate",
      },
      emaDistances: {
        ema20: { distance: 6.5, distancePct: 0.32, emaValue: 2042, period: 20 },
        ema50: { distance: 11.2, distancePct: 0.54, emaValue: 2037, period: 50 },
        ema200: { distance: 18.4, distancePct: 0.9, emaValue: 2030, period: 200 },
      },
    },
    reasons: ["Macro headlines mixed", "Range bound last 5 sessions"],
  },
];

const patternTemplate = [
  "Double Bottom",
  "Flag Break",
  "Ascending Triangle",
  "Bullish Engulf",
  "RSI Divergence",
  "Trend Continuation",
];

const makePatterns = () =>
  Array.from({ length: 30 }, (_, index) => {
    const trades = ["BUY", "SELL", "HOLD"] as const;
    const stages = ["DETECTED", "CONFIRMED", "WATCH"] as const;
    return {
      pattern: patternTemplate[index % patternTemplate.length],
      success: (0.68 + (index % 5) * 0.04).toFixed(2),
      trade: trades[index % trades.length],
      stage: stages[index % stages.length],
    };
  });

const nasdaqPatterns = makePatterns();
const xauusdPatterns = makePatterns();

const timeframes = ["5m", "15m", "30m", "1h", "4h", "1d"] as const;

const timeframePatterns: Record<
  (typeof timeframes)[number],
  Array<{ name: string; completion: number; signal: string }>
> = {
  "5m": [
    { name: "Double Bottom", completion: 82, signal: "bullish" },
    { name: "RSI Divergence", completion: 71, signal: "bullish" },
  ],
  "15m": [
    { name: "Falling Wedge", completion: 64, signal: "neutral" },
    { name: "Flag Break", completion: 79, signal: "bullish" },
  ],
  "30m": [
    { name: "Ascending Triangle", completion: 86, signal: "bullish" },
    { name: "Volume Spike", completion: 58, signal: "neutral" },
  ],
  "1h": [
    { name: "Trend Continuation", completion: 74, signal: "bullish" },
    { name: "Order Block", completion: 62, signal: "neutral" },
  ],
  "4h": [
    { name: "Breakout", completion: 68, signal: "bullish" },
    { name: "Supply Zone", completion: 55, signal: "bearish" },
  ],
  "1d": [
    { name: "Macro Reversal", completion: 61, signal: "neutral" },
    { name: "Momentum Fade", completion: 49, signal: "bearish" },
  ],
};

const newsItems = [
  {
    title: "NASDAQ futures climb after soft CPI print",
    source: "MarketAux",
    sentiment: "bullish",
    time: "12m ago",
  },
  {
    title: "Gold steadies as yields dip ahead of Fed minutes",
    source: "Bloomberg",
    sentiment: "neutral",
    time: "28m ago",
  },
  {
    title: "Tech earnings beat expectations; guidance mixed",
    source: "Reuters",
    sentiment: "bullish",
    time: "1h ago",
  },
  {
    title: "Dollar index firms as risk appetite cools",
    source: "WSJ",
    sentiment: "bearish",
    time: "2h ago",
  },
  {
    title: "Macro calendar: ISM, jobless claims due",
    source: "MarketAux",
    sentiment: "neutral",
    time: "4h ago",
  },
];

const miniSeries = [
  [12, 16, 14, 20, 22, 21, 28, 32, 29, 35],
  [24, 20, 18, 17, 19, 16, 15, 14, 18, 16],
];

function MiniSparkline({ values, accent }: { values: number[]; accent: string }) {
  const points = useMemo(() => {
    const max = Math.max(...values);
    const min = Math.min(...values);
    return values
      .map((value, index) => {
        const x = (index / (values.length - 1)) * 120;
        const y = 40 - ((value - min) / (max - min || 1)) * 40;
        return `${x},${y}`;
      })
      .join(" ");
  }, [values]);

  return (
    <svg viewBox="0 0 120 40" className="h-10 w-full">
      <polyline
        fill="none"
        stroke={accent}
        strokeWidth="2"
        points={points}
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function HomePage() {
  const [activeTf, setActiveTf] = useState<(typeof timeframes)[number]>("15m");
  const [theme, setTheme] = useState<"evening" | "morning">("evening");
  const {
    autoRefresh,
    toggleAutoRefresh,
    fetchAll,
    isLoading,
    customAnalysis,
    customAnalysisLoading,
    runCustomAnalysis,
  } = useDashboardStore();
  const { isOpen, type, symbol, data, title, open, close } = useDetailPanelStore();

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const interval = setInterval(() => {
      fetchAll();
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAll]);

  useEffect(() => {
    if (theme === "morning") {
      document.documentElement.setAttribute("data-theme", "dawn");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }, [theme]);

  return (
    <div className="min-h-screen bg-background text-textPrimary">
      <header className="border-b border-white/10">
        <div className="mx-auto flex h-[60px] max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/5">
              <Activity className="h-4 w-4 text-accent" />
            </div>
            <div>
              <p className="text-sm font-semibold">AI Trading Dashboard</p>
              <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">NASDAQ + XAUUSD</p>
            </div>
          </div>

          <div className="hidden items-center gap-6 lg:flex">
            {marketTickers.map((ticker) => (
              <div key={ticker.label} className="flex items-center gap-2 text-sm">
                <span className="text-textSecondary">{ticker.label}:</span>
                <span className="font-mono">${ticker.price}</span>
                <span
                  className={`font-mono ${ticker.trend === "up" ? "text-success" : "text-danger"}`}
                >
                  {ticker.change}
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchAll}
              className="gradient-button flex items-center gap-2 text-xs uppercase tracking-[0.2em]"
            >
              <PlayCircle className="h-4 w-4" />
              {isLoading ? "Running" : "Run Analysis"}
            </button>
            <button
              onClick={fetchAll}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 text-textSecondary transition hover:border-white/30"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button
              onClick={() => setTheme(theme === "evening" ? "morning" : "evening")}
              className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-textSecondary transition hover:border-white/30"
            >
              {theme === "evening" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
              {theme === "evening" ? "Morning" : "Evening"}
            </button>
            <div className="hidden items-center gap-3 text-xs text-textSecondary md:flex">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(event) => toggleAutoRefresh(event.target.checked)}
                  className="h-4 w-4 accent-accent"
                />
                Auto 30s
              </label>
              <span className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Live
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-6 py-8 md:grid-cols-2 lg:grid-cols-3">
        <div className="flex flex-col gap-6">
          {signalCards.map((signal) => (
            <div key={signal.symbol} className="glass-card card-hover p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Signal</p>
                  <h3 className="mt-2 text-lg font-semibold">{signal.symbol}</h3>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    signal.signal === "BUY"
                      ? "bg-success/20 text-success"
                      : signal.signal === "SELL"
                        ? "bg-danger/20 text-danger"
                        : "bg-white/10 text-textSecondary"
                  }`}
                >
                  {signal.signal}
                </span>
              </div>
              <div className="mt-4 flex items-center justify-between gap-6">
                <CircularProgress
                  value={signal.confidence}
                  label="Confidence"
                  sublabel={`${signal.confidence}%`}
                  isInteractive
                  onClick={() =>
                    open(
                      "trend_channel",
                      {
                        ...signal.liveMetrics.trendChannel,
                        trendStrength: signal.liveMetrics.trendChannel.trendStrength,
                      },
                      signal.symbol as "NASDAQ" | "XAUUSD",
                      `Trend Channel Overview (${signal.symbol})`
                    )
                  }
                />
                <div className="flex-1 space-y-2 text-xs text-textSecondary">
                  <div className="flex items-center justify-between">
                    <span>Nearest Support</span>
                    <span className="font-mono">
                      {signal.liveMetrics.nearestSupport.price} ({signal.liveMetrics.nearestSupport.distance})
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Nearest Resistance</span>
                    <span className="font-mono">
                      {signal.liveMetrics.nearestResistance.price} ({signal.liveMetrics.nearestResistance.distance})
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Trend Strength</span>
                    <span className="font-mono">
                      {Math.round(signal.liveMetrics.trendChannel.trendStrength * 100)}%
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                {[
                  {
                    label: "EMA 20",
                    detail: signal.liveMetrics.emaDistances.ema20,
                  },
                  {
                    label: "EMA 50",
                    detail: signal.liveMetrics.emaDistances.ema50,
                  },
                  {
                    label: "EMA 200",
                    detail: signal.liveMetrics.emaDistances.ema200,
                  },
                  {
                    label: "Channel U",
                    detail: {
                      distancePct: signal.liveMetrics.trendChannel.distanceToUpper,
                      distance: signal.liveMetrics.trendChannel.distanceToUpper,
                      emaValue: signal.liveMetrics.trendChannel.channelWidth,
                      currentPrice: signal.currentPrice,
                      period: 0,
                    },
                    type: "trend_channel" as const,
                    title: "Channel Upper Distance",
                    data: {
                      ...signal.liveMetrics.trendChannel,
                    },
                  },
                  {
                    label: "Channel L",
                    detail: {
                      distancePct: signal.liveMetrics.trendChannel.distanceToLower,
                      distance: signal.liveMetrics.trendChannel.distanceToLower,
                      emaValue: signal.liveMetrics.trendChannel.channelWidth,
                      currentPrice: signal.currentPrice,
                      period: 0,
                    },
                    type: "trend_channel" as const,
                    title: "Channel Lower Distance",
                    data: {
                      ...signal.liveMetrics.trendChannel,
                    },
                  },
                  {
                    label: "S/R Bias",
                    detail: {
                      distancePct:
                        signal.liveMetrics.nearestSupport.distance +
                        signal.liveMetrics.nearestResistance.distance,
                      distance:
                        signal.liveMetrics.nearestSupport.distance +
                        signal.liveMetrics.nearestResistance.distance,
                      emaValue: signal.liveMetrics.nearestSupport.price,
                      currentPrice: signal.currentPrice,
                      period: 0,
                    },
                    type: "support_resistance" as const,
                    title: `Support Level: ${signal.liveMetrics.nearestSupport.price} (${signal.symbol})`,
                    data: {
                      ...signal.liveMetrics.supportResistance[0],
                    },
                  },
                ].map((metric, index) => {
                  const detailType = metric.type ?? "ema_distance";
                  const detailData =
                    metric.data ??
                    {
                      ...metric.detail,
                      currentPrice: signal.currentPrice,
                      period: metric.detail.period,
                    };
                  const detailTitle = metric.title ?? `${metric.label} (${signal.symbol})`;
                  return (
                    <div key={`${signal.symbol}-${metric.label}-${index}`} className="rounded-lg border border-white/5 bg-white/5 p-3">
                      <CircularProgress
                        value={Math.min(Math.abs(metric.detail.distancePct) * 40, 100)}
                        size={48}
                        strokeWidth={6}
                        sublabel={`${metric.detail.distancePct}%`}
                        isInteractive
                        onClick={() =>
                          open(detailType, detailData, signal.symbol as "NASDAQ" | "XAUUSD", detailTitle)
                        }
                      />
                      <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-textSecondary">
                        {metric.label}
                      </p>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                {signal.liveMetrics.supportResistance.map((level) => (
                  <div
                    key={`${signal.symbol}-${level.price}`}
                    className="flex items-center justify-between rounded-full border border-white/5 bg-white/5 px-3 py-2"
                  >
                    <span className="font-mono">{level.price}</span>
                    <span
                      className={`text-[10px] uppercase ${
                        level.type === "support" ? "text-success" : "text-danger"
                      }`}
                    >
                      {level.type}
                    </span>
                    <span className="text-[10px] text-textSecondary">
                      {Math.round(level.strength * 100)}%
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                {signal.metrics.map((metric) => (
                  <div key={metric.label} className="rounded-lg border border-white/5 bg-white/5 p-3">
                    <p className="text-textSecondary uppercase tracking-[0.2em] text-[10px]">
                      {metric.label}
                    </p>
                    <p className="mt-1 font-mono text-sm">{metric.value}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 space-y-1 text-xs text-textSecondary">
                {signal.reasons.map((reason) => (
                  <p key={reason}>• {reason}</p>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-6">
          <div className="glass-card card-hover p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Pattern Engine</p>
                <h3 className="mt-2 text-lg font-semibold">NASDAQ + XAUUSD Top 30</h3>
              </div>
              <span className="text-xs text-textSecondary">Updated 4m ago</span>
            </div>
            <div className="mt-4 space-y-6">
              {[
                { title: "NASDAQ Patterns", subtitle: "Top 30 candidates", rows: nasdaqPatterns },
                { title: "XAUUSD Patterns", subtitle: "Top 30 candidates", rows: xauusdPatterns },
              ].map((section) => (
                <div key={section.title}>
                  <div className="flex items-center justify-between">
                    <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">
                      {section.title}
                    </p>
                    <span className="text-xs text-textSecondary">{section.subtitle}</span>
                  </div>
                  <div className="mt-3 max-h-[200px] overflow-y-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="sticky top-0 bg-background/80 text-textSecondary">
                        <tr>
                          <th className="py-2">Pattern</th>
                          <th className="py-2">p_success</th>
                          <th className="py-2">Trade</th>
                          <th className="py-2">Stage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {section.rows.map((row, index) => (
                          <tr
                            key={`${section.title}-${index}`}
                            className="border-t border-white/5 hover:bg-accent/10 transition"
                          >
                            <td className="py-2">{row.pattern}</td>
                            <td className="py-2 font-mono">{row.success}</td>
                            <td className="py-2">
                              <span
                                className={`rounded-full px-2 py-1 text-[10px] uppercase ${
                                  row.trade === "BUY"
                                    ? "bg-success/20 text-success"
                                    : row.trade === "SELL"
                                      ? "bg-danger/20 text-danger"
                                      : "bg-white/10 text-textSecondary"
                                }`}
                              >
                                {row.trade}
                              </span>
                            </td>
                            <td className="py-2 text-textSecondary">{row.stage}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card card-hover p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Claude Patterns</p>
                <h3 className="mt-2 text-lg font-semibold">Multi-timeframe Insights</h3>
              </div>
              <button
                onClick={runCustomAnalysis}
                className="flex items-center gap-2 rounded-full border border-accent/40 px-3 py-1 text-xs uppercase tracking-[0.2em] text-accent"
              >
                <Brain className="h-4 w-4" />
                {customAnalysisLoading ? "Analyzing" : "Analyze Custom"}
              </button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => setActiveTf(tf)}
                  className={`rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] transition ${
                    activeTf === tf
                      ? "border-accent text-accent"
                      : "border-white/10 text-textSecondary hover:border-white/30"
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
            <div className="mt-4 grid gap-3">
              {timeframePatterns[activeTf].map((pattern) => (
                <div
                  key={pattern.name}
                  className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 p-3"
                >
                  <div>
                    <p className="text-sm font-semibold">{pattern.name}</p>
                    <p className="text-xs text-textSecondary uppercase tracking-[0.2em]">{pattern.signal}</p>
                  </div>
                  <CircularProgress
                    value={pattern.completion}
                    size={48}
                    strokeWidth={6}
                    colorClassName={
                      pattern.signal === "bullish"
                        ? "text-success"
                        : pattern.signal === "bearish"
                          ? "text-danger"
                          : "text-accent"
                    }
                    isInteractive
                    onClick={() =>
                      open(
                        "trend_channel",
                        {
                          ...signalCards[0].liveMetrics.trendChannel,
                        },
                        "NASDAQ",
                        `Pattern Confidence: ${pattern.name}`
                      )
                    }
                  />
                </div>
              ))}
            </div>
            {customAnalysis && (
              <div className="mt-4 rounded-xl border border-accent/20 bg-accent/5 p-4 text-xs">
                <p className="text-sm font-semibold text-accent">Custom Analysis (Last 100 candles)</p>
                <p className="mt-2 text-textSecondary">{customAnalysis.summary}</p>
                <ul className="mt-3 space-y-1 text-textSecondary">
                  {customAnalysis.insights.map((insight) => (
                    <li key={insight}>• {insight}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="glass-card card-hover p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Sentiment</p>
                <h3 className="mt-2 text-lg font-semibold">Claude Interpretation</h3>
              </div>
              <span className="text-xs text-textSecondary">Confidence 85%</span>
            </div>
            <div className="mt-4 flex items-center justify-between gap-4">
              <CircularProgress
                value={85}
                label="Bullish"
                sublabel="🐂"
                isInteractive
                onClick={() =>
                  open(
                    "trend_channel",
                    { ...signalCards[0].liveMetrics.trendChannel },
                    "NASDAQ",
                    "Sentiment Trend Strength"
                  )
                }
              />
              <div className="flex-1 space-y-3">
                {[
                  { label: "Up", value: 60, color: "bg-success" },
                  { label: "Down", value: 30, color: "bg-danger" },
                  { label: "Sideways", value: 10, color: "bg-white/40" },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-xs text-textSecondary">
                      <span>{item.label}</span>
                      <span className="font-mono">{item.value}%</span>
                    </div>
                    <div className="mt-1 h-2 w-full rounded-full bg-white/10">
                      <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${item.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-4 space-y-1 text-xs text-textSecondary">
              <p>• News flow: tech earnings positive</p>
              <p>• Volatility: declining across indices</p>
              <p>• Macro: inflation easing narrative</p>
            </div>
          </div>

          <div className="glass-card card-hover p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">MarketAux</p>
                <h3 className="mt-2 text-lg font-semibold">Live News Feed</h3>
              </div>
              <span className="text-xs text-textSecondary">30 headlines</span>
            </div>
            <div className="mt-4 max-h-[300px] space-y-3 overflow-y-auto">
              {newsItems.map((item) => (
                <div key={item.title} className="rounded-xl border border-white/5 bg-white/5 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">{item.title}</p>
                      <p className="text-xs text-textSecondary">{item.source}</p>
                    </div>
                    <span
                      className={`mt-1 h-2 w-2 rounded-full ${
                        item.sentiment === "bullish"
                          ? "bg-success"
                          : item.sentiment === "bearish"
                            ? "bg-danger"
                            : "bg-white/40"
                      }`}
                    />
                  </div>
                  <p className="mt-2 text-xs text-textSecondary">{item.time}</p>
                </div>
              ))}
            </div>
          </div>

          {["NASDAQ", "XAUUSD"].map((symbol, index) => (
            <div key={symbol} className="glass-card card-hover p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">Chart</p>
                  <h3 className="mt-2 text-lg font-semibold">{symbol} Candlestick</h3>
                </div>
                <span className="text-xs text-textSecondary">Highcharts Dark</span>
              </div>
              <div className="mt-4 h-[300px] rounded-xl border border-white/5 bg-gradient-to-br from-white/5 to-transparent">
                <div className="flex h-full items-center justify-center text-xs uppercase tracking-[0.3em] text-textSecondary">
                  Candlestick chart placeholder
                </div>
              </div>
              <div className="mt-4">
                <MiniSparkline values={miniSeries[index]} accent={index === 0 ? "#10b981" : "#ef4444"} />
              </div>
            </div>
          ))}
        </div>
      </main>

      <DetailPanel
        isOpen={isOpen}
        onClose={close}
        title={title}
        symbol={symbol ?? "NASDAQ"}
        type={type}
        data={data}
      />
    </div>
  );
}
