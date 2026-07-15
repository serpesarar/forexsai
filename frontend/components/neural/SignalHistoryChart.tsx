"use client";

/**
 * SignalHistoryChart — the Active Signal panel reborn as a chart.
 * Candles + a glowing "signal wave" ribbon that follows price and is
 * tinted by what the system voted on each stretch of candles:
 * BUY = green, SELL = red, neutral = gray. Segment boundaries carry
 * entry arrows; the active (last) segment draws entry / TP / SL lines.
 * Works standalone with demo data; accepts real candles/segments when
 * the backend is wired.
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useNeuralLocale } from "./i18n";

export type WaveDir = "BUY" | "SELL" | "HOLD";
export interface WaveCandle { o: number; h: number; l: number; c: number; label?: string }
export interface WaveSegment { from: number; to: number; dir: WaveDir }
export interface ActiveOverlay { dir: WaveDir; entry: number; tps: number[]; sl: number }

const DIR_RGB: Record<WaveDir, string> = {
  BUY: "52, 211, 153",
  SELL: "248, 113, 113",
  HOLD: "148, 163, 184",
};

// ── Demo data (used until the live feed takes over) ───────────────────────
function demoData(): { candles: WaveCandle[]; segments: WaveSegment[]; active: ActiveOverlay } {
  const candles: WaveCandle[] = [];
  let p = 21500;
  const drift = [
    ...Array(10).fill(9), ...Array(8).fill(-13), ...Array(6).fill(2),
    ...Array(14).fill(14), ...Array(8).fill(-4), ...Array(18).fill(11),
  ];
  for (let i = 0; i < 64; i++) {
    const o = p;
    const wob = Math.sin(i * 2.7) * 16 + Math.cos(i * 1.3) * 9;
    const c = o + (drift[i] ?? 6) + wob * 0.45;
    const h = Math.max(o, c) + 10 + Math.abs(Math.sin(i * 1.7)) * 14;
    const l = Math.min(o, c) - 10 - Math.abs(Math.cos(i * 2.1)) * 14;
    candles.push({ o, h, l, c });
    p = c;
  }
  const segments: WaveSegment[] = [
    { from: 0, to: 9, dir: "BUY" },
    { from: 10, to: 17, dir: "SELL" },
    { from: 18, to: 23, dir: "HOLD" },
    { from: 24, to: 37, dir: "BUY" },
    { from: 38, to: 45, dir: "HOLD" },
    { from: 46, to: 63, dir: "BUY" },
  ];
  const last = candles[63].c;
  return {
    candles,
    segments,
    active: { dir: "BUY", entry: candles[46].o, tps: [last + 60, last + 200, last + 390], sl: candles[46].o - 120 },
  };
}

export default function SignalHistoryChart({
  candles: candlesProp,
  segments: segmentsProp,
  active: activeProp,
  dateLabels,
  isLive = false,
}: {
  candles?: WaveCandle[];
  segments?: WaveSegment[];
  active?: ActiveOverlay | null;
  dateLabels?: string[]; // one label per segment start, same order as segments
  isLive?: boolean;
}) {
  const { L } = useNeuralLocale();
  const demo = useMemo(demoData, []);
  const candles = candlesProp && candlesProp.length >= 10 ? candlesProp : demo.candles;
  const segments = segmentsProp && segmentsProp.length > 0 ? segmentsProp : demo.segments;
  const active = activeProp === undefined ? demo.active : activeProp;

  const W = 920;
  const H = 340;
  const PAD_T = 16;
  const PAD_B = 34;
  const PAD_R = 74; // room for TP/SL labels
  const PAD_L = 8;

  const { toY, toX, cw, lo, hi } = useMemo(() => {
    let lo = Infinity;
    let hi = -Infinity;
    for (const c of candles) {
      lo = Math.min(lo, c.l);
      hi = Math.max(hi, c.h);
    }
    if (active) {
      for (const t of active.tps) hi = Math.max(hi, t);
      lo = Math.min(lo, active.sl);
    }
    const pad = (hi - lo) * 0.06 || 1;
    lo -= pad;
    hi += pad;
    const innerW = W - PAD_L - PAD_R;
    const cw = innerW / candles.length;
    const toY = (p: number) => PAD_T + (1 - (p - lo) / (hi - lo)) * (H - PAD_T - PAD_B);
    const toX = (i: number) => PAD_L + i * cw + cw / 2;
    return { toY, toX, cw, lo, hi };
  }, [candles, active]);

  // wave path per segment (smooth through closes)
  const segPath = (s: WaveSegment) => {
    const pts: string[] = [];
    for (let i = Math.max(0, s.from); i <= Math.min(candles.length - 1, s.to); i++) {
      pts.push(`${i === s.from ? "M" : "L"} ${toX(i).toFixed(1)} ${toY(candles[i].c).toFixed(1)}`);
    }
    return pts.join(" ");
  };
  const segAreaPath = (s: WaveSegment) => {
    const from = Math.max(0, s.from);
    const to = Math.min(candles.length - 1, s.to);
    let d = `M ${toX(from).toFixed(1)} ${(H - PAD_B).toFixed(1)} `;
    for (let i = from; i <= to; i++) d += `L ${toX(i).toFixed(1)} ${toY(candles[i].c).toFixed(1)} `;
    d += `L ${toX(to).toFixed(1)} ${(H - PAD_B).toFixed(1)} Z`;
    return d;
  };

  const fmt = (p: number) =>
    p >= 1000 ? p.toLocaleString("en-US", { maximumFractionDigits: 0 }) : p.toFixed(2);

  const dirWord = (d: WaveDir) => (d === "HOLD" ? L("NÖTR", "NEUTRAL") : d);
  const lastClose = candles[candles.length - 1].c;
  const lastSeg = segments[segments.length - 1];

  return (
    <div>
      {/* legend */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {(["BUY", "SELL", "HOLD"] as WaveDir[]).map((d) => (
          <span
            key={d}
            className="flex items-center gap-1.5 rounded-full border border-white/[0.07] bg-white/[0.02] px-2.5 py-1 font-mono text-[9px] tracking-[0.2em] text-gray-400"
          >
            <span className="h-1.5 w-4 rounded-full" style={{ background: `rgba(${DIR_RGB[d]}, 0.8)` }} />
            {dirWord(d)}
          </span>
        ))}
        <span className="ml-auto font-mono text-[9px] tracking-[0.25em] text-gray-600">
          {L("SİNYAL DALGASI — SON 64 MUM", "SIGNAL WAVE — LAST 64 CANDLES")}
        </span>
      </div>

      <div className="rounded-xl border border-white/[0.06] bg-black/40 p-2">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label={L("Sinyal geçmişi grafiği", "Signal history chart")}>
          <defs>
            {(["BUY", "SELL", "HOLD"] as WaveDir[]).map((d) => (
              <linearGradient key={d} id={`wave-${d}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={`rgba(${DIR_RGB[d]}, 0.30)`} />
                <stop offset="100%" stopColor={`rgba(${DIR_RGB[d]}, 0)`} />
              </linearGradient>
            ))}
          </defs>

          {/* horizontal gridlines */}
          {[0.25, 0.5, 0.75].map((f) => {
            const y = PAD_T + f * (H - PAD_T - PAD_B);
            const price = hi - f * (hi - lo);
            return (
              <g key={f}>
                <line x1={PAD_L} x2={W - PAD_R} y1={y} y2={y} stroke="rgba(148,163,184,0.08)" strokeWidth="1" />
                <text x={W - PAD_R + 6} y={y + 3} fill="#475569" fontSize="9" fontFamily="monospace">
                  {fmt(price)}
                </text>
              </g>
            );
          })}

          {/* segment tint bands + boundary markers */}
          {segments.map((s, si) => {
            const x0 = toX(Math.max(0, s.from)) - cw / 2;
            const x1 = toX(Math.min(candles.length - 1, s.to)) + cw / 2;
            return (
              <g key={`band-${si}`}>
                <rect x={x0} y={PAD_T} width={x1 - x0} height={H - PAD_T - PAD_B} fill={`rgba(${DIR_RGB[s.dir]}, 0.035)`}>
                  <title>
                    {`${dirWord(s.dir)} · ${dateLabels?.[si] ?? ""}`}
                  </title>
                </rect>
                {si > 0 && <line x1={x0} x2={x0} y1={PAD_T} y2={H - PAD_B} stroke="rgba(148,163,184,0.12)" strokeDasharray="2 4" strokeWidth="1" />}
                {/* direction arrow at segment start */}
                {s.dir !== "HOLD" && (
                  <motion.text
                    x={toX(s.from)}
                    y={s.dir === "BUY" ? toY(candles[Math.max(0, s.from)].l) + 14 : toY(candles[Math.max(0, s.from)].h) - 8}
                    textAnchor="middle"
                    fontSize="10"
                    fill={`rgb(${DIR_RGB[s.dir]})`}
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.6 + si * 0.12 }}
                  >
                    {s.dir === "BUY" ? "▲" : "▼"}
                  </motion.text>
                )}
                {/* date label */}
                {dateLabels?.[si] && (
                  <text x={x0 + 3} y={H - PAD_B + 14} fill="#475569" fontSize="8.5" fontFamily="monospace">
                    {dateLabels[si]}
                  </text>
                )}
              </g>
            );
          })}

          {/* candles */}
          {candles.map((c, i) => {
            const x = toX(i);
            const up = c.c >= c.o;
            const col = up ? "#34d399" : "#f87171";
            return (
              <motion.g
                key={i}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 0.9 }}
                viewport={{ once: true }}
                transition={{ delay: Math.min(i * 0.012, 0.8), duration: 0.3 }}
              >
                <line x1={x} x2={x} y1={toY(c.h)} y2={toY(c.l)} stroke={col} strokeOpacity="0.55" strokeWidth="1" />
                <rect
                  x={x - cw * 0.28}
                  y={toY(Math.max(c.o, c.c))}
                  width={cw * 0.56}
                  height={Math.max(1.2, Math.abs(toY(c.o) - toY(c.c)))}
                  fill={col}
                  fillOpacity="0.75"
                  rx="0.5"
                />
              </motion.g>
            );
          })}

          {/* signal wave: area + glowing line per segment */}
          {segments.map((s, si) => (
            <g key={`wave-${si}`}>
              <motion.path
                d={segAreaPath(s)}
                fill={`url(#wave-${s.dir})`}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 + si * 0.1, duration: 0.6 }}
              />
              <motion.path
                d={segPath(s)}
                fill="none"
                stroke={`rgba(${DIR_RGB[s.dir]}, 0.95)`}
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ filter: `drop-shadow(0 0 6px rgba(${DIR_RGB[s.dir]}, 0.8))` }}
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.35 + si * 0.12, duration: 0.7, ease: "easeOut" }}
              />
            </g>
          ))}

          {/* active signal overlay: entry / TPs / SL */}
          {active && (
            <g>
              {[{ p: active.entry, col: "148, 163, 184", tag: L("GİRİŞ", "ENTRY") },
                ...active.tps.map((t, i) => ({ p: t, col: DIR_RGB.BUY, tag: `TP${i + 1}` })),
                { p: active.sl, col: DIR_RGB.SELL, tag: "SL" }].map((ln) => (
                <g key={ln.tag}>
                  <line
                    x1={toX(Math.max(0, lastSeg.from))}
                    x2={W - PAD_R}
                    y1={toY(ln.p)}
                    y2={toY(ln.p)}
                    stroke={`rgba(${ln.col}, 0.55)`}
                    strokeWidth="1"
                    strokeDasharray="5 4"
                  />
                  <rect x={W - PAD_R + 2} y={toY(ln.p) - 8} width={PAD_R - 6} height={16} rx="3" fill="rgba(8,12,22,0.9)" stroke={`rgba(${ln.col}, 0.4)`} strokeWidth="0.6" />
                  <text x={W - PAD_R + 6} y={toY(ln.p) + 3.5} fill={`rgb(${ln.col})`} fontSize="8.5" fontFamily="monospace" letterSpacing="0.05em">
                    {ln.tag} {fmt(ln.p)}
                  </text>
                </g>
              ))}
            </g>
          )}

          {/* live price dot */}
          <motion.circle
            cx={toX(candles.length - 1)}
            cy={toY(lastClose)}
            r="4"
            fill={`rgb(${DIR_RGB[lastSeg.dir]})`}
            style={{ filter: `drop-shadow(0 0 8px rgba(${DIR_RGB[lastSeg.dir]}, 1))` }}
            animate={{ opacity: [1, 0.45, 1], scale: [1, 1.35, 1] }}
            transition={{ repeat: Infinity, duration: 1.8 }}
          />
        </svg>
      </div>

      <p className="mt-3 text-[13px] leading-relaxed font-light text-gray-400">
        <span className="mr-1.5 text-cyan-500/70">◆</span>
        {L(
          "Renkli dalga, sistemin o mumlar boyunca hangi yönde sinyal verdiğini gösterir — yeşil BUY, kırmızı SELL, gri nötr/bekleme. Kesikli çizgiler aktif sinyalin giriş, hedef ve stop seviyeleri.",
          "The colored wave shows which direction the system was signalling across those candles — green BUY, red SELL, gray neutral. Dashed lines are the active signal's entry, targets and stop."
        )}
        {isLive ? "" : ` ${L("(demo veri)", "(demo data)")}`}
      </p>
    </div>
  );
}
