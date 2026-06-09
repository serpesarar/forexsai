"use client";

import { useState } from "react";
import { RefreshCw, TrendingUp, TrendingDown, Minus, Activity, Target, HelpCircle, X } from "lucide-react";
import { useRtyhiimDetect, useConsolidation } from "../lib/api/rtyhiim";
import { useI18nStore } from "../lib/i18n/store";

interface RhythmDetectorSimpleProps {
  symbol?: string;
  symbolLabel?: string;
}

export default function RhythmDetectorSimple({ symbol = "NDX.INDX", symbolLabel = "NASDAQ" }: RhythmDetectorSimpleProps) {
  const { t, locale } = useI18nStore();
  const { data, isLoading, refetch } = useRtyhiimDetect(symbol);
  const { data: consolidation } = useConsolidation(symbol, 20, "1m");
  const [showInfo, setShowInfo] = useState(false);

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

  // Periyodu okunabilir biçimde göster (sn -> dk / saat)
  const formatPeriod = (seconds: number) => {
    if (!seconds || seconds <= 0) return "—";
    if (seconds < 90) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const rz = state?.reaction_zone;
  const noData = state?.data_source === "no_data" || state?.pattern_type === "insufficient_data";

  return (
    <>
      {/* Info Modal */}
      {showInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowInfo(false)}>
          <div className="bg-background border border-white/10 rounded-2xl p-6 max-w-lg mx-4 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{locale === "en" ? "Market Rhythm Guide" : "Piyasa Ritmi Rehberi"}</h3>
              <button onClick={() => setShowInfo(false)} className="p-1 hover:bg-white/10 rounded-full">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-textSecondary">
              <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <p className="font-medium text-emerald-400 mb-1">BUY {locale === "en" ? "Signal" : "Sinyali"}</p>
                <p>{locale === "en" ? "Pattern detected with upward momentum. High confidence = stronger signal." : "Yukarı momentum ile pattern tespit edildi. Yüksek güven = güçlü sinyal."}</p>
              </div>
              <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                <p className="font-medium text-red-400 mb-1">SELL {locale === "en" ? "Signal" : "Sinyali"}</p>
                <p>{locale === "en" ? "Pattern detected with downward momentum. Look for short opportunities." : "Aşağı momentum ile pattern tespit edildi. Short fırsatları arayın."}</p>
              </div>
              <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/20">
                <p className="font-medium text-cyan-400 mb-1">{locale === "en" ? "Consolidation (Sideways)" : "Konsolidasyon (Yatay)"}</p>
                <p>{locale === "en" ? "Price moving in a range. Wait for breakout direction before entering." : "Fiyat dar aralıkta hareket ediyor. Giriş yapmadan kırılım yönünü bekleyin."}</p>
              </div>
              <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <p className="font-medium text-amber-400 mb-1">{locale === "en" ? "Trending" : "Trend"}</p>
                <p>{locale === "en" ? "Clear directional movement. Trade with the trend, not against it." : "Net yönlü hareket. Trendle işlem yapın, karşısında değil."}</p>
              </div>
              <div className="p-3 bg-white/5 rounded-lg">
                <p className="font-medium text-white mb-1">{locale === "en" ? "Key Metrics" : "Önemli Metrikler"}</p>
                <ul className="space-y-1 text-xs">
                  <li>• <strong>{locale === "en" ? "Period" : "Periyot"}:</strong> {locale === "en" ? "Dominant cycle duration in seconds" : "Baskın döngü süresi (saniye)"}</li>
                  <li>• <strong>{locale === "en" ? "Regularity" : "Düzenlilik"}:</strong> {locale === "en" ? "How consistent the pattern is (higher = more reliable)" : "Pattern ne kadar tutarlı (yüksek = güvenilir)"}</li>
                  <li>• <strong>{locale === "en" ? "Amplitude" : "Genlik"}:</strong> {locale === "en" ? "Price swing magnitude" : "Fiyat salınım büyüklüğü"}</li>
                </ul>
              </div>
              <p className="text-xs p-3 bg-white/5 rounded-lg">💡 {locale === "en" ? "Use with other indicators for confirmation. High regularity + clear direction = best signals." : "Teyit için diğer göstergelerle birlikte kullanın. Yüksek düzenlilik + net yön = en iyi sinyaller."}</p>
            </div>
          </div>
        </div>
      )}
    <div className="glass-premium p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold">{t("rhythmPanel.title")}</h3>
          <p className="text-xs text-textSecondary">
            {symbolLabel} • {t("rhythmPanel.subtitle")}
            {state?.timeframe_used && state.timeframe_used !== "none" && (
              <span className="ml-1 px-1.5 py-0.5 rounded bg-white/10 text-[10px] font-mono">{state.timeframe_used}</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowInfo(true)}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition"
          >
            <HelpCircle className="w-4 h-4 text-textSecondary" />
          </button>
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
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
              <p className="text-xs text-textSecondary">{t("rhythmPanel.confidence")}</p>
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
              {isConsolidating ? t("rhythmPanel.sideways") : t("rhythmPanel.trending")}
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
                {t("rhythmPanel.breakoutExpected")}
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
                <span>{t("rhythmPanel.currentPrice")}: {consolidation.current_price.toFixed(2)}</span>
                <span>{t("rhythmPanel.position")}: %{consolidation.position_in_range.toFixed(0)}</span>
              </div>
            </div>

            {/* Özet Bilgiler */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-black/20 rounded-lg p-2">
                <p className="text-textSecondary text-[10px]">{t("rhythmPanel.range")}</p>
                <p className="font-semibold">{consolidation.range_percent.toFixed(2)}%</p>
              </div>
              <div className="bg-black/20 rounded-lg p-2">
                <p className="text-textSecondary text-[10px]">{t("rhythmPanel.score")}</p>
                <p className="font-semibold">{consolidation.consolidation_score}/100</p>
              </div>
              <div className="bg-black/20 rounded-lg p-2">
                <p className="text-textSecondary text-[10px]">{t("rhythmPanel.midpoint")}</p>
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
            <p className="text-[10px] text-textSecondary mb-1">{t("rhythmPanel.period")}</p>
            <p className="text-sm font-bold">{formatPeriod(state.dominant_period_s)}</p>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <p className="text-[10px] text-textSecondary mb-1">{t("rhythmPanel.regularity")}</p>
            <p className="text-sm font-bold">{Math.round(state.regularity * 100)}%</p>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <p className="text-[10px] text-textSecondary mb-1">{t("rhythmPanel.amplitude")}</p>
            <p className="text-sm font-bold">{state.amplitude.toFixed(2)}</p>
          </div>
        </div>
      )}

      {/* Tahminler */}
      {state?.predictions && state.predictions.length > 0 && (
        <div className="bg-white/5 rounded-xl p-3">
          <p className="text-xs text-textSecondary mb-2">{t("rhythmPanel.shortTermPredictions")}</p>
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

      {/* Sıradaki Tepki Bölgesi (Reaction Zone) */}
      {rz && (
        <div className={`rounded-xl p-4 border ${rz.next_type === "support" ? "bg-emerald-500/10 border-emerald-500/25" : "bg-red-500/10 border-red-500/25"}`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {rz.next_type === "support" ? (
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              <span className={`text-sm font-semibold ${rz.next_type === "support" ? "text-emerald-400" : "text-red-400"}`}>
                {locale === "en"
                  ? (rz.next_type === "support" ? "Next reaction: Support" : "Next reaction: Resistance")
                  : (rz.next_type === "support" ? "Sıradaki tepki: Destek" : "Sıradaki tepki: Direnç")}
              </span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/30 font-mono">
              ~{rz.eta_label}
            </span>
          </div>
          <div className="flex items-end justify-between">
            <div>
              <p className="text-[10px] text-textSecondary">{locale === "en" ? "Expected zone (price ± band)" : "Beklenen bölge (fiyat ± sapma)"}</p>
              <p className="text-lg font-bold font-mono">{rz.price.toFixed(2)}</p>
              <p className="text-[11px] text-textSecondary font-mono">{rz.lower.toFixed(2)} – {rz.upper.toFixed(2)}</p>
            </div>
            <div className="text-right">
              <span className={`text-xs font-bold px-2 py-1 rounded ${rz.expected_direction === "BUY" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                {rz.expected_direction}
              </span>
              {state?.touches_confirmed && (
                <p className="text-[10px] text-textSecondary mt-1">
                  {locale === "en" ? "confirmed" : "onaylı"} ✓ ({state.upper_touches}/{state.lower_touches})
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Yükleniyor */}
      {isLoading && (
        <div className="text-center py-2">
          <p className="text-xs text-textSecondary animate-pulse">{t("rhythmPanel.analyzing")}</p>
        </div>
      )}

      {/* Gerçek veri yok (sentetik göstermiyoruz) */}
      {!isLoading && noData && (
        <div className="text-center py-4">
          <Activity className="w-8 h-8 text-textSecondary mx-auto mb-2 opacity-50" />
          <p className="text-xs text-textSecondary">
            {locale === "en"
              ? "No real-time data for this symbol's finest timeframe yet."
              : "Bu sembolün en ince zaman dilimi için henüz canlı veri yok."}
          </p>
        </div>
      )}

      {/* Veri Yok */}
      {!isLoading && !state && (
        <div className="text-center py-4">
          <Activity className="w-8 h-8 text-textSecondary mx-auto mb-2 opacity-50" />
          <p className="text-xs text-textSecondary">{t("rhythmPanel.waitingData")}</p>
        </div>
      )}
    </div>
    </>
  );
}
