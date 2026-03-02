"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
    ColorType,
    createChart,
    CrosshairMode,
    IChartApi,
    ISeriesApi,
    Time,
} from "lightweight-charts";
import { ActivityIcon as Activity, HarmonicIcon as Hexagon, CloseIcon as XIcon, TargetIcon as Target, AlertIcon as ShieldAlert, ArrowUpIcon as TrendingUp, ArrowDownIcon as TrendingDown } from "../ui/CustomIcons";
import { Maximize2, Minimize2 } from "lucide-react";
import { PanelHeader } from "../PanelHeader";
import { useQuery } from "@tanstack/react-query";
import { useI18nStore } from "../../lib/i18n/store";
import {
    HarmonicPattern,
    ClassicPattern,
    DetectedPattern,
    HARMONIC_PATTERNS,
    CLASSIC_PATTERNS,
    CandleData,
    HARMONIC_COLOR,
    HARMONIC_COLOR_CANDLE,
    HARMONIC_COLOR_WICK,
    HARMONIC_COLOR_DARK,
    HARMONIC_FILL,
    HARMONIC_GLOW,
    CLASSIC_COLOR,
    CLASSIC_COLOR_CANDLE,
    CLASSIC_COLOR_WICK,
    CLASSIC_FILL,
} from "../../types/harmonicPatterns";
import {
    detectHarmonicPatterns,
    detectClassicPatterns,
} from "../../utils/harmonicPatternDetector";
import { useFullscreen } from "../../hooks/useFullscreen";
import styles from "./harmonic-visualizer.module.css";

// ─── CONFIG ──────────────────────────────────────────────────────────

const API_BASE = "https://upbeat-flow-production.up.railway.app";
const P = { bg: "var(--bg-primary)", card: "var(--bg-card)", surface: "var(--bg-surface)", border: "var(--border-subtle)", text: "var(--text-primary)", muted: "var(--text-muted)", green: "var(--accent-positive)", red: "var(--accent-negative)", warn: "var(--accent-warning)", accent: "var(--accent-info)", purple: "var(--accent-purple)" };

const SYMBOLS: { key: string; label: string }[] = [
    { key: "NDX.INDX", label: "NASDAQ" },
    { key: "XAUUSD", label: "XAUUSD" },
    { key: "GDAXI.INDX", label: "DAX" },
    { key: "USOIL.FOREX", label: "US Oil" },
];

const TIMEFRAMES = ["5m", "15m", "1h", "4h"] as const;
type TimeframeType = (typeof TIMEFRAMES)[number];

// Pulse colors for candle blinking effect
const PULSE_COLORS_HARMONIC = [
    { body: '#FF9D2F', wick: '#CC7000' },
    { body: '#FFB347', wick: '#E08A00' },
];
const PULSE_COLORS_CLASSIC = [
    { body: '#4DC9F6', wick: '#0090CC' },
    { body: '#7DD8F8', wick: '#40B0E0' },
];

// ─── DATA FETCHING ───────────────────────────────────────────────────

async function fetchOHLCV(
    symbol: string,
    timeframe: string
): Promise<CandleData[]> {
    const res = await fetch(
        `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(
            symbol
        )}&timeframe=${timeframe}&limit=300`
    );
    if (!res.ok) throw new Error("Failed to fetch OHLCV data");
    const data = await res.json();
    const raw: any[] = data.data || [];
    return raw.map((d) => ({
        time: Math.floor(d.timestamp / 1000),
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
    }));
}

// ─── HELPERS ─────────────────────────────────────────────────────────

function isHarmonicPattern(p: DetectedPattern): p is HarmonicPattern {
    return "points" in p && "fibRatios" in p;
}

function getPatternDisplayName(
    pattern: DetectedPattern,
    locale: string
): string {
    if (isHarmonicPattern(pattern)) {
        const config = HARMONIC_PATTERNS[pattern.type];
        return locale === "tr" && config?.nameTr ? config.nameTr : pattern.name;
    }
    const classicConfig = CLASSIC_PATTERNS[pattern.type];
    return locale === "tr" && classicConfig?.nameTr
        ? classicConfig.nameTr
        : pattern.name;
}

function getPatternEmoji(pattern: DetectedPattern): string {
    if (isHarmonicPattern(pattern)) {
        return HARMONIC_PATTERNS[pattern.type]?.emoji || "📊";
    }
    return CLASSIC_PATTERNS[pattern.type]?.emoji || "📊";
}

function getConfidenceClass(confidence: number): string {
    if (confidence >= 70) return styles.confidenceHigh;
    if (confidence >= 45) return styles.confidenceMedium;
    return styles.confidenceLow;
}

function throttle<T extends (...args: any[]) => void>(fn: T, delay: number): T {
    let lastCall = 0;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    return ((...args: any[]) => {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            fn(...args);
        } else {
            if (timeoutId) clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                lastCall = Date.now();
                fn(...args);
            }, delay - (now - lastCall));
        }
    }) as T;
}

function formatTime(time: number): string {
    const d = new Date(time * 1000);
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

// ─── TYPES ───────────────────────────────────────────────────────────

interface PixelPoint {
    x: number;
    y: number;
    label: string;
    time: number;
    price: number;
}

interface FormationOverlayData {
    pattern: DetectedPattern;
    pixelPoints: PixelPoint[];
    isBig: boolean;
    color: string;
}

// ─── COMPONENT ───────────────────────────────────────────────────────

export default function HarmonicVisualizerPanel() {
    const { t, locale } = useI18nStore();

    // ── State
    const [symbol, setSymbol] = useState<string>(SYMBOLS[0].key);
    const [timeframe, setTimeframe] = useState<TimeframeType>("4h");
    const [selectedPattern, setSelectedPattern] = useState<DetectedPattern | null>(null);
    const [chartSize, setChartSize] = useState({ width: 0, height: 0 });
    const [overlayVersion, setOverlayVersion] = useState(0);
    const { isFullscreen, toggleFullscreen } = useFullscreen();

    // ── Refs
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    // ── Data fetch
    const {
        data: candles,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ["harmonic-ohlcv", symbol, timeframe],
        queryFn: () => fetchOHLCV(symbol, timeframe),
        refetchInterval: 30000,
        staleTime: 15000,
    });

    // ── Pattern detection (memoized)
    const patterns = useMemo<DetectedPattern[]>(() => {
        if (!candles || candles.length < 10) return [];
        const harmonic = detectHarmonicPatterns(candles);
        const classic = detectClassicPatterns(candles);
        return [...harmonic, ...classic];
    }, [candles]);

    // ── Build candle color map from patterns
    const candleColorMap = useMemo(() => {
        const map = new Map<number, 'harmonic' | 'classic'>();
        for (const pattern of patterns) {
            const isBig = isHarmonicPattern(pattern);
            const type = isBig ? 'harmonic' : 'classic';
            const indices = 'candleIndices' in pattern ? (pattern as any).candleIndices as number[] : [];
            for (const idx of indices) {
                // Harmonic (big) takes priority over classic
                if (!map.has(idx) || type === 'harmonic') {
                    map.set(idx, type);
                }
            }
        }
        return map;
    }, [patterns]);

    // ── Chart initialization
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const container = chartContainerRef.current;
        const chart = createChart(container, {
            layout: {
                background: { type: ColorType.Solid, color: "#0a0e27" },
                textColor: "#d1d4dc",
            },
            grid: {
                vertLines: { color: "rgba(42,46,57,0.4)" },
                horzLines: { color: "rgba(42,46,57,0.4)" },
            },
            crosshair: { mode: CrosshairMode.Normal },
            width: container.clientWidth,
            height: container.clientHeight || 500,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: "rgba(42,46,57,0.8)",
            },
            rightPriceScale: {
                borderColor: "rgba(42,46,57,0.8)",
            },
        });

        const candleSeries = chart.addCandlestickSeries({
            upColor: "#26a69a",
            downColor: "#ef5350",
            borderVisible: true,
            wickUpColor: "#26a69a",
            wickDownColor: "#ef5350",
            borderUpColor: "#26a69a",
            borderDownColor: "#ef5350",
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;

        const handleResize = throttle(() => {
            if (!container) return;
            const w = container.clientWidth;
            const h = container.clientHeight || 500;
            chart.applyOptions({ width: w, height: h });
            setChartSize({ width: w, height: h });
            setOverlayVersion(v => v + 1);
        }, 100);

        const observer = new ResizeObserver(handleResize);
        observer.observe(container);
        handleResize();

        const onVisibleRangeChange = () => setOverlayVersion(v => v + 1);
        chart.timeScale().subscribeVisibleLogicalRangeChange(onVisibleRangeChange);

        return () => {
            observer.disconnect();
            chart.timeScale().unsubscribeVisibleLogicalRangeChange(onVisibleRangeChange);
            chart.remove();
            chartRef.current = null;
            candleSeriesRef.current = null;
        };
    }, []);

    // ── Update chart data with per-candle coloring (static, removed polling memory leak)
    useEffect(() => {
        if (!candleSeriesRef.current || !candles || candles.length === 0) return;

        const chartData = candles.map((c, idx) => {
            const colorType = candleColorMap.get(idx);
            if (colorType === 'harmonic') {
                const colors = PULSE_COLORS_HARMONIC[0];
                return {
                    time: c.time as Time,
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close,
                    color: colors.body,
                    wickColor: colors.wick,
                    borderColor: colors.body,
                };
            } else if (colorType === 'classic') {
                const colors = PULSE_COLORS_CLASSIC[0];
                return {
                    time: c.time as Time,
                    open: c.open,
                    high: c.high,
                    low: c.low,
                    close: c.close,
                    color: colors.body,
                    wickColor: colors.wick,
                    borderColor: colors.body,
                };
            }
            return {
                time: c.time as Time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close,
            };
        });

        candleSeriesRef.current.setData(chartData);
        chartRef.current?.timeScale().fitContent();

        const timer = setTimeout(() => setOverlayVersion(v => v + 1), 50);
        return () => clearTimeout(timer);
    }, [candles, candleColorMap]);

    // ── Calculate SVG overlay data
    const overlayData = useMemo<FormationOverlayData[]>(() => {
        const chart = chartRef.current;
        const series = candleSeriesRef.current;
        if (!chart || !series || patterns.length === 0) return [];

        const timeScale = chart.timeScale();
        const visibleRange = timeScale.getVisibleRange();

        const result: FormationOverlayData[] = [];

        for (const pattern of patterns) {
            const isBig = isHarmonicPattern(pattern);
            const color = isBig ? HARMONIC_COLOR : CLASSIC_COLOR;

            let rawPoints: { label: string; time: number; price: number; isProjected?: boolean }[];
            if (isBig) {
                const hp = pattern as HarmonicPattern;
                rawPoints = [
                    { label: "X", time: hp.points.X.time, price: hp.points.X.price },
                    { label: "A", time: hp.points.A.time, price: hp.points.A.price },
                    { label: "B", time: hp.points.B.time, price: hp.points.B.price },
                    { label: "C", time: hp.points.C.time, price: hp.points.C.price },
                    { label: "D", time: hp.points.D.time, price: hp.points.D.price, isProjected: hp.isProjected },
                ];
            } else {
                const cp = pattern as ClassicPattern;
                rawPoints = cp.points.map((pt, idx) => ({
                    label: `P${idx + 1}`,
                    time: pt.time,
                    price: pt.price,
                }));
            }

            if (visibleRange) {
                const from = visibleRange.from as number;
                const to = visibleRange.to as number;
                const patternTimes = rawPoints.map(p => p.time);
                const patternMin = Math.min(...patternTimes);
                const patternMax = Math.max(...patternTimes);
                if (patternMax < from || patternMin > to) continue;
            }

            const pixelPoints: PixelPoint[] = [];
            let valid = true;
            for (const pt of rawPoints) {
                const x = timeScale.timeToCoordinate(pt.time as Time);
                const y = series.priceToCoordinate(pt.price);
                if (x === null || y === null) {
                    valid = false;
                    break;
                }
                pixelPoints.push({
                    x: x as number,
                    y: y as number,
                    label: pt.label,
                    time: pt.time,
                    price: pt.price,
                });
            }
            if (!valid || pixelPoints.length < 2) continue;

            result.push({ pattern, pixelPoints, isBig, color });
        }

        return result;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [patterns, overlayVersion, chartSize.width, chartSize.height]);

    // ── Render SVG overlay elements
    const svgElements = useMemo(() => {
        return overlayData.map((data, idx) => {
            const { pixelPoints, isBig, color, pattern } = data;
            const isForming = pattern.status === "FORMING";
            const hp = isBig ? (pattern as HarmonicPattern) : null;

            // Separate completed and projected points
            const completedPoints = isForming && hp
                ? pixelPoints.slice(0, -1) // All except D
                : pixelPoints;
            const projectedPoint = isForming && hp ? pixelPoints[pixelPoints.length - 1] : null;

            const completedStr = completedPoints.map(p => `${p.x},${p.y}`).join(" ");
            const fullStr = pixelPoints.map(p => `${p.x},${p.y}`).join(" ");
            const polygonPoints = isBig ? fullStr : undefined;

            return (
                <g key={`formation-${idx}`} className={isBig ? styles.formationGlowBig : styles.formationGlowSmall}>
                    {/* Filled region */}
                    {isBig && polygonPoints && (
                        <polygon
                            points={polygonPoints}
                            fill={isForming ? 'rgba(255, 140, 0, 0.05)' : HARMONIC_FILL}
                            stroke="none"
                        />
                    )}

                    {/* Completed formation line */}
                    <polyline
                        points={completedStr}
                        fill="none"
                        stroke={color}
                        strokeWidth={isBig ? 2.5 : 2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        style={{
                            filter: isBig ? `drop-shadow(0 0 6px ${color}) drop-shadow(0 0 12px ${HARMONIC_GLOW})` : `drop-shadow(0 0 4px ${color})`,
                        }}
                    />

                    {/* Projected D line (dashed) */}
                    {isForming && projectedPoint && completedPoints.length > 0 && (
                        <>
                            <line
                                x1={completedPoints[completedPoints.length - 1].x}
                                y1={completedPoints[completedPoints.length - 1].y}
                                x2={projectedPoint.x}
                                y2={projectedPoint.y}
                                stroke={color}
                                strokeWidth={2}
                                strokeDasharray="8,5"
                                opacity={0.7}
                                style={{ filter: `drop-shadow(0 0 6px ${color})` }}
                            />
                            {/* D zone rectangle (price range) */}
                            {hp?.projectedD && (() => {
                                const chart = chartRef.current;
                                const series = candleSeriesRef.current;
                                if (!chart || !series) return null;
                                const yMin = series.priceToCoordinate(hp.projectedD.priceMax);
                                const yMax = series.priceToCoordinate(hp.projectedD.priceMin);
                                if (yMin === null || yMax === null) return null;
                                return (
                                    <rect
                                        x={projectedPoint.x - 15}
                                        y={Math.min(yMin as number, yMax as number)}
                                        width={30}
                                        height={Math.abs((yMax as number) - (yMin as number))}
                                        fill={`${color}20`}
                                        stroke={color}
                                        strokeWidth={1}
                                        strokeDasharray="4,3"
                                        rx={4}
                                        className={styles.projectedZone}
                                    />
                                );
                            })()}
                            {/* Arrow after D showing expected direction */}
                            {(() => {
                                const dir = pattern.direction;
                                const arrowLen = 30;
                                const arrowY = dir === 'BULLISH'
                                    ? projectedPoint.y - arrowLen
                                    : projectedPoint.y + arrowLen;
                                return (
                                    <g className={styles.projectionArrow}>
                                        <line
                                            x1={projectedPoint.x}
                                            y1={projectedPoint.y}
                                            x2={projectedPoint.x}
                                            y2={arrowY}
                                            stroke={dir === 'BULLISH' ? '#16C784' : '#EA3943'}
                                            strokeWidth={2.5}
                                            strokeDasharray="4,3"
                                            opacity={0.8}
                                        />
                                        <polygon
                                            points={dir === 'BULLISH'
                                                ? `${projectedPoint.x - 6},${arrowY + 8} ${projectedPoint.x},${arrowY} ${projectedPoint.x + 6},${arrowY + 8}`
                                                : `${projectedPoint.x - 6},${arrowY - 8} ${projectedPoint.x},${arrowY} ${projectedPoint.x + 6},${arrowY - 8}`}
                                            fill={dir === 'BULLISH' ? '#16C784' : '#EA3943'}
                                            opacity={0.8}
                                        />
                                    </g>
                                );
                            })()}
                        </>
                    )}

                    {/* Point markers + labels */}
                    {pixelPoints.map((pt, ptIdx) => {
                        const isProjectedPt = isForming && ptIdx === pixelPoints.length - 1;
                        return (
                            <g
                                key={`pt-${ptIdx}`}
                                className={styles.pointMarker}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedPattern(pattern);
                                }}
                            >
                                {isBig && !isProjectedPt && (
                                    <circle
                                        cx={pt.x}
                                        cy={pt.y}
                                        r={10}
                                        fill="none"
                                        stroke={color}
                                        strokeWidth={1}
                                        opacity={0.4}
                                        className={styles.glowRing}
                                    />
                                )}
                                <circle
                                    cx={pt.x}
                                    cy={pt.y}
                                    r={isBig ? 5 : 3.5}
                                    fill={isProjectedPt ? 'transparent' : color}
                                    stroke={isProjectedPt ? color : "#fff"}
                                    strokeWidth={isProjectedPt ? 2 : 1.5}
                                    strokeDasharray={isProjectedPt ? "3,2" : undefined}
                                />
                                <text
                                    x={pt.x + (ptIdx % 2 === 0 ? 10 : -10)}
                                    y={pt.y - 10}
                                    fill={isProjectedPt ? color : "#fff"}
                                    fontSize="11"
                                    fontWeight="bold"
                                    textAnchor={ptIdx % 2 === 0 ? "start" : "end"}
                                    style={{
                                        textShadow: `0 0 6px ${color}`,
                                        opacity: isProjectedPt ? 0.7 : 1,
                                    }}
                                >
                                    {pt.label}{isProjectedPt ? "?" : ""}
                                </text>
                            </g>
                        );
                    })}

                    {/* Formation name near last completed point */}
                    {completedPoints.length > 0 && (
                        <text
                            x={completedPoints[completedPoints.length - 1].x + 15}
                            y={completedPoints[completedPoints.length - 1].y + 4}
                            fill={color}
                            fontSize="10"
                            fontWeight="bold"
                            className={styles.formationLabel}
                            style={{ textShadow: `0 0 8px ${color}` }}
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPattern(pattern);
                            }}
                        >
                            {getPatternEmoji(pattern)} {getPatternDisplayName(pattern, locale)}
                            {pattern.direction === "BULLISH" ? " ↑" : " ↓"}
                            {isForming ? " (FORMING)" : ""}
                        </text>
                    )}
                </g>
            );
        });
    }, [overlayData, locale]);

    // ── Render
    return (
        <div className={`${styles.panel} ${isFullscreen ? styles.panelFullscreen : ''}`}>
            {/* Header */}
            <PanelHeader
                title="HARMONIC"
                subtitle="PATTERN VISUALIZER"
                icon={<Hexagon size={24} strokeWidth={2.5} />}
                iconColor="var(--accent-cyan)"
                iconBg="var(--accent-cyan-08)"
                iconBorder="var(--accent-cyan-15)"
                symbols={SYMBOLS}
                activeSymbol={symbol}
                onSymbolChange={setSymbol}
                timeframe={timeframe}
                onTimeframeChange={(tf) => setTimeframe(tf as TimeframeType)}
                timeframes={[...TIMEFRAMES]}
                onRefresh={() => refetch()}
                loading={isLoading}
                panelId="harmonic-visualizer"
            />

            {/* Color legend */}
            <div className={styles.legend}>
                <div className={styles.legendItem}>
                    <span className={styles.legendDot} style={{ background: HARMONIC_COLOR_CANDLE }} />
                    <span>Harmonic (XABCD)</span>
                </div>
                <div className={styles.legendItem}>
                    <span className={styles.legendDot} style={{ background: CLASSIC_COLOR_CANDLE }} />
                    <span>Classic Patterns</span>
                </div>
                <div className={styles.legendItem}>
                    <span className={styles.legendDotDashed} style={{ borderColor: HARMONIC_COLOR }} />
                    <span>Projected (Forming)</span>
                </div>
            </div>

            {/* Chart area */}
            <div className={styles.chartWrapper}>
                {isLoading && (
                    <div className={styles.loadingOverlay}>
                        <Activity size={24} className={styles.spin} />
                        <span>{t("harmonicVisualizer.loadingChart")}</span>
                    </div>
                )}
                {error && (
                    <div className={styles.errorOverlay}>
                        <span>⚠️ {t("harmonicVisualizer.noChartData")}</span>
                    </div>
                )}
                <div ref={chartContainerRef} className={styles.chartContainer} />

                {/* SVG Formation Overlay */}
                {overlayData.length > 0 && (
                    <svg
                        className={styles.svgOverlay}
                        width={chartSize.width}
                        height={chartSize.height}
                    >
                        {svgElements}
                    </svg>
                )}
            </div>

            {/* Pattern list */}
            <div className={styles.patternList}>
                <div className={styles.patternListHeader}>
                    <Activity size={14} />
                    <span>
                        {t("harmonicVisualizer.activePatterns")} ({patterns.length})
                    </span>
                    {patterns.length > 0 && (
                        <span className={styles.clickHint}>{t("harmonicVisualizer.clickToView")}</span>
                    )}
                </div>
                {patterns.length === 0 ? (
                    <div className={styles.noPatterns}>{t("harmonicVisualizer.noPatterns")}</div>
                ) : (
                    <div className={styles.patternCards}>
                        {patterns.map((p, idx) => {
                            const big = isHarmonicPattern(p);
                            return (
                                <div
                                    key={idx}
                                    className={`${styles.patternCard} ${big ? styles.patternCardBig : styles.patternCardSmall} ${p.status === 'FORMING' ? styles.patternCardForming : ''}`}
                                    onClick={() => setSelectedPattern(p)}
                                >
                                    <div className={styles.patternCardTop}>
                                        <span className={styles.patternEmoji}>
                                            {getPatternEmoji(p)}
                                        </span>
                                        <span className={styles.patternName}>
                                            {getPatternDisplayName(p, locale)}
                                        </span>
                                        <span
                                            className={`${styles.dirBadge} ${p.direction === "BULLISH"
                                                ? styles.bullish
                                                : styles.bearish
                                                }`}
                                        >
                                            {p.direction === "BULLISH" ? "↑" : "↓"}{" "}
                                            {p.direction === "BULLISH"
                                                ? t("harmonicVisualizer.bullish")
                                                : t("harmonicVisualizer.bearish")}
                                        </span>
                                    </div>
                                    <div className={styles.patternCardBottom}>
                                        <span className={`${styles.confBadge} ${getConfidenceClass(p.confidence)}`}>
                                            {t("harmonicVisualizer.confidence")}: {p.confidence}%
                                        </span>
                                        <span className={`${styles.statusBadge} ${p.status === 'FORMING' ? styles.statusForming : ''}`}>
                                            {p.status === "COMPLETED" ? t("harmonicVisualizer.completed") : t("harmonicVisualizer.forming")}
                                        </span>
                                        {p.target_price && (
                                            <span className={styles.tpBadge}>
                                                TP: {p.target_price.toFixed(2)}
                                            </span>
                                        )}
                                        {isHarmonicPattern(p) && p.projectedD && (
                                            <span className={styles.projBadge}>
                                                D: {p.projectedD.priceMin.toFixed(0)}-{p.projectedD.priceMax.toFixed(0)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Detail Modal */}
            {selectedPattern && (
                <div className={styles.modalBackdrop} onClick={() => setSelectedPattern(null)}>
                    <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                        <button className={styles.modalClose} onClick={() => setSelectedPattern(null)}>
                            <XIcon size={18} />
                        </button>

                        <div className={`${styles.modalHeader} ${isHarmonicPattern(selectedPattern) ? styles.modalHeaderBig : styles.modalHeaderSmall}`}>
                            <span className={styles.modalEmoji}>{getPatternEmoji(selectedPattern)}</span>
                            <h3>{getPatternDisplayName(selectedPattern, locale)} {t("harmonicVisualizer.formation")}</h3>
                            <span className={`${styles.modalDir} ${selectedPattern.direction === "BULLISH" ? styles.bullish : styles.bearish}`}>
                                {selectedPattern.direction === "BULLISH" ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                {selectedPattern.direction === "BULLISH" ? t("harmonicVisualizer.bullish") : t("harmonicVisualizer.bearish")}
                            </span>
                        </div>

                        <div className={styles.modalBody}>
                            <div className={styles.detailRow}>
                                <span>{t("harmonicVisualizer.confidence")}</span>
                                <strong className={getConfidenceClass(selectedPattern.confidence)}>
                                    %{selectedPattern.confidence}
                                </strong>
                            </div>

                            <div className={styles.detailRow}>
                                <span>{t("harmonicVisualizer.status")}</span>
                                <strong>{selectedPattern.status === "COMPLETED" ? t("harmonicVisualizer.completed") : t("harmonicVisualizer.forming")}</strong>
                            </div>

                            <div className={styles.detailRow}>
                                <span>{t("harmonicVisualizer.expectedMove")}</span>
                                <strong style={{ color: selectedPattern.direction === "BULLISH" ? "#16C784" : "#EA3943" }}>
                                    {selectedPattern.direction === "BULLISH" ? `${t("harmonicVisualizer.upward")} ↑` : `${t("harmonicVisualizer.downward")} ↓`}
                                </strong>
                            </div>

                            {selectedPattern.target_price && (
                                <div className={styles.detailRow}>
                                    <span><Target size={14} /> {t("harmonicVisualizer.targetPrice")}</span>
                                    <strong style={{ color: P.green }}>
                                        {selectedPattern.target_price.toFixed(2)}
                                    </strong>
                                </div>
                            )}

                            {selectedPattern.stop_loss && (
                                <div className={styles.detailRow}>
                                    <span><ShieldAlert size={14} /> {t("harmonicVisualizer.stopLossLabel")}</span>
                                    <strong style={{ color: "#ff4444" }}>
                                        {selectedPattern.stop_loss.toFixed(2)}
                                    </strong>
                                </div>
                            )}

                            {/* Projected D zone for forming patterns */}
                            {isHarmonicPattern(selectedPattern) && selectedPattern.projectedD && (
                                <div className={styles.detailRow}>
                                    <span>D Zone</span>
                                    <strong style={{ color: HARMONIC_COLOR }}>
                                        {selectedPattern.projectedD.priceMin.toFixed(2)} - {selectedPattern.projectedD.priceMax.toFixed(2)}
                                    </strong>
                                </div>
                            )}

                            {isHarmonicPattern(selectedPattern) && (
                                <div className={styles.pointsGrid}>
                                    {(["X", "A", "B", "C", "D"] as const).map((key) => {
                                        const pt = selectedPattern.points[key];
                                        const isProj = key === "D" && selectedPattern.isProjected;
                                        return (
                                            <div key={key} className={`${styles.pointItem} ${isProj ? styles.pointItemProjected : ''}`}>
                                                <span className={styles.pointKey}>{key}{isProj ? "?" : ""}</span>
                                                <span className={styles.pointPrice}>{pt.price.toFixed(2)}</span>
                                                <span className={styles.pointTime}>{isProj ? "Projected" : formatTime(pt.time)}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {isHarmonicPattern(selectedPattern) && (
                                <div className={styles.fibSection}>
                                    <span className={styles.fibTitle}>{t("harmonicVisualizer.fibRatios")}</span>
                                    <div className={styles.fibValues}>
                                        <span>AB/XA: {selectedPattern.fibRatios.ab}</span>
                                        <span>BC/AB: {selectedPattern.fibRatios.bc}</span>
                                        {selectedPattern.fibRatios.cd > 0 && <span>CD/BC: {selectedPattern.fibRatios.cd}</span>}
                                        <span>AD/XA: {selectedPattern.fibRatios.xd}</span>
                                    </div>
                                </div>
                            )}

                            {!isHarmonicPattern(selectedPattern) && (
                                <div className={styles.pointsGrid}>
                                    {(selectedPattern as ClassicPattern).points.map((pt, idx) => (
                                        <div key={idx} className={styles.pointItem}>
                                            <span className={styles.pointKey}>P{idx + 1}</span>
                                            <span className={styles.pointPrice}>{pt.price.toFixed(2)}</span>
                                            <span className={styles.pointTime}>{formatTime(pt.time)}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className={styles.modalFooter}>
                            <button
                                className={styles.alarmBtn}
                                onClick={() => setSelectedPattern(null)}
                            >
                                🔔 {t("harmonicVisualizer.setAlarm")}
                            </button>
                            <button
                                className={styles.closeBtn}
                                onClick={() => setSelectedPattern(null)}
                            >
                                {t("harmonicVisualizer.close")}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
