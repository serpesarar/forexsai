"use client";

import { useState, useEffect } from "react";
import { ChevronDown, Moon } from "lucide-react";
import {
  EmelIcon, PulseIcon, SignalsIcon, LearningIcon,
  ChartsIcon, TradingIcon, NasdaqIcon, GoldIcon,
  ArrowUpIcon, ArrowDownIcon, AdvancedAnalysisIcon
} from "../ui/CustomIcons";
import Image from "next/image";
import MLPredictionPanel from "../../components/MLPredictionPanel";
import ClaudeAnalysisPanel from "../../components/ClaudeAnalysisPanel";
import DetailedAnalysisPanel from "../../components/DetailedAnalysisPanel";
import LearningDashboardPanel from "../../components/LearningDashboardPanel";
import PredictionHistoryTable from "../../components/PredictionHistoryTable";
import OrderBlockPanelSimple from "../../components/OrderBlockPanelSimple";
import RhythmDetectorSimple from "../../components/RhythmDetectorSimple";
import TradingChartWrapper from "../../components/TradingChartWrapper";
import LiveChartPanel from "../../components/LiveChartPanel";
import { useI18nStore } from "../../lib/i18n/store";

// Golden Ratio constant
const PHI = 1.618;

// Symbol configurations
const SYMBOLS = {
  "NDX.INDX": {
    label: "NASDAQ-100",
    shortLabel: "NASDAQ",
    icon: NasdaqIcon,
    color: "from-emerald-500/20 to-teal-500/20",
    accent: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  "XAUUSD": {
    label: "Gold (XAU/USD)",
    shortLabel: "XAUUSD",
    icon: GoldIcon,
    color: "from-amber-500/20 to-yellow-500/20",
    accent: "text-amber-400",
    border: "border-amber-500/30",
  },
} as const;

type SymbolKey = keyof typeof SYMBOLS;

export default function TradingView() {
  const { t, locale } = useI18nStore();
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolKey>("NDX.INDX");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>("");

  // Set date only on client to avoid hydration mismatch
  useEffect(() => {
    setCurrentDate(new Date().toLocaleDateString(locale === "en" ? "en-US" : "tr-TR"));
  }, [locale]);

  const currentSymbol = SYMBOLS[selectedSymbol];
  const SymbolIcon = currentSymbol.icon;

  const symbolSelector = (
    <div className="relative z-50">
      <button
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className={`group flex items-center gap-2 md:gap-3 rounded-xl bg-gradient-to-r ${currentSymbol.color} px-3 py-2 md:px-4 md:py-2.5 border ${currentSymbol.border} transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]`}
      >
        <div className={`flex h-7 w-7 md:h-9 md:w-9 items-center justify-center rounded-lg bg-white/10`}>
          <SymbolIcon className={`h-3.5 w-3.5 md:h-5 md:w-5 ${currentSymbol.accent}`} />
        </div>
        <div className="text-left">
          <p className="text-[9px] md:text-[10px] text-textSecondary font-medium">{t("tradingPage.activeSymbol")}</p>
          <p className="text-xs md:text-sm font-bold">{currentSymbol.shortLabel}</p>
        </div>
        <ChevronDown className={`h-3.5 w-3.5 md:h-4 md:w-4 transition-transform duration-300 ${dropdownOpen ? "rotate-180" : ""}`} />
      </button>
      {dropdownOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/20" onClick={() => setDropdownOpen(false)} />
          <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-64 overflow-hidden rounded-xl border border-white/10 bg-background shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
            {(Object.entries(SYMBOLS) as [SymbolKey, typeof SYMBOLS[SymbolKey]][]).map(([key, sym]) => {
              const Icon = sym.icon;
              const isSelected = key === selectedSymbol;
              return (
                <button
                  key={key}
                  onClick={() => { setSelectedSymbol(key); setDropdownOpen(false); }}
                  className={`flex w-full items-center gap-3 px-4 py-3 transition-all duration-200 ${isSelected ? `bg-gradient-to-r ${sym.color} border-l-4 ${sym.border}` : "hover:bg-white/5 border-l-4 border-transparent"
                    }`}
                >
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${isSelected ? "bg-white/20" : "bg-white/10"}`}>
                    <Icon className={`h-4 w-4 ${sym.accent}`} />
                  </div>
                  <div className="text-left flex-1">
                    <p className="font-bold text-sm">{sym.shortLabel}</p>
                    <p className="text-xs text-textSecondary">{sym.label}</p>
                  </div>
                  {isSelected && <div className="h-3 w-3 rounded-full bg-accent animate-pulse" />}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );

  return (
    <div className="w-full text-white animate-in fade-in duration-300">
      <div className="flex justify-between items-center px-4 md:px-6 pt-4 mb-2">
        <div className="flex items-center gap-3">
          <TradingIcon size={24} className="text-accent" />
          <h1 className="text-xl font-bold">AI Trading</h1>
        </div>
        {symbolSelector}
      </div>
      {/* Main Content - Golden Ratio Layout */}
      <main className="relative z-10 mx-auto max-w-[1600px] p-3 md:p-6 pb-20">
        {/* 
          Golden Ratio Grid Layout:
          - Main prediction area: 61.8% width (φ / (1 + φ))
          - Side panels: 38.2% width (1 / (1 + φ))
          - Vertical sections follow same ratio
          - Mobile: Single column
        */}

        <div
          className="grid gap-4 md:gap-6 items-start grid-cols-1 lg:grid-cols-[1.618fr_1fr]"
        >
          {/* LEFT COLUMN - Primary Analysis (61.8%) */}
          <div className="space-y-6 self-start">
            {/* Row 1: ML Prediction - Large Primary Panel */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <EmelIcon size={20} className="text-accent" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  {t("tradingPage.mlModelPrediction")}
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <MLPredictionPanelLarge symbol={selectedSymbol} symbolLabel={currentSymbol.shortLabel} />
              </div>
            </section>

            {/* Row 2: Claude AI Analysis - Large */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <PulseIcon size={20} className="text-purple-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  {t("tradingPage.claudeAIAnalysis")}
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <ClaudeAnalysisPanelLarge symbol={selectedSymbol} symbolLabel={currentSymbol.shortLabel} />
              </div>
            </section>

          </div>

          {/* RIGHT COLUMN - Secondary Analysis (38.2%) */}
          <div className="space-y-4 md:space-y-6 self-start min-w-0 overflow-hidden">
            {/* Detailed Analysis */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <AdvancedAnalysisIcon size={20} className="text-sky-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  {t("tradingPage.detailedAnalysis")}
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <DetailedAnalysisPanel symbol={selectedSymbol} symbolLabel={currentSymbol.shortLabel} />
              </div>
            </section>

            {/* Smart Money Zones */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <SignalsIcon size={20} className="text-cyan-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  Smart Money Zones
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <OrderBlockPanelSimple symbol={selectedSymbol} symbolLabel={currentSymbol.shortLabel} />
              </div>
            </section>

            {/* Rhythm Detector */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <PulseIcon size={20} className="text-pink-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  {t("tradingPage.rhythmDetector")}
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <RhythmDetectorSimple symbol={selectedSymbol} symbolLabel={currentSymbol.shortLabel} />
              </div>
            </section>

            {/* Learning Dashboard */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <LearningIcon size={20} className="text-purple-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  {t("tradingPage.learningSystem")}
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <LearningDashboardPanel symbol={selectedSymbol} />
              </div>
            </section>

            {/* Prediction History */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <ChartsIcon size={20} className="text-indigo-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  {t("tradingPage.predictionHistory")}
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <PredictionHistoryTable symbol={selectedSymbol} />
              </div>
            </section>
          </div>
        </div>

        {/* Full-Width Charts Section */}
        <section className="mt-6 md:mt-8">
          <div className="mb-3 md:mb-4 flex items-center gap-2">
            <ChartsIcon size={24} className="text-blue-400" />
            <h2 className="text-base md:text-lg font-bold uppercase tracking-wider">
              {t("tradingPage.livePriceCharts")}
            </h2>
            <span className="ml-2 flex items-center gap-1 text-xs text-success">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              {t("tradingPage.live")}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {/* NASDAQ Chart */}
            <LiveChartPanel
              symbol="NDX.INDX"
              symbolLabel="NASDAQ-100"
              height={300}
            />

            {/* XAUUSD Chart */}
            <LiveChartPanel
              symbol="XAUUSD"
              symbolLabel="Gold (XAU/USD)"
              height={300}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

// Enhanced ML Prediction Panel - Larger version for main view
function MLPredictionPanelLarge({ symbol, symbolLabel }: { symbol: string; symbolLabel: string }) {
  return (
    <div className="relative">
      <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-accent/30 via-purple-500/20 to-accent/30 opacity-50 blur-sm" />
      <div className="relative">
        <MLPredictionPanel symbol={symbol} symbolLabel={symbolLabel} />
      </div>
    </div>
  );
}

// Enhanced Claude Analysis Panel - Larger version for main view

function ClaudeAnalysisPanelLarge({ symbol, symbolLabel }: { symbol: string; symbolLabel: string }) {
  return (
    <div className="relative">
      <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-purple-500/30 via-pink-500/20 to-purple-500/30 opacity-50 blur-sm" />
      <div className="relative">
        <ClaudeAnalysisPanel symbol={symbol} symbolLabel={symbolLabel} />
      </div>
    </div>
  );
}
