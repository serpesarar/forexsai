// Harmonic Pattern Visualizer - Type Definitions (V2 - Range-based Fibonacci)

export interface PivotPoint {
    time: number;      // Unix timestamp (seconds)
    price: number;     // Price at pivot (high for pivot high, low for pivot low)
    high: number;
    low: number;
    type: 'high' | 'low';
    index: number;     // Index in candle array
}

// Range-based Fibonacci ratio for accurate detection
export interface FibRange {
    min: number;
    max: number;
    ideal: number;     // Perfect ratio for confidence scoring
}

// Harmonic pattern definition with range-based ratios
export interface HarmonicPatternDef {
    name: string;
    nameTr: string;
    emoji: string;
    color: string;
    // B = AB/XA retracement
    B: FibRange;
    // C = BC/AB retracement
    C: FibRange;
    // D_XA = AD/XA (retracement or extension of XA leg)
    D_XA: FibRange;
    // D_BC = CD/BC extension
    D_BC: FibRange;
    // isMajor: true = XABCD 5-point, false = ABCD 4-point
    isMajor: boolean;
}

export type PatternStatus = 'COMPLETED' | 'FORMING';

export interface HarmonicPattern {
    type: string;
    name: string;
    points: {
        X: PivotPoint;
        A: PivotPoint;
        B: PivotPoint;
        C: PivotPoint;
        D: PivotPoint;
    };
    color: string;
    fibRatios: {
        ab: number;
        bc: number;
        cd: number;
        xd: number;
    };
    direction: 'BULLISH' | 'BEARISH';
    confidence: number;  // 0-100
    isProjected?: boolean;
    projectedD?: { price: number; priceMin: number; priceMax: number; time: number };
    target_price?: number;
    stop_loss?: number;
    status: PatternStatus;
    candleIndices: number[];  // All candle indices between X and D
}

export interface ClassicPattern {
    type: string;
    name: string;
    points: PivotPoint[];
    color: string;
    direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    neckline?: number;
    confidence: number;
    target_price?: number;
    stop_loss?: number;
    status: PatternStatus;
    candleIndices: number[];  // All candle indices in the pattern
}

export type DetectedPattern = HarmonicPattern | ClassicPattern;

export interface DetectionOptions {
    deviation: number;       // ZigZag deviation %
    fibTolerance: number;    // Extra tolerance on fib ranges (additive)
    maxPivots: number;       // Max pivots to scan
    minConfidence: number;   // Minimum confidence to report
}

export interface CandleData {
    time: number;       // Unix timestamp (seconds)
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
}

// ─── COLOR CONSTANTS ─────────────────────────────────────────────────
// Big formations (Harmonic XABCD) → Galaxy orange family
export const HARMONIC_COLOR = '#FF8C00';
export const HARMONIC_COLOR_DARK = '#FF6B35';
export const HARMONIC_COLOR_CANDLE = '#FF9D2F';
export const HARMONIC_COLOR_WICK = '#CC7000';
export const HARMONIC_FILL = 'rgba(255, 140, 0, 0.10)';
export const HARMONIC_GLOW = 'rgba(255, 140, 0, 0.5)';

// Small formations (Classic) → Galaxy blue family
export const CLASSIC_COLOR = '#00BFFF';
export const CLASSIC_COLOR_DARK = '#87CEEB';
export const CLASSIC_COLOR_CANDLE = '#4DC9F6';
export const CLASSIC_COLOR_WICK = '#0090CC';
export const CLASSIC_FILL = 'rgba(0, 191, 255, 0.08)';

// ─── HARMONIC PATTERN DEFINITIONS (Range-based) ──────────────────────
// Standard Fibonacci ratios with tolerance ranges
export const HARMONIC_PATTERNS: Record<string, HarmonicPatternDef> = {
    GARTLEY: {
        name: 'Gartley',
        nameTr: 'Gartley',
        emoji: '⭐',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.55, max: 0.68, ideal: 0.618 },
        C:    { min: 0.382, max: 0.886, ideal: 0.618 },
        D_XA: { min: 0.746, max: 0.826, ideal: 0.786 },
        D_BC: { min: 1.272, max: 1.618, ideal: 1.272 },
    },
    BUTTERFLY: {
        name: 'Butterfly',
        nameTr: 'Kelebek',
        emoji: '🦋',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.72, max: 0.85, ideal: 0.786 },
        C:    { min: 0.382, max: 0.886, ideal: 0.618 },
        D_XA: { min: 1.20, max: 1.68, ideal: 1.272 },
        D_BC: { min: 1.618, max: 2.618, ideal: 1.618 },
    },
    BAT: {
        name: 'Bat',
        nameTr: 'Yarasa',
        emoji: '🦇',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.35, max: 0.55, ideal: 0.382 },
        C:    { min: 0.382, max: 0.886, ideal: 0.618 },
        D_XA: { min: 0.82, max: 0.92, ideal: 0.886 },
        D_BC: { min: 1.618, max: 2.618, ideal: 2.0 },
    },
    CRAB: {
        name: 'Crab',
        nameTr: 'Yengeç',
        emoji: '🦀',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.35, max: 0.65, ideal: 0.618 },
        C:    { min: 0.382, max: 0.886, ideal: 0.618 },
        D_XA: { min: 1.55, max: 1.70, ideal: 1.618 },
        D_BC: { min: 2.618, max: 3.618, ideal: 2.618 },
    },
    DEEP_CRAB: {
        name: 'Deep Crab',
        nameTr: 'Derin Yengeç',
        emoji: '🦞',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.82, max: 0.92, ideal: 0.886 },
        C:    { min: 0.382, max: 0.886, ideal: 0.618 },
        D_XA: { min: 1.55, max: 1.70, ideal: 1.618 },
        D_BC: { min: 2.0, max: 3.618, ideal: 2.618 },
    },
    SHARK: {
        name: 'Shark',
        nameTr: 'Köpekbalığı',
        emoji: '🦈',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.35, max: 0.65, ideal: 0.446 },
        C:    { min: 1.08, max: 1.68, ideal: 1.13 },
        D_XA: { min: 0.82, max: 0.92, ideal: 0.886 },
        D_BC: { min: 1.618, max: 2.236, ideal: 1.618 },
    },
    CYPHER: {
        name: 'Cypher',
        nameTr: 'Şifre',
        emoji: '🔮',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.382, max: 0.618, ideal: 0.382 },
        C:    { min: 1.13, max: 1.414, ideal: 1.272 },
        D_XA: { min: 0.72, max: 0.82, ideal: 0.786 },
        D_BC: { min: 1.272, max: 2.0, ideal: 1.414 },
    },
    THREE_DRIVES: {
        name: 'Three Drives',
        nameTr: 'Üç Sürüş',
        emoji: '🔱',
        color: HARMONIC_COLOR,
        isMajor: true,
        B:    { min: 0.55, max: 0.72, ideal: 0.618 },
        C:    { min: 1.20, max: 1.68, ideal: 1.272 },
        D_XA: { min: 1.20, max: 1.68, ideal: 1.272 },
        D_BC: { min: 0.55, max: 0.72, ideal: 0.618 },
    },
};

// ─── CLASSIC PATTERN DEFINITIONS ─────────────────────────────────────
export const CLASSIC_PATTERNS: Record<string, { name: string; nameTr: string; color: string; emoji: string }> = {
    DOUBLE_TOP: {
        name: 'Double Top',
        nameTr: 'Çift Tepe',
        color: CLASSIC_COLOR,
        emoji: '🔻',
    },
    DOUBLE_BOTTOM: {
        name: 'Double Bottom',
        nameTr: 'Çift Dip',
        color: CLASSIC_COLOR,
        emoji: '🔺',
    },
    ASCENDING_TRIANGLE: {
        name: 'Ascending Triangle',
        nameTr: 'Yükselen Üçgen',
        color: CLASSIC_COLOR,
        emoji: '△',
    },
    DESCENDING_TRIANGLE: {
        name: 'Descending Triangle',
        nameTr: 'Alçalan Üçgen',
        color: CLASSIC_COLOR,
        emoji: '▽',
    },
    HEAD_SHOULDERS: {
        name: 'Head & Shoulders',
        nameTr: 'Omuz Baş Omuz',
        color: CLASSIC_COLOR,
        emoji: '👤',
    },
    INV_HEAD_SHOULDERS: {
        name: 'Inv. Head & Shoulders',
        nameTr: 'Ters Omuz Baş Omuz',
        color: CLASSIC_COLOR,
        emoji: '🙃',
    },
    RISING_WEDGE: {
        name: 'Rising Wedge',
        nameTr: 'Yükselen Kama',
        color: CLASSIC_COLOR,
        emoji: '📐',
    },
    FALLING_WEDGE: {
        name: 'Falling Wedge',
        nameTr: 'Düşen Kama',
        color: CLASSIC_COLOR,
        emoji: '📐',
    },
    TRIPLE_TOP: {
        name: 'Triple Top',
        nameTr: 'Üçlü Tepe',
        color: CLASSIC_COLOR,
        emoji: '🔻',
    },
    TRIPLE_BOTTOM: {
        name: 'Triple Bottom',
        nameTr: 'Üçlü Dip',
        color: CLASSIC_COLOR,
        emoji: '🔺',
    },
};

export const DEFAULT_DETECTION_OPTIONS: DetectionOptions = {
    deviation: 0.015,       // 1.5% ZigZag deviation (was 5% — way too high)
    fibTolerance: 0.04,     // 4% extra tolerance on fib ranges
    maxPivots: 300,
    minConfidence: 25,
};
