"use client";

import { useState, useEffect } from "react";
import { ChevronDown, TrendingUp, Activity, BarChart3, Brain, Sparkles, LineChart, Home, Zap } from "lucide-react";
import Image from "next/image";
import { TradingBackground } from "../../components/TradingBackground";
import Link from "next/link";
import MLPredictionPanel from "../../components/MLPredictionPanel";
import ClaudeAnalysisPanel from "../../components/ClaudeAnalysisPanel";
import DetailedAnalysisPanel from "../../components/DetailedAnalysisPanel";
import LearningDashboardPanel from "../../components/LearningDashboardPanel";
import PredictionHistoryTable from "../../components/PredictionHistoryTable";
import OrderBlockPanelSimple from "../../components/OrderBlockPanelSimple";
import RhythmDetectorSimple from "../../components/RhythmDetectorSimple";
import TradingChartWrapper from "../../components/TradingChartWrapper";
import LiveChartPanel from "../../components/LiveChartPanel";
import { LanguageSwitcher } from "../../components/LanguageSwitcher";
import { useI18nStore } from "../../lib/i18n/store";

// Golden Ratio constant
const PHI = 1.618;

// Symbol configurations
const SYMBOLS = {
  "NDX.INDX": {
    label: "NASDAQ-100",
    shortLabel: "NASDAQ",
    icon: TrendingUp,
    color: "from-emerald-500/20 to-teal-500/20",
    accent: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  "XAUUSD": {
    label: "Gold (XAU/USD)",
    shortLabel: "XAUUSD",
    icon: Activity,
    color: "from-amber-500/20 to-yellow-500/20",
    accent: "text-amber-400",
    border: "border-amber-500/30",
  },
} as const;

type SymbolKey = keyof typeof SYMBOLS;

export default function TradingDashboard() {
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

  return (
    <div className="min-h-screen bg-background relative">
      {/* Animated Background */}
      <TradingBackground />
      {/* Header with Symbol Selector - Premium Design */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-xl">
        {/* Animated gradient line */}
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#00E0C6]/50 to-transparent" />
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#00E0C6] to-transparent animate-pulse opacity-50" />
        
        <div className="mx-auto flex max-w-[1800px] items-center justify-between px-3 py-2 md:px-6 md:py-3">
          {/* Symbol Dropdown */}
          <div className="relative z-50">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className={`group flex items-center gap-2 md:gap-4 rounded-xl md:rounded-2xl bg-gradient-to-r ${currentSymbol.color} px-3 py-2 md:px-6 md:py-4 border ${currentSymbol.border} transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-accent/20 active:scale-[0.98]`}
            >
              <div className={`flex h-8 w-8 md:h-12 md:w-12 items-center justify-center rounded-lg md:rounded-xl bg-white/10 transition-transform duration-300 group-hover:rotate-12`}>
                <SymbolIcon className={`h-4 w-4 md:h-6 md:w-6 ${currentSymbol.accent}`} />
              </div>
              <div className="text-left">
                <p className="text-[10px] md:text-xs text-textSecondary font-medium">{t("tradingPage.activeSymbol")}</p>
                <p className="text-sm md:text-lg font-bold">{currentSymbol.shortLabel}</p>
              </div>
              <ChevronDown className={`h-4 w-4 md:h-5 md:w-5 transition-transform duration-300 ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown Menu - Fixed positioning */}
            {dropdownOpen && (
              <>
                <div className="fixed inset-0 z-40 bg-black/20" onClick={() => setDropdownOpen(false)} />
                <div className="absolute left-0 top-[calc(100%+8px)] z-50 w-64 md:w-80 overflow-hidden rounded-xl md:rounded-2xl border border-white/10 bg-background shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
                  {(Object.entries(SYMBOLS) as [SymbolKey, typeof SYMBOLS[SymbolKey]][]).map(([key, sym]) => {
                    const Icon = sym.icon;
                    const isSelected = key === selectedSymbol;
                    return (
                      <button
                        key={key}
                        onClick={() => {
                          setSelectedSymbol(key);
                          setDropdownOpen(false);
                        }}
                        className={`flex w-full items-center gap-3 md:gap-4 px-4 py-3 md:px-6 md:py-5 transition-all duration-200 ${
                          isSelected 
                            ? `bg-gradient-to-r ${sym.color} border-l-4 ${sym.border}` 
                            : "hover:bg-white/5 border-l-4 border-transparent"
                        }`}
                      >
                        <div className={`flex h-9 w-9 md:h-12 md:w-12 items-center justify-center rounded-lg md:rounded-xl ${isSelected ? "bg-white/20" : "bg-white/10"}`}>
                          <Icon className={`h-4 w-4 md:h-6 md:w-6 ${sym.accent}`} />
                        </div>
                        <div className="text-left flex-1">
                          <p className="font-bold text-sm md:text-base">{sym.shortLabel}</p>
                          <p className="text-xs md:text-sm text-textSecondary hidden md:block">{sym.label}</p>
                        </div>
                        {isSelected && (
                          <div className="h-3 w-3 rounded-full bg-accent animate-pulse" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* Logo + Title - Premium Design */}
          <div className="hidden lg:flex items-center gap-4">
            {/* Logo */}
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-[#00E0C6]/20 to-[#3B82F6]/20 rounded-xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative h-10 w-10 rounded-xl overflow-hidden border border-white/10 bg-white/5">
                <Image
                  src="/bu.png"
                  alt="ForexsAI"
                  width={40}
                  height={40}
                  className="object-cover"
                />
              </div>
            </div>
            
            {/* Title */}
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg xl:text-xl font-bold tracking-tight">
                  <span className="text-white">AI Trading</span>
                  <span className="ml-1.5 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] bg-clip-text text-transparent">Dashboard</span>
                </h1>
                <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#00E0C6]/10 border border-[#00E0C6]/20">
                  <Zap className="h-3 w-3 text-[#00E0C6]" />
                  <span className="text-[10px] font-bold text-[#00E0C6] uppercase tracking-wider">Live</span>
                </div>
              </div>
              <p className="text-[11px] text-white/40 font-medium tracking-wide">Quantitative Analysis • ML Model + Claude AI</p>
            </div>
          </div>

          {/* Right Side - Navigation + Time */}
          <div className="flex items-center gap-2 md:gap-3">
            <Link 
              href="/charts"
              className="group flex items-center gap-1.5 md:gap-2 px-3 py-2 md:px-4 md:py-2.5 rounded-xl bg-gradient-to-r from-[#00E0C6]/10 to-[#3B82F6]/10 border border-[#00E0C6]/20 hover:border-[#00E0C6]/40 hover:from-[#00E0C6]/20 hover:to-[#3B82F6]/20 transition-all duration-300"
            >
              <BarChart3 className="h-4 w-4 text-[#00E0C6] group-hover:scale-110 transition-transform" />
              <span className="text-xs md:text-sm font-semibold text-white/90 hidden sm:inline">{t("tradingPage.charts")}</span>
            </Link>
            <Link 
              href="/"
              className="group flex items-center gap-1.5 md:gap-2 px-3 py-2 md:px-4 md:py-2.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300"
            >
              <Home className="h-4 w-4 text-white/70 group-hover:text-white group-hover:scale-110 transition-all" />
              <span className="text-xs md:text-sm font-medium text-white/70 group-hover:text-white hidden sm:inline">{t("tradingPage.homePage")}</span>
            </Link>
            <div className="text-right hidden md:block pl-3 border-l border-white/10">
              <p className="text-sm font-mono font-bold text-white/90">{currentDate || "—"}</p>
              <p className="text-[10px] text-white/40 flex items-center gap-1.5 justify-end font-medium">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00E0C6] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00E0C6]"></span>
                </span>
                {t("tradingPage.liveAnalysis")}
              </p>
            </div>
            {/* Mobile live indicator */}
            <div className="flex md:hidden items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-[#00E0C6]/10 border border-[#00E0C6]/20">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00E0C6] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#00E0C6]"></span>
              </span>
              <span className="text-[10px] font-bold text-[#00E0C6]">LIVE</span>
            </div>
            {/* Language Switcher */}
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      {/* Main Content - Golden Ratio Layout */}
      <main className="relative z-10 mx-auto max-w-[1800px] p-3 md:p-6">
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
                <Brain className="h-5 w-5 text-accent" />
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
                <Sparkles className="h-5 w-5 text-purple-400" />
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
                <Sparkles className="h-5 w-5 text-sky-400" />
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
                <BarChart3 className="h-5 w-5 text-cyan-400" />
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
                <Activity className="h-5 w-5 text-pink-400" />
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
                <Brain className="h-5 w-5 text-purple-400" />
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
                <LineChart className="h-5 w-5 text-indigo-400" />
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
            <LineChart className="h-5 w-5 md:h-6 md:w-6 text-blue-400" />
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
