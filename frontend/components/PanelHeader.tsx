"use client";

import { ReactNode } from "react";
import { PanelInfoButton } from "./PanelInfoButton";
import { RotateIcon as RefreshCw } from "./ui/CustomIcons";

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

// ── Types ──
export interface SymbolOption {
  key: string;
  label: string;
}

export interface PanelHeaderProps {
  // Title
  title: string;
  subtitle: string;
  
  // Icon
  icon: ReactNode;
  iconBg?: string;
  iconBorder?: string;
  iconColor?: string;
  
  // Symbol Switcher
  symbols: SymbolOption[];
  activeSymbol: string;
  onSymbolChange: (symbol: string) => void;
  
  // Timeframe (optional)
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  timeframes?: string[];
  
  // Actions
  onRefresh: () => void;
  loading?: boolean;
  panelId: string;
  
  // Extra content (price display, etc.)
  extraContent?: ReactNode;
}

// ── Component ──
export function PanelHeader({
  title,
  subtitle,
  icon,
  iconBg = "var(--info-bg)",
  iconBorder = "var(--info-border)",
  iconColor = "var(--accent-cyan)",
  symbols,
  activeSymbol,
  onSymbolChange,
  timeframe,
  onTimeframeChange,
  timeframes = ["5m", "15m", "1h"],
  onRefresh,
  loading = false,
  panelId,
  extraContent,
}: PanelHeaderProps) {
  return (
    <div 
      className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4 lg:gap-5 relative"
      style={{ 
        background: "var(--bg-card)", 
        borderBottom: "1px solid var(--border-subtle)",
        padding: "var(--panel-header-padding, 20px 24px)",
        fontFamily: FONT,
      }}
    >
      {/* Subtle grid pattern background */}
      <div 
        className="absolute inset-0 opacity-[0.02] pointer-events-none" 
        style={{ 
          backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='20' height='20' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20 0L0 0 0 20' fill='none' stroke='%23FFF' stroke-width='1'/%3E%3C/svg%3E\")", 
          backgroundSize: "20px 20px" 
        }} 
      />

      {/* Left: Icon + Title + Extra Content */}
      <div className="flex items-center gap-5 z-10 flex-wrap">
        {/* Icon + Title Group */}
        <div className="flex items-center gap-4">
          {/* Icon Box - 3D Premium Style */}
          <div 
            className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300 hover:scale-105"
            style={{ 
              background: `linear-gradient(135deg, ${iconBg} 0%, rgba(255,255,255,0.05) 100%)`,
              border: `1px solid ${iconBorder}`,
              boxShadow: `
                0 4px 12px rgba(0,0,0,0.4),
                0 1px 2px rgba(255,255,255,0.1) inset,
                0 -1px 2px rgba(0,0,0,0.3) inset
              `,
            }}
          >
            <div style={{ 
              color: iconColor,
              filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.3))",
            }}>{icon}</div>
          </div>

          {/* Title Stack */}
          <div className="flex flex-col gap-0.5">
            {/* Main Title with Cyan Accent */}
            <div className="flex items-center gap-3">
              <h1 
                className="text-lg font-semibold tracking-tight"
                style={{ 
                  color: "var(--accent-cyan)",
                  fontSize: "17px",
                  fontWeight: 650,
                  letterSpacing: "-0.01em",
                }}
              >
                {title}
              </h1>
              {timeframe && (
                <span 
                  className="text-[11px] px-2 py-0.5 rounded-md uppercase tracking-wider font-semibold"
                  style={{ 
                    background: "var(--bg-input)", 
                    color: "var(--text-muted)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  {timeframe}
                </span>
              )}
            </div>
            
            {/* Subtitle */}
            <div 
              className="text-xs font-medium uppercase tracking-wider"
              style={{ 
                color: "var(--text-muted)",
                opacity: 0.9,
                letterSpacing: "0.04em",
              }}
            >
              {subtitle}
            </div>
          </div>
        </div>

        {/* Divider + Extra Content (Price, etc.) */}
        {extraContent && (
          <>
            <div 
              className="h-10 w-[1px] hidden lg:block" 
              style={{ background: "var(--border-subtle)" }} 
            />
            <div className="hidden lg:block">
              {extraContent}
            </div>
          </>
        )}
      </div>

      {/* Right: Controls */}
      <div className="flex items-center gap-3 z-10 flex-wrap">
        {/* Timeframe Selector (if provided) */}
        {onTimeframeChange && (
          <div 
            className="flex rounded-lg p-0.5"
            style={{ 
              background: "var(--bg-input)", 
              border: "1px solid var(--border-subtle)" 
            }}
          >
            {timeframes.map((tf) => (
              <button 
                key={tf} 
                onClick={() => onTimeframeChange(tf)}
                className="px-3 py-1.5 text-xs font-semibold transition-all rounded-md"
                style={{
                  background: timeframe === tf ? "var(--bg-surface)" : "transparent",
                  color: timeframe === tf ? "var(--text-primary)" : "var(--text-secondary)",
                  boxShadow: timeframe === tf ? "var(--shadow-elev-1)" : "none",
                  border: `1px solid ${timeframe === tf ? "var(--border-default)" : "transparent"}`,
                }}
              >
                {tf}
              </button>
            ))}
          </div>
        )}

        {/* Symbol Switcher */}
        <div 
          className="flex rounded-lg p-0.5"
          style={{ 
            background: "var(--bg-input)", 
            border: "1px solid var(--border-subtle)" 
          }}
        >
          {symbols.map((s) => (
            <button 
              key={s.key} 
              onClick={() => onSymbolChange(s.key)}
              className="px-3.5 py-2 text-xs font-semibold transition-all rounded-md"
              style={{
                background: activeSymbol === s.key ? "rgba(255,255,255,0.04)" : "transparent",
                color: activeSymbol === s.key ? "var(--text-primary)" : "var(--text-secondary)",
                boxShadow: activeSymbol === s.key ? "var(--shadow-elev-1)" : "none",
                border: `1px solid ${activeSymbol === s.key ? "rgba(255,255,255,0.07)" : "transparent"}`,
                fontWeight: activeSymbol === s.key ? 600 : 500,
                minHeight: "34px",
              }}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Refresh Button */}
        <button 
          onClick={onRefresh} 
          className="w-9 h-9 rounded-lg flex items-center justify-center transition-all hover:bg-white/5"
          style={{ 
            border: "1px solid var(--border-subtle)", 
            background: "var(--bg-input)",
          }}
        >
          <RefreshCw 
            className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} 
            style={{ color: "var(--text-muted)" }} 
          />
        </button>

        {/* Info Button */}
        <PanelInfoButton panelId={panelId} />
      </div>
    </div>
  );
}

// ── Compact Panel Header (for smaller panels) ──
export function PanelHeaderCompact({
  title,
  subtitle,
  icon,
  iconColor = "var(--accent-cyan)",
  onRefresh,
  loading = false,
  panelId,
  children, // Additional controls
}: {
  title: string;
  subtitle: string;
  icon: ReactNode;
  iconColor?: string;
  onRefresh: () => void;
  loading?: boolean;
  panelId: string;
  children?: ReactNode;
}) {
  return (
    <div 
      className="flex justify-between items-center relative"
      style={{ 
        background: "var(--bg-card)", 
        borderBottom: "1px solid var(--border-subtle)",
        padding: "16px 20px",
        fontFamily: FONT,
      }}
    >
      {/* Subtle grid pattern */}
      <div 
        className="absolute inset-0 opacity-[0.02] pointer-events-none" 
        style={{ 
          backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='20' height='20' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20 0L0 0 0 20' fill='none' stroke='%23FFF' stroke-width='1'/%3E%3C/svg%3E\")", 
          backgroundSize: "20px 20px" 
        }} 
      />

      {/* Left: Icon + Title */}
      <div className="flex items-center gap-3 z-10">
        <div 
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300 hover:scale-105"
          style={{ 
            background: "linear-gradient(135deg, var(--accent-cyan-08) 0%, rgba(255,255,255,0.05) 100%)",
            border: "1px solid var(--accent-cyan-15)",
            boxShadow: `
              0 4px 12px rgba(0,0,0,0.4),
              0 1px 2px rgba(255,255,255,0.1) inset,
              0 -1px 2px rgba(0,0,0,0.3) inset
            `,
          }}
        >
          <div style={{ 
            color: iconColor,
            filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.3))",
          }}>{icon}</div>
        </div>
        <div className="flex flex-col gap-0.5">
          <h1 
            className="text-base font-semibold tracking-tight"
            style={{ 
              color: "var(--accent-cyan)",
              fontWeight: 650,
              letterSpacing: "-0.01em",
            }}
          >
            {title}
          </h1>
          <div 
            className="text-[11px] font-medium uppercase tracking-wider"
            style={{ color: "var(--text-muted)" }}
          >
            {subtitle}
          </div>
        </div>
      </div>

      {/* Right: Controls */}
      <div className="flex items-center gap-2 z-10">
        {children}
        <button 
          onClick={onRefresh} 
          className="w-8 h-8 rounded-lg flex items-center justify-center transition-all hover:bg-white/5"
          style={{ 
            border: "1px solid var(--border-subtle)", 
            background: "var(--bg-input)",
          }}
        >
          <RefreshCw 
            className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} 
            style={{ color: "var(--text-muted)" }} 
          />
        </button>
        <PanelInfoButton panelId={panelId} />
      </div>
    </div>
  );
}

export default PanelHeader;
