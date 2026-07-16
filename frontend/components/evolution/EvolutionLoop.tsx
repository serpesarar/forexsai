"use client";

/**
 * Evrim Döngüsü — hero'nun kalbi. Kendi kendini besleyen döngünün canlı,
 * orbital görselleştirmesi: Sinyal → Sonuç → Analiz → Öğren → Enjekte.
 * Kuyruklu yıldız halkada döner; her düğüm tıklanınca ilgili bölüme götürür.
 */

import { motion } from "framer-motion";
import { BrainCog, GraduationCap, Microscope, Target, Zap } from "lucide-react";

import { PulseDot } from "./ui";

const SIZE = 300;
const RADIUS = 118;

const NODES = [
  { label: "Sinyal", icon: <Zap size={16} />, color: "#60A5FA", section: "harita" },
  { label: "Sonuç", icon: <Target size={16} />, color: "#34D399", section: "performans" },
  { label: "Analiz", icon: <Microscope size={16} />, color: "#FB7185", section: "analiz" },
  { label: "Öğren", icon: <GraduationCap size={16} />, color: "#C4B5FD", section: "dersler" },
  { label: "Enjekte", icon: <BrainCog size={16} />, color: "#FCD34D", section: "dersler" },
];

export default function EvolutionLoop({ activeRuns }: { activeRuns: number }) {
  const goTo = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className="relative shrink-0"
      style={{ width: SIZE, height: SIZE }}
      aria-hidden
    >
      {/* halka */}
      <svg width={SIZE} height={SIZE} className="absolute inset-0">
        <defs>
          <linearGradient id="loop-ring" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#60A5FA33" />
            <stop offset="50%" stopColor="#C4B5FD33" />
            <stop offset="100%" stopColor="#34D39933" />
          </linearGradient>
        </defs>
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="url(#loop-ring)"
          strokeWidth={1.5}
          strokeDasharray="3 6"
        />
      </svg>

      {/* dönen parıltı yayı */}
      <motion.div
        className="absolute inset-0"
        animate={{ rotate: 360 }}
        transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
      >
        <span
          className="absolute left-1/2 top-1/2 h-2 w-2 rounded-full"
          style={{
            transform: `translate(-50%, -50%) translateY(-${RADIUS}px)`,
            background: "#A5B4FC",
            boxShadow: "0 0 12px 4px #818CF8AA, 0 0 34px 10px #818CF833",
          }}
        />
      </motion.div>

      {/* düğümler */}
      {NODES.map((n, i) => {
        const angle = -90 + (360 / NODES.length) * i;
        const rad = (angle * Math.PI) / 180;
        const x = SIZE / 2 + RADIUS * Math.cos(rad);
        const y = SIZE / 2 + RADIUS * Math.sin(rad);
        return (
          <motion.button
            key={n.label}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.15 + i * 0.09, type: "spring", damping: 16 }}
            whileHover={{ scale: 1.12 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => goTo(n.section)}
            className="group absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1"
            style={{ left: x, top: y, pointerEvents: "auto" }}
            title={`${n.label} — bölüme git`}
          >
            <span
              className="flex h-10 w-10 items-center justify-center rounded-2xl border text-white backdrop-blur-sm transition-shadow"
              style={{
                background: `${n.color}18`,
                borderColor: `${n.color}45`,
                color: n.color,
                boxShadow: `0 0 18px -4px ${n.color}66`,
              }}
            >
              {n.icon}
            </span>
            <span className="text-[10px] font-medium text-slate-400 transition group-hover:text-slate-200">
              {n.label}
            </span>
          </motion.button>
        );
      })}

      {/* merkez */}
      <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1.5">
        <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 backdrop-blur-sm">
          <PulseDot color={activeRuns > 0 ? "#34D399" : "#818CF8"} />
          <span className="text-[11px] font-semibold text-slate-200">
            {activeRuns > 0 ? `${activeRuns} analiz çalışıyor` : "döngü canlı"}
          </span>
        </span>
      </div>
    </motion.div>
  );
}
