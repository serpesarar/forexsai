"use client";

import { useMemo, useRef, useEffect, useState, useCallback } from "react";
import { Eye, EyeOff, Grid3X3, Layers } from "lucide-react";

interface TrendChannelChartProps {
  closes: number[];
  dates?: string[];
  upper: number[];
  lower: number[];
  middle: number[];
  supportLevels: { price: number; label: string; strength?: string }[];
  resistanceLevels: { price: number; label: string; strength?: string }[];
  currentPrice: number;
  decimals: number;
  supportProximity: boolean;
  resistanceProximity: boolean;
  supportIntensity: number;
  resistanceIntensity: number;
}

const BASE_W = 900;
const BASE_H = 420;
const PAD = { top: 20, right: 90, bottom: 75, left: 10 };

export default function TrendChannelChart({
  closes,
  dates,
  upper,
  lower,
  middle,
  supportLevels,
  resistanceLevels,
  currentPrice,
  decimals,
  supportProximity,
  resistanceProximity,
  supportIntensity,
  resistanceIntensity,
}: TrendChannelChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [tick, setTick] = useState(0);

  // Visibility Toggles
  const [showSR, setShowSR] = useState(true);
  const [showGrid, setShowGrid] = useState(true);

  // Constants for Neon Colors
  const NEON_RED = "#ff0040";
  const NEON_CYAN = "#00f0ff";

  // Data-window scrolling: offset = how many candles scrolled back from end
  const VISIBLE_CANDLES = 60;
  const totalCandles = closes.length;
  const maxOffset = Math.max(0, totalCandles - VISIBLE_CANDLES);
  const [scrollOffset, setScrollOffset] = useState(0); // 0 = most recent
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, offset: 0 });

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1200);
    return () => clearInterval(id);
  }, []);

  // Mouse handlers for horizontal scroll through data
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    dragStart.current = { x: e.clientX, offset: scrollOffset };
  }, [scrollOffset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.current.x;
    // Each 8px of drag = 1 candle scroll
    const candleShift = Math.round(dx / 8);
    const newOffset = Math.max(0, Math.min(maxOffset, dragStart.current.offset + candleShift));
    setScrollOffset(newOffset);
  }, [isDragging, maxOffset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Scroll wheel = horizontal scroll through candles
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -3 : 3; // scroll down = go back, up = go forward
    setScrollOffset(prev => Math.max(0, Math.min(maxOffset, prev + delta)));
  }, [maxOffset]);

  // Touch handlers for mobile swipe
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setIsDragging(true);
      dragStart.current = { x: e.touches[0].clientX, offset: scrollOffset };
    }
  }, [scrollOffset]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1 && isDragging) {
      const dx = e.touches[0].clientX - dragStart.current.x;
      const candleShift = Math.round(dx / 8);
      const newOffset = Math.max(0, Math.min(maxOffset, dragStart.current.offset + candleShift));
      setScrollOffset(newOffset);
    }
  }, [isDragging, maxOffset]);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Double-click to reset to latest
  const handleDoubleClick = useCallback(() => {
    setScrollOffset(0);
  }, []);

  // Slice visible data window based on scrollOffset
  const visibleWindow = useMemo(() => {
    const end = totalCandles - scrollOffset;
    const start = Math.max(0, end - VISIBLE_CANDLES);
    return {
      closes: closes.slice(start, end),
      dates: dates ? dates.slice(start, end) : [],
      upper: upper.slice(start, end),
      lower: lower.slice(start, end),
      middle: middle.slice(start, end),
      start, end,
      isAtLatest: scrollOffset === 0,
    };
  }, [closes, dates, upper, lower, middle, totalCandles, scrollOffset]);

  const computed = useMemo(() => {
    const vc = visibleWindow.closes;
    const vd = visibleWindow.dates;
    const vu = visibleWindow.upper;
    const vl = visibleWindow.lower;
    const vm = visibleWindow.middle;
    if (!vc.length) return null;

    // Y-axis auto-scales to VISIBLE data only
    const visiblePrices = [
      ...vc, ...vu, ...vl,
      ...supportLevels.map((s) => s.price),
      ...resistanceLevels.map((r) => r.price),
      ...(visibleWindow.isAtLatest ? [currentPrice] : []),
    ].filter((v) => v > 0);

    const rawMin = Math.min(...visiblePrices);
    const rawMax = Math.max(...visiblePrices);
    const pad = (rawMax - rawMin) * 0.06;
    const minP = rawMin - pad;
    const maxP = rawMax + pad;
    const range = maxP - minP || 1;

    const plotW = BASE_W - PAD.left - PAD.right;
    const plotH = BASE_H - PAD.top - PAD.bottom;

    const xScale = (i: number) => PAD.left + (i / Math.max(1, vc.length - 1)) * plotW;
    const yScale = (price: number) => PAD.top + plotH - ((price - minP) / range) * plotH;

    const pricePts = vc.map((c, i) => `${xScale(i)},${yScale(c)}`);
    // Extend line to currentPrice when viewing latest data
    const lastIdx = vc.length - 1;
    const extendedPricePts = visibleWindow.isAtLatest
      ? [...pricePts, `${xScale(lastIdx)},${yScale(currentPrice)}`]
      : pricePts;
    const pricePath = `M${extendedPricePts.join("L")}`;
    const areaPath = `${pricePath}L${xScale(lastIdx)},${BASE_H - PAD.bottom}L${xScale(0)},${BASE_H - PAD.bottom}Z`;

    const makePath = (arr: number[]) => {
      if (!arr.length) return "";
      return `M${arr.map((v, i) => `${xScale(i)},${yScale(v)}`).join("L")}`;
    };

    let channelFillPath = "";
    if (vu.length && vl.length) {
      const upPts = vu.map((v, i) => `${xScale(i)},${yScale(v)}`).join("L");
      const downPts = [...vl].reverse().map((v, i) => `${xScale(vl.length - 1 - i)},${yScale(v)}`).join("L");
      channelFillPath = `M${upPts}L${downPts}Z`;
    }

    const gridCount = 6;
    const gridLines: { y: number; price: number }[] = [];
    for (let i = 0; i <= gridCount; i++) {
      const price = minP + (range * i) / gridCount;
      gridLines.push({ y: yScale(price), price });
    }

    // Compute X-axis labels (dates) - pick ~6 evenly spaced
    const xLabels: { x: number; label: string }[] = [];
    if (vd.length > 0) {
      const step = Math.max(1, Math.floor(vd.length / 6));
      for (let i = 0; i < vd.length; i += step) {
        if (i < vd.length) {
          xLabels.push({ x: xScale(i), label: vd[i] });
        }
      }
      // Ensure last one is included if space permits
      if (vd.length > 0 && xLabels[xLabels.length - 1].label !== vd[vd.length - 1]) {
        xLabels.push({ x: xScale(vd.length - 1), label: vd[vd.length - 1] });
      }
    }

    return {
      pricePath, areaPath,
      upperPath: makePath(vu),
      lowerPath: makePath(vl),
      middlePath: makePath(vm),
      channelFillPath,
      yScale, xScale, minP, maxP, gridLines, xLabels,
      lastX: xScale(vc.length - 1),
    };
  }, [visibleWindow, supportLevels, resistanceLevels, currentPrice, decimals]);

  // Calculate Touch Points (Where price touched S/R levels)
  // Note: Using 'closes' as proxy for High/Low since full OHLC is not available in props
  const touchPoints = useMemo(() => {
    if (!closes || closes.length === 0) return [];

    // Helper to check touch
    const isTouch = (price: number, level: number) => Math.abs(price - level) / level <= 0.001; // 0.1% tolerance

    const points: { x: number; y: number; color: string; key: string }[] = [];
    // Only check visible window + some buffer for context, or just full visible window
    // User asked for "historical touch points", let's show them on the visible portion
    const startIdx = visibleWindow.start;
    const endIdx = visibleWindow.end;
    const windowCloses = visibleWindow.closes;

    // We need to map visible index to x-coordinate
    // visibleWindow.closes[0] corresponds to index 0 in the current view

    if (!computed) return [];

    const { xScale, yScale } = computed;

    // Support touches
    supportLevels.forEach((s, lvlIdx) => {
      windowCloses.forEach((price, i) => {
        if (isTouch(price, s.price)) {
          const x = xScale(i);
          const y = yScale(s.price);
          if (x >= 0 && x <= BASE_W) {
            points.push({ x, y, color: NEON_CYAN, key: `s-${lvlIdx}-${i}` });
          }
        }
      });
    });

    // Resistance touches
    resistanceLevels.forEach((r, lvlIdx) => {
      windowCloses.forEach((price, i) => {
        if (isTouch(price, r.price)) {
          const x = xScale(i);
          const y = yScale(r.price);
          if (x >= 0 && x <= BASE_W) {
            points.push({ x, y, color: NEON_RED, key: `r-${lvlIdx}-${i}` });
          }
        }
      });
    });

    return points;
  }, [visibleWindow, supportLevels, resistanceLevels, computed]); // Depend on computed for scales

  if (!computed) return null;

  const { pricePath, areaPath, upperPath, lowerPath, middlePath, channelFillPath, yScale, lastX, gridLines, xLabels } = computed;
  const pulse = Math.sin(tick * Math.PI * 0.8);
  // Make pulse stronger and faster for S/R lines as requested
  const srPulse = 0.5 + Math.sin(tick * Math.PI * 1.5) * 0.4;

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-2xl select-none"
      style={{ background: "rgba(2,6,23,0.7)", cursor: isDragging ? "grabbing" : "grab" }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onDoubleClick={handleDoubleClick}
    >
      {/* Global styles for animations */}
      <style jsx>{`
        @keyframes neonPulse {
          0%, 100% { opacity: 0.7; filter: brightness(1) drop-shadow(0 0 2px rgba(0,0,0,0.5)); }
          50% { opacity: 1; filter: brightness(1.2) drop-shadow(0 0 5px rgba(0,0,0,0.5)); }
        }
        @keyframes ripple {
          0% { transform: scale(1); opacity: 0.8; stroke-width: 2px; }
          100% { transform: scale(3); opacity: 0; stroke-width: 0px; }
        }
        .neon-pulse { animation: neonPulse 1.5s ease-in-out infinite; }
        .ripple-effect { animation: ripple 1.5s ease-out infinite; transform-origin: center; transform-box: fill-box; }
      `}</style>
      {/* Scroll controls */}
      <div className="absolute top-2 left-2 z-10 flex items-center gap-1">
        <button
          onClick={(e) => { e.stopPropagation(); setScrollOffset(prev => Math.min(maxOffset, prev + 20)); }}
          className="w-7 h-7 rounded-md flex items-center justify-center text-sm font-bold font-mono transition-all hover:brightness-150"
          style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}
          title="Scroll back in time"
        >◀</button>
        <button
          onClick={(e) => { e.stopPropagation(); setScrollOffset(prev => Math.max(0, prev - 20)); }}
          className="w-7 h-7 rounded-md flex items-center justify-center text-sm font-bold font-mono transition-all hover:brightness-150"
          style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}
          title="Scroll forward in time"
        >▶</button>
        {scrollOffset > 0 && (
          <button
            onClick={(e) => { e.stopPropagation(); setScrollOffset(0); }}
            className="h-7 px-2 rounded-md flex items-center justify-center text-[10px] font-bold font-mono transition-all hover:brightness-150"
            style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.1)" }}
          >↻ Son</button>
        )}
        {scrollOffset > 0 && (
          <span className="text-[9px] font-mono ml-1" style={{ color: "rgba(255,255,255,0.35)" }}>
            -{scrollOffset} bar
          </span>
        )}
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${BASE_W} ${BASE_H}`}
        className="w-full"
        style={{ height: "100%", minHeight: 280 }}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <filter id="tcPriceGlow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="tcSupportGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feFlood floodColor="#00f0ff" floodOpacity="0.6" result="color" />
            <feComposite in="color" in2="blur" operator="in" result="glow" />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="tcResistGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feFlood floodColor="#ff0040" floodOpacity="0.6" result="color" />
            <feComposite in="color" in2="blur" operator="in" result="glow" />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="tcSRNeonGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="tcTagGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="tcBeamGlow">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <linearGradient id="tcAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00ff88" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#00ff88" stopOpacity="0.01" />
          </linearGradient>
          <linearGradient id="tcChannelFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.08" />
            <stop offset="50%" stopColor="#6366f1" stopOpacity="0.03" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.08" />
          </linearGradient>
          <radialGradient id="tcDotGlow">
            <stop offset="0%" stopColor="#00ff88" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#00ff88" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Background grid */}
        {gridLines.map((g, i) => (
          <g key={`grid-${i}`}>
            <line x1={PAD.left} y1={g.y} x2={BASE_W - PAD.right} y2={g.y} stroke="rgba(255,255,255,0.04)" strokeWidth={1} />
            <text x={BASE_W - PAD.right + 6} y={g.y + 4} fill="rgba(255,255,255,0.18)" fontSize={9} fontFamily="monospace">
              {g.price.toFixed(decimals)}
            </text>
          </g>
        ))}

        {/* ══ VERTICAL BEAM LINES at date positions - bright pulsing rays ══ */}
        {showGrid && xLabels.map((l, i) => (
          <g key={`vgl-${i}`}>
            {/* Wide neon glow behind the beam - softer breathing pulse */}
            <line
              x1={l.x} y1={PAD.top}
              x2={l.x} y2={BASE_H - PAD.bottom}
              stroke="#22d3ee"
              strokeWidth={4}
              filter="url(#tcBeamGlow)"
              opacity={0.6}
            >
              <animate
                attributeName="opacity"
                values="0.3;0.6;0.3"
                dur="4s"
                begin={`${i * 0.5}s`}
                repeatCount="indefinite"
              />
            </line>
            {/* Core bright beam line - very thin but pure white/cyan mix */}
            <line
              x1={l.x} y1={PAD.top}
              x2={l.x} y2={BASE_H - PAD.bottom}
              stroke="#ccfbf1"
              strokeWidth={1}
            >
              <animate
                attributeName="opacity"
                values="0.6;0.9;0.6"
                dur="4s"
                begin={`${i * 0.5}s`}
                repeatCount="indefinite"
              />
            </line>
          </g>
        ))}

        {/* ══ DATE AXIS SEPARATOR LINE ══ */}
        <line
          x1={PAD.left} y1={BASE_H - PAD.bottom}
          x2={BASE_W - PAD.right} y2={BASE_H - PAD.bottom}
          stroke="rgba(56,189,248,0.3)"
          strokeWidth={1.5}
        />

        {/* ══ X-AXIS DATE LABELS with tick marks ══ */}
        {xLabels.map((l, i) => (
          <g key={`xl-${i}`}>
            {/* Tick mark down from separator */}
            <line
              x1={l.x} y1={BASE_H - PAD.bottom}
              x2={l.x} y2={BASE_H - PAD.bottom + 10}
              stroke="rgba(56,189,248,0.5)"
              strokeWidth={1.5}
            />
            {/* Date label */}
            <text
              x={l.x}
              y={BASE_H - PAD.bottom + 26}
              textAnchor="middle"
              fill="rgba(255,255,255,0.95)"
              fontSize={11.5}
              fontWeight="700"
              fontFamily="monospace"
              style={{ textShadow: "0 0 8px rgba(56,189,248,0.4), 0 0 3px rgba(0,0,0,1)" }}
            >
              {l.label}
            </text>
          </g>
        ))}

        {/* Channel fill */}
        {channelFillPath && <path d={channelFillPath} fill="url(#tcChannelFill)" />}
        {/* Upper channel */}
        <path d={upperPath} fill="none" stroke="#6366f1" strokeWidth={1.5} opacity={0.5} />
        {/* Lower channel */}
        <path d={lowerPath} fill="none" stroke="#6366f1" strokeWidth={1.5} opacity={0.5} />
        {/* Middle regression */}
        <path d={middlePath} fill="none" stroke="#6366f1" strokeWidth={1} strokeDasharray="6 4" opacity={0.3} />

        {/* ══ RESISTANCE LEVELS - Neon Red Pulse ══ */}
        {showSR && resistanceLevels.map((r, i) => {
          const y = yScale(r.price);
          if (y < PAD.top - 5 || y > BASE_H - PAD.bottom + 5) return null;
          const isStrong = r.strength === "strong";
          const proxGlow = resistanceProximity;
          return (
            <g key={`rl-${i}`} className="neon-pulse">
              {/* Always-on subtle neon glow zone */}
              <rect
                x={PAD.left} y={y - 12}
                width={BASE_W - PAD.left - PAD.right} height={24}
                fill={NEON_RED}
                opacity={proxGlow ? resistanceIntensity * 0.1 : srPulse * 0.05}
              />
              {/* Main Line with Strong Sharp Glow */}
              <line
                x1={PAD.left} y1={y} x2={BASE_W - PAD.right} y2={y}
                stroke={NEON_RED}
                strokeWidth={2}
                opacity={1}
                filter="url(#tcResistGlow)"
              />
              {/* Price tag */}
              <rect
                x={BASE_W - PAD.right + 2} y={y - 11}
                width={84} height={22} rx={4}
                fill="rgba(255,0,64,0.15)"
                stroke={NEON_RED} strokeWidth={1}
                filter="url(#tcTagGlow)"
              />
              <text
                x={BASE_W - PAD.right + 8} y={y + 4}
                fill={NEON_RED} fontSize={10.5} fontFamily="monospace" fontWeight="bold"
              >
                {r.label} {r.price.toFixed(decimals)}
              </text>
            </g>
          );
        })}

        {/* ══ SUPPORT LEVELS - Neon Cyan Pulse ══ */}
        {showSR && supportLevels.map((s, i) => {
          const y = yScale(s.price);
          if (y < PAD.top - 5 || y > BASE_H - PAD.bottom + 5) return null;
          const isStrong = s.strength === "strong";
          const proxGlow = supportProximity;
          return (
            <g key={`sl-${i}`} className="neon-pulse">
              <rect
                x={PAD.left} y={y - 12}
                width={BASE_W - PAD.left - PAD.right} height={24}
                fill={NEON_CYAN}
                opacity={proxGlow ? supportIntensity * 0.1 : srPulse * 0.05}
              />
              {/* Main Line with Strong Sharp Glow */}
              <line
                x1={PAD.left} y1={y} x2={BASE_W - PAD.right} y2={y}
                stroke={NEON_CYAN}
                strokeWidth={2}
                opacity={1}
                filter="url(#tcSupportGlow)"
              />
              <rect
                x={BASE_W - PAD.right + 2} y={y - 11}
                width={84} height={22} rx={4}
                fill="rgba(0,240,255,0.15)"
                stroke={NEON_CYAN} strokeWidth={1}
                filter="url(#tcTagGlow)"
              />
              <text
                x={BASE_W - PAD.right + 8} y={y + 4}
                fill={NEON_CYAN} fontSize={10.5} fontFamily="monospace" fontWeight="bold"
              >
                {s.label} {s.price.toFixed(decimals)}
              </text>
            </g>
          );
        })}

        {/* ══ HISTORICAL TOUCH RIPPLES ══ */}
        {showSR && touchPoints.map((tp) => (
          <circle
            key={tp.key}
            cx={tp.x}
            cy={tp.y}
            r={4}
            fill="none"
            stroke={tp.color}
            strokeWidth={2}
            opacity={0.6}
            className="ripple-effect"
          />
        ))}

        {/* Price area fill */}
        <path d={areaPath} fill="url(#tcAreaGrad)" />

        {/* Price line */}
        <path d={pricePath} fill="none" stroke="#00ff88" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" filter="url(#tcPriceGlow)" />

        {/* Current price horizontal line + dot (only when viewing latest) */}
        {visibleWindow.isAtLatest && (
          <>
            <line x1={PAD.left} y1={yScale(currentPrice)} x2={BASE_W - PAD.right} y2={yScale(currentPrice)} stroke="#00ff88" strokeWidth={1} strokeDasharray="3 3" opacity={0.4} />
            <circle cx={lastX} cy={yScale(currentPrice)} r={16 + pulse * 4} fill="url(#tcDotGlow)" opacity={0.35 + pulse * 0.15} />
            <circle cx={lastX} cy={yScale(currentPrice)} r={5} fill="#00ff88" stroke="#020617" strokeWidth={2} />
            <rect x={BASE_W - PAD.right + 2} y={yScale(currentPrice) - 12} width={84} height={24} rx={5} fill="rgba(0,255,136,0.18)" stroke="#00ff88" strokeWidth={1.2} />
            <text x={BASE_W - PAD.right + 10} y={yScale(currentPrice) + 5} fill="#00ff88" fontSize={11} fontFamily="monospace" fontWeight="bold">
              {currentPrice.toFixed(decimals)}
            </text>
          </>
        )}
        {/* Historical mode indicator */}
        {!visibleWindow.isAtLatest && (
          <text x={BASE_W / 2} y={PAD.top + 14} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize={10} fontFamily="monospace">
            ◀ Geçmiş veri ({scrollOffset} bar geri) — Çift tıkla: en son
          </text>
        )}
      </svg>

      {/* ══ CONTROL TOGGLES ══ */}
      <div className="flex items-center justify-center gap-4 mt-2 mb-1">
        <button
          onClick={() => setShowSR(!showSR)}
          className={`
            px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all duration-300
            ${showSR
              ? "bg-slate-800 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(34,211,238,0.15)]"
              : "bg-slate-900/50 text-slate-500 border border-transparent hover:bg-slate-800"
            }
          `}
        >
          {showSR ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          <span>S/R Seviyeleri</span>
        </button>

        <div className="w-px h-4 bg-slate-800" />

        <button
          onClick={() => setShowGrid(!showGrid)}
          className={`
            px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all duration-300
            ${showGrid
              ? "bg-slate-800 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(34,211,238,0.15)]"
              : "bg-slate-900/50 text-slate-500 border border-transparent hover:bg-slate-800"
            }
          `}
        >
          <Grid3X3 className="w-3.5 h-3.5" />
          <span>Izgara / Işınlar</span>
        </button>
      </div>
    </div>
  );
}
