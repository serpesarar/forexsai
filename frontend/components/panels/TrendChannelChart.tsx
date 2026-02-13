"use client";

import { useMemo, useRef, useEffect, useState, useCallback } from "react";

interface TrendChannelChartProps {
  closes: number[];
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
const BASE_H = 380;
const PAD = { top: 20, right: 90, bottom: 20, left: 10 };

export default function TrendChannelChart({
  closes,
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

  // Pan & zoom state
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 });

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1200);
    return () => clearInterval(id);
  }, []);

  // Mouse handlers for drag-to-pan
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY, panX, panY };
  }, [panX, panY]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.current.x;
    const dy = e.clientY - dragStart.current.y;
    setPanX(dragStart.current.panX + dx / zoom);
    setPanY(dragStart.current.panY + dy / zoom);
  }, [isDragging, zoom]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Scroll-to-zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.5, Math.min(5, z * delta)));
  }, []);

  // Touch handlers for pinch-to-zoom
  const lastTouchDist = useRef<number | null>(null);
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      lastTouchDist.current = Math.hypot(dx, dy);
    } else if (e.touches.length === 1) {
      setIsDragging(true);
      dragStart.current = { x: e.touches[0].clientX, y: e.touches[0].clientY, panX, panY };
    }
  }, [panX, panY]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2 && lastTouchDist.current !== null) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.hypot(dx, dy);
      const scale = dist / lastTouchDist.current;
      setZoom((z) => Math.max(0.5, Math.min(5, z * scale)));
      lastTouchDist.current = dist;
    } else if (e.touches.length === 1 && isDragging) {
      const dx = e.touches[0].clientX - dragStart.current.x;
      const dy = e.touches[0].clientY - dragStart.current.y;
      setPanX(dragStart.current.panX + dx / zoom);
      setPanY(dragStart.current.panY + dy / zoom);
    }
  }, [isDragging, zoom]);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    lastTouchDist.current = null;
  }, []);

  // Double-click to reset
  const handleDoubleClick = useCallback(() => {
    setZoom(1);
    setPanX(0);
    setPanY(0);
  }, []);

  const computed = useMemo(() => {
    if (!closes.length) return null;

    const allPrices = [
      ...closes, ...upper, ...lower,
      ...supportLevels.map((s) => s.price),
      ...resistanceLevels.map((r) => r.price),
      currentPrice,
    ].filter((v) => v > 0);

    const rawMin = Math.min(...allPrices);
    const rawMax = Math.max(...allPrices);
    const pad = (rawMax - rawMin) * 0.06;
    const minP = rawMin - pad;
    const maxP = rawMax + pad;
    const range = maxP - minP || 1;

    const plotW = BASE_W - PAD.left - PAD.right;
    const plotH = BASE_H - PAD.top - PAD.bottom;

    const xScale = (i: number) => PAD.left + (i / Math.max(1, closes.length - 1)) * plotW;
    const yScale = (price: number) => PAD.top + plotH - ((price - minP) / range) * plotH;

    const pricePts = closes.map((c, i) => `${xScale(i)},${yScale(c)}`);
    // Extend line to currentPrice so green line tracks live price
    const lastIdx = closes.length - 1;
    const extendedPricePts = [...pricePts, `${xScale(lastIdx)},${yScale(currentPrice)}`];
    const pricePath = `M${extendedPricePts.join("L")}`;
    const areaPath = `${pricePath}L${xScale(lastIdx)},${BASE_H - PAD.bottom}L${xScale(0)},${BASE_H - PAD.bottom}Z`;

    const makePath = (arr: number[]) => {
      if (!arr.length) return "";
      return `M${arr.map((v, i) => `${xScale(i)},${yScale(v)}`).join("L")}`;
    };

    let channelFillPath = "";
    if (upper.length && lower.length) {
      const upPts = upper.map((v, i) => `${xScale(i)},${yScale(v)}`).join("L");
      const downPts = [...lower].reverse().map((v, i) => `${xScale(lower.length - 1 - i)},${yScale(v)}`).join("L");
      channelFillPath = `M${upPts}L${downPts}Z`;
    }

    const gridCount = 6;
    const gridLines: { y: number; price: number }[] = [];
    for (let i = 0; i <= gridCount; i++) {
      const price = minP + (range * i) / gridCount;
      gridLines.push({ y: yScale(price), price });
    }

    return {
      pricePath, areaPath,
      upperPath: makePath(upper),
      lowerPath: makePath(lower),
      middlePath: makePath(middle),
      channelFillPath,
      yScale, xScale, minP, maxP, gridLines,
      lastX: xScale(closes.length - 1),
    };
  }, [closes, upper, lower, middle, supportLevels, resistanceLevels, currentPrice, decimals]);

  if (!computed) return null;

  const { pricePath, areaPath, upperPath, lowerPath, middlePath, channelFillPath, yScale, lastX, gridLines } = computed;
  const pulse = Math.sin(tick * Math.PI * 0.8);
  const srPulse = 0.45 + Math.sin(tick * Math.PI * 0.6) * 0.25;

  // Compute viewBox with pan/zoom
  const vbW = BASE_W / zoom;
  const vbH = BASE_H / zoom;
  const vbX = (BASE_W - vbW) / 2 - panX;
  const vbY = (BASE_H - vbH) / 2 - panY;

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
      {/* Zoom controls */}
      <div className="absolute top-2 left-2 z-10 flex items-center gap-1">
        <button
          onClick={(e) => { e.stopPropagation(); setZoom(z => Math.min(5, z * 1.25)); }}
          className="w-7 h-7 rounded-md flex items-center justify-center text-sm font-bold font-mono transition-all hover:brightness-150"
          style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}
        >+</button>
        <button
          onClick={(e) => { e.stopPropagation(); setZoom(z => Math.max(0.5, z * 0.8)); }}
          className="w-7 h-7 rounded-md flex items-center justify-center text-sm font-bold font-mono transition-all hover:brightness-150"
          style={{ background: "rgba(255,51,102,0.1)", color: "#ff3366", border: "1px solid rgba(255,51,102,0.2)" }}
        >−</button>
        {zoom !== 1 && (
          <button
            onClick={(e) => { e.stopPropagation(); setZoom(1); setPanX(0); setPanY(0); }}
            className="h-7 px-2 rounded-md flex items-center justify-center text-[10px] font-bold font-mono transition-all hover:brightness-150"
            style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.1)" }}
          >{zoom.toFixed(1)}x ↺</button>
        )}
      </div>

      <svg
        ref={svgRef}
        viewBox={`${vbX} ${vbY} ${vbW} ${vbH}`}
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
            <feGaussianBlur stdDeviation={4 + supportIntensity * 6} result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="tcResistGlow">
            <feGaussianBlur stdDeviation={4 + resistanceIntensity * 6} result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="tcSRNeonGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="tcTagGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
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

        {/* Channel fill */}
        {channelFillPath && <path d={channelFillPath} fill="url(#tcChannelFill)" />}
        {/* Upper channel */}
        <path d={upperPath} fill="none" stroke="#6366f1" strokeWidth={1.5} opacity={0.5} />
        {/* Lower channel */}
        <path d={lowerPath} fill="none" stroke="#6366f1" strokeWidth={1.5} opacity={0.5} />
        {/* Middle regression */}
        <path d={middlePath} fill="none" stroke="#6366f1" strokeWidth={1} strokeDasharray="6 4" opacity={0.3} />

        {/* ══ RESISTANCE LEVELS - always neon glow ══ */}
        {resistanceLevels.map((r, i) => {
          const y = yScale(r.price);
          if (y < PAD.top - 5 || y > BASE_H - PAD.bottom + 5) return null;
          const isStrong = r.strength === "strong";
          const proxGlow = resistanceProximity;
          return (
            <g key={`rl-${i}`}>
              {/* Always-on subtle neon glow zone */}
              <rect
                x={PAD.left} y={y - 10}
                width={BASE_W - PAD.left - PAD.right} height={20}
                fill="#ff3366"
                opacity={proxGlow ? resistanceIntensity * 0.08 : srPulse * 0.035}
              />
              {/* The S/R line with neon glow filter always on */}
              <line
                x1={PAD.left} y1={y} x2={BASE_W - PAD.right} y2={y}
                stroke="#ff3366"
                strokeWidth={isStrong ? 2.5 : 1.8}
                strokeDasharray={isStrong ? "none" : "10 5"}
                opacity={proxGlow ? 0.95 : 0.5 + srPulse * 0.2}
                filter={proxGlow ? "url(#tcResistGlow)" : "url(#tcSRNeonGlow)"}
              />
              {/* Price tag */}
              <rect
                x={BASE_W - PAD.right + 2} y={y - 11}
                width={84} height={22} rx={4}
                fill="rgba(255,51,102,0.18)"
                stroke="#ff3366" strokeWidth={1}
                filter="url(#tcTagGlow)"
              />
              <text
                x={BASE_W - PAD.right + 8} y={y + 4}
                fill="#ff3366" fontSize={10.5} fontFamily="monospace" fontWeight="bold"
              >
                {r.label} {r.price.toFixed(decimals)}
              </text>
            </g>
          );
        })}

        {/* ══ SUPPORT LEVELS - always neon glow ══ */}
        {supportLevels.map((s, i) => {
          const y = yScale(s.price);
          if (y < PAD.top - 5 || y > BASE_H - PAD.bottom + 5) return null;
          const isStrong = s.strength === "strong";
          const proxGlow = supportProximity;
          return (
            <g key={`sl-${i}`}>
              <rect
                x={PAD.left} y={y - 10}
                width={BASE_W - PAD.left - PAD.right} height={20}
                fill="#00ccff"
                opacity={proxGlow ? supportIntensity * 0.08 : srPulse * 0.035}
              />
              <line
                x1={PAD.left} y1={y} x2={BASE_W - PAD.right} y2={y}
                stroke="#00ccff"
                strokeWidth={isStrong ? 2.5 : 1.8}
                strokeDasharray={isStrong ? "none" : "10 5"}
                opacity={proxGlow ? 0.95 : 0.5 + srPulse * 0.2}
                filter={proxGlow ? "url(#tcSupportGlow)" : "url(#tcSRNeonGlow)"}
              />
              <rect
                x={BASE_W - PAD.right + 2} y={y - 11}
                width={84} height={22} rx={4}
                fill="rgba(0,204,255,0.15)"
                stroke="#00ccff" strokeWidth={1}
                filter="url(#tcTagGlow)"
              />
              <text
                x={BASE_W - PAD.right + 8} y={y + 4}
                fill="#00ccff" fontSize={10.5} fontFamily="monospace" fontWeight="bold"
              >
                {s.label} {s.price.toFixed(decimals)}
              </text>
            </g>
          );
        })}

        {/* Price area fill */}
        <path d={areaPath} fill="url(#tcAreaGrad)" />

        {/* Price line */}
        <path d={pricePath} fill="none" stroke="#00ff88" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" filter="url(#tcPriceGlow)" />

        {/* Current price horizontal line */}
        <line x1={PAD.left} y1={yScale(currentPrice)} x2={BASE_W - PAD.right} y2={yScale(currentPrice)} stroke="#00ff88" strokeWidth={1} strokeDasharray="3 3" opacity={0.4} />

        {/* Current price dot glow */}
        <circle cx={lastX} cy={yScale(currentPrice)} r={16 + pulse * 4} fill="url(#tcDotGlow)" opacity={0.35 + pulse * 0.15} />
        <circle cx={lastX} cy={yScale(currentPrice)} r={5} fill="#00ff88" stroke="#020617" strokeWidth={2} />

        {/* Current price tag */}
        <rect x={BASE_W - PAD.right + 2} y={yScale(currentPrice) - 12} width={84} height={24} rx={5} fill="rgba(0,255,136,0.18)" stroke="#00ff88" strokeWidth={1.2} />
        <text x={BASE_W - PAD.right + 10} y={yScale(currentPrice) + 5} fill="#00ff88" fontSize={11} fontFamily="monospace" fontWeight="bold">
          {currentPrice.toFixed(decimals)}
        </text>
      </svg>
    </div>
  );
}
