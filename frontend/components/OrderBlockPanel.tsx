"use client";

import { useMemo, useState } from "react";
import { PlayCircle, HelpCircle, TrendingUp, TrendingDown, Target } from "lucide-react";
import OrderBlockChart from "./OrderBlockChart";
import OrderBlockSignals from "./OrderBlockSignals";
import OrderBlockSettings, { defaultSettings, OrderBlockSettingsValue } from "./OrderBlockSettings";
import { useOrderBlockDetect } from "../lib/api/orderBlocks";
import { useFVGDetect } from "../lib/api/fvg";
import GuidePanel from "./GuidePanel";

const timeframes = ["5m", "15m", "1h", "4h"] as const;

interface OrderBlockPanelProps {
  symbol?: string;
  symbolLabel?: string;
}

export default function OrderBlockPanel({ symbol = "NDX.INDX", symbolLabel = "NASDAQ" }: OrderBlockPanelProps) {
  const [showGuide, setShowGuide] = useState(false);
  const [timeframe, setTimeframe] = useState<(typeof timeframes)[number]>("5m");
  const [settings, setSettings] = useState<OrderBlockSettingsValue>(defaultSettings);

  const payload = useMemo(
    () => ({
      symbol,
      timeframe,
      limit: 500,
      config: {
        fractal_period: settings.fractalPeriod,
        min_displacement_atr: settings.minDisplacementAtr,
        min_score: settings.minScore,
        zone_type: settings.zoneType,
        max_tests: settings.maxTests
      }
    }),
    [symbol, settings, timeframe]
  );

  const { data, isLoading, error, refetch } = useOrderBlockDetect(payload);
  const typedData = data as {
    order_blocks?: any[];
    active_signals?: any[];
    total_order_blocks?: number;
    combined_signal?: { action: string; confidence: number; reasoning: string[] };
  } | undefined;
  const orderBlocks = typedData?.order_blocks ?? [];
  const signals = typedData?.active_signals ?? [];

  // FVG Detection with intraday support
  const [fvgTimeframe, setFvgTimeframe] = useState<"1m" | "5m" | "1h" | "1d">("5m");
  const { data: fvgData, isLoading: fvgLoading, refetch: refetchFvg } = useFVGDetect({
    symbol,
    timeframe: fvgTimeframe,
    limit: 200,
  });
  const fvgs = fvgData?.fvgs ?? [];
  const unfilledFVGs = fvgs.filter((f) => f.is_valid && !f.is_filled);

  return (
    <>
      <GuidePanel
        isOpen={showGuide}
        onClose={() => setShowGuide(false)}
        type="orderblock"
        symbol={symbolLabel}
      />
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-textSecondary">Order Block Detector (SMC) • {symbolLabel}</p>
            <h3 className="text-lg font-semibold">Smart Money Zones</h3>
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
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 transition"
            >
              <PlayCircle className="w-4 h-4" /> Scan
            </button>
          </div>
        </div>
      <div className="flex flex-wrap gap-2 text-sm">
        {timeframes.map((frame) => (
          <button
            key={frame}
            onClick={() => setTimeframe(frame)}
            className={`px-3 py-1 rounded-full ${
              timeframe === frame ? "bg-white text-background" : "bg-white/10 text-textSecondary"
            }`}
          >
            {frame}
          </button>
        ))}
      </div>
      <div className="text-xs text-textSecondary">
        {isLoading ? "Scanning..." : `Found ${typedData?.total_order_blocks ?? 0} OBs`}
      </div>

      {error ? <p className="text-sm text-danger">Order block scan failed.</p> : null}

      <OrderBlockChart orderBlocks={orderBlocks} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-3 min-w-0">
          <p className="text-sm font-medium text-textSecondary">Order Block List</p>
          <div className="space-y-3 max-h-72 overflow-auto pr-1">
            {orderBlocks.slice(0, 6).map((ob: any) => (
              <div key={ob.index} className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium">{ob.type === "bullish" ? "🟢 Bullish" : "🔴 Bearish"}</span>
                  <span className="text-sm font-mono font-semibold">{Math.round(ob.score)}/100</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full mt-3">
                  <div className={`h-2 rounded-full ${ob.type === "bullish" ? "bg-success" : "bg-danger"}`} style={{ width: `${ob.score}%` }} />
                </div>
                <div className="mt-3 text-sm text-textSecondary font-mono">
                  Zone: {Number(ob.zone_low).toFixed(2)} - {Number(ob.zone_high).toFixed(2)}
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {ob.has_choch && <span className="px-2.5 py-1 bg-accent/20 text-accent rounded-full text-xs font-medium">CHoCH ✓</span>}
                  {ob.has_bos && <span className="px-2.5 py-1 bg-white/10 rounded-full text-xs">BOS ✓</span>}
                  {ob.has_fvg && <span className="px-2.5 py-1 bg-white/10 rounded-full text-xs">FVG ✓</span>}
                  <span className="px-2.5 py-1 bg-white/10 rounded-full text-xs">Fib {ob.fib_level}</span>
                </div>
              </div>
            ))}
            {orderBlocks.length > 6 && (
              <p className="text-xs text-textSecondary text-center py-2">+{orderBlocks.length - 6} more Order Blocks</p>
            )}
          </div>
        </div>
        <div className="space-y-3 min-w-0">
          <p className="text-sm font-medium text-textSecondary">Entry Signals</p>
          <OrderBlockSignals signals={signals} />
        </div>
      </div>

      {/* Fair Value Gaps Section */}
      <div className="border-t border-white/10 pt-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-400" />
            <p className="text-sm font-medium text-textSecondary">Fair Value Gaps (FVG)</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              {(["1m", "5m", "1h", "1d"] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setFvgTimeframe(tf)}
                  className={`px-2 py-0.5 rounded text-xs ${
                    fvgTimeframe === tf
                      ? "bg-cyan-500 text-white"
                      : "bg-white/10 text-textSecondary hover:bg-white/20"
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
            <div className="text-xs text-textSecondary">
              {fvgLoading ? "Scanning..." : `${fvgData?.total_fvgs ?? 0} FVGs (${fvgData?.unfilled_count ?? 0} unfilled)`}
            </div>
          </div>
        </div>
        
        {fvgs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nearest Bullish FVG */}
            {fvgData?.nearest_bullish && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-medium text-emerald-400">Nearest Bullish FVG</span>
                </div>
                <div className="text-lg font-mono font-semibold text-white">
                  {fvgData.nearest_bullish.gap_low.toFixed(2)} - {fvgData.nearest_bullish.gap_high.toFixed(2)}
                </div>
                <div className="flex items-center gap-3 mt-2 text-xs text-textSecondary">
                  <span>Gap: {fvgData.nearest_bullish.gap_percent.toFixed(2)}%</span>
                  <span>Score: {Math.round(fvgData.nearest_bullish.score)}/100</span>
                  <span className={fvgData.nearest_bullish.is_filled ? "text-zinc-500" : "text-emerald-400"}>
                    {fvgData.nearest_bullish.is_filled ? "Filled" : `${fvgData.nearest_bullish.fill_percent.toFixed(0)}% filled`}
                  </span>
                </div>
              </div>
            )}

            {/* Nearest Bearish FVG */}
            {fvgData?.nearest_bearish && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="w-4 h-4 text-red-400" />
                  <span className="text-sm font-medium text-red-400">Nearest Bearish FVG</span>
                </div>
                <div className="text-lg font-mono font-semibold text-white">
                  {fvgData.nearest_bearish.gap_low.toFixed(2)} - {fvgData.nearest_bearish.gap_high.toFixed(2)}
                </div>
                <div className="flex items-center gap-3 mt-2 text-xs text-textSecondary">
                  <span>Gap: {fvgData.nearest_bearish.gap_percent.toFixed(2)}%</span>
                  <span>Score: {Math.round(fvgData.nearest_bearish.score)}/100</span>
                  <span className={fvgData.nearest_bearish.is_filled ? "text-zinc-500" : "text-red-400"}>
                    {fvgData.nearest_bearish.is_filled ? "Filled" : `${fvgData.nearest_bearish.fill_percent.toFixed(0)}% filled`}
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-textSecondary text-center py-4">
            {fvgLoading ? "Scanning for FVGs..." : "No significant FVGs detected"}
          </div>
        )}

        {/* FVG List */}
        {unfilledFVGs.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-textSecondary mb-2">Unfilled FVGs (potential reversal zones)</p>
            <div className="space-y-2 max-h-40 overflow-auto">
              {unfilledFVGs.slice(0, 5).map((fvg, idx) => (
                <div key={idx} className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2 text-sm">
                  <div className="flex items-center gap-2">
                    {fvg.type === "bullish" ? (
                      <TrendingUp className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <TrendingDown className="w-3 h-3 text-red-400" />
                    )}
                    <span className="font-mono">{fvg.gap_low.toFixed(2)} - {fvg.gap_high.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-textSecondary">
                    <span>{fvg.gap_percent.toFixed(2)}%</span>
                    <span className="text-cyan-400">{fvg.fill_percent.toFixed(0)}% filled</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-white/10 pt-5">
        <p className="text-sm font-medium text-textSecondary mb-4">Order Block Settings</p>
        <OrderBlockSettings value={settings} onChange={setSettings} />
      </div>

      {typedData?.combined_signal && (
        <div className="bg-white/5 rounded-xl p-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs text-textSecondary">Combined Signal</p>
              <p className="text-lg font-semibold mt-1">{typedData.combined_signal.action}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-textSecondary">Confidence</p>
              <p className="text-lg font-semibold mt-1">{Math.round(typedData.combined_signal.confidence * 100)}%</p>
            </div>
          </div>
          <ul className="mt-4 space-y-1 text-sm text-textSecondary">
            {typedData.combined_signal.reasoning.slice(0, 4).map((item: string) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      )}
      </div>
    </>
  );
}
