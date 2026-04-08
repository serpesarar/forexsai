"use client";

import { useEffect, useMemo, useState } from "react";
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle, CheckCircle2, XCircle, HelpCircle, X, Layers, Activity, Clock3, ChevronRight, Zap } from "lucide-react";
import { useOrderBlockBacktest, useOrderBlockDetect } from "../lib/api/orderBlocks";
import { useRefreshAge } from "../hooks/useRefreshAge";
import { useI18nStore } from "../lib/i18n/store";
import SMCPanel from "./panels/SMCPanel";

const SYMBOLS = [
  { id: "NDX.INDX", label: "NASDAQ", flag: "🇺🇸" },
  { id: "XAUUSD", label: "XAUUSD", flag: "🥇" },
  { id: "GDAXI.INDX", label: "DAX", flag: "🇩🇪" },
  { id: "USOIL.FOREX", label: "US OIL", flag: "🛢️" },
];

interface SymbolDataProps {
  symbol: string;
  symbolLabel: string;
  timeframe: "5m" | "15m" | "1h" | "4h";
  isActive: boolean;
}

// Types for new API response
interface CHoCH {
  detected: boolean;
  type: string;
  index: number;
  price: number;
  prev_swing: number;
  strength: string;
}

interface BOS {
  detected: boolean;
  type: string;
  index: number;
  price: number;
  broken_level: number;
  confirmation: boolean;
}

interface FVG {
  detected: boolean;
  direction: string;
  high: number;
  low: number;
  size: number;
  filled: boolean;
  fill_percentage: number;
}

interface OrderBlock {
  detected: boolean;
  type: string;
  zone_low: number;
  zone_high: number;
  score: number;
  strength: string;
  tested: boolean;
  mitigated: boolean;
}

interface StructureData {
  choch: CHoCH[];
  bos: BOS[];
  fvg: FVG[];
  order_blocks: OrderBlock[];
  trend: string;
  counts: {
    choch: number;
    bos: number;
    fvg: number;
    ob: number;
  };
}

interface SupportResistanceLevel {
  type: string;
  name: string;
  price: number;
  distance: number;
  distance_display: string;
  strength: string;
  is_next?: boolean;
  touch_count?: number;
}

interface SupportResistanceData {
  all_levels?: SupportResistanceLevel[];
  nearest_support?: SupportResistanceLevel | null;
  nearest_resistance?: SupportResistanceLevel | null;
  pivot?: number;
  range_high?: number;
  range_low?: number;
  method?: string;
}

interface ApiResponse {
  symbol: string;
  order_blocks?: OrderBlock[];
  structure?: StructureData;
  choch_list?: CHoCH[];
  bos_list?: BOS[];
  fvg_list?: FVG[];
  combined_signal?: { action: string; confidence: number; reasoning: string[]; reasons: string[] };
  trend?: string;
  support_resistance?: SupportResistanceData;
  timestamp?: string;
  warning?: string;
}

interface OrderBlockPanelUnifiedProps {
  symbol?: string;
}

function SymbolData({ symbol, symbolLabel, timeframe, isActive }: SymbolDataProps) {
  const [showProfessional, setShowProfessional] = useState(false);
  const payload = useMemo(() => ({
    symbol,
    timeframe,
    limit: 500,
    config: {
      fractal_period: 2,
      min_displacement_atr: 1.0,
      min_score: 50,
      zone_type: "wick" as const,
      max_tests: 2
    }
  }), [symbol, timeframe]);

  const { data, isLoading, isFetching, error, refetch } = useOrderBlockDetect(payload);
  const backtestMutation = useOrderBlockBacktest();

  const typedData = data as unknown as ApiResponse | undefined;
  const analyzedAt = typedData?.timestamp || null;
  const { refreshAge, markRefreshed } = useRefreshAge(analyzedAt ? new Date(analyzedAt) : null);

  useEffect(() => {
    if (analyzedAt) {
      markRefreshed(analyzedAt);
    }
  }, [analyzedAt, markRefreshed]);

  // Extract data from new API structure
  const structure = typedData?.structure;
  const orderBlocks = structure?.order_blocks ?? typedData?.order_blocks ?? [];
  const chochList = structure?.choch ?? typedData?.choch_list ?? [];
  const bosList = structure?.bos ?? typedData?.bos_list ?? [];
  const fvgList = structure?.fvg ?? [];
  const trend = structure?.trend ?? typedData?.trend ?? "ranging";
  const signal = typedData?.combined_signal;
  const supportResistance = typedData?.support_resistance;

  const nearestBullish = orderBlocks.find((ob: OrderBlock) => ob.type === "bullish");
  const nearestBearish = orderBlocks.find((ob: OrderBlock) => ob.type === "bearish");
  const nearestSupport = supportResistance?.nearest_support ?? null;
  const nearestResistance = supportResistance?.nearest_resistance ?? null;

  // Latest CHoCH and BOS
  const latestCHoCH = chochList[chochList.length - 1];
  const latestBOS = bosList[bosList.length - 1];

  // Unfilled FVGs
  const unfilledFVGs = fvgList.filter((fvg: FVG) => !fvg.filled);

  const getSignalStyle = (action: string) => {
    if (action === "BUY" || action === "STRONG BUY") return { bg: "bg-emerald-500/20", border: "border-emerald-500/50", text: "text-emerald-400", icon: TrendingUp };
    if (action === "SELL" || action === "STRONG SELL") return { bg: "bg-red-500/20", border: "border-red-500/50", text: "text-red-400", icon: TrendingDown };
    return { bg: "bg-zinc-500/20", border: "border-zinc-500/50", text: "text-zinc-400", icon: AlertCircle };
  };

  const signalStyle = signal ? getSignalStyle(signal.action) : null;
  const SignalIcon = signalStyle?.icon || AlertCircle;
  const srMethodLabel = supportResistance?.method === "swing_cluster_fib"
    ? "Clustered swings + Fib fallback"
    : "Order block fallback";
  const backtestError = backtestMutation.error instanceof Error ? backtestMutation.error.message : null;

  if (!isActive) return null;

  if (error) {
    return (
      <div className="p-4 text-center">
        <AlertCircle className="w-6 h-6 text-red-400 mx-auto mb-2" />
        <p className="text-xs text-red-400">Error loading data</p>
      </div>
    );
  }

  return (
    <>
      {showProfessional && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-3 backdrop-blur-sm md:items-center" onClick={() => setShowProfessional(false)}>
          <div className="w-full max-w-4xl overflow-hidden rounded-2xl border border-white/10 bg-background shadow-2xl" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <h3 className="text-base font-semibold text-white">Professional Smart Money Details</h3>
                <p className="text-xs text-textSecondary">{symbolLabel} • Daily rule-based structure, liquidity, gaps and bias context</p>
              </div>
              <button onClick={() => setShowProfessional(false)} className="rounded-lg border border-white/10 bg-white/5 p-2 text-textSecondary transition hover:bg-white/10">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="max-h-[78vh] overflow-y-auto">
              <SMCPanel lockedSymbol={symbol} />
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3 animate-in fade-in duration-200">
      {analyzedAt && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[11px] text-textSecondary">
          <div className="flex flex-wrap items-center gap-2">
            <Clock3 className="h-3.5 w-3.5" />
            <span>
              Last scan: {new Date(analyzedAt).toLocaleString()}
            </span>
            <span className="rounded-full border border-purple-500/20 bg-purple-500/10 px-2 py-0.5 font-semibold text-purple-300">
              {refreshAge}
            </span>
          </div>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-[11px] font-medium text-textSecondary transition hover:bg-white/10"
            disabled={isFetching}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      )}

      {typedData?.warning && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
          {typedData.warning}
        </div>
      )}

      {/* Trend Indicator */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <span className="text-xs text-textSecondary">Market Trend</span>
        </div>
        <span className={`text-xs font-medium ${trend === "bullish" ? "text-emerald-400" :
            trend === "bearish" ? "text-red-400" : "text-yellow-400"
          }`}>
          {trend.toUpperCase()}
        </span>
      </div>

      {/* Ana Sinyal */}
      {signal && signalStyle && (
        <div className={`${signalStyle.bg} ${signalStyle.border} border rounded-xl p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${signalStyle.bg}`}>
                <SignalIcon className={`w-5 h-5 ${signalStyle.text}`} />
              </div>
              <div>
                <p className={`text-lg font-bold ${signalStyle.text}`}>{signal.action}</p>
                <p className="text-xs text-textSecondary">SMC Signal</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{Math.round(signal.confidence * 100)}%</p>
              <p className="text-xs text-textSecondary">Confidence</p>
            </div>
          </div>
          {signal.reasons && signal.reasons.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {signal.reasons.map((reason, index) => (
                <span
                  key={`${reason}-${index}`}
                  className="rounded-full border border-white/10 bg-white/10 px-2 py-1 text-[10px] font-medium text-white/90"
                >
                  {reason}
                </span>
              ))}
            </div>
          )}
          {signal.reasoning && signal.reasoning.length > 0 && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <p className="text-xs text-textSecondary">{signal.reasoning[0]}</p>
            </div>
          )}
        </div>
      )}

      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-white">Backtest Snapshot</p>
            <p className="text-[11px] text-textSecondary">Historical order block signals over the latest 500 candles</p>
          </div>
          <button
            onClick={() => backtestMutation.mutate({ symbol, timeframe, config: payload.config })}
            disabled={backtestMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/10 px-3 py-2 text-xs font-medium text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${backtestMutation.isPending ? "animate-spin" : ""}`} />
            {backtestMutation.isPending ? "Running..." : "Run Backtest"}
          </button>
        </div>

        {backtestMutation.data && (
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="text-[10px] uppercase tracking-wide text-textSecondary">Win Rate</p>
              <p className="mt-1 text-xl font-bold text-emerald-400">{backtestMutation.data.win_rate}%</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="text-[10px] uppercase tracking-wide text-textSecondary">Signals</p>
              <p className="mt-1 text-xl font-bold text-white">{backtestMutation.data.total_signals}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="text-[10px] uppercase tracking-wide text-textSecondary">Wins</p>
              <p className="mt-1 text-xl font-bold text-emerald-400">{backtestMutation.data.wins}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3">
              <p className="text-[10px] uppercase tracking-wide text-textSecondary">Losses</p>
              <p className="mt-1 text-xl font-bold text-red-400">{backtestMutation.data.losses}</p>
            </div>
          </div>
        )}

        {!backtestMutation.data && !backtestMutation.isPending && !backtestError && (
          <p className="mt-3 text-xs text-textSecondary">Run the backtest to see win rate and resolved signal counts.</p>
        )}

        {backtestError && (
          <p className="mt-3 text-xs text-red-400">{backtestError}</p>
        )}
      </div>

      {/* Destek/Direnç Zonları */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-medium text-emerald-400">Nearest Support</span>
          </div>
          {nearestSupport ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestSupport.price).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                {nearestSupport.name} • {nearestSupport.distance_display} • {nearestSupport.strength}
                {nearestSupport.touch_count ? ` • Touches: ${nearestSupport.touch_count}` : ""}
              </p>
            </>
          ) : nearestBullish ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestBullish.zone_low).toFixed(2)} - {Number(nearestBullish.zone_high).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                OB fallback • Strength: {nearestBullish.strength} • Score: {nearestBullish.score}/100
              </p>
            </>
          ) : (
            <p className="text-xs text-textSecondary">Not detected</p>
          )}
        </div>

        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <span className="text-xs font-medium text-red-400">Nearest Resistance</span>
          </div>
          {nearestResistance ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestResistance.price).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                {nearestResistance.name} • {nearestResistance.distance_display} • {nearestResistance.strength}
                {nearestResistance.touch_count ? ` • Touches: ${nearestResistance.touch_count}` : ""}
              </p>
            </>
          ) : nearestBearish ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestBearish.zone_low).toFixed(2)} - {Number(nearestBearish.zone_high).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                OB fallback • Strength: {nearestBearish.strength} • Score: {nearestBearish.score}/100
              </p>
            </>
          ) : (
            <p className="text-xs text-textSecondary">Not detected</p>
          )}
        </div>
      </div>

      {(nearestSupport || nearestResistance) && (
        <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[10px] text-textSecondary">
          Method: {srMethodLabel}
        </div>
      )}

      <button
        onClick={() => setShowProfessional(true)}
        className="flex w-full items-center justify-between rounded-xl border border-purple-500/20 bg-purple-500/10 px-4 py-3 text-left transition hover:bg-purple-500/15"
      >
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-purple-500/15 p-2">
            <Zap className="h-4 w-4 text-purple-300" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Professional Details</p>
            <p className="text-[11px] text-textSecondary">Open the legacy Smart Money analysis as a deeper, scrollable context panel</p>
          </div>
        </div>
        <ChevronRight className="h-4 w-4 text-purple-300" />
      </button>

      {/* CHoCH Detection */}
      {latestCHoCH && (
        <div className={`rounded-xl p-3 border ${latestCHoCH.type === "bullish"
            ? "bg-emerald-500/10 border-emerald-500/30"
            : "bg-red-500/10 border-red-500/30"
          }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${latestCHoCH.type === "bullish" ? "text-emerald-400" : "text-red-400"
                }`}>
                CHoCH ({latestCHoCH.type.toUpperCase()})
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10">
                {latestCHoCH.strength}
              </span>
            </div>
            <span className="text-xs font-mono">{latestCHoCH.price.toFixed(2)}</span>
          </div>
        </div>
      )}

      {/* BOS Detection */}
      {latestBOS && (
        <div className={`rounded-xl p-3 border ${latestBOS.type === "bullish"
            ? "bg-blue-500/10 border-blue-500/30"
            : "bg-orange-500/10 border-orange-500/30"
          }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium ${latestBOS.type === "bullish" ? "text-blue-400" : "text-orange-400"
                }`}>
                BOS ({latestBOS.type.toUpperCase()})
              </span>
              {latestBOS.confirmation && (
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              )}
            </div>
            <span className="text-xs font-mono">{latestBOS.price.toFixed(2)}</span>
          </div>
        </div>
      )}

      {/* FVG List */}
      {unfilledFVGs.length > 0 && (
        <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-cyan-400">Fair Value Gaps (FVG)</span>
            <span className="text-[10px] text-textSecondary">{unfilledFVGs.length} open</span>
          </div>
          <div className="space-y-1">
            {unfilledFVGs.slice(0, 3).map((fvg: FVG, i: number) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  {fvg.direction === "bullish" ? (
                    <TrendingUp className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-400" />
                  )}
                  <span className="font-mono">{fvg.low.toFixed(2)} - {fvg.high.toFixed(2)}</span>
                </div>
                <span className="text-[10px] text-textSecondary">
                  {fvg.fill_percentage.toFixed(0)}% filled
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Structure Check Summary */}
      <div className="bg-white/5 rounded-xl p-3">
        <p className="text-xs font-medium text-textSecondary mb-2">Structure Check</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            {chochList.length > 0 ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={chochList.length > 0 ? "text-white" : "text-textSecondary"}>
              CHoCH ({chochList.length})
            </span>
          </div>
          <div className="flex items-center gap-2">
            {bosList.length > 0 ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={bosList.length > 0 ? "text-white" : "text-textSecondary"}>
              BOS ({bosList.length})
            </span>
          </div>
          <div className="flex items-center gap-2">
            {fvgList.length > 0 ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={fvgList.length > 0 ? "text-white" : "text-textSecondary"}>
              FVG ({fvgList.length})
            </span>
          </div>
          <div className="flex items-center gap-2">
            {orderBlocks.length > 0 ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={orderBlocks.length > 0 ? "text-white" : "text-textSecondary"}>
              OB ({orderBlocks.length})
            </span>
          </div>
        </div>
      </div>

      {(isLoading || isFetching) && (
        <div className="text-center py-2">
          <p className="text-xs text-textSecondary animate-pulse">Analyzing...</p>
        </div>
      )}
      </div>
    </>
  );
}

export default function OrderBlockPanelUnified({ symbol }: OrderBlockPanelUnifiedProps) {
  const { t } = useI18nStore();
  const initialSymbol = symbol ?? "NDX.INDX";
  const isSymbolLocked = Boolean(symbol);
  const [timeframe, setTimeframe] = useState<"5m" | "15m" | "1h" | "4h">("5m");
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    setActiveSymbol(initialSymbol);
  }, [initialSymbol]);

  const activeSymbolLabel = SYMBOLS.find(s => s.id === activeSymbol)?.label || "";
  const visibleSymbols = isSymbolLocked ? SYMBOLS.filter((item) => item.id === activeSymbol) : SYMBOLS;

  return (
    <>
      {/* Info Modal */}
      {showInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowInfo(false)}>
          <div className="bg-background border border-white/10 rounded-2xl p-6 max-w-lg mx-4 space-y-4 max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Smart Money Concepts</h3>
              <button onClick={() => setShowInfo(false)} className="p-1 hover:bg-white/10 rounded-full">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-textSecondary">
              <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                <p className="font-medium text-purple-400 mb-1">Order Blocks</p>
                <p className="text-xs">Institutional zones where smart money accumulated positions.</p>
              </div>
              <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <p className="font-medium text-emerald-400 mb-1">CHoCH (Change of Character)</p>
                <p className="text-xs">Trend reversal signal - price breaks previous swing against trend.</p>
              </div>
              <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <p className="font-medium text-blue-400 mb-1">BOS (Break of Structure)</p>
                <p className="text-xs">Trend continuation signal - price breaks previous swing in trend direction.</p>
              </div>
              <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
                <p className="font-medium text-cyan-400 mb-1">FVG (Fair Value Gap)</p>
                <p className="text-xs">Price imbalance zone - market often returns to fill these gaps.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="glass-premium p-5 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-purple-400" />
            <div>
              <h3 className="text-base font-semibold">Smart Money Zones</h3>
              <p className="text-xs text-textSecondary">4 Symbols • CHoCH, BOS, FVG, OB Detection</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowInfo(true)}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition"
            >
              <HelpCircle className="w-4 h-4 text-textSecondary" />
            </button>
          </div>
        </div>

        {/* Symbol Selector - Tabs */}
        <div className="grid grid-cols-4 gap-1">
          {visibleSymbols.map((sym) => (
            <button
              key={sym.id}
              onClick={() => !isSymbolLocked && setActiveSymbol(sym.id)}
              className={`py-2 px-1 rounded-lg text-xs font-medium transition ${activeSymbol === sym.id
                  ? "bg-purple-500 text-white"
                  : "bg-white/5 text-textSecondary hover:bg-white/10"
                }`}
            >
              <span className="mr-1">{sym.flag}</span>
              {sym.label}
            </button>
          ))}
        </div>

        {/* Timeframe Selector */}
        <div className="flex gap-1">
          {(["5m", "15m", "1h", "4h"] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition ${timeframe === tf
                  ? "bg-accent text-white"
                  : "bg-white/5 text-textSecondary hover:bg-white/10"
                }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Symbol Data */}
        {visibleSymbols.map((sym) => (
          <SymbolData
            key={sym.id}
            symbol={sym.id}
            symbolLabel={sym.label}
            timeframe={timeframe}
            isActive={activeSymbol === sym.id}
          />
        ))}
      </div>
    </>
  );
}
