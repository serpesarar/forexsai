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
import { Activity, RefreshCw, Hexagon, X as XIcon, Target, ShieldAlert, TrendingUp, TrendingDown } from "lucide-react";
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
    HARMONIC_COLOR_DARK,
    HARMONIC_FILL,
    HARMONIC_GLOW,
    CLASSIC_COLOR,
    CLASSIC_FILL,
} from "../../types/harmonicPatterns";
import {
    detectHarmonicPatterns,
    detectClassicPatterns,
} from "../../utils/harmonicPatternDetector";
import styles from "./harmonic-visualizer.module.css";

// ─── CONFIG ──────────────────────────────────────────────────────────

const API_BASE = "https://upbeat-flow-production.up.railway.app";

const SYMBOLS = [
    { value: "NDX.INDX", label: "NASDAQ" },
    { value: "XAUUSD", label: "XAU/USD" },
] as const;

const TIMEFRAMES = ["5m", "15m", "1h", "4h"] as const;
type TimeframeType = (typeof TIMEFRAMES)[number];

// ─── DATA FETCHING ───────────────────────────────────────────────────

async function fetchOHLCV(
    symbol: string,
    timeframe: string
): Promise<CandleData[]> {
    const res = await fetch(
        `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(
            symbol
        )}&timeframe=${timeframe}&limit=200`
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

/** Throttle helper to limit resize calls */
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

/** Format Unix timestamp to readable date string */
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
    const [symbol, setSymbol] = useState<string>(SYMBOLS[0].value);
    const [timeframe, setTimeframe] = useState<TimeframeType>("15m");
    const [selectedPattern, setSelectedPattern] = useState<DetectedPattern | null>(null);
    const [chartSize, setChartSize] = useState({ width: 0, height: 0 });
    const [overlayVersion, setOverlayVersion] = useState(0); // Forces SVG re-render

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
                vertLines: { color: "rgba(42,46,57,0.5)" },
                horzLines: { color: "rgba(42,46,57,0.5)" },
            },
            crosshair: { mode: CrosshairMode.Normal },
            width: container.clientWidth,
            height: container.clientHeight || 450,
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
            borderVisible: false,
            wickUpColor: "#26a69a",
            wickDownColor: "#ef5350",
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;

        // Throttled resize handler
        const handleResize = throttle(() => {
            if (!container) return;
            const w = container.clientWidth;
            const h = container.clientHeight || 450;
            chart.applyOptions({ width: w, height: h });
            setChartSize({ width: w, height: h });
            setOverlayVersion(v => v + 1);
        }, 100);

        const observer = new ResizeObserver(handleResize);
        observer.observe(container);
        handleResize();

        // Update overlay when chart scrolls/zooms
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

    // ── Update chart data
    useEffect(() => {
        if (!candleSeriesRef.current || !candles || candles.length === 0) return;
        const chartData = candles.map((c) => ({
            time: c.time as Time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
        }));
        candleSeriesRef.current.setData(chartData);
        chartRef.current?.timeScale().fitContent();
        // Force overlay recalc after data load
        setTimeout(() => setOverlayVersion(v => v + 1), 100);
    }, [candles]);

    // ── Calculate SVG overlay data (with viewport filtering & null checks)
    const overlayData = useMemo<FormationOverlayData[]>(() => {
        const chart = chartRef.current;
        const series = candleSeriesRef.current;
        if (!chart || !series || patterns.length === 0) return [];

        const timeScale = chart.timeScale();

        // Get visible range for viewport filtering
        const visibleRange = timeScale.getVisibleRange();

        const result: FormationOverlayData[] = [];

        for (const pattern of patterns) {
            const isBig = isHarmonicPattern(pattern);
            const color = isBig ? HARMONIC_COLOR : CLASSIC_COLOR;

            // Get points based on pattern type
            let rawPoints: { label: string; time: number; price: number }[];
            if (isBig) {
                const hp = pattern as HarmonicPattern;
                rawPoints = [
                    { label: "X", time: hp.points.X.time, price: hp.points.X.price },
                    { label: "A", time: hp.points.A.time, price: hp.points.A.price },
                    { label: "B", time: hp.points.B.time, price: hp.points.B.price },
                    { label: "C", time: hp.points.C.time, price: hp.points.C.price },
                    { label: "D", time: hp.points.D.time, price: hp.points.D.price },
                ];
            } else {
                const cp = pattern as ClassicPattern;
                rawPoints = cp.points.map((pt, idx) => ({
                    label: `P${idx + 1}`,
                    time: pt.time,
                    price: pt.price,
                }));
            }

            // Viewport filter: skip if pattern is entirely outside visible range
            if (visibleRange) {
                const from = visibleRange.from as number;
                const to = visibleRange.to as number;
                const patternTimes = rawPoints.map(p => p.time);
                const patternMin = Math.min(...patternTimes);
                const patternMax = Math.max(...patternTimes);
                // Skip if pattern is completely outside viewport
                if (patternMax < from || patternMin > to) continue;
            }

            // Convert to pixel coordinates (with null safety)
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

    // ── Render SVG overlay elements (memoized)
    const svgElements = useMemo(() => {
        return overlayData.map((data, idx) => {
            const { pixelPoints, isBig, color, pattern } = data;

            // Build polyline points string
            const pointsStr = pixelPoints.map(p => `${p.x},${p.y}`).join(" ");

            // Build polygon fill path for big formations
            const polygonPoints = isBig ? pointsStr : undefined;

            return (
                <g key={`formation-${idx}`} className={isBig ? styles.formationGlowBig : styles.formationGlowSmall}>
                    {/* Filled region (transparent) */}
                    {isBig && polygonPoints && (
                        <polygon
                            points={polygonPoints}
                            fill={HARMONIC_FILL}
                            stroke="none"
                        />
                    )}

                    {/* Main formation line */}
                    <polyline
                        points={pointsStr}
                        fill="none"
                        stroke={color}
                        strokeWidth={isBig ? 3 : 2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeDasharray={pattern.status === "FORMING" ? "8,4" : undefined}
                        style={{
                            filter: isBig ? `drop-shadow(0 0 8px ${color}) drop-shadow(0 0 16px ${HARMONIC_GLOW})` : "none",
                        }}
                    />

                    {/* Point markers + labels */}
                    {pixelPoints.map((pt, ptIdx) => (
                        <g
                            key={`pt-${ptIdx}`}
                            className={styles.pointMarker}
                            onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPattern(pattern);
                            }}
                        >
                            {/* Glow ring for big formations */}
                            {isBig && (
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
                            {/* Point dot */}
                            <circle
                                cx={pt.x}
                                cy={pt.y}
                                r={isBig ? 5 : 3.5}
                                fill={color}
                                stroke="#fff"
                                strokeWidth={1.5}
                            />
                            {/* Label */}
                            <text
                                x={pt.x + (ptIdx % 2 === 0 ? 10 : -10)}
                                y={pt.y - 10}
                                fill="#fff"
                                fontSize="11"
                                fontWeight="bold"
                                textAnchor={ptIdx % 2 === 0 ? "start" : "end"}
                                style={{ textShadow: `0 0 6px ${color}` }}
                            >
                                {pt.label}
                            </text>
                        </g>
                    ))}

                    {/* Formation name near last point */}
                    {pixelPoints.length > 0 && (
                        <text
                            x={pixelPoints[pixelPoints.length - 1].x + 15}
                            y={pixelPoints[pixelPoints.length - 1].y + 4}
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
                        </text>
                    )}
                </g>
            );
        });
    }, [overlayData, locale]);

    // ── Render
    return (
        <div className={styles.panel}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <Hexagon size={18} className={styles.iconGlow} />
                    <h2 className={styles.title}>{t("harmonicVisualizer.title")}</h2>
                </div>
                <div className={styles.headerControls}>
                    {/* Symbol selector */}
                    <select
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value)}
                        className={styles.select}
                    >
                        {SYMBOLS.map((s) => (
                            <option key={s.value} value={s.value}>
                                {s.label}
                            </option>
                        ))}
                    </select>
                    {/* Timeframe selector */}
                    <div className={styles.timeframeGroup}>
                        {TIMEFRAMES.map((tf) => (
                            <button
                                key={tf}
                                onClick={() => setTimeframe(tf)}
                                className={`${styles.tfBtn} ${timeframe === tf ? styles.tfBtnActive : ""}`}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>
                    {/* Refresh */}
                    <button
                        onClick={() => refetch()}
                        className={styles.refreshBtn}
                        title="Refresh"
                    >
                        <RefreshCw size={14} className={isLoading ? styles.spin : ""} />
                    </button>
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
                                    className={`${styles.patternCard} ${big ? styles.patternCardBig : styles.patternCardSmall}`}
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
                                        <span className={styles.statusBadge}>
                                            {p.status === "COMPLETED" ? t("harmonicVisualizer.completed") : t("harmonicVisualizer.forming")}
                                        </span>
                                        {p.target_price && (
                                            <span className={styles.tpBadge}>
                                                TP: {p.target_price.toFixed(2)}
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

                        {/* Modal Header */}
                        <div className={`${styles.modalHeader} ${isHarmonicPattern(selectedPattern) ? styles.modalHeaderBig : styles.modalHeaderSmall}`}>
                            <span className={styles.modalEmoji}>{getPatternEmoji(selectedPattern)}</span>
                            <h3>{getPatternDisplayName(selectedPattern, locale)} {t("harmonicVisualizer.formation")}</h3>
                            <span className={`${styles.modalDir} ${selectedPattern.direction === "BULLISH" ? styles.bullish : styles.bearish}`}>
                                {selectedPattern.direction === "BULLISH" ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                {selectedPattern.direction === "BULLISH" ? t("harmonicVisualizer.bullish") : t("harmonicVisualizer.bearish")}
                            </span>
                        </div>

                        {/* Modal Body */}
                        <div className={styles.modalBody}>
                            {/* Confidence */}
                            <div className={styles.detailRow}>
                                <span>{t("harmonicVisualizer.confidence")}</span>
                                <strong className={getConfidenceClass(selectedPattern.confidence)}>
                                    %{selectedPattern.confidence}
                                </strong>
                            </div>

                            {/* Status */}
                            <div className={styles.detailRow}>
                                <span>{t("harmonicVisualizer.status")}</span>
                                <strong>{selectedPattern.status === "COMPLETED" ? t("harmonicVisualizer.completed") : t("harmonicVisualizer.forming")}</strong>
                            </div>

                            {/* Direction */}
                            <div className={styles.detailRow}>
                                <span>{t("harmonicVisualizer.expectedMove")}</span>
                                <strong style={{ color: selectedPattern.direction === "BULLISH" ? "#00ff88" : "#ff4444" }}>
                                    {selectedPattern.direction === "BULLISH" ? `${t("harmonicVisualizer.upward")} ↑` : `${t("harmonicVisualizer.downward")} ↓`}
                                </strong>
                            </div>

                            {/* Target Price */}
                            {selectedPattern.target_price && (
                                <div className={styles.detailRow}>
                                    <span><Target size={14} /> {t("harmonicVisualizer.targetPrice")}</span>
                                    <strong style={{ color: "#00ff88" }}>
                                        {selectedPattern.target_price.toFixed(2)}
                                    </strong>
                                </div>
                            )}

                            {/* Stop Loss */}
                            {selectedPattern.stop_loss && (
                                <div className={styles.detailRow}>
                                    <span><ShieldAlert size={14} /> {t("harmonicVisualizer.stopLossLabel")}</span>
                                    <strong style={{ color: "#ff4444" }}>
                                        {selectedPattern.stop_loss.toFixed(2)}
                                    </strong>
                                </div>
                            )}

                            {/* Points (XABCD) for harmonic patterns */}
                            {isHarmonicPattern(selectedPattern) && (
                                <div className={styles.pointsGrid}>
                                    {(["X", "A", "B", "C", "D"] as const).map((key) => {
                                        const pt = selectedPattern.points[key];
                                        return (
                                            <div key={key} className={styles.pointItem}>
                                                <span className={styles.pointKey}>{key}</span>
                                                <span className={styles.pointPrice}>{pt.price.toFixed(2)}</span>
                                                <span className={styles.pointTime}>{formatTime(pt.time)}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Fib Ratios for harmonic patterns */}
                            {isHarmonicPattern(selectedPattern) && (
                                <div className={styles.fibSection}>
                                    <span className={styles.fibTitle}>{t("harmonicVisualizer.fibRatios")}</span>
                                    <div className={styles.fibValues}>
                                        <span>AB: {selectedPattern.fibRatios.ab}</span>
                                        <span>BC: {selectedPattern.fibRatios.bc}</span>
                                        <span>CD: {selectedPattern.fibRatios.cd}</span>
                                        <span>XD: {selectedPattern.fibRatios.xd}</span>
                                    </div>
                                </div>
                            )}

                            {/* Classic pattern points */}
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

                        {/* Modal Footer */}
                        <div className={styles.modalFooter}>
                            <button
                                className={styles.alarmBtn}
                                onClick={() => {
                                    // Placeholder for alarm functionality
                                    setSelectedPattern(null);
                                }}
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
