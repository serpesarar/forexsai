"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { createChart, ColorType, type CandlestickData, type Time } from "lightweight-charts";
import {
  ArrowLeft,
  Activity,
  BarChart3,
  Grip,
  Info,
  LayoutDashboard,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import AuthGuard from "@/components/AuthGuard";
import { TradingBackground } from "@/components/TradingBackground";
import SymbolTopNav from "@/components/SymbolTopNav";
import { LazyPanel } from "@/components/LazyPanel";
import MLPredictionPanel from "@/components/MLPredictionPanel";
import ClaudeAnalysisPanelV2 from "@/components/ClaudeAnalysisPanelV2";
import LearningDashboardPanel from "@/components/LearningDashboardPanel";
import PredictionHistoryTable from "@/components/PredictionHistoryTable";
import StrategyPerformanceDashboard from "@/components/StrategyPerformanceDashboard";
import WhaleTrackerPanel from "@/components/WhaleTrackerPanel";
import PatternEngineV2 from "@/components/PatternEngineV2";
import CandlestickPatternPanel from "@/components/CandlestickPatternPanel";
import {
  DraggableDashboard,
  DroppableColumn,
  EditModeButton,
  EditModeControls,
  SortableCard,
} from "@/components/DraggableDashboard";
import {
  DashboardEditProvider,
  type DashboardCard,
  type DashboardLayout,
  useColumnCards,
} from "@/contexts/DashboardEditContext";
import { useLivePrices } from "@/hooks/useLivePrices";
import { fetcher } from "@/lib/api";
import { useI18nStore } from "@/lib/i18n/store";
import MetaEnginePanel from "@/components/panels/MetaEnginePanel";
import PulsePanel from "@/components/panels/PulsePanel";
import PulseMLPanel from "@/components/panels/PulseMLPanel";
import PulseV3Panel from "@/components/panels/PulseV3Panel";
import EmelPanel from "@/components/panels/EmelPanel";
import EmelInversePanel from "@/components/panels/EmelInversePanel";
import ReboundDetectionPanel from "@/components/panels/ReboundDetectionPanel";
import COTWhalePanel from "@/components/panels/COTWhalePanel";
import MTFMatrixPanel from "@/components/panels/MTFMatrixPanel";
import ClearTrendPanelV3 from "@/components/panels/ClearTrendPanelV3";
import SMCPanel from "@/components/panels/SMCPanel";
import RiskRewardPanel from "@/components/panels/RiskRewardPanel";
import SeasonalityPanel from "@/components/panels/SeasonalityPanel";
import SmartSetupPanel from "@/components/panels/SmartSetupPanel";
import OrderBlockPanelUnified from "@/components/OrderBlockPanelUnified";

const SYMBOL = "NDX.INDX";
const SYMBOL_LABEL = "NASDAQ";
const PATTERN_SYMBOL = "NASDAQ" as const;
const STORAGE_KEY = "nasdaq-dashboard-layout-v1";

type ChartTimeframe = "5m" | "15m" | "1h" | "4h";

type OhlcvResponse = {
  data?: Array<{
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
  }>;
};

// Dashboard layout yapılandırması - draggable grid için
const GRID_LAYOUT: DashboardLayout = {
  version: 1,
  cards: [
    { id: "pulse-panel", title: "Pulse 1", column: "left", order: 1, visible: true, size: "large", collapsed: false },
    { id: "pulse-ml", title: "Pulse 2", column: "left", order: 2, visible: true, size: "large", collapsed: false },
    { id: "pulse-v3", title: "Pulse 3", column: "left", order: 3, visible: true, size: "large", collapsed: false },
    { id: "emel-panel", title: "EMEL", column: "left", order: 4, visible: true, size: "large", collapsed: false },
    { id: "emel-inverse-panel", title: "EMEL Inverse", column: "left", order: 5, visible: true, size: "large", collapsed: false },
    { id: "rebound-detection", title: "Rebound Detection", column: "left", order: 6, visible: true, size: "large", collapsed: false },
    { id: "learning-dashboard", title: "Learning Dashboard", column: "left", order: 7, visible: true, size: "large", collapsed: false },
    { id: "cot-whale", title: "COT Whale", column: "left", order: 8, visible: true, size: "large", collapsed: false },
    { id: "clear-trend", title: "Clear Trend", column: "right", order: 1, visible: true, size: "large", collapsed: false },
    { id: "mtf-matrix", title: "MTF Matrix", column: "right", order: 2, visible: true, size: "large", collapsed: false },
    { id: "smc-panel", title: "Smart Money Concepts", column: "right", order: 3, visible: true, size: "large", collapsed: false },
    { id: "risk-reward", title: "Risk Reward", column: "right", order: 4, visible: true, size: "large", collapsed: false },
    { id: "pattern-engine", title: "Pattern Engine", column: "right", order: 5, visible: true, size: "large", collapsed: false },
    { id: "whale-tracker", title: "Whale Tracker", column: "right", order: 6, visible: true, size: "large", collapsed: false },
    { id: "candlestick-patterns", title: "Candlestick Patterns", column: "right", order: 7, visible: true, size: "large", collapsed: false },
    { id: "seasonality", title: "Seasonality", column: "right", order: 8, visible: true, size: "large", collapsed: false },
    { id: "smart-setup", title: "Smart Setup", column: "right", order: 9, visible: true, size: "large", collapsed: false },
  ],
};

// Her kart için fallback yükseklikleri (lazy loading için)
const FALLBACK_HEIGHTS: Record<string, number> = {
  "pulse-panel": 380,
  "pulse-ml": 360,
  "pulse-v3": 360,
  "emel-panel": 420,
  "emel-inverse-panel": 360,
  "rebound-detection": 320,
  "learning-dashboard": 420,
  "cot-whale": 340,
  "clear-trend": 380,
  "mtf-matrix": 340,
  "smc-panel": 420,
  "risk-reward": 320,
  "pattern-engine": 340,
  "whale-tracker": 320,
  "candlestick-patterns": 320,
  "seasonality": 320,
  "smart-setup": 340,
};

// Framer Motion animasyon ayarları
function frame(index: number) {
  return {
    initial: { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.28, delay: index * 0.025, ease: "easeOut" as const },
  };
}

// Küçük bilgi chip'i komponenti
function InfoChip({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-medium text-slate-300"
    >
      {children}
    </motion.div>
  );
}

// Reusable TooltipWrapper - Her panel kartı için bilgi baloncuğu
interface TooltipWrapperProps {
  children: React.ReactNode;
  tooltipText: string;
  title: string;
}

function TooltipWrapper({ children, tooltipText, title }: TooltipWrapperProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="relative">
      {/* Bilgi ikonu - sağ üst köşe */}
      <div
        className="absolute -top-3 -right-3 z-20 flex h-7 w-7 cursor-pointer items-center justify-center rounded-full border border-slate-700 bg-slate-800 shadow-lg transition-all hover:border-cyan-500/50 hover:bg-slate-700"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <Info className="h-4 w-4 text-cyan-400" />
      </div>

      {/* Framer Motion tooltip */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute -top-2 right-8 z-50 w-72 rounded-2xl border border-slate-700 bg-slate-900 p-4 shadow-2xl shadow-black/50"
          >
            <div className="mb-2 flex items-center gap-2">
              <Info className="h-4 w-4 text-cyan-400" />
              <span className="text-sm font-semibold text-slate-200">{title}</span>
            </div>
            <p className="text-xs leading-5 text-slate-400">{tooltipText}</p>
            {/* Ok işareti */}
            <div className="absolute -right-2 top-6 h-4 w-4 rotate-45 border-r border-t border-slate-700 bg-slate-900" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ana içerik */}
      <div className="relative">
        {children}
      </div>
    </div>
  );
}

// Her panel için tooltip metinleri (Türkçe/İngilizce)
const PANEL_TOOLTIPS: Record<string, { tr: string; en: string }> = {
  "pulse-panel": {
    tr: "6 bileşenli algoritmik scalp skorlaması (100 puan sistemi). Momentum, hacim ve volatilite faktörlerini birleştirir.",
    en: "6-component algorithmic scalp scoring (100-point system). Combines momentum, volume and volatility factors.",
  },
  "pulse-ml": {
    tr: "Makine öğrenimi destekli Pulse versiyonu. LSTM ve LightGBM modellerinin konsensüsü.",
    en: "ML-enhanced Pulse version. Consensus of LSTM and LightGBM models.",
  },
  "pulse-v3": {
    tr: "En gelişmiş Pulse versiyonu. Multi-timeframe analiz ve pattern recognition entegrasyonu.",
    en: "Most advanced Pulse version. Multi-timeframe analysis and pattern recognition integration.",
  },
  "emel-panel": {
    tr: "9 checkpoint sistemi ile güçlü sinyal üretimi. Eğilim, momentum ve yapısal dayanıklılık kontrolü.",
    en: "Strong signal generation with 9-checkpoint system. Trend, momentum and structural resilience checks.",
  },
  "emel-inverse-panel": {
    tr: "EMEL algoritmasının ters yön analizi. Düşüş eğilimlerini erken tespit için optimize edilmiştir.",
    en: "Inverse direction analysis of EMEL algorithm. Optimized for early detection of downtrends.",
  },
  "rebound-detection": {
    tr: "Fiyat sekme noktalarını tespit eder. Destek/direnç kırılmaları ve momentum dönüşleri.",
    en: "Detects price bounce points. Support/resistance breaks and momentum reversals.",
  },
  "learning-dashboard": {
    tr: "Öğrenme sistemi performans metrikleri. Model doğruluğu ve sinyal kalitesi geçmişi.",
    en: "Learning system performance metrics. Model accuracy and signal quality history.",
  },
  "cot-whale": {
    tr: "COT (Commitment of Traders) raporları ve balina pozisyonlama analizi. Kurumsal akış takibi.",
    en: "COT (Commitment of Traders) reports and whale positioning analysis. Institutional flow tracking.",
  },
  "clear-trend": {
    tr: "ICT tabanlı HTF bias + FVG + Swing Structure. Yüksek zaman dilimli trend yönü analizi.",
    en: "ICT-based HTF bias + FVG + Swing Structure. High timeframe trend direction analysis.",
  },
  "mtf-matrix": {
    tr: "Multi-Timeframe Matrix. 5m'den günlüğe kadar tüm zaman dilimlerinde sinyal konsensüsü.",
    en: "Multi-Timeframe Matrix. Signal consensus across all timeframes from 5m to daily.",
  },
  "smc-panel": {
    tr: "Smart Money Concepts: CHoCH, BOS, FVG, Order Block, Liquidity ve Market Structure tam analizi.",
    en: "Smart Money Concepts: Full analysis of CHoCH, BOS, FVG, Order Block, Liquidity and Market Structure.",
  },
  "risk-reward": {
    tr: "Risk/Ödül hesaplayıcı. Otomatik stop-loss ve take-profit seviyeleri önerisi.",
    en: "Risk/Reward calculator. Automatic stop-loss and take-profit level suggestions.",
  },
  "pattern-engine": {
    tr: "Harmonik ve klasik pattern tanıma motoru. AB=CD, Gartley, Bat, Butterfly ve daha fazlası.",
    en: "Harmonic and classic pattern recognition engine. AB=CD, Gartley, Bat, Butterfly and more.",
  },
  "whale-tracker": {
    tr: "Büyük oyuncu hareket takibi. Anormal hacim ve odaak hacim analizi.",
    en: "Big player movement tracking. Abnormal volume and delta volume analysis.",
  },
  "candlestick-patterns": {
    tr: "Japon mum bar desenleri tanıma. Doji, Engulfing, Hammer, Shooting Star ve 30+ pattern.",
    en: "Japanese candlestick pattern recognition. Doji, Engulfing, Hammer, Shooting Star and 30+ patterns.",
  },
  "seasonality": {
    tr: "Mevsimsellik analizi. Tarihsel performans istatistikleri ve aylık/getiri dağılımı.",
    en: "Seasonality analysis. Historical performance statistics and monthly/return distribution.",
  },
  "smart-setup": {
    tr: "Akıllı setup önerileri. Risk/ödül optimize edilmiş giriş noktaları.",
    en: "Smart setup suggestions. Risk/reward optimized entry points.",
  },
};

// Üst bölüm için özel tooltip'ler
const TOP_SECTION_TOOLTIPS = {
  meta: {
    tr: "Tüm modellerin (Pulse, EMEL, SMC, ML) konsensüs skorunu gösterir. Büyük resim meta-sinyali üretir.",
    en: "Shows consensus score of all models (Pulse, EMEL, SMC, ML). Generates big picture meta-signal.",
  },
  strategy: {
    tr: "Risk skorlama + pozisyon büyüklüğü önerisi. VIX, ADX, Volatilite ve News Proximity dikkate alır.",
    en: "Risk scoring + position size recommendation. Considers VIX, ADX, Volatility and News Proximity.",
  },
};

function NasdaqHeroChart({ timeframe }: { timeframe: ChartTimeframe }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [candles, setCandles] = useState<CandlestickData<Time>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetcher<OhlcvResponse>(
          `/api/data/ohlcv?symbol=${encodeURIComponent(SYMBOL)}&timeframe=${timeframe}&limit=180`
        );
        const nextCandles = (response.data || [])
          .filter((item) => item && item.timestamp)
          .map((item) => ({
            time: Math.floor(item.timestamp / 1000) as Time,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
          }));
        if (alive) {
          setCandles(nextCandles);
        }
      } catch (err) {
        if (alive) {
          setError(err instanceof Error ? err.message : "Chart data unavailable");
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    };

    load();
    const timer = window.setInterval(load, 60_000);

    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [timeframe]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "#0b1120" },
        textColor: "#94a3b8",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(148,163,184,0.08)" },
        horzLines: { color: "rgba(148,163,184,0.08)" },
      },
      rightPriceScale: {
        borderColor: "rgba(148,163,184,0.15)",
      },
      timeScale: {
        borderColor: "rgba(148,163,184,0.15)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
      },
      handleScroll: {
        vertTouchDrag: false,
      },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#f43f5e",
      wickUpColor: "#10b981",
      wickDownColor: "#f43f5e",
      borderUpColor: "#10b981",
      borderDownColor: "#f43f5e",
    });

    if (candles.length > 0) {
      series.setData(candles);
      chart.timeScale().fitContent();
    }

    const resize = () => {
      if (!container) return;
      const { width, height } = container.getBoundingClientRect();
      chart.applyOptions({ width, height });
    };

    resize();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
    };
  }, [candles]);

  return (
    <div className="relative h-[320px] overflow-hidden rounded-3xl border border-slate-800 bg-[#0b1120]">
      <div ref={containerRef} className="h-full w-full" />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/35 backdrop-blur-[1px]">
          <RefreshCw className="h-6 w-6 animate-spin text-slate-400" />
        </div>
      )}
      {!loading && error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/60 px-6 text-center text-sm text-slate-400">
          {error}
        </div>
      )}
    </div>
  );
}

function GridCardRenderer({ card, index, locale }: { card: DashboardCard; index: number; locale: string }) {
  let content: React.ReactNode = null;

  switch (card.id) {
    case "pulse-panel":
      content = <PulsePanel symbol={SYMBOL} />;
      break;
    case "pulse-ml":
      content = <PulseMLPanel symbol={SYMBOL} />;
      break;
    case "pulse-v3":
      content = <PulseV3Panel symbol={SYMBOL} />;
      break;
    case "emel-panel":
      content = <EmelPanel symbol={SYMBOL} />;
      break;
    case "emel-inverse-panel":
      content = <EmelInversePanel symbol={SYMBOL} />;
      break;
    case "rebound-detection":
      content = <ReboundDetectionPanel symbol={SYMBOL} />;
      break;
    case "learning-dashboard":
      content = <LearningDashboardPanel symbol={SYMBOL} />;
      break;
    case "cot-whale":
      content = <COTWhalePanel symbol={SYMBOL} />;
      break;
    case "clear-trend":
      content = <ClearTrendPanelV3 symbol={SYMBOL} />;
      break;
    case "mtf-matrix":
      content = <MTFMatrixPanel symbol={SYMBOL} />;
      break;
    case "smc-panel":
      content = <SMCPanel lockedSymbol={SYMBOL} />;
      break;
    case "risk-reward":
      content = <RiskRewardPanel symbol={SYMBOL} />;
      break;
    case "pattern-engine":
      content = <PatternEngineV2 symbol={PATTERN_SYMBOL} />;
      break;
    case "whale-tracker":
      content = <WhaleTrackerPanel symbol={SYMBOL} />;
      break;
    case "candlestick-patterns":
      content = <CandlestickPatternPanel symbol={SYMBOL} />;
      break;
    case "seasonality":
      content = <SeasonalityPanel symbol={SYMBOL} />;
      break;
    case "smart-setup":
      content = <SmartSetupPanel symbol={SYMBOL} />;
      break;
    default:
      content = null;
  }

  if (!content) return null;

  const tooltipText = PANEL_TOOLTIPS[card.id]?.[locale as "tr" | "en"] || PANEL_TOOLTIPS[card.id]?.en || "";

  return (
    <SortableCard key={card.id} card={card}>
      <TooltipWrapper tooltipText={tooltipText} title={card.title}>
        <motion.div {...frame(index)}>
          <LazyPanel fallbackHeight={FALLBACK_HEIGHTS[card.id] || 320}>{content}</LazyPanel>
        </motion.div>
      </TooltipWrapper>
    </SortableCard>
  );
}

function NasdaqEditableGrid({ locale }: { locale: string }) {
  const leftCards = useColumnCards("left");
  const rightCards = useColumnCards("right");

  return (
    <DraggableDashboard>
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <DroppableColumn columnId="left">
          {leftCards.map((card, index) => (
            <GridCardRenderer key={card.id} card={card} index={index} locale={locale} />
          ))}
        </DroppableColumn>
        <DroppableColumn columnId="right">
          {rightCards.map((card, index) => (
            <GridCardRenderer key={card.id} card={card} index={index + leftCards.length} locale={locale} />
          ))}
        </DroppableColumn>
      </div>
    </DraggableDashboard>
  );
}

// Üst bölüm kartı - Meta Engine ve Strategy için tooltip'li kart
function TopSectionCard({
  children,
  title,
  tooltipText,
  delay = 0,
}: {
  children: React.ReactNode;
  title: string;
  tooltipText: string;
  delay?: number;
}) {
  return (
    <motion.div {...frame(delay)} className="relative">
      <TooltipWrapper tooltipText={tooltipText} title={title}>
        <div className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl md:p-6">
          {children}
        </div>
      </TooltipWrapper>
    </motion.div>
  );
}

function NasdaqPageContent() {
  const { locale } = useI18nStore();
  const { tickers, isLoading, lastUpdate } = useLivePrices();
  const [timeframe, setTimeframe] = useState<ChartTimeframe>("15m");
  const nasdaqTicker = useMemo(() => tickers.find((item) => item.label === SYMBOL_LABEL), [tickers]);
  const isPositive = (nasdaqTicker?.change || "").startsWith("+");

  const copy = locale === "tr"
    ? {
        title: "NASDAQ Komuta Merkezi",
        subtitle: "NDX.INDX için tüm ana analiz panelleri tek ekranda.",
        back: "Ana dashboard",
        quick1: "Canlı WebSocket akışı",
        quick2: "NASDAQ'a kilitli paneller",
        quick3: "Sürükle bırak düzeni",
        refresh: "Panelleri yenile",
        overview: "Piyasa Özeti",
        edit: "Düzeni özelleştir",
        ai: "AI Prediction Stack",
        history: "Prediction History",
        orderBlocks: "Order Blocks & SMC Flow",
        updated: "Son güncelleme",
        metaTitle: "Meta-Intelligence Engine",
        strategyTitle: "Strategy Optimizer",
      }
    : {
        title: "NASDAQ Command Center",
        subtitle: "All major NDX.INDX analysis panels in a single focused route.",
        back: "Main dashboard",
        quick1: "Live WebSocket stream",
        quick2: "Panels locked to NASDAQ",
        quick3: "Drag and drop layout",
        refresh: "Refresh panels",
        overview: "Market Overview",
        edit: "Customize layout",
        ai: "AI Prediction Stack",
        history: "Prediction History",
        orderBlocks: "Order Blocks & SMC Flow",
        updated: "Last update",
        metaTitle: "Meta-Intelligence Engine",
        strategyTitle: "Strategy Optimizer",
      };

  return (
    <div className="relative min-h-screen overflow-x-hidden text-slate-100">
      <TradingBackground />
      <SymbolTopNav />
      <DashboardEditProvider storageKey={STORAGE_KEY} defaultLayout={GRID_LAYOUT}>
        <div className="relative z-10 mx-auto flex w-full max-w-[1680px] flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
          {/* EN ÜST - NASDAQ Command Center Başlık */}
          <motion.div {...frame(0)} className="flex items-center justify-between rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl md:p-6">
            <div className="flex items-center gap-4">
              <Link href="/" className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-3 py-2 text-sm text-slate-400 transition hover:text-white">
                <ArrowLeft className="h-4 w-4" />
                {copy.back}
              </Link>
              <div>
                <h1 className="text-3xl font-black tracking-tight text-white md:text-5xl">{copy.title}</h1>
                <p className="mt-1 text-sm text-slate-400">{copy.subtitle}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-black text-white">
                {isLoading || !nasdaqTicker ? "--" : `$${nasdaqTicker.price}`}
              </span>
              {!isLoading && nasdaqTicker?.change && (
                <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-bold ${isPositive ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                  {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  {nasdaqTicker.change}
                </span>
              )}
            </div>
          </motion.div>

          {/* Clear Trend (tam genişlik) */}
          <motion.section {...frame(1)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl shadow-black/20 backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              <div>
                <h2 className="text-lg font-bold text-white">
                  {locale === "tr" ? "Clear Trend" : "Clear Trend"}
                </h2>
                <p className="text-sm text-slate-400">
                  {locale === "tr" ? "ICT tabanlı trend analizi ve FVG" : "ICT-based trend analysis and FVG"}
                </p>
              </div>
            </div>
            <LazyPanel fallbackHeight={380}>
              <ClearTrendPanelV3 symbol={SYMBOL} />
            </LazyPanel>
          </motion.section>

          {/* Meta Engine + Strategy Optimizer (yan yana tam genişlik) */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <TopSectionCard
              title={copy.metaTitle}
              tooltipText={locale === "tr" ? TOP_SECTION_TOOLTIPS.meta.tr : TOP_SECTION_TOOLTIPS.meta.en}
              delay={2}
            >
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-emerald-500/20 bg-emerald-500/10">
                  <Activity className="h-5 w-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{copy.metaTitle}</h3>
                  <p className="text-sm text-slate-400">
                    {locale === "tr" ? "Tüm modellerin konsensüs skoru" : "Consensus score of all models"}
                  </p>
                </div>
              </div>
              <LazyPanel fallbackHeight={320}>
                <MetaEnginePanel symbol={SYMBOL} />
              </LazyPanel>
            </TopSectionCard>

            <TopSectionCard
              title={copy.strategyTitle}
              tooltipText={locale === "tr" ? TOP_SECTION_TOOLTIPS.strategy.tr : TOP_SECTION_TOOLTIPS.strategy.en}
              delay={3}
            >
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-cyan-500/20 bg-cyan-500/10">
                  <BarChart3 className="h-5 w-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{copy.strategyTitle}</h3>
                  <p className="text-sm text-slate-400">
                    {locale === "tr" ? "Risk skorlama ve pozisyon önerisi" : "Risk scoring and position suggestion"}
                  </p>
                </div>
              </div>
              <LazyPanel fallbackHeight={320}>
                <StrategyPerformanceDashboard symbol={SYMBOL} />
              </LazyPanel>
            </TopSectionCard>
          </div>

          {/* DRAGGABLE GRID - 2 kolonlu sürüklenebilir grid */}
          <motion.div {...frame(4)}>
            <NasdaqEditableGrid locale={locale} />
          </motion.div>

          {/* AI PREDICTION STACK - ML + Claude yan yana */}
          <motion.section {...frame(5)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl shadow-black/20 backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-cyan-400" />
              <div>
                <h2 className="text-lg font-bold text-white">{copy.ai}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "Model ve Claude analizi aynı bölümde." : "Model and Claude analysis in a single section."}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-6 2xl:grid-cols-2">
              <LazyPanel fallbackHeight={520}>
                <MLPredictionPanel symbol={SYMBOL} symbolLabel={SYMBOL_LABEL} />
              </LazyPanel>
              <LazyPanel fallbackHeight={520}>
                <ClaudeAnalysisPanelV2 symbol={SYMBOL} symbolLabel={SYMBOL_LABEL} />
              </LazyPanel>
            </div>
          </motion.section>

          {/* PREDICTION HISTORY */}
          <motion.section {...frame(6)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl shadow-black/20 backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <LayoutDashboard className="h-5 w-5 text-emerald-400" />
              <div>
                <h2 className="text-lg font-bold text-white">{copy.history}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "NASDAQ tahmin geçmişi ve öğrenme çıktıları." : "NASDAQ prediction history and learning outcomes."}</p>
              </div>
            </div>
            <LazyPanel fallbackHeight={520}>
              <PredictionHistoryTable symbol={SYMBOL} />
            </LazyPanel>
          </motion.section>

          {/* ORDER BLOCK & SMC FLOW (Unified) */}
          <motion.section {...frame(7)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl shadow-black/20 backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-fuchsia-400" />
              <div>
                <h2 className="text-lg font-bold text-white">{copy.orderBlocks}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "Order block ve smart money akışı tek panelde." : "Order block and smart money flow in one panel."}</p>
              </div>
            </div>
            <LazyPanel fallbackHeight={620}>
              <OrderBlockPanelUnified symbol={SYMBOL} />
            </LazyPanel>
          </motion.section>
        </div>
        <EditModeControls />
      </DashboardEditProvider>
    </div>
  );
}

export default function NasdaqPage() {
  return (
    <AuthGuard>
      <NasdaqPageContent />
    </AuthGuard>
  );
}
