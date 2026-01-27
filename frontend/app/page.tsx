"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Brain,
  Clock,
  Loader2,
  Moon,
  PlayCircle,
  RefreshCw,
  Sun,
  Sparkles,
  BarChart3,
  GripVertical,
  LineChart,
} from "lucide-react";
import Link from "next/link";
import CircularProgress from "../components/CircularProgress";
import DetailPanel from "../components/DetailPanel";
import { useDashboardStore, useDetailPanelStore } from "../lib/store";
import { fetcher } from "../lib/api";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useI18nStore } from "../lib/i18n/store";
import TradingChartWrapper from "../components/TradingChartWrapper";
import OrderBlockPanelSimple from "../components/OrderBlockPanelSimple";
import RhythmDetectorSimple from "../components/RhythmDetectorSimple";
import MLPredictionPanel from "../components/MLPredictionPanel";
import ClaudeAnalysisPanel from "../components/ClaudeAnalysisPanel";
import PatternEngineV2 from "../components/PatternEngineV2";
import { useDashboardEdit, DashboardCard } from "../contexts/DashboardEditContext";
import { EditModeButton, EditModeControls, DraggableDashboard, SortableCard } from "../components/DraggableDashboard";
import { useLivePrices } from "../hooks/useLivePrices";
import { useCachedDashboardData, cachedToSignalCard } from "../hooks/useCachedDashboardData";

const initialMarketTickers = [
  { label: "NASDAQ", price: "--", change: "--%", trend: "up" as const },
  { label: "XAU/USD", price: "--", change: "--%", trend: "up" as const },
];

// Placeholder shown only while cache is loading
const loadingSignalCard = (symbol: string) => ({
  symbol,
  currentPrice: 0,
  signal: "HOLD",
  confidence: 0,
  trend: "NEUTRAL" as string,
  trendStrength: 0,
  volatility: "MEDIUM" as string,
  volumeConfirmed: false,
  metrics: [
    { label: "RSI", value: "-- (Loading)" },
    { label: "Trend", value: "Loading..." },
    { label: "Support", value: "--" },
    { label: "Volatility", value: "--" },
  ],
  liveMetrics: {
    supportResistance: [],
    nearestSupport: { price: 0, distance: 0, distancePct: 0 },
    nearestResistance: { price: 0, distance: 0, distancePct: 0 },
    trendChannel: { distanceToUpper: 0, distanceToLower: 0, trendStrength: 0, channelWidth: 0, rSquared: 0, slope: 0, trendQuality: "weak" },
    emaDistances: {
      ema20: { distance: 0, distancePct: 0, emaValue: 0, period: 20 },
      ema50: { distance: 0, distancePct: 0, emaValue: 0, period: 50 },
      ema200: { distance: 0, distancePct: 0, emaValue: 0, period: 200 },
    },
  },
  reasons: ["Loading cached data..."],
});

const initialSignalCards = [
  {
    symbol: "NASDAQ",
    currentPrice: 0,
    signal: "HOLD",
    confidence: 0,
    trend: "NEUTRAL" as string,
    trendStrength: 0,
    volatility: "MEDIUM" as string,
    volumeConfirmed: false,
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
    currentPrice: 0,
    signal: "HOLD",
    confidence: 0,
    trend: "NEUTRAL" as string,
    trendStrength: 0,
    volatility: "MEDIUM" as string,
    volumeConfirmed: false,
    metrics: [
      { label: "RSI", value: "-- (Loading)" },
      { label: "Trend", value: "Loading..." },
      { label: "Support", value: "--" },
      { label: "Volatility", value: "--" },
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

const initialNewsItems = [
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
  
  // Live prices hook - updates every 3 seconds with daily change %
  const { tickers: liveTickers, isLoading: pricesLoading } = useLivePrices(3000);
  const marketTickers = liveTickers.length > 0 ? liveTickers : initialMarketTickers;
  
  // Cache hook - loads pre-computed data from backend immediately
  const { nasdaq: cachedNasdaq, xauusd: cachedXauusd, hasData: hasCachedData } = useCachedDashboardData();
  
  const [_marketTickersOld, setMarketTickers] = useState(initialMarketTickers);
  const [signalCards, setSignalCards] = useState(initialSignalCards);
  
  // Update signal cards from cache on first load
  useEffect(() => {
    if (hasCachedData) {
      const nasdaqCard = cachedToSignalCard(cachedNasdaq ?? null, "NASDAQ");
      const xauusdCard = cachedToSignalCard(cachedXauusd ?? null, "XAUUSD");
      
      setSignalCards((prev) => {
        const updated = [...prev];
        if (nasdaqCard) {
          const idx = updated.findIndex(c => c.symbol === "NASDAQ");
          if (idx >= 0) updated[idx] = nasdaqCard as any;
        }
        if (xauusdCard) {
          const idx = updated.findIndex(c => c.symbol === "XAUUSD");
          if (idx >= 0) updated[idx] = xauusdCard as any;
        }
        return updated;
      });
    }
  }, [hasCachedData, cachedNasdaq, cachedXauusd]);
  const [newsItems, setNewsItems] = useState(initialNewsItems);
  const [claudeSentiments, setClaudeSentiments] = useState<{ nasdaq?: any; xauusd?: any }>({});
  const [claudePatterns, setClaudePatterns] = useState<{ nasdaq?: any; xauusd?: any }>({});
  const [claudePatternsLoading, setClaudePatternsLoading] = useState(false);
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
  const { t, locale } = useI18nStore();

  const refreshLive = async () => {
    try {
      const lang = locale;
      const [nasdaq, xauusd, news, taNasdaq, taXau] = await Promise.all([
        fetcher<any>("/api/run/nasdaq", { method: "POST", body: "{}" }),
        fetcher<any>("/api/run/xauusd", { method: "POST", body: "{}" }),
        fetcher<any>(`/api/news/feed?lang=${lang}`),
        fetcher<any>("/api/ta/snapshot?symbol=NDX.INDX"),
        fetcher<any>("/api/ta/snapshot?symbol=XAUUSD"),
      ]);
      // Claude sentiment + patterns per asset (live, not mock)
      const settled = await Promise.allSettled([
        fetcher<any>(`/api/claude/analyze-sentiment?symbol=NDX.INDX&lang=${lang}`, { method: "POST", body: "{}" }),
        fetcher<any>(`/api/claude/analyze-sentiment?symbol=XAUUSD&lang=${lang}`, { method: "POST", body: "{}" }),
        fetcher<any>(`/api/claude/analyze-patterns?lang=${lang}`, {
          method: "POST",
          body: JSON.stringify({ symbol: "NDX.INDX", timeframes }),
        }),
        fetcher<any>(`/api/claude/analyze-patterns?lang=${lang}`, {
          method: "POST",
          body: JSON.stringify({ symbol: "XAUUSD", timeframes }),
        }),
      ]);
      const [s1, s2, p1, p2] = settled;
      if (s1.status === "fulfilled" && s2.status === "fulfilled") {
        setClaudeSentiments({ nasdaq: s1.value, xauusd: s2.value });
      }
      if (p1.status === "fulfilled" && p2.status === "fulfilled") {
        setClaudePatterns({ nasdaq: p1.value, xauusd: p2.value });
      }

      const formatPrice = (value?: number | null) =>
        value === null || value === undefined ? "--" : value.toLocaleString(undefined, { maximumFractionDigits: 2 });

      setMarketTickers((prev) =>
        prev.map((t) => {
          if (t.label === "NASDAQ") return { ...t, price: formatPrice(nasdaq?.metrics?.current_price) };
          if (t.label === "XAU/USD") return { ...t, price: formatPrice(xauusd?.metrics?.current_price) };
          return t;
        })
      );

      const toLevel = (lvl: any) => {
        const price = Number(lvl?.price ?? 0);
        const strength = Number(lvl?.strength ?? 0);
        const hits = Number(lvl?.hits ?? 0);
        return {
          price,
          type: lvl?.kind === "resistance" ? ("resistance" as const) : ("support" as const),
          strength,
          reliability: Math.min(0.98, 0.6 + strength * 0.35),
          hits,
          lastTouched: new Date().toISOString(),
          distance: 0,
          distancePct: 0,
        };
      };

      const enrichFromTA = (card: any, ta: any) => {
        const price = Number(ta?.current_price ?? card.currentPrice);
        const supports = (ta?.supports ?? []).map(toLevel);
        const resistances = (ta?.resistances ?? []).map(toLevel);
        const sr = [...supports, ...resistances]
          .map((lvl: any) => {
            const distance = Number((price - lvl.price).toFixed(2));
            const distancePct = Number(((distance / (price || 1)) * 100).toFixed(2));
            return { ...lvl, distance, distancePct };
          })
          .slice(0, 4);

        const nearestSupport =
          sr
            .filter((l: any) => l.type === "support")
            .sort((a: any, b: any) => a.distance - b.distance)[0] ?? card.liveMetrics.nearestSupport;
        const nearestResistance =
          sr
            .filter((l: any) => l.type === "resistance")
            .sort((a: any, b: any) => b.distance - a.distance)[0] ?? card.liveMetrics.nearestResistance;

        const ema20 = Number(ta?.ema?.ema20 ?? card.liveMetrics.emaDistances.ema20.emaValue);
        const ema50 = Number(ta?.ema?.ema50 ?? card.liveMetrics.emaDistances.ema50.emaValue);
        const ema200 = Number(ta?.ema?.ema200 ?? card.liveMetrics.emaDistances.ema200.emaValue);

        return {
          ...card,
          currentPrice: price,
          liveMetrics: {
            ...card.liveMetrics,
            supportResistance: sr.length ? sr : card.liveMetrics.supportResistance,
            nearestSupport: { price: nearestSupport.price, distance: nearestSupport.distance, distancePct: nearestSupport.distancePct },
            nearestResistance: {
              price: nearestResistance.price,
              distance: nearestResistance.distance,
              distancePct: nearestResistance.distancePct,
            },
            emaDistances: {
              ema20: { ...card.liveMetrics.emaDistances.ema20, emaValue: ema20, distance: Number((price - ema20).toFixed(2)), distancePct: Number((((price - ema20) / (price || 1)) * 100).toFixed(2)) },
              ema50: { ...card.liveMetrics.emaDistances.ema50, emaValue: ema50, distance: Number((price - ema50).toFixed(2)), distancePct: Number((((price - ema50) / (price || 1)) * 100).toFixed(2)) },
              ema200: { ...card.liveMetrics.emaDistances.ema200, emaValue: ema200, distance: Number((price - ema200).toFixed(2)), distancePct: Number((((price - ema200) / (price || 1)) * 100).toFixed(2)) },
            },
            trendChannel: {
              ...card.liveMetrics.trendChannel,
              trendStrength:
                ta?.trend === "BULLISH" ? 0.75 : ta?.trend === "BEARISH" ? 0.25 : 0.5,
            },
          },
        };
      };

      const applyPrice = (card: any, currentPrice?: number | null, apiSignal?: any) => {
        const price = currentPrice ?? card.currentPrice;
        const sr = (card.liveMetrics?.supportResistance ?? []).map((lvl: any) => {
          const distance = Number((price - lvl.price).toFixed(2));
          const distancePct = Number(((distance / (price || 1)) * 100).toFixed(2));
          return { ...lvl, distance, distancePct };
        });
        const nearestSupport = sr.find((l: any) => l.type === "support") ?? card.liveMetrics.nearestSupport;
        const nearestResistance = sr.find((l: any) => l.type === "resistance") ?? card.liveMetrics.nearestResistance;
        
        // Extract trend from API metrics
        const apiTrend = apiSignal?.metrics?.trend || "NEUTRAL";
        const apiTrendStrength = apiSignal?.metrics?.trend_strength || 50;
        const apiVolatility = apiSignal?.metrics?.volatility || "MEDIUM";
        const apiVolumeConfirmed = apiSignal?.metrics?.volume_confirmed ?? true;
        
        return {
          ...card,
          currentPrice: price,
          signal: apiSignal?.signal ?? card.signal,
          trend: apiTrend,
          trendStrength: apiTrendStrength,
          volatility: apiVolatility,
          volumeConfirmed: apiVolumeConfirmed,
          confidence: apiSignal ? Math.round((apiSignal.confidence ?? 0) * 100) : card.confidence,
          liveMetrics: {
            ...card.liveMetrics,
            supportResistance: sr,
            nearestSupport: {
              ...card.liveMetrics.nearestSupport,
              price: nearestSupport.price,
              distance: nearestSupport.distance,
              distancePct: nearestSupport.distancePct,
            },
            nearestResistance: {
              ...card.liveMetrics.nearestResistance,
              price: nearestResistance.price,
              distance: nearestResistance.distance,
              distancePct: nearestResistance.distancePct,
            },
          },
        };
      };

      setSignalCards((prev) =>
        prev.map((card) => {
          if (card.symbol === "NASDAQ") return enrichFromTA(applyPrice(card, nasdaq?.metrics?.current_price, nasdaq), taNasdaq);
          if (card.symbol === "XAUUSD") return enrichFromTA(applyPrice(card, xauusd?.metrics?.current_price, xauusd), taXau);
          return card;
        })
      );

      const apiNews = (news?.news ?? []).slice(0, 10).map((n: any) => ({
        title: n.title,
        source: "MarketAux",
        sentiment: "neutral",
        time: locale === "tr" ? t("news.emptyTime") : "now",
      }));
      if (apiNews.length) {
        setNewsItems(apiNews);
      } else {
        // Ensure Turkish UI doesn't show English fallback headlines
        setNewsItems([
          {
            title: t("news.emptyTitle"),
            source: t("news.emptySource"),
            sentiment: "neutral",
            time: t("news.emptyTime"),
          },
        ]);
      }
    } catch {
      // keep existing UI values on error
    }
  };

  const runClaudePatterns = async () => {
    setClaudePatternsLoading(true);
    try {
      const lang = locale;
      const [patNasdaq, patXauusd] = await Promise.all([
        fetcher<any>(`/api/claude/analyze-patterns?lang=${lang}`, {
          method: "POST",
          body: JSON.stringify({ symbol: "NDX.INDX", timeframes }),
        }),
        fetcher<any>(`/api/claude/analyze-patterns?lang=${lang}`, {
          method: "POST",
          body: JSON.stringify({ symbol: "XAUUSD", timeframes }),
        }),
      ]);
      setClaudePatterns({ nasdaq: patNasdaq, xauusd: patXauusd });
    } finally {
      setClaudePatternsLoading(false);
    }
  };

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const interval = setInterval(() => {
      fetchAll();
      refreshLive();
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAll]);

  useEffect(() => {
    refreshLive();
  }, []);

  // When language changes, refetch dynamic content in that language.
  useEffect(() => {
    refreshLive();
  }, [locale]);

  useEffect(() => {
    if (theme === "morning") {
      document.documentElement.setAttribute("data-theme", "dawn");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }, [theme]);

  const formatPctShort = (value: number) => {
    const v = Number(value);
    const abs = Math.abs(v);
    if (!Number.isFinite(v)) return "--";
    if (abs >= 1000) return ">999%";
    return `${v.toFixed(2)}%`;
  };

  const formatSentimentLabel = (s?: string) => {
    if (s === "BULLISH") return t("common.bullish");
    if (s === "BEARISH") return t("common.bearish");
    if (s === "NEUTRAL") return t("common.neutral");
    return s ?? "--";
  };

  const renderSentimentBlock = (assetLabel: string, assetKey: "nasdaq" | "xauusd") => {
    const d = claudeSentiments[assetKey];
    const confidencePct = d?.confidence ? Math.round(d.confidence * 100) : 0;
    return (
      <div className="rounded-xl border border-white/5 bg-white/5 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{assetLabel}</p>
          <span className="text-xs text-textSecondary">
            {t("common.confidence")} {confidencePct}%
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between gap-4">
          <CircularProgress
            value={confidencePct}
            label={formatSentimentLabel(d?.sentiment)}
            sublabel={d?.sentiment === "BULLISH" ? "🐂" : d?.sentiment === "BEARISH" ? "🐻" : "—"}
            isInteractive
            onClick={() =>
              open(
                "trend_channel",
                { ...signalCards[assetKey === "nasdaq" ? 0 : 1].liveMetrics.trendChannel },
                assetKey === "nasdaq" ? "NASDAQ" : "XAUUSD",
                `${t("sentiment.subtitle")} (${assetLabel})`
              )
            }
          />
          <div className="flex-1 space-y-3">
            {[
              { label: t("sentiment.up"), value: d?.probability_up ?? 0, color: "bg-success" },
              { label: t("sentiment.down"), value: d?.probability_down ?? 0, color: "bg-danger" },
              { label: t("common.sideways"), value: d?.probability_sideways ?? 0, color: "bg-white/40" },
            ].map((item) => (
              <div key={`${assetLabel}-${item.label}`}>
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
        {Array.isArray(d?.key_factors) && d.key_factors.length > 0 && (
          <div className="mt-3 space-y-1 text-xs text-textSecondary">
            {d.key_factors.slice(0, 3).map((kf: any) => (
              <p key={`${assetLabel}-${kf.factor}`}>• {kf.factor}: {kf.reasoning}</p>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderClaudePatternsBlock = (assetLabel: string, assetKey: "nasdaq" | "xauusd") => {
    const d = claudePatterns[assetKey];
    const tf = activeTf;
    const block = d?.analyses?.[tf];
    const patterns = block?.detected_patterns ?? [];
    return (
      <div className="rounded-xl border border-white/5 bg-white/5 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{assetLabel}</p>
          <span className="text-xs text-textSecondary">{tf}</span>
        </div>
        <div className="mt-3 grid gap-3">
          {Array.isArray(patterns) && patterns.slice(0, 6).map((p: any) => (
            <div key={`${assetLabel}-${p.pattern_name}`} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 p-3">
              <div>
                <p className="text-sm font-semibold">{p.pattern_name}</p>
                <p className="text-xs text-textSecondary uppercase tracking-[0.2em]">{p.signal}</p>
              </div>
              <CircularProgress
                value={Number(p.completion_percentage ?? 0)}
                size={48}
                strokeWidth={6}
                colorClassName={
                  p.signal === "bullish"
                    ? "text-success"
                    : p.signal === "bearish"
                      ? "text-danger"
                      : "text-accent"
                }
                isInteractive
                onClick={() =>
                  open(
                    "trend_channel",
                    { ...signalCards[assetKey === "nasdaq" ? 0 : 1].liveMetrics.trendChannel },
                    assetKey === "nasdaq" ? "NASDAQ" : "XAUUSD",
                    `Pattern: ${p.pattern_name} (${assetLabel})`
                  )
                }
              />
            </div>
          ))}
          {!block && (
            <div className="text-xs text-textSecondary">{t("claudePatterns.analyzing")}</div>
          )}
        </div>
        {block?.summary && (
          <div className="mt-3 text-xs text-textSecondary">
            <p className="font-semibold">{block.recommendation}</p>
            <p className="mt-1">{block.summary}</p>
          </div>
        )}
      </div>
    );
  };

  const { isEditMode, layout } = useDashboardEdit();
  
  // Helper to check card visibility
  const isCardVisible = (cardId: string) => {
    const card = layout.cards.find(c => c.id === cardId);
    return card?.visible ?? true;
  };

  // Helper to get card config for SortableCard
  const getCard = (cardId: string): DashboardCard | undefined => layout.cards.find(c => c.id === cardId);

  // Get sorted cards for a column based on layout order
  const getColumnCards = (column: "left" | "center" | "right") => {
    return layout.cards
      .filter(c => c.column === column && c.visible)
      .sort((a, b) => a.order - b.order);
  };

  // Dynamic card content renderer
  const renderCardContent = (cardId: string): React.ReactNode => {
    switch (cardId) {
      case "signal-nasdaq":
        const nasdaqSignal = signalCards.find(s => s.symbol === "NASDAQ");
        if (!nasdaqSignal) return null;
        return renderSignalCard(nasdaqSignal);
      case "signal-xauusd":
        const xauusdSignal = signalCards.find(s => s.symbol === "XAUUSD");
        if (!xauusdSignal) return null;
        return renderSignalCard(xauusdSignal);
      case "pattern-engine":
        return <PatternEngineV2 />;
      case "claude-patterns":
        return renderClaudePatternCard();
      case "sentiment":
        return renderSentimentCard();
      case "news":
        return renderNewsCard();
      default:
        return null;
    }
  };

  // Signal card renderer
  const renderSignalCard = (signal: typeof signalCards[0]) => {
    const isDataLoading = !signal.currentPrice || signal.currentPrice === 0 || !hasCachedData;
    
    return (
      <div className="glass-card card-hover p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("trendAnalysis.title")}</p>
            <h3 className="mt-2 text-lg font-semibold">{signal.symbol}</h3>
          </div>
          {isDataLoading ? (
            <span className="rounded-full px-3 py-1 text-xs font-semibold bg-white/10 text-textSecondary flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Loading...
            </span>
          ) : (
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
              signal.trend === "BULLISH" ? "bg-success/20 text-success" :
              signal.trend === "BEARISH" ? "bg-danger/20 text-danger" : "bg-white/10 text-textSecondary"
            }`}>
              {signal.trend || "NEUTRAL"}
            </span>
          )}
        </div>
        <div className="mt-4 flex items-center justify-between gap-6">
          {isDataLoading ? (
            <div className="flex items-center justify-center w-[100px] h-[100px]">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin text-accent mx-auto" />
                <p className="mt-2 text-[10px] text-textSecondary">Calculating...</p>
              </div>
            </div>
          ) : (
            <CircularProgress
              value={signal.confidence}
              label={t("trendAnalysis.trendStrength")}
              sublabel={`${signal.confidence}%`}
              isInteractive
              onClick={() => open("trend_channel", { ...signal.liveMetrics.trendChannel }, signal.symbol as "NASDAQ" | "XAUUSD", `Trend Channel Overview (${signal.symbol})`)}
            />
          )}
          <div className="flex-1 space-y-2 text-xs text-textSecondary">
            <div className="flex items-center justify-between">
              <span>Nearest Support</span>
              <span className="font-mono">{isDataLoading ? "..." : `${signal.liveMetrics.nearestSupport.price} (${signal.liveMetrics.nearestSupport.distance})`}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Nearest Resistance</span>
              <span className="font-mono">{isDataLoading ? "..." : `${signal.liveMetrics.nearestResistance.price} (${signal.liveMetrics.nearestResistance.distance})`}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Trend Strength</span>
              <span className="font-mono">{isDataLoading ? "..." : `${Math.round(signal.liveMetrics.trendChannel.trendStrength * 100)}%`}</span>
            </div>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
          {(() => {
            if (isDataLoading) {
              return ["EMA 20", "EMA 50", "EMA 200", "Channel U", "Channel L", "S/R Bias"].map((label, index) => (
                <div key={`${signal.symbol}-${label}-loading-${index}`} className="rounded-lg border border-white/5 bg-white/5 p-3 flex flex-col items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-textSecondary" />
                  <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-textSecondary">{label}</p>
                </div>
              ));
            }
            const pipValue = signal.symbol === "XAUUSD" ? 0.1 : 1;
            const toPips = (dist: number) => Math.round(dist / pipValue);
            const metrics = [
              { label: "EMA 20", distance: signal.liveMetrics.emaDistances.ema20.distance, maxPips: 50 },
              { label: "EMA 50", distance: signal.liveMetrics.emaDistances.ema50.distance, maxPips: 100 },
              { label: "EMA 200", distance: signal.liveMetrics.emaDistances.ema200.distance, maxPips: 200 },
              { label: "Channel U", distance: signal.liveMetrics.nearestResistance.distance, maxPips: 50 },
              { label: "Channel L", distance: signal.liveMetrics.nearestSupport.distance, maxPips: 50 },
              { label: "S/R Bias", distance: Math.abs(signal.liveMetrics.nearestSupport.distance) < Math.abs(signal.liveMetrics.nearestResistance.distance) ? signal.liveMetrics.nearestSupport.distance : signal.liveMetrics.nearestResistance.distance, maxPips: 50 },
            ];
            return metrics.map((metric, index) => {
              const pips = toPips(metric.distance);
              const absPips = Math.abs(pips);
              const isAbove = metric.distance >= 0;
              const fillPercent = isAbove 
                ? Math.max(0, 100 - (absPips / metric.maxPips) * 100)
                : Math.min(100, (absPips / metric.maxPips) * 100);
              const colorClass = isAbove ? "text-success" : "text-danger";
              const pipsLabel = `${pips >= 0 ? "+" : ""}${pips} pips`;
              return (
                <div key={`${signal.symbol}-${metric.label}-${index}`} className="rounded-lg border border-white/5 bg-white/5 p-3 group relative">
                  <CircularProgress 
                    value={fillPercent} 
                    size={64} 
                    strokeWidth={8} 
                    sublabel={pipsLabel} 
                    colorClassName={colorClass}
                    isInteractive 
                    onClick={() => {}} 
                  />
                  <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-textSecondary">{metric.label}</p>
                  <div className="absolute -top-1 -right-1">
                    <div className={`w-2 h-2 rounded-full ${isAbove ? "bg-success" : "bg-danger"}`} />
                  </div>
                </div>
              );
            });
          })()}
        </div>
        <div className="mt-2 text-[9px] text-textSecondary/60 text-center">
          🟢 Fiyat seviyenin üstünde (yaklaştıkça dolar) • 🔴 Fiyat seviyenin altında (uzaklaştıkça dolar)
        </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {signal.liveMetrics.supportResistance.map((level) => (
          <div key={`${signal.symbol}-${level.price}`} className="flex items-center justify-between rounded-full border border-white/5 bg-white/5 px-3 py-2">
            <span className="font-mono">{level.price}</span>
            <span className={`text-[10px] uppercase ${level.type === "support" ? "text-success" : "text-danger"}`}>{level.type}</span>
            <span className="text-[10px] text-textSecondary">{Math.round(level.strength * 100)}%</span>
          </div>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
        {signal.metrics.map((metric) => (
          <div key={metric.label} className="rounded-lg border border-white/5 bg-white/5 p-3">
            <p className="text-textSecondary uppercase tracking-[0.2em] text-[10px]">{metric.label}</p>
            <p className="mt-1 font-mono text-sm">{metric.value}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-1 text-xs text-textSecondary">
        {signal.reasons.map((reason) => (<p key={reason}>• {reason}</p>))}
      </div>
    </div>
    );
  };

  // Claude patterns card renderer
  const renderClaudePatternCard = () => (
    <div className="glass-card card-hover p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("claudePatterns.title")}</p>
          <h3 className="mt-2 text-lg font-semibold">{t("claudePatterns.subtitle")}</h3>
        </div>
        <button onClick={runClaudePatterns} className="flex items-center gap-2 rounded-full border border-accent/40 px-3 py-1 text-xs uppercase tracking-[0.2em] text-accent">
          <Brain className="h-4 w-4" />
          {claudePatternsLoading ? t("claudePatterns.analyzing") : t("claudePatterns.analyzeCustom")}
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {timeframes.map((tf) => (
          <button key={tf} onClick={() => setActiveTf(tf)} className={`rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] transition ${activeTf === tf ? "border-accent text-accent" : "border-white/10 text-textSecondary hover:border-white/30"}`}>
            {tf}
          </button>
        ))}
      </div>
      <div className="mt-4 space-y-4">
        {renderClaudePatternsBlock("NASDAQ", "nasdaq")}
        {renderClaudePatternsBlock("XAUUSD", "xauusd")}
      </div>
      {customAnalysis && (
        <div className="mt-4 rounded-xl border border-accent/20 bg-accent/5 p-4 text-xs">
          <p className="text-sm font-semibold text-accent">{t("customAnalysis.title")}</p>
          <p className="mt-2 text-textSecondary">{customAnalysis.summary}</p>
          <ul className="mt-3 space-y-1 text-textSecondary">
            {customAnalysis.insights.map((insight) => (<li key={insight}>• {insight}</li>))}
          </ul>
        </div>
      )}
    </div>
  );

  // Sentiment card renderer
  const renderSentimentCard = () => (
    <div className="glass-card card-hover p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("sentiment.title")}</p>
          <h3 className="mt-2 text-lg font-semibold">{t("sentiment.subtitle")}</h3>
        </div>
        <span className="text-xs text-textSecondary">{t("common.live")}</span>
      </div>
      <div className="mt-4 space-y-4">
        {renderSentimentBlock("NASDAQ", "nasdaq")}
        {renderSentimentBlock("XAUUSD", "xauusd")}
      </div>
    </div>
  );

  // News card renderer
  const renderNewsCard = () => (
    <div className="glass-card card-hover p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("news.title")}</p>
          <h3 className="mt-2 text-lg font-semibold">{t("news.subtitle")}</h3>
        </div>
        <span className="text-xs text-textSecondary">30 {t("news.headlines")}</span>
      </div>
      <div className="mt-4 max-h-[300px] space-y-3 overflow-y-auto">
        {newsItems.map((item) => (
          <div key={item.title} className="rounded-xl border border-white/5 bg-white/5 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{item.title}</p>
                <p className="text-xs text-textSecondary">{item.source}</p>
              </div>
              <span className={`mt-1 h-2 w-2 rounded-full ${item.sentiment === "bullish" ? "bg-success" : item.sentiment === "bearish" ? "bg-danger" : "bg-white/40"}`} />
            </div>
            <p className="mt-2 text-xs text-textSecondary">{item.time}</p>
          </div>
        ))}
      </div>
    </div>
  );

  // Render a column with sorted cards
  const renderColumn = (column: "left" | "center" | "right") => {
    const cards = getColumnCards(column);
    return (
      <div className="flex flex-col gap-6">
        {cards.map((card) => (
          <SortableCard key={card.id} card={card}>
            {renderCardContent(card.id)}
          </SortableCard>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background text-textPrimary">
      {/* Premium Header */}
      <header className="relative overflow-hidden border-b border-white/10 bg-gradient-to-b from-slate-900 to-background">
        {/* Animated top border */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent to-transparent animate-pulse" />
        
        <div className="mx-auto flex h-[56px] md:h-[72px] max-w-7xl items-center justify-between px-4 md:px-6">
          {/* Logo & Title */}
          <div className="flex items-center gap-2 md:gap-3 group">
            <div className="relative">
              <div className="absolute -inset-1 rounded-full bg-accent/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative flex h-8 w-8 md:h-10 md:w-10 items-center justify-center rounded-full border border-white/20 bg-white/5 shadow-lg">
                <Activity className="h-4 w-4 md:h-5 md:w-5 text-accent" />
              </div>
            </div>
            <div>
              <p className="text-sm md:text-base font-bold bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">{t("header.title")}</p>
              <p className="hidden sm:block text-[10px] uppercase tracking-[0.3em] text-textSecondary">{t("header.subtitle")}</p>
            </div>
          </div>

          {/* Market Tickers */}
          <div className="hidden lg:flex items-center gap-6">
            {marketTickers.map((ticker) => {
              const isLoadingPrice = pricesLoading || ticker.price === "--" || ticker.price === "-";
              return (
                <div key={ticker.label} className="group flex items-center gap-3 px-4 py-2 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10 transition-all duration-300">
                  {isLoadingPrice ? (
                    <>
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 animate-pulse">
                        <Loader2 className="h-4 w-4 animate-spin text-textSecondary" />
                      </div>
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-textSecondary">{ticker.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-textSecondary">Loading...</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${ticker.trend === "up" ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                        {ticker.trend === "up" ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                      </div>
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-textSecondary">{ticker.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold">${ticker.price}</span>
                          <span className={`font-mono text-xs px-1.5 py-0.5 rounded ${ticker.trend === "up" ? "bg-success/20 text-success" : "bg-danger/20 text-danger"}`}>
                            {ticker.change}
                          </span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {/* Actions - Desktop */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/charts"
              className="group relative overflow-hidden flex items-center gap-2 rounded-xl bg-gradient-to-r from-accent/20 to-purple-500/20 border border-accent/30 px-4 py-2.5 text-sm font-semibold text-accent hover:from-accent/30 hover:to-purple-500/30 transition-all duration-300"
            >
              <LineChart className="h-4 w-4" />
              Grafikler
            </Link>
            <Link
              href="/trading"
              className="group relative overflow-hidden flex items-center gap-2 rounded-xl bg-gradient-to-r from-accent/20 to-purple-500/20 border border-accent/30 px-4 py-2.5 text-sm font-semibold text-accent hover:from-accent/30 hover:to-purple-500/30 transition-all duration-300"
            >
              <BarChart3 className="h-4 w-4" />
              AI Trading Panel
            </Link>
            <button
              onClick={fetchAll}
              className="relative overflow-hidden flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-white hover:from-emerald-500 hover:to-teal-400 transition-all duration-300"
            >
              <PlayCircle className="h-4 w-4" />
              {isLoading ? t("common.running") : t("common.runAnalysis")}
            </button>
            <button
              onClick={() => setTheme(theme === "evening" ? "morning" : "evening")}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-textSecondary hover:border-white/20 hover:bg-white/10 transition-all duration-300"
            >
              {theme === "evening" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <LanguageSwitcher />
            <EditModeButton />
            <div className="hidden lg:flex items-center gap-4 pl-4 border-l border-white/10">
              <label className="flex items-center gap-2 text-xs text-textSecondary cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => toggleAutoRefresh(e.target.checked)}
                  className="h-4 w-4 accent-accent rounded"
                />
                {t("common.auto30s")}
              </label>
              <div className="flex items-center gap-2 text-xs">
                <div className="relative">
                  <div className="h-2 w-2 rounded-full bg-success" />
                  <div className="absolute inset-0 h-2 w-2 rounded-full bg-success animate-ping" />
                </div>
                <span className="text-success font-medium">{t("common.live")}</span>
              </div>
            </div>
          </div>

          {/* Actions - Mobile */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={fetchAll}
              className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-r from-emerald-600 to-teal-500 text-white"
            >
              <PlayCircle className="h-4 w-4" />
            </button>
            <button
              onClick={() => setTheme(theme === "evening" ? "morning" : "evening")}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-textSecondary"
            >
              {theme === "evening" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </div>
        
        {/* Bottom gradient line */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      </header>

      <DraggableDashboard>
      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-4 px-4 py-4 md:gap-6 md:px-6 md:py-8 md:grid-cols-2 lg:grid-cols-3 pb-20 md:pb-8">
        {/* Dynamic columns based on layout.cards order */}
        {renderColumn("left")}
        {renderColumn("center")}
        {renderColumn("right")}

          {/* ML Prediction & Claude AI Section - Full Width Cards */}
          <div className="md:col-span-2 lg:col-span-3">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="h-5 w-5 text-accent" />
              <h2 className="text-lg font-bold">{t("panels.aiPrediction")}</h2>
              <Link
                href="/trading"
                className="ml-auto flex items-center gap-2 text-sm text-accent hover:underline"
              >
                <Sparkles className="h-4 w-4" />
                {t("panels.fullScreenView")} →
              </Link>
            </div>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              {/* NASDAQ Panels */}
              <div className="space-y-6">
                <div className="relative">
                  <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-emerald-500/20 to-teal-500/20 blur-sm" />
                  <div className="relative">
                    <MLPredictionPanel symbol="NDX.INDX" symbolLabel="NASDAQ" />
                  </div>
                </div>
                <div className="relative">
                  <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-sm" />
                  <div className="relative">
                    <ClaudeAnalysisPanel symbol="NDX.INDX" symbolLabel="NASDAQ" />
                  </div>
                </div>
              </div>
              {/* XAUUSD Panels */}
              <div className="space-y-6">
                <div className="relative">
                  <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-amber-500/20 to-yellow-500/20 blur-sm" />
                  <div className="relative">
                    <MLPredictionPanel symbol="XAUUSD" symbolLabel="XAUUSD" />
                  </div>
                </div>
                <div className="relative">
                  <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-sm" />
                  <div className="relative">
                    <ClaudeAnalysisPanel symbol="XAUUSD" symbolLabel="XAUUSD" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Order Block & Rhythm Detector Section - Full Width Stacked */}
          <div className="md:col-span-2 lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
            <OrderBlockPanelSimple symbol="NDX.INDX" symbolLabel="NASDAQ" />
            <OrderBlockPanelSimple symbol="XAUUSD" symbolLabel="XAUUSD" />
          </div>
          <div className="md:col-span-2 lg:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6">
            <RhythmDetectorSimple symbol="NDX.INDX" symbolLabel="NASDAQ" />
            <RhythmDetectorSimple symbol="XAUUSD" symbolLabel="XAUUSD" />
          </div>

          {/* Charts Section */}
          <div className="md:col-span-2 lg:col-span-3 grid grid-cols-1 xl:grid-cols-2 gap-6">
            <TradingChartWrapper 
              symbol="NDX.INDX" 
              symbolLabel="NASDAQ" 
              initialTimeframe="1d" 
              height={350} 
            />
            <TradingChartWrapper 
              symbol="XAUUSD" 
              symbolLabel="XAUUSD" 
              initialTimeframe="1d" 
              height={350} 
            />
          </div>
      </main>
      </DraggableDashboard>

      <DetailPanel
        isOpen={isOpen}
        onClose={close}
        title={title}
        symbol={symbol ?? "NASDAQ"}
        type={type}
        data={data}
      />

      {/* Edit Mode Floating Controls - Enhanced */}
      <EditModeControls />

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-nav md:hidden flex items-center justify-around">
        <button 
          onClick={fetchAll}
          className={`mobile-nav-item ${isLoading ? 'text-accent' : ''}`}
        >
          <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="text-[10px] mt-1">{isLoading ? t("common.running") : t("common.runAnalysis")}</span>
        </button>
        <Link href="/trading" className="mobile-nav-item">
          <BarChart3 className="h-5 w-5" />
          <span className="text-[10px] mt-1">Trading</span>
        </Link>
        <button className="mobile-nav-item active">
          <Activity className="h-5 w-5" />
          <span className="text-[10px] mt-1">Dashboard</span>
        </button>
        <LanguageSwitcher />
      </nav>
    </div>
  );
}
