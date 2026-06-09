"use client";

import { useState } from "react";
import { Activity, HelpCircle, TrendingUp, TrendingDown, Minus, Target } from "lucide-react";
import { useRtyhiimDetect, useConsolidation } from "../lib/api/rtyhiim";
import GuidePanel from "./GuidePanel";

interface RTYHIIMDetectorPanelProps {
  symbol?: string;
  symbolLabel?: string;
}

interface RtyhiimReactionZone {
  next_type: string;
  expected_direction: string;
  price: number;
  band: number;
  lower: number;
  upper: number;
  eta_seconds: number;
  eta_label: string;
  eta_bars: number;
}

interface RtyhiimData {
  state?: {
    pattern_type: string;
    dominant_period_s: number;
    confidence: number;
    regularity: number;
    amplitude: number;
    direction: string;
    predictions: Array<{ horizon: string; value: number }>;
    timeframe_used?: string;
    data_source?: string;
    upper_touches?: number;
    lower_touches?: number;
    touches_confirmed?: boolean;
    reaction_zone?: RtyhiimReactionZone | null;
  };
}

function formatPeriod(seconds: number): string {
  if (!seconds || seconds <= 0) return "—";
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export default function RTYHIIMDetectorPanel({ symbol = "NDX.INDX", symbolLabel = "NASDAQ" }: RTYHIIMDetectorPanelProps) {
  const [showGuide, setShowGuide] = useState(false);
  const { data, isLoading, error, refetch } = useRtyhiimDetect(symbol);
  const { data: consolidation, isLoading: consLoading } = useConsolidation(symbol, 20, "1m");
  const typedData = data as RtyhiimData | undefined;
  const state = typedData?.state;
  const rz = state?.reaction_zone;
  const noData = state?.data_source === "no_data" || state?.pattern_type === "insufficient_data";

  return (
    <>
      <GuidePanel
        isOpen={showGuide}
        onClose={() => setShowGuide(false)}
        type="rtyhiim"
        symbol={symbolLabel}
      />
      <div className="glass-premium p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-textSecondary">RTYHIIM Detector • {symbolLabel}</p>
            <h3 className="text-lg font-semibold">Rhythm Intelligence</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowGuide(true)}
              className="p-2 rounded-full hover:bg-white/10 transition text-accent"
              aria-label="Help"
              title="Kullanım Kılavuzu"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
            <button
              onClick={() => refetch()}
              className="p-2 rounded-full hover:bg-white/10 transition"
              aria-label="Refresh RTYHIIM"
            >
              <Activity className="w-4 h-4" />
            </button>
          </div>
        </div>
        {isLoading ? (
          <div className="space-y-2">
            <div className="skeleton h-4 w-20" />
            <div className="skeleton h-3 w-full" />
          </div>
        ) : error ? (
          <div className="text-xs text-danger">RTYHIIM verisi alınamadı.</div>
        ) : noData ? (
          <div className="text-xs text-textSecondary bg-white/5 rounded-lg p-3">
            Bu sembol için yeterli {state?.timeframe_used && state.timeframe_used !== "none" ? state.timeframe_used : "M1"} verisi yok — ritim analizi yapılamıyor.
          </div>
        ) : state ? (
          <>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2 py-1 rounded bg-accent/20 text-accent">{state.pattern_type}</span>
              {state.timeframe_used && (
                <span className="px-2 py-0.5 rounded bg-white/10 text-textSecondary">{state.timeframe_used}</span>
              )}
              <span className="text-textSecondary">Period: <span className="text-white">{formatPeriod(state.dominant_period_s)}</span></span>
              <span className="text-textSecondary">Conf: <span className="text-white">{Math.round(state.confidence * 100)}%</span></span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-white/5 rounded-lg p-2 text-center">
                <p className="text-textSecondary text-[10px]">Regularity</p>
                <p className="font-semibold">{Math.round(state.regularity * 100)}%</p>
              </div>
              <div className="bg-white/5 rounded-lg p-2 text-center">
                <p className="text-textSecondary text-[10px]">Amplitude</p>
                <p className="font-semibold">{state.amplitude.toFixed(2)}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-2 text-center">
                <p className="text-textSecondary text-[10px]">Signal</p>
                <p className={`font-semibold ${state.direction === "BUY" ? "text-success" : state.direction === "SELL" ? "text-danger" : ""}`}>
                  {state.direction}
                </p>
              </div>
            </div>
            <div className="text-[10px] text-textSecondary">
              <span className="uppercase tracking-wider">Predictions:</span>
              <div className="flex flex-wrap gap-2 mt-1">
                {state.predictions.map((p: any) => (
                  <span key={p.horizon} className="px-2 py-0.5 bg-white/5 rounded font-mono">
                    {p.horizon}: {p.value.toFixed(0)}
                  </span>
                ))}
              </div>
            </div>

            {/* Reaction Zone — sıradaki tepki bölgesi */}
            {rz && (
              <div className={`rounded-lg p-3 border ${
                rz.next_type === "support"
                  ? "bg-emerald-500/10 border-emerald-500/30"
                  : "bg-red-500/10 border-red-500/30"
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-semibold ${
                    rz.next_type === "support" ? "text-emerald-400" : "text-red-400"
                  }`}>
                    {rz.next_type === "support" ? "Sıradaki Destek (Dip)" : "Sıradaki Direnç (Tepe)"}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/10 text-[10px] text-textSecondary">
                    {rz.eta_label}
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-mono font-bold text-white">{rz.price.toFixed(2)}</span>
                  <span className="text-[10px] text-textSecondary">± {rz.band.toFixed(2)}</span>
                </div>
                <div className="text-[10px] text-textSecondary mt-1">
                  Bant: <span className="text-white font-mono">{rz.lower.toFixed(2)}</span> – <span className="text-white font-mono">{rz.upper.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    rz.expected_direction === "BUY" ? "bg-success/20 text-success" : "bg-danger/20 text-danger"
                  }`}>
                    {rz.expected_direction}
                  </span>
                  {state.touches_confirmed && (
                    <span className="text-[10px] text-emerald-400">
                      ✓ Dokunuş onaylı ({state.upper_touches}↑ / {state.lower_touches}↓)
                    </span>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-xs text-textSecondary">No rhythm data available.</p>
        )}

        {/* Consolidation / Range Detection */}
        <div className="border-t border-white/10 pt-4 mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-medium text-textSecondary">Yatay Hareket Tespiti (1m)</span>
          </div>
          
          {consLoading ? (
            <div className="skeleton h-16 w-full" />
          ) : consolidation ? (
            <div className="space-y-3">
              {/* Consolidation Status */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {consolidation.is_consolidating ? (
                    <span className="px-2 py-1 rounded bg-cyan-500/20 text-cyan-400 text-xs font-medium">
                      CONSOLIDATION
                    </span>
                  ) : (
                    <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-400 text-xs font-medium">
                      TRENDING
                    </span>
                  )}
                  <span className="text-xs text-textSecondary">
                    Score: <span className="text-white font-semibold">{consolidation.consolidation_score}/100</span>
                  </span>
                </div>
                {consolidation.breakout_direction && (
                  <div className="flex items-center gap-1 text-xs">
                    {consolidation.breakout_direction === "UP" ? (
                      <TrendingUp className="w-3 h-3 text-emerald-400" />
                    ) : consolidation.breakout_direction === "DOWN" ? (
                      <TrendingDown className="w-3 h-3 text-red-400" />
                    ) : (
                      <Minus className="w-3 h-3 text-zinc-400" />
                    )}
                    <span className={
                      consolidation.breakout_direction === "UP" ? "text-emerald-400" :
                      consolidation.breakout_direction === "DOWN" ? "text-red-400" : "text-zinc-400"
                    }>
                      {consolidation.breakout_direction}
                    </span>
                  </div>
                )}
              </div>

              {/* Range Display */}
              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-emerald-400">High: {consolidation.range_high.toFixed(2)}</span>
                  <span className="text-red-400">Low: {consolidation.range_low.toFixed(2)}</span>
                </div>
                
                {/* Range Bar */}
                <div className="relative h-3 bg-zinc-700 rounded-full overflow-hidden">
                  <div 
                    className="absolute h-full bg-cyan-500 rounded-full transition-all"
                    style={{ 
                      left: '0%',
                      width: `${Math.min(100, Math.max(0, consolidation.position_in_range))}%`
                    }}
                  />
                  <div 
                    className="absolute w-1 h-full bg-white"
                    style={{ left: `${Math.min(100, Math.max(0, consolidation.position_in_range))}%` }}
                  />
                </div>
                
                <div className="flex justify-between text-[10px] text-textSecondary mt-1">
                  <span>Range: {consolidation.range_size.toFixed(2)} ({consolidation.range_percent.toFixed(2)}%)</span>
                  <span>Pos: {consolidation.position_in_range.toFixed(0)}%</span>
                </div>
              </div>

              {/* Current Price & Midpoint */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-white/5 rounded p-2 text-center">
                  <p className="text-[10px] text-textSecondary">Current</p>
                  <p className="font-mono font-semibold">{consolidation.current_price.toFixed(2)}</p>
                </div>
                <div className="bg-white/5 rounded p-2 text-center">
                  <p className="text-[10px] text-textSecondary">Midpoint</p>
                  <p className="font-mono font-semibold">{consolidation.midpoint.toFixed(2)}</p>
                </div>
              </div>

              {/* Swing Points Info */}
              <div className="bg-white/5 rounded-lg p-3 mt-2">
                <div className="flex items-center justify-between text-[10px] mb-2">
                  <span className="text-textSecondary">Swing Noktaları</span>
                  <span className="text-white">{consolidation.swing_count} swing (min 4)</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <span className={consolidation.swing_high_consistency ? "text-emerald-400" : "text-zinc-500"}>
                        {consolidation.swing_high_consistency ? "✓" : "✗"}
                      </span>
                      <span className="text-[10px] text-textSecondary">Tepeler ({consolidation.swing_highs?.length || 0})</span>
                    </div>
                    <div className="text-[10px] text-textSecondary">
                      Sapma: <span className="text-white">{consolidation.high_deviation?.toFixed(2) || 0}</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <span className={consolidation.swing_low_consistency ? "text-emerald-400" : "text-zinc-500"}>
                        {consolidation.swing_low_consistency ? "✓" : "✗"}
                      </span>
                      <span className="text-[10px] text-textSecondary">Dipler ({consolidation.swing_lows?.length || 0})</span>
                    </div>
                    <div className="text-[10px] text-textSecondary">
                      Sapma: <span className="text-white">{consolidation.low_deviation?.toFixed(2) || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-textSecondary">Consolidation verisi yok</p>
          )}
        </div>
      </div>
    </>
  );
}
