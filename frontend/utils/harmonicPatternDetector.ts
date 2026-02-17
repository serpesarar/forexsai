/**
 * Harmonic Pattern Detection Engine V2
 * 
 * Range-based Fibonacci detection for XABCD harmonics + classic patterns.
 * Scans full chart history with proper zigzag pivot detection.
 * Supports FORMING patterns (3 legs found → project 4th).
 */

import {
    PivotPoint,
    FibRange,
    HarmonicPatternDef,
    HarmonicPattern,
    ClassicPattern,
    DetectedPattern,
    DetectionOptions,
    CandleData,
    PatternStatus,
    HARMONIC_PATTERNS,
    CLASSIC_PATTERNS,
    HARMONIC_COLOR,
    CLASSIC_COLOR,
    DEFAULT_DETECTION_OPTIONS,
} from '../types/harmonicPatterns';

// ─── ZIGZAG PIVOT DETECTION ──────────────────────────────────────────

/**
 * Find pivot points using ZigZag with alternating high/low enforcement.
 * Uses 2-bar lookback/lookahead for pivot confirmation.
 */
export function findPivots(
    candles: CandleData[],
    deviation: number = DEFAULT_DETECTION_OPTIONS.deviation
): PivotPoint[] {
    if (candles.length < 5) return [];

    const pivots: PivotPoint[] = [];
    let lastPivotHigh = candles[0].high;
    let lastPivotLow = candles[0].low;
    let trend = 0; // 0=undetermined, 1=up, -1=down

    for (let i = 2; i < candles.length - 2; i++) {
        const prev2 = candles[i - 2];
        const prev1 = candles[i - 1];
        const curr = candles[i];
        const next1 = candles[i + 1];
        const next2 = candles[i + 2];

        const isPivotHigh =
            curr.high >= prev1.high &&
            curr.high >= prev2.high &&
            curr.high >= next1.high &&
            curr.high >= next2.high;

        const isPivotLow =
            curr.low <= prev1.low &&
            curr.low <= prev2.low &&
            curr.low <= next1.low &&
            curr.low <= next2.low;

        if (isPivotHigh) {
            const change = Math.abs(curr.high - lastPivotLow) / lastPivotLow;
            if (change >= deviation) {
                // Replace last same-direction pivot if this one is higher
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

        if (isPivotLow) {
            const change = Math.abs(lastPivotHigh - curr.low) / lastPivotHigh;
            if (change >= deviation) {
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

    return pivots;
}

// ─── FIBONACCI RANGE HELPERS ─────────────────────────────────────────

function inRange(value: number, range: FibRange, tolerance: number = 0): boolean {
    return value >= (range.min - tolerance) && value <= (range.max + tolerance);
}

/**
 * Score how close a value is to the ideal within a range. Returns 0-100.
 */
function rangeScore(value: number, range: FibRange): number {
    if (value < range.min || value > range.max) {
        // Outside range — calculate penalty
        const dist = value < range.min ? range.min - value : value - range.max;
        return Math.max(0, 80 - dist * 300);
    }
    const distFromIdeal = Math.abs(value - range.ideal);
    const rangeSpan = range.max - range.min;
    if (rangeSpan === 0) return 100;
    const normalized = distFromIdeal / rangeSpan;
    return Math.round(100 - normalized * 40); // 60-100 when in range
}

/**
 * Calculate candle indices between two pivot indices (inclusive).
 */
function getIndicesBetween(startIdx: number, endIdx: number): number[] {
    const result: number[] = [];
    const lo = Math.min(startIdx, endIdx);
    const hi = Math.max(startIdx, endIdx);
    for (let i = lo; i <= hi; i++) result.push(i);
    return result;
}

// ─── HARMONIC PATTERN DETECTION ──────────────────────────────────────

export function detectHarmonicPatterns(
    candles: CandleData[],
    options: Partial<DetectionOptions> = {}
): HarmonicPattern[] {
    const opts: DetectionOptions = { ...DEFAULT_DETECTION_OPTIONS, ...options };
    const pivots = findPivots(candles, opts.deviation);

    if (pivots.length < 4) return [];

    const patterns: HarmonicPattern[] = [];
    const tol = opts.fibTolerance;

    // Scan consecutive 5-pivot windows AND also try skipping pivots (gap=1)
    const maxI = pivots.length;

    for (let xi = 0; xi < maxI - 3; xi++) {
        const X = pivots[xi];

        for (let ai = xi + 1; ai < Math.min(xi + 4, maxI); ai++) {
            const A = pivots[ai];
            // X and A must be different types (high vs low)
            if (X.type === A.type) continue;

            const XA = Math.abs(A.price - X.price);
            if (XA === 0) continue;

            for (let bi = ai + 1; bi < Math.min(ai + 4, maxI); bi++) {
                const B = pivots[bi];
                if (B.type === A.type) continue;

                const AB = Math.abs(B.price - A.price);
                if (AB === 0) continue;
                const abRatio = AB / XA;

                for (let ci = bi + 1; ci < Math.min(bi + 4, maxI); ci++) {
                    const C = pivots[ci];
                    if (C.type === B.type) continue;

                    const BC = Math.abs(C.price - B.price);
                    if (BC === 0) continue;
                    const bcRatio = BC / AB;

                    // Check COMPLETED patterns (D exists)
                    for (let di = ci + 1; di < Math.min(ci + 4, maxI); di++) {
                        const D = pivots[di];
                        if (D.type === C.type) continue;

                        const CD = Math.abs(D.price - C.price);
                        const AD = Math.abs(D.price - X.price);
                        const cdBcRatio = BC > 0 ? CD / BC : 0;
                        const adXaRatio = XA > 0 ? AD / XA : 0;

                        // Check against each pattern definition
                        for (const [key, def] of Object.entries(HARMONIC_PATTERNS)) {
                            if (!inRange(abRatio, def.B, tol)) continue;
                            if (!inRange(bcRatio, def.C, tol)) continue;

                            // D must match either D_XA or D_BC
                            const dXaOk = inRange(adXaRatio, def.D_XA, tol);
                            const dBcOk = inRange(cdBcRatio, def.D_BC, tol);
                            if (!dXaOk && !dBcOk) continue;

                            // Calculate confidence from all ratios
                            const scores = [
                                rangeScore(abRatio, def.B),
                                rangeScore(bcRatio, def.C),
                                dXaOk ? rangeScore(adXaRatio, def.D_XA) : 0,
                                dBcOk ? rangeScore(cdBcRatio, def.D_BC) : 0,
                            ];
                            const validScores = scores.filter(s => s > 0);
                            const confidence = Math.round(
                                validScores.reduce((a, b) => a + b, 0) / validScores.length
                            );

                            if (confidence < opts.minConfidence) continue;

                            // Direction: If D is below A → expect reversal UP (BULLISH)
                            const isBullish = X.type === 'low'; // X is low, pattern ends at D low → bullish reversal
                            const direction: 'BULLISH' | 'BEARISH' = isBullish ? 'BULLISH' : 'BEARISH';

                            // Target: 38.2% and 61.8% retracement of AD leg from D
                            const adLeg = Math.abs(D.price - A.price);
                            const target_price = direction === 'BULLISH'
                                ? D.price + adLeg * 0.618
                                : D.price - adLeg * 0.618;
                            const stop_loss = direction === 'BULLISH'
                                ? D.price - Math.abs(D.price - X.price) * 0.1
                                : D.price + Math.abs(D.price - X.price) * 0.1;

                            const candleIndices = getIndicesBetween(X.index, D.index);

                            patterns.push({
                                type: key,
                                name: def.name,
                                points: { X, A, B, C, D },
                                color: def.color,
                                fibRatios: {
                                    ab: Math.round(abRatio * 1000) / 1000,
                                    bc: Math.round(bcRatio * 1000) / 1000,
                                    cd: Math.round(cdBcRatio * 1000) / 1000,
                                    xd: Math.round(adXaRatio * 1000) / 1000,
                                },
                                direction,
                                confidence,
                                target_price: Math.round(target_price * 100) / 100,
                                stop_loss: Math.round(stop_loss * 100) / 100,
                                status: 'COMPLETED' as PatternStatus,
                                candleIndices,
                            });
                        }
                    }

                    // Check FORMING patterns (XAB + C exists, project D)
                    // Only if C is among the last 10 pivots (recent)
                    if (ci >= maxI - 10) {
                        for (const [key, def] of Object.entries(HARMONIC_PATTERNS)) {
                            if (!inRange(abRatio, def.B, tol)) continue;
                            if (!inRange(bcRatio, def.C, tol)) continue;

                            // Project D from D_XA ratio
                            const dXaIdeal = def.D_XA.ideal;
                            const projectedDPrice = X.type === 'low'
                                ? X.price + XA * dXaIdeal   // bullish: D goes up then reverses
                                : X.price - XA * dXaIdeal;  // bearish: D goes down

                            // Actually for XABCD: if X is low and A is high (upleg),
                            // then D should be near X level (retracement) or below for extensions
                            const dPriceFromXA = A.price > X.price
                                ? A.price - XA * dXaIdeal   // D retraces from A downward
                                : A.price + XA * dXaIdeal;  // D retraces from A upward

                            const dPriceMin = A.price > X.price
                                ? A.price - XA * def.D_XA.max
                                : A.price + XA * def.D_XA.min;
                            const dPriceMax = A.price > X.price
                                ? A.price - XA * def.D_XA.min
                                : A.price + XA * def.D_XA.max;

                            // Project D time: average of AB + CD durations
                            const avgLegDuration = (C.index - B.index);
                            const projectedDTime = candles[Math.min(candles.length - 1, C.index + avgLegDuration)]?.time || C.time + 86400;

                            const scores = [rangeScore(abRatio, def.B), rangeScore(bcRatio, def.C)];
                            const confidence = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length * 0.7); // 70% max for forming

                            if (confidence < opts.minConfidence) continue;

                            const isBullish = X.type === 'low';
                            const direction: 'BULLISH' | 'BEARISH' = isBullish ? 'BULLISH' : 'BEARISH';

                            // Create a synthetic D point for the pattern structure
                            const syntheticD: PivotPoint = {
                                time: projectedDTime,
                                price: dPriceFromXA,
                                high: dPriceFromXA,
                                low: dPriceFromXA,
                                type: C.type === 'high' ? 'low' : 'high',
                                index: Math.min(candles.length - 1, C.index + avgLegDuration),
                            };

                            const candleIndices = getIndicesBetween(X.index, C.index);

                            patterns.push({
                                type: key,
                                name: def.name,
                                points: { X, A, B, C, D: syntheticD },
                                color: def.color,
                                fibRatios: {
                                    ab: Math.round(abRatio * 1000) / 1000,
                                    bc: Math.round(bcRatio * 1000) / 1000,
                                    cd: 0,
                                    xd: Math.round(dXaIdeal * 1000) / 1000,
                                },
                                direction,
                                confidence,
                                isProjected: true,
                                projectedD: {
                                    price: Math.round(dPriceFromXA * 100) / 100,
                                    priceMin: Math.round(Math.min(dPriceMin, dPriceMax) * 100) / 100,
                                    priceMax: Math.round(Math.max(dPriceMin, dPriceMax) * 100) / 100,
                                    time: projectedDTime,
                                },
                                target_price: undefined,
                                stop_loss: undefined,
                                status: 'FORMING' as PatternStatus,
                                candleIndices,
                            });
                        }
                    }
                }
            }
        }
    }

    patterns.sort((a, b) => b.confidence - a.confidence);
    return deduplicatePatterns(patterns);
}

// ─── CLASSIC PATTERN DETECTION ───────────────────────────────────────

export function detectClassicPatterns(
    candles: CandleData[],
    options: Partial<DetectionOptions> = {}
): ClassicPattern[] {
    const opts: DetectionOptions = { ...DEFAULT_DETECTION_OPTIONS, ...options };
    const patterns: ClassicPattern[] = [];

    if (candles.length < 20) return patterns;

    // Use full dataset for pivot detection, scan multiple windows
    const windowSizes = [candles.length, Math.min(100, candles.length), Math.min(50, candles.length)];

    for (const windowSize of windowSizes) {
        const startIdx = candles.length - windowSize;
        const window = candles.slice(startIdx);
        if (window.length < 20) continue;

        const localHighs: PivotPoint[] = [];
        const localLows: PivotPoint[] = [];

        for (let i = 2; i < window.length - 2; i++) {
            const curr = window[i];
            if (
                curr.high > window[i - 1].high &&
                curr.high > window[i - 2].high &&
                curr.high > window[i + 1].high &&
                curr.high > window[i + 2].high
            ) {
                localHighs.push({
                    time: curr.time,
                    price: curr.high,
                    high: curr.high,
                    low: curr.low,
                    type: 'high',
                    index: startIdx + i,
                });
            }
            if (
                curr.low < window[i - 1].low &&
                curr.low < window[i - 2].low &&
                curr.low < window[i + 1].low &&
                curr.low < window[i + 2].low
            ) {
                localLows.push({
                    time: curr.time,
                    price: curr.low,
                    high: curr.high,
                    low: curr.low,
                    type: 'low',
                    index: startIdx + i,
                });
            }
        }

        // ── Double Top (scan all pairs, not just last 2) ──
        for (let i = 0; i < localHighs.length - 1; i++) {
            for (let j = i + 1; j < localHighs.length; j++) {
                const h1 = localHighs[i];
                const h2 = localHighs[j];
                const priceDiff = Math.abs(h1.price - h2.price) / h1.price;
                const timeDist = h2.index - h1.index;
                if (priceDiff < 0.025 && timeDist >= 5 && timeDist <= windowSize * 0.8) {
                    const topAvg = (h1.price + h2.price) / 2;
                    const betweenCandles = candles.slice(h1.index, h2.index + 1);
                    const neckline = Math.min(...betweenCandles.map(c => c.low));
                    const necklineVal = isFinite(neckline) ? neckline : topAvg * 0.98;
                    const height = topAvg - necklineVal;
                    const candleIndices = getIndicesBetween(h1.index, h2.index);
                    patterns.push({
                        type: 'DOUBLE_TOP',
                        name: CLASSIC_PATTERNS.DOUBLE_TOP.name,
                        points: [h1, h2],
                        color: CLASSIC_PATTERNS.DOUBLE_TOP.color,
                        direction: 'BEARISH',
                        neckline: isFinite(neckline) ? neckline : undefined,
                        confidence: Math.round((1 - priceDiff / 0.025) * 75 + 25),
                        target_price: Math.round((necklineVal - height) * 100) / 100,
                        stop_loss: Math.round(topAvg * 100) / 100,
                        status: 'COMPLETED',
                        candleIndices,
                    });
                }
            }
        }

        // ── Double Bottom ──
        for (let i = 0; i < localLows.length - 1; i++) {
            for (let j = i + 1; j < localLows.length; j++) {
                const l1 = localLows[i];
                const l2 = localLows[j];
                const priceDiff = Math.abs(l1.price - l2.price) / l1.price;
                const timeDist = l2.index - l1.index;
                if (priceDiff < 0.025 && timeDist >= 5 && timeDist <= windowSize * 0.8) {
                    const bottomAvg = (l1.price + l2.price) / 2;
                    const betweenCandles = candles.slice(l1.index, l2.index + 1);
                    const neckline = Math.max(...betweenCandles.map(c => c.high));
                    const necklineVal = isFinite(neckline) ? neckline : bottomAvg * 1.02;
                    const heightB = necklineVal - bottomAvg;
                    const candleIndices = getIndicesBetween(l1.index, l2.index);
                    patterns.push({
                        type: 'DOUBLE_BOTTOM',
                        name: CLASSIC_PATTERNS.DOUBLE_BOTTOM.name,
                        points: [l1, l2],
                        color: CLASSIC_PATTERNS.DOUBLE_BOTTOM.color,
                        direction: 'BULLISH',
                        neckline: isFinite(neckline) ? neckline : undefined,
                        confidence: Math.round((1 - priceDiff / 0.025) * 75 + 25),
                        target_price: Math.round((necklineVal + heightB) * 100) / 100,
                        stop_loss: Math.round(bottomAvg * 100) / 100,
                        status: 'COMPLETED',
                        candleIndices,
                    });
                }
            }
        }

        // ── Head & Shoulders ──
        for (let i = 0; i < localHighs.length - 2; i++) {
            const ls = localHighs[i];
            const head = localHighs[i + 1];
            const rs = localHighs[i + 2];
            const shoulderDiff = Math.abs(ls.price - rs.price) / ls.price;
            const isHead = head.price > ls.price && head.price > rs.price;
            if (isHead && shoulderDiff < 0.035) {
                const shoulderAvg = (ls.price + rs.price) / 2;
                const headHeight = head.price - shoulderAvg;
                const candleIndices = getIndicesBetween(ls.index, rs.index);
                patterns.push({
                    type: 'HEAD_SHOULDERS',
                    name: CLASSIC_PATTERNS.HEAD_SHOULDERS.name,
                    points: [ls, head, rs],
                    color: CLASSIC_PATTERNS.HEAD_SHOULDERS.color,
                    direction: 'BEARISH',
                    confidence: Math.round((1 - shoulderDiff / 0.035) * 70 + 30),
                    target_price: Math.round((shoulderAvg - headHeight) * 100) / 100,
                    stop_loss: Math.round(head.price * 100) / 100,
                    status: 'COMPLETED',
                    candleIndices,
                });
            }
        }

        // ── Inverse Head & Shoulders ──
        for (let i = 0; i < localLows.length - 2; i++) {
            const ls = localLows[i];
            const head = localLows[i + 1];
            const rs = localLows[i + 2];
            const shoulderDiff = Math.abs(ls.price - rs.price) / ls.price;
            const isInvHead = head.price < ls.price && head.price < rs.price;
            if (isInvHead && shoulderDiff < 0.035) {
                const shoulderAvg = (ls.price + rs.price) / 2;
                const headDepth = shoulderAvg - head.price;
                const candleIndices = getIndicesBetween(ls.index, rs.index);
                patterns.push({
                    type: 'INV_HEAD_SHOULDERS',
                    name: CLASSIC_PATTERNS.INV_HEAD_SHOULDERS.name,
                    points: [ls, head, rs],
                    color: CLASSIC_PATTERNS.INV_HEAD_SHOULDERS.color,
                    direction: 'BULLISH',
                    confidence: Math.round((1 - shoulderDiff / 0.035) * 70 + 30),
                    target_price: Math.round((shoulderAvg + headDepth) * 100) / 100,
                    stop_loss: Math.round(head.price * 100) / 100,
                    status: 'COMPLETED',
                    candleIndices,
                });
            }
        }

        // ── Triple Top ──
        for (let i = 0; i < localHighs.length - 2; i++) {
            const h1 = localHighs[i];
            const h2 = localHighs[i + 1];
            const h3 = localHighs[i + 2];
            const avg = (h1.price + h2.price + h3.price) / 3;
            const maxDiff = Math.max(
                Math.abs(h1.price - avg) / avg,
                Math.abs(h2.price - avg) / avg,
                Math.abs(h3.price - avg) / avg
            );
            if (maxDiff < 0.02) {
                const candleIndices = getIndicesBetween(h1.index, h3.index);
                const between = candles.slice(h1.index, h3.index + 1);
                const neckline = Math.min(...between.map(c => c.low));
                const height = avg - (isFinite(neckline) ? neckline : avg * 0.98);
                patterns.push({
                    type: 'TRIPLE_TOP',
                    name: CLASSIC_PATTERNS.TRIPLE_TOP.name,
                    points: [h1, h2, h3],
                    color: CLASSIC_PATTERNS.TRIPLE_TOP.color,
                    direction: 'BEARISH',
                    confidence: Math.round((1 - maxDiff / 0.02) * 75 + 25),
                    target_price: Math.round(((isFinite(neckline) ? neckline : avg * 0.98) - height) * 100) / 100,
                    stop_loss: Math.round(avg * 100) / 100,
                    status: 'COMPLETED',
                    candleIndices,
                });
            }
        }

        // ── Triple Bottom ──
        for (let i = 0; i < localLows.length - 2; i++) {
            const l1 = localLows[i];
            const l2 = localLows[i + 1];
            const l3 = localLows[i + 2];
            const avg = (l1.price + l2.price + l3.price) / 3;
            const maxDiff = Math.max(
                Math.abs(l1.price - avg) / avg,
                Math.abs(l2.price - avg) / avg,
                Math.abs(l3.price - avg) / avg
            );
            if (maxDiff < 0.02) {
                const candleIndices = getIndicesBetween(l1.index, l3.index);
                const between = candles.slice(l1.index, l3.index + 1);
                const neckline = Math.max(...between.map(c => c.high));
                const height = (isFinite(neckline) ? neckline : avg * 1.02) - avg;
                patterns.push({
                    type: 'TRIPLE_BOTTOM',
                    name: CLASSIC_PATTERNS.TRIPLE_BOTTOM.name,
                    points: [l1, l2, l3],
                    color: CLASSIC_PATTERNS.TRIPLE_BOTTOM.color,
                    direction: 'BULLISH',
                    confidence: Math.round((1 - maxDiff / 0.02) * 75 + 25),
                    target_price: Math.round(((isFinite(neckline) ? neckline : avg * 1.02) + height) * 100) / 100,
                    stop_loss: Math.round(avg * 100) / 100,
                    status: 'COMPLETED',
                    candleIndices,
                });
            }
        }

        // ── Ascending Triangle ──
        if (localHighs.length >= 2 && localLows.length >= 2) {
            const topPrices = localHighs.slice(-3);
            const bottomPrices = localLows.slice(-3);
            if (topPrices.length >= 2 && bottomPrices.length >= 2) {
                const topFlat = Math.abs(topPrices[topPrices.length - 1].price - topPrices[topPrices.length - 2].price) / topPrices[0].price < 0.018;
                const bottomRising = bottomPrices[bottomPrices.length - 1].price > bottomPrices[bottomPrices.length - 2].price;
                if (topFlat && bottomRising) {
                    const allPts = [...topPrices.slice(-2), ...bottomPrices.slice(-2)].sort((a, b) => a.index - b.index);
                    const candleIndices = getIndicesBetween(allPts[0].index, allPts[allPts.length - 1].index);
                    const resistance = topPrices[topPrices.length - 1].price;
                    const support = bottomPrices[bottomPrices.length - 1].price;
                    const triHeight = resistance - support;
                    patterns.push({
                        type: 'ASCENDING_TRIANGLE',
                        name: CLASSIC_PATTERNS.ASCENDING_TRIANGLE.name,
                        points: allPts,
                        color: CLASSIC_PATTERNS.ASCENDING_TRIANGLE.color,
                        direction: 'BULLISH',
                        confidence: 65,
                        target_price: Math.round((resistance + triHeight) * 100) / 100,
                        stop_loss: Math.round(support * 100) / 100,
                        status: 'COMPLETED',
                        candleIndices,
                    });
                }
            }
        }

        // ── Descending Triangle ──
        if (localHighs.length >= 2 && localLows.length >= 2) {
            const topPrices = localHighs.slice(-3);
            const bottomPrices = localLows.slice(-3);
            if (topPrices.length >= 2 && bottomPrices.length >= 2) {
                const bottomFlat = Math.abs(bottomPrices[bottomPrices.length - 1].price - bottomPrices[bottomPrices.length - 2].price) / bottomPrices[0].price < 0.018;
                const topFalling = topPrices[topPrices.length - 1].price < topPrices[topPrices.length - 2].price;
                if (bottomFlat && topFalling) {
                    const allPts = [...topPrices.slice(-2), ...bottomPrices.slice(-2)].sort((a, b) => a.index - b.index);
                    const candleIndices = getIndicesBetween(allPts[0].index, allPts[allPts.length - 1].index);
                    const resistanceD = topPrices[topPrices.length - 1].price;
                    const supportD = bottomPrices[bottomPrices.length - 1].price;
                    const triHeightD = resistanceD - supportD;
                    patterns.push({
                        type: 'DESCENDING_TRIANGLE',
                        name: CLASSIC_PATTERNS.DESCENDING_TRIANGLE.name,
                        points: allPts,
                        color: CLASSIC_PATTERNS.DESCENDING_TRIANGLE.color,
                        direction: 'BEARISH',
                        confidence: 65,
                        target_price: Math.round((supportD - triHeightD) * 100) / 100,
                        stop_loss: Math.round(resistanceD * 100) / 100,
                        status: 'COMPLETED',
                        candleIndices,
                    });
                }
            }
        }

        // ── Rising Wedge ──
        if (localHighs.length >= 3 && localLows.length >= 3) {
            const highs = localHighs.slice(-3);
            const lows = localLows.slice(-3);
            const highsRising = highs[2].price > highs[1].price && highs[1].price > highs[0].price;
            const lowsRising = lows[2].price > lows[1].price && lows[1].price > lows[0].price;
            const converging = (highs[2].price - lows[2].price) < (highs[0].price - lows[0].price);
            if (highsRising && lowsRising && converging) {
                const allPts = [...highs, ...lows].sort((a, b) => a.index - b.index);
                const candleIndices = getIndicesBetween(allPts[0].index, allPts[allPts.length - 1].index);
                patterns.push({
                    type: 'RISING_WEDGE',
                    name: CLASSIC_PATTERNS.RISING_WEDGE.name,
                    points: allPts,
                    color: CLASSIC_PATTERNS.RISING_WEDGE.color,
                    direction: 'BEARISH',
                    confidence: 60,
                    target_price: Math.round(lows[0].price * 100) / 100,
                    stop_loss: Math.round(highs[2].price * 100) / 100,
                    status: 'COMPLETED',
                    candleIndices,
                });
            }
        }

        // ── Falling Wedge ──
        if (localHighs.length >= 3 && localLows.length >= 3) {
            const highs = localHighs.slice(-3);
            const lows = localLows.slice(-3);
            const highsFalling = highs[2].price < highs[1].price && highs[1].price < highs[0].price;
            const lowsFalling = lows[2].price < lows[1].price && lows[1].price < lows[0].price;
            const converging = (highs[2].price - lows[2].price) < (highs[0].price - lows[0].price);
            if (highsFalling && lowsFalling && converging) {
                const allPts = [...highs, ...lows].sort((a, b) => a.index - b.index);
                const candleIndices = getIndicesBetween(allPts[0].index, allPts[allPts.length - 1].index);
                patterns.push({
                    type: 'FALLING_WEDGE',
                    name: CLASSIC_PATTERNS.FALLING_WEDGE.name,
                    points: allPts,
                    color: CLASSIC_PATTERNS.FALLING_WEDGE.color,
                    direction: 'BULLISH',
                    confidence: 60,
                    target_price: Math.round(highs[0].price * 100) / 100,
                    stop_loss: Math.round(lows[2].price * 100) / 100,
                    status: 'COMPLETED',
                    candleIndices,
                });
            }
        }
    }

    // Deduplicate classic patterns (same type, overlapping indices)
    return deduplicateClassicPatterns(patterns);
}

// ─── COMBINED DETECTION ──────────────────────────────────────────────

export function detectAllPatterns(
    candles: CandleData[],
    options: Partial<DetectionOptions> = {}
): DetectedPattern[] {
    const harmonic = detectHarmonicPatterns(candles, options);
    const classic = detectClassicPatterns(candles, options);
    return [...harmonic, ...classic];
}

// ─── DEDUPLICATION ───────────────────────────────────────────────────

function deduplicatePatterns(patterns: HarmonicPattern[]): HarmonicPattern[] {
    const result: HarmonicPattern[] = [];
    for (const pattern of patterns) {
        const hasOverlap = result.some(existing => {
            if (existing.type !== pattern.type) return false;
            const dDiff = Math.abs(existing.points.D.index - pattern.points.D.index);
            const xDiff = Math.abs(existing.points.X.index - pattern.points.X.index);
            return dDiff <= 8 && xDiff <= 8;
        });
        if (!hasOverlap) result.push(pattern);
    }
    return result;
}

function deduplicateClassicPatterns(patterns: ClassicPattern[]): ClassicPattern[] {
    const result: ClassicPattern[] = [];
    for (const pattern of patterns) {
        const hasOverlap = result.some(existing => {
            if (existing.type !== pattern.type) return false;
            // Check if points overlap significantly
            const existingIndices = new Set(existing.candleIndices);
            const overlap = pattern.candleIndices.filter(i => existingIndices.has(i)).length;
            return overlap > pattern.candleIndices.length * 0.5;
        });
        if (!hasOverlap) result.push(pattern);
    }
    return result;
}
