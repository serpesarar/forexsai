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
  Scale,
  Clock
} from "lucide-react";
import { useState, useEffect } from "react";
import { useI18nStore } from "../lib/i18n/store";
import { useClaudeAnalysisStore } from "../lib/claudeAnalysisStore";

type Props = {
  symbol: string;
  symbolLabel: string;
};

const neonDir: Record<string, { color: string; glow: string }> = {
  BUY: { color: "#00ff88", glow: "rgba(0,255,136,0.15)" },
  SELL: { color: "#ff3366", glow: "rgba(255,51,102,0.15)" },
  HOLD: { color: "#f0b429", glow: "rgba(240,180,41,0.15)" },
};

function DirectionBadge({ direction, isClaudeDecision, t }: { direction: string; isClaudeDecision?: boolean; t: (key: string) => string }) {
  const nd = neonDir[direction] || neonDir.HOLD;
  const Icon = direction === "BUY" ? TrendingUp : direction === "SELL" ? TrendingDown : Minus;
  const label = direction === "BUY" ? t("directions.buy") : direction === "SELL" ? t("directions.sell") : t("directions.hold");

  return (
    <div className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg font-mono" style={{ background: `${nd.color}12`, border: `1px solid ${nd.color}25` }}>
      {isClaudeDecision && <Brain className="w-4 h-4" style={{ color: "#818cf8" }} />}
      <Icon className="w-4 h-4" style={{ color: nd.color, filter: `drop-shadow(0 0 4px ${nd.color})` }} />
      <span className="text-sm font-bold" style={{ color: nd.color }}>{label}</span>
    </div>
  );
}

function AgreementBadge({ agreement, t }: { agreement: boolean; t: (key: string) => string }) {
  return agreement ? (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.15)" }}>
      <CheckCircle2 className="w-4 h-4" style={{ color: "#00ff88" }} />
      <span className="text-xs font-mono font-medium" style={{ color: "#00ff88" }}>{t("claudeAnalysis.agreed")}</span>
    </div>
  ) : (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.15)" }}>
      <XCircle className="w-4 h-4" style={{ color: "#ff3366" }} />
      <span className="text-xs font-mono font-medium" style={{ color: "#ff3366" }}>{t("claudeAnalysis.different")}</span>
    </div>
  );
}

export default function ClaudeAnalysisPanel({ symbol, symbolLabel }: Props) {
  const [shouldFetch, setShouldFetch] = useState(false);
  const { data: fetchedData, isLoading, error, refetch } = useAIAnalysis(symbol, shouldFetch);
  const [expanded, setExpanded] = useState(false);
  const { t, locale } = useI18nStore();
  const { getAnalysis, setAnalysis, getLastUpdated } = useClaudeAnalysisStore();
  
  // Get persisted data
  const persistedData = getAnalysis(symbol);
  const lastUpdated = getLastUpdated(symbol);
  
  // Use fetched data if available, otherwise use persisted data
  const data = fetchedData || persistedData;
  
  // Persist new data when fetched
  useEffect(() => {
    if (fetchedData) {
      setAnalysis(symbol, fetchedData);
    }
  }, [fetchedData, symbol, setAnalysis]);
  
  const handleAnalyze = () => {
    setShouldFetch(true);
    refetch();
  };

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(2,6,23,0.85)", border: "1px solid rgba(255,255,255,0.06)", boxShadow: "0 0 40px rgba(129,140,248,0.10), inset 0 1px 0 rgba(255,255,255,0.04)" }}>
      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between" style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(129,140,248,0.15)", boxShadow: "0 0 16px rgba(129,140,248,0.3)" }}>
            <Sparkles className="w-5 h-5" style={{ color: "#818cf8" }} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{t("claudeAnalysis.title")}</p>
            <h3 className="text-base font-bold font-mono text-white/90">{symbolLabel}</h3>
          </div>
        </div>
        <button
          onClick={handleAnalyze}
          className="px-4 py-2 rounded-xl flex items-center gap-2 transition-all hover:brightness-125"
          style={{ background: "rgba(129,140,248,0.12)", border: "1px solid rgba(129,140,248,0.2)" }}
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} style={{ color: "#818cf8" }} />
          <span className="text-sm font-mono font-medium" style={{ color: "#818cf8" }}>
            {isLoading ? t("claudeAnalysis.analyzing") : shouldFetch && data ? t("claudeAnalysis.refresh") : t("claudeAnalysis.analyze")}
          </span>
        </button>
      </div>

      <div className="p-5 space-y-4">
        {/* Show last updated time if we have persisted data */}
        {lastUpdated && data && !isLoading && (
          <div className="flex items-center gap-2 text-[10px] font-mono px-3 py-2 rounded-lg" style={{ background: "rgba(255,255,255,0.03)", color: "rgba(255,255,255,0.3)" }}>
            <Clock className="w-3 h-3" />
            <span>{t("claudeAnalysis.lastAnalysis")}: {new Date(lastUpdated).toLocaleString(locale === "en" ? "en-US" : "tr-TR")}</span>
          </div>
        )}

        {!data && !isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Brain className="w-12 h-12 mb-4 opacity-30" style={{ color: "#818cf8" }} />
            <p className="text-sm font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>{t("claudeAnalysis.ready")}</p>
            <p className="text-xs font-mono mt-1" style={{ color: "rgba(255,255,255,0.2)" }}>{t("claudeAnalysis.apiSaving")}</p>
          </div>
        ) : isLoading ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-12 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
            <div className="h-24 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
            <div className="h-16 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 p-4 rounded-xl" style={{ background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.15)" }}>
            <AlertTriangle className="w-5 h-5" style={{ color: "#ff3366" }} />
            <span className="text-sm font-mono" style={{ color: "#ff3366" }}>{t("claudeAnalysis.error")}</span>
          </div>
        ) : data ? (
          <>
            {/* ML vs Claude Comparison */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl p-4 text-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <p className="text-[9px] uppercase tracking-widest font-mono mb-3" style={{ color: "rgba(255,255,255,0.3)" }}>ML MODEL</p>
                <DirectionBadge direction={data.ml_prediction.direction} t={t} />
                <p className="text-[10px] font-mono mt-3" style={{ color: "rgba(255,255,255,0.35)" }}>{data.ml_prediction.confidence.toFixed(0)}% {t("mlPrediction.confidence")}</p>
              </div>
              
              <div className="rounded-xl p-4 flex flex-col items-center justify-center" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <AgreementBadge agreement={data.claude_analysis.agreement} t={t} />
                <p className="text-[10px] font-mono mt-3" style={{ color: "rgba(255,255,255,0.3)" }}>
                  {data.claude_analysis.agreement ? t("claudeAnalysis.agreement") : t("claudeAnalysis.disagreement")}
                </p>
              </div>
              
              <div className="rounded-xl p-4 text-center" style={{ background: "rgba(129,140,248,0.06)", border: "1px solid rgba(129,140,248,0.12)" }}>
                <p className="text-[9px] uppercase tracking-widest font-mono mb-3" style={{ color: "#818cf8" }}>CLAUDE AI</p>
                <DirectionBadge direction={data.claude_analysis.claude_direction} isClaudeDecision t={t} />
                <p className="text-[10px] font-mono mt-3" style={{ color: "rgba(255,255,255,0.35)" }}>{data.claude_analysis.claude_confidence.toFixed(0)}% {t("mlPrediction.confidence")}</p>
              </div>
            </div>

            {/* Position Recommendation */}
            <div className="flex items-center justify-between px-4 py-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4" style={{ color: "#00ccff" }} />
                <span className="text-xs font-mono" style={{ color: "rgba(255,255,255,0.4)" }}>{t("claudeAnalysis.recommendation")}</span>
              </div>
              <span className="text-xs font-bold font-mono px-3 py-1 rounded-full" style={{
                background: data.claude_analysis.position_size_suggestion === "No Trade" ? "rgba(255,51,102,0.12)" :
                  data.claude_analysis.position_size_suggestion === "Large" ? "rgba(0,255,136,0.12)" :
                  data.claude_analysis.position_size_suggestion === "Medium" ? "rgba(0,204,255,0.12)" : "rgba(240,180,41,0.12)",
                color: data.claude_analysis.position_size_suggestion === "No Trade" ? "#ff3366" :
                  data.claude_analysis.position_size_suggestion === "Large" ? "#00ff88" :
                  data.claude_analysis.position_size_suggestion === "Medium" ? "#00ccff" : "#f0b429",
                border: `1px solid ${data.claude_analysis.position_size_suggestion === "No Trade" ? "rgba(255,51,102,0.25)" :
                  data.claude_analysis.position_size_suggestion === "Large" ? "rgba(0,255,136,0.25)" :
                  data.claude_analysis.position_size_suggestion === "Medium" ? "rgba(0,204,255,0.25)" : "rgba(240,180,41,0.25)"}`,
              }}>
                {data.claude_analysis.position_size_suggestion === "No Trade" ? t("claudeAnalysis.positionSize.noTrade") :
                 data.claude_analysis.position_size_suggestion === "Large" ? t("claudeAnalysis.positionSize.large") :
                 data.claude_analysis.position_size_suggestion === "Medium" ? t("claudeAnalysis.positionSize.medium") : t("claudeAnalysis.positionSize.small")}
              </span>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-3" style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.10)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4" style={{ color: "#00ff88" }} />
                  <p className="text-xs font-mono font-bold" style={{ color: "#00ff88" }}>{t("common.bullish")}</p>
                </div>
                <ul className="space-y-1">
                  {data.claude_analysis.strengths.slice(0, 3).map((s, i) => (
                    <li key={i} className="text-[10px] font-mono flex gap-1" style={{ color: "rgba(255,255,255,0.4)" }}>
                      <span style={{ color: "#00ff88" }}>+</span>
                      <span className="line-clamp-2">{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="rounded-xl p-3" style={{ background: "rgba(255,51,102,0.04)", border: "1px solid rgba(255,51,102,0.10)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-4 h-4" style={{ color: "#ff3366" }} />
                  <p className="text-xs font-mono font-bold" style={{ color: "#ff3366" }}>{t("claudeAnalysis.riskAssessment")}</p>
                </div>
                <ul className="space-y-1">
                  {data.claude_analysis.weaknesses.slice(0, 3).map((w, i) => (
                    <li key={i} className="text-[10px] font-mono flex gap-1" style={{ color: "rgba(255,255,255,0.4)" }}>
                      <span style={{ color: "#ff3366" }}>-</span>
                      <span className="line-clamp-2">{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Price Levels */}
            <div className="rounded-xl p-4" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4" style={{ color: "#00ccff" }} />
                <p className="text-xs font-mono font-bold" style={{ color: "rgba(255,255,255,0.5)" }}>{t("claudeAnalysis.recommendation")}</p>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg p-2" style={{ background: "rgba(0,204,255,0.05)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>Entry</p>
                  <p className="text-sm font-mono font-bold text-white/80">{data.claude_analysis.recommended_entry.toFixed(2)}</p>
                </div>
                <div className="rounded-lg p-2" style={{ background: "rgba(0,255,136,0.05)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "#00ff88" }}>Take Profit</p>
                  <p className="text-sm font-mono font-bold" style={{ color: "#00ff88" }}>{data.claude_analysis.recommended_tp.toFixed(2)}</p>
                </div>
                <div className="rounded-lg p-2" style={{ background: "rgba(255,51,102,0.05)" }}>
                  <p className="text-[9px] font-mono" style={{ color: "#ff3366" }}>Stop Loss</p>
                  <p className="text-sm font-mono font-bold" style={{ color: "#ff3366" }}>{data.claude_analysis.recommended_sl.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Expandable Assessment */}
            <div>
              <button
                onClick={() => setExpanded(!expanded)}
                className="w-full text-left px-4 py-3 rounded-xl transition-all hover:brightness-125"
                style={{ background: "rgba(129,140,248,0.06)", border: "1px solid rgba(129,140,248,0.10)" }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4" style={{ color: "#818cf8" }} />
                    <span className="text-xs font-mono font-bold" style={{ color: "#818cf8" }}>{t("claudeAnalysis.reasoning")}</span>
                  </div>
                  <span className="text-[10px] font-mono" style={{ color: "rgba(255,255,255,0.3)" }}>{expanded ? t("claudeAnalysis.showLess") : t("claudeAnalysis.showMore")}</span>
                </div>
              </button>
              
              {expanded && (
                <div className="mt-2 p-4 rounded-xl text-[11px] font-mono leading-relaxed max-h-48 overflow-auto" style={{ background: "rgba(0,0,0,0.3)", color: "rgba(255,255,255,0.45)" }}>
                  {data.claude_analysis.general_assessment}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between text-[10px] font-mono pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.04)", color: "rgba(255,255,255,0.2)" }}>
              <span className="flex items-center gap-1">
                <Brain className="w-3 h-3" />
                {data.claude_analysis.model_used}
              </span>
              <span>{new Date(data.claude_analysis.timestamp).toLocaleTimeString(locale === "en" ? "en-US" : "tr-TR")}</span>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
