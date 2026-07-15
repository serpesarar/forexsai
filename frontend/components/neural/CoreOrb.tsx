"use client";

/**
 * CoreOrb — the "electronic brain" centerpiece of the Neural panel.
 * A canvas-rendered energy sphere: three tilted particle rings orbiting a
 * breathing core, expanding pulse waves, and drifting energy motes. The
 * orb's hue follows the ensemble verdict (BUY green / SELL red / HOLD cyan).
 * Verdict text is an HTML overlay for crisp type.
 */

import { useEffect, useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useNeuralLocale } from "./i18n";

export type CoreDirection = "BUY" | "SELL" | "HOLD";

const HUES: Record<CoreDirection, { rgb: string; soft: string; word: string; text: string }> = {
  BUY: { rgb: "52, 211, 153", soft: "16, 185, 129", word: "YUKARI", text: "text-emerald-300" },
  SELL: { rgb: "248, 113, 113", soft: "239, 68, 68", word: "AŞAĞI", text: "text-red-300" },
  HOLD: { rgb: "34, 211, 238", soft: "6, 182, 212", word: "BEKLE", text: "text-cyan-300" },
};

type Ring = { radius: number; tilt: number; rot: number; speed: number; count: number };

const RINGS: Ring[] = [
  { radius: 0.86, tilt: 0.32, rot: 0.5, speed: 0.00042, count: 46 },
  { radius: 0.7, tilt: 0.24, rot: -0.9, speed: -0.00058, count: 38 },
  { radius: 0.98, tilt: 0.16, rot: 1.9, speed: 0.0003, count: 54 },
];

export default function CoreOrb({
  direction,
  confidence,
  size = 340,
}: {
  direction: CoreDirection;
  confidence: number;
  size?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  const { L } = useNeuralLocale();
  const hue = HUES[direction];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const DPR = Math.min(window.devicePixelRatio || 1, 2);
    const S = size;
    canvas.width = S * DPR;
    canvas.height = S * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);

    const cx = S / 2;
    const cy = S / 2;
    const R = S * 0.31; // core radius
    const rgb = HUES[direction].rgb;

    let raf = 0;
    let hidden = false;
    let pulses: number[] = [0]; // pulse ring progress 0..1

    const motes = Array.from({ length: 26 }, () => ({
      a: Math.random() * Math.PI * 2,
      d: R * (1.15 + Math.random() * 0.85),
      v: (Math.random() - 0.5) * 0.0012,
      r: 0.6 + Math.random() * 1.3,
      o: 0.15 + Math.random() * 0.4,
    }));

    const drawCore = (t: number) => {
      const breathe = 1 + Math.sin(t / 1100) * 0.045;
      const r = R * breathe;

      const halo = ctx.createRadialGradient(cx, cy, r * 0.2, cx, cy, r * 2.1);
      halo.addColorStop(0, `rgba(${rgb}, 0.32)`);
      halo.addColorStop(0.45, `rgba(${rgb}, 0.10)`);
      halo.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = halo;
      ctx.fillRect(0, 0, S, S);

      const body = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.35, r * 0.1, cx, cy, r);
      body.addColorStop(0, `rgba(${rgb}, 0.55)`);
      body.addColorStop(0.55, `rgba(${rgb}, 0.16)`);
      body.addColorStop(1, `rgba(${rgb}, 0.05)`);
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = body;
      ctx.fill();
      ctx.strokeStyle = `rgba(${rgb}, 0.5)`;
      ctx.lineWidth = 1.2;
      ctx.shadowBlur = 18;
      ctx.shadowColor = `rgba(${rgb}, 0.9)`;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // inner "neuron" arcs
      for (let i = 0; i < 3; i++) {
        const a0 = t / (900 + i * 300) + (i * Math.PI * 2) / 3;
        ctx.beginPath();
        ctx.arc(cx, cy, r * (0.45 + i * 0.16), a0, a0 + Math.PI * (0.55 - i * 0.1));
        ctx.strokeStyle = `rgba(${rgb}, ${0.35 - i * 0.08})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    };

    const drawRing = (ring: Ring, t: number) => {
      const cosT = Math.cos(ring.rot);
      const sinT = Math.sin(ring.rot);
      for (let i = 0; i < ring.count; i++) {
        const a = (i / ring.count) * Math.PI * 2 + t * ring.speed;
        const ex = Math.cos(a) * R * ring.radius * 1.6;
        const ey = Math.sin(a) * R * ring.radius * 1.6 * ring.tilt;
        const x = cx + ex * cosT - ey * sinT;
        const y = cy + ex * sinT + ey * cosT;
        const depth = (Math.sin(a) + 1) / 2; // 0 back → 1 front
        const alpha = 0.12 + depth * 0.65;
        const rad = 0.7 + depth * 1.5;
        ctx.beginPath();
        ctx.arc(x, y, rad, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${rgb}, ${alpha})`;
        ctx.fill();
      }
    };

    const drawPulses = () => {
      pulses = pulses.map((p) => p + 0.006).filter((p) => p < 1);
      if (pulses.length === 0 || (pulses[pulses.length - 1] > 0.45 && pulses.length < 3)) pulses.push(0);
      for (const p of pulses) {
        ctx.beginPath();
        ctx.arc(cx, cy, R + p * R * 1.55, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${rgb}, ${0.28 * (1 - p)})`;
        ctx.lineWidth = 1.4 * (1 - p) + 0.3;
        ctx.stroke();
      }
    };

    const drawMotes = () => {
      for (const m of motes) {
        m.a += m.v;
        const x = cx + Math.cos(m.a) * m.d;
        const y = cy + Math.sin(m.a) * m.d * 0.92;
        ctx.beginPath();
        ctx.arc(x, y, m.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${rgb}, ${m.o})`;
        ctx.fill();
      }
    };

    const frame = (t: number) => {
      ctx.clearRect(0, 0, S, S);
      drawPulses();
      drawRing(RINGS[2], t);
      drawCore(t);
      drawRing(RINGS[0], t);
      drawRing(RINGS[1], t);
      drawMotes();
    };

    const loop = (t: number) => {
      if (!hidden) frame(t);
      raf = requestAnimationFrame(loop);
    };

    const onVis = () => {
      hidden = document.hidden;
    };
    document.addEventListener("visibilitychange", onVis);

    if (reduced) frame(0);
    else raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [direction, size, reduced]);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <canvas ref={canvasRef} style={{ width: size, height: size }} aria-hidden />
      {/* verdict overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
        <motion.div
          key={`${direction}-${confidence}`}
          initial={{ opacity: 0, scale: 0.8, filter: "blur(6px)" }}
          animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className={`font-mono text-[10px] tracking-[0.4em] mb-1 ${hue.text} opacity-80`}>
            {direction === "HOLD" ? L("KARAR", "VERDICT") : L("YÖN", "DIRECTION")}
          </div>
          <div className={`text-4xl md:text-5xl font-bold tracking-wide ${hue.text} drop-shadow-[0_0_18px_rgba(0,0,0,0.6)]`}>
            {direction}
          </div>
          <div className="mt-1.5 font-mono text-sm text-white/85">%{confidence}</div>
          <div className="font-mono text-[9px] tracking-[0.3em] text-gray-500 mt-0.5">{L("ENSEMBLE GÜVENİ", "ENSEMBLE CONFIDENCE")}</div>
        </motion.div>
      </div>
    </div>
  );
}
