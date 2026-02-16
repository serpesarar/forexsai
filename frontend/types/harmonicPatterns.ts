// Harmonic Pattern Visualizer - Type Definitions

export interface PivotPoint {
    time: number;      // Unix timestamp (seconds)
    price: number;     // Close price at pivot
    high: number;
    low: number;
    type: 'high' | 'low';
    index: number;     // Index in candle array
}

export interface FibRatios {
    B: number;   // AB/XA ratio
    C: number;   // BC/AB ratio
    D: number;   // CD/BC ratio (also XD/XA projection)
}

export interface PatternConfig {
    name: string;
    nameTr: string;
    fibs: FibRatios;
    color: string;
    emoji: string;
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
    target_price?: number;
    stop_loss?: number;
    status: PatternStatus;
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
}

export type DetectedPattern = HarmonicPattern | ClassicPattern;

export interface DetectionOptions {
    deviation: number;    // ZigZag deviation (default 0.05 = 5%)
    tolerance: number;    // Fibonacci tolerance (default 0.02 = 2%)
    maxPivots: number;    // Max pivots to analyze
    lookback: number;     // Candles to look back for classic patterns
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
// Big formations (Harmonic) → Galaxy orange family
export const HARMONIC_COLOR = '#FF8C00';
export const HARMONIC_COLOR_DARK = '#FF6B35';
export const HARMONIC_FILL = 'rgba(255, 140, 0, 0.10)';
export const HARMONIC_GLOW = 'rgba(255, 140, 0, 0.5)';

// Small formations (Classic) → Ice blue family
export const CLASSIC_COLOR = '#00BFFF';
export const CLASSIC_COLOR_DARK = '#87CEEB';
export const CLASSIC_FILL = 'rgba(0, 191, 255, 0.05)';

// Pattern type constants — all harmonics use orange, all classics use blue
export const HARMONIC_PATTERNS: Record<string, PatternConfig> = {
    BUTTERFLY: {
        name: 'Butterfly',
        nameTr: 'Kelebek',
        fibs: { B: 0.786, C: 0.886, D: 1.618 },
        color: HARMONIC_COLOR,
        emoji: '🦋',
    },
    BAT: {
        name: 'Bat',
        nameTr: 'Yarasa',
        fibs: { B: 0.5, C: 0.886, D: 1.618 },
        color: HARMONIC_COLOR,
        emoji: '🦇',
    },
    GARTLEY: {
        name: 'Gartley',
        nameTr: 'Gartley',
        fibs: { B: 0.618, C: 0.786, D: 1.272 },
        color: HARMONIC_COLOR,
        emoji: '⭐',
    },
    CRAB: {
        name: 'Crab',
        nameTr: 'Yengeç',
        fibs: { B: 0.618, C: 0.786, D: 1.618 },
        color: HARMONIC_COLOR,
        emoji: '🦀',
    },
    SHARK: {
        name: 'Shark',
        nameTr: 'Köpekbalığı',
        fibs: { B: 0.886, C: 1.13, D: 1.618 },
        color: HARMONIC_COLOR,
        emoji: '🦈',
    },
};

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
};

export const DEFAULT_DETECTION_OPTIONS: DetectionOptions = {
    deviation: 0.05,     // 5% ZigZag deviation
    tolerance: 0.02,     // 2% Fibonacci tolerance
    maxPivots: 200,
    lookback: 50,
};
