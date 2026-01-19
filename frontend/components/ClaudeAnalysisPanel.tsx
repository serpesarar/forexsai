"use client";

import { useAIAnalysis } from "../lib/api/aiAnalysis";
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  RefreshCw,
  Sparkles,
  Shield,
  Target,
  Scale
} from "lucide-react";
import { useState } from "react";
import { useI18nStore } from "../lib/i18n/store";

type Props = {
  symbol: string;
  symbolLabel: string;
};

function DirectionBadge({ direction, isClaudeDecision }: { direction: string; isClaudeDecision?: boolean }) {
  const config = {
    BUY: { bg: "bg-success/20", text: "text-success", icon: TrendingUp, label: "ALIŞ" },
    SELL: { bg: "bg-danger/20", text: "text-danger", icon: TrendingDown, label: "SATIŞ" },
    HOLD: { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, label: "BEKLE" },
  }[direction] || { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, label: direction };

  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}>
      {isClaudeDecision && <Brain className="w-4 h-4 text-accent" />}
      <Icon className={`w-4 h-4 ${config.text}`} />
      <span className={`text-sm font-semibold ${config.text}`}>{config.label}</span>
    </div>
  );
}

function AgreementBadge({ agreement }: { agreement: boolean }) {
  return agreement ? (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-success/10 text-success">
      <CheckCircle2 className="w-4 h-4" />
      <span className="text-xs font-medium">MUTABIK</span>
    </div>
  ) : (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-warning/10 text-warning">
      <XCircle className="w-4 h-4" />
      <span className="text-xs font-medium">FARKLI GÖRÜŞ</span>
    </div>
  );
}

export default function ClaudeAnalysisPanel({ symbol, symbolLabel }: Props) {
  const [shouldFetch, setShouldFetch] = useState(false);
  const { data, isLoading, error, refetch } = useAIAnalysis(symbol, shouldFetch);
  const [expanded, setExpanded] = useState(false);
  const t = useI18nStore((s) => s.t);
  
  const handleAnalyze = () => {
    setShouldFetch(true);
    refetch();
  };

  return (
    <div className="glass-card p-8 space-y-6 rounded-2xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/30 to-pink-500/30">
            <Sparkles className="h-6 w-6 text-purple-400" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">{t("claudeAnalysis.title")}</p>
            <h3 className="text-xl font-bold">{symbolLabel}</h3>
          </div>
        </div>
        <button
          onClick={handleAnalyze}
          className="px-4 py-2 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 transition flex items-center gap-2"
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""} text-purple-400`} />
          <span className="text-sm text-purple-400 font-medium">
            {isLoading ? t("claudeAnalysis.analyzing") : shouldFetch && data ? t("claudeAnalysis.refresh") : t("claudeAnalysis.analyze")}
          </span>
        </button>
      </div>

      {!shouldFetch && !data ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Brain className="w-12 h-12 text-purple-400/50 mb-4" />
          <p className="text-textSecondary text-sm mb-2">{t("claudeAnalysis.ready")}</p>
          <p className="text-textSecondary/70 text-xs">{t("claudeAnalysis.apiSaving")}</p>
        </div>
      ) : isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-12 w-full rounded-xl" />
          <div className="skeleton h-24 w-full rounded-xl" />
          <div className="skeleton h-16 w-full rounded-xl" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 bg-danger/10 rounded-xl text-danger">
          <AlertTriangle className="w-5 h-5" />
          <span className="text-sm">{t("claudeAnalysis.error")}</span>
        </div>
      ) : data ? (
        <>
          {/* ML vs Claude Comparison */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white/5 rounded-2xl p-5 text-center border border-white/5">
              <p className="text-xs uppercase text-textSecondary mb-3 tracking-wider">ML MODEL</p>
              <DirectionBadge direction={data.ml_prediction.direction} />
              <p className="text-sm text-textSecondary mt-3 font-medium">{data.ml_prediction.confidence.toFixed(0)}% {t("mlPrediction.confidence")}</p>
            </div>
            
            <div className="bg-white/5 rounded-2xl p-5 flex flex-col items-center justify-center border border-white/5">
              <AgreementBadge agreement={data.claude_analysis.agreement} />
              <p className="text-xs text-textSecondary mt-3">
                {data.claude_analysis.agreement ? t("claudeAnalysis.agreement") : t("claudeAnalysis.disagreement")}
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl p-5 text-center border border-purple-500/20">
              <p className="text-xs uppercase text-purple-400 mb-3 tracking-wider">CLAUDE AI</p>
              <DirectionBadge direction={data.claude_analysis.claude_direction} isClaudeDecision />
              <p className="text-sm text-textSecondary mt-3 font-medium">{data.claude_analysis.claude_confidence.toFixed(0)}% {t("mlPrediction.confidence")}</p>
            </div>
          </div>

          {/* Position Recommendation */}
          <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-accent" />
              <span className="text-sm text-textSecondary">{t("claudeAnalysis.recommendation")}</span>
            </div>
            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${
              data.claude_analysis.position_size_suggestion === "No Trade" 
                ? "bg-danger/20 text-danger"
                : data.claude_analysis.position_size_suggestion === "Large"
                ? "bg-success/20 text-success"
                : data.claude_analysis.position_size_suggestion === "Medium"
                ? "bg-accent/20 text-accent"
                : "bg-warning/20 text-warning"
            }`}>
              {data.claude_analysis.position_size_suggestion === "No Trade" ? "İşlem Yapma" :
               data.claude_analysis.position_size_suggestion === "Large" ? "Büyük" :
               data.claude_analysis.position_size_suggestion === "Medium" ? "Orta" : "Küçük"}
            </span>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-success/5 rounded-xl p-3 border border-success/10">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-success" />
                <p className="text-xs font-medium text-success">{t("common.bullish")}</p>
              </div>
              <ul className="space-y-1">
                {data.claude_analysis.strengths.slice(0, 3).map((s, i) => (
                  <li key={i} className="text-xs text-textSecondary flex gap-1">
                    <span className="text-success">+</span>
                    <span className="line-clamp-2">{s}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="bg-danger/5 rounded-xl p-3 border border-danger/10">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-danger" />
                <p className="text-xs font-medium text-danger">{t("claudeAnalysis.riskAssessment")}</p>
              </div>
              <ul className="space-y-1">
                {data.claude_analysis.weaknesses.slice(0, 3).map((w, i) => (
                  <li key={i} className="text-xs text-textSecondary flex gap-1">
                    <span className="text-danger">-</span>
                    <span className="line-clamp-2">{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Price Levels */}
          <div className="bg-white/5 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-accent" />
              <p className="text-xs font-medium">{t("claudeAnalysis.recommendation")}</p>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-[10px] text-textSecondary">Entry</p>
                <p className="text-sm font-mono">{data.claude_analysis.recommended_entry.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-[10px] text-success">Take Profit</p>
                <p className="text-sm font-mono text-success">{data.claude_analysis.recommended_tp.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-[10px] text-danger">Stop Loss</p>
                <p className="text-sm font-mono text-danger">{data.claude_analysis.recommended_sl.toFixed(2)}</p>
              </div>
            </div>
          </div>

          {/* Expandable Assessment */}
          <div>
            <button
              onClick={() => setExpanded(!expanded)}
              className="w-full text-left p-3 bg-white/5 rounded-xl hover:bg-white/10 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-accent" />
                  <span className="text-xs font-medium">{t("claudeAnalysis.reasoning")}</span>
                </div>
                <span className="text-xs text-textSecondary">{expanded ? t("claudeAnalysis.showLess") : t("claudeAnalysis.showMore")}</span>
              </div>
            </button>
            
            {expanded && (
              <div className="mt-2 p-3 bg-white/5 rounded-xl text-xs text-textSecondary leading-relaxed max-h-48 overflow-auto">
                {data.claude_analysis.general_assessment}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between text-[10px] text-textSecondary pt-2 border-t border-white/5">
            <span className="flex items-center gap-1">
              <Brain className="w-3 h-3" />
              {data.claude_analysis.model_used}
            </span>
            <span>{new Date(data.claude_analysis.timestamp).toLocaleTimeString("tr-TR")}</span>
          </div>
        </>
      ) : null}
    </div>
  );
}
