"use client";

import { Activity } from "lucide-react";
import { useRtyhiimDetect } from "../lib/api/rtyhiim";

export default function RTYHIIMDetectorPanel() {
  const { data, isLoading, error, refetch } = useRtyhiimDetect();
  const state = data?.state;

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-textSecondary">RTYHIIM Detector</p>
          <h3 className="text-lg font-semibold">Rhythm Intelligence</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 rounded-full hover:bg-white/10 transition"
          aria-label="Refresh RTYHIIM"
        >
          <Activity className="w-4 h-4" />
        </button>
      </div>
      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-6 w-24" />
          <div className="skeleton h-3 w-full" />
        </div>
      ) : error ? (
        <div className="text-sm text-danger">RTYHIIM verisi alınamadı.</div>
      ) : state ? (
        <>
          <div className="flex items-center gap-3 text-sm">
            <span className="px-3 py-1 rounded-full bg-white/10">{state.pattern_type}</span>
            <span>Period: {state.dominant_period_s.toFixed(1)}s</span>
            <span>Confidence: {Math.round(state.confidence * 100)}%</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white/5 rounded-lg p-3">
              <p className="text-textSecondary">Regularity</p>
              <p className="font-semibold">{Math.round(state.regularity * 100)}%</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3">
              <p className="text-textSecondary">Amplitude</p>
              <p className="font-semibold">{state.amplitude.toFixed(2)}</p>
            </div>
          </div>
          <div className="text-sm">
            Signal: <span className="font-semibold">{state.direction}</span>
          </div>
          <div className="text-xs text-textSecondary">
            Predictions: {state.predictions.map((p: any) => `${p.horizon}: ${p.value.toFixed(2)}`).join(" | ")}
          </div>
        </>
      ) : (
        <p className="text-sm text-textSecondary">No rhythm data available.</p>
      )}
    </div>
  );
}
