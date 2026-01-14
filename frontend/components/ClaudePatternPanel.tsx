"use client";

import { useState } from "react";
import { useClaudePatterns } from "../lib/api";

const timeframes = ["5m", "15m", "30m", "1h", "4h", "1d"] as const;

export default function ClaudePatternPanel() {
  const [active, setActive] = useState<string>("5m");
  const { data, isLoading, error, refetch } = useClaudePatterns({
    symbol: "NDX.INDX",
    timeframes: [...timeframes]
  });

  const activeData = (data as any)?.analyses?.[active];

  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-textSecondary">Claude AI - Pattern Detection</p>
          <h3 className="text-lg font-semibold">Multi-Timeframe Intelligence</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="text-sm px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 transition"
        >
          Analyze Now
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {timeframes.map((frame) => (
          <button
            key={frame}
            onClick={() => setActive(frame)}
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              active === frame ? "bg-white text-background" : "bg-white/10 text-textSecondary"
            }`}
          >
            {frame}
          </button>
        ))}
      </div>
      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-6 w-1/2" />
          <div className="skeleton h-20 w-full" />
        </div>
      ) : error ? (
        <div className="text-sm text-danger">Claude analiz verisi alınamadı.</div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {activeData?.detected_patterns?.map((pattern: any) => (
              <div key={pattern.pattern_name} className="bg-white/5 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{pattern.pattern_name}</p>
                    <p className="text-xs text-textSecondary">Source: {pattern.pattern_source}</p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-success/20 text-success">
                    {pattern.signal.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-textSecondary">Completion</p>
                  <div className="h-2 bg-white/10 rounded-full">
                    <div
                      className="h-2 bg-success rounded-full"
                      style={{ width: `${pattern.completion_percentage}%` }}
                    />
                  </div>
                </div>
                <div className="text-xs grid grid-cols-3 gap-2">
                  <div>
                    <p className="text-textSecondary">Entry</p>
                    <p className="font-semibold">{pattern.entry}</p>
                  </div>
                  <div>
                    <p className="text-textSecondary">Stop</p>
                    <p className="font-semibold">{pattern.stop_loss}</p>
                  </div>
                  <div>
                    <p className="text-textSecondary">Target</p>
                    <p className="font-semibold">{pattern.target}</p>
                  </div>
                </div>
                <div className="text-xs">
                  <p className="text-textSecondary">Confidence</p>
                  <p className="font-semibold">{Math.round(pattern.confidence * 100)}%</p>
                </div>
              </div>
            ))}
          </div>
          <div className="text-sm text-textSecondary">{activeData?.summary}</div>
          <div className="text-sm font-semibold">Recommendation: {activeData?.recommendation}</div>
        </>
      )}
    </div>
  );
}
