"use client";

/**
 * CandleInsightPanel — tıklanan mumun "Ne oldu?" paneli.
 * TradingView "Backtest fundamentals" deneyiminden ilhamla: özet + katalizörler
 * + makro bağlam (sparkline'lı) + teknik gözlem + seans rozeti.
 * Haber akışı yokken de anlamlı içerik üretir (makro/takvim/teknik).
 */

import React from "react";
import { format } from "date-fns";
import {
  ArrowDown, ArrowUp, Brain, Calendar, ChevronRight, Clock, Flame,
  Gauge, Newspaper, Sparkles, TrendingDown, TrendingUp, X, Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CandleContextResponse, CandleEvent, MacroDriver } from "@/lib/api/marketEvents";

interface CandleInsightPanelProps {
  data: CandleContextResponse | null;
  isLoading: boolean;
  error: string | null;
  locale: string;
  timeframe: string;
  onClose: () => void;
  onEventClick?: (event: CandleEvent) => void;
}

const T: Record<string, Record<string, string>> = {
  tr: {
    whatHappened: "Ne oldu?",
    candleWindow: "Mum aralığı",
    catalysts: "Katalizörler",
    macroContext: "Makro Bağlam",
    technicals: "Teknik Gözlem",
    open: "Açılış", close: "Kapanış", high: "Yüksek", low: "Düşük",
    volume: "Hacim",
    confidence: "Analiz güveni",
    loading: "Mum bağlamı analiz ediliyor...",
    error: "Bağlam yüklenemedi",
    noCatalyst: "Bu aralıkta bilinen katalizör yok",
    impact: "etki",
    bullish: "Yükseliş", bearish: "Düşüş", neutral: "Nötr",
    halfDay: "Yarım gün",
    holiday: "Tatil",
    significant: "Önemli hareket",
    forecast: "Bkl", previous: "Önc",
  },
  en: {
    whatHappened: "What happened?",
    candleWindow: "Candle window",
    catalysts: "Catalysts",
    macroContext: "Macro Context",
    technicals: "Technicals",
    open: "Open", close: "Close", high: "High", low: "Low",
    volume: "Volume",
    confidence: "Analysis confidence",
    loading: "Analyzing candle context...",
    error: "Failed to load context",
    noCatalyst: "No known catalyst in this window",
    impact: "impact",
    bullish: "Bullish", bearish: "Bearish", neutral: "Neutral",
    halfDay: "Half day",
    holiday: "Holiday",
    significant: "Significant move",
    forecast: "Fcst", previous: "Prev",
  },
};

function t(locale: string, key: string): string {
  return (T[locale] || T.en)[key] || T.en[key] || key;
}

function isTr(locale: string): boolean {
  return locale === "tr";
}

/** Küçük SVG sparkline — makro serinin son ~12 noktası. */
function Sparkline({ points, positive }: { points: number[]; positive: boolean }) {
  if (!points || points.length < 3) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const w = 64;
  const h = 20;
  const step = w / (points.length - 1);
  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${(h - ((p - min) / span) * (h - 3) - 1.5).toFixed(1)}`)
    .join(" ");
  const color = positive ? "#22c55e" : "#ef4444";
  return (
    <svg width={w} height={h} className="flex-shrink-0 opacity-90">
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle
        cx={w}
        cy={h - ((points[points.length - 1] - min) / span) * (h - 3) - 1.5}
        r="2"
        fill={color}
      />
    </svg>
  );
}

function MagnitudeBadge({ magnitude, label }: { magnitude: string; label: string }) {
  const styles: Record<string, string> = {
    extreme: "bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/40",
    big: "bg-red-500/15 text-red-300 border-red-500/40",
    notable: "bg-amber-500/15 text-amber-300 border-amber-500/40",
    minor: "bg-gray-700/50 text-gray-400 border-gray-600",
  };
  const icon = magnitude === "extreme" ? <Flame className="w-3 h-3" />
    : magnitude === "big" ? <Zap className="w-3 h-3" />
      : magnitude === "notable" ? <Gauge className="w-3 h-3" /> : null;
  return (
    <span className={cn(
      "inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border font-medium capitalize",
      styles[magnitude] || styles.minor
    )}>
      {icon}{label}
    </span>
  );
}

function eventIcon(type: CandleEvent["type"]) {
  if (type === "economic") return <Calendar className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />;
  if (type === "earnings") return <Sparkles className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />;
  return <Newspaper className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />;
}

function MacroRow({ driver, locale }: { driver: MacroDriver; locale: string }) {
  const rising = driver.direction === "up";
  const impactColor = driver.impact_on_symbol === "bullish"
    ? "text-green-400"
    : driver.impact_on_symbol === "bearish" ? "text-red-400" : "text-gray-500";
  return (
    <div className={cn(
      "flex items-center gap-2.5 p-2.5 rounded-lg border transition-colors",
      driver.is_significant
        ? "bg-sky-500/[0.06] border-sky-500/20"
        : "bg-gray-800/30 border-gray-800"
    )}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-semibold text-gray-200 truncate">{driver.label}</span>
          <span className={cn(
            "inline-flex items-center gap-0.5 text-[11px] font-mono font-semibold",
            rising ? "text-green-400" : "text-red-400"
          )}>
            {rising ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {driver.change_pct > 0 ? "+" : ""}{driver.change_pct}%
          </span>
        </div>
        <p className="text-[10px] text-gray-500 leading-snug mt-0.5 line-clamp-2">
          {isTr(locale) ? driver.note_tr : driver.note_en}
        </p>
      </div>
      <div className="flex flex-col items-end gap-1">
        <Sparkline points={driver.sparkline} positive={rising} />
        <span className={cn("text-[9px] uppercase tracking-wide font-semibold", impactColor)}>
          {driver.impact_on_symbol === "neutral"
            ? t(locale, "neutral")
            : driver.impact_on_symbol === "bullish" ? `↑ ${t(locale, "impact")}` : `↓ ${t(locale, "impact")}`}
        </span>
      </div>
    </div>
  );
}

export default function CandleInsightPanel({
  data, isLoading, error, locale, timeframe, onClose, onEventClick,
}: CandleInsightPanelProps) {
  const candle = data?.candle;
  const explanation = data?.explanation;
  const session = data?.session;
  const significance = data?.significance;
  const macro = data?.macro || [];
  const events = data?.events || [];
  const bullets = explanation
    ? (isTr(locale) ? explanation.bullets_tr : explanation.bullets_en)
    : [];

  const up = candle?.direction === "up";
  const flat = candle?.direction === "flat";

  return (
    <div className="absolute top-16 right-4 bottom-4 z-20 w-[380px] max-w-[calc(100%-2rem)] flex flex-col bg-[#0d0d12]/97 backdrop-blur-xl border border-gray-800 rounded-2xl shadow-[0_16px_60px_rgba(0,0,0,0.6)] overflow-hidden">
      {/* Üst şerit — yön rengiyle degrade */}
      <div className={cn(
        "h-1 w-full",
        flat ? "bg-gray-700" : up
          ? "bg-gradient-to-r from-green-500 via-emerald-400 to-transparent"
          : "bg-gradient-to-r from-red-500 via-rose-400 to-transparent"
      )} />

      {/* Header */}
      <div className="flex items-start justify-between px-4 pt-3.5 pb-3 border-b border-gray-800/80">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={cn(
              "text-base font-bold tracking-tight",
              flat ? "text-gray-200" : up ? "text-green-400" : "text-red-400"
            )}>
              {t(locale, "whatHappened")}
            </h3>
            {candle && !flat && (
              <span className={cn(
                "inline-flex items-center gap-1 text-xs font-mono font-bold px-2 py-0.5 rounded-md",
                up ? "bg-green-500/15 text-green-400" : "bg-red-500/15 text-red-400"
              )}>
                {up ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                {candle.change_pct > 0 ? "+" : ""}{candle.change_pct.toFixed(2)}%
              </span>
            )}
          </div>
          {candle && (
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <span className="inline-flex items-center gap-1 text-[10px] text-gray-400 font-mono bg-gray-800/60 px-2 py-0.5 rounded-md border border-gray-700/60">
                <Clock className="w-3 h-3" />
                {format(new Date(candle.timestamp * 1000), "d MMM HH:mm")}
                <span className="text-gray-600">·</span>
                {timeframe.toUpperCase()}
              </span>
              {session && (
                <span className="inline-flex items-center gap-1 text-[10px] text-gray-300 bg-violet-500/10 border border-violet-500/25 px-2 py-0.5 rounded-md">
                  {session.emoji} {isTr(locale) ? session.label_tr : session.label_en}
                </span>
              )}
              {session?.is_half_day && (
                <span className="text-[10px] text-amber-300 bg-amber-500/10 border border-amber-500/25 px-2 py-0.5 rounded-md">
                  {t(locale, "halfDay")}
                </span>
              )}
              {significance && significance.magnitude !== "minor" && (
                <MagnitudeBadge
                  magnitude={significance.magnitude}
                  label={isTr(locale) ? significance.magnitude_tr : significance.magnitude_en}
                />
              )}
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-1.5 -mr-1 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors flex-shrink-0"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-3.5 space-y-4 scrollbar-thin">
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-14 gap-3">
            <div className="relative">
              <div className="w-10 h-10 border-2 border-violet-500/20 border-t-violet-400 rounded-full animate-spin" />
              <Brain className="w-4 h-4 text-violet-400 absolute inset-0 m-auto" />
            </div>
            <span className="text-xs text-gray-500">{t(locale, "loading")}</span>
          </div>
        )}

        {!isLoading && error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/25 text-xs text-red-300">
            {/404/.test(error)
              ? (isTr(locale)
                ? "Backend bu özelliği içermiyor (market-events endpoint'i bulunamadı). Backend'i güncelleyip yeniden başlatın."
                : "The backend doesn't include this feature yet (market-events endpoint not found). Update and restart the backend.")
              : `${t(locale, "error")}: ${error}`}
          </div>
        )}

        {!isLoading && !error && data?.success && (
          <>
            {/* Özet */}
            {explanation && (
              <p className="text-[13px] text-gray-200 leading-relaxed font-medium">
                {isTr(locale) ? explanation.summary_tr : explanation.summary_en}
              </p>
            )}

            {/* Katalizör bullet'ları */}
            {bullets.length > 0 && (
              <ul className="space-y-2">
                {bullets.map((bullet, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-300 leading-relaxed">
                    <span className="text-gray-600 mt-0.5">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            )}

            {/* Olaylar (takvim/haber/bilanço) */}
            {events.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2 flex items-center gap-1.5">
                  <Calendar className="w-3 h-3" /> {t(locale, "catalysts")}
                  <span className="text-gray-600 font-normal">({events.length})</span>
                </h4>
                <div className="space-y-1.5">
                  {events.slice(0, 5).map((ev, i) => (
                    <button
                      key={`${ev.id}-${i}`}
                      onClick={() => onEventClick?.(ev)}
                      className="w-full text-left p-2.5 rounded-lg bg-gray-800/40 border border-gray-800 hover:border-gray-600 hover:bg-gray-800/70 transition-all group"
                    >
                      <div className="flex items-center gap-2">
                        {eventIcon(ev.type)}
                        <span className="text-[11px] text-gray-200 font-medium flex-1 truncate">
                          {isTr(locale) ? ev.title_tr : ev.title}
                        </span>
                        <span className="text-[10px] text-gray-500 font-mono">
                          {format(new Date(ev.timestamp), "HH:mm")}
                        </span>
                        <ChevronRight className="w-3 h-3 text-gray-600 group-hover:text-gray-400 transition-colors" />
                      </div>
                      {(ev.forecast || ev.previous) && (
                        <div className="flex gap-3 mt-1 ml-6 text-[10px] text-gray-500 font-mono">
                          {ev.forecast && <span>{t(locale, "forecast")}: {ev.forecast}</span>}
                          {ev.previous && <span>{t(locale, "previous")}: {ev.previous}</span>}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Makro bağlam */}
            {macro.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2 flex items-center gap-1.5">
                  🌐 {t(locale, "macroContext")}
                </h4>
                <div className="space-y-1.5">
                  {macro.slice(0, 4).map((driver) => (
                    <MacroRow key={driver.key} driver={driver} locale={locale} />
                  ))}
                </div>
              </div>
            )}

            {/* Teknik gözlem */}
            {explanation && (isTr(locale) ? explanation.technical_tr : explanation.technical_en) && (
              <div>
                <h4 className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-1.5 flex items-center gap-1.5">
                  <Gauge className="w-3 h-3" /> {t(locale, "technicals")}
                </h4>
                <p className="text-xs text-gray-400 leading-relaxed bg-gray-800/30 border border-gray-800 rounded-lg p-2.5">
                  {isTr(locale) ? explanation.technical_tr : explanation.technical_en}
                </p>
              </div>
            )}

            {/* OHLC */}
            {candle && (
              <div className="grid grid-cols-4 gap-1.5">
                {([
                  ["open", candle.open, "text-gray-200"],
                  ["high", candle.high, "text-green-400"],
                  ["low", candle.low, "text-red-400"],
                  ["close", candle.close, up ? "text-green-400" : flat ? "text-gray-200" : "text-red-400"],
                ] as const).map(([key, value, color]) => (
                  <div key={key} className="bg-gray-800/40 border border-gray-800 rounded-lg px-2 py-1.5 text-center">
                    <span className="block text-[9px] uppercase tracking-wide text-gray-600">{t(locale, key)}</span>
                    <span className={cn("block text-[11px] font-mono font-semibold", color)}>
                      {value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Güven barı */}
            {explanation && (
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[10px] text-gray-600 whitespace-nowrap">{t(locale, "confidence")}</span>
                <div className="flex-1 h-1 rounded-full bg-gray-800 overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-700",
                      explanation.confidence >= 60 ? "bg-green-500"
                        : explanation.confidence >= 40 ? "bg-amber-500" : "bg-gray-600"
                    )}
                    style={{ width: `${explanation.confidence}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-gray-500">{explanation.confidence}%</span>
              </div>
            )}
          </>
        )}

        {!isLoading && !error && data && !data.success && (
          <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800 text-xs text-gray-500">
            {t(locale, "noCatalyst")}
          </div>
        )}
      </div>
    </div>
  );
}
