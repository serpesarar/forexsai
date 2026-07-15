"use client";

/**
 * SignalSimulator — auto-cycling demo signal card. Every few seconds a new
 * mock signal springs in: direction badge, animated confidence bar,
 * self-drawing sparkline and a staggered TP/SL ladder. Pure demo data.
 */

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

type DemoSignal = {
  symbol: string;
  name: string;
  dir: "BUY" | "SELL";
  price: string;
  conf: number;
  models: string;
  tps: string[];
  sl: string;
  spark: string; // svg polyline points
};

const SIGNALS: DemoSignal[] = [
  {
    symbol: "NDX.INDX", name: "NASDAQ 100", dir: "BUY", price: "21,847.2", conf: 84,
    models: "5 / 6 MODELS ALIGNED", tps: ["22,105", "22,290", "22,480"], sl: "21,690",
    spark: "0,34 12,30 24,31 36,25 48,27 60,20 72,22 84,15 96,17 108,10 120,12 132,6",
  },
  {
    symbol: "XAUUSD", name: "GOLD SPOT", dir: "BUY", price: "3,412.80", conf: 71,
    models: "4 / 6 MODELS ALIGNED", tps: ["3,428", "3,447", "3,465"], sl: "3,396",
    spark: "0,30 12,32 24,26 36,28 48,22 60,25 72,18 84,21 96,14 108,16 120,11 132,8",
  },
  {
    symbol: "GDAXI.INDX", name: "DAX 40", dir: "SELL", price: "24,186.5", conf: 66,
    models: "4 / 6 MODELS ALIGNED", tps: ["24,050", "23,910", "23,770"], sl: "24,310",
    spark: "0,8 12,12 24,10 36,16 48,14 60,20 72,18 84,25 96,23 108,29 120,27 132,33",
  },
  {
    symbol: "USOIL.FOREX", name: "WTI CRUDE", dir: "BUY", price: "68.42", conf: 78,
    models: "5 / 6 MODELS ALIGNED", tps: ["69.10", "69.75", "70.40"], sl: "67.85",
    spark: "0,32 12,28 24,30 36,24 48,26 60,19 72,23 84,16 96,18 108,12 120,14 132,7",
  },
];

const rowStagger = {
  hidden: { opacity: 0, x: -14 },
  show: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: 0.35 + i * 0.12, duration: 0.45, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

function SignalCard({ s }: { s: DemoSignal }) {
  const buy = s.dir === "BUY";
  const stroke = buy ? "#34d399" : "#f87171";
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#080c16]/90 backdrop-blur-xl p-6 md:p-7 shadow-[0_30px_60px_-20px_rgba(0,0,0,0.8)]">
      {/* sweep shine */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent skew-x-[-18deg]"
        initial={{ left: "-40%" }}
        animate={{ left: "120%" }}
        transition={{ repeat: Infinity, duration: 3.2, ease: "easeInOut", repeatDelay: 1.4 }}
      />

      {/* header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="font-mono text-lg md:text-xl font-bold text-white tracking-wide">{s.symbol}</span>
            <motion.span
              initial={{ scale: 0, rotate: -12 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 320, damping: 14, delay: 0.15 }}
              className={`px-2.5 py-1 rounded-md text-[11px] font-bold tracking-[0.2em] font-mono ${
                buy ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/40" : "bg-red-500/15 text-red-400 border border-red-500/40"
              }`}
            >
              {buy ? "▲ BUY" : "▼ SELL"}
            </motion.span>
          </div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-gray-600 mt-1.5">{s.name} · {s.models}</p>
        </div>
        <div className="text-right">
          <div className="font-mono text-base md:text-lg text-gray-200">{s.price}</div>
          <div className="text-[10px] uppercase tracking-[0.25em] text-gray-600 mt-0.5">entry</div>
        </div>
      </div>

      {/* sparkline */}
      <svg viewBox="0 0 132 40" className="w-full h-12 mb-5" preserveAspectRatio="none" aria-hidden>
        <motion.polyline
          points={s.spark}
          fill="none"
          stroke={stroke}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.3, ease: "easeOut", delay: 0.2 }}
          style={{ filter: `drop-shadow(0 0 6px ${stroke})` }}
        />
      </svg>

      {/* confidence */}
      <div className="mb-5">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-[10px] uppercase tracking-[0.3em] text-gray-500">confidence</span>
          <span className={`font-mono text-sm font-bold ${buy ? "text-emerald-400" : "text-red-400"}`}>{s.conf}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${buy ? "bg-gradient-to-r from-emerald-600 to-emerald-300" : "bg-gradient-to-r from-red-600 to-red-300"}`}
            initial={{ width: "0%" }}
            animate={{ width: `${s.conf}%` }}
            transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
          />
        </div>
      </div>

      {/* TP / SL ladder */}
      <div className="grid grid-cols-4 gap-2.5">
        {s.tps.map((tp, i) => (
          <motion.div key={tp} custom={i} variants={rowStagger} initial="hidden" animate="show" className="rounded-lg bg-white/[0.03] border border-white/[0.07] px-2.5 py-2 text-center">
            <div className="text-[9px] uppercase tracking-[0.2em] text-gray-600 mb-0.5">TP{i + 1}</div>
            <div className={`font-mono text-xs ${buy ? "text-emerald-300" : "text-red-300"}`}>{tp}</div>
          </motion.div>
        ))}
        <motion.div custom={3} variants={rowStagger} initial="hidden" animate="show" className="rounded-lg bg-red-500/[0.06] border border-red-500/20 px-2.5 py-2 text-center">
          <div className="text-[9px] uppercase tracking-[0.2em] text-red-500/70 mb-0.5">SL</div>
          <div className="font-mono text-xs text-red-300">{s.sl}</div>
        </motion.div>
      </div>
    </div>
  );
}

export default function SignalSimulator() {
  const [idx, setIdx] = useState(0);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % SIGNALS.length), 4600);
    return () => clearInterval(t);
  }, [reduced]);

  return (
    <div className="relative">
      {/* live badge */}
      <div className="absolute -top-3 right-5 z-20 flex items-center gap-2 rounded-full border border-white/10 bg-black/80 px-3 py-1.5 backdrop-blur">
        <motion.span
          className="h-1.5 w-1.5 rounded-full bg-emerald-400"
          animate={{ opacity: [1, 0.2, 1], scale: [1, 1.4, 1] }}
          transition={{ repeat: Infinity, duration: 1.6 }}
        />
        <span className="text-[9px] uppercase tracking-[0.35em] text-gray-400 font-mono">demo feed</span>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 36, rotateX: -14, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, rotateX: 0, scale: 1 }}
          exit={{ opacity: 0, y: -28, rotateX: 10, scale: 0.97 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          style={{ transformPerspective: 900 }}
        >
          <SignalCard s={SIGNALS[idx]} />
        </motion.div>
      </AnimatePresence>

      {/* progress dots — button stays a 44px tap target, the visible dot is the inner span */}
      <div className="mt-3 flex justify-center">
        {SIGNALS.map((_, i) => (
          <button
            key={i}
            onClick={() => setIdx(i)}
            aria-label={`Show demo signal ${i + 1}`}
            className="flex items-center justify-center bg-transparent border-0"
          >
            <span
              className="block h-1.5 rounded-full transition-all duration-500"
              style={{ width: i === idx ? 24 : 6, background: i === idx ? "rgba(34,211,238,0.8)" : "rgba(255,255,255,0.15)" }}
            />
          </button>
        ))}
      </div>
    </div>
  );
}
