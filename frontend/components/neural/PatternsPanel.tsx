"use client";

/**
 * PatternsPanel — "Tespit Edilen Formasyonlar" list + detail modal.
 * Each detected pattern row opens a chart: pivot points (X-A-B-C-D)
 * are marked on the candles, legs draw themselves in, fib ratios label
 * the legs, and a comet repeatedly glides from C toward the PROJECTED
 * D completion zone (PRZ) which pulses with target rings + price tag.
 */

import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Shapes, X } from "lucide-react";
import { useNeuralLocale, type LFn } from "./i18n";
import type { LivePatternRaw, LiveCandle } from "@/lib/api/neural";

// ── Types & demo data ──────────────────────────────────────────────────────

interface PivotPt { i: number; p: number; tag: string }
export interface DetectedPattern {
  id: string;
  name: (L: LFn) => string;
  tf: string;
  dirUp: boolean;
  completion: number; // 0-100
  status: (L: LFn) => string;
  targetPrice: string;
  targetNote: (L: LFn) => string;
  pivots: PivotPt[]; // indices into its candle series
  projected: { i: number; p: number }; // expected D completion
  przLow: number;
  przHigh: number;
  ratios: { legFrom: number; legTo: number; label: string }[]; // pivot idx refs
  candles: { o: number; h: number; l: number; c: number }[];
  /** kesin bozulma fiyatı — fiyat bu seviyeyi yön aleyhine geçerse formasyon geçersiz */
  invalidation?: number;
  /** fiyat bozulma sınırını zaten geçti mi */
  broken?: boolean;
  /** serinin son kapanışı (şimdiki fiyat çizgisi için) */
  lastPrice?: number;
}

function genCandles(seedPath: number[], jitter = 8): { o: number; h: number; l: number; c: number }[] {
  const out: { o: number; h: number; l: number; c: number }[] = [];
  for (let i = 0; i < seedPath.length - 1; i++) {
    const o = seedPath[i];
    const c = seedPath[i + 1];
    const wob = Math.abs(Math.sin(i * 2.3)) * jitter;
    out.push({ o, c, h: Math.max(o, c) + wob, l: Math.min(o, c) - wob });
  }
  return out;
}

/** Smooth-ish path through anchor points, `steps` candles per leg. */
function pathThrough(anchors: number[], steps: number): number[] {
  const pts: number[] = [];
  for (let a = 0; a < anchors.length - 1; a++) {
    for (let s = 0; s < steps; s++) {
      const t = s / steps;
      const eased = t * t * (3 - 2 * t);
      pts.push(anchors[a] + (anchors[a + 1] - anchors[a]) * eased + Math.sin((a * steps + s) * 1.9) * 6);
    }
  }
  pts.push(anchors[anchors.length - 1]);
  return pts;
}

function buildPatterns(): DetectedPattern[] {
  // Bullish Gartley — X(21990) A(21400) B(21765) C(21510) → D projected 21860?
  // classic bullish gartley: X high? Use standard: X low→A high... keep visual truth: legs zigzag, D below C for bullish PRZ.
  const gartleyAnchors = [21480, 22050, 21700, 21930, 21620];
  const gartleyCandles = genCandles(pathThrough(gartleyAnchors, 7), 9);
  const gStep = 7;
  const gartley: DetectedPattern = {
    id: "gartley",
    name: (L) => L("Boğa Gartley", "Bullish Gartley"),
    tf: "4H",
    dirUp: true,
    completion: 86,
    status: (L) => L("D AYAĞI BEKLENİYOR", "AWAITING D LEG"),
    targetPrice: "21,590",
    targetNote: (L) =>
      L("Tahmini tamamlanma: 21.560–21.620 PRZ bölgesi (~9 mum içinde) — dönüş alım bölgesi.", "Expected completion: 21,560–21,620 PRZ (~9 candles) — reversal buy zone."),
    pivots: [
      { i: 0, p: gartleyAnchors[0], tag: "X" },
      { i: gStep, p: gartleyAnchors[1], tag: "A" },
      { i: gStep * 2, p: gartleyAnchors[2], tag: "B" },
      { i: gStep * 3, p: gartleyAnchors[3], tag: "C" },
    ],
    projected: { i: gStep * 4 + 5, p: 21590 },
    przLow: 21560,
    przHigh: 21620,
    ratios: [
      { legFrom: 1, legTo: 2, label: "AB = 0.618·XA" },
      { legFrom: 2, legTo: 3, label: "BC = 0.382·AB" },
      { legFrom: 3, legTo: 4, label: "CD ≈ 1.272·BC" },
    ],
    candles: gartleyCandles,
    invalidation: 21470,
    lastPrice: gartleyCandles[gartleyCandles.length - 1]?.c,
  };

  // Ascending Triangle — flat top ~22040, rising lows; breakout target above
  const triAnchors = [21600, 22030, 21740, 22040, 21850, 22035, 21930];
  const triCandles = genCandles(pathThrough(triAnchors, 5), 7);
  const triangle: DetectedPattern = {
    id: "triangle",
    name: (L) => L("Yükselen Üçgen", "Ascending Triangle"),
    tf: "1H",
    dirUp: true,
    completion: 72,
    status: (L) => L("KIRILIM İZLENİYOR", "WATCHING BREAKOUT"),
    targetPrice: "22,480",
    targetNote: (L) =>
      L("22.040 direnci kırılırsa ölçülü hedef 22.480 (üçgen yüksekliği kadar).", "If 22,040 breaks, measured target is 22,480 (triangle height projected)."),
    pivots: [
      { i: 5, p: 22030, tag: "R1" },
      { i: 10, p: 21740, tag: "L1" },
      { i: 15, p: 22040, tag: "R2" },
      { i: 20, p: 21850, tag: "L2" },
      { i: 25, p: 22035, tag: "R3" },
    ],
    projected: { i: 34, p: 22480 },
    przLow: 22440,
    przHigh: 22520,
    ratios: [{ legFrom: 0, legTo: 4, label: "" }],
    candles: triCandles,
    invalidation: 21720,
    lastPrice: triCandles[triCandles.length - 1]?.c,
  };

  // Completed bearish ABCD on 15m
  const abcdAnchors = [22100, 21880, 21990, 21700];
  const abcdCandles = genCandles(pathThrough(abcdAnchors, 8), 6);
  const abcd: DetectedPattern = {
    id: "abcd",
    name: (L) => L("Ayı ABCD (tamamlandı)", "Bearish ABCD (completed)"),
    tf: "15m",
    dirUp: false,
    completion: 100,
    status: (L) => L("GERÇEKLEŞTİ ✓", "PLAYED OUT ✓"),
    targetPrice: "21,700",
    targetNote: (L) =>
      L("D noktası 21.700'de tamamlandı, hedefe ulaştı — arşiv kaydı.", "D completed at 21,700 and hit target — archived record."),
    pivots: [
      { i: 0, p: abcdAnchors[0], tag: "A" },
      { i: 8, p: abcdAnchors[1], tag: "B" },
      { i: 16, p: abcdAnchors[2], tag: "C" },
      { i: 24, p: abcdAnchors[3], tag: "D" },
    ],
    projected: { i: 24, p: 21700 },
    przLow: 21680,
    przHigh: 21730,
    ratios: [
      { legFrom: 0, legTo: 1, label: "AB" },
      { legFrom: 2, legTo: 3, label: "CD = 1.0·AB" },
    ],
    candles: abcdCandles,
    invalidation: 22015,
    lastPrice: abcdCandles[abcdCandles.length - 1]?.c,
  };

  return [gartley, triangle, abcd];
}

// ── Live pattern mapper (backend /api/patterns → DetectedPattern) ──────────

const fmtP = (p: number) =>
  p >= 1000 ? p.toLocaleString("en-US", { maximumFractionDigits: 0 }) : p.toFixed(2);

/** Pick the most interesting patterns: forming harmonics first, then top completed. */
export function mapLivePatterns(raws: LivePatternRaw[], candles: LiveCandle[]): DetectedPattern[] {
  if (!raws.length || candles.length < 20) return [];

  const seen = new Set<string>();
  const pick: LivePatternRaw[] = [];
  const forming = raws
    .filter((p) => p.status === "FORMING" && p.projected)
    .sort((a, b) => b.confidence - a.confidence);
  const completed = raws
    .filter((p) => p.status === "COMPLETED")
    .sort((a, b) => b.confidence - a.confidence);
  for (const p of [...forming, ...completed]) {
    if (pick.length >= 4) break;
    if (seen.has(p.name)) continue;
    seen.add(p.name);
    pick.push(p);
  }

  // Pivotları mumlara ZAMAN ile eşle (backend'in candle dizisi ile buradaki
  // /api/data/ohlcv dizisi ayrı isteklerdir; ham index 1-2 bar kayabilir).
  const tsToIdx = new Map<number, number>();
  candles.forEach((c, i) => tsToIdx.set(Math.round(c.ts / 1000), i));
  const alignIdx = (v: { index: number; time?: number }): number => {
    const t = Number(v.time ?? 0);
    if (t > 0 && tsToIdx.has(t)) return tsToIdx.get(t)!;
    return v.index;
  };
  const lastPrice = candles[candles.length - 1].c;

  return pick.map((p, pi): DetectedPattern => {
    const entries = Object.entries(p.points)
      .filter(([, v]) => Number.isFinite(v.index) && v.price > 0)
      .map(([k, v]) => [k, { ...v, index: alignIdx(v) }] as [string, { index: number; price: number; time?: number }]);
    const isForming = p.status === "FORMING";
    const pivotEntries = isForming ? entries.filter(([k]) => k !== "D") : entries;
    const idxs = entries.map(([, v]) => v.index);

    // projected index: for forming use D point's index (synthetic), else last pivot
    const dPoint = entries.find(([k]) => k === "D")?.[1];
    const projIdxRaw = dPoint ? dPoint.index : Math.max(...idxs);
    const projPrice = p.projected?.price ?? dPoint?.price ?? p.targetPrice ?? 0;

    const start = Math.max(0, Math.min(...idxs) - 3);
    const endData = Math.min(candles.length - 1, Math.max(...idxs) + 3);
    const slice = candles.slice(start, endData + 1).map(({ o, h, l, c }) => ({ o, h, l, c }));

    const pivots = pivotEntries
      .sort((a, b) => a[1].index - b[1].index)
      .map(([tag, v]) => ({ i: v.index - start, p: v.price, tag }));

    const projectedI = Math.max(projIdxRaw - start, (pivots[pivots.length - 1]?.i ?? 0) + 4);

    const ratios: DetectedPattern["ratios"] = [];
    if (p.ratios) {
      const r = p.ratios;
      if (r.ab) ratios.push({ legFrom: 1, legTo: 2, label: `AB=${r.ab.toFixed(2)}·XA` });
      if (r.bc) ratios.push({ legFrom: 2, legTo: 3, label: `BC=${r.bc.toFixed(2)}·AB` });
      const cd = r.cd || r.xd;
      if (cd) ratios.push({ legFrom: 3, legTo: 4, label: `CD≈${cd.toFixed(2)}·BC` });
    }

    const target = fmtP(projPrice);
    const barsAway = Math.max(0, projIdxRaw - endData);

    const invalidation = Number.isFinite(Number(p.invalidation)) ? Number(p.invalidation) : undefined;
    const broken =
      p.invalidated === true ||
      (invalidation !== undefined &&
        (p.signal === "bullish" ? lastPrice < invalidation : lastPrice > invalidation));

    return {
      id: `${p.name}-${pi}`,
      name: (L) => L(p.nameTr, p.name),
      tf: p.timeframe,
      dirUp: p.signal === "bullish",
      completion: isForming ? Math.min(95, Math.max(50, p.confidence)) : 100,
      status: (L) =>
        broken
          ? L("BOZULDU ✗", "PATTERN BROKE ✗")
          : isForming
          ? L("D AYAĞI BEKLENİYOR", "AWAITING D LEG")
          : L("TAMAMLANDI ✓", "COMPLETED ✓"),
      targetPrice: target,
      targetNote: (L) =>
        isForming
          ? L(
              `Tahmini tamamlanma: ${target} bölgesi${barsAway ? ` (~${barsAway} mum içinde)` : ""} — motor güveni %${p.confidence}.`,
              `Expected completion: ${target} zone${barsAway ? ` (~${barsAway} candles)` : ""} — engine confidence ${p.confidence}%.`
            )
          : L(
              `Formasyon tamamlandı. Hedef: ${p.targetPrice ? fmtP(p.targetPrice) : target}${p.stopLoss ? ` · Stop: ${fmtP(p.stopLoss)}` : ""}.`,
              `Pattern completed. Target: ${p.targetPrice ? fmtP(p.targetPrice) : target}${p.stopLoss ? ` · Stop: ${fmtP(p.stopLoss)}` : ""}.`
            ),
      pivots,
      projected: { i: projectedI, p: projPrice },
      przLow: projPrice * 0.9965,
      przHigh: projPrice * 1.0035,
      ratios,
      candles: slice,
      invalidation,
      broken,
      lastPrice,
    };
  });
}

// ── Pattern chart (inside modal) ───────────────────────────────────────────

function PatternChart({ pat }: { pat: DetectedPattern }) {
  const { L } = useNeuralLocale();
  const W = 860, H = 380, PAD = 16, PAD_R = 104;
  const total = Math.max(pat.projected.i + 4, pat.candles.length + 2);

  let lo = Math.min(...pat.candles.map((c) => c.l), pat.przLow);
  let hi = Math.max(...pat.candles.map((c) => c.h), pat.przHigh);
  // bozulma çizgisi görünür kalsın; ama aralığı en fazla %35 genişletsin
  if (Number.isFinite(pat.invalidation)) {
    const range = hi - lo || 1;
    const inv = pat.invalidation!;
    if (inv < lo) lo = Math.max(inv, lo - range * 0.35);
    if (inv > hi) hi = Math.min(inv, hi + range * 0.35);
  }
  const vpad = (hi - lo) * 0.08;
  lo -= vpad; hi += vpad;

  const toY = (p: number) => PAD + (1 - (p - lo) / (hi - lo)) * (H - PAD * 2);
  const toX = (i: number) => PAD + (i / total) * (W - PAD - PAD_R);

  const lastPivot = pat.pivots[pat.pivots.length - 1];
  const isProjection = pat.completion < 100;
  const invY = Number.isFinite(pat.invalidation) ? toY(pat.invalidation!) : null;
  const nowY =
    Number.isFinite(pat.lastPrice) && pat.lastPrice! > lo && pat.lastPrice! < hi
      ? toY(pat.lastPrice!)
      : null;

  // pivot polyline
  const pivotPath = pat.pivots.map((pv, i) => `${i === 0 ? "M" : "L"} ${toX(pv.i)} ${toY(pv.p)}`).join(" ");
  const projPath = `M ${toX(lastPivot.i)} ${toY(lastPivot.p)} L ${toX(pat.projected.i)} ${toY(pat.projected.p)}`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label={pat.name(L)}>
      {/* candles */}
      {pat.candles.map((c, i) => {
        const x = toX(i);
        const up = c.c >= c.o;
        const col = up ? "#34d399" : "#f87171";
        const cw = (W - PAD - PAD_R) / total;
        return (
          <motion.g key={i} initial={{ opacity: 0 }} animate={{ opacity: 0.65 }} transition={{ delay: Math.min(i * 0.015, 0.5) }}>
            <line x1={x} x2={x} y1={toY(c.h)} y2={toY(c.l)} stroke={col} strokeOpacity="0.5" strokeWidth="1" />
            <rect x={x - cw * 0.26} y={toY(Math.max(c.o, c.c))} width={cw * 0.52} height={Math.max(1, Math.abs(toY(c.o) - toY(c.c)))} fill={col} fillOpacity="0.6" rx="0.5" />
          </motion.g>
        );
      })}

      {/* PRZ zone */}
      <motion.rect
        x={toX(pat.projected.i) - 34}
        y={toY(pat.przHigh)}
        width={68}
        height={toY(pat.przLow) - toY(pat.przHigh)}
        rx="4"
        fill={pat.dirUp ? "rgba(52,211,153,0.12)" : "rgba(248,113,113,0.12)"}
        stroke={pat.dirUp ? "#34d399" : "#f87171"}
        strokeOpacity="0.45"
        strokeDasharray="4 3"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 1.2, duration: 0.5 }}
      />

      {/* pivot legs */}
      <motion.path
        d={pivotPath}
        fill="none"
        stroke="#22d3ee"
        strokeWidth="1.8"
        strokeLinejoin="round"
        style={{ filter: "drop-shadow(0 0 5px rgba(34,211,238,0.7))" }}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1, ease: "easeInOut", delay: 0.3 }}
      />

      {/* projected leg */}
      <motion.path
        d={projPath}
        fill="none"
        stroke={pat.dirUp ? "#34d399" : "#f87171"}
        strokeWidth="1.6"
        strokeDasharray="6 5"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: isProjection ? 0.9 : 0.5 }}
        transition={{ delay: 1.1, duration: 0.8 }}
      />

      {/* comet gliding toward D (only for forming patterns) */}
      {isProjection && (
        <>
          <motion.circle
            r="4"
            fill="#fff"
            style={{ filter: `drop-shadow(0 0 8px ${pat.dirUp ? "#34d399" : "#f87171"})` }}
            initial={{ cx: toX(lastPivot.i), cy: toY(lastPivot.p), opacity: 0 }}
            animate={{
              cx: [toX(lastPivot.i), toX(pat.projected.i)],
              cy: [toY(lastPivot.p), toY(pat.projected.p)],
              opacity: [0, 1, 1, 0.2],
            }}
            transition={{ repeat: Infinity, duration: 2.2, delay: 1.6, repeatDelay: 0.8, ease: "easeInOut" }}
          />
          {/* comet tail */}
          <motion.circle
            r="8"
            fill={pat.dirUp ? "rgba(52,211,153,0.25)" : "rgba(248,113,113,0.25)"}
            initial={{ cx: toX(lastPivot.i), cy: toY(lastPivot.p), opacity: 0 }}
            animate={{
              cx: [toX(lastPivot.i), toX(pat.projected.i)],
              cy: [toY(lastPivot.p), toY(pat.projected.p)],
              opacity: [0, 0.8, 0.8, 0],
            }}
            transition={{ repeat: Infinity, duration: 2.2, delay: 1.55, repeatDelay: 0.8, ease: "easeInOut" }}
          />
        </>
      )}

      {/* D target: pulsing rings + label */}
      <g>
        {isProjection && (
          <>
            <motion.circle
              cx={toX(pat.projected.i)} cy={toY(pat.projected.p)} r="7" fill="none"
              stroke={pat.dirUp ? "#34d399" : "#f87171"} strokeWidth="1.4"
              animate={{ r: [7, 18], opacity: [0.9, 0] }}
              transition={{ repeat: Infinity, duration: 1.8, delay: 1.4 }}
            />
            <motion.circle
              cx={toX(pat.projected.i)} cy={toY(pat.projected.p)} r="7" fill="none"
              stroke={pat.dirUp ? "#34d399" : "#f87171"} strokeWidth="1"
              animate={{ r: [7, 26], opacity: [0.5, 0] }}
              transition={{ repeat: Infinity, duration: 1.8, delay: 2.1 }}
            />
          </>
        )}
        <circle cx={toX(pat.projected.i)} cy={toY(pat.projected.p)} r="4.5" fill={pat.dirUp ? "#34d399" : "#f87171"} style={{ filter: `drop-shadow(0 0 8px ${pat.dirUp ? "#34d399" : "#f87171"})` }} />
        <text x={toX(pat.projected.i) + 12} y={toY(pat.projected.p) - 10} fill={pat.dirUp ? "#6ee7b7" : "#fca5a5"} fontSize="10" fontFamily="monospace" fontWeight="700" letterSpacing="0.08em">
          {isProjection ? "D?" : "D"} {pat.targetPrice}
        </text>
        <text x={toX(pat.projected.i) + 12} y={toY(pat.projected.p) + 4} fill="#64748b" fontSize="8" fontFamily="monospace">
          {isProjection ? L("tahmini bölge", "projected zone") : L("tamamlandı", "completed")}
        </text>
      </g>

      {/* pivot dots + tags */}
      {pat.pivots.map((pv, i) => (
        <motion.g key={pv.tag} initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.35 + i * 0.18, type: "spring", stiffness: 300, damping: 16 }}>
          <circle cx={toX(pv.i)} cy={toY(pv.p)} r="4" fill="#0a0f1c" stroke="#22d3ee" strokeWidth="1.6" />
          <text x={toX(pv.i)} y={toY(pv.p) - 9} textAnchor="middle" fill="#67e8f9" fontSize="11" fontFamily="monospace" fontWeight="700">
            {pv.tag}
          </text>
        </motion.g>
      ))}

      {/* current price line (subtle) */}
      {nowY !== null && (
        <g>
          <line x1={PAD} x2={W - PAD_R + 62} y1={nowY} y2={nowY} stroke="#67e8f9" strokeOpacity="0.35" strokeWidth="1" strokeDasharray="2 4" />
          <text x={W - PAD_R + 66} y={nowY + 3} fill="#67e8f9" fillOpacity="0.75" fontSize="8" fontFamily="monospace" letterSpacing="0.1em">
            {L("ŞİMDİ", "NOW")} {fmtP(pat.lastPrice!)}
          </text>
        </g>
      )}

      {/* PATTERN BROKE — kırmızı lazer bozulma çizgisi */}
      {invY !== null && (
        <g>
          {/* laser glow underlay */}
          <motion.line
            x1={PAD} x2={W - PAD_R + 62} y1={invY} y2={invY}
            stroke="#ef4444" strokeWidth="6" strokeLinecap="round"
            initial={{ opacity: 0 }}
            animate={{ opacity: pat.broken ? [0.22, 0.4, 0.22] : [0.1, 0.26, 0.1] }}
            transition={{ repeat: Infinity, duration: 1.6, ease: "easeInOut" }}
            style={{ filter: "blur(3px)" }}
          />
          {/* laser core */}
          <motion.line
            x1={PAD} x2={W - PAD_R + 62} y1={invY} y2={invY}
            stroke={pat.broken ? "#ff2d2d" : "#ef4444"} strokeWidth="1.6"
            strokeDasharray={pat.broken ? undefined : "12 7"}
            initial={{ opacity: 0 }}
            animate={{ opacity: pat.broken ? 1 : [0.6, 1, 0.6], strokeDashoffset: pat.broken ? 0 : [0, -38] }}
            transition={{ repeat: Infinity, duration: 1.6, ease: "linear" }}
            style={{ filter: "drop-shadow(0 0 6px rgba(239,68,68,0.95)) drop-shadow(0 0 14px rgba(239,68,68,0.45))" }}
          />
          {/* label */}
          <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }}>
            <rect x={PAD + 2} y={invY - 22} width={pat.broken ? 168 : 208} height={16} rx="3" fill="rgba(127,29,29,0.55)" stroke="#ef4444" strokeOpacity="0.6" strokeWidth="0.6" />
            <text x={PAD + 8} y={invY - 10.5} fill="#fecaca" fontSize="9" fontFamily="monospace" fontWeight="700" letterSpacing="0.08em">
              {pat.broken
                ? `✗ PATTERN BROKE · ${fmtP(pat.invalidation!)}`
                : `⚠ ${fmtP(pat.invalidation!)} ${pat.dirUp ? L("ALTI", "BELOW") : L("ÜSTÜ", "ABOVE")} = PATTERN BROKE`}
            </text>
          </motion.g>
        </g>
      )}

      {/* fib ratio labels on legs */}
      {pat.ratios.filter((r) => r.label).map((r, i) => {
        const a = pat.pivots[r.legFrom] ?? pat.pivots[pat.pivots.length - 1];
        const b = r.legTo < pat.pivots.length ? pat.pivots[r.legTo] : { i: pat.projected.i, p: pat.projected.p };
        const mx = (toX(a.i) + toX(b.i)) / 2;
        const my = (toY(a.p) + toY(b.p)) / 2;
        return (
          <motion.text key={r.label} x={mx} y={my - 8} textAnchor="middle" fill="#94a3b8" fontSize="8.5" fontFamily="monospace"
            initial={{ opacity: 0 }} animate={{ opacity: 0.9 }} transition={{ delay: 1.3 + i * 0.15 }}>
            {r.label}
          </motion.text>
        );
      })}
    </svg>
  );
}

// ── List + modal ───────────────────────────────────────────────────────────

export default function PatternsPanel({ live }: { live?: DetectedPattern[] }) {
  const { L } = useNeuralLocale();
  const demo = useMemo(buildPatterns, []);
  const patterns = live && live.length > 0 ? live : demo;
  const isLive = Boolean(live && live.length > 0);
  const [sel, setSel] = useState<DetectedPattern | null>(null);

  // ESC ile kapat — ModelDetailModal ile aynı davranış
  useEffect(() => {
    if (!sel) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSel(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sel]);

  return (
    <>
      <div className="space-y-2.5">
        {patterns.map((p, i) => (
          <motion.button
            key={p.id}
            type="button"
            onClick={() => setSel(p)}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.015, y: -1 }}
            transition={{ delay: i * 0.09, duration: 0.45 }}
            className="group flex w-full items-center gap-3.5 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-left transition-all hover:border-cyan-400/30 hover:bg-white/[0.04]"
          >
            <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
              p.dirUp ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" : "border-red-500/30 bg-red-500/10 text-red-400"
            }`}>
              <Shapes size={16} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2">
                <span className="text-[13px] font-medium text-gray-200">{p.name(L)}</span>
                <span className="rounded border border-white/10 px-1.5 py-0.5 font-mono text-[8px] tracking-[0.2em] text-gray-500">{p.tf}</span>
              </span>
              <span className="mt-1.5 flex items-center gap-2">
                <span className="h-1 w-24 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.span
                    className={`block h-full rounded-full ${p.dirUp ? "bg-emerald-400/80" : "bg-red-400/80"}`}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${p.completion}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.9, delay: 0.3 + i * 0.1 }}
                  />
                </span>
                <span className="font-mono text-[9px] text-gray-600">%{p.completion}</span>
                <span className={`font-mono text-[8px] tracking-[0.2em] ${p.broken ? "text-red-400" : p.completion === 100 ? "text-gray-500" : p.dirUp ? "text-emerald-500/80" : "text-red-500/80"}`}>
                  {p.status(L)}
                </span>
              </span>
            </span>
            <span className="text-right shrink-0">
              <span className="block font-mono text-xs text-gray-300">{p.targetPrice}</span>
              <span className="font-mono text-[8px] tracking-[0.2em] text-gray-600">{L("HEDEF", "TARGET")}</span>
            </span>
            <span className="font-mono text-[10px] text-cyan-400/0 group-hover:text-cyan-400/90 transition-colors shrink-0" aria-hidden>↗</span>
          </motion.button>
        ))}
      </div>
      <p className="mt-3 text-[13px] font-light text-gray-400">
        <span className="mr-1.5 text-cyan-500/70">◆</span>
        {L("Formasyona tıkla — grafikte tespit noktaları ve tahmini tamamlanma ayağı animasyonla açılır.", "Click a pattern — the chart opens with detection points and the projected completion leg animated.")}
        {isLive ? "" : ` ${L("(demo)", "(demo)")}`}
      </p>

      {/* detail modal — portal: transform'lu ata elemanlar position:fixed'i
          kırdığı için body'ye render edilir; modal her zaman viewport ortasında */}
      {typeof document !== "undefined" &&
        createPortal(
      <AnimatePresence>
        {sel && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[90] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4"
            onClick={() => setSel(null)}
            role="dialog"
            aria-modal="true"
            aria-label={sel.name(L)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 24 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 12 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              onClick={(e) => e.stopPropagation()}
              className="w-[min(96vw,1100px)] max-h-[92vh] overflow-y-auto rounded-2xl border border-white/10 bg-[#080c16]"
              style={{ boxShadow: `0 0 60px -18px ${sel.dirUp ? "rgba(52,211,153,0.35)" : "rgba(248,113,113,0.35)"}, 0 50px 120px -30px rgba(0,0,0,1)` }}
            >
              <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-white/[0.07] bg-[#080c16]/95 backdrop-blur px-5 py-4">
                <span className={`h-2.5 w-2.5 rounded-full ${sel.dirUp ? "bg-emerald-400" : "bg-red-400"}`} style={{ boxShadow: `0 0 10px ${sel.dirUp ? "#34d399" : "#f87171"}` }} />
                <h2 className="flex-1 text-sm font-bold tracking-wide text-white">
                  {sel.name(L)} <span className="ml-1.5 font-mono text-[10px] text-gray-500">{sel.tf}</span>
                </h2>
                <span className={`rounded-md border px-2.5 py-1 font-mono text-[10px] font-bold ${
                  sel.broken
                    ? "border-red-500/60 bg-red-500/15 text-red-300"
                    : sel.dirUp ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" : "border-red-500/40 bg-red-500/10 text-red-300"
                }`}>
                  {sel.status(L)}
                </span>
                <button onClick={() => setSel(null)} aria-label={L("Kapat", "Close")} className="flex items-center justify-center rounded-lg border border-white/10 text-gray-400 hover:text-white hover:bg-white/[0.06] transition-colors">
                  <X size={16} />
                </button>
              </div>
              <div className="p-5">
                <div className="rounded-xl border border-white/[0.06] bg-black/40 p-3">
                  <PatternChart pat={sel} />
                </div>

                {/* key levels */}
                <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                    <div className="font-mono text-[8px] tracking-[0.2em] text-gray-600">{L("HEDEF", "TARGET")}</div>
                    <div className={`mt-0.5 font-mono text-sm ${sel.dirUp ? "text-emerald-300" : "text-red-300"}`}>{sel.targetPrice}</div>
                  </div>
                  <div className={`rounded-lg border px-3 py-2 ${sel.broken ? "border-red-500/50 bg-red-500/10" : "border-red-500/25 bg-red-500/[0.04]"}`}>
                    <div className="font-mono text-[8px] tracking-[0.2em] text-red-400/80">{L("BOZULMA SINIRI", "BREAK LEVEL")}</div>
                    <div className="mt-0.5 font-mono text-sm text-red-300">
                      {sel.invalidation !== undefined ? fmtP(sel.invalidation) : "—"}
                    </div>
                  </div>
                  <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                    <div className="font-mono text-[8px] tracking-[0.2em] text-gray-600">{L("GÜVEN", "CONFIDENCE")}</div>
                    <div className="mt-0.5 font-mono text-sm text-cyan-300">%{sel.completion}</div>
                  </div>
                  <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                    <div className="font-mono text-[8px] tracking-[0.2em] text-gray-600">{L("ŞİMDİKİ FİYAT", "CURRENT PRICE")}</div>
                    <div className="mt-0.5 font-mono text-sm text-gray-200">
                      {sel.lastPrice !== undefined ? fmtP(sel.lastPrice) : "—"}
                    </div>
                  </div>
                </div>

                {/* broken warning */}
                {sel.broken && (
                  <div className="mt-3 flex items-center gap-2.5 rounded-lg border border-red-500/40 bg-red-500/10 px-3.5 py-2.5">
                    <span className="font-mono text-sm text-red-400">✗</span>
                    <p className="text-[12.5px] font-light text-red-200/90">
                      {L(
                        "Bu formasyon BOZULDU — fiyat bozulma sınırını geçti, senaryo artık geçersiz.",
                        "This pattern is BROKEN — price crossed the invalidation level, the scenario is no longer valid."
                      )}
                    </p>
                  </div>
                )}

                <p className="mt-4 text-[13px] font-light leading-relaxed text-gray-400">
                  <span className="mr-1.5 text-cyan-500/70">◆</span>
                  {sel.targetNote(L)}
                  {sel.invalidation !== undefined && !sel.broken && (
                    <span className="text-red-300/80">
                      {" "}{L(
                        `Fiyat ${fmtP(sel.invalidation)} seviyesinin ${sel.dirUp ? "altına inerse" : "üstüne çıkarsa"} formasyon kesin bozulur (kırmızı çizgi).`,
                        `If price moves ${sel.dirUp ? "below" : "above"} ${fmtP(sel.invalidation)}, the pattern is definitively broken (red line).`
                      )}
                    </span>
                  )}
                </p>
                <p className="mt-4 text-center font-mono text-[9px] tracking-[0.25em] text-gray-700">
                  {isLive
                    ? L("CANLI MOTOR ÇIKTISI — harmonic_pattern_service · 4H", "LIVE ENGINE OUTPUT — harmonic_pattern_service · 4H")
                    : L("DEMO GÖRÜNÜM — CANLIDA GERÇEK MOTOR ÇIKTISI AKAR", "DEMO VIEW — LIVE ENGINE OUTPUT WHEN WIRED")}
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>,
          document.body
        )}
    </>
  );
}
