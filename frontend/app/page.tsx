"use client";

import { useEffect, useMemo, useState, lazy, Suspense } from "react";
import { useRouter } from "next/navigation";
import { GripVertical } from "lucide-react";
import {
  EmelIcon, PulseIcon, SignalsIcon, LoadingIcon,
  ThemeSunIcon, ThemeMoonIcon, NasdaqIcon, GoldIcon,
  OilIcon, DaxIcon, ArrowUpIcon, ArrowDownIcon
} from "../components/ui/CustomIcons";
import Link from "next/link";
import { useAuthStore, useIsAuthenticated, waitForHydration } from "../lib/auth/store";
import CircularProgress from "../components/CircularProgress";
import DetailPanel from "../components/DetailPanel";
import { useDashboardStore, useDetailPanelStore } from "../lib/store";
import { fetcher } from "../lib/api";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { useI18nStore } from "../lib/i18n/store";
import SharedNavHeader from "../components/SharedNavHeader";
import Sidebar from "../components/Sidebar";
// Critical / lightweight - static imports
import MLFactorPanel from "../components/MLFactorPanel";
import { NasdaqEarningsPanel } from "../components/EarningsPanel";
import UserMenu from "../components/UserMenu";
import { TradingBackground } from "../components/TradingBackground";
import { LazyPanel } from "../components/LazyPanel";
import WSStatusBadge from "../components/WSStatusBadge";

// Heavy panels - dynamic imports (code-split into separate chunks)
const TradingChartWrapper = lazy(() => import("../components/TradingChartWrapper"));
const OrderBlockPanelSimple = lazy(() => import("../components/OrderBlockPanelSimple"));
const RhythmDetectorSimple = lazy(() => import("../components/RhythmDetectorSimple"));
const MLPredictionPanel = lazy(() => import("../components/MLPredictionPanel"));
const ClaudeAnalysisPanel = lazy(() => import("../components/ClaudeAnalysisPanel"));
const PatternEngineV2 = lazy(() => import("../components/PatternEngineV2"));
const AdvancedAnalysisPanel = lazy(() => import("../components/AdvancedAnalysisPanel"));
const InstitutionalDataPanel = lazy(() => import("../components/InstitutionalDataPanel"));
const CandlestickPatternPanel = lazy(() => import("../components/CandlestickPatternPanel"));
const StrategyPerformancePanel = lazy(() => import("../components/StrategyPerformancePanel"));
const EmelPanel = lazy(() => import("../components/panels/EmelPanel"));
const PulsePanel = lazy(() => import("../components/panels/PulsePanel"));
const PulseV3Panel = lazy(() => import("../components/panels/PulseV3Panel"));
const PulseMLPanel = lazy(() => import("../components/panels/PulseMLPanel"));
const ClearTrendPanel = lazy(() => import("../components/panels/ClearTrendPanelV3"));
const CyberpunkTrendPanel = lazy(() => import("../components/panels/CyberpunkTrendPanel"));
const LearningDashboardPanel = lazy(() => import("../components/LearningDashboardPanel"));
const LearningDashboardV2 = lazy(() => import("../components/panels/LearningDashboardV2"));
const ModelAnalysisPanel = lazy(() => import("../components/panels/ModelAnalysisPanel"));
const COMEXNewsPanel = lazy(() => import("../components/COMEXNewsPanel"));
const WhaleTrackerPanel = lazy(() => import("../components/WhaleTrackerPanel"));
const PredictionHistoryTable = lazy(() => import("../components/PredictionHistoryTable"));
const SMCPanel = lazy(() => import("../components/panels/SMCPanel"));
const MTFMatrixPanel = lazy(() => import("../components/panels/MTFMatrixPanel"));
const RiskRewardPanel = lazy(() => import("../components/panels/RiskRewardPanel"));
const COTWhalePanel = lazy(() => import("../components/panels/COTWhalePanel"));
const SeasonalityPanel = lazy(() => import("../components/panels/SeasonalityPanel"));
const SmartSetupPanel = lazy(() => import("../components/panels/SmartSetupPanel"));
const HarmonicVisualizerPanel = lazy(() => import("../components/panels/HarmonicVisualizerPanel"));
const StrategyOptimizerPanel = lazy(() => import("../components/panels/StrategyOptimizerPanel"));
const NewsChartCorrelationPanel = lazy(() => import("../components/panels/NewsChartCorrelationPanel"));
const NewsCorrelationDashboard = lazy(() => import("./news-correlation/page"));
import { useDashboardEdit, DashboardCard } from "../contexts/DashboardEditContext";
import { EditModeButton, EditModeControls, DraggableDashboard, SortableCard } from "../components/DraggableDashboard";
import { useLivePrices } from "../hooks/useLivePrices";
import { useCachedDashboardData, cachedToSignalCard } from "../hooks/useCachedDashboardData";
import { useSingleTimeframeAnalysis, type Timeframe, type TimeframeAnalysis } from "../hooks/useMTFAnalysis";

// Import Navigation and Views
import { useNavigationStore } from "../lib/store/navigation";
import ChartsView from "../components/views/ChartsView";
import TradingView from "../components/views/TradingView";
import AnalysisView from "../components/views/AnalysisView";
import SignalsView from "../components/views/SignalsView";

const initialMarketTickers = [
  { label: "NASDAQ", price: "--", change: "--%", trend: "up" as const },
  { label: "XAU/USD", price: "--", change: "--%", trend: "up" as const },
  { label: "DAX", price: "--", change: "--%", trend: "up" as const },
  { label: "US OIL", price: "--", change: "--%", trend: "up" as const },
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

const trendTimeframes: Timeframe[] = ["M1", "M5", "M15", "M30", "H1", "H4"];

export default function HomePage() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const { checkAuth } = useAuthStore();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const { activeView } = useNavigationStore();

  const [activeTf, setActiveTf] = useState<(typeof timeframes)[number]>("15m");
  const [theme, setTheme] = useState<"evening" | "morning">("evening");
  const [trendTf, setTrendTf] = useState<Timeframe>("M15");

  // Read theme from URL query parameter on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlTheme = params.get("theme");
    if (urlTheme === "morning") {
      setTheme("morning");
    }
  }, []);

  // Auth check
  const [isAuthed, setIsAuthed] = useState(false);
  useEffect(() => {
    const check = async () => {
      try {
        await waitForHydration();
        const authed = await checkAuth();
        setIsAuthed(authed);
        setIsCheckingAuth(false);
        if (!authed) {
          router.push("/welcome");
        }
      } catch (e) {
        console.error("[Auth] Check failed:", e);
        setIsCheckingAuth(false);
        router.push("/welcome");
      }
    };
    check();
    // Safety timeout: if auth check takes >5s, stop loading
    const timeout = setTimeout(() => {
      setIsCheckingAuth(false);
    }, 5000);
    return () => clearTimeout(timeout);
  }, []);

  // Live prices hook - updates every 15 seconds
  const { tickers: liveTickers, isLoading: pricesLoading } = useLivePrices(15000);

  // Cache hook - loads pre-computed data from backend immediately
  const { nasdaq: cachedNasdaq, xauusd: cachedXauusd, hasData: hasCachedData } = useCachedDashboardData();

  // MTF Analysis hooks - fetch real technical analysis per timeframe
  const { data: nasdaqMTF, isLoading: nasdaqMTFLoading } = useSingleTimeframeAnalysis("NDX.INDX", trendTf, 30000);
  const { data: xauusdMTF, isLoading: xauusdMTFLoading } = useSingleTimeframeAnalysis("XAUUSD", trendTf, 30000);

  const [manualTickers, setMarketTickers] = useState(initialMarketTickers);

  // Use live tickers if available and valid, otherwise fallback to manual fetch
  const marketTickers = useMemo(() => {
    const hasLiveData = liveTickers.some(t => t.price !== "--" && t.price !== "-");
    return hasLiveData ? liveTickers : manualTickers;
  }, [liveTickers, manualTickers]);
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

      // Trigger Pulse panel refreshes via custom event
      window.dispatchEvent(new CustomEvent("pulse-refresh"));
      // Trigger ALL dashboard panels refresh
      window.dispatchEvent(new CustomEvent("dashboard-refresh"));

      // Use allSettled so one failing endpoint doesn't block all
      const results = await Promise.allSettled([
        fetcher<any>("/api/run/nasdaq", { method: "POST", body: "{}" }),
        fetcher<any>("/api/run/xauusd", { method: "POST", body: "{}" }),
        fetcher<any>("/api/run/usoil", { method: "POST", body: "{}" }),
        fetcher<any>("/api/run/dax", { method: "POST", body: "{}" }),
        fetcher<any>(`/api/news/feed?lang=${lang}`),
        fetcher<any>("/api/ta/snapshot?symbol=NDX.INDX"),
        fetcher<any>("/api/ta/snapshot?symbol=XAUUSD"),
        fetcher<any>("/api/ta/snapshot?symbol=CL.COMM"),
        fetcher<any>("/api/ta/snapshot?symbol=GDAXI.INDX"),
      ]);
      const nasdaq = results[0].status === "fulfilled" ? results[0].value : null;
      const xauusd = results[1].status === "fulfilled" ? results[1].value : null;
      const usoil = results[2].status === "fulfilled" ? results[2].value : null;
      const dax = results[3].status === "fulfilled" ? results[3].value : null;
      const news = results[4].status === "fulfilled" ? results[4].value : null;
      const taNasdaq = results[5].status === "fulfilled" ? results[5].value : null;
      const taXau = results[6].status === "fulfilled" ? results[6].value : null;
      const taUsOil = results[7].status === "fulfilled" ? results[7].value : null;
      const taDax = results[8].status === "fulfilled" ? results[8].value : null;
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
          if (t.label === "US OIL") return { ...t, price: formatPrice(usoil?.metrics?.current_price) };
          if (t.label === "DAX") return { ...t, price: formatPrice(dax?.metrics?.current_price) };
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
    // DISABLED: Auto-refresh removed - WebSocket handles real-time updates now
    // The fetchAll() call was causing full page re-renders every 30 seconds
    // which broke the smooth live price experience and clock ticking
    return undefined;

    /* OLD CODE - REMOVED:
    if (!autoRefresh) return undefined;
    const interval = setInterval(() => {
      fetchAll();
      window.dispatchEvent(new CustomEvent("pulse-refresh"));
      window.dispatchEvent(new CustomEvent("dashboard-refresh"));
    }, 30000);
    return () => clearInterval(interval);
    */
  }, [autoRefresh, fetchAll]);

  // Defer heavy refreshLive so page renders instantly with cached data
  useEffect(() => {
    const timer = setTimeout(() => refreshLive(), 3000);
    return () => clearTimeout(timer);
  }, []);

  // When language changes, refetch dynamic content in that language.
  useEffect(() => {
    refreshLive();
  }, [locale]);

  useEffect(() => {
    if (theme === "morning") {
      document.documentElement.setAttribute("data-theme", "morning");
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
            sublabel={d?.sentiment === "BULLISH" ? <ArrowUpIcon size={20} className="text-success" /> : d?.sentiment === "BEARISH" ? <ArrowDownIcon size={20} className="text-danger" /> : "—"}
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

  // Dynamic card content renderer - ALL panels must be listed here for edit mode
  const renderCardContent = (cardId: string): React.ReactNode => {
    switch (cardId) {
      case "signal-nasdaq": {
        const nasdaqSignal = signalCards.find(s => s.symbol === "NASDAQ");
        if (!nasdaqSignal) return null;
        return renderSignalCard(nasdaqSignal);
      }
      case "signal-xauusd": {
        const xauusdSignal = signalCards.find(s => s.symbol === "XAUUSD");
        if (!xauusdSignal) return null;
        return renderSignalCard(xauusdSignal);
      }
      case "pattern-engine":
        return <PatternEngineV2 />;
      case "claude-patterns":
        return renderClaudePatternCard();
      case "sentiment":
        return renderSentimentCard();
      case "news":
        return renderNewsCard();
      case "comex-news":
        return <COMEXNewsPanel />;
      case "mtf-advanced":
      case "advanced-nasdaq":
      case "advanced-xauusd":
        return <AdvancedAnalysisPanel />;
      case "whale-tracker":
        return <WhaleTrackerPanel />;
      case "institutional-data":
        return <InstitutionalDataPanel />;
      case "candlestick-patterns":
        return <CandlestickPatternPanel symbol="XAUUSD" />;
      case "clear-trend":
        return <CyberpunkTrendPanel />;
      case "emel-panel":
        return <EmelPanel />;
      case "pulse-panel":
        return <PulsePanel />;
      case "pulse-v3":
        return <PulseV3Panel />;
      case "pulse-ml":
        return <PulseMLPanel />;
      case "learning-dashboard":
        return <LearningDashboardV2 />;
      case "strategy-performance":
        return <StrategyPerformancePanel />;
      case "model-analysis":
        return <ModelAnalysisPanel />;
      case "smc-panel":
        return <SMCPanel />;
      case "mtf-matrix":
        return <MTFMatrixPanel />;
      case "risk-reward":
        return <RiskRewardPanel />;
      case "cot-whale":
        return <COTWhalePanel />;
      case "seasonality":
        return <SeasonalityPanel />;
      case "smart-setup":
        return <SmartSetupPanel />;
      case "harmonic-visualizer":
        return <HarmonicVisualizerPanel />;
      case "strategy-optimizer":
        return <StrategyOptimizerPanel />;
      case "news-correlation":
        return <NewsChartCorrelationPanel />;
      default:
        return null;
    }
  };

  // Signal card renderer
  const getTimeframeMultiplier = (tf: Timeframe): number => {
    const multipliers: Record<Timeframe, number> = {
      "M1": 0.2,
      "M5": 0.5,
      "M15": 1,
      "M30": 1.5,
      "H1": 2,
      "H4": 4,
      "D1": 1,
    };
    return multipliers[tf];
  };

  const renderSignalCard = (signal: typeof signalCards[0]) => {
    const isMTFLoading = signal.symbol === "NASDAQ" ? nasdaqMTFLoading : xauusdMTFLoading;
    const mtfData = signal.symbol === "NASDAQ" ? nasdaqMTF : xauusdMTF;
    // Only block on cached data — MTF is an optional enhancement, never block on it
    const isDataLoading = !hasCachedData && !mtfData && (!signal.currentPrice || signal.currentPrice === 0);
    const tfMultiplier = getTimeframeMultiplier(trendTf);

    // Use MTF data if available, otherwise fall back to cached data
    const currentTrend = mtfData?.trend || signal.trend || "NEUTRAL";
    const currentConfidence = mtfData?.confidence || signal.confidence;
    const atrThreshold = mtfData?.max_pip_threshold || Math.round(50 * tfMultiplier);

    return (
      <div className="signal-card-premium p-5 shimmer-effect">
        <div className="flex items-center justify-between relative z-10">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("trendAnalysis.title")}</p>
            <h3 className="mt-2 text-lg font-semibold bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">{signal.symbol}</h3>
          </div>
          {isDataLoading || isMTFLoading ? (
            <span className="rounded-full px-3 py-1 text-xs font-semibold bg-white/10 text-textSecondary flex items-center gap-1">
              <LoadingIcon size={12} className="animate-spin" />
              Loading...
            </span>
          ) : (
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${currentTrend === "BULLISH" ? "bg-success/20 text-success" :
                currentTrend === "BEARISH" ? "bg-danger/20 text-danger" : "bg-white/10 text-textSecondary"
                }`}>
                {currentTrend}
              </span>
              {mtfData?.signal && (
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${mtfData.signal.includes("BUY") ? "bg-success/30 text-success" :
                  mtfData.signal.includes("SELL") ? "bg-danger/30 text-danger" : "bg-white/10 text-textSecondary"
                  }`}>
                  {mtfData.signal.replace("_", " ")}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Timeframe Tabs */}
        <div className="mt-3 flex gap-1 p-1 rounded-lg bg-white/5">
          {trendTimeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => setTrendTf(tf)}
              className={`flex-1 px-2 py-1.5 rounded-md text-[10px] font-semibold uppercase tracking-wider transition-all ${trendTf === tf
                ? "bg-accent text-white shadow-lg"
                : "text-textSecondary hover:text-white hover:bg-white/10"
                }`}
            >
              {tf}
            </button>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between gap-6">
          {isDataLoading || isMTFLoading ? (
            <div className="flex items-center justify-center w-[100px] h-[100px]">
              <div className="text-center">
                <LoadingIcon size={32} className="animate-spin text-accent mx-auto" />
                <p className="mt-2 text-[10px] text-textSecondary">Calculating...</p>
              </div>
            </div>
          ) : (
            <CircularProgress
              value={currentConfidence}
              label={t("trendAnalysis.trendStrength")}
              sublabel={`${Math.round(currentConfidence)}%`}
              isInteractive
              onClick={() => open("trend_channel", { ...signal.liveMetrics.trendChannel }, signal.symbol as "NASDAQ" | "XAUUSD", `Trend Channel Overview (${signal.symbol})`)}
            />
          )}
          <div className="flex-1 space-y-2 text-xs text-textSecondary">
            {mtfData ? (
              <>
                <div className="flex items-center justify-between">
                  <span>RSI (14)</span>
                  <span className={`font-mono ${mtfData.rsi14 > 70 ? "text-danger" : mtfData.rsi14 < 30 ? "text-success" : ""}`}>
                    {mtfData.rsi14.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>ATR SL/TP</span>
                  <span className="font-mono text-[10px]">
                    SL: {mtfData.atr.dynamic_sl_pips}p / TP: {mtfData.atr.dynamic_tp_pips}p
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Volatility</span>
                  <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${mtfData.atr.volatility_level === "LOW" ? "bg-success/20 text-success" :
                    mtfData.atr.volatility_level === "HIGH" || mtfData.atr.volatility_level === "EXTREME" ? "bg-danger/20 text-danger" :
                      "bg-white/10"
                    }`}>
                    {mtfData.atr.volatility_level}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Volume</span>
                  <span className={`font-mono text-[10px] ${mtfData.volume.volume_confirmation ? "text-success" : ""}`}>
                    {mtfData.volume.volume_ratio.toFixed(2)}x {mtfData.volume.volume_trend}
                  </span>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span>Nearest Support</span>
                  <span className="font-mono">{isDataLoading ? "..." : `${signal.liveMetrics.nearestSupport.price}`}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Nearest Resistance</span>
                  <span className="font-mono">{isDataLoading ? "..." : `${signal.liveMetrics.nearestResistance.price}`}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Trend Strength</span>
                  <span className="font-mono">{isDataLoading ? "..." : `${Math.round(signal.liveMetrics.trendChannel.trendStrength * 100)}%`}</span>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
          {(() => {
            if (isDataLoading) {
              return ["EMA 20", "EMA 50", "EMA 200", "Channel U", "Channel L", "S/R Bias"].map((label, index) => (
                <div key={`${signal.symbol}-${label}-loading-${index}`} className="rounded-lg border border-white/5 bg-white/5 p-3 flex flex-col items-center justify-center">
                  <LoadingIcon size={24} className="animate-spin text-textSecondary" />
                  <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-textSecondary">{label}</p>
                </div>
              ));
            }
            // Use MTF data if available for more accurate EMA distances
            const dynamicMaxPips = atrThreshold || Math.round(50 * tfMultiplier);
            const toPips = (dist: number) => Math.round(dist);

            // If MTF data is available, use it; otherwise fallback to cached data
            const ema20Dist = mtfData?.ema.ema20_distance ?? signal.liveMetrics.emaDistances.ema20.distance;
            const ema50Dist = mtfData?.ema.ema50_distance ?? signal.liveMetrics.emaDistances.ema50.distance;
            const ema200Dist = mtfData?.ema.ema200_distance ?? signal.liveMetrics.emaDistances.ema200.distance;

            const nearestSupport = mtfData?.supports?.[0];
            const nearestResistance = mtfData?.resistances?.[0];
            const supportDist = nearestSupport?.distance_pips ?? signal.liveMetrics.nearestSupport.distance;
            const resistanceDist = nearestResistance?.distance_pips ?? signal.liveMetrics.nearestResistance.distance;

            const metrics = [
              { label: `EMA 20`, distance: ema20Dist, maxPips: dynamicMaxPips, above: mtfData?.ema.price_above_ema20, period: 20, emaLevel: mtfData?.ema.ema20 },
              { label: `EMA 50`, distance: ema50Dist, maxPips: dynamicMaxPips * 2, above: mtfData?.ema.price_above_ema50, period: 50, emaLevel: mtfData?.ema.ema50 },
              { label: `EMA 200`, distance: ema200Dist, maxPips: dynamicMaxPips * 4, above: mtfData?.ema.price_above_ema200, period: 200, emaLevel: mtfData?.ema.ema200 },
              { label: "BB Upper", distance: mtfData ? (mtfData.current_price - mtfData.bollinger.upper) : resistanceDist, maxPips: dynamicMaxPips, isBollinger: true, bbLevel: mtfData?.bollinger.upper },
              { label: "BB Lower", distance: mtfData ? (mtfData.current_price - mtfData.bollinger.lower) : supportDist, maxPips: dynamicMaxPips, isBollinger: true, bbLevel: mtfData?.bollinger.lower },
              { label: "%B", distance: mtfData ? ((mtfData.bollinger.percent_b - 0.5) * 100) : 0, maxPips: 50, isBollinger: true, percentB: mtfData?.bollinger.percent_b },
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

              const handleMetricClick = () => {
                if (metric.period) {
                  open("ema_distance", {
                    period: metric.period,
                    distance: metric.distance,
                    distancePct: (metric.distance / (mtfData?.current_price || 1)) * 100,
                    isAbove: isAbove,
                    emaLevel: metric.emaLevel || 0,
                    currentPrice: mtfData?.current_price || 0,
                    timeframe: trendTf,
                  }, signal.symbol as "NASDAQ" | "XAUUSD", `EMA ${metric.period}`);
                } else if (metric.isBollinger) {
                  open("trend_channel", {
                    type: metric.label,
                    distance: metric.distance,
                    level: metric.bbLevel || metric.percentB || 0,
                    currentPrice: mtfData?.current_price || 0,
                    upper: mtfData?.bollinger.upper,
                    lower: mtfData?.bollinger.lower,
                    middle: mtfData?.bollinger.middle,
                    percentB: mtfData?.bollinger.percent_b,
                    trendStrength: 0.5,
                    timeframe: trendTf,
                  }, signal.symbol as "NASDAQ" | "XAUUSD", metric.label);
                }
              };

              return (
                <div key={`${signal.symbol}-${metric.label}-${index}`} className="rounded-lg border border-white/5 bg-white/5 p-3 group relative">
                  <CircularProgress
                    value={fillPercent}
                    size={64}
                    strokeWidth={8}
                    sublabel={pipsLabel}
                    colorClassName={colorClass}
                    isInteractive
                    onClick={handleMetricClick}
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
          <span className="font-semibold text-accent">{trendTf}</span> • 🟢 Above level • 🔴 Below level • Max: {Math.round(50 * tfMultiplier)}-{Math.round(200 * tfMultiplier)} pips
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
    <div className="glass-premium rounded-2xl p-5 transition-all duration-300 hover:shadow-glow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("claudePatterns.title")}</p>
          <h3 className="mt-2 text-lg font-semibold">{t("claudePatterns.subtitle")}</h3>
        </div>
        <button onClick={runClaudePatterns} className="flex items-center gap-2 rounded-full border border-accent/40 px-3 py-1 text-xs uppercase tracking-[0.2em] text-accent">
          <EmelIcon size={16} />
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
    <div className="glass-premium rounded-2xl p-5 transition-all duration-300 hover:shadow-glow-sm">
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
    <div className="glass-premium rounded-2xl p-5 transition-all duration-300 hover:shadow-glow-sm">
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

  // Cards that are always visible (top of page) - skip LazyPanel for these
  const alwaysVisibleCards = new Set(["signal-nasdaq", "signal-xauusd"]);

  // Render cards for a column as flat array (no wrapper div — CSS grid handles layout)
  const renderColumnCards = (column: "left" | "center" | "right") => {
    const cards = getColumnCards(column).filter(c => c.size !== "full");
    return cards.map((card) => (
      <SortableCard key={card.id} card={card}>
        {alwaysVisibleCards.has(card.id) ? (
          renderCardContent(card.id)
        ) : (
          <LazyPanel fallbackHeight={250}>
            {renderCardContent(card.id)}
          </LazyPanel>
        )}
      </SortableCard>
    ));
  };

  // Show loading while checking auth
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent via-purple-500 to-cyan-500 flex items-center justify-center animate-pulse">
              <LoadingIcon size={32} className="text-white" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LoadingIcon size={20} className="animate-spin text-accent" />
            <span className="text-textSecondary">Yükleniyor...</span>
          </div>
        </div>
      </div>
    );
  }

  // If not authenticated, will redirect (handled in useEffect)
  if (!isAuthenticated && !isAuthed) {
    return null;
  }

  return (
    <div className="min-h-screen text-textPrimary relative">
      {/* Sidebar Navigation */}
      <div className="relative z-[999]">
        <Sidebar />
      </div>

      {/* Main Content - offset by sidebar width */}
      <div className="transition-all duration-300" style={{ marginLeft: 72 }}>
        {/* Animated Background with Star Particles */}
        <TradingBackground />

        {/* ─── FLOATING PRICE STICKERS ─── */}
        <div className="sticky top-0 z-40 py-2 px-4 md:px-6 pointer-events-none">
          <div className="flex items-center justify-center relative">
            <div className="flex items-center gap-6 overflow-x-auto scrollbar-none pointer-events-auto">
              {marketTickers.map((ticker) => {
                const isLoadingPrice = pricesLoading || ticker.price === "--" || ticker.price === "-";
                const isUp = ticker.trend === "up";
                const accent = ticker.label === "NASDAQ"
                  ? { from: "#3b82f6", glow: "rgba(59,130,246,0.25)" }
                  : ticker.label === "XAU/USD"
                    ? { from: "#f59e0b", glow: "rgba(245,158,11,0.25)" }
                    : ticker.label === "DAX"
                      ? { from: "#10b981", glow: "rgba(16,185,129,0.25)" }
                      : { from: "#ef4444", glow: "rgba(239,68,68,0.25)" };
                const IconComponent = ticker.label === "NASDAQ" ? NasdaqIcon : ticker.label === "XAU/USD" ? GoldIcon : ticker.label === "DAX" ? DaxIcon : OilIcon;
                return (
                  <div key={ticker.label} className="flex items-center gap-2 px-2 py-1 flex-shrink-0 bg-transparent border-0 shadow-none rounded-none">
                    <IconComponent size={20} style={{ color: accent.from }} />
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black uppercase tracking-[0.15em] opacity-90" style={{ color: accent.from }}>{ticker.label}</span>
                      <div className="flex items-baseline gap-1.5 mt-0.5">
                        <span className="font-mono text-sm font-black text-white">{isLoadingPrice ? "---" : `$${ticker.price}`}</span>
                        {!isLoadingPrice && (
                          <span className={`text-[10px] font-black tracking-tighter flex items-center gap-0.5 ${isUp ? "text-emerald-400" : "text-rose-400"}`} style={{ textShadow: `0 0 10px ${isUp ? 'rgba(52,211,153,0.5)' : 'rgba(251,113,133,0.5)'}` }}>
                            {isUp ? <ArrowUpIcon size={10} /> : <ArrowDownIcon size={10} />} {ticker.change}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Top Right Controls (Theme Toggle & WS Status) */}
            <div className="absolute right-0 flex items-center gap-3 pointer-events-auto">
              <WSStatusBadge />
              <button onClick={() => setTheme(theme === "evening" ? "morning" : "evening")}
                className="flex h-8 w-8 items-center justify-center text-slate-400 hover:text-white transition-all bg-transparent border-0">
                {theme === "evening" ? <ThemeSunIcon size={18} /> : <ThemeMoonIcon size={18} />}
              </button>
            </div>
          </div>
        </div>

        {/* ─── DYNAMIC VIEW RENDERING ─── */}
        <div className="w-full relative min-h-screen pointer-events-auto">
          {activeView === "dashboard" && (
            <div className="animate-in fade-in duration-300">
              <DraggableDashboard>
                <main className="w-full px-3 sm:px-4 md:px-6 lg:px-8 py-4 md:py-6 pb-20 md:pb-8">
                  {/* ML Factor + Earnings - Inline row above grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                    <MLFactorPanel
                      baseConfidence={signalCards[0]?.confidence || 60}
                      applyToSymbols={["NDX.INDX", "XAUUSD"]}
                      locale={locale}
                    />
                    <NasdaqEarningsPanel />
                  </div>
                  {/* ═══ CLEAR TREND — Full-width hero panel ═══ */}
                  {getCard("clear-trend")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={300}>
                        <CyberpunkTrendPanel />
                      </LazyPanel>
                    </div>
                  )}

                  {/* ═══ RISK-REWARD — Full-width panel under CyberpunkTrend ═══ */}
                  {getCard("risk-reward")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={300}>
                        <RiskRewardPanel />
                      </LazyPanel>
                    </div>
                  )}

                  {/* ═══ PULSE PANELS ═══ */}
                  {getCard("pulse-panel")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={300}>
                        <PulsePanel />
                      </LazyPanel>
                    </div>
                  )}
                  {getCard("pulse-ml")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={300}>
                        <PulseMLPanel />
                      </LazyPanel>
                    </div>
                  )}
                  {getCard("pulse-v3")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={300}>
                        <PulseV3Panel />
                      </LazyPanel>
                    </div>
                  )}
                  {getCard("emel-panel")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={300}>
                        <EmelPanel />
                      </LazyPanel>
                    </div>
                  )}

                  {/* ═══ HARMONIC VISUALIZER ═══ */}
                  {getCard("harmonic-visualizer")?.visible !== false && (
                    <div className="mb-6 w-full">
                      <LazyPanel fallbackHeight={400}>
                        <HarmonicVisualizerPanel />
                      </LazyPanel>
                    </div>
                  )}

                </main>
              </DraggableDashboard>
            </div>
          )}
          {activeView === "charts" && <ChartsView />}
          {activeView === "trading" && <TradingView />}
          {activeView === "analysis" && <AnalysisView />}
          {activeView === "signals" && <SignalsView />}
          {activeView === "news-correlation" && (
            <div className="w-full h-[calc(100vh-64px)] overflow-hidden bg-[#0a0a0a]">
              <NewsCorrelationDashboard />
            </div>
          )}
        </div>

        <DetailPanel
          isOpen={isOpen}
          onClose={close}
          title={title}
          symbol={symbol ?? "NASDAQ"}
          type={type}
          data={data}
        />

        {/* Edit Mode Floating Controls - Enhanced */}
        {activeView === "dashboard" && <EditModeControls />}

        {/* Mobile Bottom Navigation */}
        <nav className="mobile-nav md:hidden flex items-center justify-around">
          <button
            onClick={fetchAll}
            className={`mobile-nav-item ${isLoading ? 'text-accent' : ''}`}
          >
            <LoadingIcon size={20} className={isLoading ? 'animate-spin' : ''} />
            <span className="text-[10px] mt-1">{isLoading ? t("common.running") : t("common.runAnalysis")}</span>
          </button>
          <Link href="/trading" className="mobile-nav-item">
            <SignalsIcon size={20} />
            <span className="text-[10px] mt-1">Trading</span>
          </Link>
          <button className="mobile-nav-item active">
            <PulseIcon size={20} />
            <span className="text-[10px] mt-1">Dashboard</span>
          </button>
          <Link href="/account" className="mobile-nav-item">
            <UserMenu />
          </Link>
        </nav>
      </div>{/* end sidebar content wrapper */}
    </div>
  );
}
