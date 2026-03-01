import React from "react";

interface IconProps {
    className?: string;
    size?: number;
    style?: React.CSSProperties;
    strokeWidth?: number;
}

// ─── SIDEBAR NAV ICONS ────────────────────────────────────────────────────────

/**
 * DashboardIcon — Dört köşe mini blok + merkezi sinyal nabzı
 */
export function DashboardIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="dash-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-info)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <filter id="dash-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Holographic backdrop lines */}
            <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="0.5" opacity="0.1" strokeDasharray="1 2" />
            {/* Left large block */}
            <rect x="3" y="3" width="8" height="18" rx="2" stroke="url(#dash-grad)" strokeWidth="1.5" fill="var(--accent-info-10)" filter="url(#dash-glow)" />
            {/* Top right block */}
            <rect x="14" y="3" width="7" height="8" rx="2" stroke="var(--accent-info)" strokeWidth="1.5" fill="var(--accent-info-10)" filter="url(#dash-glow)" />
            {/* Bottom right block with graph */}
            <rect x="14" y="14" width="7" height="7" rx="2" stroke="var(--accent-info)" strokeWidth="1" opacity="0.7" />
            <path d="M 15 18 L 17 16 L 18 17 L 20 15" stroke="var(--accent-info)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="7" cy="7" r="1.5" fill="var(--accent-info)" filter="url(#dash-glow)" />
            <circle cx="7" cy="17" r="1.5" fill="var(--accent-info)" filter="url(#dash-glow)" />
        </svg>
    );
}

/**
 * ChartsIcon — Stilize mum grafiği: 3 gövde + ince fitil çizgileri
 */
export function ChartsIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="chart-bull" x1="0%" y1="100%" x2="0%" y2="0%">
                    <stop offset="0%" stopColor="var(--accent-positive)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <linearGradient id="chart-bear" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-negative)" />
                    <stop offset="100%" stopColor="var(--accent-purple)" />
                </linearGradient>
                <filter id="chart-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Holographic grid */}
            <line x1="2" y1="20" x2="22" y2="20" stroke="currentColor" strokeWidth="1" opacity="0.3" strokeDasharray="2 3" />
            <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="0.5" opacity="0.1" />

            {/* Bull candle */}
            <line x1="6" y1="5" x2="6" y2="18" stroke="var(--accent-positive)" strokeWidth="1.5" filter="url(#chart-glow)" />
            <rect x="4" y="9" width="4" height="6" rx="1" fill="url(#chart-bull)" filter="url(#chart-glow)" />

            {/* Bear candle (tall) */}
            <line x1="12" y1="3" x2="12" y2="22" stroke="var(--accent-negative)" strokeWidth="1.5" filter="url(#chart-glow)" />
            <rect x="10" y="5" width="4" height="12" rx="1" fill="url(#chart-bear)" filter="url(#chart-glow)" />

            {/* Bull candle 2 */}
            <line x1="18" y1="8" x2="18" y2="16" stroke="var(--accent-info)" strokeWidth="1.5" filter="url(#chart-glow)" />
            <rect x="16" y="10" width="4" height="4" rx="1" fill="url(#chart-bull)" filter="url(#chart-glow)" />
            {/* Dynamic trend line overlay */}
            <path d="M 3 14 L 10 6 L 15 10 L 22 4" stroke="currentColor" strokeWidth="1" opacity="0.8" strokeLinecap="round" strokeDasharray="3 3" />
        </svg>
    );
}

/**
 * TradingIcon — Nöral ağ: 3 düğüm + bağlantı çizgileri + çıktı sinyali
 */
export function TradingIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="trade-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-negative)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <filter id="trade-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="2" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Grid structure */}
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="0.5" strokeDasharray="1 3" opacity="0.2" />
            {/* Exchange arrows complex */}
            <path d="M 14 5 L 19 10 L 14 15" stroke="url(#trade-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="var(--accent-negative-10)" filter="url(#trade-glow)" />
            <path d="M 19 10 L 4 10" stroke="var(--accent-negative)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="3 3" filter="url(#trade-glow)" />

            <path d="M 10 19 L 5 14 L 10 9" stroke="url(#trade-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="var(--accent-info-10)" filter="url(#trade-glow)" />
            <path d="M 5 14 L 20 14" stroke="var(--accent-info)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="3 3" filter="url(#trade-glow)" />

            {/* Central glowing node */}
            <circle cx="12" cy="12" r="3" fill="url(#trade-grad)" filter="url(#trade-glow)" />
            <circle cx="12" cy="12" r="1" fill="currentColor" />
            <circle cx="4" cy="10" r="1.5" fill="var(--accent-negative)" filter="url(#trade-glow)" />
            <circle cx="20" cy="14" r="1.5" fill="var(--accent-info)" filter="url(#trade-glow)" />
        </svg>
    );
}

/**
 * AnalysisIcon — Büyüteç içinde micro trend eğrisi
 */
export function AnalysisIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="ai-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-warning)" />
                    <stop offset="100%" stopColor="var(--accent-negative)" />
                </linearGradient>
                <filter id="ai-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Lens scope backdrop */}
            <path d="M 2 10 L 4 10 M 10 2 L 10 4 M 16 10 L 18 10 M 10 16 L 10 18" stroke="currentColor" strokeWidth="0.5" opacity="0.4" />
            {/* Cyber eye / Magnifier */}
            <circle cx="10" cy="10" r="7" stroke="url(#ai-grad)" strokeWidth="1.5" fill="var(--accent-negative-10)" filter="url(#ai-glow)" />
            {/* Lens flare / inner targeting */}
            <circle cx="10" cy="10" r="3" stroke="var(--accent-warning)" strokeWidth="1" strokeDasharray="1 2" opacity="0.5" filter="url(#ai-glow)" />
            <path d="M 10 10 L 10 6" stroke="var(--accent-warning)" strokeWidth="1" filter="url(#ai-glow)" />
            <path d="M 10 10 L 13 10" stroke="var(--accent-negative)" strokeWidth="1" filter="url(#ai-glow)" />
            {/* Handle as a circuit trace */}
            <path d="M 15 15 L 18 18 L 18 22 M 18 18 L 22 18" stroke="url(#ai-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter="url(#ai-glow)" />
            <circle cx="22" cy="18" r="1.5" fill="var(--accent-negative)" />
            <circle cx="18" cy="22" r="1.5" fill="var(--accent-warning)" />
            {/* Sine wave traversing eye */}
            <path d="M 5 12 Q 7 7 10 10 T 15 8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.8" />
            <circle cx="15" cy="8" r="1" fill="currentColor" filter="url(#ai-glow)" />
        </svg>
    );
}

/**
 * SignalsIcon — Radar dalgaları (concentric arcs) + merkez nokta
 */
export function SignalsIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="sig-grad" x1="50%" y1="100%" x2="50%" y2="0%">
                    <stop offset="0%" stopColor="var(--accent-positive)" />
                    <stop offset="50%" stopColor="var(--accent-info)" />
                    <stop offset="100%" stopColor="var(--accent-purple)" />
                </linearGradient>
                <filter id="sig-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="2" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Radar base sweep */}
            <path d="M 2 22 L 22 22 L 12 12 Z" fill="url(#sig-grad)" opacity="0.15" />
            <line x1="12" y1="22" x2="12" y2="12" stroke="currentColor" strokeWidth="1" strokeDasharray="1 2" opacity="0.4" />
            <line x1="2" y1="22" x2="22" y2="22" stroke="currentColor" strokeWidth="1" strokeLinecap="round" opacity="0.2" />

            {/* Broadcasting arcs */}
            <path d="M 5 15 Q 12 8 19 15" stroke="url(#sig-grad)" strokeWidth="1.5" strokeLinecap="round" filter="url(#sig-glow)" />
            <path d="M 8 18 Q 12 14 16 18" stroke="var(--accent-info)" strokeWidth="2" strokeLinecap="round" filter="url(#sig-glow)" />
            <path d="M 2 12 Q 12 2 22 12" stroke="var(--accent-purple)" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4 2" filter="url(#sig-glow)" />

            {/* Epicenters */}
            <circle cx="12" cy="22" r="3" fill="var(--accent-positive)" filter="url(#sig-glow)" />
            <circle cx="12" cy="22" r="1.5" fill="currentColor" />

            {/* Satellite nodes */}
            <circle cx="5" cy="15" r="1.5" fill="var(--accent-info)" filter="url(#sig-glow)" />
            <circle cx="19" cy="15" r="1.5" fill="var(--accent-info)" filter="url(#sig-glow)" />
        </svg>
    );
}

// ─── PANEL ICONS ──────────────────────────────────────────────────────────────

/**
 * PulseIcon — Kalp atış nabzı + sinyal yıldızı
 */
export function PulseIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="pulse-grad" x1="0%" y1="50%" x2="100%" y2="50%">
                    <stop offset="0%" stopColor="var(--accent-info)" stopOpacity="0" />
                    <stop offset="30%" stopColor="var(--accent-info)" />
                    <stop offset="70%" stopColor="var(--accent-purple)" />
                    <stop offset="100%" stopColor="var(--accent-negative)" stopOpacity="0" />
                </linearGradient>
                <filter id="pulse-glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Grid bg */}
            <path d="M 2 12 L 22 12 M 12 2 L 12 22" stroke="currentColor" strokeWidth="0.5" strokeDasharray="1 3" opacity="0.2" />

            {/* Signal wave */}
            <path d="M 1 12 L 5 12 L 8 5 L 12 19 L 16 9 L 19 12 L 23 12" stroke="url(#pulse-grad)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" filter="url(#pulse-glow)" />

            {/* Nodes */}
            <circle cx="8" cy="5" r="2" fill="var(--accent-info)" filter="url(#pulse-glow)" />
            <circle cx="12" cy="19" r="2" fill="var(--accent-purple)" filter="url(#pulse-glow)" />
            <circle cx="16" cy="9" r="2" fill="var(--accent-negative)" filter="url(#pulse-glow)" />
        </svg>
    );
}

/**
 * EmelIcon — 9 nokta 3×3 checkpoint grid, köşeleri vurgulu
 */
export function EmelIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="emel-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-negative)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <filter id="emel-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="2" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Neural Net connections */}
            <path d="M 4 4 L 20 20 M 20 4 L 4 20 M 12 2 L 12 22 M 2 12 L 22 12" stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
            {/* Sub glow lines */}
            <path d="M 6 12 L 12 6 L 18 12 L 12 18 Z" stroke="url(#emel-grad)" strokeWidth="1" strokeDasharray="2 2" filter="url(#emel-glow)" opacity="0.6" />
            {/* Core brain/grid */}
            <rect x="7" y="7" width="10" height="10" rx="3" stroke="url(#emel-grad)" strokeWidth="2" filter="url(#emel-glow)" />
            <circle cx="12" cy="12" r="2.5" fill="var(--accent-negative)" filter="url(#emel-glow)" />
            {/* Floating nodes */}
            <circle cx="6" cy="6" r="2" fill="var(--accent-info)" filter="url(#emel-glow)" />
            <circle cx="18" cy="6" r="2" fill="var(--accent-info)" filter="url(#emel-glow)" />
            <circle cx="6" cy="18" r="2" fill="var(--accent-info)" filter="url(#emel-glow)" />
            <circle cx="18" cy="18" r="2" fill="var(--accent-info)" filter="url(#emel-glow)" />
        </svg>
    );
}

/**
 * SMCIcon — Smart Money: para blokları + akış oku
 */
export function SMCIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="smc-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-positive)" />
                    <stop offset="100%" stopColor="var(--accent-warning)" />
                </linearGradient>
                <filter id="smc-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Order block rectangles */}
            <rect x="2" y="14" width="9" height="5" rx="1.5" stroke="url(#smc-grad)" strokeWidth="1.5" fill="var(--accent-positive-15)" filter="url(#smc-glow)" />
            <rect x="2" y="8" width="8" height="3" rx="1" stroke="var(--accent-warning)" strokeWidth="1" opacity="0.6" />
            {/* Flow arrow to right */}
            <path d="M13 12 L19 12" stroke="url(#smc-grad)" strokeWidth="2" strokeLinecap="round" filter="url(#smc-glow)" />
            <path d="M16 8 L20 12 L16 16" stroke="url(#smc-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter="url(#smc-glow)" />
            {/* Target circle */}
            <circle cx="20" cy="12" r="2" fill="var(--accent-warning)" filter="url(#smc-glow)" />
        </svg>
    );
}

/**
 * MTFIcon — Katmanlı timeframe: 4 paralel katman artan yükseklikte
 */
export function MTFIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="mtf-grad" x1="0%" y1="100%" x2="0%" y2="0%">
                    <stop offset="0%" stopColor="var(--accent-info)" />
                    <stop offset="100%" stopColor="var(--accent-positive)" />
                </linearGradient>
                <filter id="mtf-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Layer 1 — M5 */}
            <rect x="2" y="19" width="20" height="3" rx="1" stroke="currentColor" strokeWidth="0.5" fill="var(--accent-info-10)" />
            {/* Layer 2 — H1 */}
            <rect x="3" y="14" width="18" height="3" rx="1" stroke="currentColor" strokeWidth="0.5" fill="var(--accent-positive-10)" />
            {/* Layer 3 — H4 */}
            <rect x="5" y="9" width="14" height="3" rx="1" stroke="currentColor" strokeWidth="0.5" fill="var(--accent-info-20)" />
            {/* Layer 4 — D1 */}
            <rect x="8" y="4" width="8" height="3" rx="1" stroke="currentColor" strokeWidth="0.5" fill="var(--accent-positive-20)" />
            {/* Signal line crossing all layers */}
            <polyline points="7,22 10,15 14,10 12,5" stroke="url(#mtf-grad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" filter="url(#mtf-glow)" />
            <circle cx="12" cy="5" r="2.5" fill="var(--accent-positive)" filter="url(#mtf-glow)" />
        </svg>
    );
}

/**
 * RiskIcon — Özel terazi: merkez direk + iki kefe
 */
export function RiskIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="risk-up" x1="0%" y1="100%" x2="0%" y2="0%">
                    <stop offset="0%" stopColor="var(--accent-positive)" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="var(--accent-positive)" />
                </linearGradient>
                <linearGradient id="risk-down" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-negative)" stopOpacity="0.5" />
                    <stop offset="100%" stopColor="var(--accent-negative)" />
                </linearGradient>
                <filter id="risk-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Center Fulcrum */}
            <path d="M12 21 L 10 23 L 14 23 Z" fill="currentColor" opacity="0.3" />
            <line x1="12" y1="21" x2="12" y2="12" stroke="currentColor" strokeWidth="1.5" opacity="0.5" />

            {/* Beam (slanted to right) */}
            <line x1="4" y1="14" x2="20" y2="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />

            {/* Left Pan (Reward) */}
            <polyline points="3,14.5 5,19 7,14" stroke="var(--accent-positive)" strokeWidth="1" strokeLinejoin="round" />
            <path d="M3 19 Q5 20 7 19 Z" fill="url(#risk-up)" filter="url(#risk-glow)" />

            {/* Right Pan (Risk) */}
            <polyline points="17,10.5 19,15 21,10" stroke="var(--accent-negative)" strokeWidth="1" strokeLinejoin="round" />
            <path d="M17 15 Q19 16 21 15 Z" fill="url(#risk-down)" filter="url(#risk-glow)" />
            <circle cx="19" cy="13" r="1.5" fill="var(--accent-negative)" filter="url(#risk-glow)" />
        </svg>
    );
}

/**
 * PatternIcon — Ascending triangle pattern (geometrik şekil)
 */
export function PatternIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="pat-grad" x1="0%" y1="100%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="var(--accent-negative)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <filter id="pat-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Grid structure */}
            <path d="M 2 20 L 22 20 M 2 10 L 22 10" stroke="currentColor" strokeWidth="0.5" strokeDasharray="1 3" opacity="0.3" />
            {/* Ascending Wedge */}
            <path d="M 4 20 L 18 10 Z" stroke="var(--accent-info)" strokeWidth="1.5" strokeLinecap="round" filter="url(#pat-glow)" />
            <path d="M 2 10 L 18 10 Z" stroke="var(--accent-negative)" strokeWidth="1.5" strokeLinecap="round" filter="url(#pat-glow)" />
            {/* Breakout Arrow */}
            <path d="M 18 10 L 22 5" stroke="url(#pat-grad)" strokeWidth="2.5" strokeLinecap="round" filter="url(#pat-glow)" />
            <polyline points="18,5 22,5 22,9" stroke="url(#pat-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter="url(#pat-glow)" />
            {/* Convergence Node */}
            <circle cx="18" cy="10" r="2.5" fill="var(--accent-info)" filter="url(#pat-glow)" />
        </svg>
    );
}

/**
 * HarmonicIcon — Butterfly / Gartley kelebek forması
 */
export function HarmonicIcon({ className, size = 18, style, strokeWidth = 1.5 }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* X-A-B-C-D harmonic points path */}
            {/* X */}
            <circle cx="2" cy="18" r="1.2" fill="currentColor" strokeWidth="0" />
            {/* A */}
            <circle cx="7" cy="5" r="1.2" fill="currentColor" strokeWidth="0" />
            {/* B */}
            <circle cx="12" cy="13" r="1.2" fill="currentColor" strokeWidth="0" />
            {/* C */}
            <circle cx="17" cy="7" r="1.2" fill="currentColor" strokeWidth="0" />
            {/* D */}
            <circle cx="22" cy="19" r="1.2" fill="currentColor" strokeWidth="0" />
            {/* Lines X→A→B→C→D */}
            <polyline points="2,18 7,5 12,13 17,7 22,19" />
            {/* XD connecting line (pattern closure) */}
            <line x1="2" y1="18" x2="22" y2="19" strokeDasharray="2 1.5" opacity="0.4" />
        </svg>
    );
}

/**
 * WhaleIcon — Balina silueti: kavislı sırt + kuyruk yüzgeci
 */
export function WhaleIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Body */}
            <path d="M2 14 Q3 8 9 9 Q15 10 18 12 Q20 13 20 15 Q18 17 15 16 Q10 15 6 16 Q3 17 2 14Z" />
            {/* Tail fin */}
            <path d="M20 15 Q22 11 23 9" />
            <path d="M20 15 Q22 17 23 20" />
            {/* Blow hole spout */}
            <path d="M10 9 Q10 6 12 4" strokeWidth="1" />
            <path d="M12 4 Q11 3 10 2 M12 4 Q13 3 14 2" strokeWidth="1" />
            {/* Eye */}
            <circle cx="7" cy="12" r="0.8" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * COTIcon — Commitment of Traders: büyük histogram blokları
 */
export function COTIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Large bullish bar (commercials) */}
            <rect x="2" y="6" width="5" height="16" rx="0.8" strokeWidth="1.5" />
            {/* Medium bar */}
            <rect x="9.5" y="10" width="5" height="12" rx="0.8" opacity="0.8" />
            {/* Short bearish bar */}
            <rect x="17" y="14" width="5" height="8" rx="0.8" opacity="0.6" />
            {/* Net position line */}
            <polyline points="4.5,6 12,8 19.5,12" strokeWidth="1.2" strokeDasharray="2 1.5" />
            {/* Baseline */}
            <line x1="2" y1="22" x2="22" y2="22" strokeWidth="0.8" opacity="0.4" />
        </svg>
    );
}

/**
 * SeasonalityIcon — Yıl döngüsü: çember + 4 mevsim dilimleri + trend eğrisi
 */
export function SeasonalityIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Outer ring */}
            <circle cx="12" cy="12" r="9" />
            {/* Quarter dividers */}
            <line x1="12" y1="3" x2="12" y2="21" strokeWidth="0.8" opacity="0.3" />
            <line x1="3" y1="12" x2="21" y2="12" strokeWidth="0.8" opacity="0.3" />
            {/* Seasonal pattern inside (sinusoidal arc) */}
            <path d="M3 12 Q5 7 8 10 Q10 12 12 9 Q14 6 17 9 Q20 12 21 12" strokeWidth="1.3" />
            {/* Center dot = current */}
            <circle cx="12" cy="9" r="1.2" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

import {
    LogOut,
    Settings,
    ShieldAlert,
    HelpCircle,
    ExternalLink,
    Crown,
    Sparkles,
    Zap,
    CheckCircle2,
    AlertTriangle,
    Info,
    ChevronDown,
    LayoutDashboard,
    LineChart,
    Activity,
    BarChart3,
    ListRestart,
    Mail,
    Earth,
    Shield,
    FileText,
    User,
    PanelLeftClose,
    PanelLeftOpen,
    Orbit,
    Globe
} from 'lucide-react';

/**
 * LearningIcon — Kitap + üzerinde sinyal büyümesi
 */
export function LearningIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Book left page */}
            <path d="M4 4 Q4 2 6 2 L12 2 L12 20 L6 20 Q4 20 4 18Z" />
            {/* Book right page */}
            <path d="M12 2 L18 2 Q20 2 20 4 L20 18 Q20 20 18 20 L12 20Z" />
            {/* Spine */}
            <line x1="12" y1="2" x2="12" y2="20" />
            {/* Text lines left */}
            <line x1="6" y1="7" x2="10.5" y2="7" strokeWidth="1" />
            <line x1="6" y1="10" x2="10.5" y2="10" strokeWidth="1" />
            <line x1="6" y1="13" x2="10.5" y2="13" strokeWidth="1" />
            {/* Growing chart on right side */}
            <polyline points="13.5,17 15,13 16.5,15 18.5,9" strokeWidth="1.3" />
            <circle cx="18.5" cy="9" r="1" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * StrategyIcon — Optimizasyon döngüsü: döngüsel ok + merkez hedef
 */
export function StrategyIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="strat-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-negative)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <filter id="strat-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Circular arrow loop */}
            <path d="M12 3 A9 9 0 1 1 4.2 17.5" stroke="url(#strat-grad)" strokeWidth="2" strokeLinecap="round" filter="url(#strat-glow)" />
            {/* Arrow tip */}
            <polyline points="2,14 4.2,17.5 7.5,16" stroke="url(#strat-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter="url(#strat-glow)" />
            {/* Center target: concentric rings */}
            <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1" opacity="0.5" strokeDasharray="2 2" />
            <circle cx="12" cy="12" r="1.5" fill="var(--accent-info)" filter="url(#strat-glow)" />
            <circle cx="12" cy="12" r="7" stroke="var(--accent-negative)" strokeWidth="0.5" opacity="0.3" />
        </svg>
    );
}

/**
 * NewsIcon — Sinyal + yazı satırları (haber akışı)
 */
export function NewsIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Main container */}
            <rect x="2" y="3" width="20" height="18" rx="1.5" />
            {/* Signal icon area (top-left) */}
            <rect x="4" y="5" width="6" height="6" rx="1" />
            {/* Signal arcs inside */}
            <path d="M5.5 9.5 A2 2 0 0 1 5.5 6.5" strokeWidth="1" />
            <path d="M8.5 6.5 A2 2 0 0 1 8.5 9.5" strokeWidth="1" />
            {/* Headline text lines */}
            <line x1="12" y1="6" x2="19" y2="6" strokeWidth="1.5" />
            <line x1="12" y1="9" x2="19" y2="9" strokeWidth="1" opacity="0.6" />
            {/* Body text lines */}
            <line x1="4" y1="14" x2="20" y2="14" strokeWidth="1" opacity="0.5" />
            <line x1="4" y1="17" x2="20" y2="17" strokeWidth="1" opacity="0.5" />
            <line x1="4" y1="20" x2="14" y2="20" strokeWidth="1" opacity="0.5" />
        </svg>
    );
}

/**
 * COMEXIcon — Altın bar + haber kabarcığı
 */
export function COMEXIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Gold bar */}
            <rect x="2" y="13" width="13" height="7" rx="1" />
            {/* Gold sheen lines */}
            <line x1="5" y1="15" x2="12" y2="15" strokeWidth="0.8" opacity="0.5" />
            <line x1="5" y1="17" x2="12" y2="17" strokeWidth="0.8" opacity="0.5" />
            {/* News bubble */}
            <path d="M13 2 Q20 2 22 7 Q22 11 18 12 Q17 12 17 14 L15 12 Q13 12 12 10 Q10 6 13 2Z" />
            {/* Exclamation inside bubble */}
            <line x1="17" y1="5" x2="17" y2="9" strokeWidth="1.5" />
            <circle cx="17" cy="10.5" r="0.7" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * CandlestickPatternIcon — Doji + Hammer + Engulfing yan yana
 */
export function CandlestickPatternIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Doji */}
            <line x1="5" y1="4" x2="5" y2="20" />
            <line x1="3" y1="12" x2="7" y2="12" strokeWidth="2.5" />

            {/* Hammer */}
            <line x1="11" y1="6" x2="11" y2="10" />
            <rect x="9.5" y="10" width="3" height="5" rx="0.5" />
            <line x1="11" y1="15" x2="11" y2="20" strokeWidth="2.5" />

            {/* Bullish engulfing (two candles) */}
            <rect x="15" y="9" width="2.5" height="7" rx="0.4" fill="currentColor" fillOpacity="0.15" />
            <rect x="18" y="6" width="3.5" height="12" rx="0.4" />
            <line x1="16.25" y1="5" x2="16.25" y2="9" strokeWidth="1" />
            <line x1="19.75" y1="4" x2="19.75" y2="6" strokeWidth="1" />
            <line x1="19.75" y1="18" x2="19.75" y2="21" strokeWidth="1" />
        </svg>
    );
}

/**
 * SentimentIcon — AI duygu göstergesi: yarım gauge + ibre
 */
export function SentimentIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Gauge outer arc */}
            <path d="M3 16 A9 9 0 0 1 21 16" />
            {/* Gauge tick marks */}
            <line x1="3" y1="16" x2="4.5" y2="14" strokeWidth="1" />
            <line x1="12" y1="7" x2="12" y2="9" strokeWidth="1" />
            <line x1="21" y1="16" x2="19.5" y2="14" strokeWidth="1" />
            {/* Gauge zones */}
            <path d="M3 16 A9 9 0 0 1 7.5 8.8" strokeWidth="2.5" opacity="0.25" />
            <path d="M7.5 8.8 A9 9 0 0 1 16.5 8.8" strokeWidth="2.5" opacity="0.2" />
            <path d="M16.5 8.8 A9 9 0 0 1 21 16" strokeWidth="2.5" opacity="0.15" />
            {/* Needle pointing right (bullish) */}
            <line x1="12" y1="16" x2="16" y2="10" strokeWidth="2" />
            {/* Pivot */}
            <circle cx="12" cy="16" r="2" />
            {/* Base line */}
            <line x1="4" y1="19" x2="20" y2="19" strokeWidth="0.8" opacity="0.4" />
        </svg>
    );
}

/**
 * InstitutionalIcon — Bina kolonları + yukarı ok
 */
export function InstitutionalIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Building frame */}
            <rect x="3" y="10" width="18" height="12" rx="0.5" />
            {/* Roof triangle */}
            <polyline points="2,10 12,3 22,10" />
            {/* Columns */}
            <line x1="7" y1="10" x2="7" y2="22" />
            <line x1="12" y1="10" x2="12" y2="22" />
            <line x1="17" y1="10" x2="17" y2="22" />
            {/* Arrow overlay */}
            <circle cx="18" cy="6" r="3.5" style={{ fill: "var(--tw-bg-opacity, currentColor)" }} strokeWidth="0" opacity="0" />
            <polyline points="20,8 20,4 16,4" strokeWidth="1.5" />
            <line x1="16" y1="8" x2="20" y2="4" strokeWidth="1.5" />
        </svg>
    );
}

/**
 * HistoryIcon — Spiral saat + onay işareti
 */
export function HistoryIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="hist-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-info)" />
                    <stop offset="100%" stopColor="var(--accent-negative)" />
                </linearGradient>
                <filter id="hist-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Clock outline */}
            <circle cx="12" cy="12" r="8" stroke="url(#hist-grad)" strokeWidth="1.5" strokeDasharray="4 2" filter="url(#hist-glow)" />
            <circle cx="12" cy="12" r="6" stroke="var(--accent-info)" strokeWidth="0.5" opacity="0.5" />
            {/* Hands */}
            <polyline points="12,7 12,12 15,15" stroke="url(#hist-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter="url(#hist-glow)" />
            {/* Rewind motion */}
            <path d="M 4 8 C 2 5 6 3 9 3" stroke="var(--accent-info)" strokeWidth="1.5" strokeLinecap="round" filter="url(#hist-glow)" />
            <polyline points="4,8 8,6 6,10" stroke="var(--accent-info)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" filter="url(#hist-glow)" />
            {/* Data point success */}
            <circle cx="12" cy="12" r="1.5" fill="#fff" />
        </svg>
    );
}

/**
 * OrderBlockIcon — Dikdörtgen bloklar + yatay fiyat çizgisi
 */
export function OrderBlockIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="ob-up" x1="0%" y1="100%" x2="0%" y2="0%">
                    <stop offset="0%" stopColor="var(--accent-positive)" />
                    <stop offset="100%" stopColor="var(--accent-info)" />
                </linearGradient>
                <linearGradient id="ob-down" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--accent-negative)" />
                    <stop offset="100%" stopColor="var(--accent-negative)" />
                </linearGradient>
                <filter id="ob-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Supply Zone (Top) */}
            <rect x="3" y="3" width="18" height="5" rx="1" stroke="url(#ob-down)" strokeWidth="1.5" fill="var(--accent-negative-15)" filter="url(#ob-glow)" />
            <line x1="2" y1="8" x2="22" y2="8" stroke="var(--accent-negative)" strokeWidth="1" strokeDasharray="2 3" opacity="0.8" />

            {/* Demand Zone (Bottom) */}
            <rect x="3" y="16" width="18" height="5" rx="1" stroke="url(#ob-up)" strokeWidth="1.5" fill="var(--accent-positive-15)" filter="url(#ob-glow)" />
            <line x1="2" y1="16" x2="22" y2="16" stroke="var(--accent-positive)" strokeWidth="1" strokeDasharray="2 3" opacity="0.8" />

            {/* Price wandering line interacting with blocks */}
            <path d="M 6 12 L 8 5 L 12 19 L 16 12 L 18 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.8" />
            <circle cx="8" cy="5" r="2" fill="var(--accent-negative)" filter="url(#ob-glow)" />
            <circle cx="12" cy="19" r="2" fill="var(--accent-positive)" filter="url(#ob-glow)" />
        </svg>
    );
}

/**
 * RhythmIcon — Dalga + nokta ritim deseni
 */
export function RhythmIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
            <defs>
                <linearGradient id="rhythm-grad" x1="0%" y1="50%" x2="100%" y2="50%">
                    <stop offset="0%" stopColor="var(--accent-info)" />
                    <stop offset="50%" stopColor="var(--accent-purple)" />
                    <stop offset="100%" stopColor="var(--accent-negative)" />
                </linearGradient>
                <filter id="rhythm-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            {/* Frequency mesh */}
            <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="0.5" opacity="0.3" strokeDasharray="1 2" />
            {/* Double helix sine wave pattern */}
            <path d="M 2 12 C 5 2 9 2 12 12 C 15 22 19 22 22 12" stroke="url(#rhythm-grad)" strokeWidth="2" strokeLinecap="round" filter="url(#rhythm-glow)" />
            <path d="M 2 12 C 5 22 9 22 12 12 C 15 2 19 2 22 12" stroke="var(--accent-info)" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" filter="url(#rhythm-glow)" />

            {/* Intersection nodes */}
            <circle cx="12" cy="12" r="2.5" fill="var(--accent-negative)" filter="url(#rhythm-glow)" />
            <circle cx="2" cy="12" r="1.5" fill="var(--accent-info)" filter="url(#rhythm-glow)" />
            <circle cx="22" cy="12" r="1.5" fill="var(--accent-negative)" filter="url(#rhythm-glow)" />
        </svg>
    );
}

/**
 * ForexsAILogoIcon — Logo: F harfi şeklinde sinyal dalgası
 */
export function ForexsAILogoIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* ECG / pulse form embedding "F" shape */}
            <polyline points="2,16 5,16 7,10 9,20 11,6 13,16 16,16" />
            {/* Rising arrow at end */}
            <line x1="16" y1="16" x2="20" y2="8" />
            <polyline points="17.5,8 20,8 20,11" />
        </svg>
    );
}

/**
 * AdvancedAnalysisIcon — MTF çoklu zaman: üst üste kümülatif çizgiler
 */
export function AdvancedAnalysisIcon({ className, size = 18, style }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
            style={style}
        >
            {/* Line 1 (NASDAQ) */}
            <polyline points="2,18 6,13 10,15 14,8 18,10 22,6" />
            {/* Line 2 (XAUUSD) offset */}
            <polyline points="2,21 6,17 10,19 14,13 18,15 22,11" opacity="0.5" />
            {/* Axis */}
            <line x1="2" y1="2" x2="2" y2="22" strokeWidth="0.8" opacity="0.3" />
        </svg>
    );
}

export const NasdaqIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
        <defs>
            <linearGradient id="ndx-grad" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="var(--accent-positive)" />
                <stop offset="100%" stopColor="var(--accent-info)" />
            </linearGradient>
            <filter id="ndx-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="1.5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        {/* Background circuit */}
        <rect x="2" y="2" width="20" height="20" rx="4" stroke="currentColor" strokeWidth="1" opacity="0.15" strokeDasharray="3 3" />
        <path d="M 6 22 L 6 18 M 10 22 L 10 16 M 14 22 L 14 14 M 18 22 L 18 10" stroke="currentColor" strokeWidth="1.5" opacity="0.2" strokeLinecap="round" />
        {/* Main trend line */}
        <path d="M 4 16 L 9 10 L 14 13 L 20 4" stroke="url(#ndx-grad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" filter="url(#ndx-glow)" />
        {/* Highlight points */}
        <circle cx="20" cy="4" r="3" fill="var(--accent-info)" filter="url(#ndx-glow)" />
        <circle cx="9" cy="10" r="2" fill="var(--accent-positive)" filter="url(#ndx-glow)" />
        <path d="M 20 4 L 20 1" stroke="var(--accent-info)" strokeWidth="1.5" filter="url(#ndx-glow)" strokeLinecap="round" />
    </svg>
);

export const GoldIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
        <defs>
            <linearGradient id="gold-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="var(--accent-warning)" />
                <stop offset="50%" stopColor="var(--accent-warning)" />
                <stop offset="100%" stopColor="var(--accent-warning)" />
            </linearGradient>
            <filter id="gold-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <path d="M12 2 L16.5 7 L22 8 L17.5 12.5 L19 18.5 L12 15 L5 18.5 L6.5 12.5 L2 8 L7.5 7 Z" stroke="url(#gold-grad)" strokeWidth="1.5" fill="var(--accent-warning-15)" strokeLinecap="round" strokeLinejoin="round" filter="url(#gold-glow)" />
        <circle cx="12" cy="11.5" r="2.5" fill="var(--accent-warning)" filter="url(#gold-glow)" />
        {/* Tech orbits */}
        <circle cx="12" cy="11.5" r="7" stroke="var(--accent-warning)" strokeWidth="1" opacity="0.6" strokeDasharray="2 3" />
        <circle cx="12" cy="11.5" r="11" stroke="var(--accent-warning)" strokeWidth="0.5" opacity="0.4" strokeDasharray="4 4" />
    </svg>
);

export const OilIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
        <defs>
            <linearGradient id="oil-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="var(--accent-negative)" />
                <stop offset="100%" stopColor="var(--accent-negative)" />
            </linearGradient>
            <filter id="oil-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        {/* 3D Drop */}
        <path d="M12 2 C 12 2 4 10 4 16 C 4 20.418 7.582 24 12 24 C 16.418 24 20 20.418 20 16 C 20 10 12 2 12 2 Z" stroke="url(#oil-grad)" strokeWidth="1.5" fill="var(--accent-negative-15)" strokeLinecap="round" strokeLinejoin="round" filter="url(#oil-glow)" />
        <path d="M12 11 L 12 19" stroke="var(--accent-negative)" strokeWidth="2.5" strokeLinecap="round" filter="url(#oil-glow)" />
        <circle cx="12" cy="15" r="2.5" fill="var(--accent-negative)" filter="url(#oil-glow)" />
        {/* Cyber highlights */}
        <path d="M 6 16 Q 6 13 12 8" stroke="var(--accent-negative)" strokeWidth="1.5" opacity="0.8" strokeLinecap="round" strokeDasharray="1 3" />
    </svg>
);

export const DaxIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ ...style, overflow: 'visible' }}>
        <defs>
            <linearGradient id="dax-grad" x1="100%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="var(--accent-info)" />
                <stop offset="100%" stopColor="var(--accent-info)" />
            </linearGradient>
            <filter id="dax-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        {/* High-tech European core */}
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1" opacity="0.25" strokeDasharray="2 3" />
        <circle cx="12" cy="12" r="7" stroke="url(#dax-grad)" strokeWidth="2" filter="url(#dax-glow)" />
        <circle cx="12" cy="12" r="4" fill="var(--accent-info-20)" />
        {/* Nodes on outer ring */}
        <circle cx="12" cy="2" r="2" fill="var(--accent-info)" filter="url(#dax-glow)" />
        <circle cx="2" cy="12" r="2" fill="var(--accent-info)" filter="url(#dax-glow)" />
        <circle cx="22" cy="12" r="2" fill="var(--accent-info)" filter="url(#dax-glow)" />
        <circle cx="12" cy="22" r="2" fill="var(--accent-info)" filter="url(#dax-glow)" />
        {/* Inner intersecting shapes */}
        <path d="M 8 12 L 12 8 L 16 12 L 12 16 Z" stroke="var(--accent-info)" strokeWidth="1.5" fill="var(--accent-info)" fillOpacity="0.4" filter="url(#dax-glow)" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const LoadingIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={`animate-spin ${className}`} style={style}>
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        <circle cx="12" cy="12" r="2" fill="currentColor" />
    </svg>
);

export const ThemeSunIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" />
    </svg>
);

export const ThemeMoonIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z" />
        <path d="M19 3l-1.5 1.5 1.5 1.5" strokeOpacity={0.5} />
    </svg>
);

export const ArrowUpIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M12 19V5M5 12l7-7 7 7" />
    </svg>
);

export const ArrowDownIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M12 5v14M5 12l7 7 7-7" />
    </svg>
);

export const ChevronIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} style={style}>
        <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const SupportMailIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <path d="M3 8L10.8906 13.2604C11.5624 13.7083 12.4376 13.7083 13.1094 13.2604L21 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <rect x="3" y="5" width="18" height="14" rx="3" stroke="currentColor" strokeWidth="2" />
    </svg>
);

export const WebsiteIcon = (props: any) => <Earth {...props} />;
export const GlobeIcon = (props: any) => <Globe {...props} />;
export const SecurityShieldIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 12L11 14L15 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const TermsIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 13H16M8 17H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const UserProfileIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <path d="M20 21V19C20 16.7909 18.2091 15 16 15H8C5.79086 15 4 16.7909 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" />
    </svg>
);

export const LogoutIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <path d="M9 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M16 17L21 12L16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const NeutralIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

export const TargetIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ overflow: 'visible' }}>
        <defs>
            <filter id="target-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="1.5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.5" />
        <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="2" />
        <circle cx="12" cy="12" r="2.5" fill="currentColor" filter="url(#target-glow)" />
        <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="12" y1="18" x2="12" y2="22" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="2" y1="12" x2="6" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="18" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
);

export const InfoIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
);

export const CloseIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
);

export const ZapIcon = ({ size = 24, className = "", strokeWidth = 1 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ overflow: 'visible' }}>
        <defs>
            <linearGradient id="zap-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ffff00" />
                <stop offset="100%" stopColor="#ff9900" />
            </linearGradient>
            <filter id="zap-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="1.5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="url(#zap-grad)" stroke="#ffff00" strokeWidth={strokeWidth} strokeLinejoin="round" filter="url(#zap-glow)" />
    </svg>
);

export const ExpandIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polyline points="15 3 21 3 21 9" />
        <polyline points="9 21 3 21 3 15" />
        <line x1="21" y1="3" x2="14" y2="10" />
        <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
);

export const ShrinkIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polyline points="4 14 10 14 10 20" />
        <polyline points="20 10 14 10 14 4" />
        <line x1="14" y1="10" x2="21" y2="3" />
        <line x1="10" y1="14" x2="3" y2="21" />
    </svg>
);

export const SettingsIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} style={{ overflow: 'visible' }}>
        <defs>
            <filter id="set-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="1" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" stroke="currentColor" strokeWidth="1.5" opacity="0.7" />
        <circle cx="12" cy="12" r="4" stroke="var(--accent-info)" strokeWidth="2" filter="url(#set-glow)" />
        <circle cx="12" cy="12" r="1.5" fill="var(--accent-positive)" filter="url(#set-glow)" />
    </svg>
);

export const RotateIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M1 4v6h6" />
        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
    </svg>
);

export const AggressiveIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.5 3.5 6.5 1 1.5 2 3 2 5a7 7 0 1 1-14 0c0-3 2.5-5.5 5-8 0 2.5 2.5 3.5 2.5 6.5z" />
    </svg>
);

export const TrophyIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M8 21h8M12 17v4M7 4h10v6a5 5 0 01-10 0V4z" />
        <path d="M7 6H4v3a4 4 0 004 4v0" />
        <path d="M17 6h3v3a4 4 0 01-4 4v0" />
    </svg>
);

export const AlertIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01" />
    </svg>
);

export const BrainIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M12 5a3 3 0 10-5.997.125 4 4 0 00-2.526 5.77 4 4 0 00.556 6.588A4 4 0 1012 18Z" />
        <path d="M12 5a3 3 0 115.997.125 4 4 0 012.526 5.77 4 4 0 01-.556 6.588A4 4 0 1112 18Z" />
        <path d="M12 18V5M12 12H9M12 12h3M12 9H9M12 9h3M12 15H9M12 15h3" />
    </svg>
);

export const ClockIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
    </svg>
);

export const EyeIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
    </svg>
);

export const CheckCircleIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
        <path d="M22 4L12 14.01l-3-3" />
    </svg>
);

export const MountainIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M8 3l4 8 5-5 5 15H2L8 3z" />
    </svg>
);

export const ActivityIcon = ({ size = 24, className = "", style, strokeWidth = 1.5 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
);

export const DatabaseIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
);

export const ChevronUpIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <polyline points="18 15 12 9 6 15" />
    </svg>
);

export const ChevronDownIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <polyline points="6 9 12 15 18 9" />
    </svg>
);

export const ArrowUpRightIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <line x1="7" y1="17" x2="17" y2="7" />
        <polyline points="7 7 17 7 17 17" />
    </svg>
);

export const ArrowDownRightIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <line x1="7" y1="7" x2="17" y2="17" />
        <polyline points="17 7 17 17 7 17" />
    </svg>
);

export const MinusIcon = ({ size = 24, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

// TrendingUp Icon
export const TrendingUpIcon = ({ size = 24, className = "", style, strokeWidth = 1.5 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
    </svg>
);

// TrendingDown Icon
export const TrendingDownIcon = ({ size = 24, className = "", style, strokeWidth = 1.5 }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <polyline points="22 17 13.5 8.5 8.5 13.5 2 7" />
        <polyline points="16 17 22 17 22 11" />
    </svg>
);

// TrendingUp (alias for compatibility)
export const TrendingUp = TrendingUpIcon;
export const TrendingDown = TrendingDownIcon;


// NewspaperIcon - For News-Chart Correlation panel
export const NewspaperIcon = ({ size = 18, className = "", style }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-4 0v-9a2 2 0 0 1 2-2h2" />
        <path d="M9 7h5" />
        <path d="M9 11h5" />
        <path d="M9 15h5" />
        <circle cx="17" cy="8" r="2" fill="currentColor" opacity="0.3" />
    </svg>
);
