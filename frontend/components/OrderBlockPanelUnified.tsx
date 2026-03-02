"use client";

import { useMemo, useState } from "react";
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle, CheckCircle2, XCircle, HelpCircle, X, Layers } from "lucide-react";
import { useOrderBlockDetect } from "../lib/api/orderBlocks";
import { useFVGDetect } from "../lib/api/fvg";
import { useI18nStore } from "../lib/i18n/store";

const SYMBOLS = [
  { id: "NDX.INDX", label: "NASDAQ", flag: "🇺🇸" },
  { id: "XAUUSD", label: "XAUUSD", flag: "🥇" },
  { id: "GDAXI.INDX", label: "DAX", flag: "🇩🇪" },
  { id: "CL.COMM", label: "US OIL", flag: "🛢️" },
];

interface SymbolDataProps {
  symbol: string;
  symbolLabel: string;
  timeframe: "5m" | "15m" | "1h" | "4h";
  isActive: boolean;
}

function SymbolData({ symbol, symbolLabel, timeframe, isActive }: SymbolDataProps) {
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

  const { data, isLoading } = useOrderBlockDetect(payload);
  const { data: fvgData, isLoading: fvgLoading } = useFVGDetect({ symbol, timeframe, limit: 200 });

  const typedData = data as {
    order_blocks?: any[];
    combined_signal?: { action: string; confidence: number; reasoning: string[] };
  } | undefined;

  const orderBlocks = typedData?.order_blocks ?? [];
  const signal = typedData?.combined_signal;
  
  const nearestBullish = orderBlocks.find(ob => ob.type === "bullish");
  const nearestBearish = orderBlocks.find(ob => ob.type === "bearish");

  const getSignalStyle = (action: string) => {
    if (action === "BUY") return { bg: "bg-emerald-500/20", border: "border-emerald-500/50", text: "text-emerald-400", icon: TrendingUp };
    if (action === "SELL") return { bg: "bg-red-500/20", border: "border-red-500/50", text: "text-red-400", icon: TrendingDown };
    return { bg: "bg-zinc-500/20", border: "border-zinc-500/50", text: "text-zinc-400", icon: AlertCircle };
  };

  const signalStyle = signal ? getSignalStyle(signal.action) : null;
  const SignalIcon = signalStyle?.icon || AlertCircle;

  if (!isActive) return null;

  return (
    <div className="space-y-3 animate-in fade-in duration-200">
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
          {signal.reasoning.length > 0 && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <p className="text-xs text-textSecondary">{signal.reasoning[0]}</p>
            </div>
          )}
        </div>
      )}

      {/* Destek/Direnç Zonları */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-medium text-emerald-400">Support Zone</span>
          </div>
          {nearestBullish ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestBullish.zone_low).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                Strength: {Math.round(nearestBullish.score)}/100
              </p>
            </>
          ) : (
            <p className="text-xs text-textSecondary">Not detected</p>
          )}
        </div>

        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <span className="text-xs font-medium text-red-400">Resistance Zone</span>
          </div>
          {nearestBearish ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestBearish.zone_high).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                Strength: {Math.round(nearestBearish.score)}/100
              </p>
            </>
          ) : (
            <p className="text-xs text-textSecondary">Not detected</p>
          )}
        </div>
      </div>

      {/* FVG */}
      {fvgData && (fvgData.nearest_bullish || fvgData.nearest_bearish) && (
        <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-cyan-400">Fair Value Gaps (FVG)</span>
            <span className="text-[10px] text-textSecondary">
              {fvgData.unfilled_count || 0} open
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {fvgData.nearest_bullish && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span className="font-mono">{fvgData.nearest_bullish.gap_low.toFixed(2)}</span>
              </div>
            )}
            {fvgData.nearest_bearish && (
              <div className="flex items-center gap-2">
                <TrendingDown className="w-3 h-3 text-red-400" />
                <span className="font-mono">{fvgData.nearest_bearish.gap_high.toFixed(2)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Structure Check */}
      <div className="bg-white/5 rounded-xl p-3">
        <p className="text-xs font-medium text-textSecondary mb-2">Structure Check</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            {orderBlocks.some(ob => ob.has_choch) ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={orderBlocks.some(ob => ob.has_choch) ? "text-white" : "text-textSecondary"}>
              CHoCH
            </span>
          </div>
          <div className="flex items-center gap-2">
            {orderBlocks.some(ob => ob.has_bos) ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={orderBlocks.some(ob => ob.has_bos) ? "text-white" : "text-textSecondary"}>
              BOS
            </span>
          </div>
          <div className="flex items-center gap-2">
            {fvgData?.unfilled_count ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={fvgData?.unfilled_count ? "text-white" : "text-textSecondary"}>
              FVG
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

      {(isLoading || fvgLoading) && (
        <div className="text-center py-2">
          <p className="text-xs text-textSecondary animate-pulse">Analyzing...</p>
        </div>
      )}
    </div>
  );
}

export default function OrderBlockPanelUnified() {
  const { t } = useI18nStore();
  const [timeframe, setTimeframe] = useState<"5m" | "15m" | "1h" | "4h">("15m");
  const [activeSymbol, setActiveSymbol] = useState("NDX.INDX");
  const [showInfo, setShowInfo] = useState(false);

  const activeSymbolLabel = SYMBOLS.find(s => s.id === activeSymbol)?.label || "";

  return (
    <>
      {/* Info Modal */}
      {showInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowInfo(false)}>
          <div className="bg-background border border-white/10 rounded-2xl p-6 max-w-lg mx-4 space-y-4 max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{t("orderBlock.infoTitle")}</h3>
              <button onClick={() => setShowInfo(false)} className="p-1 hover:bg-white/10 rounded-full">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-textSecondary">
              <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                <p className="font-medium text-purple-400 mb-1">{t("orderBlock.infoAlgoTitle")}</p>
                <p className="text-xs">{t("orderBlock.infoAlgoDesc")}</p>
              </div>
              <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <p className="font-medium text-emerald-400 mb-1">{t("orderBlock.infoBullish")}</p>
                <p>{t("orderBlock.infoBullishDesc")}</p>
              </div>
              <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                <p className="font-medium text-red-400 mb-1">{t("orderBlock.infoBearish")}</p>
                <p>{t("orderBlock.infoBearishDesc")}</p>
              </div>
              <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
                <p className="font-medium text-cyan-400 mb-1">FVG (Fair Value Gap)</p>
                <p>{t("orderBlock.infoFvgDesc")}</p>
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
              <p className="text-xs text-textSecondary">4 Symbols • Order Blocks & FVG</p>
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
          {SYMBOLS.map((sym) => (
            <button
              key={sym.id}
              onClick={() => setActiveSymbol(sym.id)}
              className={`py-2 px-1 rounded-lg text-xs font-medium transition ${
                activeSymbol === sym.id
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
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition ${
                timeframe === tf
                  ? "bg-accent text-white"
                  : "bg-white/5 text-textSecondary hover:bg-white/10"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Symbol Data */}
        {SYMBOLS.map((sym) => (
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
