/**
 * Harmonic Pattern Detection Engine
 * 
 * Detects XABCD harmonic patterns (Butterfly, Bat, Gartley, Crab, Shark)
 * and classic patterns (Double Top/Bottom, Triangles, Head & Shoulders)
 * using ZigZag pivot detection + Fibonacci ratio validation.
 */

import {
    PivotPoint,
    HarmonicPattern,
    ClassicPattern,
    DetectedPattern,
    DetectionOptions,
    CandleData,
    PatternStatus,
    HARMONIC_PATTERNS,
    CLASSIC_PATTERNS,
    DEFAULT_DETECTION_OPTIONS,
} from '../types/harmonicPatterns';

// ─── ZIGZAG PIVOT DETECTION ──────────────────────────────────────────

/**
 * Find pivot points using the ZigZag algorithm.
 * A pivot high has higher highs on both sides; pivot low has lower lows on both sides.
 * The deviation param filters out insignificant swings.
 */
export function findPivots(
    candles: CandleData[],
    deviation: number = DEFAULT_DETECTION_OPTIONS.deviation
): PivotPoint[] {
    if (candles.length < 5) return [];

    const pivots: PivotPoint[] = [];
    let lastPivotHigh = candles[0].high;
    let lastPivotLow = candles[0].low;
    let trend = 0; // 0 = undetermined, 1 = up, -1 = down

    for (let i = 2; i < candles.length - 2; i++) {
        const prev2 = candles[i - 2];
        const prev1 = candles[i - 1];
        const curr = candles[i];
        const next1 = candles[i + 1];
        const next2 = candles[i + 2];

        // Check for pivot high: current high > neighbors
        const isPivotHigh =
            curr.high >= prev1.high &&
            curr.high >= prev2.high &&
            curr.high >= next1.high &&
            curr.high >= next2.high;

        // Check for pivot low: current low < neighbors
        const isPivotLow =
            curr.low <= prev1.low &&
            curr.low <= prev2.low &&
            curr.low <= next1.low &&
            curr.low <= next2.low;

        if (isPivotHigh) {
            const change = Math.abs(curr.high - lastPivotLow) / lastPivotLow;
            if (change >= deviation) {
                if (trend !== 1 || curr.high > lastPivotHigh) {
                    // Remove duplicate same-direction pivot
                    if (trend === 1 && pivots.length > 0 && pivots[pivots.length - 1].type === 'high') {
                        if (curr.high > pivots[pivots.length - 1].high) {
                            pivots.pop();
                        } else {
                            continue;
                        }
                    }
                    pivots.push({
                        time: curr.time,
                        price: curr.high,
                        high: curr.high,
                        low: curr.low,
                        type: 'high',
                        index: i,
                    });
                    lastPivotHigh = curr.high;
                    trend = 1;
                }
            }
        }

        if (isPivotLow) {
            const change = Math.abs(lastPivotHigh - curr.low) / lastPivotHigh;
            if (change >= deviation) {
                if (trend !== -1 || curr.low < lastPivotLow) {
                    // Remove duplicate same-direction pivot
                    if (trend === -1 && pivots.length > 0 && pivots[pivots.length - 1].type === 'low') {
                        if (curr.low < pivots[pivots.length - 1].low) {
                            pivots.pop();
                        } else {
                            continue;
                        }
                    }
                    pivots.push({
                        time: curr.time,
                        price: curr.low,
                        high: curr.high,
                        low: curr.low,
                        type: 'low',
                        index: i,
                    });
                    lastPivotLow = curr.low;
                    trend = -1;
                }
            }
        }
    }

    return pivots;
}

// ─── FIBONACCI HELPERS ───────────────────────────────────────────────

/**
 * Check if actual ratio matches expected Fibonacci ratio within tolerance.
 */
function isValidFib(
    actual: number,
    expected: number,
    tolerance: number = DEFAULT_DETECTION_OPTIONS.tolerance
): boolean {
    return Math.abs(actual - expected) <= tolerance;
}

/**
 * Calculate confidence score (0-100) based on how closely ratios match.
 */
function calculateConfidence(
    abRatio: number,
    bcRatio: number,
    cdRatio: number,
    expected: { B: number; C: number; D: number }
): number {
    const errors = [
        Math.abs(abRatio - expected.B),
        Math.abs(bcRatio - expected.C),
        Math.abs(cdRatio - expected.D),
    ];
    const avgError = errors.reduce((sum, e) => sum + e, 0) / errors.length;
    // Perfect match = 100, each 0.01 error reduces score by ~5 points
    return Math.max(0, Math.min(100, Math.round(100 - avgError * 500)));
}

// ─── HARMONIC PATTERN DETECTION ──────────────────────────────────────

/**
 * Detect harmonic patterns (XABCD) from candle data.
 * Scans all valid 5-pivot sequences and checks Fibonacci ratios.
 */
export function detectHarmonicPatterns(
    candles: CandleData[],
    options: Partial<DetectionOptions> = {}
): HarmonicPattern[] {
    const opts = { ...DEFAULT_DETECTION_OPTIONS, ...options };
    const pivots = findPivots(candles, opts.deviation);

    if (pivots.length < 5) return [];

    const patterns: HarmonicPattern[] = [];
    const maxScan = Math.min(pivots.length - 4, opts.maxPivots);

    for (let i = 0; i < maxScan; i++) {
        const X = pivots[i];
        const A = pivots[i + 1];
        const B = pivots[i + 2];
        const C = pivots[i + 3];
        const D = pivots[i + 4];

        // Calculate leg lengths
        const XA = Math.abs(A.price - X.price);
        const AB = Math.abs(B.price - A.price);
        const BC = Math.abs(C.price - B.price);
        const CD = Math.abs(D.price - C.price);

        // Avoid division by zero
        if (XA === 0 || AB === 0 || BC === 0) continue;

        const abRatio = AB / XA;
        const bcRatio = BC / AB;
        const cdRatio = CD / BC;
        const xdRatio = Math.abs(D.price - X.price) / XA;

        // Check each harmonic pattern
        for (const [key, config] of Object.entries(HARMONIC_PATTERNS)) {
            if (
                isValidFib(abRatio, config.fibs.B, opts.tolerance) &&
                isValidFib(bcRatio, config.fibs.C, opts.tolerance) &&
                (isValidFib(cdRatio, config.fibs.D, opts.tolerance) ||
                    isValidFib(xdRatio, config.fibs.D, opts.tolerance))
            ) {
                const confidence = calculateConfidence(abRatio, bcRatio, cdRatio, config.fibs);

                // Only include patterns with reasonable confidence
                if (confidence >= 30) {
                    const direction: 'BULLISH' | 'BEARISH' = D.price < A.price ? 'BULLISH' : 'BEARISH';
                    // Target: 61.8% retracement of CD leg from D
                    const cdLeg = Math.abs(D.price - C.price);
                    const target_price = direction === 'BULLISH'
                        ? D.price + cdLeg * 0.618
                        : D.price - cdLeg * 0.618;
                    // Stop loss: X point (invalidates the pattern)
                    const stop_loss = X.price;

                    patterns.push({
                        type: key,
                        name: config.name,
                        points: { X, A, B, C, D },
                        color: config.color,
                        fibRatios: {
                            ab: Math.round(abRatio * 1000) / 1000,
                            bc: Math.round(bcRatio * 1000) / 1000,
                            cd: Math.round(cdRatio * 1000) / 1000,
                            xd: Math.round(xdRatio * 1000) / 1000,
                        },
                        direction,
                        confidence,
                        target_price: Math.round(target_price * 100) / 100,
                        stop_loss: Math.round(stop_loss * 100) / 100,
                        status: 'COMPLETED' as PatternStatus,
                    });
                }
            }
        }
    }

    // Sort by confidence (highest first) and deduplicate overlapping patterns
    patterns.sort((a, b) => b.confidence - a.confidence);
    return deduplicatePatterns(patterns);
}

// ─── CLASSIC PATTERN DETECTION ───────────────────────────────────────

/**
 * Detect classic chart patterns from candle data.
 */
export function detectClassicPatterns(
    candles: CandleData[],
    options: Partial<DetectionOptions> = {}
): ClassicPattern[] {
    const opts = { ...DEFAULT_DETECTION_OPTIONS, ...options };
    const patterns: ClassicPattern[] = [];
    const lookback = Math.min(opts.lookback, candles.length);
    const recent = candles.slice(-lookback);

    if (recent.length < 10) return patterns;

    // Find local highs and lows
    const localHighs: PivotPoint[] = [];
    const localLows: PivotPoint[] = [];

    for (let i = 2; i < recent.length - 2; i++) {
        const curr = recent[i];
        if (
            curr.high > recent[i - 1].high &&
            curr.high > recent[i - 2].high &&
            curr.high > recent[i + 1].high &&
            curr.high > recent[i + 2].high
        ) {
            localHighs.push({
                time: curr.time,
                price: curr.high,
                high: curr.high,
                low: curr.low,
                type: 'high',
                index: candles.length - lookback + i,
            });
        }
        if (
            curr.low < recent[i - 1].low &&
            curr.low < recent[i - 2].low &&
            curr.low < recent[i + 1].low &&
            curr.low < recent[i + 2].low
        ) {
            localLows.push({
                time: curr.time,
                price: curr.low,
                high: curr.high,
                low: curr.low,
                type: 'low',
                index: candles.length - lookback + i,
            });
        }
    }

    // ── Double Top ──
    if (localHighs.length >= 2) {
        const last2 = localHighs.slice(-2);
        const priceDiff = Math.abs(last2[0].price - last2[1].price) / last2[0].price;
        if (priceDiff < 0.02) {
            const neckline = Math.min(
                ...recent.slice(last2[0].index - (candles.length - lookback), last2[1].index - (candles.length - lookback))
                    .map(c => c.low)
            );
            const topAvg = (last2[0].price + last2[1].price) / 2;
            const necklineVal = isFinite(neckline) ? neckline : topAvg * 0.98;
            const height = topAvg - necklineVal;
            patterns.push({
                type: 'DOUBLE_TOP',
                name: CLASSIC_PATTERNS.DOUBLE_TOP.name,
                points: last2,
                color: CLASSIC_PATTERNS.DOUBLE_TOP.color,
                direction: 'BEARISH',
                neckline: isFinite(neckline) ? neckline : undefined,
                confidence: Math.round((1 - priceDiff / 0.02) * 80 + 20),
                target_price: Math.round((necklineVal - height) * 100) / 100,
                stop_loss: Math.round(topAvg * 100) / 100,
                status: 'COMPLETED' as PatternStatus,
            });
        }
    }

    // ── Double Bottom ──
    if (localLows.length >= 2) {
        const last2 = localLows.slice(-2);
        const priceDiff = Math.abs(last2[0].price - last2[1].price) / last2[0].price;
        if (priceDiff < 0.02) {
            const neckline = Math.max(
                ...recent.slice(
                    Math.max(0, last2[0].index - (candles.length - lookback)),
                    last2[1].index - (candles.length - lookback)
                ).map(c => c.high)
            );
            const bottomAvg = (last2[0].price + last2[1].price) / 2;
            const necklineValB = isFinite(neckline) ? neckline : bottomAvg * 1.02;
            const heightB = necklineValB - bottomAvg;
            patterns.push({
                type: 'DOUBLE_BOTTOM',
                name: CLASSIC_PATTERNS.DOUBLE_BOTTOM.name,
                points: last2,
                color: CLASSIC_PATTERNS.DOUBLE_BOTTOM.color,
                direction: 'BULLISH',
                neckline: isFinite(neckline) ? neckline : undefined,
                confidence: Math.round((1 - priceDiff / 0.02) * 80 + 20),
                target_price: Math.round((necklineValB + heightB) * 100) / 100,
                stop_loss: Math.round(bottomAvg * 100) / 100,
                status: 'COMPLETED' as PatternStatus,
            });
        }
    }

    // ── Head & Shoulders ──
    if (localHighs.length >= 3) {
        const last3 = localHighs.slice(-3);
        const [leftShoulder, head, rightShoulder] = last3;
        const shoulderDiff = Math.abs(leftShoulder.price - rightShoulder.price) / leftShoulder.price;
        const isHead = head.price > leftShoulder.price && head.price > rightShoulder.price;

        if (isHead && shoulderDiff < 0.03) {
            const shoulderAvg = (leftShoulder.price + rightShoulder.price) / 2;
            const headHeight = head.price - shoulderAvg;
            patterns.push({
                type: 'HEAD_SHOULDERS',
                name: CLASSIC_PATTERNS.HEAD_SHOULDERS.name,
                points: last3,
                color: CLASSIC_PATTERNS.HEAD_SHOULDERS.color,
                direction: 'BEARISH',
                confidence: Math.round((1 - shoulderDiff / 0.03) * 70 + 30),
                target_price: Math.round((shoulderAvg - headHeight) * 100) / 100,
                stop_loss: Math.round(head.price * 100) / 100,
                status: 'COMPLETED' as PatternStatus,
            });
        }
    }

    // ── Ascending Triangle ──
    if (localHighs.length >= 2 && localLows.length >= 2) {
        const topPrices = localHighs.slice(-3).map(h => h.price);
        const bottomPrices = localLows.slice(-3).map(l => l.price);

        const topFlat = topPrices.length >= 2 &&
            Math.abs(topPrices[topPrices.length - 1] - topPrices[topPrices.length - 2]) / topPrices[0] < 0.015;
        const bottomRising = bottomPrices.length >= 2 &&
            bottomPrices[bottomPrices.length - 1] > bottomPrices[bottomPrices.length - 2];

        if (topFlat && bottomRising) {
            const resistance = topPrices[topPrices.length - 1];
            const support = bottomPrices[bottomPrices.length - 1];
            const triHeight = resistance - support;
            patterns.push({
                type: 'ASCENDING_TRIANGLE',
                name: CLASSIC_PATTERNS.ASCENDING_TRIANGLE.name,
                points: [...localHighs.slice(-2), ...localLows.slice(-2)],
                color: CLASSIC_PATTERNS.ASCENDING_TRIANGLE.color,
                direction: 'BULLISH',
                confidence: 65,
                target_price: Math.round((resistance + triHeight) * 100) / 100,
                stop_loss: Math.round(support * 100) / 100,
                status: 'COMPLETED' as PatternStatus,
            });
        }
    }

    // ── Descending Triangle ──
    if (localHighs.length >= 2 && localLows.length >= 2) {
        const topPrices = localHighs.slice(-3).map(h => h.price);
        const bottomPrices = localLows.slice(-3).map(l => l.price);

        const bottomFlat = bottomPrices.length >= 2 &&
            Math.abs(bottomPrices[bottomPrices.length - 1] - bottomPrices[bottomPrices.length - 2]) / bottomPrices[0] < 0.015;
        const topFalling = topPrices.length >= 2 &&
            topPrices[topPrices.length - 1] < topPrices[topPrices.length - 2];

        if (bottomFlat && topFalling) {
            const resistanceD = topPrices[topPrices.length - 1];
            const supportD = bottomPrices[bottomPrices.length - 1];
            const triHeightD = resistanceD - supportD;
            patterns.push({
                type: 'DESCENDING_TRIANGLE',
                name: CLASSIC_PATTERNS.DESCENDING_TRIANGLE.name,
                points: [...localHighs.slice(-2), ...localLows.slice(-2)],
                color: CLASSIC_PATTERNS.DESCENDING_TRIANGLE.color,
                direction: 'BEARISH',
                confidence: 65,
                target_price: Math.round((supportD - triHeightD) * 100) / 100,
                stop_loss: Math.round(resistanceD * 100) / 100,
                status: 'COMPLETED' as PatternStatus,
            });
        }
    }

    return patterns;
}

// ─── COMBINED DETECTION ──────────────────────────────────────────────

/**
 * Run full pattern detection (harmonic + classic) on candle data.
 */
export function detectAllPatterns(
    candles: CandleData[],
    options: Partial<DetectionOptions> = {}
): DetectedPattern[] {
    const harmonic = detectHarmonicPatterns(candles, options);
    const classic = detectClassicPatterns(candles, options);
    return [...harmonic, ...classic];
}

// ─── DEDUPLICATION ───────────────────────────────────────────────────

/**
 * Remove overlapping harmonic patterns (keep highest confidence).
 * Two patterns overlap if their D-points are within 5 candles of each other.
 */
function deduplicatePatterns(patterns: HarmonicPattern[]): HarmonicPattern[] {
    const result: HarmonicPattern[] = [];

    for (const pattern of patterns) {
        const hasOverlap = result.some(existing => {
            const dDiff = Math.abs(existing.points.D.index - pattern.points.D.index);
            const xDiff = Math.abs(existing.points.X.index - pattern.points.X.index);
            return dDiff <= 5 && xDiff <= 5;
        });

        if (!hasOverlap) {
            result.push(pattern);
        }
    }

    return result;
}
