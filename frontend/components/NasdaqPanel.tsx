"use client";

import { RefreshCw } from "lucide-react";
import { useNasdaq } from "../lib/api";

function Badge({ label }: { label: string }) {
  const color =
    label === "BUY" ? "bg-success/20 text-success" : label === "SELL" ? "bg-danger/20 text-danger" : "bg-warning/20 text-warning";
  return <span className={`px-3 py-1 rounded-full text-xs font-semibold ${color}`}>{label}</span>;
}

export default function NasdaqPanel() {
  const { data, isLoading, refetch, error } = useNasdaq();

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-textSecondary">NASDAQ 100 Analysis</p>
          <h3 className="text-lg font-semibold">ML Signal Overview</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-full hover:bg-white/10 transition"
          aria-label="Refresh NASDAQ"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-6 w-24" />
          <div className="skeleton h-3 w-full" />
          <div className="skeleton h-3 w-5/6" />
        </div>
      ) : error ? (
        <div className="text-sm text-danger">NASDAQ verisi alınamadı. Lütfen tekrar deneyin.</div>
      ) : (
        <>
          <div className="flex items-center gap-3">
            <Badge label={(data as any).signal} />
            <span className="text-sm text-textSecondary">Confidence</span>
            <div className="flex-1 h-2 bg-white/10 rounded-full">
              <div className="h-2 rounded-full bg-success" style={{ width: `${data.confidence * 100}%` }} />
            </div>
            <span className="text-sm font-semibold">{Math.round(data.confidence * 100)}%</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white/5 rounded-lg p-3">
              <p className="text-textSecondary">Distance to EMA(20)</p>
              <p className="font-semibold">+{data.metrics.distance_to_ema} pts</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3">
              <p className="text-textSecondary">Distance to Support</p>
              <p className="font-semibold">{data.metrics.distance_to_support} pts</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3">
              <p className="text-textSecondary">Support Strength</p>
              <p className="font-semibold">{Math.round(data.metrics.support_strength * 10)}/10 ⭐</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3">
              <p className="text-textSecondary">RSI</p>
              <p className="font-semibold">{data.metrics.rsi} (neutral)</p>
            </div>
          </div>
          <div>
            <p className="text-sm text-textSecondary mb-2">Reasoning</p>
            <ul className="list-disc list-inside text-sm space-y-1">
              {data.reasoning.map((item: string) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          {data.model_status && (
            <p className="text-xs text-warning">{data.model_status}</p>
          )}
          <p className="text-xs text-textSecondary">Timestamp: {data.timestamp}</p>
        </>
      )}
    </div>
  );
}
