"use client";

import { useState } from "react";
import { RefreshCw, TrendingUp, TrendingDown, Minus, Activity, Target } from "lucide-react";
import { useRtyhiimDetect, useConsolidation } from "../lib/api/rtyhiim";

interface RhythmDetectorSimpleProps {
  symbol?: string;
  symbolLabel?: string;
}

export default function RhythmDetectorSimple({ symbol = "NDX.INDX", symbolLabel = "NASDAQ" }: RhythmDetectorSimpleProps) {
  const { data, isLoading, refetch } = useRtyhiimDetect(symbol);
  const { data: consolidation } = useConsolidation(symbol, 20, "1m");

  const state = (data as any)?.state;

  // Yön ikonu ve rengi
  const getDirectionStyle = (direction: string) => {
    if (direction === "BUY") return { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/20" };
    if (direction === "SELL") return { icon: TrendingDown, color: "text-red-400", bg: "bg-red-500/20" };
    return { icon: Minus, color: "text-zinc-400", bg: "bg-zinc-500/20" };
  };

  const directionStyle = state ? getDirectionStyle(state.direction) : null;
  const DirectionIcon = directionStyle?.icon || Activity;

  // Consolidation durumu
  const isConsolidating = consolidation?.is_consolidating;
  const breakoutDir = consolidation?.breakout_direction;

  return (
    <div className="glass-card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold">Piyasa Ritmi</h3>
          <p className="text-xs text-textSecondary">{symbolLabel} • Hareket Analizi</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Ana Durum Kartı */}
      {state && directionStyle && (
        <div className={`${directionStyle.bg} border border-white/10 rounded-xl p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl ${directionStyle.bg}`}>
                <DirectionIcon className={`w-6 h-6 ${directionStyle.color}`} />
              </div>
              <div>
                <p className={`text-xl font-bold ${directionStyle.color}`}>{state.direction}</p>
                <p className="text-xs text-textSecondary">{state.pattern_type}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold">{Math.round(state.confidence * 100)}%</p>
              <p className="text-xs text-textSecondary">Güven</p>
            </div>
          </div>
        </div>
      )}

      {/* Consolidation / Trend Durumu */}
      <div className={`rounded-xl p-4 ${isConsolidating ? "bg-cyan-500/10 border border-cyan-500/20" : "bg-amber-500/10 border border-amber-500/20"}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Target className={`w-4 h-4 ${isConsolidating ? "text-cyan-400" : "text-amber-400"}`} />
            <span className={`text-sm font-medium ${isConsolidating ? "text-cyan-400" : "text-amber-400"}`}>
              {isConsolidating ? "YATAY HAREKET" : "TREND HAREKETİ"}
            </span>
          </div>
          {breakoutDir && breakoutDir !== "NONE" && (
            <div className="flex items-center gap-1">
              {breakoutDir === "UP" ? (
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              <span className={`text-xs font-medium ${breakoutDir === "UP" ? "text-emerald-400" : "text-red-400"}`}>
                Kırılım Bekleniyor
              </span>
            </div>
          )}
        </div>

        {consolidation && (
          <>
            {/* Fiyat Aralığı */}
            <div className="bg-black/20 rounded-lg p-3 mb-3">
              <div className="flex justify-between text-xs mb-2">
                <span className="text-emerald-400">↑ {consolidation.range_high.toFixed(2)}</span>
                <span className="text-red-400">↓ {consolidation.range_low.toFixed(2)}</span>
              </div>
              
              {/* Range Bar */}
              <div className="relative h-4 bg-zinc-700 rounded-full overflow-hidden">
                <div 
                  className={`absolute h-full rounded-full transition-all ${isConsolidating ? "bg-cyan-500" : "bg-amber-500"}`}
                  style={{ width: `${Math.min(100, Math.max(5, consolidation.position_in_range))}%` }}
                />
                {/* Orta nokta çizgisi */}
                <div className="absolute w-0.5 h-full bg-white/30 left-1/2" />
              </div>
              
              <div className="flex justify-between text-[10px] text-textSecondary mt-2">
                <span>Şu an: {consolidation.current_price.toFixed(2)}</span>
                <span>Pozisyon: %{consolidation.position_in_range.toFixed(0)}</span>
              </div>
            </div>

            {/* Özet Bilgiler */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-black/20 rounded-lg p-2">
                <p className="text-textSecondary text-[10px]">Aralık</p>
                <p className="font-semibold">{consolidation.range_percent.toFixed(2)}%</p>
              </div>
              <div className="bg-black/20 rounded-lg p-2">
                <p className="text-textSecondary text-[10px]">Skor</p>
                <p className="font-semibold">{consolidation.consolidation_score}/100</p>
              </div>
              <div className="bg-black/20 rounded-lg p-2">
                <p className="text-textSecondary text-[10px]">Orta</p>
                <p className="font-semibold font-mono">{consolidation.midpoint.toFixed(0)}</p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Ritim Detayları */}
      {state && (
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <p className="text-[10px] text-textSecondary mb-1">Periyot</p>
            <p className="text-sm font-bold">{state.dominant_period_s.toFixed(0)}s</p>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <p className="text-[10px] text-textSecondary mb-1">Düzenlilik</p>
            <p className="text-sm font-bold">{Math.round(state.regularity * 100)}%</p>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <p className="text-[10px] text-textSecondary mb-1">Genlik</p>
            <p className="text-sm font-bold">{state.amplitude.toFixed(2)}</p>
          </div>
        </div>
      )}

      {/* Tahminler */}
      {state?.predictions && state.predictions.length > 0 && (
        <div className="bg-white/5 rounded-xl p-3">
          <p className="text-xs text-textSecondary mb-2">Kısa Vadeli Tahminler</p>
          <div className="flex flex-wrap gap-2">
            {state.predictions.map((p: any) => (
              <div key={p.horizon} className="bg-black/20 rounded-lg px-3 py-1.5">
                <span className="text-[10px] text-textSecondary">{p.horizon}: </span>
                <span className="text-xs font-mono font-semibold">{p.value.toFixed(0)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Yükleniyor */}
      {isLoading && (
        <div className="text-center py-2">
          <p className="text-xs text-textSecondary animate-pulse">Analiz ediliyor...</p>
        </div>
      )}

      {/* Veri Yok */}
      {!isLoading && !state && (
        <div className="text-center py-4">
          <Activity className="w-8 h-8 text-textSecondary mx-auto mb-2 opacity-50" />
          <p className="text-xs text-textSecondary">Ritim verisi bekleniyor...</p>
        </div>
      )}
    </div>
  );
}
