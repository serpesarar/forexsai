"use client";

import React, { memo } from "react";
import { cn } from "@/lib/utils";
import type { SymbolImpact, ImpactDirection } from "@/types/news-correlation";

interface ImpactBadgeProps {
  impact: SymbolImpact;
  showScore?: boolean;
  showConfidence?: boolean;
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  isGhost?: boolean;
  onClick?: () => void;
  className?: string;
}

// Color configurations for each direction
const directionStyles: Record<ImpactDirection, {
  bg: string;
  text: string;
  border: string;
  glow: string;
  icon: string;
}> = {
  bullish: {
    bg: "bg-green-500/20",
    text: "text-green-400",
    border: "border-green-500/50",
    glow: "shadow-[0_0_10px_rgba(34,197,94,0.3)]",
    icon: "↑",
  },
  bearish: {
    bg: "bg-red-500/20",
    text: "text-red-400",
    border: "border-red-500/50",
    glow: "shadow-[0_0_10px_rgba(239,68,68,0.3)]",
    icon: "↓",
  },
  neutral: {
    bg: "bg-yellow-500/20",
    text: "text-yellow-400",
    border: "border-yellow-500/50",
    glow: "shadow-[0_0_10px_rgba(234,179,8,0.3)]",
    icon: "→",
  },
};

// Size configurations
const sizeStyles = {
  sm: {
    container: "px-2 py-0.5 text-xs gap-1",
    icon: "text-xs",
    score: "text-[10px]",
  },
  md: {
    container: "px-2.5 py-1 text-sm gap-1.5",
    icon: "text-sm",
    score: "text-xs",
  },
  lg: {
    container: "px-3 py-1.5 text-base gap-2",
    icon: "text-base",
    score: "text-sm",
  },
};

// Score-based intensity
const getScoreIntensity = (score: number): string => {
  if (score >= 8) return "ring-2 ring-offset-1 ring-offset-background";
  if (score >= 5) return "ring-1 ring-offset-0";
  return "";
};

export const ImpactBadge = memo(function ImpactBadge({
  impact,
  showScore = true,
  showConfidence = false,
  size = "md",
  interactive = false,
  isGhost = false,
  onClick,
  className,
}: ImpactBadgeProps) {
  const styles = directionStyles[impact.direction];
  const sizeConfig = sizeStyles[size];
  const scoreIntensity = getScoreIntensity(impact.score);
  
  // Ghost markers have reduced opacity
  const ghostStyles = isGhost 
    ? "opacity-40 grayscale-[0.3]" 
    : "";

  return (
    <button
      onClick={onClick}
      disabled={!interactive}
      className={cn(
        // Base styles
        "inline-flex items-center rounded-full border font-medium",
        "backdrop-blur-sm transition-all duration-200",
        "select-none",
        
        // Direction-based colors
        styles.bg,
        styles.text,
        styles.border,
        
        // Size
        sizeConfig.container,
        
        // Interactive states
        interactive && [
          "cursor-pointer hover:scale-105 active:scale-95",
          "hover:" + styles.glow,
        ],
        !interactive && "cursor-default",
        
        // Score intensity ring
        scoreIntensity,
        
        // Ghost marker
        ghostStyles,
        
        // Custom class
        className
      )}
      title={`${impact.symbol}: ${impact.reasoning} (${Math.round(impact.confidence * 100)}% confidence)`}
    >
      {/* Direction Icon */}
      <span className={cn("font-bold", sizeConfig.icon)}>
        {styles.icon}
      </span>
      
      {/* Symbol */}
      <span className="font-semibold tracking-wide">
        {impact.symbol}
      </span>
      
      {/* Score */}
      {showScore && (
        <span 
          className={cn(
            "opacity-80 tabular-nums",
            sizeConfig.score
          )}
        >
          {impact.score}/10
        </span>
      )}
      
      {/* Confidence indicator (optional) */}
      {showConfidence && (
        <span 
          className={cn(
            "opacity-60 ml-1",
            sizeConfig.score
          )}
        >
          {Math.round(impact.confidence * 100)}%
        </span>
      )}
      
      {/* Ghost indicator */}
      {isGhost && (
        <span className="ml-0.5 text-[10px] opacity-50" title="Indirect impact">
          ○
        </span>
      )}
    </button>
  );
});

// Compact version for small spaces
interface CompactImpactBadgeProps {
  symbol: string;
  direction: ImpactDirection;
  score: number;
  size?: "sm" | "md";
  className?: string;
}

export const CompactImpactBadge = memo(function CompactImpactBadge({
  symbol,
  direction,
  score,
  size = "sm",
  className,
}: CompactImpactBadgeProps) {
  const styles = directionStyles[direction];
  
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs font-medium",
        styles.bg,
        styles.text,
        className
      )}
    >
      <span>{styles.icon}</span>
      <span>{symbol}</span>
    </span>
  );
});

// Multi-impact badge row
interface ImpactBadgeRowProps {
  impacts: SymbolImpact[];
  currentSymbol?: string;
  maxVisible?: number;
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  onSymbolClick?: (symbol: string) => void;
  className?: string;
}

export const ImpactBadgeRow = memo(function ImpactBadgeRow({
  impacts,
  currentSymbol,
  maxVisible = 4,
  size = "md",
  interactive = true,
  onSymbolClick,
  className,
}: ImpactBadgeRowProps) {
  // Sort: current symbol first, then by score
  const sortedImpacts = [...impacts].sort((a, b) => {
    if (a.symbol === currentSymbol) return -1;
    if (b.symbol === currentSymbol) return 1;
    return b.score - a.score;
  });
  
  const visibleImpacts = sortedImpacts.slice(0, maxVisible);
  const remainingCount = sortedImpacts.length - maxVisible;
  
  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {visibleImpacts.map((impact) => (
        <ImpactBadge
          key={impact.symbol}
          impact={impact}
          size={size}
          interactive={interactive}
          isGhost={impact.symbol !== currentSymbol && currentSymbol !== undefined}
          onClick={() => onSymbolClick?.(impact.symbol)}
        />
      ))}
      
      {remainingCount > 0 && (
        <button
          className={cn(
            "inline-flex items-center rounded-full border border-slate-600",
            "bg-slate-800/50 text-slate-400 text-xs px-2 py-1",
            "hover:bg-slate-700/50 transition-colors"
          )}
          title={`${remainingCount} more affected instruments`}
        >
          +{remainingCount}
        </button>
      )}
    </div>
  );
});

export default ImpactBadge;
