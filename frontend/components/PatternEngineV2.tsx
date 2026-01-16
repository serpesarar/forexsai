"use client";

import { useState, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  AlertTriangle,
  ChevronRight,
  X,
  Info,
  BarChart3,
  Zap,
  Calendar,
  Layers,
  CheckCircle2,
  Circle,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

// Pattern type definition
interface Pattern {
  id: string;
  patternKey: string; // Key for i18n lookup (e.g., "doubleBottom")
  symbol: "NASDAQ" | "XAUUSD";
  timeframe: string;
  completion: number; // 0-100
  signal: "bullish" | "bearish" | "neutral";
  stage: "detected" | "forming" | "confirming" | "confirmed" | "active" | "completed" | "failed";
  successRate: number; // 0-100
  detectedAt: string; // ISO date
  detectedCandle: number; // Candle index where detected
  entry: number;
  target: number;
  stopLoss: number;
  currentPrice: number;
  expectedMove: number; // Percentage
}

// Mock data generator - in real app, this comes from API
const generateMockPatterns = (): Pattern[] => {
  const now = new Date();
  return [
    {
      id: "p1",
      patternKey: "doubleBottom",
      symbol: "NASDAQ",
      timeframe: "1h",
      completion: 78,
      signal: "bullish",
      stage: "confirming",
      successRate: 72,
      detectedAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      detectedCandle: 45,
      entry: 21450,
      target: 21680,
      stopLoss: 21320,
      currentPrice: 21547,
      expectedMove: 1.07,
    },
    {
      id: "p2",
      patternKey: "ascendingTriangle",
      symbol: "NASDAQ",
      timeframe: "4h",
      completion: 65,
      signal: "bullish",
      stage: "forming",
      successRate: 68,
      detectedAt: new Date(now.getTime() - 8 * 60 * 60 * 1000).toISOString(),
      detectedCandle: 12,
      entry: 21500,
      target: 21850,
      stopLoss: 21350,
      currentPrice: 21547,
      expectedMove: 1.63,
    },
    {
      id: "p3",
      patternKey: "rsiDivergence",
      symbol: "NASDAQ",
      timeframe: "15m",
      completion: 92,
      signal: "bearish",
      stage: "confirmed",
      successRate: 65,
      detectedAt: new Date(now.getTime() - 45 * 60 * 1000).toISOString(),
      detectedCandle: 8,
      entry: 21560,
      target: 21380,
      stopLoss: 21640,
      currentPrice: 21547,
      expectedMove: -0.84,
    },
    {
      id: "p4",
      patternKey: "bullFlag",
      symbol: "XAUUSD",
      timeframe: "1h",
      completion: 54,
      signal: "bullish",
      stage: "forming",
      successRate: 71,
      detectedAt: new Date(now.getTime() - 3 * 60 * 60 * 1000).toISOString(),
      detectedCandle: 28,
      entry: 2045,
      target: 2068,
      stopLoss: 2032,
      currentPrice: 2048.5,
      expectedMove: 1.12,
    },
    {
      id: "p5",
      patternKey: "headAndShoulders",
      symbol: "XAUUSD",
      timeframe: "4h",
      completion: 82,
      signal: "bearish",
      stage: "confirming",
      successRate: 74,
      detectedAt: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(),
      detectedCandle: 6,
      entry: 2052,
      target: 2018,
      stopLoss: 2072,
      currentPrice: 2048.5,
      expectedMove: -1.66,
    },
    {
      id: "p6",
      patternKey: "breakout",
      symbol: "XAUUSD",
      timeframe: "15m",
      completion: 45,
      signal: "bullish",
      stage: "detected",
      successRate: 62,
      detectedAt: new Date(now.getTime() - 20 * 60 * 1000).toISOString(),
      detectedCandle: 3,
      entry: 2047,
      target: 2062,
      stopLoss: 2039,
      currentPrice: 2048.5,
      expectedMove: 0.73,
    },
  ];
};

// Pattern Card Component
function PatternCard({
  pattern,
  onClick,
  t,
}: {
  pattern: Pattern;
  onClick: () => void;
  t: (key: string) => string;
}) {
  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "bullish":
        return "text-emerald-400";
      case "bearish":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  const getSignalBg = (signal: string) => {
    switch (signal) {
      case "bullish":
        return "bg-emerald-500/10 border-emerald-500/20";
      case "bearish":
        return "bg-red-500/10 border-red-500/20";
      default:
        return "bg-gray-500/10 border-gray-500/20";
    }
  };

  const getStageColor = (stage: string) => {
    switch (stage) {
      case "confirmed":
      case "active":
        return "text-emerald-400 bg-emerald-500/20";
      case "confirming":
        return "text-amber-400 bg-amber-500/20";
      case "forming":
      case "detected":
        return "text-blue-400 bg-blue-500/20";
      case "completed":
        return "text-purple-400 bg-purple-500/20";
      case "failed":
        return "text-red-400 bg-red-500/20";
      default:
        return "text-gray-400 bg-gray-500/20";
    }
  };

  const getCompletionColor = (completion: number) => {
    if (completion >= 80) return "stroke-emerald-500";
    if (completion >= 50) return "stroke-amber-500";
    return "stroke-blue-500";
  };

  const patternName = t(`patternEngine.patterns.${pattern.patternKey}.name`) || pattern.patternKey;
  const stageName = t(`patternEngine.stages.${pattern.stage}`) || pattern.stage;

  const timeSinceDetection = useMemo(() => {
    const diff = Date.now() - new Date(pattern.detectedAt).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }, [pattern.detectedAt]);

  return (
    <div
      onClick={onClick}
      className={`group relative cursor-pointer rounded-xl border p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg ${getSignalBg(pattern.signal)}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {/* Circular Progress */}
          <div className="relative h-14 w-14">
            <svg className="h-14 w-14 -rotate-90 transform">
              <circle
                cx="28"
                cy="28"
                r="24"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-white/10"
              />
              <circle
                cx="28"
                cy="28"
                r="24"
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${(pattern.completion / 100) * 150.8} 150.8`}
                className={`${getCompletionColor(pattern.completion)} transition-all duration-500`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-bold">{pattern.completion}%</span>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-white">{patternName}</h4>
            <div className="mt-1 flex items-center gap-2">
              <span className={`flex items-center gap-1 text-xs ${getSignalColor(pattern.signal)}`}>
                {pattern.signal === "bullish" ? (
                  <ArrowUpRight className="h-3 w-3" />
                ) : pattern.signal === "bearish" ? (
                  <ArrowDownRight className="h-3 w-3" />
                ) : (
                  <Minus className="h-3 w-3" />
                )}
                {t(`common.${pattern.signal}`)}
              </span>
              <span className="text-xs text-gray-500">•</span>
              <span className="text-xs text-gray-400">{pattern.timeframe}</span>
            </div>
          </div>
        </div>

        {/* Stage Badge */}
        <span className={`rounded-full px-2 py-1 text-[10px] font-medium uppercase ${getStageColor(pattern.stage)}`}>
          {stageName}
        </span>
      </div>

      {/* Stats Row */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-white/5 p-2 text-center">
          <p className="text-[10px] uppercase text-gray-500">{t("patternEngine.successRate")}</p>
          <p className="mt-1 font-mono text-sm font-semibold text-white">{pattern.successRate}%</p>
        </div>
        <div className="rounded-lg bg-white/5 p-2 text-center">
          <p className="text-[10px] uppercase text-gray-500">{t("patternEngine.expectedMove")}</p>
          <p className={`mt-1 font-mono text-sm font-semibold ${pattern.expectedMove >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {pattern.expectedMove >= 0 ? "+" : ""}{pattern.expectedMove}%
          </p>
        </div>
        <div className="rounded-lg bg-white/5 p-2 text-center">
          <p className="text-[10px] uppercase text-gray-500">{t("patternEngine.detected")}</p>
          <p className="mt-1 font-mono text-sm font-semibold text-white">{timeSinceDetection}</p>
        </div>
      </div>

      {/* Hover Arrow */}
      <div className="absolute right-3 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100">
        <ChevronRight className="h-5 w-5 text-white/50" />
      </div>
    </div>
  );
}

// Pattern Detail Modal
function PatternDetailModal({
  pattern,
  onClose,
  t,
}: {
  pattern: Pattern;
  onClose: () => void;
  t: (key: string) => string;
}) {
  const patternName = t(`patternEngine.patterns.${pattern.patternKey}.name`) || pattern.patternKey;
  const patternDesc = t(`patternEngine.patterns.${pattern.patternKey}.description`) || "";
  const afterCompletion = t(`patternEngine.patterns.${pattern.patternKey}.afterCompletion`) || "";
  const tradingTip = t(`patternEngine.patterns.${pattern.patternKey}.tradingTip`) || "";
  const stageName = t(`patternEngine.stages.${pattern.stage}`) || pattern.stage;

  const riskReward = Math.abs((pattern.target - pattern.entry) / (pattern.entry - pattern.stopLoss)).toFixed(2);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-slate-900/95 p-6 backdrop-blur">
          <div className="flex items-center gap-4">
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${pattern.signal === "bullish" ? "bg-emerald-500/20" : pattern.signal === "bearish" ? "bg-red-500/20" : "bg-gray-500/20"}`}>
              {pattern.signal === "bullish" ? (
                <TrendingUp className="h-6 w-6 text-emerald-400" />
              ) : pattern.signal === "bearish" ? (
                <TrendingDown className="h-6 w-6 text-red-400" />
              ) : (
                <Minus className="h-6 w-6 text-gray-400" />
              )}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{patternName}</h2>
              <p className="text-sm text-gray-400">{pattern.symbol} • {pattern.timeframe}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-gray-400 transition-colors hover:bg-white/10 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-6 p-6">
          {/* Completion Progress */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-400">{t("patternEngine.completion")}</span>
              <span className="text-2xl font-bold text-white">{pattern.completion}%</span>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-white/10">
              <div
                className={`h-full rounded-full transition-all duration-500 ${pattern.completion >= 80 ? "bg-emerald-500" : pattern.completion >= 50 ? "bg-amber-500" : "bg-blue-500"}`}
                style={{ width: `${pattern.completion}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between text-xs text-gray-500">
              <span>{t("patternEngine.stages.detected")}</span>
              <span>{t("patternEngine.stages.forming")}</span>
              <span>{t("patternEngine.stages.confirmed")}</span>
              <span>{t("patternEngine.stages.completed")}</span>
            </div>
          </div>

          {/* Pattern Information */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
              <Info className="h-4 w-4 text-blue-400" />
              {t("patternEngine.patternInfo")}
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-gray-300">{patternDesc}</p>
          </div>

          {/* After Completion */}
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
              <Target className="h-4 w-4" />
              {t("patternEngine.afterCompletion")}
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-gray-300">{afterCompletion}</p>
          </div>

          {/* Trading Strategy */}
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-emerald-400">
              <Zap className="h-4 w-4" />
              {t("patternEngine.tradingStrategy")}
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-gray-300">{tradingTip}</p>
          </div>

          {/* Key Levels */}
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
              <p className="text-xs uppercase text-gray-500">{t("patternEngine.entryZone")}</p>
              <p className="mt-2 font-mono text-lg font-bold text-emerald-400">{pattern.entry.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4 text-center">
              <p className="text-xs uppercase text-gray-500">{t("patternEngine.targetZone")}</p>
              <p className="mt-2 font-mono text-lg font-bold text-blue-400">{pattern.target.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-center">
              <p className="text-xs uppercase text-gray-500">{t("patternEngine.stopLoss")}</p>
              <p className="mt-2 font-mono text-lg font-bold text-red-400">{pattern.stopLoss.toLocaleString()}</p>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-gray-500">
                <BarChart3 className="h-4 w-4" />
                {t("patternEngine.successRate")}
              </div>
              <p className="mt-2 text-2xl font-bold text-white">{pattern.successRate}%</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-gray-500">
                <Target className="h-4 w-4" />
                {t("patternEngine.riskReward")}
              </div>
              <p className="mt-2 text-2xl font-bold text-white">1:{riskReward}</p>
            </div>
          </div>

          {/* Detection Info */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
              <Calendar className="h-4 w-4 text-purple-400" />
              {t("patternEngine.detectionDate")}
            </h3>
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs uppercase text-gray-500">{t("patternEngine.detected")}</p>
                <p className="mt-1 font-mono text-white">{formatDate(pattern.detectedAt)}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-gray-500">{t("patternEngine.candleInfo")}</p>
                <p className="mt-1 font-mono text-white">#{pattern.detectedCandle} ({pattern.timeframe})</p>
              </div>
              <div>
                <p className="text-xs uppercase text-gray-500">{t("patternEngine.timeframe")}</p>
                <p className="mt-1 font-mono text-white">{pattern.timeframe}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-gray-500">{t("patternEngine.currentStage")}</p>
                <p className="mt-1 font-mono text-white">{stageName}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main Pattern Engine V2 Component
export default function PatternEngineV2() {
  const { t } = useI18nStore();
  const [selectedSymbol, setSelectedSymbol] = useState<"ALL" | "NASDAQ" | "XAUUSD">("ALL");
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);

  const patterns = useMemo(() => generateMockPatterns(), []);

  const filteredPatterns = useMemo(() => {
    if (selectedSymbol === "ALL") return patterns;
    return patterns.filter((p) => p.symbol === selectedSymbol);
  }, [patterns, selectedSymbol]);

  const nasdaqPatterns = filteredPatterns.filter((p) => p.symbol === "NASDAQ");
  const xauusdPatterns = filteredPatterns.filter((p) => p.symbol === "XAUUSD");

  return (
    <div className="glass-card p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("patternEngine.title")}</p>
          <h3 className="mt-2 text-lg font-semibold">{t("patternEngine.subtitle")}</h3>
        </div>
        
        {/* Filter Tabs */}
        <div className="flex rounded-lg border border-white/10 bg-white/5 p-1">
          {(["ALL", "NASDAQ", "XAUUSD"] as const).map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                selectedSymbol === sym
                  ? "bg-accent text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {sym}
            </button>
          ))}
        </div>
      </div>

      {/* Patterns Grid */}
      <div className="mt-6 space-y-6">
        {/* NASDAQ Section */}
        {(selectedSymbol === "ALL" || selectedSymbol === "NASDAQ") && nasdaqPatterns.length > 0 && (
          <div>
            <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-400">
              <Layers className="h-4 w-4" />
              {t("patternEngine.nasdaqPatterns")}
              <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs">{nasdaqPatterns.length}</span>
            </h4>
            <div className="grid gap-4 md:grid-cols-2">
              {nasdaqPatterns.map((pattern) => (
                <PatternCard
                  key={pattern.id}
                  pattern={pattern}
                  onClick={() => setSelectedPattern(pattern)}
                  t={t}
                />
              ))}
            </div>
          </div>
        )}

        {/* XAUUSD Section */}
        {(selectedSymbol === "ALL" || selectedSymbol === "XAUUSD") && xauusdPatterns.length > 0 && (
          <div>
            <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-400">
              <Layers className="h-4 w-4" />
              {t("patternEngine.xauusdPatterns")}
              <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs">{xauusdPatterns.length}</span>
            </h4>
            <div className="grid gap-4 md:grid-cols-2">
              {xauusdPatterns.map((pattern) => (
                <PatternCard
                  key={pattern.id}
                  pattern={pattern}
                  onClick={() => setSelectedPattern(pattern)}
                  t={t}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {filteredPatterns.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Circle className="h-12 w-12 text-gray-600" />
            <p className="mt-4 text-gray-400">{t("patternEngine.noPatterns")}</p>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedPattern && (
        <PatternDetailModal
          pattern={selectedPattern}
          onClose={() => setSelectedPattern(null)}
          t={t}
        />
      )}
    </div>
  );
}
