"use client";

import { useMemo, useState } from "react";
import { PlayCircle } from "lucide-react";
import OrderBlockChart from "./OrderBlockChart";
import OrderBlockSignals from "./OrderBlockSignals";
import OrderBlockSettings, { defaultSettings, OrderBlockSettingsValue } from "./OrderBlockSettings";
import { useOrderBlockDetect } from "../lib/api/orderBlocks";

const timeframes = ["5m", "15m", "1h", "4h"] as const;

export default function OrderBlockPanel() {
  const [timeframe, setTimeframe] = useState<(typeof timeframes)[number]>("5m");
  const [settings, setSettings] = useState<OrderBlockSettingsValue>(defaultSettings);
  const payload = useMemo(
    () => ({
      symbol: "NDX.INDX",
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
    [settings, timeframe]
  );

  const { data, isLoading, error, refetch } = useOrderBlockDetect(payload);
  const orderBlocks = data?.order_blocks ?? [];
  const signals = data?.active_signals ?? [];

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-textSecondary">Order Block Detector (SMC)</p>
          <h3 className="text-lg font-semibold">Smart Money Zones</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 transition"
        >
          <PlayCircle className="w-4 h-4" /> Scan Order Blocks
        </button>
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
        {isLoading ? "Scanning..." : `Found ${data?.total_order_blocks ?? 0} OBs`}
      </div>

      {error ? <p className="text-sm text-danger">Order block scan failed.</p> : null}

      <OrderBlockChart orderBlocks={orderBlocks} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="text-sm text-textSecondary">Order Block List</p>
          <div className="space-y-2 max-h-56 overflow-auto">
            {orderBlocks.map((ob: any) => (
              <div key={ob.index} className="bg-white/5 rounded-lg p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span>{ob.type === "bullish" ? "🟢 Bullish" : "🔴 Bearish"}</span>
                  <span>{Math.round(ob.score)}/100</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full mt-2">
                  <div className="h-2 bg-success rounded-full" style={{ width: `${ob.score}%` }} />
                </div>
                <div className="mt-2 text-textSecondary">Zone: {ob.zone_low} - {ob.zone_high}</div>
                <div className="flex flex-wrap gap-2 mt-2 text-[10px]">
                  {ob.has_choch && <span className="px-2 py-1 bg-white/10 rounded-full">CHoCH ✓</span>}
                  {ob.has_bos && <span className="px-2 py-1 bg-white/10 rounded-full">BOS ✓</span>}
                  {ob.has_fvg && <span className="px-2 py-1 bg-white/10 rounded-full">FVG ✓</span>}
                  <span className="px-2 py-1 bg-white/10 rounded-full">Fib {ob.fib_level}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-2">
          <p className="text-sm text-textSecondary">Active Entry Signals</p>
          <OrderBlockSignals signals={signals} />
        </div>
      </div>

      <div className="border-t border-white/10 pt-4">
        <p className="text-sm text-textSecondary mb-3">Order Block Settings</p>
        <OrderBlockSettings value={settings} onChange={setSettings} />
      </div>

      {data?.combined_signal && (
        <div className="bg-white/5 rounded-xl p-4 text-sm">
          <p className="font-semibold">Combined Signal: {data.combined_signal.action}</p>
          <p className="text-textSecondary">Confidence: {Math.round(data.combined_signal.confidence * 100)}%</p>
          <ul className="list-disc list-inside text-xs text-textSecondary mt-2">
            {data.combined_signal.reasoning.map((item: string) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
