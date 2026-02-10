"use client";

import { useMemo, useRef, useEffect, useState } from "react";

interface TrendChannelChartProps {
  closes: number[];
  upper: number[];
  lower: number[];
  middle: number[];
  supportLevels: { price: number; label: string }[];
  resistanceLevels: { price: number; label: string }[];
  currentPrice: number;
  supportProximity: boolean;
  resistanceProximity: boolean;
  supportIntensity: number;
  resistanceIntensity: number;
}

const W = 480;
const H = 200;
const PAD = { top: 12, right: 50, bottom: 12, left: 8 };

export default function TrendChannelChart({
  closes,
  upper,
  lower,
  middle,
  supportLevels,
  resistanceLevels,
  currentPrice,
  supportProximity,
  resistanceProximity,
  supportIntensity,
  resistanceIntensity,
}: TrendChannelChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tick, setTick] = useState(0);

  // Pulse animation tick
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const { pricePath, areaPath, upperPath, lowerPath, middlePath, yScale, xScale, minP, maxP } =
    useMemo(() => {
      if (!closes.length) return { pricePath: "", areaPath: "", upperPath: "", lowerPath: "", middlePath: "", yScale: () => 0, xScale: () => 0, minP: 0, maxP: 0 };

      // Collect all price values to determine y-axis range
      const allPrices = [
        ...closes,
        ...upper,
        ...lower,
        ...supportLevels.map((s) => s.price),
        ...resistanceLevels.map((r) => r.price),
        currentPrice,
      ].filter((v) => v > 0);

      const minP = Math.min(...allPrices) * 0.999;
      const maxP = Math.max(...allPrices) * 1.001;
      const range = maxP - minP || 1;

      const plotW = W - PAD.left - PAD.right;
      const plotH = H - PAD.top - PAD.bottom;

      const xScale = (i: number) => PAD.left + (i / Math.max(1, closes.length - 1)) * plotW;
      const yScale = (price: number) => PAD.top + plotH - ((price - minP) / range) * plotH;

      // Price line
      const pricePts = closes.map((c, i) => `${xScale(i)},${yScale(c)}`);
      const pricePath = `M${pricePts.join("L")}`;

      // Area fill under price
      const areaPath = `${pricePath}L${xScale(closes.length - 1)},${yScale(minP)}L${xScale(0)},${yScale(minP)}Z`;

      // Channel lines
      const upperPts = upper.map((v, i) => `${xScale(i)},${yScale(v)}`);
      const lowerPts = lower.map((v, i) => `${xScale(i)},${yScale(v)}`);
      const middlePts = middle.map((v, i) => `${xScale(i)},${yScale(v)}`);

      const upperPath = upperPts.length ? `M${upperPts.join("L")}` : "";
      const lowerPath = lowerPts.length ? `M${lowerPts.join("L")}` : "";
      const middlePath = middlePts.length ? `M${middlePts.join("L")}` : "";

      return { pricePath, areaPath, upperPath, lowerPath, middlePath, yScale, xScale, minP, maxP };
    }, [closes, upper, lower, middle, supportLevels, resistanceLevels, currentPrice]);

  if (!closes.length) return null;

  const pulseScale = 1 + Math.sin(tick * Math.PI) * 0.03;
  const lastX = PAD.left + ((closes.length - 1) / Math.max(1, closes.length - 1)) * (W - PAD.left - PAD.right);

  return (
    <div className="relative w-full overflow-hidden rounded-xl" style={{ aspectRatio: `${W}/${H}` }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-full"
        preserveAspectRatio="none"
      >
        <defs>
          {/* Horizon fade mask */}
          <linearGradient id="horizonFade" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="white" />
            <stop offset="80%" stopColor="white" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
          <mask id="horizonMask">
            <rect width={W} height={H} fill="url(#horizonFade)" />
          </mask>

          {/* Price line glow */}
          <filter id="priceGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Support glow */}
          <filter id="supportGlow">
            <feGaussianBlur stdDeviation={2 + supportIntensity * 4} result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Resistance glow */}
          <filter id="resistanceGlow">
            <feGaussianBlur stdDeviation={2 + resistanceIntensity * 4} result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Area gradient */}
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00ff88" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#00ff88" stopOpacity="0.01" />
          </linearGradient>

          {/* Channel fill */}
          <linearGradient id="channelFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1a1a2e" stopOpacity="0.3" />
            <stop offset="50%" stopColor="#1a1a2e" stopOpacity="0.05" />
            <stop offset="100%" stopColor="#1a1a2e" stopOpacity="0.3" />
          </linearGradient>

          {/* Current price dot pulse */}
          <radialGradient id="priceDotGlow">
            <stop offset="0%" stopColor="#00ff88" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#00ff88" stopOpacity="0" />
          </radialGradient>
        </defs>

        <g mask="url(#horizonMask)">
          {/* Channel fill area between upper and lower */}
          {upperPath && lowerPath && (
            <path
              d={`${upperPath}L${PAD.left + ((lower.length - 1) / Math.max(1, lower.length - 1)) * (W - PAD.left - PAD.right)},${yScale(lower[lower.length - 1])}${lowerPath.replace("M", "L").split("L").reverse().join("L")}Z`}
              fill="url(#channelFill)"
              opacity={0.4}
            />
          )}

          {/* Upper channel line */}
          <path
            d={upperPath}
            fill="none"
            stroke="#1a1a2e"
            strokeWidth={1.2}
            strokeDasharray="none"
            opacity={0.7}
          />

          {/* Lower channel line */}
          <path
            d={lowerPath}
            fill="none"
            stroke="#1a1a2e"
            strokeWidth={1.2}
            opacity={0.7}
          />

          {/* Middle regression line */}
          <path
            d={middlePath}
            fill="none"
            stroke="#2a2a3e"
            strokeWidth={0.8}
            strokeDasharray="4 4"
            opacity={0.5}
          />

          {/* Support levels */}
          {supportLevels.map((s, i) => {
            const y = yScale(s.price);
            if (y < PAD.top || y > H - PAD.bottom) return null;
            return (
              <g key={`s-${i}`}>
                <line
                  x1={PAD.left}
                  y1={y}
                  x2={W - PAD.right}
                  y2={y}
                  stroke="#00ccff"
                  strokeWidth={supportProximity ? 1.5 : 0.8}
                  strokeDasharray="6 3"
                  opacity={supportProximity ? 0.9 : 0.5}
                  filter={supportProximity ? "url(#supportGlow)" : undefined}
                  style={supportProximity ? { transform: `scaleY(${pulseScale})`, transformOrigin: `0 ${y}px` } : undefined}
                />
                <text
                  x={W - PAD.right + 4}
                  y={y + 3}
                  fill="#00ccff"
                  fontSize={8}
                  fontFamily="monospace"
                  opacity={0.8}
                >
                  {s.label}
                </text>
              </g>
            );
          })}

          {/* Resistance levels */}
          {resistanceLevels.map((r, i) => {
            const y = yScale(r.price);
            if (y < PAD.top || y > H - PAD.bottom) return null;
            return (
              <g key={`r-${i}`}>
                <line
                  x1={PAD.left}
                  y1={y}
                  x2={W - PAD.right}
                  y2={y}
                  stroke="#ff3366"
                  strokeWidth={resistanceProximity ? 1.5 : 0.8}
                  strokeDasharray="6 3"
                  opacity={resistanceProximity ? 0.9 : 0.5}
                  filter={resistanceProximity ? "url(#resistanceGlow)" : undefined}
                  style={resistanceProximity ? { transform: `scaleY(${pulseScale})`, transformOrigin: `0 ${y}px` } : undefined}
                />
                <text
                  x={W - PAD.right + 4}
                  y={y + 3}
                  fill="#ff3366"
                  fontSize={8}
                  fontFamily="monospace"
                  opacity={0.8}
                >
                  {r.label}
                </text>
              </g>
            );
          })}

          {/* Price area fill */}
          <path d={areaPath} fill="url(#areaGrad)" />

          {/* Price line */}
          <path
            d={pricePath}
            fill="none"
            stroke="#00ff88"
            strokeWidth={2.5}
            strokeLinejoin="round"
            strokeLinecap="round"
            filter="url(#priceGlow)"
          />

          {/* Current price dot with pulse */}
          <circle
            cx={lastX}
            cy={yScale(currentPrice)}
            r={12}
            fill="url(#priceDotGlow)"
            opacity={0.4 + Math.sin(tick * Math.PI) * 0.2}
          />
          <circle
            cx={lastX}
            cy={yScale(currentPrice)}
            r={4}
            fill="#00ff88"
            stroke="#00ff88"
            strokeWidth={1}
          />

          {/* Current price horizontal line */}
          <line
            x1={lastX}
            y1={yScale(currentPrice)}
            x2={W - PAD.right}
            y2={yScale(currentPrice)}
            stroke="#00ff88"
            strokeWidth={0.5}
            strokeDasharray="2 2"
            opacity={0.6}
          />
          <text
            x={W - PAD.right + 4}
            y={yScale(currentPrice) + 3}
            fill="#00ff88"
            fontSize={9}
            fontFamily="monospace"
            fontWeight="bold"
          >
            NOW
          </text>
        </g>
      </svg>
    </div>
  );
}
