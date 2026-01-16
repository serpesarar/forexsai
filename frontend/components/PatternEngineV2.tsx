"use client";

import { useState, useMemo, useEffect } from "react";
import { createPortal } from "react-dom";
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
  Maximize2,
  Minimize2,
  Activity,
  Shield,
  DollarSign,
  Timer,
  Eye,
  TrendingUp as TrendUp,
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

// Compact Pattern Card Component - Fixed overflow issues
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
      case "bullish": return "text-emerald-400";
      case "bearish": return "text-red-400";
      default: return "text-gray-400";
    }
  };

  const getSignalBg = (signal: string) => {
    switch (signal) {
      case "bullish": return "bg-emerald-500/10 border-emerald-500/30";
      case "bearish": return "bg-red-500/10 border-red-500/30";
      default: return "bg-gray-500/10 border-gray-500/30";
    }
  };

  const getStageColor = (stage: string) => {
    switch (stage) {
      case "confirmed":
      case "active": return "text-emerald-400 bg-emerald-500/20";
      case "confirming": return "text-amber-400 bg-amber-500/20";
      case "forming":
      case "detected": return "text-blue-400 bg-blue-500/20";
      case "completed": return "text-purple-400 bg-purple-500/20";
      case "failed": return "text-red-400 bg-red-500/20";
      default: return "text-gray-400 bg-gray-500/20";
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
    if (hours > 0) return `${hours}h`;
    return `${minutes}m`;
  }, [pattern.detectedAt]);

  return (
    <div
      onClick={onClick}
      className={`group relative cursor-pointer rounded-xl border p-3 transition-all duration-300 hover:scale-[1.01] hover:shadow-lg hover:border-white/30 ${getSignalBg(pattern.signal)}`}
    >
      {/* Compact Header */}
      <div className="flex items-center gap-3">
        {/* Mini Circular Progress */}
        <div className="relative h-11 w-11 flex-shrink-0">
          <svg className="h-11 w-11 -rotate-90 transform">
            <circle cx="22" cy="22" r="18" stroke="currentColor" strokeWidth="3" fill="none" className="text-white/10" />
            <circle
              cx="22" cy="22" r="18" strokeWidth="3" fill="none" strokeLinecap="round"
              strokeDasharray={`${(pattern.completion / 100) * 113} 113`}
              className={`${getCompletionColor(pattern.completion)} transition-all duration-500`}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[11px] font-bold">{pattern.completion}%</span>
          </div>
        </div>

        {/* Pattern Info - Truncated */}
        <div className="flex-1 min-w-0 overflow-hidden">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-white text-sm truncate">{patternName}</h4>
            <span className={`flex-shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase ${getStageColor(pattern.stage)}`}>
              {stageName}
            </span>
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 text-[11px]">
            <span className={`flex items-center gap-0.5 ${getSignalColor(pattern.signal)}`}>
              {pattern.signal === "bullish" ? <ArrowUpRight className="h-3 w-3" /> : pattern.signal === "bearish" ? <ArrowDownRight className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
              {t(`common.${pattern.signal}`)}
            </span>
            <span className="text-gray-600">•</span>
            <span className="text-gray-400">{pattern.timeframe}</span>
          </div>
        </div>
      </div>

      {/* Compact Stats Row */}
      <div className="mt-2.5 flex items-center justify-between gap-2 text-[10px]">
        <div className="flex items-center gap-1 text-gray-400">
          <span className="uppercase">Success</span>
          <span className="font-mono font-semibold text-white">{pattern.successRate}%</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="uppercase text-gray-400">Move</span>
          <span className={`font-mono font-semibold ${pattern.expectedMove >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {pattern.expectedMove >= 0 ? "+" : ""}{pattern.expectedMove}%
          </span>
        </div>
        <div className="flex items-center gap-1 text-gray-400">
          <Timer className="h-3 w-3" />
          <span className="font-mono text-white">{timeSinceDetection}</span>
        </div>
      </div>

      {/* Hover Indicator */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100">
        <Eye className="h-4 w-4 text-white/40" />
      </div>
    </div>
  );
}

// Pattern Detail Modal - Click on card
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
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/10 bg-slate-900 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-slate-900/95 p-4 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${pattern.signal === "bullish" ? "bg-emerald-500/20" : pattern.signal === "bearish" ? "bg-red-500/20" : "bg-gray-500/20"}`}>
              {pattern.signal === "bullish" ? <TrendingUp className="h-5 w-5 text-emerald-400" /> : pattern.signal === "bearish" ? <TrendingDown className="h-5 w-5 text-red-400" /> : <Minus className="h-5 w-5 text-gray-400" />}
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{patternName}</h2>
              <p className="text-xs text-gray-400">{pattern.symbol} • {pattern.timeframe}</p>
            </div>
          </div>
          <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 text-gray-400 hover:bg-white/10 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 p-4">
          {/* Progress */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">{t("patternEngine.completion")}</span>
              <span className="text-xl font-bold text-white">{pattern.completion}%</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
              <div className={`h-full rounded-full ${pattern.completion >= 80 ? "bg-emerald-500" : pattern.completion >= 50 ? "bg-amber-500" : "bg-blue-500"}`} style={{ width: `${pattern.completion}%` }} />
            </div>
          </div>
          {/* Info Cards */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
            <h3 className="flex items-center gap-2 text-xs font-semibold text-white"><Info className="h-3.5 w-3.5 text-blue-400" />{t("patternEngine.patternInfo")}</h3>
            <p className="mt-2 text-xs leading-relaxed text-gray-300">{patternDesc}</p>
          </div>
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
            <h3 className="flex items-center gap-2 text-xs font-semibold text-amber-400"><Target className="h-3.5 w-3.5" />{t("patternEngine.afterCompletion")}</h3>
            <p className="mt-2 text-xs leading-relaxed text-gray-300">{afterCompletion}</p>
          </div>
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
            <h3 className="flex items-center gap-2 text-xs font-semibold text-emerald-400"><Zap className="h-3.5 w-3.5" />{t("patternEngine.tradingStrategy")}</h3>
            <p className="mt-2 text-xs leading-relaxed text-gray-300">{tradingTip}</p>
          </div>
          {/* Levels */}
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2 text-center">
              <p className="text-[10px] uppercase text-gray-500">{t("patternEngine.entryZone")}</p>
              <p className="mt-1 font-mono text-sm font-bold text-emerald-400">{pattern.entry.toLocaleString()}</p>
            </div>
            <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-2 text-center">
              <p className="text-[10px] uppercase text-gray-500">{t("patternEngine.targetZone")}</p>
              <p className="mt-1 font-mono text-sm font-bold text-blue-400">{pattern.target.toLocaleString()}</p>
            </div>
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-2 text-center">
              <p className="text-[10px] uppercase text-gray-500">{t("patternEngine.stopLoss")}</p>
              <p className="mt-1 font-mono text-sm font-bold text-red-400">{pattern.stopLoss.toLocaleString()}</p>
            </div>
          </div>
          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-lg border border-white/10 bg-white/5 p-2">
              <div className="flex items-center gap-1.5 text-[10px] uppercase text-gray-500"><BarChart3 className="h-3 w-3" />{t("patternEngine.successRate")}</div>
              <p className="mt-1 text-lg font-bold text-white">{pattern.successRate}%</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/5 p-2">
              <div className="flex items-center gap-1.5 text-[10px] uppercase text-gray-500"><Target className="h-3 w-3" />{t("patternEngine.riskReward")}</div>
              <p className="mt-1 text-lg font-bold text-white">1:{riskReward}</p>
            </div>
          </div>
          {/* Detection */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
            <h3 className="flex items-center gap-2 text-xs font-semibold text-white"><Calendar className="h-3.5 w-3.5 text-purple-400" />{t("patternEngine.detectionDate")}</h3>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div><p className="text-[10px] uppercase text-gray-500">{t("patternEngine.detected")}</p><p className="mt-0.5 font-mono text-white">{formatDate(pattern.detectedAt)}</p></div>
              <div><p className="text-[10px] uppercase text-gray-500">{t("patternEngine.candleInfo")}</p><p className="mt-0.5 font-mono text-white">#{pattern.detectedCandle} ({pattern.timeframe})</p></div>
              <div><p className="text-[10px] uppercase text-gray-500">{t("patternEngine.timeframe")}</p><p className="mt-0.5 font-mono text-white">{pattern.timeframe}</p></div>
              <div><p className="text-[10px] uppercase text-gray-500">{t("patternEngine.currentStage")}</p><p className="mt-0.5 font-mono text-white">{stageName}</p></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// FULLSCREEN Panel Modal - Expanded view with more details (uses Portal)
function FullscreenPatternModal({
  patterns,
  onClose,
  t,
}: {
  patterns: Pattern[];
  onClose: () => void;
  t: (key: string) => string;
}) {
  const [mounted, setMounted] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [filter, setFilter] = useState<"ALL" | "NASDAQ" | "XAUUSD">("ALL");
  const [sortBy, setSortBy] = useState<"completion" | "successRate" | "detected">("completion");

  useEffect(() => {
    setMounted(true);
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  const filteredPatterns = useMemo(() => {
    let result = filter === "ALL" ? patterns : patterns.filter(p => p.symbol === filter);
    return result.sort((a, b) => {
      if (sortBy === "completion") return b.completion - a.completion;
      if (sortBy === "successRate") return b.successRate - a.successRate;
      return new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime();
    });
  }, [patterns, filter, sortBy]);

  const stats = useMemo(() => {
    const bullish = patterns.filter(p => p.signal === "bullish").length;
    const bearish = patterns.filter(p => p.signal === "bearish").length;
    const avgCompletion = Math.round(patterns.reduce((acc, p) => acc + p.completion, 0) / patterns.length);
    const avgSuccess = Math.round(patterns.reduce((acc, p) => acc + p.successRate, 0) / patterns.length);
    const confirmed = patterns.filter(p => p.stage === "confirmed" || p.stage === "active").length;
    return { bullish, bearish, avgCompletion, avgSuccess, confirmed, total: patterns.length };
  }, [patterns]);

  const getSignalColor = (signal: string) => signal === "bullish" ? "text-emerald-400" : signal === "bearish" ? "text-red-400" : "text-gray-400";
  const getSignalBg = (signal: string) => signal === "bullish" ? "bg-emerald-500/10 border-emerald-500/30" : signal === "bearish" ? "bg-red-500/10 border-red-500/30" : "bg-gray-500/10 border-gray-500/30";
  const getStageColor = (stage: string) => {
    if (stage === "confirmed" || stage === "active") return "text-emerald-400 bg-emerald-500/20";
    if (stage === "confirming") return "text-amber-400 bg-amber-500/20";
    if (stage === "forming" || stage === "detected") return "text-blue-400 bg-blue-500/20";
    return "text-gray-400 bg-gray-500/20";
  };

  if (!mounted) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[9999] bg-slate-950" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, width: '100vw', height: '100vh' }}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 bg-slate-900/80 px-6 py-4 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent/30 to-purple-500/30">
            <Activity className="h-6 w-6 text-accent" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">{t("patternEngine.title")}</h1>
            <p className="text-sm text-gray-400">{t("patternEngine.subtitle")} • {stats.total} Active</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-accent focus:outline-none"
          >
            <option value="completion">Sort: Completion</option>
            <option value="successRate">Sort: Success Rate</option>
            <option value="detected">Sort: Newest</option>
          </select>
          {/* Filter */}
          <div className="flex rounded-lg border border-white/10 bg-white/5 p-1">
            {(["ALL", "NASDAQ", "XAUUSD"] as const).map(sym => (
              <button key={sym} onClick={() => setFilter(sym)} className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${filter === sym ? "bg-accent text-white" : "text-gray-400 hover:text-white"}`}>
                {sym}
              </button>
            ))}
          </div>
          {/* Close */}
          <button onClick={onClose} className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-gray-400 hover:bg-white/10 hover:text-white">
            <Minimize2 className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Stats Sidebar */}
        <div className="w-72 flex-shrink-0 border-r border-white/10 bg-slate-900/50 p-4 space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Overview</h3>
          
          {/* Signal Distribution */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs text-gray-500 uppercase mb-3">Signal Distribution</p>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-emerald-400">Bullish</span>
                  <span className="text-sm font-bold text-emerald-400">{stats.bullish}</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(stats.bullish / stats.total) * 100}%` }} />
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-red-400">Bearish</span>
                  <span className="text-sm font-bold text-red-400">{stats.bearish}</span>
                </div>
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: `${(stats.bearish / stats.total) * 100}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
              <p className="text-[10px] uppercase text-gray-500">Avg Completion</p>
              <p className="mt-1 text-2xl font-bold text-white">{stats.avgCompletion}%</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
              <p className="text-[10px] uppercase text-gray-500">Avg Success</p>
              <p className="mt-1 text-2xl font-bold text-white">{stats.avgSuccess}%</p>
            </div>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-center">
              <p className="text-[10px] uppercase text-gray-500">Confirmed</p>
              <p className="mt-1 text-2xl font-bold text-emerald-400">{stats.confirmed}</p>
            </div>
            <div className="rounded-xl border border-accent/20 bg-accent/5 p-3 text-center">
              <p className="text-[10px] uppercase text-gray-500">Total Active</p>
              <p className="mt-1 text-2xl font-bold text-accent">{stats.total}</p>
            </div>
          </div>

          {/* Legend */}
          <div className="rounded-xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs text-gray-500 uppercase mb-3">Stage Legend</p>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-blue-500" /><span className="text-gray-400">Detected / Forming</span></div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-amber-500" /><span className="text-gray-400">Confirming</span></div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500" /><span className="text-gray-400">Confirmed / Active</span></div>
              <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-purple-500" /><span className="text-gray-400">Completed</span></div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-auto p-6">
          {selectedPattern ? (
            // Selected Pattern Detail View
            <div className="mx-auto max-w-4xl">
              <button onClick={() => setSelectedPattern(null)} className="mb-4 flex items-center gap-2 text-sm text-gray-400 hover:text-white">
                <ChevronRight className="h-4 w-4 rotate-180" /> Back to list
              </button>
              
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Left Column */}
                <div className="space-y-4">
                  {/* Pattern Header */}
                  <div className={`rounded-2xl border p-6 ${getSignalBg(selectedPattern.signal)}`}>
                    <div className="flex items-center gap-4">
                      <div className="relative h-20 w-20">
                        <svg className="h-20 w-20 -rotate-90 transform">
                          <circle cx="40" cy="40" r="34" stroke="currentColor" strokeWidth="6" fill="none" className="text-white/10" />
                          <circle cx="40" cy="40" r="34" strokeWidth="6" fill="none" strokeLinecap="round"
                            strokeDasharray={`${(selectedPattern.completion / 100) * 213.6} 213.6`}
                            className={selectedPattern.completion >= 80 ? "stroke-emerald-500" : selectedPattern.completion >= 50 ? "stroke-amber-500" : "stroke-blue-500"}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-xl font-bold">{selectedPattern.completion}%</span>
                        </div>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-white">{t(`patternEngine.patterns.${selectedPattern.patternKey}.name`)}</h2>
                        <p className="mt-1 text-gray-400">{selectedPattern.symbol} • {selectedPattern.timeframe}</p>
                        <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-medium uppercase ${getStageColor(selectedPattern.stage)}`}>
                          {t(`patternEngine.stages.${selectedPattern.stage}`)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-white"><Info className="h-4 w-4 text-blue-400" />{t("patternEngine.patternInfo")}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-gray-300">{t(`patternEngine.patterns.${selectedPattern.patternKey}.description`)}</p>
                  </div>

                  {/* After Completion */}
                  <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400"><Target className="h-4 w-4" />{t("patternEngine.afterCompletion")}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-gray-300">{t(`patternEngine.patterns.${selectedPattern.patternKey}.afterCompletion`)}</p>
                  </div>

                  {/* Trading Strategy */}
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-emerald-400"><Zap className="h-4 w-4" />{t("patternEngine.tradingStrategy")}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-gray-300">{t(`patternEngine.patterns.${selectedPattern.patternKey}.tradingTip`)}</p>
                  </div>
                </div>

                {/* Right Column */}
                <div className="space-y-4">
                  {/* Price Levels */}
                  <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                    <h3 className="text-sm font-semibold text-white mb-4">Key Price Levels</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3">
                        <div className="flex items-center gap-2"><DollarSign className="h-4 w-4 text-emerald-400" /><span className="text-sm text-gray-400">{t("patternEngine.entryZone")}</span></div>
                        <span className="font-mono text-lg font-bold text-emerald-400">{selectedPattern.entry.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border border-blue-500/30 bg-blue-500/10 p-3">
                        <div className="flex items-center gap-2"><Target className="h-4 w-4 text-blue-400" /><span className="text-sm text-gray-400">{t("patternEngine.targetZone")}</span></div>
                        <span className="font-mono text-lg font-bold text-blue-400">{selectedPattern.target.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border border-red-500/30 bg-red-500/10 p-3">
                        <div className="flex items-center gap-2"><Shield className="h-4 w-4 text-red-400" /><span className="text-sm text-gray-400">{t("patternEngine.stopLoss")}</span></div>
                        <span className="font-mono text-lg font-bold text-red-400">{selectedPattern.stopLoss.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 p-5">
                      <div className="flex items-center gap-2 text-xs uppercase text-gray-500"><BarChart3 className="h-4 w-4" />{t("patternEngine.successRate")}</div>
                      <p className="mt-2 text-3xl font-bold text-white">{selectedPattern.successRate}%</p>
                      <p className="mt-1 text-xs text-gray-500">Historical accuracy</p>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 p-5">
                      <div className="flex items-center gap-2 text-xs uppercase text-gray-500"><Target className="h-4 w-4" />{t("patternEngine.riskReward")}</div>
                      <p className="mt-2 text-3xl font-bold text-white">1:{Math.abs((selectedPattern.target - selectedPattern.entry) / (selectedPattern.entry - selectedPattern.stopLoss)).toFixed(1)}</p>
                      <p className="mt-1 text-xs text-gray-500">Risk to reward ratio</p>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 p-5">
                      <div className="flex items-center gap-2 text-xs uppercase text-gray-500"><TrendUp className="h-4 w-4" />{t("patternEngine.expectedMove")}</div>
                      <p className={`mt-2 text-3xl font-bold ${selectedPattern.expectedMove >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {selectedPattern.expectedMove >= 0 ? "+" : ""}{selectedPattern.expectedMove}%
                      </p>
                      <p className="mt-1 text-xs text-gray-500">Projected price change</p>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-white/0 p-5">
                      <div className="flex items-center gap-2 text-xs uppercase text-gray-500"><Timer className="h-4 w-4" />{t("patternEngine.detected")}</div>
                      <p className="mt-2 text-xl font-bold text-white">{new Date(selectedPattern.detectedAt).toLocaleDateString()}</p>
                      <p className="mt-1 text-xs text-gray-500">Candle #{selectedPattern.detectedCandle}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Pattern List Grid
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredPatterns.map(pattern => {
                const patternName = t(`patternEngine.patterns.${pattern.patternKey}.name`) || pattern.patternKey;
                return (
                  <div
                    key={pattern.id}
                    onClick={() => setSelectedPattern(pattern)}
                    className={`group cursor-pointer rounded-xl border p-4 transition-all hover:scale-[1.02] hover:shadow-xl ${getSignalBg(pattern.signal)}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="relative h-14 w-14 flex-shrink-0">
                        <svg className="h-14 w-14 -rotate-90 transform">
                          <circle cx="28" cy="28" r="23" stroke="currentColor" strokeWidth="4" fill="none" className="text-white/10" />
                          <circle cx="28" cy="28" r="23" strokeWidth="4" fill="none" strokeLinecap="round"
                            strokeDasharray={`${(pattern.completion / 100) * 144.5} 144.5`}
                            className={pattern.completion >= 80 ? "stroke-emerald-500" : pattern.completion >= 50 ? "stroke-amber-500" : "stroke-blue-500"}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold">{pattern.completion}%</span>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-white truncate">{patternName}</h4>
                        <div className="mt-1 flex items-center gap-2 text-xs">
                          <span className={getSignalColor(pattern.signal)}>
                            {pattern.signal === "bullish" ? <ArrowUpRight className="inline h-3 w-3" /> : <ArrowDownRight className="inline h-3 w-3" />}
                            {t(`common.${pattern.signal}`)}
                          </span>
                          <span className="text-gray-500">•</span>
                          <span className="text-gray-400">{pattern.timeframe}</span>
                        </div>
                      </div>
                      <span className={`flex-shrink-0 rounded-full px-2 py-1 text-[10px] font-medium uppercase ${getStageColor(pattern.stage)}`}>
                        {t(`patternEngine.stages.${pattern.stage}`)}
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-center text-[10px]">
                      <div className="rounded-lg bg-white/5 py-1.5">
                        <p className="text-gray-500 uppercase">Success</p>
                        <p className="font-mono font-semibold text-white">{pattern.successRate}%</p>
                      </div>
                      <div className="rounded-lg bg-white/5 py-1.5">
                        <p className="text-gray-500 uppercase">Move</p>
                        <p className={`font-mono font-semibold ${pattern.expectedMove >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {pattern.expectedMove >= 0 ? "+" : ""}{pattern.expectedMove}%
                        </p>
                      </div>
                      <div className="rounded-lg bg-white/5 py-1.5">
                        <p className="text-gray-500 uppercase">Symbol</p>
                        <p className="font-mono font-semibold text-white">{pattern.symbol}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}

// Main Pattern Engine V2 Component
export default function PatternEngineV2() {
  const { t } = useI18nStore();
  const [selectedSymbol, setSelectedSymbol] = useState<"ALL" | "NASDAQ" | "XAUUSD">("ALL");
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const patterns = useMemo(() => generateMockPatterns(), []);

  const filteredPatterns = useMemo(() => {
    if (selectedSymbol === "ALL") return patterns;
    return patterns.filter((p) => p.symbol === selectedSymbol);
  }, [patterns, selectedSymbol]);

  const nasdaqPatterns = filteredPatterns.filter((p) => p.symbol === "NASDAQ");
  const xauusdPatterns = filteredPatterns.filter((p) => p.symbol === "XAUUSD");

  return (
    <div className="glass-card p-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-[0.2em] text-textSecondary">{t("patternEngine.title")}</p>
          <h3 className="mt-1 text-sm font-semibold truncate">{t("patternEngine.subtitle")}</h3>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Filter Tabs */}
          <div className="flex rounded-lg border border-white/10 bg-white/5 p-0.5">
            {(["ALL", "NASDAQ", "XAUUSD"] as const).map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`rounded px-2 py-1 text-[10px] font-medium transition-all ${
                  selectedSymbol === sym ? "bg-accent text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                {sym}
              </button>
            ))}
          </div>
          
          {/* Fullscreen Button */}
          <button
            onClick={() => setIsFullscreen(true)}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 transition-all hover:bg-white/10 hover:text-white"
            title="Expand to fullscreen"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Patterns List - Compact */}
      <div className="mt-4 space-y-4 max-h-[400px] overflow-y-auto pr-1">
        {/* NASDAQ Section */}
        {(selectedSymbol === "ALL" || selectedSymbol === "NASDAQ") && nasdaqPatterns.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-[11px] font-medium text-gray-500">
              <Layers className="h-3 w-3" />
              {t("patternEngine.nasdaqPatterns")}
              <span className="rounded-full bg-white/10 px-1.5 py-0.5 text-[10px]">{nasdaqPatterns.length}</span>
            </h4>
            <div className="space-y-2">
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
            <h4 className="mb-2 flex items-center gap-2 text-[11px] font-medium text-gray-500">
              <Layers className="h-3 w-3" />
              {t("patternEngine.xauusdPatterns")}
              <span className="rounded-full bg-white/10 px-1.5 py-0.5 text-[10px]">{xauusdPatterns.length}</span>
            </h4>
            <div className="space-y-2">
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
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Circle className="h-8 w-8 text-gray-600" />
            <p className="mt-2 text-xs text-gray-400">{t("patternEngine.noPatterns")}</p>
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

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <FullscreenPatternModal
          patterns={patterns}
          onClose={() => setIsFullscreen(false)}
          t={t}
        />
      )}
    </div>
  );
}
