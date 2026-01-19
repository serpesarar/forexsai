"use client";

import { usePrediction } from "../lib/api/prediction";
import { TrendingUp, TrendingDown, Minus, Target, AlertTriangle, Activity, RefreshCw, HelpCircle, X, Zap } from "lucide-react";
import { useState } from "react";
import { useI18nStore } from "../lib/i18n/store";

// Golden Ratio
const PHI = 1.618;

type Props = {
  symbol: string;
  symbolLabel: string;
  compact?: boolean;
};

function DirectionBadge({ direction, confidence, t }: { direction: string; confidence: number; t: (key: string) => string }) {
  const config = {
    BUY: { bg: "bg-success/20", text: "text-success", icon: TrendingUp, labelKey: "directions.buy", border: "border-success/30" },
    SELL: { bg: "bg-danger/20", text: "text-danger", icon: TrendingDown, labelKey: "directions.sell", border: "border-danger/30" },
    HOLD: { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, labelKey: "directions.hold", border: "border-white/10" },
  }[direction] || { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, labelKey: direction, border: "border-white/10" };

  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-4 px-6 py-5 rounded-2xl border ${config.bg} ${config.border}`}>
      <div className={`flex h-14 w-14 items-center justify-center rounded-xl ${config.bg}`}>
        <Icon className={`w-8 h-8 ${config.text}`} />
      </div>
      <div>
        <p className={`text-2xl font-bold ${config.text}`}>{t(config.labelKey)}</p>
        <p className="text-sm text-textSecondary mt-1">{t("mlPrediction.confidence")}: {confidence.toFixed(0)}%</p>
      </div>
      <div className="ml-auto">
        <Zap className={`w-6 h-6 ${config.text} opacity-50`} />
      </div>
    </div>
  );
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-textSecondary font-medium">{label}</span>
        <span className="font-bold">{value.toFixed(0)}%</span>
      </div>
      <div className="h-3 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function PriceTarget({ label, price, pips, type }: { label: string; price: number; pips: number; type: "target" | "stop" | "entry" }) {
  const colors = {
    target: "text-success",
    stop: "text-danger",
    entry: "text-white",
  };
  
  const bgColors = {
    target: "bg-success/10",
    stop: "bg-danger/10",
    entry: "bg-white/5",
  };

  return (
    <div className={`flex justify-between items-center py-3 px-4 rounded-xl ${bgColors[type]} mb-2 last:mb-0`}>
      <span className="text-textSecondary font-medium">{label}</span>
      <div className="text-right flex items-center gap-3">
        <span className={`font-mono text-lg font-bold ${colors[type]}`}>{price.toFixed(2)}</span>
        {pips > 0 && (
          <span className="text-xs text-textSecondary bg-white/10 px-2 py-1 rounded-full">{pips.toFixed(0)} pips</span>
        )}
      </div>
    </div>
  );
}

export default function MLPredictionPanel({ symbol, symbolLabel }: Props) {
  const { data, isLoading, error, refetch } = usePrediction(symbol);
  const [showGuide, setShowGuide] = useState(false);
  const t = useI18nStore((s) => s.t);

  return (
    <>
      {/* Simple Guide Modal */}
      {showGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowGuide(false)}>
          <div className="bg-background border border-white/10 rounded-2xl p-6 max-w-md mx-4 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{t("mlPrediction.guide")}</h3>
              <button onClick={() => setShowGuide(false)} className="p-1 hover:bg-white/10 rounded-full">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-sm text-textSecondary">
              <p><strong className="text-white">BUY:</strong> Model yukarı hareket bekliyor</p>
              <p><strong className="text-white">SELL:</strong> Model aşağı hareket bekliyor</p>
              <p><strong className="text-white">HOLD:</strong> Belirsiz, bekleyin</p>
              <p><strong className="text-white">Target Pips:</strong> ATR bazlı kar hedefi</p>
              <p><strong className="text-white">R/R:</strong> Risk/Reward oranı (1.5+ önerilir)</p>
              <p className="text-xs mt-4 p-3 bg-white/5 rounded-lg">💡 %70+ güvenle işlem açın. Yüksek volatilitede pozisyon küçültün.</p>
            </div>
          </div>
        </div>
      )}
      <div className="glass-card p-8 space-y-6 rounded-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent/30 to-blue-500/30">
              <Zap className="h-6 w-6 text-accent" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("mlPrediction.title")}</p>
              <h3 className="mt-1 text-xl font-bold">{symbolLabel}</h3>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowGuide(true)}
              className="p-2 rounded-full hover:bg-white/10 transition"
              aria-label="Tahmin rehberi"
            >
              <HelpCircle className="w-4 h-4 text-textSecondary" />
            </button>
            <button
              onClick={() => refetch()}
              className="p-2 rounded-full hover:bg-white/10 transition"
              aria-label="Yenile"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            <div className="skeleton h-16 w-full rounded-xl" />
            <div className="skeleton h-24 w-full rounded-xl" />
            <div className="skeleton h-20 w-full rounded-xl" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 p-4 bg-danger/10 rounded-xl text-danger">
            <AlertTriangle className="w-5 h-5" />
            <span className="text-sm">{t("mlPrediction.noData")}</span>
          </div>
        ) : data ? (
          <>
            {/* Direction & Confidence */}
            <div className="grid grid-cols-2 gap-4">
              <DirectionBadge direction={data.direction} confidence={data.confidence} t={t} />
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-xs text-textSecondary mb-2">{t("common.confidence")}</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-success">{t("common.bullish")}</span>
                      <span>{data.probability_up.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full">
                      <div className="h-2 bg-success rounded-full" style={{ width: `${data.probability_up}%` }} />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-danger">{t("common.bearish")}</span>
                      <span>{data.probability_down.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full">
                      <div className="h-2 bg-danger rounded-full" style={{ width: `${data.probability_down}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Price Targets */}
            <div className="bg-white/5 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-accent" />
                <p className="text-sm font-medium">{t("mlPrediction.target")}</p>
                <span className="ml-auto text-xs text-textSecondary px-2 py-1 bg-white/10 rounded-full">
                  RR: {data.risk_reward.toFixed(2)}
                </span>
              </div>
              <div className="space-y-1">
                <PriceTarget label={t("mlPrediction.entry")} price={data.entry_price} pips={0} type="entry" />
                <PriceTarget label={t("mlPrediction.target")} price={data.target_price} pips={data.target_pips} type="target" />
                <PriceTarget label={t("mlPrediction.stopLoss")} price={data.stop_price} pips={data.stop_pips} type="stop" />
              </div>
            </div>

            {/* Scores */}
            <div className="bg-white/5 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-accent" />
                <p className="text-sm font-medium">{t("mlPrediction.modelScore")}</p>
                <span className="ml-auto text-xs text-textSecondary px-2 py-1 bg-white/10 rounded-full">
                  Vol: {data.volatility_regime}
                </span>
              </div>
              <div className="space-y-3">
                <ScoreBar label="Teknik" value={data.technical_score} color="bg-accent" />
                <ScoreBar label="Momentum" value={data.momentum_score} color="bg-success" />
                <ScoreBar label="Trend" value={data.trend_score} color="bg-blue-500" />
              </div>
            </div>

            {/* Key Levels */}
            {data.key_levels && data.key_levels.length > 0 && (
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-sm font-medium mb-3">{t("common.support")}/{t("common.resistance")}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {data.key_levels.slice(0, 4).map((level) => (
                    <div key={level.type} className="flex justify-between p-2 bg-white/5 rounded-lg">
                      <span className="text-textSecondary">{level.type}</span>
                      <span className="font-mono">{level.price.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reasoning */}
            <div className="space-y-2">
              <p className="text-xs text-textSecondary uppercase tracking-wider">{t("claudeAnalysis.reasoning")}</p>
              <ul className="space-y-1.5 text-sm text-textSecondary max-h-32 overflow-auto">
                {data.reasoning.slice(0, 5).map((reason, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-accent">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between text-xs text-textSecondary pt-3 border-t border-white/10">
              <span>Model: {data.model_version}</span>
              <span>{new Date(data.timestamp).toLocaleTimeString("tr-TR")}</span>
            </div>
          </>
        ) : null}
      </div>
    </>
  );
}
