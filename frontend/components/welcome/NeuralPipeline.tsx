"use client";

/**
 * NeuralPipeline — animated SVG of the real ForexSAI ensemble:
 * six model nodes stream light pulses along bezier wires into the
 * ENSEMBLE core, which fires a signal node that flips BUY / SELL.
 * Pulses use SMIL <animateMotion> (zero-JS, GPU friendly); the core
 * breathes with framer-motion.
 */

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

const MODELS = [
  { id: "ml", label: "ML · LightGBM", sub: "150+ features", color: "#4f8cff", y: 40 },
  { id: "p1", label: "PULSE 1", sub: "algo scalp", color: "#fb923c", y: 108 },
  { id: "p2", label: "PULSE 2", sub: "ML + TA hybrid", color: "#f97316", y: 176 },
  { id: "p3", label: "PULSE 3", sub: "multi-timeframe", color: "#ea580c", y: 244 },
  { id: "emel", label: "EMEL", sub: "10-check strategic", color: "#a855f7", y: 312 },
  { id: "smc", label: "SMC / ICT", sub: "order blocks · FVG", color: "#14b8a6", y: 380 },
];

const CX = 470; // ensemble core x
const CY = 210; // ensemble core y
const SX = 760; // signal node x

function wirePath(y: number): string {
  return `M 148 ${y} C 300 ${y}, 330 ${CY}, ${CX - 46} ${CY}`;
}

function SignalFlip() {
  const [buy, setBuy] = useState(true);
  useEffect(() => {
    const t = setInterval(() => setBuy((b) => !b), 3200);
    return () => clearInterval(t);
  }, []);
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={buy ? "buy" : "sell"}
        initial={{ opacity: 0, y: 14, scale: 0.8, filter: "blur(6px)" }}
        animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
        exit={{ opacity: 0, y: -14, scale: 0.8, filter: "blur(6px)" }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className={`font-mono text-sm md:text-base font-bold tracking-[0.3em] ${
          buy ? "text-emerald-400" : "text-red-400"
        }`}
      >
        {buy ? "▲ BUY" : "▼ SELL"}
      </motion.div>
    </AnimatePresence>
  );
}

export default function NeuralPipeline() {
  const reduced = useReducedMotion();

  return (
    <div className="relative w-full">
      <svg viewBox="0 0 880 420" className="w-full h-auto" role="img" aria-label="Six AI models feeding one ensemble signal">
        <defs>
          <filter id="np-glow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="np-core" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(34,211,238,0.9)" />
            <stop offset="45%" stopColor="rgba(34,211,238,0.25)" />
            <stop offset="100%" stopColor="rgba(34,211,238,0)" />
          </radialGradient>
        </defs>

        {/* wires */}
        {MODELS.map((m) => (
          <g key={m.id}>
            <path id={`wire-${m.id}`} d={wirePath(m.y)} fill="none" stroke={m.color} strokeOpacity="0.18" strokeWidth="1.2" />
            {!reduced && (
              <>
                <circle r="3" fill={m.color} filter="url(#np-glow)">
                  <animateMotion dur={`${2.4 + MODELS.indexOf(m) * 0.35}s`} repeatCount="indefinite">
                    <mpath href={`#wire-${m.id}`} xlinkHref={`#wire-${m.id}`} />
                  </animateMotion>
                </circle>
                <circle r="1.6" fill="#ffffff" opacity="0.8">
                  <animateMotion dur={`${2.4 + MODELS.indexOf(m) * 0.35}s`} begin={`${0.7 + MODELS.indexOf(m) * 0.2}s`} repeatCount="indefinite">
                    <mpath href={`#wire-${m.id}`} xlinkHref={`#wire-${m.id}`} />
                  </animateMotion>
                </circle>
              </>
            )}
          </g>
        ))}

        {/* ensemble → signal wire */}
        <path id="wire-out" d={`M ${CX + 46} ${CY} C ${CX + 140} ${CY}, ${SX - 130} ${CY}, ${SX - 58} ${CY}`} fill="none" stroke="#22d3ee" strokeOpacity="0.25" strokeWidth="1.5" strokeDasharray="4 6" />
        {!reduced &&
          [0, 0.55, 1.1].map((b) => (
            <circle key={b} r="3.4" fill="#22d3ee" filter="url(#np-glow)">
              <animateMotion dur="1.7s" begin={`${b}s`} repeatCount="indefinite">
                <mpath href="#wire-out" xlinkHref="#wire-out" />
              </animateMotion>
            </circle>
          ))}

        {/* model nodes */}
        {MODELS.map((m, i) => (
          <g key={m.id}>
            <rect x="8" y={m.y - 24} width="140" height="48" rx="10" fill="rgba(255,255,255,0.03)" stroke={m.color} strokeOpacity="0.35" />
            <circle cx="26" cy={m.y} r="4" fill={m.color} filter="url(#np-glow)">
              {!reduced && <animate attributeName="opacity" values="1;0.35;1" dur={`${1.6 + i * 0.2}s`} repeatCount="indefinite" />}
            </circle>
            <text x="40" y={m.y - 3} fill="#e5e7eb" fontSize="11.5" fontFamily="ui-monospace, monospace" fontWeight="600" letterSpacing="0.08em">
              {m.label}
            </text>
            <text x="40" y={m.y + 13} fill="#6b7280" fontSize="9.5" fontFamily="ui-monospace, monospace" letterSpacing="0.05em">
              {m.sub}
            </text>
          </g>
        ))}

        {/* ensemble core */}
        <circle cx={CX} cy={CY} r="72" fill="url(#np-core)" opacity="0.5" />
        {!reduced && (
          <>
            <circle cx={CX} cy={CY} r="46" fill="none" stroke="#22d3ee" strokeOpacity="0.4" strokeWidth="1">
              <animate attributeName="r" values="46;58;46" dur="3s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" values="0.4;0;0.4" dur="3s" repeatCount="indefinite" />
            </circle>
            <circle cx={CX} cy={CY} r="46" fill="none" stroke="#a855f7" strokeOpacity="0.3" strokeWidth="1">
              <animate attributeName="r" values="46;66;46" dur="3s" begin="1.5s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" values="0.3;0;0.3" dur="3s" begin="1.5s" repeatCount="indefinite" />
            </circle>
          </>
        )}
        <circle cx={CX} cy={CY} r="44" fill="rgba(8,12,22,0.92)" stroke="#22d3ee" strokeOpacity="0.6" strokeWidth="1.4" filter="url(#np-glow)" />
        <text x={CX} y={CY - 4} textAnchor="middle" fill="#e5e7eb" fontSize="11" fontFamily="ui-monospace, monospace" fontWeight="700" letterSpacing="0.2em">
          ENSEMBLE
        </text>
        <text x={CX} y={CY + 13} textAnchor="middle" fill="#22d3ee" fontSize="8.5" fontFamily="ui-monospace, monospace" letterSpacing="0.12em">
          regime-aware
        </text>

        {/* signal node shell */}
        <rect x={SX - 56} y={CY - 34} width="118" height="68" rx="14" fill="rgba(8,12,22,0.92)" stroke="rgba(34,211,238,0.45)" strokeWidth="1.2" filter="url(#np-glow)" />
        <text x={SX + 3} y={CY - 14} textAnchor="middle" fill="#6b7280" fontSize="8.5" fontFamily="ui-monospace, monospace" letterSpacing="0.25em">
          LIVE SIGNAL
        </text>
      </svg>

      {/* HTML overlay for the flipping BUY/SELL (crisper text than SVG) */}
      <div
        className="absolute flex items-center justify-center pointer-events-none"
        style={{ left: `${((SX - 56) / 880) * 100}%`, top: `${((CY - 10) / 420) * 100}%`, width: `${(118 / 880) * 100}%`, height: `${(40 / 420) * 100}%` }}
      >
        <SignalFlip />
      </div>
    </div>
  );
}
