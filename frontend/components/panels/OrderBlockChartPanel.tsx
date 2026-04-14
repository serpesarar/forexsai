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

// ── Professional SMC Color Palette ──
// Order Blocks → Gold/Yellow (distinctive, never confused with TP/SL)
const OB_BULL_COLOR  = "rgba(234, 179, 8, 0.22)";   // golden fill
const OB_BULL_BORDER = "rgba(234, 179, 8, 0.92)";   // #eab308
const OB_BEAR_COLOR  = "rgba(245, 158, 11, 0.20)";  // amber fill
const OB_BEAR_BORDER = "rgba(245, 158, 11, 0.90)";  // #f59e0b

// FVG → blue-teal (subtle, doesn't compete with OB or TP/SL)
const FVG_BULL_COLOR  = "rgba(56, 189, 248, 0.10)";  // sky-300
const FVG_BULL_BORDER = "rgba(56, 189, 248, 0.45)";
const FVG_BEAR_COLOR  = "rgba(167, 139, 250, 0.10)"; // violet-400
const FVG_BEAR_BORDER = "rgba(167, 139, 250, 0.40)";

// TP levels → 3 shades of green (bright → darker)
const TP1_COLOR = "#22c55e";   // green-500 — closest target
const TP2_COLOR = "#16a34a";   // green-600
const TP3_COLOR = "#15803d";   // green-700 — extension

// SL → bold red
const SL_COLOR       = "#ef4444";   // red-500
const SL_BG_COLOR    = "rgba(239, 68, 68, 0.10)";

// Entry zone → neutral white
const ENTRY_FILL  = "rgba(248, 250, 252, 0.06)";
const ENTRY_BORDER = "rgba(248, 250, 252, 0.35)";

// Swing lines → blue (unchanged)
const SWING_LINE_COLOR  = "rgba(59, 130, 246, 0.7)";
const SWING_LABEL_COLOR = "#3b82f6";

// Structure markers
const BOS_COLOR   = "#facc15";
const CHOCH_COLOR = "#f97316";

// S/R price lines
const SR_SUPPORT_COLOR    = "rgba(34, 197, 94, 0.6)";
const SR_RESISTANCE_COLOR = "rgba(239, 68, 68, 0.55)";

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
            color: CHOCH_COLOR,
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
            color: BOS_COLOR,
            shape: "circle",
            text: `BOS`,
          });
        }
      }
    }

    // Sort by time (required by lightweight-charts)
    markers.sort((a, b) => (a.time as number) - (b.time as number));
    candleSeriesRef.current.setMarkers(markers);

    // S/R price lines — remove old ones first, then add clean limited set
    for (const pl of priceLinesRef.current) {
      try { candleSeriesRef.current.removePriceLine(pl); } catch { /* ignore */ }
    }
    priceLinesRef.current = [];

    if (obData?.support_resistance) {
      const sr = obData.support_resistance as any;
      const levels = (sr?.all_levels || []) as any[];
      // Only show top 2 support + 2 resistance (nearest) to avoid clutter
      const supports = levels.filter((l: any) => l.type === "support").slice(0, 2);
      const resistances = levels.filter((l: any) => l.type === "resistance").slice(-2);
      const filteredLevels = [...supports, ...resistances];
      for (const level of filteredLevels) {
        try {
          const isRes = level.type === "resistance";
          const touches = level.touch_count || 1;
          const pl = candleSeriesRef.current.createPriceLine({
            price: level.price,
            color: isRes ? SR_RESISTANCE_COLOR : SR_SUPPORT_COLOR,
            lineWidth: touches >= 2 ? 2 : 1,
            lineStyle: 2, // dashed
            axisLabelVisible: true,
            title: `${level.name || ""}${touches >= 2 ? " \u2022" + touches : ""}`,
          });
          priceLinesRef.current.push(pl);
        } catch { /* ignore */ }
      }
    }

    chartRef.current?.timeScale().fitContent();
    setOverlayVersion((v) => v + 1);
  }, [candles, obData]);

  // ── Canvas overlay: OB zones, FVG zones, swing lines, TP/SL projection, BOS/ChoCH lines
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

    const timeToX = (time: number): number | null => {
      const coord = timeScale.timeToCoordinate(time as Time);
      return coord !== null ? coord : null;
    };
    const priceToY = (price: number): number | null => {
      const coord = series.priceToCoordinate(price);
      return coord !== null ? coord : null;
    };

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
    const chartW = chartSize.width;

    // ── 1. Draw Swing High/Low horizontal lines (blue)
    const swingPoints = (obData as any)?.swing_points as any[] | undefined;
    if (swingPoints?.length) {
      // Find most recent significant swing high and low
      const swingHighs = swingPoints.filter((s: any) => s.type === "high");
      const swingLows = swingPoints.filter((s: any) => s.type === "low");

      const drawSwingLine = (sw: any, label: string) => {
        const yPos = priceToY(sw.price);
        if (yPos === null) return;

        let startX = xLeft;
        if (sw.index >= 0 && sw.index < candles.length) {
          const x = timeToX(candles[sw.index].time);
          if (x !== null) startX = x;
        }

        // Dashed blue line
        ctx.strokeStyle = SWING_LINE_COLOR;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(startX, yPos);
        ctx.lineTo(chartW, yPos);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label with background
        ctx.font = "bold 9px Inter, sans-serif";
        const text = `${label} ${sw.price.toFixed(1)}`;
        const tm = ctx.measureText(text);
        const lx = chartW - tm.width - 8;
        const ly = yPos - 4;
        ctx.fillStyle = "rgba(59, 130, 246, 0.15)";
        ctx.fillRect(lx - 3, ly - 9, tm.width + 6, 12);
        ctx.fillStyle = SWING_LABEL_COLOR;
        ctx.fillText(text, lx, ly);
      };

      // Draw last 2 swing highs and lows
      for (const sh of swingHighs.slice(-2)) drawSwingLine(sh, "SH");
      for (const sl of swingLows.slice(-2)) drawSwingLine(sl, "SL");
    }

    // ── 2. Draw TP/SL projection — individual numbered lines (clean & readable)
    const projection = (obData as any)?.projection as any | undefined;
    if (projection) {
      const isBullish = projection.direction === "bullish";

      // Helper: draw a single horizontal price line with a right-side pill label
      const drawPriceLine = (
        price: number,
        color: string,
        lineWidth: number,
        dashed: boolean,
        label: string,
        bgAlpha = 0.12,
      ) => {
        const y = priceToY(price);
        if (y === null) return;

        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.setLineDash(dashed ? [6, 3] : []);
        ctx.beginPath();
        ctx.moveTo(xLeft, y);
        ctx.lineTo(chartW, y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Right-side pill
        ctx.font = `bold 10px Inter, sans-serif`;
        const tm = ctx.measureText(label);
        const px = chartW - tm.width - 14;
        const py = y - 7;
        ctx.fillStyle = color.replace(/[\d.]+\)$/, `${bgAlpha})`).replace(/^#/, `rgba(${parseInt(color.slice(1,3),16)},${parseInt(color.slice(3,5),16)},${parseInt(color.slice(5,7),16)},${bgAlpha})`);
        // Use solid bg instead of parsing hex
        ctx.fillStyle = `rgba(10,14,23,0.75)`;
        ctx.fillRect(px - 4, py, tm.width + 8, 14);
        ctx.fillStyle = color;
        ctx.fillText(label, px, py + 10);
      };

      // ── Entry zone (subtle white box) ─────────────────────────────────────
      const ezLowY  = priceToY(projection.entry_zone_low);
      const ezHighY = priceToY(projection.entry_zone_high);
      if (ezLowY !== null && ezHighY !== null) {
        const ezTop = Math.min(ezLowY, ezHighY);
        const ezH   = Math.max(2, Math.abs(ezHighY - ezLowY));
        ctx.fillStyle = ENTRY_FILL;
        ctx.fillRect(xLeft, ezTop, chartW - xLeft, ezH);
        ctx.strokeStyle = ENTRY_BORDER;
        ctx.lineWidth = 0.8;
        ctx.setLineDash([3, 3]);
        ctx.strokeRect(xLeft, ezTop, chartW - xLeft, ezH);
        ctx.setLineDash([]);
        ctx.font = "bold 9px Inter, sans-serif";
        ctx.fillStyle = "rgba(248,250,252,0.55)";
        ctx.fillText("ENTRY", xLeft + 6, ezTop + 10);
      }

      // ── SL — thick red solid line ──────────────────────────────────────────
      const slY = priceToY(projection.stop_loss);
      if (slY !== null) {
        // Red fill below SL (danger zone)
        const slFillH = isBullish ? chartSize.height - slY : slY;
        if (slFillH > 0) {
          ctx.fillStyle = SL_BG_COLOR;
          ctx.fillRect(xLeft, isBullish ? slY : 0, chartW - xLeft, slFillH);
        }
        ctx.strokeStyle = SL_COLOR;
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(xLeft, slY);
        ctx.lineTo(chartW, slY);
        ctx.stroke();

        // Label pill
        const slLabel = `⊗ SL  ${projection.stop_loss.toFixed(1)}`;
        ctx.font = "bold 10px Inter, sans-serif";
        const slTm = ctx.measureText(slLabel);
        const slPx = chartW - slTm.width - 14;
        ctx.fillStyle = "rgba(10,14,23,0.80)";
        ctx.fillRect(slPx - 4, slY - 8, slTm.width + 8, 14);
        ctx.fillStyle = SL_COLOR;
        ctx.fillText(slLabel, slPx, slY + 3);
      }

      // ── TP1 — bright green solid ────────────────────────────────────────────
      const tp1Y = priceToY(projection.tp1);
      if (tp1Y !== null) {
        ctx.strokeStyle = TP1_COLOR;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(xLeft, tp1Y);
        ctx.lineTo(chartW, tp1Y);
        ctx.stroke();

        const tp1Label = `① TP1  ${projection.tp1.toFixed(1)}`;
        ctx.font = "bold 10px Inter, sans-serif";
        const t1m = ctx.measureText(tp1Label);
        const t1x = chartW - t1m.width - 14;
        ctx.fillStyle = "rgba(10,14,23,0.80)";
        ctx.fillRect(t1x - 4, tp1Y - 8, t1m.width + 8, 14);
        ctx.fillStyle = TP1_COLOR;
        ctx.fillText(tp1Label, t1x, tp1Y + 3);
      }

      // ── TP2 — medium green solid ────────────────────────────────────────────
      const tp2Y = priceToY(projection.tp2);
      if (tp2Y !== null) {
        ctx.strokeStyle = TP2_COLOR;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(xLeft, tp2Y);
        ctx.lineTo(chartW, tp2Y);
        ctx.stroke();

        const tp2Label = `② TP2  ${projection.tp2.toFixed(1)}`;
        ctx.font = "bold 10px Inter, sans-serif";
        const t2m = ctx.measureText(tp2Label);
        const t2x = chartW - t2m.width - 14;
        ctx.fillStyle = "rgba(10,14,23,0.80)";
        ctx.fillRect(t2x - 4, tp2Y - 8, t2m.width + 8, 14);
        ctx.fillStyle = TP2_COLOR;
        ctx.fillText(tp2Label, t2x, tp2Y + 3);
      }

      // ── TP3 — dark green dashed (Fibonacci extension) ──────────────────────
      const tp3Y = priceToY(projection.tp3);
      if (tp3Y !== null) {
        ctx.strokeStyle = TP3_COLOR;
        ctx.lineWidth = 1;
        ctx.setLineDash([8, 4]);
        ctx.beginPath();
        ctx.moveTo(xLeft, tp3Y);
        ctx.lineTo(chartW, tp3Y);
        ctx.stroke();
        ctx.setLineDash([]);

        const tp3Label = `③ TP3  ${projection.tp3.toFixed(1)}`;
        ctx.font = "bold 10px Inter, sans-serif";
        const t3m = ctx.measureText(tp3Label);
        const t3x = chartW - t3m.width - 14;
        ctx.fillStyle = "rgba(10,14,23,0.80)";
        ctx.fillRect(t3x - 4, tp3Y - 8, t3m.width + 8, 14);
        ctx.fillStyle = TP3_COLOR;
        ctx.fillText(tp3Label, t3x, tp3Y + 3);
      }

      // ── Swing range arrow (vertical, right edge) ───────────────────────────
      const swHighY = priceToY(projection.swing_high);
      const swLowY  = priceToY(projection.swing_low);
      if (swHighY !== null && swLowY !== null) {
        const arrowX = chartW - 8;
        const topY   = Math.min(swHighY, swLowY);
        const botY   = Math.max(swHighY, swLowY);
        const midY   = (topY + botY) / 2;

        ctx.strokeStyle = "rgba(250, 204, 21, 0.60)";
        ctx.lineWidth = 1;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(arrowX, topY + 5);
        ctx.lineTo(arrowX, botY - 5);
        ctx.stroke();

        ctx.fillStyle = "rgba(250, 204, 21, 0.80)";
        ctx.beginPath(); ctx.moveTo(arrowX, topY); ctx.lineTo(arrowX-3, topY+5); ctx.lineTo(arrowX+3, topY+5); ctx.fill();
        ctx.beginPath(); ctx.moveTo(arrowX, botY); ctx.lineTo(arrowX-3, botY-5); ctx.lineTo(arrowX+3, botY-5); ctx.fill();

        ctx.font = "bold 8px Inter, sans-serif";
        ctx.fillStyle = "rgba(250,204,21,0.85)";
        const rText = `${projection.swing_range.toFixed(0)}`;
        ctx.save();
        ctx.translate(arrowX - 4, midY);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(rText, -ctx.measureText(rText).width / 2, 0);
        ctx.restore();
      }
    }

    // ── 3. Draw OB zones — Gold/Yellow (distinct from green TP and red SL)
    if (obData?.order_blocks) {
      const obs = obData.order_blocks as any[];
      // Only show top 5 OBs to avoid clutter
      const visibleOBs = obs.slice(0, 5);
      visibleOBs.forEach((ob: any, obSeq: number) => {
        const zoneLow  = ob.zone_low;
        const zoneHigh = ob.zone_high;
        const isBullish = ob.type === "bullish";
        if (!zoneLow || !zoneHigh) return;

        const yLow  = priceToY(zoneLow);
        const yHigh = priceToY(zoneHigh);
        if (yLow === null || yHigh === null) return;

        const y = Math.min(yLow, yHigh);
        const h = Math.abs(yLow - yHigh);
        if (h < 1) return;

        const obIdx = ob.index || 0;
        let obX = xLeft;
        if (obIdx >= 0 && obIdx < candles.length) {
          const x = timeToX(candles[obIdx].time);
          if (x !== null) obX = x;
        }

        // Gold fill — horizontal gradient (brighter at origin, fades right)
        const fillColor = isBullish ? OB_BULL_COLOR : OB_BEAR_COLOR;
        const borderColor = isBullish ? OB_BULL_BORDER : OB_BEAR_BORDER;

        const grad = ctx.createLinearGradient(obX, y, chartW, y);
        // Both bull and bear use gold/amber shades — different opacity only
        if (isBullish) {
          grad.addColorStop(0, "rgba(234,179,8,0.30)");
          grad.addColorStop(0.6, "rgba(234,179,8,0.12)");
          grad.addColorStop(1, "rgba(234,179,8,0.04)");
        } else {
          grad.addColorStop(0, "rgba(245,158,11,0.28)");
          grad.addColorStop(0.6, "rgba(245,158,11,0.11)");
          grad.addColorStop(1, "rgba(245,158,11,0.03)");
        }
        ctx.fillStyle = grad;
        ctx.fillRect(obX, y, chartW - obX, h);

        // Left accent bar (4px solid gold)
        ctx.fillStyle = borderColor;
        ctx.fillRect(obX, y, 4, h);

        // Top + bottom border lines (solid, 1px)
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 1;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(obX + 4, y);
        ctx.lineTo(chartW, y);
        ctx.moveTo(obX + 4, y + h);
        ctx.lineTo(chartW, y + h);
        ctx.stroke();

        // Numbered label pill (①②③...) at left side
        const num = ["①","②","③","④","⑤"][obSeq] ?? `${obSeq+1}`;
        const status = ob.tested ? " ✓" : ob.mitigated ? " ✗" : "";
        const score  = ob.score != null ? ` ${ob.score}` : "";
        const label  = `${num} ${isBullish ? "Bull" : "Bear"} OB${score}${status}`;
        ctx.font = "bold 9.5px Inter, sans-serif";
        const lm = ctx.measureText(label);
        const pillX = obX + 8;
        const pillY = y + 3;

        ctx.fillStyle = "rgba(10,14,23,0.72)";
        ctx.fillRect(pillX - 2, pillY, lm.width + 6, 13);
        ctx.fillStyle = borderColor;
        ctx.fillText(label, pillX + 1, pillY + 10);

        // Price labels on right axis
        ctx.font = "8px Inter, sans-serif";
        ctx.fillStyle = borderColor;
        ctx.fillText(zoneHigh.toFixed(1), chartW - 52, y - 2);
        ctx.fillText(zoneLow.toFixed(1),  chartW - 52, y + h + 9);
      });
    }

    // ── 4. Draw FVG zones
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

        // Teal/violet fill for FVG (clearly distinct from gold OB and green/red TP/SL)
        const fvgFill   = isBullish ? FVG_BULL_COLOR : FVG_BEAR_COLOR;
        const fvgBorder = isBullish ? FVG_BULL_BORDER : FVG_BEAR_BORDER;

        ctx.fillStyle = fvgFill;
        ctx.fillRect(fvgX, y, chartW - fvgX, h);

        // Diagonal hatch for FVG texture
        ctx.strokeStyle = fvgBorder;
        ctx.lineWidth = 0.5;
        ctx.setLineDash([]);
        ctx.save();
        ctx.beginPath();
        ctx.rect(fvgX, y, chartW - fvgX, h);
        ctx.clip();
        const fvgStep = 8;
        for (let lx = fvgX - h; lx < chartW; lx += fvgStep) {
          ctx.beginPath();
          ctx.moveTo(lx, y + h);
          ctx.lineTo(lx + h, y);
          ctx.stroke();
        }
        ctx.restore();

        // Dashed border
        ctx.strokeStyle = fvgBorder;
        ctx.lineWidth = 0.8;
        ctx.setLineDash([3, 3]);
        ctx.strokeRect(fvgX, y, chartW - fvgX, h);
        ctx.setLineDash([]);

        // FVG label
        ctx.font = "bold 8px Inter, sans-serif";
        ctx.fillStyle = fvgBorder;
        ctx.fillText("FVG", fvgX + 4, y + 9);
      }
    }

    // ── 5. Draw BOS/ChoCH as horizontal dashed lines at the broken level
    if (obData?.bos_list) {
      for (const b of obData.bos_list as any[]) {
        const level = b.broken_level;
        if (!level) continue;
        const yPos = priceToY(level);
        if (yPos === null) continue;

        let startX = xLeft;
        if (b.index >= 0 && b.index < candles.length) {
          const x = timeToX(candles[b.index].time);
          if (x !== null) startX = Math.max(xLeft, x - 40);
        }

        ctx.strokeStyle = BOS_COLOR;
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(startX, yPos);
        ctx.lineTo(chartW, yPos);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label
        ctx.font = "bold 8px Inter, sans-serif";
        ctx.fillStyle = BOS_COLOR;
        ctx.fillText("BOS", startX + 3, yPos - 3);
      }
    }

    if (obData?.choch_list) {
      for (const ch of obData.choch_list as any[]) {
        const level = ch.broken_level;
        if (!level) continue;
        const yPos = priceToY(level);
        if (yPos === null) continue;

        let startX = xLeft;
        if (ch.index >= 0 && ch.index < candles.length) {
          const x = timeToX(candles[ch.index].time);
          if (x !== null) startX = Math.max(xLeft, x - 40);
        }

        ctx.strokeStyle = CHOCH_COLOR;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 2]);
        ctx.beginPath();
        ctx.moveTo(startX, yPos);
        ctx.lineTo(chartW, yPos);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.font = "bold 8px Inter, sans-serif";
        ctx.fillStyle = CHOCH_COLOR;
        ctx.fillText("CHoCH", startX + 3, yPos - 3);
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
          <span><span className={styles.legendDot} style={{ background: "#eab308" }} />Bull OB</span>
          <span><span className={styles.legendDot} style={{ background: "#f59e0b" }} />Bear OB</span>
          <span><span className={styles.legendDot} style={{ background: "#38bdf8" }} />FVG</span>
          <span><span className={styles.legendDot} style={{ background: BOS_COLOR }} />BOS</span>
          <span><span className={styles.legendDot} style={{ background: CHOCH_COLOR }} />CHoCH</span>
          <span><span className={styles.legendDot} style={{ background: "#3b82f6" }} />Swing</span>
          <span><span className={styles.legendDot} style={{ background: TP1_COLOR }} />TP①②③</span>
          <span><span className={styles.legendDot} style={{ background: SL_COLOR }} />SL</span>
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
              <div style={{ fontSize: 11, fontWeight: 700, color: '#eab308', marginBottom: 6 }}>Bull OB (Gold Zone)</div>
              <p className={styles.helpText}>Kurumsal alım bölgesi. Fiyat banda geldiğinde direkt alım yerine önce tutunma, bullish mum veya yukarı yönlü teyit bekle.</p>
            </div>
            <div className={styles.helpBlock}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#f59e0b', marginBottom: 6 }}>Bear OB (Amber Zone)</div>
              <p className={styles.helpText}>Kurumsal satış bölgesi. Fiyat banda dokunduğunda rejection, zayıflama veya aşağı yönlü teyit görmeden satışa atlama.</p>
            </div>
            <div className={styles.helpBlock}>
              <div className={styles.helpLabelBos}>BOS</div>
              <p className={styles.helpText}>Break of Structure. Trend devamının teyidi sayılır. Minimum ATR x 0.15 deplasman filtresi ile gürültü azaltıldı.</p>
            </div>
            <div className={styles.helpBlock}>
              <div className={styles.helpLabelChoch}>CHoCH</div>
              <p className={styles.helpText}>Change of Character. İlk dönüş sinyali. CHoCH sonrası ikinci teyit veya BOS beklemek daha güvenlidir.</p>
            </div>
            <div className={styles.helpBlock}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#3b82f6', marginBottom: 6 }}>Swing High/Low (Blue)</div>
              <p className={styles.helpText}>Fractal bazlı swing noktaları. Mavi kesikli çizgiler olarak gösterilir. Swing aralığı TP/SL hesaplamasının temelidir.</p>
            </div>
            <div className={styles.helpBlock}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#22c55e', marginBottom: 6 }}>① TP1 · ② TP2 · ③ TP3 (Green Lines)</div>
              <p className={styles.helpText}>Sembol bazlı Fibonacci projeksiyonları. NASDAQ: 1.618x–2.0x, Gold: 1.618x–2.618x. TP3 kesikli çizgidir (uzatma hedefi).</p>
            </div>
            <div className={styles.helpBlock}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#ef4444', marginBottom: 6 }}>⊗ SL (Red Line)</div>
              <p className={styles.helpText}>Sembol bazlı ATR marjini: NASDAQ 1.0×ATR, Gold 0.5×ATR, Oil 1.2×ATR. Kalın kırmızı çizgi olarak gösterilir.</p>
            </div>
            <div className={styles.helpFooter}>Temas tek başına giriş değildir; fiyatın bölgede nasıl davrandığını beklemek daha güvenli senaryodur. TP/SL alanları swing bazlı projeksiyondur.</div>
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
        {(obData as any)?.projection ? (() => {
          const p = (obData as any).projection;
          const isBull = p.direction === "bullish";
          return (
            <div className={styles.statItem} style={{ color: isBull ? "#22c55e" : "#ef4444", gap: 6, display: "flex", flexWrap: "wrap" }}>
              <span style={{ color: "#ef4444", fontWeight: 700 }}>⊗ SL {p.stop_loss.toFixed(1)}</span>
              <span style={{ color: "#22c55e" }}>① {p.tp1.toFixed(1)}</span>
              <span style={{ color: "#16a34a" }}>② {p.tp2.toFixed(1)}</span>
              <span style={{ color: "#15803d" }}>③ {p.tp3.toFixed(1)}</span>
              <span style={{ color: "#facc15", marginLeft: 4 }}>Range {p.swing_range.toFixed(0)}pts · {p.confidence}</span>
            </div>
          );
        })() : null}
        {signal?.reasons?.length ? (
          <div className={styles.statItem} style={{ marginLeft: "auto" }}>
            {signal.reasons.slice(0, 3).join(" \u00B7 ")}
          </div>
        ) : null}
      </div>
    </div>
  );
}
