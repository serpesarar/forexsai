"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  ColorType,
  createChart,
  CrosshairMode,
  IChartApi,
  ISeriesApi,
  Time,
  SeriesMarker,
} from "lightweight-charts";
import { HelpCircle, Maximize2, Minimize2, RefreshCw, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetcher } from "../../lib/api";
import type { OrderBlockDetectResponse } from "../../lib/api/orderBlocks";
import styles from "./ob-chart.module.css";

// ─── CONFIG ──────────────────────────────────────────────────────────

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US OIL" },
];

const TIMEFRAMES = ["5m", "15m", "1h", "4h"] as const;
type TF = (typeof TIMEFRAMES)[number];

const BULL_HIGHLIGHT = "#facc15";
const OB_BULL_COLOR = "rgba(250, 204, 21, 0.16)";
const OB_BULL_BORDER = "rgba(250, 204, 21, 0.64)";
const OB_BEAR_COLOR = "rgba(239, 83, 80, 0.18)";
const OB_BEAR_BORDER = "rgba(239, 83, 80, 0.6)";
const FVG_BULL_COLOR = "rgba(250, 204, 21, 0.1)";
const FVG_BEAR_COLOR = "rgba(239, 83, 80, 0.08)";
const SR_SUPPORT_COLOR = BULL_HIGHLIGHT;
const SR_RESISTANCE_COLOR = "#ef5350";

interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ─── DATA FETCHING ───────────────────────────────────────────────────

async function fetchOHLCV(symbol: string, timeframe: string): Promise<CandleData[]> {
  const data = await fetcher<{ data?: any[] }>(
    `/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=300`,
    { cache: "no-store" }
  );
  const raw: any[] = data.data || [];
  return raw.map((d) => ({
    time: Math.floor(d.timestamp / 1000),
    open: d.open,
    high: d.high,
    low: d.low,
    close: d.close,
    volume: d.volume || 0,
  }));
}

// ─── HELPERS ─────────────────────────────────────────────────────────

function throttle<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  let lastCall = 0;
  return ((...args: any[]) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      fn(...args);
    }
  }) as T;
}

// ─── COMPONENT ───────────────────────────────────────────────────────

export default function OrderBlockChartPanel() {
  const [symbol, setSymbol] = useState(SYMBOLS[0].key);
  const [timeframe, setTimeframe] = useState<TF>("5m");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showGuide, setShowGuide] = useState(true);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const priceLinesRef = useRef<any[]>([]);
  const detectPayload = useMemo(
    () => ({
      symbol,
      timeframe,
      limit: 300,
      config: {
        fractal_period: 2,
        min_displacement_atr: 1.0,
        min_score: 50,
        zone_type: "wick" as const,
        max_tests: 2,
      },
    }),
    [symbol, timeframe]
  );

  const toggleFullscreen = useCallback(() => {
    if (!wrapperRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else {
      wrapperRef.current.requestFullscreen().catch(() => {});
    }
  }, []);

  useEffect(() => {
    const onChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);
  const [chartSize, setChartSize] = useState({ width: 0, height: 0 });
  const [overlayVersion, setOverlayVersion] = useState(0);

  // ── OHLCV data
  const {
    data: candles,
    isLoading: candlesLoading,
  } = useQuery({
    queryKey: ["ob-chart-ohlcv", symbol, timeframe],
    queryFn: () => fetchOHLCV(symbol, timeframe),
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 0,
  });

  // ── Order block detect data
  const { data: obData, isLoading: obLoading } = useQuery<OrderBlockDetectResponse>({
    queryKey: ["ob-chart-detect", detectPayload],
    queryFn: () =>
      fetcher<OrderBlockDetectResponse>("/api/order-blocks/detect", {
        method: "POST",
        body: JSON.stringify(detectPayload),
        cache: "no-store",
      }),
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    staleTime: 0,
  });

  // ── Chart init
  useEffect(() => {
    if (!chartContainerRef.current) return;
    const container = chartContainerRef.current;

    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "#0a0e17" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(42,46,57,0.3)" },
        horzLines: { color: "rgba(42,46,57,0.3)" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      width: container.clientWidth,
      height: container.clientHeight || 500,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: "rgba(42,46,57,0.6)",
      },
      rightPriceScale: {
        borderColor: "rgba(42,46,57,0.6)",
      },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: true,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      borderUpColor: "#26a69a",
      borderDownColor: "#ef5350",
    });

    chartRef.current = chart;
    candleSeriesRef.current = series;

    const handleResize = throttle(() => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 500;
      chart.applyOptions({ width: w, height: h });
      setChartSize({ width: w, height: h });
      setOverlayVersion((v) => v + 1);
    }, 100);

    const observer = new ResizeObserver(handleResize);
    observer.observe(container);
    handleResize();

    const onRange = () => setOverlayVersion((v) => v + 1);
    chart.timeScale().subscribeVisibleLogicalRangeChange(onRange);

    return () => {
      observer.disconnect();
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(onRange);
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
    };
  }, []);

  // ── Update candle data + markers
  useEffect(() => {
    if (!candleSeriesRef.current || !candles?.length) return;

    const chartData = candles.map((c) => ({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeriesRef.current.setData(chartData);

    // BOS/CHoCH markers
    const markers: SeriesMarker<Time>[] = [];

    if (obData?.choch_list) {
      for (const ch of obData.choch_list as any[]) {
        const idx = ch.index;
        if (idx >= 0 && idx < candles.length) {
          const isBullish = ch.type === "bullish";
          markers.push({
            time: candles[idx].time as Time,
            position: isBullish ? "belowBar" : "aboveBar",
            color: isBullish ? BULL_HIGHLIGHT : "#ef5350",
            shape: isBullish ? "arrowUp" : "arrowDown",
            text: `CHoCH`,
          });
        }
      }
    }

    if (obData?.bos_list) {
      for (const b of obData.bos_list as any[]) {
        const idx = b.index;
        if (idx >= 0 && idx < candles.length) {
          const isBullish = b.type === "bullish";
          markers.push({
            time: candles[idx].time as Time,
            position: isBullish ? "belowBar" : "aboveBar",
            color: isBullish ? BULL_HIGHLIGHT : "#ff8a65",
            shape: "circle",
            text: `BOS`,
          });
        }
      }
    }

    // Sort by time (required by lightweight-charts)
    markers.sort((a, b) => (a.time as number) - (b.time as number));
    candleSeriesRef.current.setMarkers(markers);

    // S/R price lines — remove old ones first
    for (const pl of priceLinesRef.current) {
      try { candleSeriesRef.current.removePriceLine(pl); } catch { /* ignore */ }
    }
    priceLinesRef.current = [];

    if (obData?.support_resistance) {
      const sr = obData.support_resistance as any;
      const levels = sr?.all_levels || [];
      for (const level of levels) {
        try {
          const pl = candleSeriesRef.current.createPriceLine({
            price: level.price,
            color: level.type === "resistance" ? SR_RESISTANCE_COLOR : SR_SUPPORT_COLOR,
            lineWidth: 1,
            lineStyle: 2, // dashed
            axisLabelVisible: true,
            title: level.name || "",
          });
          priceLinesRef.current.push(pl);
        } catch { /* ignore */ }
      }
    }

    chartRef.current?.timeScale().fitContent();
    setOverlayVersion((v) => v + 1);
  }, [candles, obData]);

  // ── Canvas overlay for OB zones and FVG zones
  const drawOverlay = useCallback(() => {
    const chart = chartRef.current;
    const series = candleSeriesRef.current;
    const canvas = canvasRef.current;
    if (!chart || !series || !canvas || !candles?.length) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = chartSize.width * dpr;
    canvas.height = chartSize.height * dpr;
    canvas.style.width = `${chartSize.width}px`;
    canvas.style.height = `${chartSize.height}px`;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, chartSize.width, chartSize.height);

    const timeScale = chart.timeScale();

    // Helper: time → x pixel
    const timeToX = (time: number): number | null => {
      const coord = timeScale.timeToCoordinate(time as Time);
      return coord !== null ? coord : null;
    };

    // Helper: price → y pixel
    const priceToY = (price: number): number | null => {
      const coord = series.priceToCoordinate(price);
      return coord !== null ? coord : null;
    };

    // Get visible time range for clipping
    const visibleRange = timeScale.getVisibleLogicalRange();
    if (!visibleRange) return;

    const firstIdx = Math.max(0, Math.floor(visibleRange.from));
    const lastIdx = Math.min(candles.length - 1, Math.ceil(visibleRange.to));
    if (firstIdx >= candles.length || lastIdx < 0) return;

    const leftTime = candles[Math.max(0, firstIdx)]?.time;
    const rightTime = candles[Math.min(candles.length - 1, lastIdx)]?.time;
    if (!leftTime || !rightTime) return;

    const xLeft = timeToX(leftTime);
    const xRight = timeToX(rightTime);
    if (xLeft === null || xRight === null) return;

    // ── Draw OB zones
    if (obData?.order_blocks) {
      for (const ob of obData.order_blocks as any[]) {
        const zoneLow = ob.zone_low;
        const zoneHigh = ob.zone_high;
        const isBullish = ob.type === "bullish";
        if (!zoneLow || !zoneHigh) continue;

        const yLow = priceToY(zoneLow);
        const yHigh = priceToY(zoneHigh);
        if (yLow === null || yHigh === null) continue;

        const y = Math.min(yLow, yHigh);
        const h = Math.abs(yLow - yHigh);
        if (h < 1) continue;

        // OB rectangle spans from OB index to right edge
        const obIdx = ob.index || 0;
        let obX = xLeft;
        if (obIdx >= 0 && obIdx < candles.length) {
          const x = timeToX(candles[obIdx].time);
          if (x !== null) obX = x;
        }

        // Fill
        ctx.fillStyle = isBullish ? OB_BULL_COLOR : OB_BEAR_COLOR;
        ctx.fillRect(obX, y, chartSize.width - obX, h);

        // Border
        ctx.strokeStyle = isBullish ? OB_BULL_BORDER : OB_BEAR_BORDER;
        ctx.lineWidth = 1;
        ctx.setLineDash([]);
        ctx.strokeRect(obX, y, chartSize.width - obX, h);

        // Label
        ctx.font = "bold 9px monospace";
        ctx.fillStyle = isBullish ? BULL_HIGHLIGHT : "#ef5350";
        const label = `${isBullish ? "Bull" : "Bear"} OB (${ob.score || 0})`;
        ctx.fillText(label, obX + 4, y + 10);
      }
    }

    // ── Draw FVG zones
    if (obData?.fvg_list) {
      for (const fvg of obData.fvg_list as any[]) {
        if (fvg.filled) continue;
        const fvgHigh = fvg.high;
        const fvgLow = fvg.low;
        const isBullish = fvg.direction === "bullish";
        if (!fvgHigh || !fvgLow) continue;

        const yLow = priceToY(fvgLow);
        const yHigh = priceToY(fvgHigh);
        if (yLow === null || yHigh === null) continue;

        const y = Math.min(yLow, yHigh);
        const h = Math.abs(yLow - yHigh);
        if (h < 1) continue;

        const fvgIdx = fvg.index || 0;
        let fvgX = xLeft;
        if (fvgIdx >= 0 && fvgIdx < candles.length) {
          const x = timeToX(candles[fvgIdx].time);
          if (x !== null) fvgX = x;
        }

        // Semi-transparent fill with diagonal hatching
        ctx.fillStyle = isBullish ? FVG_BULL_COLOR : FVG_BEAR_COLOR;
        ctx.fillRect(fvgX, y, chartSize.width - fvgX, h);

        // Dashed border
        ctx.strokeStyle = isBullish ? "rgba(250,204,21,0.36)" : "rgba(239,83,80,0.3)";
        ctx.lineWidth = 0.5;
        ctx.setLineDash([3, 3]);
        ctx.strokeRect(fvgX, y, chartSize.width - fvgX, h);
        ctx.setLineDash([]);

        // FVG label
        ctx.font = "8px monospace";
        ctx.fillStyle = isBullish ? "rgba(250,204,21,0.72)" : "rgba(239,83,80,0.5)";
        ctx.fillText("FVG", fvgX + 3, y + 9);
      }
    }
  }, [candles, obData, chartSize, overlayVersion]);

  useEffect(() => {
    drawOverlay();
  }, [drawOverlay, overlayVersion]);

  const isLoading = candlesLoading || obLoading;
  const signal = obData?.combined_signal;
  const trend = obData?.trend || "ranging";

  const obCount = obData?.order_blocks?.length || 0;
  const chochCount = (obData?.choch_list as any[])?.length || 0;
  const bosCount = (obData?.bos_list as any[])?.length || 0;
  const fvgCount = (obData?.fvg_list as any[])?.filter((f: any) => !f.filled)?.length || 0;

  return (
    <div ref={wrapperRef} className={styles.wrapper} style={isFullscreen ? { background: '#0a0e17' } : undefined}>
      {/* Toolbar */}
      <div className={styles.toolbar}>
        <button
          className={styles.helpBtn}
          onClick={() => setShowGuide((prev) => !prev)}
          type="button"
        >
          <HelpCircle size={14} />
        </button>
        {SYMBOLS.map((s) => (
          <button
            key={s.key}
            className={`${styles.symbolBtn} ${symbol === s.key ? styles.symbolBtnActive : ""}`}
            onClick={() => setSymbol(s.key)}
          >
            {s.label}
          </button>
        ))}
        <div className={styles.separator} />
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf}
            className={`${styles.tfBtn} ${timeframe === tf ? styles.tfBtnActive : ""}`}
            onClick={() => setTimeframe(tf)}
          >
            {tf}
          </button>
        ))}
        <div className={styles.separator} />
        <div className={styles.legendRow}>
          <span><span className={styles.legendDot} style={{ background: BULL_HIGHLIGHT }} />Bull OB</span>
          <span><span className={styles.legendDot} style={{ background: "#ef5350" }} />Bear OB</span>
          <span><span className={styles.legendDot} style={{ background: BULL_HIGHLIGHT }} />BOS</span>
          <span><span className={styles.legendDot} style={{ background: "#ff8a65" }} />CHoCH</span>
        </div>
        <div className={styles.autoRefresh}>1m auto</div>
        <button className={styles.fullscreenBtn} onClick={toggleFullscreen}>
          {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
        </button>
      </div>

      <div className={styles.contentRow}>
        {showGuide ? (
          <div className={styles.helpPanel}>
            <div className={styles.helpPanelHeader}>
              <div className={styles.helpPanelTitle}>
                <HelpCircle size={14} />
                <span>SMC Guide</span>
              </div>
              <button className={styles.helpCloseBtn} onClick={() => setShowGuide(false)} type="button">
                <X size={14} />
              </button>
            </div>
            <div className={styles.helpBlock}>
              <div className={styles.helpLabelBull}>Bull OB</div>
              <p className={styles.helpText}>Kurumsal alım bölgesi. Fiyat banda geldiğinde direkt alım yerine önce tutunma, bullish mum veya yukarı yönlü teyit bekle.</p>
            </div>
            <div className={styles.helpBlock}>
              <div className={styles.helpLabelBear}>Bear OB</div>
              <p className={styles.helpText}>Kurumsal satış bölgesi. Fiyat banda dokunduğunda rejection, zayıflama veya aşağı yönlü teyit görmeden satışa atlama.</p>
            </div>
            <div className={styles.helpBlock}>
              <div className={styles.helpLabelBos}>BOS</div>
              <p className={styles.helpText}>Break of Structure. Trend devamının teyidi sayılır. Bölge temasından sonra işlem yönünde BOS gelirse senaryo güçlenir.</p>
            </div>
            <div className={styles.helpBlock}>
              <div className={styles.helpLabelChoch}>CHoCH</div>
              <p className={styles.helpText}>Change of Character. İlk dönüş sinyali olabilir. Tek başına giriş yerine CHoCH sonrası ikinci teyit veya BOS beklemek daha güvenlidir.</p>
            </div>
            <div className={styles.helpFooter}>Temas tek başına giriş değildir; fiyatın bölgede nasıl davrandığını beklemek daha güvenli senaryodur.</div>
          </div>
        ) : null}

        <div className={styles.chartContainer} ref={chartContainerRef}>
          {isLoading && (
            <div className={styles.loading}>
              <RefreshCw size={16} style={{ marginRight: 8, animation: "spin 1s linear infinite" }} />
              Loading chart data...
            </div>
          )}

          {/* Canvas overlay for zones */}
          <canvas
            ref={canvasRef}
            className={styles.overlay}
            style={{ width: chartSize.width, height: chartSize.height }}
          />

          {/* Signal badge */}
          {signal?.action && signal.action !== "NEUTRAL" && (
            <div
              className={`${styles.signalBadge} ${
                signal.action === "BUY" ? styles.signalBuy : styles.signalSell
              }`}
            >
              {signal.action} — {Math.round((signal.confidence || 0) * 100)}%
            </div>
          )}

          {/* Trend tag */}
          <div
            className={`${styles.trendTag} ${
              trend === "bullish"
                ? styles.trendBullish
                : trend === "bearish"
                ? styles.trendBearish
                : styles.trendRanging
            }`}
          >
            {trend}
          </div>
        </div>
      </div>

      <div className={styles.statsBar}>
        <div className={styles.statItem}>
          OBs: <span className={styles.statValue}>{obCount}</span>
        </div>
        <div className={styles.statItem}>
          CHoCH: <span className={styles.statValue}>{chochCount}</span>
        </div>
        <div className={styles.statItem}>
          BOS: <span className={styles.statValue}>{bosCount}</span>
        </div>
        <div className={styles.statItem}>
          FVG: <span className={styles.statValue}>{fvgCount}</span>
        </div>
        {signal?.reasons?.length ? (
          <div className={styles.statItem} style={{ marginLeft: "auto" }}>
            {signal.reasons.slice(0, 3).join(" · ")}
          </div>
        ) : null}
      </div>
    </div>
  );
}
