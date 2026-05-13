"use client";

/**
 * PSI Speedometer — Compact dashboard hero gauge
 * ================================================
 * A car-dashboard-style analog dial that sits at the very top of the home
 * page (above Meta-Engine). Designed to be:
 *
 *   - Instantly readable at a glance (color band + needle position)
 *   - Compact (fits in a single row, ~210px wide)
 *   - Non-intrusive when PSI is NORMAL (subdued green)
 *   - Loud when PSI escalates (red glow + pulsing ring)
 *
 * It piggybacks on the same `/api/pandemic-sensitivity` endpoint as the
 * detailed panel below — single HTTP call shared between both via a 5-min
 * polling cycle. If the call fails the gauge silently shows "—" and never
 * blocks the rest of the page.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Sparkles } from "lucide-react";
import { fetcher } from "../lib/api";

// ─── Types ───────────────────────────────────────────────────────────────────

interface PSIResponse {
  success: boolean;
  data: {
    psi_score: number;
    risk_level: "NORMAL" | "ELEVATED" | "WARNING" | "HIGH_RISK" | "CRITICAL";
    risk_color: string;
    summary: string;
    age_minutes: number;
  };
  error?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const LEVEL_LABELS: Record<string, string> = {
  NORMAL: "NORMAL",
  ELEVATED: "ELEVATED",
  WARNING: "WARNING",
  HIGH_RISK: "HIGH RISK",
  CRITICAL: "CRITICAL",
};

const LEVEL_DESCRIPTIONS: Record<string, string> = {
  NORMAL: "Baseline strategy",
  ELEVATED: "Stay alert",
  WARNING: "Reduce leverage",
  HIGH_RISK: "Defensive bias",
  CRITICAL: "Risk-off mode",
};

function levelColor(level: string): string {
  switch (level) {
    case "CRITICAL": return "#dc2626";
    case "HIGH_RISK": return "#ea580c";
    case "WARNING": return "#f59e0b";
    case "ELEVATED": return "#eab308";
    default: return "#16a34a";
  }
}

// Smoothly tween a numeric value over `duration` ms.
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
      const elapsed = ts - startRef.current;
      const t = Math.min(1, elapsed / duration);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setVal(fromRef.current + (target - fromRef.current) * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration]);

  return val;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function PSISpeedometer() {
  const [psi, setPsi] = useState<PSIResponse["data"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetcher<PSIResponse>("/api/pandemic-sensitivity");
        if (cancelled) return;
        if (res.success) {
          setPsi(res.data);
          setError(false);
        } else {
          setError(true);
        }
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 5 * 60 * 1000); // 5-min refresh
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const score = psi?.psi_score ?? 0;
  const level = psi?.risk_level ?? "NORMAL";
  const color = levelColor(level);
  const animatedScore = useAnimatedNumber(score, 1200);

  // Speedometer geometry — 240° arc (sweeps from 8 o'clock to 4 o'clock)
  const VB = 200;          // viewbox
  const CX = 100;
  const CY = 110;
  const R = 78;
  const START_ANGLE_DEG = 150;   // bottom-left
  const SWEEP_DEG = 240;         // total arc
  const END_ANGLE_DEG = START_ANGLE_DEG + SWEEP_DEG;

  const polar = (cx: number, cy: number, r: number, deg: number) => {
    const rad = ((deg - 180) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  };
  const arcPath = (r: number, startDeg: number, endDeg: number) => {
    const start = polar(CX, CY, r, startDeg);
    const end = polar(CX, CY, r, endDeg);
    const large = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`;
  };

  // Color band stops mapped to PSI thresholds
  const bands = useMemo(() => [
    { from: 0,   to: 20,  color: "#16a34a" }, // NORMAL
    { from: 20,  to: 40,  color: "#eab308" }, // ELEVATED
    { from: 40,  to: 60,  color: "#f59e0b" }, // WARNING
    { from: 60,  to: 80,  color: "#ea580c" }, // HIGH_RISK
    { from: 80,  to: 100, color: "#dc2626" }, // CRITICAL
  ], []);

  const needleDeg = useMemo(
    () => START_ANGLE_DEG + (Math.min(100, Math.max(0, animatedScore)) / 100) * SWEEP_DEG,
    [animatedScore],
  );

  const isElevated = level !== "NORMAL";
  const isCritical = level === "CRITICAL" || level === "HIGH_RISK";

  return (
    <div
      className="relative w-full flex items-center justify-center"
      title={psi?.summary ?? "Pandemic Sensitivity Index"}
    >
      {/* Outer card */}
      <div
        className={`
          relative inline-flex items-center gap-4 sm:gap-6
          px-4 sm:px-6 py-3 rounded-full
          bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950
          border transition-all duration-700
          ${isCritical ? "border-red-500/50 shadow-[0_0_28px_rgba(220,38,38,0.3)]" :
            isElevated ? "border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.18)]" :
            "border-purple-500/25 shadow-[0_0_18px_rgba(168,85,247,0.12)]"}
        `}
      >
        {/* Pulsing ring when CRITICAL */}
        {isCritical && (
          <span className="absolute inset-0 rounded-full border-2 border-red-500/40 animate-ping pointer-events-none" />
        )}

        {/* ── Speedometer dial ───────────────────────────────────── */}
        <div className="relative shrink-0" style={{ width: 130, height: 100 }}>
          <svg
            viewBox={`0 0 ${VB} 150`}
            className="w-full h-full overflow-visible"
            aria-label={`PSI gauge: ${Math.round(score)}, ${LEVEL_LABELS[level]}`}
          >
            {/* Color band */}
            {bands.map((b) => {
              const startDeg = START_ANGLE_DEG + (b.from / 100) * SWEEP_DEG;
              const endDeg = START_ANGLE_DEG + (b.to / 100) * SWEEP_DEG;
              return (
                <path
                  key={b.from}
                  d={arcPath(R, startDeg, endDeg)}
                  stroke={b.color}
                  strokeWidth="11"
                  strokeLinecap="butt"
                  fill="none"
                  opacity="0.75"
                />
              );
            })}

            {/* Outer ring stroke for crisp edge */}
            <path
              d={arcPath(R, START_ANGLE_DEG, END_ANGLE_DEG)}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="13"
              fill="none"
            />

            {/* Tick marks every 20 (major) */}
            {[0, 20, 40, 60, 80, 100].map((t) => {
              const deg = START_ANGLE_DEG + (t / 100) * SWEEP_DEG;
              const outer = polar(CX, CY, R + 7, deg);
              const inner = polar(CX, CY, R - 5, deg);
              return (
                <line
                  key={t}
                  x1={inner.x} y1={inner.y}
                  x2={outer.x} y2={outer.y}
                  stroke="rgba(255,255,255,0.55)"
                  strokeWidth="1.4"
                />
              );
            })}

            {/* Minor ticks every 10 */}
            {[10, 30, 50, 70, 90].map((t) => {
              const deg = START_ANGLE_DEG + (t / 100) * SWEEP_DEG;
              const outer = polar(CX, CY, R + 3, deg);
              const inner = polar(CX, CY, R - 2, deg);
              return (
                <line
                  key={t}
                  x1={inner.x} y1={inner.y}
                  x2={outer.x} y2={outer.y}
                  stroke="rgba(255,255,255,0.18)"
                  strokeWidth="1"
                />
              );
            })}

            {/* Major tick labels */}
            {[0, 50, 100].map((t) => {
              const deg = START_ANGLE_DEG + (t / 100) * SWEEP_DEG;
              const p = polar(CX, CY, R + 16, deg);
              return (
                <text
                  key={t}
                  x={p.x} y={p.y + 3}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="600"
                  fill="rgba(255,255,255,0.45)"
                >
                  {t}
                </text>
              );
            })}

            {/* Needle (rotates around hub) */}
            <g
              style={{
                transform: `rotate(${needleDeg - 90}deg)`,
                transformOrigin: `${CX}px ${CY}px`,
                transition: "transform 1.2s cubic-bezier(.2,.8,.2,1)",
              }}
            >
              {/* Needle shadow */}
              <polygon
                points={`${CX - 3},${CY + 4} ${CX + 3},${CY + 4} ${CX + 1},${CY - R + 10} ${CX - 1},${CY - R + 10}`}
                fill={color}
                opacity="0.95"
                style={{ filter: `drop-shadow(0 0 4px ${color})` }}
              />
              {/* Needle tip */}
              <circle cx={CX} cy={CY - R + 10} r="2" fill="#fff" opacity="0.8" />
            </g>

            {/* Center hub */}
            <circle cx={CX} cy={CY} r="8" fill="#0a0a0a" stroke={color} strokeWidth="2" />
            <circle cx={CX} cy={CY} r="3" fill={color} />
          </svg>

          {/* Score below the dial */}
          <div
            className="absolute left-0 right-0 text-center pointer-events-none"
            style={{ bottom: -4 }}
          >
            <div
              className="text-2xl font-extrabold tabular-nums leading-none"
              style={{ color, textShadow: `0 0 12px ${color}55` }}
            >
              {loading ? "—" : Math.round(animatedScore)}
            </div>
          </div>
        </div>

        {/* ── Label block ────────────────────────────────────────── */}
        <div className="min-w-0 flex-1 sm:flex-none">
          <div className="flex items-center gap-1.5 mb-0.5">
            <Activity className="w-3 h-3 text-purple-400" />
            <span className="text-[9px] font-bold uppercase tracking-[0.18em] text-purple-300">
              Pandemic Sensitivity
            </span>
            <Sparkles className="w-3 h-3 text-purple-400/70" />
          </div>
          <div
            className="text-base sm:text-lg font-extrabold tracking-wide leading-tight"
            style={{ color }}
          >
            {error ? "OFFLINE" : LEVEL_LABELS[level]}
          </div>
          <div className="text-[10px] text-gray-400 leading-tight max-w-[180px]">
            {error ? "PSI service unreachable" : LEVEL_DESCRIPTIONS[level]}
          </div>
        </div>
      </div>
    </div>
  );
}
