"use client";

/**
 * ModelSynapses — the orb's input layer. Three model nodes on each side,
 * connected to the core with bezier "synapse" wires; light pulses travel
 * inward (models feeding the brain). Node color = the model's current vote.
 * On mobile the beams hide and nodes collapse into a 2×3 grid.
 */

import { motion, useReducedMotion } from "framer-motion";
import CoreOrb, { CoreDirection } from "./CoreOrb";
import type { ModelVote, Dir } from "./panels";
import { useNeuralLocale } from "./i18n";

const DIR_STYLE: Record<Dir, { text: string; ring: string; bg: string; pulse: string }> = {
  BUY: { text: "text-emerald-300", ring: "border-emerald-500/40", bg: "bg-emerald-500/[0.07]", pulse: "#34d399" },
  SELL: { text: "text-red-300", ring: "border-red-500/40", bg: "bg-red-500/[0.07]", pulse: "#f87171" },
  HOLD: { text: "text-gray-400", ring: "border-white/10", bg: "bg-white/[0.03]", pulse: "#6b7280" },
};

function VoteNode({
  v,
  align,
  delay,
  onSelect,
}: {
  v: ModelVote;
  align: "left" | "right";
  delay: number;
  onSelect?: () => void;
}) {
  const { L } = useNeuralLocale();
  const s = DIR_STYLE[v.dir];
  return (
    <motion.button
      type="button"
      onClick={onSelect}
      initial={{ opacity: 0, x: align === "left" ? -24 : 24 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ scale: 1.025, y: -2 }}
      whileTap={{ scale: 0.98 }}
      transition={{ delay, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={`group relative rounded-xl border ${s.ring} ${s.bg} backdrop-blur-sm px-4 py-3 w-full lg:w-[220px] text-left cursor-pointer transition-shadow hover:shadow-[0_0_24px_rgba(34,211,238,0.12)] hover:border-cyan-400/30 ${
        align === "right" ? "lg:text-right" : ""
      }`}
    >
      <span
        className="pointer-events-none absolute top-2 right-2.5 font-mono text-[9px] text-cyan-400/0 group-hover:text-cyan-400/80 transition-colors"
        aria-hidden
      >
        ↗
      </span>
      <div className={`flex items-center gap-2 ${align === "right" ? "lg:flex-row-reverse" : ""}`}>
        <motion.span
          className="h-2 w-2 rounded-full shrink-0"
          style={{ background: v.color, boxShadow: `0 0 8px ${v.color}` }}
          animate={{ opacity: [1, 0.4, 1] }}
          transition={{ repeat: Infinity, duration: 2 + delay }}
        />
        <span className="font-mono text-[11px] tracking-[0.2em] text-gray-300">{v.label}</span>
        <span className={`ml-auto font-mono text-xs font-bold ${s.text} ${align === "right" ? "lg:ml-0 lg:mr-auto" : ""}`}>
          {v.dir}
          {v.dir !== "HOLD" && v.conf > 0 ? ` %${v.conf}` : ""}
        </span>
      </div>
      <p className={`mt-1.5 text-[11px] font-light leading-snug text-gray-500`}>{v.note}</p>
      <span
        className={`mt-1.5 block font-mono text-[8px] tracking-[0.25em] text-gray-700 group-hover:text-cyan-500/70 transition-colors ${
          align === "right" ? "lg:text-right" : ""
        }`}
      >
        {L("TIKLA — DETAY", "CLICK — DETAILS")}
      </span>
    </motion.button>
  );
}

export default function ModelSynapses({
  votes,
  direction,
  confidence,
  onSelect,
}: {
  votes: ModelVote[];
  direction: CoreDirection;
  confidence: number;
  onSelect?: (id: string) => void;
}) {
  const reduced = useReducedMotion();
  const left = votes.slice(0, 3);
  const right = votes.slice(3, 6);

  // beam endpoints in a 1000×420 viewBox — nodes at x≈195/805, orb center 500,210
  const yPos = [80, 210, 340];

  return (
    <div className="relative">
      {/* synapse beams (desktop only) */}
      <svg
        viewBox="0 0 1000 420"
        className="pointer-events-none absolute inset-0 hidden h-full w-full lg:block"
        preserveAspectRatio="none"
        aria-hidden
      >
        <defs>
          <filter id="syn-glow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="3" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {left.map((v, i) => {
          const id = `syn-l-${v.id}`;
          const d = `M 225 ${yPos[i]} C 340 ${yPos[i]}, 360 210, 435 210`;
          return (
            <g key={id}>
              <path id={id} d={d} fill="none" stroke={v.color} strokeOpacity="0.16" strokeWidth="1.2" />
              {!reduced && (
                <circle r="2.6" fill={DIR_STYLE[v.dir].pulse} filter="url(#syn-glow)">
                  <animateMotion dur={`${2 + i * 0.4}s`} repeatCount="indefinite">
                    <mpath href={`#${id}`} xlinkHref={`#${id}`} />
                  </animateMotion>
                </circle>
              )}
            </g>
          );
        })}
        {right.map((v, i) => {
          const id = `syn-r-${v.id}`;
          const d = `M 775 ${yPos[i]} C 660 ${yPos[i]}, 640 210, 565 210`;
          return (
            <g key={id}>
              <path id={id} d={d} fill="none" stroke={v.color} strokeOpacity="0.16" strokeWidth="1.2" />
              {!reduced && (
                <circle r="2.6" fill={DIR_STYLE[v.dir].pulse} filter="url(#syn-glow)">
                  <animateMotion dur={`${2.2 + i * 0.4}s`} repeatCount="indefinite">
                    <mpath href={`#${id}`} xlinkHref={`#${id}`} />
                  </animateMotion>
                </circle>
              )}
            </g>
          );
        })}
      </svg>

      {/* layout: nodes | orb | nodes */}
      <div className="relative flex flex-col items-center gap-6 lg:grid lg:grid-cols-[1fr_auto_1fr] lg:items-center lg:gap-2">
        <div className="order-2 grid w-full grid-cols-1 gap-3 sm:grid-cols-3 lg:order-1 lg:flex lg:flex-col lg:items-start lg:gap-8">
          {left.map((v, i) => (
            <VoteNode key={v.id} v={v} align="left" delay={0.3 + i * 0.15} onSelect={() => onSelect?.(v.id)} />
          ))}
        </div>

        <div className="order-1 lg:order-2 lg:px-6">
          <CoreOrb direction={direction} confidence={confidence} size={330} />
        </div>

        <div className="order-3 grid w-full grid-cols-1 gap-3 sm:grid-cols-3 lg:flex lg:flex-col lg:items-end lg:gap-8">
          {right.map((v, i) => (
            <VoteNode key={v.id} v={v} align="right" delay={0.45 + i * 0.15} onSelect={() => onSelect?.(v.id)} />
          ))}
        </div>
      </div>
    </div>
  );
}
