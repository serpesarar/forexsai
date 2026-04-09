"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Activity,
  BarChart3,
  Grip,
  Info,
  LayoutDashboard,
  TrendingDown,
  TrendingUp,
  Maximize2,
  Minimize2,
} from "lucide-react";
import AuthGuard from "@/components/AuthGuard";
import { TradingBackground } from "@/components/TradingBackground";
import SymbolTopNav from "@/components/SymbolTopNav";
import { LazyPanel } from "@/components/LazyPanel";
import MLPredictionPanel from "@/components/MLPredictionPanel";
import ClaudeAnalysisPanelV2 from "@/components/ClaudeAnalysisPanelV2";
import PredictionHistoryTable from "@/components/PredictionHistoryTable";
import StrategyPerformanceDashboard from "@/components/StrategyPerformanceDashboard";
import WhaleTrackerPanel from "@/components/WhaleTrackerPanel";
import PatternEngineV2 from "@/components/PatternEngineV2";
import CandlestickPatternPanel from "@/components/CandlestickPatternPanel";
import HarmonicVisualizerPanel from "@/components/panels/HarmonicVisualizerPanel";
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
import { useI18nStore } from "@/lib/i18n/store";
import MetaEnginePanel from "@/components/panels/MetaEnginePanel";
import PulsePanel from "@/components/panels/PulsePanel";
import PulseMLPanel from "@/components/panels/PulseMLPanel";
import PulseV3Panel from "@/components/panels/PulseV3Panel";
import EmelPanel from "@/components/panels/EmelPanel";
import COTWhalePanel from "@/components/panels/COTWhalePanel";
import MTFMatrixPanel from "@/components/panels/MTFMatrixPanel";
import ClearTrendPanelV3 from "@/components/panels/ClearTrendPanelV3";
import SMCPanel from "@/components/panels/SMCPanel";
import RiskRewardPanel from "@/components/panels/RiskRewardPanel";
import SmartSetupPanel from "@/components/panels/SmartSetupPanel";
import OrderBlockPanelUnified from "@/components/OrderBlockPanelUnified";

const SYMBOL = "XAUUSD";
const SYMBOL_LABEL = "XAU/USD";
const PATTERN_SYMBOL = "XAUUSD" as const;
const STORAGE_KEY = "xauusd-dashboard-layout-v1";

const GRID_LAYOUT: DashboardLayout = {
  version: 1,
  cards: [
    { id: "pulse-panel", title: "Pulse 1 – Algo Scalp", column: "left", order: 1, visible: true, size: "large", collapsed: false },
    { id: "pulse-ml", title: "Pulse 2 – ML Hybrid", column: "left", order: 2, visible: true, size: "large", collapsed: false },
    { id: "pulse-v3", title: "Pulse 3 – Hybrid MTF", column: "left", order: 3, visible: true, size: "large", collapsed: false },
    { id: "emel-panel", title: "EMEL Panel", column: "left", order: 4, visible: true, size: "large", collapsed: false },
    { id: "smc-panel", title: "Smart Money Concepts", column: "right", order: 1, visible: true, size: "large", collapsed: false },
    { id: "order-block-unified", title: "Order Blocks (Unified)", column: "right", order: 2, visible: true, size: "large", collapsed: false },
    { id: "mtf-matrix", title: "MTF Confluence Matrix", column: "right", order: 3, visible: true, size: "large", collapsed: false },
    { id: "cot-whale-intel", title: "COT + Whale Intelligence", column: "right", order: 4, visible: true, size: "large", collapsed: false },
    { id: "risk-reward", title: "Risk/Reward Optimizer", column: "right", order: 5, visible: true, size: "large", collapsed: false },
    { id: "harmonic-visualizer", title: "Harmonic Visualizer", column: "right", order: 6, visible: true, size: "large", collapsed: false },
    { id: "whale-tracker", title: "Whale Tracker", column: "right", order: 7, visible: true, size: "large", collapsed: false },
    { id: "candlestick-patterns", title: "Candlestick Patterns", column: "right", order: 8, visible: true, size: "large", collapsed: false },
    { id: "smart-setup", title: "Smart Setup Generator", column: "right", order: 9, visible: true, size: "large", collapsed: false },
  ],
};

const FALLBACK_HEIGHTS: Record<string, number> = {
  "pulse-panel": 440,
  "pulse-ml": 440,
  "pulse-v3": 440,
  "emel-panel": 480,
  "smc-panel": 520,
  "order-block-unified": 480,
  "mtf-matrix": 460,
  "cot-whale-intel": 460,
  "risk-reward": 420,
  "harmonic-visualizer": 520,
  "whale-tracker": 440,
  "candlestick-patterns": 440,
  "smart-setup": 440,
};

function frame(index: number) {
  return {
    initial: { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.28, delay: index * 0.025, ease: "easeOut" as const },
  };
}

const PANEL_TOOLTIPS: Record<string, { tr: string; en: string }> = {
  "pulse-panel": { tr: "6 bileşenli algoritmik scalp.", en: "6-component algorithmic scalp." },
  "pulse-ml": { tr: "ML destekli Pulse.", en: "ML-enhanced Pulse." },
  "pulse-v3": { tr: "Gelişmiş Pulse MTF.", en: "Advanced Pulse MTF." },
  "emel-panel": { tr: "9 checkpoint sinyal sistemi.", en: "9-checkpoint signal system." },
  "smc-panel": { tr: "Smart Money Concepts.", en: "Smart Money Concepts." },
  "order-block-unified": { tr: "Order Blocks Unified.", en: "Order Blocks Unified." },
  "mtf-matrix": { tr: "Multi-Timeframe Matrix.", en: "Multi-Timeframe Matrix." },
  "cot-whale-intel": { tr: "COT + Whale Intel.", en: "COT + Whale Intel." },
  "risk-reward": { tr: "Risk/Ödül hesaplayıcı.", en: "Risk/Reward calculator." },
  "harmonic-visualizer": { tr: "Harmonik pattern görselleştirici.", en: "Harmonic pattern visualizer." },
  "whale-tracker": { tr: "Balina takip.", en: "Whale tracking." },
  "candlestick-patterns": { tr: "Mum desenleri.", en: "Candlestick patterns." },
  "smart-setup": { tr: "Akıllı setup.", en: "Smart setup." },
};

const TOP_SECTION_TOOLTIPS = {
  meta: { tr: "Tüm modellerin konsensüs skoru.", en: "All models consensus score." },
  strategy: { tr: "Risk skorlama.", en: "Risk scoring." },
  clearTrend: { tr: "ICT trend analizi.", en: "ICT trend analysis." },
};

interface MaximizeWrapperProps {
  children: React.ReactNode;
  title: string;
  tooltipText: string;
  isMaximized: boolean;
  onMaximize: () => void;
}

function MaximizeWrapper({ children, title, tooltipText, isMaximized, onMaximize }: MaximizeWrapperProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (isMaximized) {
    return (
      <div className="fixed inset-4 z-50 rounded-3xl border border-slate-700 bg-slate-950 p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold text-white">{title}</h3>
            <span className="text-xs text-slate-400">{tooltipText}</span>
          </div>
          <button onClick={onMaximize} className="rounded-full bg-slate-800 p-2 hover:bg-slate-700">
            <Minimize2 className="h-5 w-5 text-amber-400" />
          </button>
        </div>
        <div className="h-[calc(100%-80px)] overflow-auto">{children}</div>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={onMaximize}
        className="absolute -top-3 right-6 z-20 flex h-7 w-7 items-center justify-center rounded-full border border-slate-700 bg-slate-800 shadow-lg hover:border-amber-500/50"
      >
        <Maximize2 className="h-3.5 w-3.5 text-amber-400" />
      </button>
      <div
        className="absolute -top-3 -right-3 z-20 flex h-7 w-7 cursor-pointer items-center justify-center rounded-full border border-slate-700 bg-slate-800 shadow-lg hover:border-cyan-500/50"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Info className="h-4 w-4 text-cyan-400" />
      </div>
      {showTooltip && (
        <div className="absolute -top-2 right-8 z-50 w-64 rounded-xl border border-slate-700 bg-slate-900 p-3 shadow-xl">
          <p className="text-xs text-slate-400">{tooltipText}</p>
        </div>
      )}
      {children}
    </div>
  );
}

function GridCardRenderer({
  card,
  index,
  locale,
  maximizedCard,
  onMaximize,
}: {
  card: DashboardCard;
  index: number;
  locale: string;
  maximizedCard: string | null;
  onMaximize: (id: string | null) => void;
}) {
  let content: React.ReactNode = null;

  switch (card.id) {
    case "pulse-panel": content = <PulsePanel symbol={SYMBOL} />; break;
    case "pulse-ml": content = <PulseMLPanel symbol={SYMBOL} />; break;
    case "pulse-v3": content = <PulseV3Panel symbol={SYMBOL} />; break;
    case "emel-panel": content = <EmelPanel symbol={SYMBOL} />; break;
    case "order-block-unified": content = <OrderBlockPanelUnified symbol={SYMBOL} />; break;
    case "mtf-matrix": content = <MTFMatrixPanel symbol={SYMBOL} />; break;
    case "cot-whale-intel": content = <COTWhalePanel symbol={SYMBOL} />; break;
    case "smc-panel": content = <SMCPanel lockedSymbol={SYMBOL} />; break;
    case "risk-reward": content = <RiskRewardPanel symbol={SYMBOL} />; break;
    case "harmonic-visualizer": content = <HarmonicVisualizerPanel />; break;
    case "whale-tracker": content = <WhaleTrackerPanel symbol={SYMBOL} />; break;
    case "candlestick-patterns": content = <CandlestickPatternPanel symbol={SYMBOL} />; break;
    case "smart-setup": content = <SmartSetupPanel symbol={SYMBOL} />; break;
  }

  if (!content) return null;

  const tooltipText = PANEL_TOOLTIPS[card.id]?.[locale as "tr" | "en"] || "";
  const isMaximized = maximizedCard === card.id;

  return (
    <SortableCard key={card.id} card={card}>
      <MaximizeWrapper
        title={card.title}
        tooltipText={tooltipText}
        isMaximized={isMaximized}
        onMaximize={() => onMaximize(isMaximized ? null : card.id)}
      >
        <motion.div {...frame(index)} className={isMaximized ? "hidden" : ""}>
          <LazyPanel fallbackHeight={FALLBACK_HEIGHTS[card.id] || 420}>
            {content}
          </LazyPanel>
        </motion.div>
      </MaximizeWrapper>
    </SortableCard>
  );
}

function XauusdEditableGrid({
  locale,
  maximizedCard,
  onMaximize,
}: {
  locale: string;
  maximizedCard: string | null;
  onMaximize: (id: string | null) => void;
}) {
  const leftCards = useColumnCards("left");
  const rightCards = useColumnCards("right");

  return (
    <DraggableDashboard>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <DroppableColumn columnId="left">
          {leftCards.map((card, index) => (
            <GridCardRenderer
              key={card.id}
              card={card}
              index={index}
              locale={locale}
              maximizedCard={maximizedCard}
              onMaximize={onMaximize}
            />
          ))}
        </DroppableColumn>
        <DroppableColumn columnId="right">
          {rightCards.map((card, index) => (
            <GridCardRenderer
              key={card.id}
              card={card}
              index={index + leftCards.length}
              locale={locale}
              maximizedCard={maximizedCard}
              onMaximize={onMaximize}
            />
          ))}
        </DroppableColumn>
      </div>
    </DraggableDashboard>
  );
}

function TopSectionCard({
  children,
  title,
  tooltipText,
  delay = 0,
  isMaximized,
  onMaximize,
}: {
  children: React.ReactNode;
  title: string;
  tooltipText: string;
  delay?: number;
  isMaximized?: boolean;
  onMaximize?: () => void;
}) {
  return (
    <motion.div {...frame(delay)} className="relative">
      <MaximizeWrapper
        title={title}
        tooltipText={tooltipText}
        isMaximized={!!isMaximized}
        onMaximize={() => onMaximize?.()}
      >
        {!isMaximized && (
          <div className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl backdrop-blur-xl md:p-6 w-full">
            {children}
          </div>
        )}
      </MaximizeWrapper>
    </motion.div>
  );
}

function XauusdPageContent() {
  const { locale } = useI18nStore();
  const { tickers, isLoading } = useLivePrices();
  const [maximizedCard, setMaximizedCard] = useState<string | null>(null);
  const [maximizedTop, setMaximizedTop] = useState<"meta" | "strategy" | null>(null);

  const xauusdTicker = useMemo(() => tickers.find((item) => item.label === SYMBOL_LABEL), [tickers]);
  const isPositive = (xauusdTicker?.change || "").startsWith("+");

  const copy = {
    title: locale === "tr" ? "Altın (XAU/USD) Komuta Merkezi" : "Gold (XAU/USD) Command Center",
    subtitle: locale === "tr" ? "XAUUSD için tüm ana analiz panelleri." : "All major XAUUSD analysis panels.",
    back: locale === "tr" ? "Ana dashboard" : "Main dashboard",
    ai: locale === "tr" ? "AI Prediction Stack" : "AI Prediction Stack",
    history: locale === "tr" ? "Prediction History" : "Prediction History",
    orderBlocks: locale === "tr" ? "Order Blocks & SMC Flow" : "Order Blocks & SMC Flow",
    metaTitle: locale === "tr" ? "Meta-Intelligence Engine" : "Meta-Intelligence Engine",
    strategyTitle: locale === "tr" ? "Strategy Optimizer" : "Strategy Optimizer",
    clearTrendTitle: locale === "tr" ? "Clear Trend Analysis" : "Clear Trend Analysis",
  };

  return (
    <div className="relative min-h-screen overflow-x-hidden text-slate-100">
      <TradingBackground />
      <SymbolTopNav />

      {maximizedCard && (
        <div className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm" onClick={() => setMaximizedCard(null)} />
      )}

      <DashboardEditProvider storageKey={STORAGE_KEY} defaultLayout={GRID_LAYOUT}>
        <div className="relative z-10 mx-auto flex w-full flex-col gap-4 px-3 sm:px-4 md:px-6 lg:px-8 py-4 md:py-6">
          {/* 1. Header */}
          <motion.div {...frame(0)} className="flex items-center justify-between rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl backdrop-blur-xl md:p-6">
            <div className="flex items-center gap-4">
              <Link href="/" className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-3 py-2 text-sm text-slate-400 hover:text-white">
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
                {isLoading || !xauusdTicker ? "--" : `$${xauusdTicker.price}`}
              </span>
              {!isLoading && xauusdTicker?.change && (
                <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-bold ${isPositive ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
                  {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  {xauusdTicker.change}
                </span>
              )}
            </div>
          </motion.div>

          {/* 2. Clear Trend */}
          <motion.section {...frame(1)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-amber-400" />
              <div>
                <h2 className="text-xl font-bold text-white">{copy.clearTrendTitle}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "ICT tabanlı trend analizi" : "ICT-based trend analysis"}</p>
              </div>
            </div>
            <LazyPanel fallbackHeight={480}>
              <ClearTrendPanelV3 symbol={SYMBOL} />
            </LazyPanel>
          </motion.section>

          {/* 4. Meta + Strategy */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <TopSectionCard
              title={copy.metaTitle}
              tooltipText={locale === "tr" ? TOP_SECTION_TOOLTIPS.meta.tr : TOP_SECTION_TOOLTIPS.meta.en}
              delay={2}
              isMaximized={maximizedTop === "meta"}
              onMaximize={() => setMaximizedTop(maximizedTop === "meta" ? null : "meta")}
            >
              <LazyPanel fallbackHeight={420}>
                <MetaEnginePanel symbol={SYMBOL} />
              </LazyPanel>
            </TopSectionCard>

            <TopSectionCard
              title={copy.strategyTitle}
              tooltipText={locale === "tr" ? TOP_SECTION_TOOLTIPS.strategy.tr : TOP_SECTION_TOOLTIPS.strategy.en}
              delay={2}
              isMaximized={maximizedTop === "strategy"}
              onMaximize={() => setMaximizedTop(maximizedTop === "strategy" ? null : "strategy")}
            >
              <LazyPanel fallbackHeight={420}>
                <StrategyPerformanceDashboard symbol={SYMBOL} />
              </LazyPanel>
            </TopSectionCard>
          </div>

          {/* 5. Draggable Grid */}
          <motion.div {...frame(3)}>
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Grip className="h-5 w-5 text-amber-400" />
                Panel Grid
              </h2>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 px-2 py-2">
                <EditModeButton />
              </div>
            </div>
            <XauusdEditableGrid locale={locale} maximizedCard={maximizedCard} onMaximize={setMaximizedCard} />
          </motion.div>

          {/* 6. AI Stack */}
          <motion.section {...frame(4)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-amber-400" />
              <div>
                <h2 className="text-lg font-bold text-white">{copy.ai}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "Model ve Claude analizi" : "Model and Claude analysis"}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 2xl:grid-cols-2">
              <LazyPanel fallbackHeight={520}>
                <MLPredictionPanel symbol={SYMBOL} symbolLabel={SYMBOL_LABEL} />
              </LazyPanel>
              <LazyPanel fallbackHeight={520}>
                <ClaudeAnalysisPanelV2 symbol={SYMBOL} symbolLabel={SYMBOL_LABEL} />
              </LazyPanel>
            </div>
          </motion.section>

          {/* 7. History */}
          <motion.section {...frame(5)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <LayoutDashboard className="h-5 w-5 text-amber-400" />
              <div>
                <h2 className="text-lg font-bold text-white">{copy.history}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "XAUUSD tahmin geçmişi" : "XAUUSD prediction history"}</p>
              </div>
            </div>
            <LazyPanel fallbackHeight={520}>
              <PredictionHistoryTable symbol={SYMBOL} />
            </LazyPanel>
          </motion.section>

          {/* 8. Order Block & SMC Flow - En altta */}
          <motion.section {...frame(6)} className="rounded-3xl border border-slate-800 bg-slate-950/85 p-5 shadow-2xl backdrop-blur-xl md:p-6">
            <div className="mb-5 flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-amber-400" />
              <div>
                <h2 className="text-lg font-bold text-white">{copy.orderBlocks}</h2>
                <p className="text-sm text-slate-400">{locale === "tr" ? "Order block ve SMC akışı" : "Order block and SMC flow"}</p>
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

export default function XauusdPage() {
  return (
    <AuthGuard>
      <XauusdPageContent />
    </AuthGuard>
  );
}
