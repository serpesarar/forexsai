"use client";

import React, { memo, useEffect, useRef, useCallback, useState, useMemo } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time, MouseEventParams } from "lightweight-charts";
import { cn } from "@/lib/utils";
import type { 
  CandleData, 
  NewsMarker, 
  SupportedSymbol,
  EnrichedNews 
} from "@/types/news-correlation";

interface NewsCorrelationChartProps {
  symbol: SupportedSymbol;
  timeframe: string;
  candles: CandleData[];
  markers: NewsMarker[];
  selectedNewsIds: string[];
  hoveredNewsId: string | null;
  news: EnrichedNews[];
  showGhostMarkers: boolean;
  onCandleClick: (candle: CandleData | null) => void;
  onMarkerClick: (newsIds: string[]) => void;
  onTimeRangeChange: (range: { from: number; to: number }) => void;
  className?: string;
}

// Chart colors - dark theme
const chartColors = {
  background: "#0a0a0f",
  grid: "#1e293b",
  text: "#94a3b8",
  border: "#334155",
  upColor: "#22c55e",
  downColor: "#ef4444",
  wickUpColor: "#22c55e",
  wickDownColor: "#ef4444",
};

// Marker colors with opacity for ghost markers
const getMarkerColor = (marker: NewsMarker, isSelected: boolean, isHovered: boolean) => {
  let baseColor = marker.color;
  
  // Apply opacity for ghost markers
  if (marker.isGhost) {
    baseColor = baseColor + "4D"; // 30% opacity in hex
  }
  
  // Highlight selected/hovered
  if (isSelected || isHovered) {
    return baseColor;
  }
  
  return baseColor;
};

export const NewsCorrelationChart = memo(function NewsCorrelationChart({
  symbol,
  timeframe,
  candles,
  markers,
  selectedNewsIds,
  hoveredNewsId,
  news,
  showGhostMarkers,
  onCandleClick,
  onMarkerClick,
  onTimeRangeChange,
  className,
}: NewsCorrelationChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<any[]>([]);
  const [isChartReady, setIsChartReady] = useState(false);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: string;
  }>({ visible: false, x: 0, y: 0, content: "" });
  
  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;
    
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: chartColors.background },
        textColor: chartColors.text,
        fontSize: 11,
      },
      grid: {
        vertLines: { color: chartColors.grid, style: 2 },
        horzLines: { color: chartColors.grid, style: 2 },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: chartColors.border,
          width: 1,
          style: 2,
          labelBackgroundColor: chartColors.border,
        },
        horzLine: {
          color: chartColors.border,
          width: 1,
          style: 2,
          labelBackgroundColor: chartColors.border,
        },
      },
      rightPriceScale: {
        borderColor: chartColors.border,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: chartColors.border,
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: (time: number) => {
          const date = new Date(time * 1000);
          return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        },
      },
      handleScroll: {
        vertTouchDrag: false,
      },
    });
    
    // Create candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: chartColors.upColor,
      downColor: chartColors.downColor,
      borderUpColor: chartColors.upColor,
      borderDownColor: chartColors.downColor,
      wickUpColor: chartColors.wickUpColor,
      wickDownColor: chartColors.wickDownColor,
    });
    
    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    setIsChartReady(true);
    
    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        const { width, height } = chartContainerRef.current.getBoundingClientRect();
        chartRef.current.applyOptions({ width, height });
      }
    };
    
    window.addEventListener("resize", handleResize);
    handleResize();
    
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);
  
  // Update candles
  useEffect(() => {
    if (!candleSeriesRef.current || !isChartReady) return;
    
    const formattedCandles = candles.map((c) => ({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    
    candleSeriesRef.current.setData(formattedCandles);
    
    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [candles, isChartReady]);
  
  // Update markers
  useEffect(() => {
    if (!candleSeriesRef.current || !isChartReady) return;
    
    // Clear existing markers
    markersRef.current.forEach((marker) => {
      candleSeriesRef.current?.detachPrimitive(marker);
    });
    markersRef.current = [];
    
    // Filter markers if needed
    const visibleMarkers = showGhostMarkers 
      ? markers 
      : markers.filter((m) => !m.isGhost);
    
    // Create lightweight-charts markers
    const chartMarkers = visibleMarkers.map((marker) => {
      const isSelected = marker.newsIds.some((id) => selectedNewsIds.includes(id));
      const isHovered = marker.newsIds.some((id) => id === hoveredNewsId);
      
      return {
        time: marker.time as Time,
        position: marker.position,
        color: getMarkerColor(marker, isSelected, isHovered),
        shape: marker.shape,
        size: isSelected || isHovered ? marker.size + 4 : marker.size,
        text: marker.impactCount > 1 ? String(marker.impactCount) : "",
      };
    });
    
    candleSeriesRef.current.setMarkers(chartMarkers);
  }, [markers, selectedNewsIds, hoveredNewsId, showGhostMarkers, isChartReady]);
  
  // Handle click events
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return;
    
    const handleClick = (param: MouseEventParams) => {
      if (!param.point || !param.time) return;
      
      // Check if clicked on a candle
      const clickedCandle = candles.find((c) => c.time === param.time);
      
      if (clickedCandle) {
        onCandleClick(clickedCandle);
      }
      
      // Check if clicked near a marker (within 5 minutes window)
      const clickTime = param.time as number;
      const nearbyMarkers = markers.filter((m) => Math.abs(m.time - clickTime) < 300);
      
      if (nearbyMarkers.length > 0) {
        const allNewsIds = nearbyMarkers.flatMap((m) => m.newsIds);
        onMarkerClick(allNewsIds);
      }
    };
    
    chartRef.current.subscribeClick(handleClick);
    
    return () => {
      chartRef.current?.unsubscribeClick(handleClick);
    };
  }, [candles, markers, onCandleClick, onMarkerClick, isChartReady]);
  
  // Handle crosshair move for tooltip
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return;
    
    const handleCrosshairMove = (param: MouseEventParams) => {
      if (!param.point || !param.time) {
        setTooltip((prev) => ({ ...prev, visible: false }));
        return;
      }
      
      const hoverTime = param.time as number;
      const nearbyMarkers = markers.filter((m) => Math.abs(m.time - hoverTime) < 300);
      
      if (nearbyMarkers.length > 0) {
        const marker = nearbyMarkers[0];
        const relatedNews = news.filter((n) => marker.newsIds.includes(n.id));
        
        if (relatedNews.length > 0) {
          const content = relatedNews
            .map((n) => `${n.headline.substring(0, 50)}...`)
            .join("\n");
          
          setTooltip({
            visible: true,
            x: param.point.x,
            y: param.point.y - 10,
            content,
          });
        }
      } else {
        setTooltip((prev) => ({ ...prev, visible: false }));
      }
    };
    
    chartRef.current.subscribeCrosshairMove(handleCrosshairMove);
    
    return () => {
      chartRef.current?.unsubscribeCrosshairMove(handleCrosshairMove);
    };
  }, [markers, news, isChartReady]);
  
  // Handle time range changes
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return;
    
    const handleVisibleTimeRangeChange = () => {
      const range = chartRef.current?.timeScale().getVisibleLogicalRange();
      if (range) {
        // Convert logical range to time
        const fromTime = Math.floor(range.from);
        const toTime = Math.floor(range.to);
        onTimeRangeChange({ from: fromTime, to: toTime });
      }
    };
    
    chartRef.current.timeScale().subscribeVisibleLogicalRangeChange(handleVisibleTimeRangeChange);
    
    return () => {
      chartRef.current?.timeScale().unsubscribeVisibleLogicalRangeChange(handleVisibleTimeRangeChange);
    };
  }, [onTimeRangeChange, isChartReady]);
  
  // Highlight selected/hovered news on chart
  useEffect(() => {
    if (!chartRef.current || !isChartReady) return;
    
    // Find time of selected news
    if (selectedNewsIds.length > 0) {
      const selectedNews = news.filter((n) => selectedNewsIds.includes(n.id));
      if (selectedNews.length > 0) {
        const newsTime = new Date(selectedNews[0].timestamp).getTime() / 1000;
        
        // Scroll to time
        chartRef.current.timeScale().scrollToPosition(newsTime, true);
        
        // Add vertical line highlight (using a primitive)
        // Note: This would need custom plugin implementation
      }
    }
  }, [selectedNewsIds, news, isChartReady]);
  
  return (
    <div className={cn("relative w-full h-full", className)}>
      {/* Chart Container */}
      <div 
        ref={chartContainerRef} 
        className="w-full h-full"
      />
      
      {/* Custom Tooltip */}
      {tooltip.visible && (
        <div
          className="absolute z-50 pointer-events-none"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: "translate(-50%, -100%)",
          }}
        >
          <div className="bg-slate-900/95 backdrop-blur-sm border border-slate-700 rounded-lg p-3 shadow-xl max-w-xs">
            <p className="text-xs text-slate-300 whitespace-pre-line">
              {tooltip.content}
            </p>
            <div className="mt-1 text-[10px] text-slate-500">
              Click to see details
            </div>
          </div>
          {/* Arrow */}
          <div className="absolute left-1/2 -translate-x-1/2 -bottom-1 w-2 h-2 bg-slate-900 border-r border-b border-slate-700 rotate-45" />
        </div>
      )}
      
      {/* Loading Overlay */}
      {!isChartReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/50">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
            <span className="text-sm text-slate-400">Loading chart...</span>
          </div>
        </div>
      )}
      
      {/* Legend/Info */}
      <div className="absolute top-4 left-4 flex items-center gap-4 pointer-events-none">
        <div className="bg-slate-900/80 backdrop-blur-sm rounded-lg px-3 py-2 border border-slate-800">
          <span className="text-sm font-bold text-white">{symbol}</span>
          <span className="text-xs text-slate-400 ml-2">{timeframe}</span>
        </div>
        
        {/* Marker legend */}
        <div className="bg-slate-900/80 backdrop-blur-sm rounded-lg px-3 py-2 border border-slate-800 flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
            <span className="text-[10px] text-slate-400">Bullish</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span className="text-[10px] text-slate-400">Bearish</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
            <span className="text-[10px] text-slate-400">Mixed</span>
          </div>
        </div>
      </div>
    </div>
  );
});

export default NewsCorrelationChart;
