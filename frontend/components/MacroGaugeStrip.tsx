"use client";

/**
 * MacroGaugeStrip — Hero-row of 4 macro speedometers
 * ===================================================
 * Sits next to the PSI Speedometer at the top of the dashboard.
 *
 *   [ DXY ]  [ VIX ]  [ Yield Curve ]  [ Risk-On / Off ]
 *
 * Tooltip is rendered via React portal at <body> level so it never gets
 * clipped by an ancestor's overflow. It is positioned with `position: fixed`
 * relative to the hovered gauge and edge-aware (flips left/right/below if it
 * would overflow the viewport).
 *
 * Localization: titles / summaries / threshold tables / direction-bias
 * sentences come from a TR/EN content map keyed by gauge + state. Backend
 * tooltip is used only as an EN fallback if a key is missing.
 */

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { fetcher } from "../lib/api";
import { useI18nStore, type Locale } from "../lib/i18n/store";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ThresholdRow { range: string; label: string; effect: string; }
interface GaugeTooltip {
  title: string;
  summary: string;
  interpretation: string;
  thresholds: ThresholdRow[];
}
interface MacroGauge {
  key: string;             // dxy / vix / yield_curve / risk_ratio
  label: string;
  subtitle?: string;
  status: "live" | "loading" | "error";
  value: number | null;
  z_score?: number | null;
  spread?: number | null;
  score: number;
  level: string;
  color: string;
  tooltip: GaugeTooltip;
}
interface MacroResponse { success: boolean; gauges: MacroGauge[]; }

// ─── Geometry ────────────────────────────────────────────────────────────────

const SWEEP = 240;
const HALF_SWEEP = SWEEP / 2;
const CX = 100;
const CY = 100;
const R = 78;

function pointAt(r: number, deg: number): { x: number; y: number } {
  const rad = (deg * Math.PI) / 180;
  return { x: CX + r * Math.sin(rad), y: CY - r * Math.cos(rad) };
}
function arcPath(r: number, startDeg: number, endDeg: number): string {
  const a = pointAt(r, startDeg);
  const b = pointAt(r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${a.x} ${a.y} A ${r} ${r} 0 ${large} 1 ${b.x} ${b.y}`;
}
function angleFromScore(score: number): number {
  return -HALF_SWEEP + (Math.max(0, Math.min(100, score)) / 100) * SWEEP;
}

// ─── Animated number ─────────────────────────────────────────────────────────

function useAnimatedNumber(target: number, duration = 900): number {
  const [val, setVal] = useState(target);
  const fromRef = useRef(target);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  useEffect(() => {
    fromRef.current = val;
    startRef.current = null;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    const tick = (ts: number) => {
      if (startRef.current === null) startRef.current = ts;
      const t = Math.min(1, (ts - startRef.current) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setVal(fromRef.current + (target - fromRef.current) * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration]);
  return val;
}

// ─── i18n CONTENT MAP ────────────────────────────────────────────────────────

type Bilingual = { en: string; tr: string };

interface GaugeI18n {
  label: Bilingual;
  subtitle: Bilingual;
  title: Bilingual;
  summary: Bilingual;
  thresholds: { range: string; label: Bilingual; effect: Bilingual }[];
}

const STATIC_TEXT: Record<string, GaugeI18n> = {
  dxy: {
    label:   { en: "DXY Pulse",        tr: "DXY Nabzı" },
    subtitle:{ en: "USD Strength",     tr: "Dolar Gücü" },
    title:   { en: "USD Dollar Index (DXY)", tr: "ABD Dolar Endeksi (DXY)" },
    summary: {
      en: "Dollar strength versus a basket of major currencies — Forex regime filter #1. Inverse to gold, oil and EUR/USD.",
      tr: "ABD dolarının başlıca para birimlerine karşı gücü — Forex'te 1 numaralı rejim filtresi. Altın, petrol ve EUR/USD ile ters hareket eder.",
    },
    thresholds: [
      { range: "z < -1σ", label: { en: "USD WEAK",   tr: "DOLAR ZAYIF" },   effect: { en: "Risk-on; XAU & EUR long bias",        tr: "Risk-on; XAU ve EUR long eğilimli" } },
      { range: "|z| < 1σ", label: { en: "NEUTRAL",   tr: "NÖTR" },          effect: { en: "No macro USD bias",                    tr: "Belirgin makro USD yönü yok" } },
      { range: "z > +1σ", label: { en: "USD STRONG", tr: "DOLAR GÜÇLÜ" },   effect: { en: "XAU & EUR short bias; NDX caution",   tr: "XAU & EUR short eğilimli; NDX'te dikkat" } },
    ],
  },
  vix: {
    label:   { en: "VIX Fear Gauge",   tr: "VIX Korku Endeksi" },
    subtitle:{ en: "Volatility Regime",tr: "Volatilite Rejimi" },
    title:   { en: "VIX (CBOE Volatility Index)", tr: "VIX (CBOE Volatilite Endeksi)" },
    summary: {
      en: "30-day implied volatility on S&P 500 — the master risk-on / risk-off switch.",
      tr: "S&P 500 üzerinde 30 günlük örtük volatilite — risk-on / risk-off ana anahtarı.",
    },
    thresholds: [
      { range: "< 15",  label: { en: "CALM",     tr: "SAKİN" },     effect: { en: "Trend long bias on indices",        tr: "Endekslerde trend long eğilimi" } },
      { range: "15-20", label: { en: "NORMAL",   tr: "NORMAL" },    effect: { en: "Standard sizing",                    tr: "Standart pozisyon büyüklüğü" } },
      { range: "20-25", label: { en: "ELEVATED", tr: "YÜKSELMİŞ" }, effect: { en: "Rallies fragile; widen stops",      tr: "Ralliler kırılgan; stop'ları genişlet" } },
      { range: "25-35", label: { en: "WARNING",  tr: "UYARI" },     effect: { en: "De-risk; XAU long bias",            tr: "Risk azalt; XAU long eğilim" } },
      { range: "> 35",  label: { en: "PANIC",    tr: "PANİK" },     effect: { en: "Defensive only; gold/USD bid",       tr: "Sadece defansif; altın/USD talep" } },
    ],
  },
  yield_curve: {
    label:   { en: "Yield Curve",      tr: "Verim Eğrisi" },
    subtitle:{ en: "10Y - 3M Spread",  tr: "10Y - 3A Farkı" },
    title:   { en: "US Yield Curve (10Y - 3M)", tr: "ABD Verim Eğrisi (10Y - 3A)" },
    summary: {
      en: "Treasury term spread. Historically the most reliable recession leading indicator.",
      tr: "ABD hazine vade farkı. Tarihsel olarak en güvenilir resesyon öncü göstergesidir.",
    },
    thresholds: [
      { range: "> +1.5%",       label: { en: "STEEP",       tr: "DİK" },          effect: { en: "Reflation; equities long, USD ↓",   tr: "Reflasyon; hisseler long, USD ↓" } },
      { range: "+0.5% to +1.5%",label: { en: "NORMAL",      tr: "NORMAL" },       effect: { en: "Growth regime; trend strategies",    tr: "Büyüme rejimi; trend stratejileri" } },
      { range: "0% to +0.5%",   label: { en: "FLAT",        tr: "DÜZ" },          effect: { en: "Late cycle; rotate to defensives",   tr: "Geç döngü; defansiflere rotasyon" } },
      { range: "< 0%",          label: { en: "INVERTED",    tr: "TERS" },         effect: { en: "Recession watch; XAU long bias",     tr: "Resesyon izleme; XAU long eğilimi" } },
      { range: "< -0.75%",      label: { en: "DEEP INVERT", tr: "DERİN TERS" },   effect: { en: "High recession probability",         tr: "Yüksek resesyon olasılığı" } },
    ],
  },
  risk_ratio: {
    label:   { en: "Risk-On / Off",    tr: "Risk-On / Off" },
    subtitle:{ en: "SPY / GLD Ratio",  tr: "SPY / GLD Oranı" },
    title:   { en: "Risk-On / Risk-Off Ratio (SPY / GLD)", tr: "Risk-On / Risk-Off Oranı (SPY / GLD)" },
    summary: {
      en: "Equity vs gold relative performance — captures investor risk appetite. Z-score over 90 days.",
      tr: "Hisse vs altın göreli performansı — yatırımcı risk iştahını ölçer. 90 günlük z-skoru.",
    },
    thresholds: [
      { range: "z > +1σ",  label: { en: "RISK-ON",  tr: "RISK-ON" },  effect: { en: "NDX/SPX long, XAU short bias",     tr: "NDX/SPX long, XAU short eğilimli" } },
      { range: "|z| < 1σ", label: { en: "NEUTRAL",  tr: "NÖTR" },     effect: { en: "No dominant regime",                tr: "Baskın rejim yok" } },
      { range: "z < -1σ",  label: { en: "RISK-OFF", tr: "RISK-OFF" }, effect: { en: "XAU/USD long, indices defensive",  tr: "XAU/USD long, endekslerde defansif" } },
    ],
  },
};

const LEVEL_LABELS: Record<string, Bilingual> = {
  // DXY / Risk-Ratio bands
  NEUTRAL:     { en: "NEUTRAL",     tr: "NÖTR" },
  ELEVATED:    { en: "ELEVATED",    tr: "YÜKSELMİŞ" },
  WARNING:     { en: "WARNING",     tr: "UYARI" },
  HIGH:        { en: "HIGH",        tr: "YÜKSEK" },
  EXTREME:     { en: "EXTREME",     tr: "AŞIRI" },
  // VIX
  CALM:        { en: "CALM",        tr: "SAKİN" },
  NORMAL:      { en: "NORMAL",      tr: "NORMAL" },
  PANIC:       { en: "PANIC",       tr: "PANİK" },
  // Yield curve
  STEEP:       { en: "STEEP",       tr: "DİK" },
  FLAT:        { en: "FLAT",        tr: "DÜZ" },
  INVERTED:    { en: "INVERTED",    tr: "TERS" },
  "DEEP INVERT": { en: "DEEP INVERT", tr: "DERİN TERS" },
  // Status
  LOADING:     { en: "LOADING",     tr: "YÜKLENİYOR" },
  OFFLINE:     { en: "OFFLINE",     tr: "ÇEVRİMDIŞI" },
  UNKNOWN:     { en: "UNKNOWN",     tr: "BİLİNMİYOR" },
};

function tx(b: Bilingual | undefined, locale: Locale): string {
  if (!b) return "";
  return locale === "tr" ? b.tr : b.en;
}

function localizeLevel(level: string, locale: Locale): string {
  const b = LEVEL_LABELS[level];
  return b ? tx(b, locale) : level;
}

// ─── Direction-bias sentence builder (locale aware) ──────────────────────────
//
// Returns a single sentence describing how the current gauge state biases the
// market. Uses the active gauge value/z-score so the sentence is data-driven.

function biasSentence(gauge: MacroGauge, locale: Locale): string {
  const z = gauge.z_score;
  const v = gauge.value;
  switch (gauge.key) {
    case "dxy":
      if (z == null) return "";
      if (z > 1.5)  return locale === "tr"
        ? "Dolar güçlü → EUR/USD short, XAU baskı altında, NDX'te repricing riski."
        : "USD strongly bid → EUR/USD short, XAU pressured, NDX growth-stocks under repricing risk.";
      if (z > 0.5)  return locale === "tr"
        ? "Dolar sağlam → altın ve risk paraları için hafif rüzgar."
        : "USD firm → mild headwind for gold and risk currencies.";
      if (z < -1.5) return locale === "tr"
        ? "Dolar belirgin zayıflıyor → XAU, EUR/USD, NDX, EM lehine."
        : "USD weakening sharply → tailwind for XAU, EUR/USD, NDX, EM.";
      if (z < -0.5) return locale === "tr"
        ? "Dolar zayıf → risk varlıkları ve emtialar için ılımlı destek."
        : "USD soft → modest support for risk and commodities.";
      return locale === "tr"
        ? "Dolar 90 günlük ortalamasına yakın → makro USD yönü yok."
        : "USD near 90-day mean → low macro USD bias.";

    case "vix":
      if (v == null) return "";
      if (v < 15) return locale === "tr"
        ? "Sakin tape — trend stratejileri lehine, stop'lar dar tutulabilir."
        : "Calm tape — trend strategies favored; stops can be tight.";
      if (v < 20) return locale === "tr"
        ? "Normal rejim — standart pozisyon büyüklüğü; mean-reversion çalışıyor."
        : "Normal regime — standard sizing; mean-reversion edges work.";
      if (v < 25) return locale === "tr"
        ? "Yükselmiş — ralliler kırılgan, stop'ları genişlet, XAU'a talep artıyor."
        : "Elevated — rallies fragile; widen stops; XAU bid increasing.";
      if (v < 35) return locale === "tr"
        ? "Uyarı — risk-off muhtemel, kaldıracı azalt, XAU/USD long eğilimi."
        : "Warning — risk-off probable; reduce leverage; XAU/USD long bias.";
      if (v < 45) return locale === "tr"
        ? "Yüksek stres — defansif kal, endeksler short eğilimli, altın güvenli liman talebi."
        : "High stress — defensive only; indices short bias; gold flight-to-quality.";
      return locale === "tr"
        ? "PANİK — tam risk-off; short kapanışları sert olabilir, USD funding sıkışması bekle."
        : "PANIC — full risk-off; short covers may be sharp; expect USD funding squeeze.";

    case "yield_curve": {
      const sp = gauge.spread ?? v;
      if (sp == null) return "";
      if (sp < -0.75) return locale === "tr"
        ? "Derin tersine dönüş — resesyon riski ekstrem, XAU long eğilim, USD nihayetinde tepe yapar."
        : "Deep inversion — recession risk extreme; XAU long bias; USD eventually peaks.";
      if (sp < -0.10) return locale === "tr"
        ? "Eğri ters — resesyon izleme aktif. XAU bid, defansifler tercih, petrol talebi riskte."
        : "Curve inverted — recession watch active; XAU bid; defensives over cyclicals; oil demand at risk.";
      if (sp < 0.50)  return locale === "tr"
        ? "Eğri düz — geç döngü. Rotasyonları dikkatli yap, büyüme yavaşlaması fiyatlanıyor."
        : "Curve flat — late cycle; trade rotations carefully; growth slowdown priced in.";
      if (sp < 1.50)  return locale === "tr"
        ? "Sağlıklı pozitif eğim — büyüme rejimi, endeksler long eğilimli, XAU range."
        : "Healthy positive slope — growth regime; indices trend long bias; XAU range-trade.";
      return locale === "tr"
        ? "Dik eğri — erken döngü / reflasyon, hisseler long eğilimli, USD zayıflıyor, emtialar arkadan rüzgar."
        : "Steep curve — early-cycle / reflation; equities long bias; USD weakening; commodities tailwind.";
    }

    case "risk_ratio":
      if (z == null) return "";
      if (z > 1.5)  return locale === "tr"
        ? "Agresif risk-on — hisseler altını belirgin geçiyor, NDX/SPX trend long, XAU baskı."
        : "Aggressive risk-on — equities outperform gold strongly; NDX/SPX trend-long; XAU pressured.";
      if (z > 0.5)  return locale === "tr"
        ? "Risk-on eğilim — hisse yukarı, altın geride."
        : "Risk-on tilt — equity upside; gold underperforms.";
      if (z < -1.5) return locale === "tr"
        ? "Agresif risk-off — altın hisseleri geçiyor, defansif akış, NDX short eğilimi."
        : "Aggressive risk-off — gold outperforms equities; defensive flow; NDX short bias.";
      if (z < -0.5) return locale === "tr"
        ? "Risk-off eğilim — altın/tahvil bid, hisse rallileri kırılgan."
        : "Risk-off tilt — gold/treasuries bid; equity rallies fragile.";
      return locale === "tr"
        ? "Nötr — baskın risk rejimi yok, sembol bazlı sinyallere göre işlem yap."
        : "Neutral — no dominant risk regime; trade by symbol-specific signals.";
  }
  return "";
}

// ─── Single gauge card ───────────────────────────────────────────────────────

const BAND_COLORS = ["#16a34a", "#84cc16", "#eab308", "#f59e0b", "#ea580c", "#dc2626"];

function GaugeCard({ gauge }: { gauge: MacroGauge }) {
  const locale = useI18nStore((s) => s.locale);
  const cardRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState(false);
  const score = gauge.score ?? 50;
  const animatedScore = useAnimatedNumber(score, 1100);
  const needleDeg = useMemo(() => angleFromScore(animatedScore), [animatedScore]);
  const isLoading = gauge.status === "loading";
  const isError = gauge.status === "error";

  const i18n = STATIC_TEXT[gauge.key];
  const labelText = i18n ? tx(i18n.label, locale) : gauge.label;
  const display = isLoading || isError
    ? "…"
    : gauge.value !== null && gauge.value !== undefined
    ? formatValue(gauge)
    : "—";
  const levelText = isLoading ? localizeLevel("LOADING", locale)
    : isError ? localizeLevel("OFFLINE", locale)
    : localizeLevel(gauge.level, locale);

  return (
    <>
      <div
        ref={cardRef}
        className="relative inline-flex"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        onFocus={() => setHover(true)}
        onBlur={() => setHover(false)}
        tabIndex={0}
      >
        <div
          className={`
            inline-flex items-center gap-2 px-3 py-2 rounded-2xl
            bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950
            border transition-all duration-500 cursor-help
            ${isError ? "border-gray-700/50" :
              isLoading ? "border-gray-700/40" :
              "border-white/10 hover:border-white/30"}
          `}
          style={{
            boxShadow: !isLoading && !isError ? `0 0 14px ${gauge.color}22` : undefined,
          }}
        >
          {/* Mini dome dial */}
          <div className="relative shrink-0" style={{ width: 90, height: 60 }}>
            <svg viewBox="0 0 200 130" className="w-full h-full overflow-visible">
              <path d={arcPath(R, -HALF_SWEEP, HALF_SWEEP)} stroke="rgba(255,255,255,0.06)" strokeWidth="14" fill="none" />
              {BAND_COLORS.slice(0, 5).map((c, i) => {
                const start = -HALF_SWEEP + (i / 5) * SWEEP;
                const end = -HALF_SWEEP + ((i + 1) / 5) * SWEEP;
                return (
                  <path key={i} d={arcPath(R, start, end)} stroke={c} strokeWidth="10" fill="none"
                        opacity={isLoading || isError ? 0.18 : 0.78} />
                );
              })}
              {[0, 25, 50, 75, 100].map((t) => {
                const deg = -HALF_SWEEP + (t / 100) * SWEEP;
                const o = pointAt(R + 6, deg);
                const i = pointAt(R - 4, deg);
                return <line key={t} x1={i.x} y1={i.y} x2={o.x} y2={o.y} stroke="rgba(255,255,255,0.4)" strokeWidth="1.4" />;
              })}
              <g
                style={{
                  transform: `rotate(${isLoading || isError ? -HALF_SWEEP : needleDeg}deg)`,
                  transformOrigin: `${CX}px ${CY}px`,
                  transition: "transform 1.1s cubic-bezier(.2,.8,.2,1)",
                  opacity: isLoading || isError ? 0.4 : 1,
                }}
              >
                <polygon
                  points={`${CX - 2.5},${CY + 6} ${CX + 2.5},${CY + 6} ${CX + 0.7},${CY - R + 8} ${CX - 0.7},${CY - R + 8}`}
                  fill={isLoading || isError ? "#6b7280" : gauge.color}
                  style={{ filter: !isLoading && !isError ? `drop-shadow(0 0 3px ${gauge.color})` : undefined }}
                />
                <circle cx={CX} cy={CY - R + 8} r="1.8" fill="#fff" opacity="0.85" />
              </g>
              <circle cx={CX} cy={CY} r="7" fill="#0a0a0a" stroke={isLoading || isError ? "#374151" : gauge.color} strokeWidth="2" />
              <circle cx={CX} cy={CY} r="2.5" fill={isLoading || isError ? "#374151" : gauge.color} />
            </svg>
          </div>

          {/* Right text */}
          <div className="min-w-0">
            <div className="text-[8px] font-bold uppercase tracking-[0.16em] text-gray-400 leading-tight">
              {labelText}
            </div>
            <div className="text-[15px] font-extrabold tabular-nums leading-tight" style={{ color: isLoading || isError ? "#9ca3af" : gauge.color }}>
              {display}
            </div>
            <div className="text-[9px] text-gray-500 leading-tight uppercase tracking-wider">
              {levelText}
            </div>
          </div>
        </div>
      </div>

      {hover && !isLoading && cardRef.current && (
        <PortalTooltip anchor={cardRef.current} gauge={gauge} locale={locale} />
      )}
    </>
  );
}

// ─── Portal tooltip ──────────────────────────────────────────────────────────

interface PortalTooltipProps {
  anchor: HTMLElement;
  gauge: MacroGauge;
  locale: Locale;
}

function PortalTooltip({ anchor, gauge, locale }: PortalTooltipProps) {
  const tipRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number; placement: "top" | "bottom" }>({ top: 0, left: 0, placement: "top" });
  const [mounted, setMounted] = useState(false);

  useLayoutEffect(() => { setMounted(true); }, []);

  useLayoutEffect(() => {
    if (!tipRef.current) return;
    const ar = anchor.getBoundingClientRect();
    const tip = tipRef.current.getBoundingClientRect();
    const margin = 10;
    let placement: "top" | "bottom" = "top";
    let top = ar.top - tip.height - margin;
    if (top < 8) {
      placement = "bottom";
      top = ar.bottom + margin;
    }
    let left = ar.left + ar.width / 2 - tip.width / 2;
    left = Math.max(8, Math.min(window.innerWidth - tip.width - 8, left));
    setPos({ top, left, placement });
  }, [anchor, gauge, mounted, locale]);

  if (typeof window === "undefined") return null;

  const i18n = STATIC_TEXT[gauge.key];
  const title = i18n ? tx(i18n.title, locale) : gauge.tooltip?.title ?? "";
  const summary = i18n ? tx(i18n.summary, locale) : gauge.tooltip?.summary ?? "";
  const interpretation = biasSentence(gauge, locale) || gauge.tooltip?.interpretation || "";
  const thresholds = i18n ? i18n.thresholds : (gauge.tooltip?.thresholds ?? []).map((t) => ({
    range: t.range, label: { en: t.label, tr: t.label }, effect: { en: t.effect, tr: t.effect },
  }));

  const valueLabel = locale === "tr" ? "Değer" : "Value";
  const zLabel     = locale === "tr" ? "Z-Skoru" : "Z-Score";
  const biasHeader = locale === "tr" ? "Yön etkisi" : "Direction bias";
  const tableHead  = locale === "tr" ? "Eşik haritası" : "Threshold map";

  return createPortal(
    <div
      ref={tipRef}
      className="fixed z-[9999] pointer-events-none"
      style={{
        top: pos.top,
        left: pos.left,
        width: 360,
        opacity: mounted ? 1 : 0,
        transition: "opacity 120ms ease-out",
      }}
      role="tooltip"
    >
      <div
        className="rounded-xl border bg-gray-950/95 backdrop-blur-md p-4 shadow-2xl"
        style={{
          borderColor: `${gauge.color}55`,
          boxShadow: `0 12px 40px rgba(0,0,0,0.55), 0 0 22px ${gauge.color}33`,
          fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
        }}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="text-[13.5px] font-bold text-white leading-snug tracking-tight">
            {title}
          </div>
          <span
            className="shrink-0 text-[10px] font-extrabold px-2 py-0.5 rounded-md uppercase tracking-wider"
            style={{ background: `${gauge.color}1f`, color: gauge.color, border: `1px solid ${gauge.color}55` }}
          >
            {localizeLevel(gauge.level, locale)}
          </span>
        </div>

        {/* Summary */}
        <div className="text-[11.5px] text-gray-300 leading-relaxed mb-3">
          {summary}
        </div>

        {/* Value chips */}
        {(gauge.value != null || (gauge.z_score != null && gauge.z_score !== undefined)) && (
          <div className="flex gap-2 mb-3">
            {gauge.value != null && (
              <div className="flex-1 rounded-lg bg-white/5 border border-white/5 px-2.5 py-1.5">
                <div className="text-[9px] uppercase tracking-wider text-gray-500 font-bold">{valueLabel}</div>
                <div className="text-[14px] font-bold text-white tabular-nums leading-none mt-0.5">{formatValue(gauge)}</div>
              </div>
            )}
            {gauge.z_score != null && (
              <div className="flex-1 rounded-lg bg-white/5 border border-white/5 px-2.5 py-1.5">
                <div className="text-[9px] uppercase tracking-wider text-gray-500 font-bold">{zLabel}</div>
                <div className="text-[14px] font-bold text-white tabular-nums leading-none mt-0.5">
                  {gauge.z_score > 0 ? "+" : ""}{gauge.z_score.toFixed(2)}σ
                </div>
              </div>
            )}
          </div>
        )}

        {/* Direction bias */}
        {interpretation && (
          <div
            className="rounded-lg px-3 py-2 mb-3 border-l-2"
            style={{ borderColor: gauge.color, background: `${gauge.color}10` }}
          >
            <div
              className="text-[9.5px] font-extrabold uppercase tracking-[0.14em] mb-1"
              style={{ color: gauge.color }}
            >
              {biasHeader}
            </div>
            <div className="text-[12px] leading-snug text-gray-100">
              {interpretation}
            </div>
          </div>
        )}

        {/* Thresholds */}
        {thresholds.length > 0 && (
          <div>
            <div className="text-[9.5px] uppercase tracking-[0.14em] text-gray-500 mb-1.5 font-extrabold">
              {tableHead}
            </div>
            <div className="rounded-md overflow-hidden border border-white/5">
              {thresholds.map((t, i) => (
                <div
                  key={i}
                  className="flex items-baseline gap-2 px-2 py-1.5 text-[10.5px] leading-snug"
                  style={{ background: i % 2 === 0 ? "rgba(255,255,255,0.025)" : "transparent" }}
                >
                  <span className="text-gray-500 tabular-nums shrink-0 font-mono w-[88px]">{t.range}</span>
                  <span className="font-bold text-gray-200 shrink-0 w-[88px]">{tx(t.label, locale)}</span>
                  <span className="text-gray-400">{tx(t.effect, locale)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tail */}
      <div
        className="absolute"
        style={{
          left: "50%",
          [pos.placement === "top" ? "bottom" : "top"]: -6,
          transform: pos.placement === "top"
            ? "translateX(-50%) rotate(45deg)"
            : "translateX(-50%) rotate(225deg)",
          width: 12,
          height: 12,
          background: "rgb(3 7 18 / 0.95)",
          borderRight: `1px solid ${gauge.color}55`,
          borderBottom: `1px solid ${gauge.color}55`,
        }}
      />
    </div>,
    document.body,
  );
}

// ─── Strip ───────────────────────────────────────────────────────────────────

export default function MacroGaugeStrip() {
  const [gauges, setGauges] = useState<MacroGauge[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const load = async (attempt = 0): Promise<void> => {
      try {
        const res = await fetcher<MacroResponse>("/api/macro-gauges");
        if (cancelled) return;
        if (res.success && Array.isArray(res.gauges)) {
          setGauges(res.gauges);
          timer = setTimeout(() => load(0), 5 * 60_000);
        } else {
          throw new Error("bad payload");
        }
      } catch {
        if (cancelled) return;
        if (attempt < 3) {
          const delays = [2_000, 5_000, 10_000];
          timer = setTimeout(() => load(attempt + 1), delays[attempt]);
        } else {
          setGauges([
            placeholder("dxy"), placeholder("vix"),
            placeholder("yield_curve"), placeholder("risk_ratio"),
          ]);
          timer = setTimeout(() => load(0), 60_000);
        }
      }
    };
    load(0);
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, []);

  const list: MacroGauge[] = gauges ?? [
    loadingPlaceholder("dxy"), loadingPlaceholder("vix"),
    loadingPlaceholder("yield_curve"), loadingPlaceholder("risk_ratio"),
  ];

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
      {list.map((g) => <GaugeCard key={g.key} gauge={g} />)}
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatValue(g: MacroGauge): string {
  if (g.value === null || g.value === undefined) return "—";
  if (g.key === "vix") return g.value.toFixed(1);
  if (g.key === "dxy") return g.value.toFixed(2);
  if (g.key === "yield_curve") return `${g.value > 0 ? "+" : ""}${g.value.toFixed(2)}%`;
  if (g.key === "risk_ratio") return g.value.toFixed(2);
  return String(g.value);
}

function loadingPlaceholder(key: string): MacroGauge {
  return {
    key, label: STATIC_TEXT[key]?.label.en ?? key,
    status: "loading", value: null, score: 50,
    level: "LOADING", color: "#6b7280",
    tooltip: { title: "", summary: "", interpretation: "", thresholds: [] },
  };
}

function placeholder(key: string): MacroGauge {
  return {
    key, label: STATIC_TEXT[key]?.label.en ?? key,
    status: "error", value: null, score: 50,
    level: "OFFLINE", color: "#6b7280",
    tooltip: { title: "", summary: "", interpretation: "", thresholds: [] },
  };
}
