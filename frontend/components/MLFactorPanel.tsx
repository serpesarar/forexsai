"use client";

import { useState, useEffect, useCallback } from "react";
import { Settings2, X, ChevronRight, RotateCcw, RefreshCw, Loader2 } from "lucide-react";
import { fetchPredictionWithFactors, type PredictionData } from "../lib/api/prediction";

type Factor = {
  id: string;
  name: string;
  nameEn: string;
  multiplier: number;
  enabled: boolean;
  weight: 1 | 2 | 3;
  description: string;
};

const DEFAULT_FACTORS: Factor[] = [
  { id: "trend", name: "Trend Analizi", nameEn: "Trend Analysis", multiplier: 0.7, enabled: true, weight: 2, description: "EMA uyumu ve trend yönü" },
  { id: "confluence", name: "Confluence", nameEn: "Confluence", multiplier: 1.15, enabled: true, weight: 2, description: "MTF ve S/R uyumu" },
  { id: "session", name: "Seans", nameEn: "Session", multiplier: 0.85, enabled: true, weight: 1, description: "Asia/London/NY seansı" },
  { id: "pattern", name: "Pattern", nameEn: "Pattern", multiplier: 1.15, enabled: true, weight: 1, description: "Chart pattern tespiti" },
  { id: "candle", name: "Mum Formasyon", nameEn: "Candlestick", multiplier: 0.9, enabled: true, weight: 1, description: "Candlestick pattern" },
  { id: "cot", name: "COT Raporu", nameEn: "COT Report", multiplier: 0.75, enabled: true, weight: 2, description: "Institutional positioning" },
  { id: "sr", name: "S/R Analizi", nameEn: "S/R Analysis", multiplier: 1.1, enabled: true, weight: 2, description: "Support/Resistance" },
  { id: "news", name: "Haber", nameEn: "News Sentiment", multiplier: 0.95, enabled: true, weight: 1, description: "Gold news sentiment" },
  { id: "regime", name: "Market Regime", nameEn: "Market Regime", multiplier: 0.8, enabled: true, weight: 2, description: "Trending/Ranging" },
];

type Props = {
  baseConfidence: number;
  symbol?: string;
  onFactorsChange?: (factors: Factor[], finalConfidence: number) => void;
  locale?: string;
};

export default function MLFactorPanel({ baseConfidence, symbol = "NDX.INDX", onFactorsChange, locale = "tr" }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [factors, setFactors] = useState<Factor[]>(DEFAULT_FACTORS);
  const [liveConfidence, setLiveConfidence] = useState(baseConfidence);
  const [isLoading, setIsLoading] = useState(false);
  const [lastPrediction, setLastPrediction] = useState<PredictionData | null>(null);

  const calculateWeightedConfidence = useCallback((factorList: Factor[], base: number): number => {
    const activeFactors = factorList.filter(f => f.enabled);
    if (activeFactors.length === 0) return base;

    // Sort by impact (furthest from 1.0) and weight
    const sorted = [...activeFactors].sort((a, b) => {
      const impactA = Math.abs(1 - a.multiplier) * a.weight;
      const impactB = Math.abs(1 - b.multiplier) * b.weight;
      return impactB - impactA;
    });

    // Take top 4 most impactful
    const top4 = sorted.slice(0, 4);

    // Weighted average calculation
    let weightedSum = 0;
    let totalWeight = 0;

    for (const f of top4) {
      weightedSum += f.multiplier * f.weight;
      totalWeight += f.weight;
    }

    const avgMultiplier = totalWeight > 0 ? weightedSum / totalWeight : 1.0;
    const clampedMultiplier = Math.max(0.5, Math.min(1.3, avgMultiplier));
    const finalConfidence = Math.max(30, Math.min(95, base * clampedMultiplier));

    return finalConfidence;
  }, []);

  // Fetch real prediction from backend with enabled factors
  const fetchWithFactors = useCallback(async () => {
    const enabledFactors = factors.filter(f => f.enabled).map(f => f.id);
    if (enabledFactors.length === 0) {
      setLiveConfidence(baseConfidence);
      return;
    }
    
    setIsLoading(true);
    try {
      const prediction = await fetchPredictionWithFactors(symbol, enabledFactors);
      setLastPrediction(prediction);
      setLiveConfidence(prediction.confidence);
      onFactorsChange?.(factors, prediction.confidence);
    } catch (err) {
      console.error("Factor prediction fetch failed:", err);
      // Fallback to local calculation
      const newConfidence = calculateWeightedConfidence(factors, baseConfidence);
      setLiveConfidence(newConfidence);
    } finally {
      setIsLoading(false);
    }
  }, [factors, symbol, baseConfidence, calculateWeightedConfidence, onFactorsChange]);

  // Initial calculation (local) on factor change
  useEffect(() => {
    const newConfidence = calculateWeightedConfidence(factors, baseConfidence);
    setLiveConfidence(newConfidence);
  }, [factors, baseConfidence, calculateWeightedConfidence]);

  const toggleFactor = (id: string) => {
    setFactors(prev => prev.map(f => 
      f.id === id ? { ...f, enabled: !f.enabled } : f
    ));
  };

  const resetFactors = () => {
    setFactors(DEFAULT_FACTORS);
  };

  const getMultiplierColor = (mult: number) => {
    if (mult > 1.05) return "text-success";
    if (mult < 0.95) return "text-danger";
    return "text-textSecondary";
  };

  const getWeightBadge = (weight: 1 | 2 | 3) => {
    const colors = {
      1: "bg-blue-500/20 text-blue-400",
      2: "bg-yellow-500/20 text-yellow-400",
      3: "bg-red-500/20 text-red-400",
    };
    const labels = { 1: "Low", 2: "Med", 3: "High" };
    return (
      <span className={`text-[10px] px-1.5 py-0.5 rounded ${colors[weight]}`}>
        {labels[weight]}
      </span>
    );
  };

  const activeCount = factors.filter(f => f.enabled).length;
  const confidenceChange = liveConfidence - baseConfidence;

  return (
    <>
      {/* Toggle Button - Fixed position */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed top-20 right-4 z-40 flex items-center gap-2 px-3 py-2 rounded-lg 
          ${isOpen ? "bg-accent text-white" : "bg-white/10 hover:bg-white/20"} 
          transition-all duration-200 shadow-lg backdrop-blur-sm border border-white/10`}
      >
        <Settings2 className="w-4 h-4" />
        <span className="text-sm font-medium">ML Faktörler</span>
        <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded-full">{activeCount}/9</span>
        <ChevronRight className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Sliding Panel */}
      <div
        className={`fixed top-16 right-0 h-[calc(100vh-4rem)] w-80 bg-background/95 backdrop-blur-xl 
          border-l border-white/10 shadow-2xl z-30 transition-transform duration-300 ease-out
          ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div>
            <h3 className="font-semibold">ML Karar Faktörleri</h3>
            <p className="text-xs text-textSecondary mt-0.5">Aktif faktörleri seçin</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchWithFactors}
              disabled={isLoading}
              className="p-1.5 hover:bg-white/10 rounded-lg transition disabled:opacity-50"
              title="Backend'den Güncelle"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-accent animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 text-accent" />
              )}
            </button>
            <button
              onClick={resetFactors}
              className="p-1.5 hover:bg-white/10 rounded-lg transition"
              title="Sıfırla"
            >
              <RotateCcw className="w-4 h-4 text-textSecondary" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-white/10 rounded-lg transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Live Confidence Display */}
        <div className="p-4 border-b border-white/10 bg-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-textSecondary">Base Confidence</span>
            <span className="font-mono text-sm">{baseConfidence.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Final Confidence</span>
            <div className="flex items-center gap-2">
              <span className={`text-xs ${confidenceChange >= 0 ? "text-success" : "text-danger"}`}>
                {confidenceChange >= 0 ? "+" : ""}{confidenceChange.toFixed(1)}%
              </span>
              <span className={`font-mono text-lg font-bold ${
                liveConfidence >= 70 ? "text-success" : 
                liveConfidence >= 55 ? "text-yellow-400" : "text-danger"
              }`}>
                {liveConfidence.toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                liveConfidence >= 70 ? "bg-success" : 
                liveConfidence >= 55 ? "bg-yellow-400" : "bg-danger"
              }`}
              style={{ width: `${liveConfidence}%` }}
            />
          </div>
        </div>

        {/* Factor List */}
        <div className="overflow-y-auto h-[calc(100%-180px)] p-2">
          {factors.map((factor) => (
            <div
              key={factor.id}
              onClick={() => toggleFactor(factor.id)}
              className={`flex items-center gap-3 p-3 rounded-xl mb-2 cursor-pointer transition-all
                ${factor.enabled 
                  ? "bg-accent/10 border border-accent/30" 
                  : "bg-white/5 border border-transparent hover:bg-white/10"
                }`}
            >
              {/* Checkbox */}
              <div className={`w-5 h-5 rounded flex items-center justify-center border-2 transition-all
                ${factor.enabled 
                  ? "bg-accent border-accent" 
                  : "border-white/30"
                }`}
              >
                {factor.enabled && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>

              {/* Factor Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`font-medium text-sm ${factor.enabled ? "text-white" : "text-textSecondary"}`}>
                    {locale === "en" ? factor.nameEn : factor.name}
                  </span>
                  {getWeightBadge(factor.weight)}
                </div>
                <p className="text-xs text-textSecondary truncate mt-0.5">
                  {factor.description}
                </p>
              </div>

              {/* Multiplier */}
              <div className={`font-mono text-sm font-bold ${getMultiplierColor(factor.multiplier)}`}>
                ×{factor.multiplier.toFixed(2)}
              </div>
            </div>
          ))}
        </div>

        {/* Footer Info */}
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-white/10 bg-background/95">
          <p className="text-[10px] text-textSecondary text-center">
            💡 En etkili 4 faktör weighted average ile uygulanır (max 0.5-1.3x)
          </p>
        </div>
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-20 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
