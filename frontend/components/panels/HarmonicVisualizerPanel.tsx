"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
    ColorType,
    createChart,
    CrosshairMode,
    IChartApi,
    ISeriesApi,
    Time,
} from "lightweight-charts";
import { Activity, RefreshCw, Hexagon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useI18nStore } from "../../lib/i18n/store";
import {
    HarmonicPattern,
    ClassicPattern,
    DetectedPattern,
    HARMONIC_PATTERNS,
    CLASSIC_PATTERNS,
    CandleData,
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

// ─── COMPONENT ───────────────────────────────────────────────────────

export default function HarmonicVisualizerPanel() {
    const { t, locale } = useI18nStore();
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const lineSeriesRefs = useRef<ISeriesApi<"Line">[]>([]);

    const [symbol, setSymbol] = useState<string>("XAUUSD");
    const [timeframe, setTimeframe] = useState<TimeframeType>("15m");
    const [detectedPatterns, setDetectedPatterns] = useState<DetectedPattern[]>(
        []
    );

    // Fetch OHLCV data
    const {
        data: candles,
        isLoading,
        refetch,
    } = useQuery({
        queryKey: ["harmonic-ohlcv", symbol, timeframe],
        queryFn: () => fetchOHLCV(symbol, timeframe),
        refetchInterval: 30000,
        staleTime: 15000,
    });

    // ── Initialize Chart ──
    useEffect(() => {
        if (!chartContainerRef.current) return;
        if (chartRef.current) return;

        const container = chartContainerRef.current;

        const chart = createChart(container, {
            width: container.clientWidth,
            height: 480,
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: "#9ca3af",
                fontSize: 11,
            },
            watermark: { visible: false },
            grid: {
                vertLines: { color: "rgba(0, 217, 255, 0.04)" },
                horzLines: { color: "rgba(0, 217, 255, 0.04)" },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
                vertLine: {
                    color: "rgba(0, 217, 255, 0.3)",
                    labelBackgroundColor: "#1a1f3a",
                },
                horzLine: {
                    color: "rgba(0, 217, 255, 0.3)",
                    labelBackgroundColor: "#1a1f3a",
                },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: "rgba(255, 255, 255, 0.06)",
            },
            rightPriceScale: {
                borderColor: "rgba(255, 255, 255, 0.06)",
            },
        });

        const candleSeries = chart.addCandlestickSeries({
            upColor: "#00d9ff",
            downColor: "#ff00ff",
            borderVisible: false,
            wickUpColor: "#00d9ff",
            wickDownColor: "#ff00ff",
        });

        const resizeObserver = new ResizeObserver(() => {
            try {
                chart.applyOptions({ width: container.clientWidth });
            } catch {
                // noop
            }
        });
        resizeObserver.observe(container);

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;

        return () => {
            resizeObserver.disconnect();
            chart.remove();
            chartRef.current = null;
            candleSeriesRef.current = null;
        };
    }, []);

    // ── Update Chart Data + Detect Patterns ──
    useEffect(() => {
        const chart = chartRef.current;
        const candleSeries = candleSeriesRef.current;

        if (!chart || !candleSeries || !candles || candles.length < 10) return;

        try {
            // Set candle data
            const chartCandles = candles.map((c) => ({
                time: c.time as Time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close,
            }));
            candleSeries.setData(chartCandles);

            // Clear old pattern lines
            lineSeriesRefs.current.forEach((line) => {
                try {
                    chart.removeSeries(line);
                } catch {
                    // series may already be removed
                }
            });
            lineSeriesRefs.current = [];

            // Detect patterns
            const harmonic = detectHarmonicPatterns(candles);
            const classic = detectClassicPatterns(candles);
            const allPatterns = [...harmonic, ...classic];
            setDetectedPatterns(allPatterns);

            // Draw harmonic patterns on chart
            const allMarkers: any[] = [];

            harmonic.forEach((pattern) => {
                const { X, A, B, C, D } = pattern.points;
                const color = pattern.color;

                // Draw XABCD connecting line
                try {
                    const lineSeries = chart.addLineSeries({
                        color: color,
                        lineWidth: 2,
                        lineStyle: 0,
                        lastValueVisible: false,
                        priceLineVisible: false,
                        crosshairMarkerVisible: false,
                        title: "",
                    });

                    lineSeries.setData([
                        { time: X.time as Time, value: X.price },
                        { time: A.time as Time, value: A.price },
                        { time: B.time as Time, value: B.price },
                        { time: C.time as Time, value: C.price },
                        { time: D.time as Time, value: D.price },
                    ]);

                    lineSeriesRefs.current.push(lineSeries);
                } catch {
                    // skip if line creation fails
                }

                // Add markers
                allMarkers.push(
                    {
                        time: X.time as Time,
                        position: X.type === "high" ? "aboveBar" : "belowBar",
                        color,
                        shape: "circle",
                        text: "X",
                        size: 1,
                    },
                    {
                        time: A.time as Time,
                        position: A.type === "high" ? "aboveBar" : "belowBar",
                        color,
                        shape: "circle",
                        text: "A",
                        size: 1,
                    },
                    {
                        time: B.time as Time,
                        position: B.type === "high" ? "aboveBar" : "belowBar",
                        color,
                        shape: "circle",
                        text: "B",
                        size: 1,
                    },
                    {
                        time: C.time as Time,
                        position: C.type === "high" ? "aboveBar" : "belowBar",
                        color,
                        shape: "circle",
                        text: "C",
                        size: 1,
                    },
                    {
                        time: D.time as Time,
                        position: D.type === "high" ? "aboveBar" : "belowBar",
                        color: "#ffffff",
                        shape: "square",
                        text: "D",
                        size: 2,
                    }
                );
            });

            // Draw classic pattern lines
            classic.forEach((pattern) => {
                if (pattern.points.length >= 2) {
                    try {
                        const lineSeries = chart.addLineSeries({
                            color: pattern.color,
                            lineWidth: 2,
                            lineStyle: 2, // dashed
                            lastValueVisible: false,
                            priceLineVisible: false,
                            crosshairMarkerVisible: false,
                            title: "",
                        });

                        const lineData = pattern.points.map((p) => ({
                            time: p.time as Time,
                            value: p.price,
                        }));

                        lineSeries.setData(lineData);
                        lineSeriesRefs.current.push(lineSeries);
                    } catch {
                        // skip
                    }

                    // Add markers for classic patterns
                    pattern.points.forEach((p, idx) => {
                        allMarkers.push({
                            time: p.time as Time,
                            position: p.type === "high" ? "aboveBar" : "belowBar",
                            color: pattern.color,
                            shape: "circle",
                            text: `P${idx + 1}`,
                            size: 1,
                        });
                    });
                }

                // Draw neckline if present
                if (pattern.neckline && pattern.points.length >= 2) {
                    try {
                        const necklineSeries = chart.addLineSeries({
                            color: pattern.color,
                            lineWidth: 1,
                            lineStyle: 3,
                            lastValueVisible: false,
                            priceLineVisible: false,
                            crosshairMarkerVisible: false,
                            title: "",
                        });

                        necklineSeries.setData([
                            {
                                time: pattern.points[0].time as Time,
                                value: pattern.neckline,
                            },
                            {
                                time: pattern.points[pattern.points.length - 1].time as Time,
                                value: pattern.neckline,
                            },
                        ]);

                        lineSeriesRefs.current.push(necklineSeries);
                    } catch {
                        // skip
                    }
                }
            });

            // Sort markers by time and set them
            if (allMarkers.length > 0) {
                allMarkers.sort(
                    (a, b) => (a.time as number) - (b.time as number)
                );
                candleSeries.setMarkers(allMarkers);
            }

            chart.timeScale().fitContent();
        } catch (err) {
            console.error("[HarmonicVisualizer] Chart update error:", err);
        }
    }, [candles]);

    // ── Symbol Change Handler ──
    const handleSymbolChange = useCallback(
        (newSymbol: string) => {
            setSymbol(newSymbol);
            setDetectedPatterns([]);
            // Clear markers
            if (candleSeriesRef.current) {
                candleSeriesRef.current.setMarkers([]);
            }
        },
        []
    );

    // ── Render ──
    const symbolLabel =
        SYMBOLS.find((s) => s.value === symbol)?.label || symbol;

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <div className={styles.iconWrapper}>
                        <Hexagon className="h-5 w-5 text-cyan-400" />
                    </div>
                    <div>
                        <div className={styles.title}>
                            {t("harmonicVisualizer.title")}
                        </div>
                        <div className={styles.subtitle}>
                            {symbolLabel} • {timeframe.toUpperCase()}
                        </div>
                    </div>
                </div>

                <div className={styles.headerRight}>
                    {/* Symbol selector */}
                    <div className={styles.symbolSelector}>
                        {SYMBOLS.map((s) => (
                            <button
                                key={s.value}
                                className={
                                    symbol === s.value
                                        ? styles.symbolBtnActive
                                        : styles.symbolBtn
                                }
                                onClick={() => handleSymbolChange(s.value)}
                            >
                                {s.label}
                            </button>
                        ))}
                    </div>

                    {/* Timeframe tabs */}
                    <div className={styles.timeframeTabs}>
                        {TIMEFRAMES.map((tf) => (
                            <button
                                key={tf}
                                className={
                                    timeframe === tf ? styles.tfBtnActive : styles.tfBtn
                                }
                                onClick={() => setTimeframe(tf)}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>

                    {/* Refresh */}
                    <button
                        className={styles.refreshBtn}
                        onClick={() => refetch()}
                        disabled={isLoading}
                    >
                        <RefreshCw
                            className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
                        />
                    </button>

                    {/* Pattern count */}
                    {detectedPatterns.length > 0 && (
                        <span className={styles.patternCount}>
                            {detectedPatterns.length}
                        </span>
                    )}
                </div>
            </div>

            {/* Chart Area */}
            <div className={styles.chartArea}>
                <div className={styles.chartContainer} style={{ position: "relative" }}>
                    {/* Pattern Overlay */}
                    {detectedPatterns.length > 0 && (
                        <div className={styles.patternOverlay}>
                            <div className={styles.overlayTitle}>
                                🎯 {t("harmonicVisualizer.activePatterns")}
                            </div>
                            {detectedPatterns.map((pattern, i) => (
                                <div
                                    key={`${pattern.type}-${i}`}
                                    className={`${styles.patternItem} ${styles.patternActive}`}
                                    style={{ borderLeftColor: pattern.color }}
                                >
                                    <div style={{ flex: 1 }}>
                                        <div
                                            className={styles.patternName}
                                            style={{ color: pattern.color }}
                                        >
                                            {getPatternEmoji(pattern)}{" "}
                                            {getPatternDisplayName(pattern, locale)}
                                        </div>
                                        <div className={styles.patternMeta}>
                                            <span
                                                className={
                                                    pattern.direction === "BULLISH"
                                                        ? styles.directionBullish
                                                        : pattern.direction === "BEARISH"
                                                            ? styles.directionBearish
                                                            : ""
                                                }
                                            >
                                                {pattern.direction === "BULLISH"
                                                    ? t("harmonicVisualizer.bullish")
                                                    : pattern.direction === "BEARISH"
                                                        ? t("harmonicVisualizer.bearish")
                                                        : "NEUTRAL"}
                                            </span>
                                            {" • "}
                                            <span
                                                className={getConfidenceClass(pattern.confidence)}
                                            >
                                                {t("harmonicVisualizer.confidence")}:{" "}
                                                {pattern.confidence}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Chart canvas */}
                    <div
                        ref={chartContainerRef}
                        style={{ height: 480, width: "100%" }}
                    />

                    {/* Loading overlay */}
                    {(isLoading || !candles?.length) && (
                        <div className={styles.loadingOverlay}>
                            <Activity className="h-10 w-10 opacity-30 animate-pulse text-cyan-400" />
                            <div className={styles.loadingText}>
                                {isLoading
                                    ? t("harmonicVisualizer.loadingChart")
                                    : t("harmonicVisualizer.noChartData")}
                            </div>
                        </div>
                    )}

                    {/* No patterns message */}
                    {!isLoading && candles && candles.length > 0 && detectedPatterns.length === 0 && (
                        <div className={styles.patternOverlay}>
                            <div className={styles.overlayTitle}>
                                🎯 {t("harmonicVisualizer.activePatterns")}
                            </div>
                            <div className={styles.emptyPatterns}>
                                {t("harmonicVisualizer.noPatterns")}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Footer — Pattern color legend */}
            <div className={styles.footer}>
                {Object.entries(HARMONIC_PATTERNS).map(([key, config]) => (
                    <div key={key} className={styles.legendItem}>
                        <div
                            className={styles.legendDot}
                            style={{ backgroundColor: config.color, color: config.color }}
                        />
                        <span>
                            {locale === "tr" ? config.nameTr : config.name}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
