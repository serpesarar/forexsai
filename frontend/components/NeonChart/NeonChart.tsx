"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ColorType,
  createChart,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  Time,
} from "lightweight-charts";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, TrendingUp, TrendingDown, AlertTriangle, Zap, RefreshCw } from "lucide-react";
import { calculateAllEMAs, detectProximity } from "../../lib/chart/calculateEMA";
import type { ProximityAlert } from "../../lib/chart/calculateEMA";
import { normalizeCandles } from "../../lib/chart/normalizeCandles";
import styles from "./neon-chart.module.css";

// ─── Types ────────────────────────────────────────────────────────
interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface NeonChartProps {
  symbol: string;
  symbolLabel: string;
  initialTimeframe?: string;
  height?: number;
}

interface OHLCLegend {
  time: string;
  o: number;
  h: number;
  l: number;
  c: number;
}

// ─── Constants ────────────────────────────────────────────────────
const API_BASE = "https://upbeat-flow-production.up.railway.app";
const P = { bg: "var(--bg-primary)", card: "var(--bg-card)", surface: "var(--bg-surface)", border: "var(--border-subtle)", text: "var(--text-primary)", muted: "var(--text-muted)", green: "var(--accent-positive)", red: "var(--accent-negative)", warn: "var(--accent-warning)", accent: "var(--accent-info)", purple: "var(--accent-purple)" };

const TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"] as const;

const EMA_CONFIG = {
  20: { color: "#ff0080", glowColor: "rgba(255,0,128,0.6)", width: 1 as const, label: "EMA20" },
  50: { color: "#ffa500", glowColor: "rgba(255,165,0,0.6)", width: 2 as const, label: "EMA50" },
  200: { color: "var(--accent-info)", glowColor: "var(--accent-info-50)", width: 3 as const, label: "EMA200" },
};

// ─── Data fetching ────────────────────────────────────────────────
async function fetchChartData(symbol: string, timeframe: string): Promise<CandleData[]> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    const res = await fetch(
      `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=300`,
      { signal: controller.signal }
    );
    clearTimeout(timeout);
    if (!res.ok) return [];
    const data = await res.json();
    const candles = data.data || [];
    // If intraday returns empty, try daily as fallback
    if (candles.length === 0 && timeframe !== "1d") {
      return fetchChartData(symbol, "1d");
    }
    return normalizeCandles(candles, timeframe);
  } catch {
    return [];
  }
}

async function fetchLivePrice(symbol: string): Promise<number | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(
      `${API_BASE}/api/data/cached/${encodeURIComponent(symbol)}`,
      { signal: controller.signal }
    );
    clearTimeout(timeout);
    if (!res.ok) return null;
    const data = await res.json();
    return data?.data?.current_price ?? data?.data?.ta_snapshot?.current_price ?? null;
  } catch {
    return null;
  }
}

// ─── Particle system for cross events ─────────────────────────────
interface Particle {
  id: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  color: string;
}

function generateParticles(x: number, y: number, color: string): Particle[] {
  const particles: Particle[] = [];
  for (let i = 0; i < 12; i++) {
    const angle = (Math.PI * 2 * i) / 12 + (Math.random() * 0.5 - 0.25);
    const speed = 30 + Math.random() * 50;
    particles.push({
      id: Date.now() + i,
      x,
      y,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      color,
    });
  }
  return particles;
}

// ═══════════════════════════════════════════════════════════════════
//  NEON CHART COMPONENT
// ═══════════════════════════════════════════════════════════════════
export default function NeonChart({
  symbol,
  symbolLabel,
  initialTimeframe = "1h",
  height = 500,
}: NeonChartProps) {
  // ── Refs ──
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const emaSeriesRefs = useRef<Record<number, ISeriesApi<"Line">>>({});

  // ── State ──
  const [timeframe, setTimeframe] = useState(initialTimeframe);
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [ohlcLegend, setOhlcLegend] = useState<OHLCLegend | null>(null);
  const [proximityAlerts, setProximityAlerts] = useState<ProximityAlert[]>([]);
  const [particles, setParticles] = useState<Particle[]>([]);
  const [crossBanner, setCrossBanner] = useState<{ type: "golden" | "death"; label: string } | null>(null);
  const [chartReady, setChartReady] = useState(false);

  // ── Data fetching ──
  const { data: chartData, isLoading, refetch } = useQuery({
    queryKey: ["neon-chart", symbol, timeframe],
    queryFn: () => fetchChartData(symbol, timeframe),
    refetchInterval: 30000,
    staleTime: 15000,
  });

  // ── Live price polling ──
  useEffect(() => {
    const fetchPrice = async () => {
      const price = await fetchLivePrice(symbol);
      if (price !== null) setLivePrice(price);
    };
    fetchPrice();
    const interval = setInterval(fetchPrice, 5000);
    return () => clearInterval(interval);
  }, [symbol]);

  // ── Compute EMAs + proximity ──
  const { emaResults, latestValues, priceInfo } = useMemo(() => {
    const candles = chartData || [];
    if (candles.length === 0) {
      return { emaResults: {}, latestValues: {}, priceInfo: null };
    }

    const closes = candles.map((c) => c.close);
    const emaResults = calculateAllEMAs(closes);

    const latest = candles[candles.length - 1];
    const prev = candles.length >= 2 ? candles[candles.length - 2] : null;
    const change = prev ? latest.close - prev.close : 0;
    const changePct = prev ? (change / prev.close) * 100 : 0;

    const latestValues: Record<number, number | null> = {};
    for (const [period, ema] of Object.entries(emaResults)) {
      latestValues[Number(period)] = ema.latestValue;
    }

    return {
      emaResults,
      latestValues,
      priceInfo: {
        price: latest.close,
        change,
        changePct,
        high24: Math.max(...candles.slice(-24).map((c) => c.high)),
        low24: Math.min(...candles.slice(-24).map((c) => c.low)),
        volume: candles.slice(-24).reduce((sum, c) => sum + c.volume, 0),
      },
    };
  }, [chartData]);

  // ── Proximity detection ──
  useEffect(() => {
    if (!chartData || chartData.length < 2) return;
    const closes = chartData.map((c) => c.close);
    const currentPrice = livePrice || closes[closes.length - 1];
    const alerts = detectProximity(currentPrice, emaResults, closes, 0.15);
    setProximityAlerts(alerts);

    // Cross event handling
    const crossAlert = alerts.find((a) => a.isCross);
    if (crossAlert && crossAlert.crossType) {
      setCrossBanner({ type: crossAlert.crossType, label: crossAlert.emaLabel });

      // Spawn particles
      const newParticles = generateParticles(
        chartContainerRef.current?.clientWidth ? chartContainerRef.current.clientWidth / 2 : 400,
        height / 2,
        crossAlert.crossType === "golden" ? "#22c55e" : "#ef4444"
      );
      setParticles(newParticles);

      // Auto-hide
      const timeout = setTimeout(() => {
        setCrossBanner(null);
        setParticles([]);
      }, 3000);
      return () => clearTimeout(timeout);
    }
  }, [chartData, livePrice, emaResults, height]);

  // ── Initialize lightweight-charts ──
  useEffect(() => {
    if (!chartContainerRef.current) return;
    if (chartInstanceRef.current) return;

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "rgba(0, 224, 198, 0.4)",
        fontSize: 10,
      },
      watermark: { visible: false },
      grid: {
        vertLines: { color: "rgba(0, 224, 198, 0.04)" },
        horzLines: { color: "rgba(0, 224, 198, 0.04)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(0, 224, 198, 0.25)",
          labelBackgroundColor: "#0a1628",
          width: 1,
        },
        horzLine: {
          color: "rgba(0, 224, 198, 0.25)",
          labelBackgroundColor: "#0a1628",
          width: 1,
        },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "rgba(0, 224, 198, 0.08)",
      },
      rightPriceScale: {
        borderColor: "rgba(0, 224, 198, 0.08)",
      },
    });

    // Candlestick series with neon-ish colors
    const candleSeries = chart.addCandlestickSeries({
      upColor: P.green,
      downColor: P.red,
      borderVisible: false,
      wickUpColor: "var(--accent-positive-60)",
      wickDownColor: "var(--accent-negative-60)",
    });

    // Volume
    const volumeSeries = chart.addHistogramSeries({
      color: "rgba(0,224,198,0.15)",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    // EMA lines
    const emaRefs: Record<number, ISeriesApi<"Line">> = {};
    for (const [periodStr, config] of Object.entries(EMA_CONFIG)) {
      const period = Number(periodStr);
      const series = chart.addLineSeries({
        color: config.color,
        lineWidth: config.width,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      emaRefs[period] = series;
    }

    // Crosshair handler
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData) {
        setOhlcLegend(null);
        return;
      }
      const candle = param.seriesData.get(candleSeries) as
        | { open: number; high: number; low: number; close: number }
        | undefined;
      if (candle) {
        setOhlcLegend({
          time: new Date(Number(param.time) * 1000).toLocaleDateString("tr-TR", {
            day: "2-digit",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          }),
          o: candle.open,
          h: candle.high,
          l: candle.low,
          c: candle.close,
        });
      }
    });

    // Resize
    const resizeObserver = new ResizeObserver(() => {
      try {
        chart.applyOptions({ width: container.clientWidth });
      } catch {}
    });
    resizeObserver.observe(container);

    chartInstanceRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    emaSeriesRefs.current = emaRefs;
    setChartReady(true);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartInstanceRef.current = null;
      setChartReady(false);
    };
  }, [height]);

  // ── Update chart data ──
  useEffect(() => {
    const chart = chartInstanceRef.current;
    const candleSeries = candleSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;

    if (!chart || !candleSeries || !volumeSeries || !chartData?.length) return;

    try {
      const candles = chartData.map((d) => ({
        time: (d.timestamp / 1000) as Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

      const volumes = chartData.map((d) => ({
        time: (d.timestamp / 1000) as Time,
        value: d.volume,
        color: d.close >= d.open ? "var(--accent-positive-20)" : "var(--accent-negative-20)",
      }));

      candleSeries.setData(candles);
      volumeSeries.setData(volumes);

      // Set EMA data
      for (const [periodStr, emaResult] of Object.entries(emaResults)) {
        const period = Number(periodStr);
        const series = emaSeriesRefs.current[period];
        if (!series) continue;

        const emaData = chartData
          .map((d, i) => {
            const val = emaResult.values[i];
            if (val === null) return null;
            return { time: (d.timestamp / 1000) as Time, value: val };
          })
          .filter(Boolean) as { time: Time; value: number }[];

        series.setData(emaData);
      }

      chart.timeScale().fitContent();
    } catch (err) {
      console.error("NeonChart data update error:", err);
    }
  }, [chartData, emaResults, chartReady]);

  // ── Derived values ──
  const displayPrice = livePrice || priceInfo?.price || 0;
  const isXAU = symbol.toUpperCase().includes("XAU");
  const proximityPeriods = new Set(proximityAlerts.map((a) => a.emaPeriod));
  const hasData = Boolean(chartData && chartData.length > 0);

  // ═══════════════════════════════════════════════════════════
  //  RENDER
  // ═══════════════════════════════════════════════════════════
  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartContent}>
        {/* ── Header ── */}
        <div className={styles.header}>
          <div className={styles.symbolGroup}>
            <div
              className={`${styles.symbolIcon} ${
                isXAU ? styles.symbolIconXAUUSD : styles.symbolIconNASDAQ
              }`}
            >
              {isXAU ? (
                <Zap className="w-6 h-6 text-amber-400" />
              ) : (
                <Activity className="w-6 h-6 text-blue-400" />
              )}
            </div>
            <div>
              <div className={styles.symbolName}>{symbolLabel}</div>
              <div className={styles.priceDisplay}>
                <span className={styles.currentPrice}>
                  {displayPrice.toLocaleString("tr-TR", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
                {priceInfo && (
                  <span
                    className={`${styles.priceChange} ${
                      priceInfo.change >= 0 ? styles.priceUp : styles.priceDown
                    }`}
                  >
                    {priceInfo.change >= 0 ? "+" : ""}
                    {priceInfo.changePct.toFixed(2)}%
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Timeframe selector */}
          <div className={styles.timeframeSelector}>
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                className={`${styles.tfButton} ${timeframe === tf ? styles.tfButtonActive : ""}`}
                onClick={() => setTimeframe(tf)}
              >
                {tf}
              </button>
            ))}
            <button
              onClick={() => refetch()}
              className={styles.tfButton}
              title="Yenile"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* ── OHLC Legend Bar ── */}
        <div className={styles.ohlcBar}>
          {ohlcLegend ? (
            <>
              <span style={{ color: "#64748b" }}>{ohlcLegend.time}</span>
              <span>
                O: <span className={styles.ohlcValue}>{ohlcLegend.o.toFixed(2)}</span>
              </span>
              <span>
                H:{" "}
                <span className={styles.ohlcValue} style={{ color: "#22c55e" }}>
                  {ohlcLegend.h.toFixed(2)}
                </span>
              </span>
              <span>
                L:{" "}
                <span className={styles.ohlcValue} style={{ color: "#ef4444" }}>
                  {ohlcLegend.l.toFixed(2)}
                </span>
              </span>
              <span>
                C: <span className={styles.ohlcValue}>{ohlcLegend.c.toFixed(2)}</span>
              </span>
            </>
          ) : (
            <span style={{ color: "#475569", fontSize: "0.7rem" }}>
              Crosshair ile mumların üzerinde gezinin
            </span>
          )}
        </div>

        {/* ── Chart Area ── */}
        <div className={styles.chartArea}>
          <div className={styles.chartWrapper} style={{ height }}>
            <div ref={chartContainerRef} style={{ height: "100%", width: "100%" }} />

            {/* Loading overlay - only show when no data at all */}
            {isLoading && !hasData && (
              <div className={styles.loadingOverlay}>
                <div className={styles.loadingSpinner}>
                  <div className={styles.neonSpinner} />
                  <span style={{ color: "#64748b", fontSize: "0.8rem" }}>
                    Veri yükleniyor...
                  </span>
                </div>
              </div>
            )}

            {/* No data state */}
            {!isLoading && !hasData && (
              <div className={styles.loadingOverlay}>
                <div className={styles.loadingSpinner}>
                  <Activity className="w-8 h-8 text-slate-600" />
                  <span style={{ color: "#64748b", fontSize: "0.8rem" }}>
                    Bu zaman diliminde veri bulunamadı
                  </span>
                </div>
              </div>
            )}

            {/* ── Proximity Alert Banner ── */}
            <AnimatePresence>
              {proximityAlerts.length > 0 && !proximityAlerts[0].isCross && (
                <motion.div
                  key="proximity-alert"
                  className={styles.proximityBanner}
                  initial={{ opacity: 0, y: -20, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -20, scale: 0.9 }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                >
                  <AlertTriangle className="w-4 h-4" />
                  <span>
                    {proximityAlerts[0].emaLabel} Yakınlaşması! (
                    {proximityAlerts[0].distancePercent.toFixed(3)}%)
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Cross Banner ── */}
            <AnimatePresence>
              {crossBanner && (
                <motion.div
                  key="cross-banner"
                  className={`${styles.proximityBanner} ${
                    crossBanner.type === "golden" ? styles.crossBanner : styles.crossBannerDeath
                  }`}
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  transition={{ type: "spring", stiffness: 400, damping: 20 }}
                >
                  {crossBanner.type === "golden" ? (
                    <TrendingUp className="w-5 h-5" />
                  ) : (
                    <TrendingDown className="w-5 h-5" />
                  )}
                  <span style={{ fontSize: "0.9rem", fontWeight: 700 }}>
                    {crossBanner.type === "golden" ? "Golden Cross" : "Death Cross"} —{" "}
                    {crossBanner.label}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Particles ── */}
            {particles.map((p) => (
              <div
                key={p.id}
                className={styles.particle}
                style={
                  {
                    left: p.x,
                    top: p.y,
                    background: p.color,
                    boxShadow: `0 0 6px ${p.color}`,
                    "--dx": `${p.dx}px`,
                    "--dy": `${p.dy}px`,
                  } as React.CSSProperties
                }
              />
            ))}
          </div>
        </div>

        {/* ── Stats Bar ── */}
        {priceInfo && (
          <div className={styles.statsBar}>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>24h Yüksek</div>
              <div className={styles.statValue} style={{ color: "#22c55e" }}>
                {priceInfo.high24.toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>24h Düşük</div>
              <div className={styles.statValue} style={{ color: "#ef4444" }}>
                {priceInfo.low24.toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className={styles.statCard}>
              <div className={styles.statLabel}>Hacim</div>
              <div className={styles.statValue}>
                {priceInfo.volume > 1_000_000
                  ? `${(priceInfo.volume / 1_000_000).toFixed(1)}M`
                  : priceInfo.volume > 1_000
                  ? `${(priceInfo.volume / 1_000).toFixed(1)}K`
                  : priceInfo.volume.toFixed(0)}
              </div>
            </div>
            {/* EMA proximity indicator cards */}
            {[20, 50, 200].map((period) => {
              const val = latestValues[period];
              const isProx = proximityPeriods.has(period);
              const config = EMA_CONFIG[period as keyof typeof EMA_CONFIG];
              return (
                <div
                  key={period}
                  className={styles.statCard}
                  style={
                    isProx
                      ? {
                          borderColor: config.color,
                          boxShadow: `0 0 12px ${config.glowColor}`,
                        }
                      : {}
                  }
                >
                  <div className={styles.statLabel} style={{ color: config.color }}>
                    {config.label}
                  </div>
                  <div className={styles.statValue}>
                    {val !== null && val !== undefined
                      ? val.toLocaleString("tr-TR", { minimumFractionDigits: 2 })
                      : "—"}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── EMA Legend ── */}
        <div className={styles.emaLegend}>
          {([20, 50, 200] as const).map((period) => {
            const config = EMA_CONFIG[period];
            const val = latestValues[period];
            const isProx = proximityPeriods.has(period);
            return (
              <div key={period} className={styles.emaLegendItem}>
                <div
                  className={`${styles.emaLegendDot} ${
                    period === 20
                      ? styles.dot20
                      : period === 50
                      ? styles.dot50
                      : styles.dot200
                  } ${isProx ? styles.emaBadgeProximity : ""}`}
                  style={
                    isProx
                      ? {
                          boxShadow: `0 0 10px ${config.color}, 0 0 20px ${config.glowColor}`,
                        }
                      : {}
                  }
                />
                <span>{config.label}</span>
                {val !== null && val !== undefined && (
                  <span className={styles.emaLegendValue}>
                    {val.toLocaleString("tr-TR", { minimumFractionDigits: 2 })}
                  </span>
                )}
                {isProx && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className={styles.emaProximityIcon}
                    style={{ color: "#ef4444", fontSize: "12px" }}
                  >
                    ⚠️
                  </motion.span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
