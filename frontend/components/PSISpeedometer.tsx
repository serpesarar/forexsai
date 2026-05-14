"use client";

/**
 * PSI Speedometer — Classic car-dashboard gauge
 * =============================================
 * Shape: 240° arc forming a dome at the TOP, opening at the BOTTOM
 * (the way a real automotive speedometer is drawn). Needle pivots from
 * the bottom-center hub and sweeps over the top arc.
 *
 *      ┌──── colored arc dome (top) ────┐
 *      │                                │
 *      └──────  open bottom  ───────────┘
 *                  ● hub
 *
 * Robustness:
 *   - Three quick retries on first mount (2s → 5s → 10s)
 *   - Distinct LOADING / WARMING / OFFLINE / LIVE states
 *   - Re-checks every 5 minutes once healthy, every 60 seconds while degraded
 *   - Works on the public `/api/pandemic-sensitivity` endpoint shared with the
 *     full panel below — no extra HTTP traffic.
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

type Status = "loading" | "live" | "warming" | "offline";

// ─── Constants ───────────────────────────────────────────────────────────────

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

// ─── Animated number tween ───────────────────────────────────────────────────

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

// ─── Geometry helpers ────────────────────────────────────────────────────────
//
// Angle convention: 0° = top (12 o'clock), increasing clockwise.
// Needle sweep: -120° (lower-left, 8 o'clock) → +120° (lower-right, 4 o'clock).
// That gives a 240° dome on TOP with the bottom 120° open — the classic
// automotive speedometer shape.

const SWEEP = 240;       // total arc degrees
const HALF_SWEEP = SWEEP / 2;  // ±120° from top
const CX = 100;
const CY = 100;
const R = 78;

function angleFromScore(score: number): number {
  const clamped = Math.max(0, Math.min(100, score));
  return -HALF_SWEEP + (clamped / 100) * SWEEP;
}

function pointAt(r: number, deg: number): { x: number; y: number } {
  const rad = (deg * Math.PI) / 180;
  return { x: CX + r * Math.sin(rad), y: CY - r * Math.cos(rad) };
}

function arcPath(r: number, startDeg: number, endDeg: number): string {
  const start = pointAt(r, startDeg);
  const end = pointAt(r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function PSISpeedometer() {
  const [psi, setPsi] = useState<PSIResponse["data"] | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  // Robust fetcher: 3 quick retries on first failure, then 5-min cycle
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const load = async (attempt = 0): Promise<void> => {
      try {
        const res = await fetcher<PSIResponse>("/api/pandemic-sensitivity");
        if (cancelled) return;
        if (res.success && res.data) {
          setPsi(res.data);
          // Backend returns psi_score=0 + summary "not yet ready" while warming.
          const warming = !res.data.psi_score && /not yet ready|warming/i.test(res.data.summary || "");
          setStatus(warming ? "warming" : "live");
          timer = setTimeout(() => load(0), warming ? 30_000 : 5 * 60_000);
        } else {
          throw new Error(res.error || "PSI service returned success=false");
        }
      } catch {
        if (cancelled) return;
        if (attempt < 3) {
          // 2s → 5s → 10s back-off; remain in loading state during retries
          const delays = [2_000, 5_000, 10_000];
          timer = setTimeout(() => load(attempt + 1), delays[attempt]);
        } else {
          setStatus("offline");
          // While offline, retry every 60s instead of 5 min
          timer = setTimeout(() => load(0), 60_000);
        }
      }
    };

    load(0);
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  const score = psi?.psi_score ?? 0;
  const level = psi?.risk_level ?? "NORMAL";
  const color = levelColor(level);
  const animatedScore = useAnimatedNumber(score, 1200);
  const needleDeg = useMemo(() => angleFromScore(animatedScore), [animatedScore]);

  // Color bands aligned to risk thresholds
  const bands = useMemo(() => [
    { from: 0,   to: 20,  color: "#16a34a" },
    { from: 20,  to: 40,  color: "#eab308" },
    { from: 40,  to: 60,  color: "#f59e0b" },
    { from: 60,  to: 80,  color: "#ea580c" },
    { from: 80,  to: 100, color: "#dc2626" },
  ], []);

  const isOffline = status === "offline";
  const isWarming = status === "warming";
  const isLoading = status === "loading";
  const isElevated = !isOffline && !isLoading && level !== "NORMAL";
  const isCritical = !isOffline && (level === "CRITICAL" || level === "HIGH_RISK");

  return (
    <div className="relative w-full flex items-center justify-center" title={psi?.summary ?? "Pandemic Sensitivity Index"}>
      <div
        className={`
          relative inline-flex items-center gap-4 sm:gap-6
          px-5 sm:px-7 py-3 rounded-full
          bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950
          border transition-all duration-700
          ${isOffline ? "border-gray-700/60 shadow-[0_0_18px_rgba(75,85,99,0.18)]" :
            isCritical ? "border-red-500/50 shadow-[0_0_28px_rgba(220,38,38,0.3)]" :
            isElevated ? "border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.18)]" :
            "border-purple-500/25 shadow-[0_0_18px_rgba(168,85,247,0.12)]"}
        `}
      >
        {isCritical && (
          <span className="absolute inset-0 rounded-full border-2 border-red-500/40 animate-ping pointer-events-none" />
        )}

        {/* ═══ Speedometer dial ═══ */}
        <div className="relative shrink-0" style={{ width: 150, height: 96 }}>
          <svg
            viewBox="0 0 200 130"
            className="w-full h-full overflow-visible"
            aria-label={`PSI gauge: ${Math.round(score)}, ${LEVEL_LABELS[level]}`}
          >
            {/* Outer bezel — soft glow ring giving the "glass dial" look */}
            <path
              d={arcPath(R + 9, -HALF_SWEEP, HALF_SWEEP)}
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="1.5"
              fill="none"
            />

            {/* Background track (full sweep, dark) */}
            <path
              d={arcPath(R, -HALF_SWEEP, HALF_SWEEP)}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="14"
              strokeLinecap="round"
              fill="none"
            />

            {/* Color bands */}
            {bands.map((b) => {
              const startDeg = -HALF_SWEEP + (b.from / 100) * SWEEP;
              const endDeg = -HALF_SWEEP + (b.to / 100) * SWEEP;
              return (
                <path
                  key={b.from}
                  d={arcPath(R, startDeg, endDeg)}
                  stroke={b.color}
                  strokeWidth="11"
                  strokeLinecap="butt"
                  fill="none"
                  opacity={isOffline ? 0.18 : 0.85}
                />
              );
            })}

            {/* Major ticks (0,20,40,60,80,100) */}
            {[0, 20, 40, 60, 80, 100].map((t) => {
              const deg = -HALF_SWEEP + (t / 100) * SWEEP;
              const outer = pointAt(R + 8, deg);
              const inner = pointAt(R - 6, deg);
              return (
                <line
                  key={t}
                  x1={inner.x} y1={inner.y}
                  x2={outer.x} y2={outer.y}
                  stroke="rgba(255,255,255,0.55)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              );
            })}

            {/* Minor ticks every 10 */}
            {[10, 30, 50, 70, 90].map((t) => {
              const deg = -HALF_SWEEP + (t / 100) * SWEEP;
              const outer = pointAt(R + 3, deg);
              const inner = pointAt(R - 2, deg);
              return (
                <line
                  key={t}
                  x1={inner.x} y1={inner.y}
                  x2={outer.x} y2={outer.y}
                  stroke="rgba(255,255,255,0.22)"
                  strokeWidth="1"
                />
              );
            })}

            {/* Numeric labels at 0 / 50 / 100 */}
            {[0, 50, 100].map((t) => {
              const deg = -HALF_SWEEP + (t / 100) * SWEEP;
              const p = pointAt(R - 16, deg);
              return (
                <text
                  key={t}
                  x={p.x} y={p.y + 3}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="700"
                  fill="rgba(255,255,255,0.55)"
                >
                  {t}
                </text>
              );
            })}

            {/* Needle — rotates around bottom-center hub */}
            <g
              style={{
                transform: `rotate(${isOffline ? -HALF_SWEEP : needleDeg}deg)`,
                transformOrigin: `${CX}px ${CY}px`,
                transition: "transform 1.2s cubic-bezier(.2,.8,.2,1)",
                opacity: isLoading ? 0.4 : 1,
              }}
            >
              <polygon
                points={`${CX - 2.5},${CY + 6} ${CX + 2.5},${CY + 6} ${CX + 0.8},${CY - R + 6} ${CX - 0.8},${CY - R + 6}`}
                fill={isOffline ? "#6b7280" : color}
                opacity="0.95"
                style={{ filter: isOffline ? "none" : `drop-shadow(0 0 4px ${color})` }}
              />
              <circle cx={CX} cy={CY - R + 6} r="2" fill="#fff" opacity="0.85" />
            </g>

            {/* Hub — center cap */}
            <circle cx={CX} cy={CY} r="9" fill="#0a0a0a" stroke={isOffline ? "#374151" : color} strokeWidth="2" />
            <circle cx={CX} cy={CY} r="3.5" fill={isOffline ? "#374151" : color} />
          </svg>

          {/* Score readout below the hub */}
          <div className="absolute left-0 right-0 text-center pointer-events-none" style={{ bottom: 0 }}>
            <div
              className="text-[22px] font-extrabold tabular-nums leading-none"
              style={{
                color: isOffline ? "#9ca3af" : color,
                textShadow: isOffline ? "none" : `0 0 12px ${color}55`,
              }}
            >
              {isLoading ? "…" : isOffline ? "—" : Math.round(animatedScore)}
            </div>
          </div>
        </div>

        {/* ═══ Label block ═══ */}
        <div className="min-w-0 flex-1 sm:flex-none">
          <div className="flex items-center gap-1.5 mb-0.5">
            <Activity className={`w-3 h-3 ${isOffline ? "text-gray-500" : "text-purple-400"}`} />
            <span className={`text-[9px] font-bold uppercase tracking-[0.18em] ${isOffline ? "text-gray-500" : "text-purple-300"}`}>
              Pandemic Sensitivity
            </span>
            <Sparkles className={`w-3 h-3 ${isOffline ? "text-gray-600" : "text-purple-400/70"}`} />
          </div>
          <div
            className="text-base sm:text-lg font-extrabold tracking-wide leading-tight"
            style={{ color: isOffline ? "#9ca3af" : color }}
          >
            {isLoading ? "LOADING…" : isWarming ? "WARMING UP" : isOffline ? "OFFLINE" : LEVEL_LABELS[level]}
          </div>
          <div className="text-[10px] text-gray-400 leading-tight max-w-[220px]">
            {isLoading ? "Fetching basket data…" :
             isWarming ? "Baskets initialising — first 60s" :
             isOffline ? "Service unreachable, retrying…" :
             LEVEL_DESCRIPTIONS[level]}
          </div>
        </div>
      </div>
    </div>
  );
}
