"use client";

import { useState, useEffect } from "react";
import { ChevronDown, TrendingUp, Activity, BarChart3, Brain, Sparkles, LineChart, Home } from "lucide-react";
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
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolKey>("NDX.INDX");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const currentSymbol = SYMBOLS[selectedSymbol];
  const SymbolIcon = currentSymbol.icon;

  return (
    <div className="min-h-screen bg-background">
      {/* Header with Symbol Selector - Animated */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-xl">
        {/* Animated gradient line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent to-transparent animate-pulse" />
        
        <div className="mx-auto flex max-w-[1800px] items-center justify-between px-6 py-4">
          {/* Symbol Dropdown */}
          <div className="relative z-50">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className={`group flex items-center gap-4 rounded-2xl bg-gradient-to-r ${currentSymbol.color} px-6 py-4 border ${currentSymbol.border} transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-accent/20 active:scale-[0.98]`}
            >
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 transition-transform duration-300 group-hover:rotate-12`}>
                <SymbolIcon className={`h-6 w-6 ${currentSymbol.accent}`} />
              </div>
              <div className="text-left min-w-[120px]">
                <p className="text-xs text-textSecondary font-medium">Aktif Sembol</p>
                <p className="text-lg font-bold">{currentSymbol.label}</p>
              </div>
              <ChevronDown className={`ml-2 h-5 w-5 transition-transform duration-300 ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown Menu - Fixed positioning */}
            {dropdownOpen && (
              <>
                <div className="fixed inset-0 z-40 bg-black/20" onClick={() => setDropdownOpen(false)} />
                <div className="absolute left-0 top-[calc(100%+8px)] z-50 w-80 overflow-hidden rounded-2xl border border-white/10 bg-background shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
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
                        className={`flex w-full items-center gap-4 px-6 py-5 transition-all duration-200 ${
                          isSelected 
                            ? `bg-gradient-to-r ${sym.color} border-l-4 ${sym.border}` 
                            : "hover:bg-white/5 border-l-4 border-transparent"
                        }`}
                      >
                        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${isSelected ? "bg-white/20" : "bg-white/10"}`}>
                          <Icon className={`h-6 w-6 ${sym.accent}`} />
                        </div>
                        <div className="text-left flex-1">
                          <p className="font-bold text-base">{sym.label}</p>
                          <p className="text-sm text-textSecondary">{sym.shortLabel}</p>
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

          {/* Title - Animated */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center animate-pulse">
                <Brain className="h-4 w-4 text-white" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text">
                AI Trading Dashboard
              </h1>
            </div>
            <p className="text-sm text-textSecondary mt-1">ML Model + Claude AI Analysis</p>
          </div>

          {/* Right Side - Home Link + Time */}
          <div className="flex items-center gap-6">
            <Link 
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-200"
            >
              <Home className="h-4 w-4" />
              <span className="text-sm">Ana Sayfa</span>
            </Link>
            <div className="text-right">
              <p className="text-sm font-mono font-bold">{new Date().toLocaleDateString("tr-TR")}</p>
              <p className="text-xs text-textSecondary flex items-center gap-1 justify-end">
                <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
                Canlı Analiz
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Golden Ratio Layout */}
      <main className="mx-auto max-w-[1800px] p-6">
        {/* 
          Golden Ratio Grid Layout:
          - Main prediction area: 61.8% width (φ / (1 + φ))
          - Side panels: 38.2% width (1 / (1 + φ))
          - Vertical sections follow same ratio
        */}
        
        <div
          className="grid gap-6 items-start"
          style={{ gridTemplateColumns: `${PHI}fr 1fr`, alignItems: "start" }}
        >
          {/* LEFT COLUMN - Primary Analysis (61.8%) */}
          <div className="space-y-6 self-start">
            {/* Row 1: ML Prediction - Large Primary Panel */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Brain className="h-5 w-5 text-accent" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  ML Model Tahmini
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
                  Claude AI Analizi
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <ClaudeAnalysisPanelLarge symbol={selectedSymbol} symbolLabel={currentSymbol.shortLabel} />
              </div>
            </section>

          </div>

          {/* RIGHT COLUMN - Secondary Analysis (38.2%) */}
          <div className="space-y-6 self-start min-w-0 overflow-hidden">
            {/* Detailed Analysis */}
            <section>
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-sky-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-textSecondary">
                  Detaylı Analiz
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
                  Ritim Dedektörü
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
                  Öğrenme Sistemi
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
                  Tahmin Geçmişi
                </h2>
              </div>
              <div className="transform-gpu transition-all duration-300">
                <PredictionHistoryTable symbol={selectedSymbol} />
              </div>
            </section>
          </div>
        </div>

        {/* Full-Width Charts Section */}
        <section className="mt-8">
          <div className="mb-4 flex items-center gap-2">
            <LineChart className="h-6 w-6 text-blue-400" />
            <h2 className="text-lg font-bold uppercase tracking-wider">
              Canlı Fiyat Grafikleri
            </h2>
            <span className="ml-2 flex items-center gap-1 text-xs text-success">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
              </span>
              Canlı
            </span>
          </div>
          
          <div className="grid grid-cols-1 gap-6">
            {/* NASDAQ Chart */}
            <LiveChartPanel 
              symbol="NDX.INDX" 
              symbolLabel="NASDAQ-100" 
              height={450} 
            />
            
            {/* XAUUSD Chart */}
            <LiveChartPanel 
              symbol="XAUUSD" 
              symbolLabel="Gold (XAU/USD)" 
              height={450} 
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
