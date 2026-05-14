"use client";

/**
 * MacroGaugeStrip — Hero-row of 4 macro speedometers
 * ===================================================
 * Sits next to the PSI Speedometer at the top of the dashboard.
 *
 *   [ PSI ]  [ DXY ]  [ VIX ]  [ Yield Curve ]  [ Risk-On/Off ]
 *
 * Each gauge is a compact dome dial (matches PSI styling) with a hover tooltip
 * explaining what the indicator means and its directional impact on the four
 * tradeable symbols (NDX / XAU / DAX / WTI). Endpoint: `/api/macro-gauges`.
 *
 * Tooltip is a portal-free absolute card, positioned above the gauge with a
 * tail. Pure CSS / inline-styled, no external lib, works on touch (long-press
 * triggers focus state).
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { fetcher } from "../lib/api";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ThresholdRow {
  range: string;
  label: string;
  effect: string;
}

interface GaugeTooltip {
  title: string;
  summary: string;
  interpretation: string;
  thresholds: ThresholdRow[];
}

interface MacroGauge {
  key: string;
  label: string;
  subtitle?: string;
  status: "live" | "loading" | "error";
  value: number | null;
  z_score?: number | null;
  spread?: number | null;
  score: number;        // 0..100 needle position
  level: string;
  color: string;
  tooltip: GaugeTooltip;
}

interface MacroResponse {
  success: boolean;
  gauges: MacroGauge[];
}

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
  const c = Math.max(0, Math.min(100, score));
  return -HALF_SWEEP + (c / 100) * SWEEP;
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

// ─── Single gauge ────────────────────────────────────────────────────────────

const BAND_COLORS = ["#16a34a", "#84cc16", "#eab308", "#f59e0b", "#ea580c", "#dc2626"];

function GaugeCard({ gauge }: { gauge: MacroGauge }) {
  const [hover, setHover] = useState(false);
  const score = gauge.score ?? 50;
  const animatedScore = useAnimatedNumber(score, 1100);
  const needleDeg = useMemo(() => angleFromScore(animatedScore), [animatedScore]);
  const isLoading = gauge.status === "loading";
  const isError = gauge.status === "error";

  // Display number: prefer raw value, fall back to z-score, else "—"
  const display =
    isLoading || isError
      ? "…"
      : gauge.value !== null && gauge.value !== undefined
      ? formatValue(gauge)
      : "—";

  return (
    <div
      className="relative inline-flex flex-col items-center"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onFocus={() => setHover(true)}
      onBlur={() => setHover(false)}
      tabIndex={0}
    >
      {/* Tooltip */}
      {hover && !isLoading && (
        <Tooltip gauge={gauge} />
      )}

      <div
        className={`
          inline-flex items-center gap-2 px-3 py-2 rounded-2xl
          bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950
          border transition-all duration-500 cursor-help
          ${isError ? "border-gray-700/50" :
            isLoading ? "border-gray-700/40" :
            "border-white/10 hover:border-white/20"}
        `}
        style={{
          boxShadow: !isLoading && !isError ? `0 0 14px ${gauge.color}22` : undefined,
        }}
      >
        {/* Mini dome dial */}
        <div className="relative shrink-0" style={{ width: 90, height: 60 }}>
          <svg viewBox="0 0 200 130" className="w-full h-full overflow-visible">
            {/* Background track */}
            <path
              d={arcPath(R, -HALF_SWEEP, HALF_SWEEP)}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="14"
              fill="none"
            />
            {/* 5-band rainbow */}
            {BAND_COLORS.slice(0, 5).map((c, i) => {
              const start = -HALF_SWEEP + (i / 5) * SWEEP;
              const end = -HALF_SWEEP + ((i + 1) / 5) * SWEEP;
              return (
                <path
                  key={i}
                  d={arcPath(R, start, end)}
                  stroke={c}
                  strokeWidth="10"
                  fill="none"
                  opacity={isLoading || isError ? 0.18 : 0.75}
                />
              );
            })}
            {/* Major ticks */}
            {[0, 25, 50, 75, 100].map((t) => {
              const deg = -HALF_SWEEP + (t / 100) * SWEEP;
              const o = pointAt(R + 6, deg);
              const i = pointAt(R - 4, deg);
              return (
                <line key={t} x1={i.x} y1={i.y} x2={o.x} y2={o.y}
                      stroke="rgba(255,255,255,0.4)" strokeWidth="1.4" />
              );
            })}
            {/* Needle */}
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
            <circle cx={CX} cy={CY} r="7" fill="#0a0a0a"
                    stroke={isLoading || isError ? "#374151" : gauge.color} strokeWidth="2" />
            <circle cx={CX} cy={CY} r="2.5" fill={isLoading || isError ? "#374151" : gauge.color} />
          </svg>
        </div>

        {/* Right text block */}
        <div className="min-w-0">
          <div className="text-[8px] font-bold uppercase tracking-[0.16em] text-gray-400 leading-tight">
            {gauge.label}
          </div>
          <div
            className="text-[15px] font-extrabold tabular-nums leading-tight"
            style={{ color: isLoading || isError ? "#9ca3af" : gauge.color }}
          >
            {display}
          </div>
          <div className="text-[9px] text-gray-500 leading-tight uppercase tracking-wider">
            {isLoading ? "…" : isError ? "ERR" : gauge.level}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Tooltip card ────────────────────────────────────────────────────────────

function Tooltip({ gauge }: { gauge: MacroGauge }) {
  return (
    <div
      className="absolute z-50 pointer-events-none"
      style={{
        bottom: "calc(100% + 12px)",
        left: "50%",
        transform: "translateX(-50%)",
        width: 320,
      }}
    >
      <div
        className="rounded-xl border border-white/10 bg-gradient-to-br from-gray-950 to-gray-900 p-3 shadow-2xl backdrop-blur-sm"
        style={{ boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 18px ${gauge.color}22` }}
      >
        <div className="flex items-center justify-between mb-1.5">
          <div className="text-[11px] font-bold text-white">{gauge.tooltip.title}</div>
          <span
            className="text-[9px] font-bold px-1.5 py-0.5 rounded"
            style={{ background: `${gauge.color}22`, color: gauge.color }}
          >
            {gauge.level}
          </span>
        </div>

        <div className="text-[10px] text-gray-400 leading-snug mb-2">
          {gauge.tooltip.summary}
        </div>

        {(gauge.value !== null || gauge.z_score !== null) && (
          <div className="flex gap-2 mb-2 text-[10px]">
            {gauge.value !== null && (
              <div className="flex-1 rounded bg-white/5 px-2 py-1">
                <div className="text-gray-500 uppercase text-[8px] tracking-wider">Value</div>
                <div className="font-bold text-white tabular-nums">{gauge.value}</div>
              </div>
            )}
            {gauge.z_score !== null && gauge.z_score !== undefined && (
              <div className="flex-1 rounded bg-white/5 px-2 py-1">
                <div className="text-gray-500 uppercase text-[8px] tracking-wider">Z-Score</div>
                <div className="font-bold text-white tabular-nums">
                  {gauge.z_score > 0 ? "+" : ""}{gauge.z_score}σ
                </div>
              </div>
            )}
          </div>
        )}

        <div
          className="rounded px-2 py-1.5 mb-2 border-l-2 text-[10px] text-gray-200 leading-snug"
          style={{ borderColor: gauge.color, background: `${gauge.color}10` }}
        >
          <span className="font-semibold" style={{ color: gauge.color }}>Direction bias: </span>
          {gauge.tooltip.interpretation}
        </div>

        {gauge.tooltip.thresholds && gauge.tooltip.thresholds.length > 0 && (
          <div>
            <div className="text-[9px] uppercase tracking-wider text-gray-500 mb-1 font-bold">
              Threshold map
            </div>
            <div className="space-y-0.5">
              {gauge.tooltip.thresholds.map((t, i) => (
                <div key={i} className="flex items-baseline gap-1.5 text-[9.5px] leading-tight">
                  <span className="text-gray-500 tabular-nums shrink-0 font-mono">{t.range}</span>
                  <span className="font-bold text-gray-200 shrink-0">{t.label}</span>
                  <span className="text-gray-400">— {t.effect}</span>
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
          bottom: -6,
          transform: "translateX(-50%) rotate(45deg)",
          width: 12,
          height: 12,
          background: "linear-gradient(135deg, transparent 50%, rgb(17 24 39) 50%)",
          borderRight: "1px solid rgba(255,255,255,0.10)",
          borderBottom: "1px solid rgba(255,255,255,0.10)",
        }}
      />
    </div>
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
          // Show error placeholders, keep retrying every 60s
          setGauges([
            placeholder("dxy", "DXY Pulse"),
            placeholder("vix", "VIX Fear"),
            placeholder("yield_curve", "Yield Curve"),
            placeholder("risk_ratio", "Risk-On / Off"),
          ]);
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

  const list: MacroGauge[] = gauges ?? [
    loadingPlaceholder("dxy", "DXY Pulse"),
    loadingPlaceholder("vix", "VIX Fear"),
    loadingPlaceholder("yield_curve", "Yield Curve"),
    loadingPlaceholder("risk_ratio", "Risk-On / Off"),
  ];

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
      {list.map((g) => (
        <GaugeCard key={g.key} gauge={g} />
      ))}
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

function loadingPlaceholder(key: string, label: string): MacroGauge {
  return {
    key, label, status: "loading", value: null, score: 50,
    level: "LOADING", color: "#6b7280",
    tooltip: { title: label, summary: "Loading…", interpretation: "", thresholds: [] },
  };
}

function placeholder(key: string, label: string): MacroGauge {
  return {
    key, label, status: "error", value: null, score: 50,
    level: "OFFLINE", color: "#6b7280",
    tooltip: { title: label, summary: "Service unreachable.", interpretation: "Retrying…", thresholds: [] },
  };
}
