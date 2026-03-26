"use client";

import { ReactNode } from "react";
import { PanelInfoButton } from "./PanelInfoButton";

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

  // Actions (onRefresh is now optional - manual refresh button removed)
  onRefresh?: () => void;
  loading?: boolean;
  panelId: string;

  // Extra content (price display, etc.)
  extraContent?: ReactNode;

  // Signal age (seconds since last signal)
  signalAge?: string;

  // Fullscreen toggle
  onFullscreen?: () => void;
  isFullscreen?: boolean;
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
  signalAge,
  onFullscreen,
  isFullscreen = false,
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

        {/* Signal Age Badge */}
        {signalAge && (
          <div
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-[12px] font-mono font-bold tracking-wide"
            style={{
              background: "color-mix(in srgb, var(--accent-info) 12%, var(--bg-input))",
              border: "1px solid color-mix(in srgb, var(--accent-info) 35%, var(--border-subtle))",
              color: "var(--text-primary)",
              boxShadow: "0 0 0 1px rgba(255,255,255,0.02) inset, 0 8px 18px rgba(0,0,0,0.22)",
            }}
          >
            <div className="w-2 h-2 rounded-full" style={{ background: "var(--accent-positive)", animation: "pulse 2s infinite", boxShadow: "0 0 10px var(--accent-positive)" }} />
            {signalAge}
          </div>
        )}

        {/* Fullscreen Toggle */}
        {onFullscreen && (
          <button
            onClick={onFullscreen}
            title={isFullscreen ? "Exit fullscreen (Esc)" : "Fullscreen"}
            className="flex items-center justify-center w-8 h-8 rounded-lg transition-all hover:opacity-80"
            style={{
              background: isFullscreen
                ? "color-mix(in srgb, var(--accent-cyan) 18%, var(--bg-input))"
                : "var(--bg-input)",
              border: `1px solid ${isFullscreen ? "var(--accent-cyan)" : "var(--border-subtle)"}`,
              color: isFullscreen ? "var(--accent-cyan)" : "var(--text-muted)",
            }}
          >
            {isFullscreen ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="4 14 10 14 10 20" /><polyline points="20 10 14 10 14 4" /><line x1="10" y1="14" x2="3" y2="21" /><line x1="21" y1="3" x2="14" y2="10" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 3 21 3 21 9" /><polyline points="9 21 3 21 3 15" /><line x1="21" y1="3" x2="14" y2="10" /><line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            )}
          </button>
        )}

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
  children,
  signalAge,
}: {
  title: string;
  subtitle: string;
  icon: ReactNode;
  iconColor?: string;
  onRefresh?: () => void;
  loading?: boolean;
  panelId: string;
  children?: ReactNode;
  signalAge?: string;
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
        {/* Signal Age Badge */}
        {signalAge && (
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-mono font-bold tracking-wide"
            style={{
              background: "color-mix(in srgb, var(--accent-info) 12%, var(--bg-input))",
              border: "1px solid color-mix(in srgb, var(--accent-info) 35%, var(--border-subtle))",
              color: "var(--text-primary)",
              boxShadow: "0 0 0 1px rgba(255,255,255,0.02) inset, 0 6px 14px rgba(0,0,0,0.2)",
            }}
          >
            <div className="w-2 h-2 rounded-full" style={{ background: "var(--accent-positive)", animation: "pulse 2s infinite", boxShadow: "0 0 10px var(--accent-positive)" }} />
            {signalAge}
          </div>
        )}
        <PanelInfoButton panelId={panelId} />
      </div>
    </div>
  );
}

export default PanelHeader;
