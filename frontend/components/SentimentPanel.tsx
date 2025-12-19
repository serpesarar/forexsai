"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { useClaudeSentiment } from "../lib/api";

export default function SentimentPanel() {
  const { data, isLoading, error } = useClaudeSentiment();
  const [open, setOpen] = useState(true);

  return (
    <div className="glass-card p-6 space-y-4">
      <div>
        <p className="text-sm text-textSecondary">Market Sentiment Analysis</p>
        <h3 className="text-lg font-semibold">Macro Intelligence</h3>
      </div>
      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-8 w-32" />
          <div className="skeleton h-3 w-full" />
        </div>
      ) : error ? (
        <div className="text-sm text-danger">Sentiment verisi alınamadı.</div>
      ) : (
        <>
          <div className="flex items-center justify-center">
            <span className="text-2xl font-semibold px-6 py-3 rounded-full bg-success/20 text-success">
              {data.sentiment}
            </span>
          </div>
          <div className="text-center text-sm">
            Confidence: <span className="font-semibold">{Math.round(data.confidence * 100)}%</span>
          </div>
          <div className="space-y-2 text-xs">
            <div>
              <div className="flex justify-between">
                <span>Up</span>
                <span>{data.probability_up}%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full">
                <div className="h-2 bg-success rounded-full" style={{ width: `${data.probability_up}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between">
                <span>Down</span>
                <span>{data.probability_down}%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full">
                <div className="h-2 bg-danger rounded-full" style={{ width: `${data.probability_down}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between">
                <span>Sideways</span>
                <span>{data.probability_sideways}%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full">
                <div className="h-2 bg-warning rounded-full" style={{ width: `${data.probability_sideways}%` }} />
              </div>
            </div>
          </div>
          <button
            onClick={() => setOpen((prev) => !prev)}
            className="flex items-center gap-2 text-sm text-textSecondary"
          >
            Key Factors <ChevronDown className={`w-4 h-4 transition ${open ? "rotate-180" : ""}`} />
          </button>
          {open && (
            <div className="space-y-2 text-sm">
              {data.key_factors.map((factor: any) => (
                <div key={factor.factor} className="bg-white/5 rounded-lg p-3">
                  <p className="font-semibold">{factor.factor}</p>
                  <p className="text-xs text-textSecondary">Weight: {Math.round(factor.weight * 100)}%</p>
                  <p className="text-xs text-textSecondary">{factor.reasoning}</p>
                </div>
              ))}
            </div>
          )}
          <div className="text-sm text-textSecondary">{data.analysis}</div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2 py-1 rounded-full bg-white/10">VIX: {data.market_data_summary.vix}</span>
            <span className="px-2 py-1 rounded-full bg-white/10">SPY: {data.market_data_summary.spy}</span>
          </div>
          <div className="text-sm font-semibold">Recommendation: {data.recommendation}</div>
        </>
      )}
    </div>
  );
}
