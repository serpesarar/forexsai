"use client";

import clsx from "clsx";

interface CircularProgressProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  colorClassName?: string;
  label?: string;
  sublabel?: string;
  animated?: boolean;
  onClick?: () => void;
  isInteractive?: boolean;
  hoverScale?: number;
}

export default function CircularProgress({
  value,
  size = 120,
  strokeWidth = 8,
  colorClassName = "text-accent",
  label,
  sublabel,
  animated = true,
  onClick,
  isInteractive = false,
  hoverScale = 1.05,
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedValue = Math.min(100, Math.max(0, value));
  const offset = circumference - (clampedValue / 100) * circumference;
  const displayText = sublabel ?? `${Math.round(clampedValue)}%`;
  const displayLen = String(displayText).length;
  const baseFontPx = Math.min(22, Math.max(11, Math.round(size * 0.18)));
  const fontPx = Math.max(10, baseFontPx - (displayLen >= 7 ? 2 : displayLen >= 9 ? 3 : 0));

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={onClick}
        className={clsx("relative", colorClassName, {
          "circular-progress": isInteractive,
        })}
        style={{
          width: size,
          height: size,
          ...(isInteractive ? { ["--hover-scale" as string]: String(hoverScale) } : {}),
        }}
        aria-label={label}
      >
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeLinecap="round"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={clsx({ "transition-all duration-700 ease-out": animated })}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="font-semibold text-textPrimary font-mono" style={{ fontSize: fontPx, lineHeight: 1.1 }}>
            {displayText}
          </span>
        </div>
      </button>
      {label && <span className="text-xs uppercase tracking-[0.2em] text-textSecondary">{label}</span>}
    </div>
  );
}
