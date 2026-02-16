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
}

export interface ClassicPattern {
    type: string;
    name: string;
    points: PivotPoint[];
    color: string;
    direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    neckline?: number;
    confidence: number;
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

// Pattern type constants
export const HARMONIC_PATTERNS: Record<string, PatternConfig> = {
    BUTTERFLY: {
        name: 'Butterfly',
        nameTr: 'Kelebek',
        fibs: { B: 0.786, C: 0.886, D: 1.618 },
        color: '#FF00FF',  // Neon Magenta
        emoji: '🦋',
    },
    BAT: {
        name: 'Bat',
        nameTr: 'Yarasa',
        fibs: { B: 0.5, C: 0.886, D: 1.618 },
        color: '#00FFFF',  // Neon Cyan
        emoji: '🦇',
    },
    GARTLEY: {
        name: 'Gartley',
        nameTr: 'Gartley',
        fibs: { B: 0.618, C: 0.786, D: 1.272 },
        color: '#FFD700',  // Neon Gold
        emoji: '⭐',
    },
    CRAB: {
        name: 'Crab',
        nameTr: 'Yengeç',
        fibs: { B: 0.618, C: 0.786, D: 1.618 },
        color: '#FF4500',  // Neon Orange
        emoji: '🦀',
    },
    SHARK: {
        name: 'Shark',
        nameTr: 'Köpekbalığı',
        fibs: { B: 0.886, C: 1.13, D: 1.618 },
        color: '#00FF00',  // Neon Green
        emoji: '🦈',
    },
};

export const CLASSIC_PATTERNS: Record<string, { name: string; nameTr: string; color: string; emoji: string }> = {
    DOUBLE_TOP: {
        name: 'Double Top',
        nameTr: 'Çift Tepe',
        color: '#DC143C',
        emoji: '🔻',
    },
    DOUBLE_BOTTOM: {
        name: 'Double Bottom',
        nameTr: 'Çift Dip',
        color: '#32CD32',
        emoji: '🔺',
    },
    ASCENDING_TRIANGLE: {
        name: 'Ascending Triangle',
        nameTr: 'Yükselen Üçgen',
        color: '#FFD700',
        emoji: '△',
    },
    DESCENDING_TRIANGLE: {
        name: 'Descending Triangle',
        nameTr: 'Alçalan Üçgen',
        color: '#FF6347',
        emoji: '▽',
    },
    HEAD_SHOULDERS: {
        name: 'Head & Shoulders',
        nameTr: 'Omuz Baş Omuz',
        color: '#FF1493',
        emoji: '👤',
    },
};

export const DEFAULT_DETECTION_OPTIONS: DetectionOptions = {
    deviation: 0.05,     // 5% ZigZag deviation
    tolerance: 0.02,     // 2% Fibonacci tolerance
    maxPivots: 200,
    lookback: 50,
};
