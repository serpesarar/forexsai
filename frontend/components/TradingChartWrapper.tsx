"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import TradingChart from "./TradingChart";
import { useNewsMarkers, NewsMarker, convertToChartMarkers } from "../hooks/useNewsMarkers";
import { Newspaper, X, ExternalLink, TrendingUp, TrendingDown, Minus, Flame } from "lucide-react";
import { normalizeCandles } from "../lib/chart/normalizeCandles";

interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ChartDataResponse {
  symbol: string;
  timeframe: string;
  data: CandleData[];
}

const API_BASE = "https://upbeat-flow-production.up.railway.app";

async function fetchChartData(symbol: string, timeframe: string): Promise<CandleData[]> {
  const res = await fetch(
    `${API_BASE}/api/data/ohlcv?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=500`
  );
  if (!res.ok) throw new Error("Failed to fetch chart data");
  const data: ChartDataResponse = await res.json();

  return normalizeCandles(data.data || [], timeframe);
}

interface TradingChartWrapperProps {
  symbol: string;
  symbolLabel: string;
  initialTimeframe?: string;
  height?: number;
}

// News Tooltip Component
function NewsTooltip({ marker, onClose }: { marker: NewsMarker; onClose: () => void }) {
  const getDirectionColor = (dir: string) => {
    if (dir === "bullish") return "text-green-400";
    if (dir === "bearish") return "text-red-400";
    return "text-gray-400";
  };

  const getDirectionIcon = (dir: string) => {
    if (dir === "bullish") return <TrendingUp className="w-3 h-3" />;
    if (dir === "bearish") return <TrendingDown className="w-3 h-3" />;
    return <Minus className="w-3 h-3" />;
  };

  const getUrgencyIcon = (urgency: string) => {
    if (urgency === "breaking") return "🚨";
    if (urgency === "high") return "🔴";
    if (urgency === "medium") return "🟡";
    return "🟢";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="bg-slate-900 border border-white/10 rounded-xl shadow-2xl p-5 max-w-md w-full mx-4 animate-in fade-in zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getUrgencyIcon(marker.urgency)}</span>
            <div>
              <span className={`text-xs font-bold uppercase tracking-wider ${getDirectionColor(marker.direction)}`}>
                {marker.direction}
              </span>
              <div className="text-xs text-slate-400">
                {new Date(marker.time).toLocaleString("tr-TR")}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-lg transition"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-white mb-2 leading-tight">
          {marker.headline}
        </h3>

        {marker.headline_en && marker.headline_en !== marker.headline && (
          <p className="text-sm text-slate-400 mb-3 italic">{marker.headline_en}</p>
        )}

        {/* Score & Impact */}
        <div className="flex items-center gap-4 mb-3">
          <div className="flex items-center gap-1 text-sm">
            <span className="text-slate-400">Etki:</span>
            <span className="font-bold text-white">{marker.score}/10</span>
          </div>
          <div className="flex items-center gap-1 text-sm">
            <span className="text-slate-400">Yön:</span>
            <span className={`flex items-center gap-1 ${getDirectionColor(marker.direction)}`}>
              {getDirectionIcon(marker.direction)}
              {marker.direction === "bullish" ? "Yükseliş" : marker.direction === "bearish" ? "Düşüş" : "Nötr"}
            </span>
          </div>
        </div>

        {/* Reasoning */}
        {marker.reasoning_tr && (
          <div className="bg-white/5 rounded-lg p-3 mb-4">
            <p className="text-xs text-slate-400 mb-1">AI Yorumu:</p>
            <p className="text-sm text-slate-200">{marker.reasoning_tr}</p>
          </div>
        )}

        {/* URL */}
        {marker.url && (
          <a
            href={marker.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition text-sm font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            Haberi Oku
          </a>
        )}
      </div>
    </div>
  );
}

export default function TradingChartWrapper({
  symbol,
  symbolLabel,
  initialTimeframe = "1d",
  height = 400,
}: TradingChartWrapperProps) {
  const [timeframe, setTimeframe] = useState(initialTimeframe);
  const [selectedMarker, setSelectedMarker] = useState<NewsMarker | null>(null);
  const [showMarkers, setShowMarkers] = useState(true);

  // Fetch chart data
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["chart-data", symbol, timeframe],
    queryFn: () => fetchChartData(symbol, timeframe),
    placeholderData: (prev) => prev,
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000,
  });

  // Fetch news markers
  const { markers: newsMarkers, loading: markersLoading } = useNewsMarkers(
    symbol,
    48, // 48 hours
    5   // min impact score
  );

  // Convert markers for TradingChart
  const chartMarkers = convertToChartMarkers(showMarkers ? newsMarkers : []);

  // Handle marker click
  const handleMarkerClick = useCallback((markerData: any) => {
    // Find full marker data
    const fullMarker = newsMarkers.find(m => m.id === markerData.id);
    if (fullMarker) {
      setSelectedMarker(fullMarker);
    }
  }, [newsMarkers]);

  if (error) {
    return (
      <div className="glass-premium rounded-2xl p-8 text-center">
        <p className="text-danger">Grafik verisi yüklenemedi</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* News Toggle Button */}
      <div className="absolute top-4 right-20 z-10">
        <button
          onClick={() => setShowMarkers(!showMarkers)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${showMarkers
            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
            : "bg-white/5 text-slate-400 hover:bg-white/10"
          }`}
        >
          <Newspaper className="w-3.5 h-3.5" />
          Haberler {showMarkers ? "Açık" : "Kapalı"}
          {newsMarkers.length > 0 && (
            <span className="bg-white/20 px-1.5 py-0.5 rounded-full text-[10px]">
              {newsMarkers.length}
            </span>
          )}
        </button>
      </div>

      <TradingChart
        symbol={symbol}
        symbolLabel={symbolLabel}
        data={data || []}
        height={height}
        onRefresh={() => refetch()}
        isLoading={isLoading}
        currentTimeframe={timeframe}
        onTimeframeChange={(tf) => setTimeframe(tf)}
        newsMarkers={chartMarkers as any}
        onMarkerClick={handleMarkerClick}
      />

      {/* Marker Legend */}
      {showMarkers && newsMarkers.length > 0 && (
        <div className="absolute bottom-12 left-4 bg-slate-900/90 backdrop-blur-sm rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-4 text-[11px] text-slate-300">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-green-500 flex items-center justify-center text-[8px]">↑</span>
              <span>Pozitif</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500 flex items-center justify-center text-[8px]">↓</span>
              <span>Negatif</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-blue-500"></span>
              <span>Nötr</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm">🚨</span>
              <span>Breaking</span>
            </div>
          </div>
        </div>
      )}

      {/* News Tooltip Modal */}
      {selectedMarker && (
        <NewsTooltip
          marker={selectedMarker}
          onClose={() => setSelectedMarker(null)}
        />
      )}
    </div>
  );
}
