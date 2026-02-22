import React from "react";

interface IconProps {
    className?: string;
    size?: number;
    style?: React.CSSProperties;
}

// ─── SIDEBAR NAV ICONS ────────────────────────────────────────────────────────

/**
 * DashboardIcon — Dört köşe mini blok + merkezi sinyal nabzı
 */
export function DashboardIcon({ className, size = 18, style }: IconProps) {
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
            {/* Top‑left block */}
            <rect x="2" y="2" width="8" height="7" rx="1.5" />
            {/* Top‑right block */}
            <rect x="14" y="2" width="8" height="7" rx="1.5" />
            {/* Bottom‑left small block */}
            <rect x="2" y="13" width="8" height="9" rx="1.5" />
            {/* Bottom‑right sparkline area */}
            <rect x="14" y="13" width="8" height="9" rx="1.5" />
            {/* Mini sparkline inside bottom‑right */}
            <polyline points="15.5,19 17,16 18.5,18 20.5,15" strokeWidth="1.2" />
        </svg>
    );
}

/**
 * ChartsIcon — Stilize mum grafiği: 3 gövde + ince fitil çizgileri
 */
export function ChartsIcon({ className, size = 18, style }: IconProps) {
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
            {/* Candle 1 (bullish) */}
            <line x1="6" y1="2" x2="6" y2="5" />
            <rect x="4.5" y="5" width="3" height="9" rx="0.5" strokeWidth="1.5" />
            <line x1="6" y1="14" x2="6" y2="17" />

            {/* Candle 2 (bearish, taller) */}
            <line x1="12" y1="3" x2="12" y2="6" />
            <rect x="10.5" y="6" width="3" height="11" rx="0.5" strokeWidth="1.5" fill="currentColor" fillOpacity="0.15" />
            <line x1="12" y1="17" x2="12" y2="20" />

            {/* Candle 3 (bullish, short) */}
            <line x1="18" y1="5" x2="18" y2="8" />
            <rect x="16.5" y="8" width="3" height="7" rx="0.5" strokeWidth="1.5" />
            <line x1="18" y1="15" x2="18" y2="19" />

            {/* Baseline */}
            <line x1="2" y1="22" x2="22" y2="22" strokeWidth="1" opacity="0.4" />
        </svg>
    );
}

/**
 * TradingIcon — Nöral ağ: 3 düğüm + bağlantı çizgileri + çıktı sinyali
 */
export function TradingIcon({ className, size = 18, style }: IconProps) {
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
            {/* Input nodes */}
            <circle cx="4" cy="7" r="2" />
            <circle cx="4" cy="17" r="2" />
            {/* Hidden node */}
            <circle cx="12" cy="12" r="2.5" />
            {/* Output node */}
            <circle cx="20" cy="12" r="2" />

            {/* Connections input→hidden */}
            <line x1="6" y1="7" x2="9.5" y2="11" />
            <line x1="6" y1="17" x2="9.5" y2="13" />

            {/* Connections hidden→output */}
            <line x1="14.5" y1="12" x2="18" y2="12" />

            {/* Signal pulse on output */}
            <path d="M20 8 Q21.5 8 22 10" strokeWidth="1.2" opacity="0.6" />
        </svg>
    );
}

/**
 * AnalysisIcon — Büyüteç içinde micro trend eğrisi
 */
export function AnalysisIcon({ className, size = 18, style }: IconProps) {
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
            {/* Magnifier circle */}
            <circle cx="10.5" cy="10.5" r="7" />
            {/* Handle */}
            <line x1="15.8" y1="15.8" x2="21" y2="21" strokeWidth="2" />
            {/* Micro trend line inside lens */}
            <polyline points="6.5,12.5 8.5,9.5 10.5,11 12.5,7.5" strokeWidth="1.3" />
            {/* Small dot at end = current price */}
            <circle cx="12.5" cy="7.5" r="0.8" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * SignalsIcon — Radar dalgaları (concentric arcs) + merkez nokta
 */
export function SignalsIcon({ className, size = 18, style }: IconProps) {
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
            {/* Inner arc */}
            <path d="M8.5 18 A6 6 0 0 1 8.5 6" />
            <path d="M15.5 6 A6 6 0 0 1 15.5 18" />
            {/* Middle arc */}
            <path d="M5.5 21 A9.5 9.5 0 0 1 5.5 3" />
            <path d="M18.5 3 A9.5 9.5 0 0 1 18.5 21" />
            {/* Center dot = signal origin */}
            <circle cx="12" cy="12" r="1.5" fill="currentColor" strokeWidth="0" />
            {/* Vertical line below */}
            <line x1="12" y1="13.5" x2="12" y2="20" />
        </svg>
    );
}

// ─── PANEL ICONS ──────────────────────────────────────────────────────────────

/**
 * PulseIcon — Kalp atış nabzı + sinyal yıldızı
 */
export function PulseIcon({ className, size = 18, style }: IconProps) {
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
            {/* ECG pulse line */}
            <polyline points="2,12 5,12 7,6 9,18 11,9 13,15 15,12 22,12" />
            {/* Signal dot */}
            <circle cx="22" cy="12" r="1.5" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * EmelIcon — 9 nokta 3×3 checkpoint grid, köşeleri vurgulu
 */
export function EmelIcon({ className, size = 18, style }: IconProps) {
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
            {/* 3×3 dot grid */}
            <circle cx="5" cy="5" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="12" cy="5" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="19" cy="5" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="5" cy="12" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="12" cy="12" r="2.2" />
            <circle cx="19" cy="12" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="5" cy="19" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="12" cy="19" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="19" cy="19" r="1.5" fill="currentColor" strokeWidth="0" />
            {/* Checkpoint path connecting them */}
            <path d="M5,5 L12,12 L19,5 M5,19 L12,12 L19,19" strokeWidth="0.8" opacity="0.4" />
        </svg>
    );
}

/**
 * SMCIcon — Smart Money: para blokları + akış oku
 */
export function SMCIcon({ className, size = 18, style }: IconProps) {
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
            {/* Order block rectangles */}
            <rect x="2" y="14" width="9" height="4" rx="1" />
            <rect x="2" y="9" width="9" height="4" rx="1" />
            {/* Flow arrow to right */}
            <path d="M13 12 L19 12" />
            <path d="M16 8 L20 12 L16 16" />
            {/* Target circle */}
            <circle cx="20" cy="12" r="1.5" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * MTFIcon — Katmanlı timeframe: 4 paralel katman artan yükseklikte
 */
export function MTFIcon({ className, size = 18, style }: IconProps) {
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
            {/* Layer 1 — M5 (narrowest) */}
            <rect x="2" y="19" width="20" height="2.5" rx="0.8" />
            {/* Layer 2 — H1 */}
            <rect x="3" y="15" width="18" height="2.5" rx="0.8" opacity="0.8" />
            {/* Layer 3 — H4 */}
            <rect x="5" y="11" width="14" height="2.5" rx="0.8" opacity="0.6" />
            {/* Layer 4 — D1 (top, narrowest) */}
            <rect x="8" y="7" width="8" height="2.5" rx="0.8" opacity="0.4" />
            {/* Signal line crossing all layers */}
            <polyline points="7,22 10,16 14,12 12,8" strokeWidth="1.2" strokeDasharray="2 1.5" />
        </svg>
    );
}

/**
 * RiskIcon — Özel terazi: merkez direk + iki kefe
 */
export function RiskIcon({ className, size = 18, style }: IconProps) {
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
            {/* Center pole */}
            <line x1="12" y1="3" x2="12" y2="21" />
            {/* Base */}
            <line x1="7" y1="21" x2="17" y2="21" />
            {/* Cross bar */}
            <line x1="4" y1="9" x2="20" y2="9" />
            {/* Left pan (slightly low = risk) */}
            <path d="M4 9 Q2 13 4 15 Q6 17 8 15 Q10 13 8 9" />
            {/* Right pan (high = reward) */}
            <path d="M16 9 Q14 11 16 13 Q18 15 20 13 Q22 11 20 9" />
            {/* R/R ratio marks */}
            <line x1="12" y1="7" x2="12" y2="5" strokeWidth="1" />
            <circle cx="12" cy="5" r="1" fill="currentColor" strokeWidth="0" />
        </svg>
    );
}

/**
 * PatternIcon — Ascending triangle pattern (geometrik şekil)
 */
export function PatternIcon({ className, size = 18, style }: IconProps) {
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
            {/* Rising lower trendline */}
            <polyline points="2,20 8,16 14,13 20,10" />
            {/* Flat upper resistance */}
            <line x1="2" y1="10" x2="22" y2="10" />
            {/* Breakout arrow */}
            <polyline points="18,10 22,6 22,10" />
            {/* Converging wedge lines */}
            <line x1="2" y1="20" x2="22" y2="10" strokeDasharray="1.5 2" opacity="0.3" />
            {/* Candle bodies inside pattern */}
            <rect x="5" y="15" width="2" height="4" rx="0.4" opacity="0.5" />
            <rect x="10" y="12" width="2" height="3" rx="0.4" opacity="0.5" />
            <rect x="15" y="10.5" width="2" height="2.5" rx="0.4" opacity="0.5" />
        </svg>
    );
}

/**
 * HarmonicIcon — Butterfly / Gartley kelebek forması
 */
export function HarmonicIcon({ className, size = 18, style }: IconProps) {
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
            {/* Circular arrow loop */}
            <path d="M12 3 A9 9 0 1 1 4.2 17.5" />
            {/* Arrow tip */}
            <polyline points="2,14 4.2,17.5 7.5,16" />
            {/* Center target: concentric rings */}
            <circle cx="12" cy="12" r="4" />
            <circle cx="12" cy="12" r="1.5" fill="currentColor" strokeWidth="0" />
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
            {/* Clock circle */}
            <circle cx="11" cy="12" r="8" />
            {/* Clock hands */}
            <polyline points="11,7 11,12 14,15" />
            {/* Rewind arrow */}
            <path d="M3 7 Q2 3 6 2" />
            <polyline points="3,7 7,5 5,9" />
            {/* Small checkmark badge */}
            <circle cx="19" cy="19" r="3.5" strokeWidth="1" />
            <polyline points="17.5,19.5 18.5,20.5 21,17.5" strokeWidth="1.2" />
        </svg>
    );
}

/**
 * OrderBlockIcon — Dikdörtgen bloklar + yatay fiyat çizgisi
 */
export function OrderBlockIcon({ className, size = 18, style }: IconProps) {
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
            {/* Supply zone block (top) */}
            <rect x="3" y="4" width="18" height="4.5" rx="1" fill="currentColor" fillOpacity="0.08" />
            <line x1="3" y1="8.5" x2="21" y2="8.5" strokeWidth="1" />
            {/* Label marker */}
            <line x1="2" y1="4" x2="2" y2="8.5" strokeWidth="2.5" />

            {/* Price wandering line */}
            <polyline points="3,14 7,12 12,16 17,11 21,13" strokeWidth="1.3" />

            {/* Demand zone block (bottom) */}
            <rect x="3" y="17.5" width="18" height="4.5" rx="1" fill="currentColor" fillOpacity="0.08" />
            <line x1="3" y1="17.5" x2="21" y2="17.5" strokeWidth="1" />
            {/* Label marker */}
            <line x1="2" y1="17.5" x2="2" y2="22" strokeWidth="2.5" />
        </svg>
    );
}

/**
 * RhythmIcon — Dalga + nokta ritim deseni
 */
export function RhythmIcon({ className, size = 18, style }: IconProps) {
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
            {/* Sine wave upper */}
            <path d="M2 9 Q5 4 8 9 Q11 14 14 9 Q17 4 20 9 Q21.5 11.5 22 9" />
            {/* Sine wave lower (mirrored, phase shifted) */}
            <path d="M2 15 Q5 20 8 15 Q11 10 14 15 Q17 20 20 15 Q21.5 12.5 22 15" opacity="0.5" />
            {/* Rhythm dots */}
            <circle cx="8" cy="9" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="14" cy="9" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="20" cy="9" r="1.5" fill="currentColor" strokeWidth="0" />
            <circle cx="5" cy="12" r="0.8" fill="currentColor" strokeWidth="0" opacity="0.5" />
            <circle cx="11" cy="12" r="0.8" fill="currentColor" strokeWidth="0" opacity="0.5" />
            <circle cx="17" cy="12" r="0.8" fill="currentColor" strokeWidth="0" opacity="0.5" />
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
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M3 3v18h18" />
        <path d="M18 7l-5 5-3-3-4 4" />
        <path d="M13 7h5v5" />
        <rect x="2" y="2" width="20" height="20" rx="2" strokeOpacity={0.2} />
    </svg>
);

export const GoldIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M12 2l3 6 6 1-4.5 4.5L18 20l-6-3-6 3 1.5-6.5L3 9l6-1 3-6z" />
        <path d="M12 7l1.5 3 3 0.5-2.25 2.25 0.75 3.25-3-1.5-3 1.5 0.75-3.25-2.25-2.25 3-0.5L12 7z" strokeOpacity={0.5} strokeWidth={1} />
    </svg>
);

export const OilIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M12 22s-8-6.5-8-12a8 8 0 1 1 16 0c0 5.5-8 12-8 12z" />
        <path d="M12 10l-2 2h4l-2 2" strokeOpacity={0.8} />
    </svg>
);

export const DaxIcon = ({ size = 24, className = "", style = {} }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
        <path d="M2 5h20M2 12h20M2 19h20" strokeOpacity={0.3} />
        <circle cx="12" cy="12" r="10" />
        <path d="M9 12l2 2 4-4" />
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

export const WebsiteIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
        <path d="M3.6 9H20.4M3.6 15H20.4M12 3V21M12 3C10 3 8 7 8 12C8 17 10 21 12 21M12 3C14 3 16 7 16 12C16 17 14 21 12 21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
);

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
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="6" />
        <circle cx="12" cy="12" r="2" />
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

export const ZapIcon = ({ size = 24, className = "" }: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
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
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
        <circle cx="12" cy="12" r="3" />
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
