"use client";

import { useMemo, useState } from "react";
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { useOrderBlockDetect } from "../lib/api/orderBlocks";
import { useFVGDetect } from "../lib/api/fvg";

interface OrderBlockPanelSimpleProps {
  symbol?: string;
  symbolLabel?: string;
}

export default function OrderBlockPanelSimple({ symbol = "NDX.INDX", symbolLabel = "NASDAQ" }: OrderBlockPanelSimpleProps) {
  const [timeframe, setTimeframe] = useState<"5m" | "15m" | "1h" | "4h">("15m");

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

  const { data, isLoading, refetch } = useOrderBlockDetect(payload);
  const { data: fvgData, isLoading: fvgLoading } = useFVGDetect({ symbol, timeframe, limit: 200 });

  const typedData = data as {
    order_blocks?: any[];
    combined_signal?: { action: string; confidence: number; reasoning: string[] };
  } | undefined;

  const orderBlocks = typedData?.order_blocks ?? [];
  const signal = typedData?.combined_signal;
  
  // En yakın bullish ve bearish OB
  const nearestBullish = orderBlocks.find(ob => ob.type === "bullish");
  const nearestBearish = orderBlocks.find(ob => ob.type === "bearish");

  // Sinyal rengi ve ikonu
  const getSignalStyle = (action: string) => {
    if (action === "BUY") return { bg: "bg-emerald-500/20", border: "border-emerald-500/50", text: "text-emerald-400", icon: TrendingUp };
    if (action === "SELL") return { bg: "bg-red-500/20", border: "border-red-500/50", text: "text-red-400", icon: TrendingDown };
    return { bg: "bg-zinc-500/20", border: "border-zinc-500/50", text: "text-zinc-400", icon: AlertCircle };
  };

  const signalStyle = signal ? getSignalStyle(signal.action) : null;
  const SignalIcon = signalStyle?.icon || AlertCircle;

  return (
    <div className="glass-card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold">Smart Money Zones</h3>
          <p className="text-xs text-textSecondary">{symbolLabel} • Order Blocks & FVG</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
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

      {/* Ana Sinyal - En Önemli Bilgi */}
      {signal && signalStyle && (
        <div className={`${signalStyle.bg} ${signalStyle.border} border rounded-xl p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${signalStyle.bg}`}>
                <SignalIcon className={`w-5 h-5 ${signalStyle.text}`} />
              </div>
              <div>
                <p className={`text-lg font-bold ${signalStyle.text}`}>{signal.action}</p>
                <p className="text-xs text-textSecondary">SMC Sinyali</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">{Math.round(signal.confidence * 100)}%</p>
              <p className="text-xs text-textSecondary">Güven</p>
            </div>
          </div>
          
          {/* Kısa Özet */}
          {signal.reasoning.length > 0 && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <p className="text-xs text-textSecondary">{signal.reasoning[0]}</p>
            </div>
          )}
        </div>
      )}

      {/* Kritik Zonlar - Sadece En Önemliler */}
      <div className="grid grid-cols-2 gap-3">
        {/* Destek (Bullish OB) */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-medium text-emerald-400">Destek Bölgesi</span>
          </div>
          {nearestBullish ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestBullish.zone_low).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                Güç: {Math.round(nearestBullish.score)}/100
              </p>
            </>
          ) : (
            <p className="text-xs text-textSecondary">Tespit edilmedi</p>
          )}
        </div>

        {/* Direnç (Bearish OB) */}
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-red-400" />
            <span className="text-xs font-medium text-red-400">Direnç Bölgesi</span>
          </div>
          {nearestBearish ? (
            <>
              <p className="text-sm font-mono font-bold text-white">
                {Number(nearestBearish.zone_high).toFixed(2)}
              </p>
              <p className="text-[10px] text-textSecondary mt-1">
                Güç: {Math.round(nearestBearish.score)}/100
              </p>
            </>
          ) : (
            <p className="text-xs text-textSecondary">Tespit edilmedi</p>
          )}
        </div>
      </div>

      {/* FVG (Boşluklar) - Basit Gösterim */}
      {fvgData && (fvgData.nearest_bullish || fvgData.nearest_bearish) && (
        <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-cyan-400">Fiyat Boşlukları (FVG)</span>
            <span className="text-[10px] text-textSecondary">
              {fvgData.unfilled_count || 0} açık
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

      {/* Kontrol Listesi - Ne Var Ne Yok */}
      <div className="bg-white/5 rounded-xl p-3">
        <p className="text-xs font-medium text-textSecondary mb-2">Yapı Kontrolü</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            {orderBlocks.some(ob => ob.has_choch) ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={orderBlocks.some(ob => ob.has_choch) ? "text-white" : "text-textSecondary"}>
              CHoCH (Trend Kırılımı)
            </span>
          </div>
          <div className="flex items-center gap-2">
            {orderBlocks.some(ob => ob.has_bos) ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={orderBlocks.some(ob => ob.has_bos) ? "text-white" : "text-textSecondary"}>
              BOS (Yapı Kırılımı)
            </span>
          </div>
          <div className="flex items-center gap-2">
            {fvgData?.unfilled_count ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={fvgData?.unfilled_count ? "text-white" : "text-textSecondary"}>
              FVG (Fiyat Boşluğu)
            </span>
          </div>
          <div className="flex items-center gap-2">
            {orderBlocks.length > 0 ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            ) : (
              <XCircle className="w-3 h-3 text-zinc-500" />
            )}
            <span className={orderBlocks.length > 0 ? "text-white" : "text-textSecondary"}>
              Order Block ({orderBlocks.length})
            </span>
          </div>
        </div>
      </div>

      {/* Yükleniyor */}
      {(isLoading || fvgLoading) && (
        <div className="text-center py-2">
          <p className="text-xs text-textSecondary animate-pulse">Analiz ediliyor...</p>
        </div>
      )}
    </div>
  );
}
