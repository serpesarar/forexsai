"use client";

import { X } from "lucide-react";
import CircularProgress from "./CircularProgress";

type DetailType = "support_resistance" | "ema_distance" | "trend_channel";

interface DetailPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  symbol: string;
  type: DetailType | null;
  data: Record<string, any> | null;
}

export default function DetailPanel({ isOpen, onClose, title, symbol, type, data }: DetailPanelProps) {
  if (!isOpen || !type || !data) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-6 md:items-center">
      <div className="detail-panel-overlay absolute inset-0" onClick={onClose} />
      <div className="detail-panel-content relative z-10 w-full max-w-2xl rounded-2xl border border-white/10 bg-background p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{symbol}</p>
            <h3 className="mt-2 text-lg font-semibold">{title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 text-textSecondary"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {type === "support_resistance" && (
          <div className="mt-6 space-y-6">
            <CircularProgress
              value={data.reliability * 100}
              size={180}
              label="Reliability Score"
              sublabel={`${Math.round(data.reliability * 100)}%`}
              colorClassName={data.reliability > 0.8 ? "text-success" : "text-accent"}
            />
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-textSecondary uppercase tracking-[0.2em]">Distance (pts)</p>
                <p className="mt-2 text-lg font-mono text-success">+{data.distance}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-textSecondary uppercase tracking-[0.2em]">Distance (%)</p>
                <p className={`mt-2 text-lg font-mono ${data.distancePct > 0 ? "text-success" : "text-danger"}`}>
                  {data.distancePct.toFixed(2)}%
                </p>
              </div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-textSecondary space-y-2">
              <div className="flex items-center justify-between">
                <span>Strength</span>
                <span className="font-mono">{data.strength}/10</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Touches</span>
                <span className="font-mono">{data.hits}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Last Touched</span>
                <span className="font-mono">{data.lastTouched}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Price Level</span>
                <span className="font-mono">${data.price}</span>
              </div>
            </div>
            <div className="rounded-xl border border-white/10 bg-gradient-to-br from-white/5 to-transparent p-4 text-xs text-textSecondary">
              Mini context chart placeholder
            </div>
          </div>
        )}

        {type === "ema_distance" && (
          <div className="mt-6 space-y-6">
            <CircularProgress
              value={Math.min(Math.abs(data.distancePct), 100)}
              size={180}
              label="Distance from EMA"
              sublabel={`${data.distancePct.toFixed(2)}%`}
              colorClassName={Math.abs(data.distancePct) > 2 ? "text-accent" : "text-textSecondary"}
            />
            <div className="grid grid-cols-2 gap-4 text-xs">
              {[
                { label: "EMA Value", value: data.emaValue },
                { label: "Current Price", value: data.currentPrice },
                { label: "Absolute Distance", value: data.distance },
                { label: "Distance %", value: `${data.distancePct.toFixed(2)}%` },
              ].map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="text-textSecondary uppercase tracking-[0.2em]">{item.label}</p>
                  <p className="mt-2 text-lg font-mono">{item.value}</p>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-textSecondary space-y-2">
              <div className="flex items-center justify-between">
                <span>Signal Interpretation</span>
                <span className="font-mono">
                  {data.distancePct > 1
                    ? "Above EMA (Bullish)"
                    : data.distancePct < -1
                      ? "Below EMA (Bearish)"
                      : "Near EMA (Neutral)"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>EMA Period</span>
                <span className="font-mono">{data.period} periods</span>
              </div>
            </div>
          </div>
        )}

        {type === "trend_channel" && (
          <div className="mt-6 space-y-6">
            <CircularProgress
              value={data.trendStrength * 100}
              size={180}
              label="Trend Strength"
              sublabel={`${Math.round(data.trendStrength * 100)}%`}
              colorClassName={data.trendStrength > 0.7 ? "text-success" : "text-accent"}
            />
            <div className="grid grid-cols-2 gap-4 text-xs">
              {[
                { label: "Channel Width", value: data.channelWidth },
                { label: "Distance to Upper", value: data.distanceToUpper },
                { label: "Distance to Lower", value: data.distanceToLower },
                { label: "R² Correlation", value: data.rSquared.toFixed(2) },
              ].map((item) => (
                <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="text-textSecondary uppercase tracking-[0.2em]">{item.label}</p>
                  <p className="mt-2 text-lg font-mono">{item.value}</p>
                </div>
              ))}
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-textSecondary space-y-2">
              <div className="flex items-center justify-between">
                <span>Position in Channel</span>
                <span className="font-mono">
                  {data.distanceToUpper < data.distanceToLower ? "Upper half" : "Lower half"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Slope</span>
                <span className="font-mono">{data.slope.toFixed(4)} pts/candle</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Trend Quality</span>
                <span className="font-mono">{data.trendQuality}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
