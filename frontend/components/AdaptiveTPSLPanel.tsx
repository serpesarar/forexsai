"use client";

import { useState } from "react";
import {
  Target,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  Layers,
  AlertTriangle,
  CheckCircle2,
  Brain,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Zap,
} from "lucide-react";
import { useAdaptiveTPSL, useTPSuccessAnalysis, useFailurePatterns } from "../lib/api/learning";
import { useI18nStore } from "../lib/i18n/store";

interface AdaptiveTPSLPanelProps {
  symbol: string;
  direction: "BUY" | "SELL";
  entryPrice: number;
  symbolLabel?: string;
}

export default function AdaptiveTPSLPanel({
  symbol,
  direction,
  entryPrice,
  symbolLabel,
}: AdaptiveTPSLPanelProps) {
  const t = useI18nStore((s) => s.t);
  const [showFibLevels, setShowFibLevels] = useState(false);
  const [showFailurePatterns, setShowFailurePatterns] = useState(false);

  const { data: adaptive, isLoading, error, refetch } = useAdaptiveTPSL(
    symbol,
    direction,
    entryPrice,
    entryPrice > 0
  );

  const { data: tpAnalysis } = useTPSuccessAnalysis(symbol, 7);
  const { data: failureData } = useFailurePatterns(symbol, direction, 10);

  if (!entryPrice || entryPrice <= 0) {
    return (
      <div className="glass-card p-6 rounded-2xl">
        <div className="flex items-center gap-3 text-textSecondary">
          <Target className="w-5 h-5" />
          <span className="text-sm">Enter a position to see adaptive TP/SL levels</span>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin text-accent" />
          <span className="text-sm text-textSecondary">Calculating adaptive levels...</span>
        </div>
        <div className="space-y-2">
          <div className="skeleton h-8 w-full rounded-lg" />
          <div className="skeleton h-8 w-full rounded-lg" />
          <div className="skeleton h-8 w-full rounded-lg" />
        </div>
      </div>
    );
  }

  if (error || !adaptive) {
    return (
      <div className="glass-card p-6 rounded-2xl">
        <div className="flex items-center gap-3 text-danger">
          <AlertTriangle className="w-5 h-5" />
          <span className="text-sm">Failed to calculate adaptive levels</span>
        </div>
      </div>
    );
  }

  const isBuy = direction === "BUY";
  const priceDiff = (price: number) => {
    const diff = price - entryPrice;
    const pips = Math.abs(diff) * (symbol.includes("XAU") ? 10 : 100);
    return { diff, pips: pips.toFixed(0), isPositive: isBuy ? diff > 0 : diff < 0 };
  };

  return (
    <div className="glass-card p-6 rounded-2xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
            isBuy ? "bg-success/20" : "bg-danger/20"
          }`}>
            <Brain className={`h-5 w-5 ${isBuy ? "text-success" : "text-danger"}`} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-textSecondary">
              Adaptive TP/SL
            </p>
            <h3 className="text-lg font-bold">{symbolLabel || symbol}</h3>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1.5 rounded-full text-xs font-semibold ${
            isBuy ? "bg-success/20 text-success" : "bg-danger/20 text-danger"
          }`}>
            {direction}
          </div>
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg hover:bg-white/10 transition"
          >
            <RefreshCw className="w-4 h-4 text-textSecondary" />
          </button>
        </div>
      </div>

      {/* Confidence */}
      <div className="bg-white/5 rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-textSecondary">Confidence</span>
          <span className={`text-lg font-bold ${
            adaptive.confidence > 70 ? "text-success" :
            adaptive.confidence > 50 ? "text-warning" : "text-danger"
          }`}>
            {adaptive.confidence.toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              adaptive.confidence > 70 ? "bg-success" :
              adaptive.confidence > 50 ? "bg-warning" : "bg-danger"
            }`}
            style={{ width: `${adaptive.confidence}%` }}
          />
        </div>
      </div>

      {/* Price Levels */}
      <div className="space-y-2">
        {/* Entry */}
        <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium">Entry</span>
          </div>
          <span className="font-mono text-sm">{adaptive.entry.toFixed(2)}</span>
        </div>

        {/* TP1 */}
        <div className="flex items-center justify-between p-3 bg-success/10 rounded-xl border border-success/20">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-success" />
            <span className="text-sm font-medium text-success">TP1</span>
            {tpAnalysis?.tp_analysis?.tp1 && (
              <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
                {tpAnalysis.tp_analysis.tp1.success_rate.toFixed(0)}% hit rate
              </span>
            )}
          </div>
          <div className="text-right">
            <span className="font-mono text-sm text-success">{adaptive.tp1.toFixed(2)}</span>
            <span className="text-xs text-textSecondary ml-2">+{priceDiff(adaptive.tp1).pips} pips</span>
          </div>
        </div>

        {/* TP2 */}
        <div className="flex items-center justify-between p-3 bg-success/10 rounded-xl border border-success/20">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-success" />
            <span className="text-sm font-medium text-success">TP2</span>
            {tpAnalysis?.tp_analysis?.tp2 && (
              <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
                {tpAnalysis.tp_analysis.tp2.success_rate.toFixed(0)}% hit rate
              </span>
            )}
          </div>
          <div className="text-right">
            <span className="font-mono text-sm text-success">{adaptive.tp2.toFixed(2)}</span>
            <span className="text-xs text-textSecondary ml-2">+{priceDiff(adaptive.tp2).pips} pips</span>
          </div>
        </div>

        {/* TP3 */}
        <div className="flex items-center justify-between p-3 bg-success/10 rounded-xl border border-success/20">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-success" />
            <span className="text-sm font-medium text-success">TP3</span>
            {tpAnalysis?.tp_analysis?.tp3 && (
              <span className="text-xs bg-success/20 text-success px-2 py-0.5 rounded-full">
                {tpAnalysis.tp_analysis.tp3.success_rate.toFixed(0)}% hit rate
              </span>
            )}
          </div>
          <div className="text-right">
            <span className="font-mono text-sm text-success">{adaptive.tp3.toFixed(2)}</span>
            <span className="text-xs text-textSecondary ml-2">+{priceDiff(adaptive.tp3).pips} pips</span>
          </div>
        </div>

        {/* Stop Loss */}
        <div className="flex items-center justify-between p-3 bg-danger/10 rounded-xl border border-danger/20">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-danger" />
            <span className="text-sm font-medium text-danger">Stop Loss</span>
          </div>
          <div className="text-right">
            <span className="font-mono text-sm text-danger">{adaptive.stop_loss.toFixed(2)}</span>
            <span className="text-xs text-textSecondary ml-2">-{priceDiff(adaptive.stop_loss).pips} pips</span>
          </div>
        </div>
      </div>

      {/* Key Levels (S/R) */}
      {adaptive.key_levels.length > 0 && (
        <div className="bg-white/5 rounded-xl p-4">
          <p className="text-xs uppercase tracking-wider text-textSecondary mb-3">Key Levels</p>
          <div className="grid grid-cols-2 gap-2">
            {adaptive.key_levels.map((level, i) => (
              <div
                key={i}
                className={`flex items-center justify-between p-2 rounded-lg ${
                  level.type === "resistance" ? "bg-danger/10" : "bg-success/10"
                }`}
              >
                <span className={`text-xs ${
                  level.type === "resistance" ? "text-danger" : "text-success"
                }`}>
                  {level.type === "resistance" ? "R" : "S"}
                </span>
                <span className="font-mono text-xs">{level.price.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fibonacci Levels (Collapsible) */}
      {Object.keys(adaptive.fib_levels).length > 0 && (
        <div className="border border-white/10 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowFibLevels(!showFibLevels)}
            className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 transition"
          >
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-medium">Fibonacci Levels</span>
            </div>
            {showFibLevels ? (
              <ChevronUp className="w-4 h-4 text-textSecondary" />
            ) : (
              <ChevronDown className="w-4 h-4 text-textSecondary" />
            )}
          </button>
          {showFibLevels && (
            <div className="p-3 space-y-1 bg-white/5">
              {Object.entries(adaptive.fib_levels)
                .sort((a, b) => parseFloat(a[0]) - parseFloat(b[0]))
                .map(([level, price]) => (
                  <div
                    key={level}
                    className="flex items-center justify-between py-1 px-2 rounded-lg hover:bg-white/5"
                  >
                    <span className={`text-xs ${
                      level === "0.618" || level === "0.764" ? "text-purple-400 font-semibold" : "text-textSecondary"
                    }`}>
                      Fib {level}
                    </span>
                    <span className="font-mono text-xs">{price.toFixed(2)}</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Reasoning */}
      {adaptive.reasoning.length > 0 && (
        <div className="bg-white/5 rounded-xl p-4">
          <p className="text-xs uppercase tracking-wider text-textSecondary mb-3">Analysis</p>
          <ul className="space-y-1.5">
            {adaptive.reasoning.map((reason, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-textSecondary">
                <Zap className="w-3 h-3 mt-0.5 text-accent flex-shrink-0" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Learned Adjustments */}
      {adaptive.learned_adjustments.adjustments.length > 0 && (
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-purple-400" />
            <p className="text-xs uppercase tracking-wider text-purple-400">
              Learned from {adaptive.learned_adjustments.total_analyzed} failures
            </p>
          </div>
          <ul className="space-y-2">
            {adaptive.learned_adjustments.adjustments.map((adj, i) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-purple-400" />
                <div>
                  <span className="text-xs text-white">{adj.action}</span>
                  <span className="text-xs text-purple-400 ml-2">({adj.frequency})</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Failure Patterns (Collapsible) */}
      {failureData && failureData.count > 0 && (
        <div className="border border-white/10 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowFailurePatterns(!showFailurePatterns)}
            className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 transition"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <span className="text-sm font-medium">Failure Patterns ({failureData.count})</span>
            </div>
            {showFailurePatterns ? (
              <ChevronUp className="w-4 h-4 text-textSecondary" />
            ) : (
              <ChevronDown className="w-4 h-4 text-textSecondary" />
            )}
          </button>
          {showFailurePatterns && (
            <div className="p-3 space-y-2 bg-white/5">
              {Object.entries(failureData.reason_stats)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([reason, count]) => (
                  <div
                    key={reason}
                    className="flex items-center justify-between py-1 px-2 rounded-lg bg-white/5"
                  >
                    <span className="text-xs text-textSecondary">{reason.replace(/_/g, " ")}</span>
                    <span className="text-xs font-semibold text-warning">{count}x</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Optimal TP Recommendation */}
      {tpAnalysis?.optimal_tp && (
        <div className="bg-accent/10 border border-accent/20 rounded-xl p-3">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-accent" />
            <span className="text-xs text-accent">
              Optimal target: <span className="font-semibold">{tpAnalysis.optimal_tp.toUpperCase()}</span>
              {" "}based on historical success
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
