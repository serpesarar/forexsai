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

// ── Theme-aware Color Palette (CSS Variables) ───────────────────────────────
const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  purple: "var(--accent-purple)",
};

const neonDir: Record<string, { color: string; glow: string }> = {
  BUY: { color: P.green, glow: `${P.green}25` },
  SELL: { color: P.red, glow: `${P.red}25` },
  HOLD: { color: P.warn, glow: `${P.warn}25` },
};

function DirectionBadge({ direction, isClaudeDecision, t }: { direction: string; isClaudeDecision?: boolean; t: (key: string) => string }) {
  const nd = neonDir[direction] || neonDir.HOLD;
  const Icon = direction === "BUY" ? TrendingUp : direction === "SELL" ? TrendingDown : Minus;
  const label = direction === "BUY" ? t("directions.buy") : direction === "SELL" ? t("directions.sell") : t("directions.hold");

  return (
    <div className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg font-mono" style={{ background: `${nd.color}12`, border: `1px solid ${nd.color}25` }}>
      {isClaudeDecision && <Brain className="w-4 h-4" style={{ color: P.purple }} />}
      <Icon className="w-4 h-4" style={{ color: nd.color, filter: `drop-shadow(0 0 4px ${nd.color})` }} />
      <span className="text-sm font-bold" style={{ color: nd.color }}>{label}</span>
    </div>
  );
}

function AgreementBadge({ agreement, t }: { agreement: boolean; t: (key: string) => string }) {
  return agreement ? (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: "var(--accent-positive-08)", border: "1px solid var(--accent-positive-15)" }}>
      <CheckCircle2 className="w-4 h-4" style={{ color: P.green }} />
      <span className="text-xs font-mono font-medium" style={{ color: P.green }}>{t("claudeAnalysis.agreed")}</span>
    </div>
  ) : (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: "var(--accent-negative-08)", border: "1px solid var(--accent-negative-15)" }}>
      <XCircle className="w-4 h-4" style={{ color: P.red }} />
      <span className="text-xs font-mono font-medium" style={{ color: P.red }}>{t("claudeAnalysis.different")}</span>
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
    refetch().catch((err) => {
      console.error("[ClaudeAnalysis] Analysis error:", err);
    });
  };
  
  // Error state UI
  if (error && !data) {
    return (
      <div className="rounded-2xl p-6" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--accent-purple-15)" }}>
            <Sparkles className="w-5 h-5" style={{ color: P.purple }} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest font-mono" style={{ color: P.muted }}>{t("claudeAnalysis.title")}</p>
            <h3 className="text-base font-bold font-mono text-white/90">{symbolLabel}</h3>
          </div>
        </div>
        <div className="text-center py-8">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3" style={{ color: P.warn }} />
          <p className="text-sm mb-2" style={{ color: P.text }}>AI Analizi şu anda kullanılamıyor</p>
          <p className="text-xs mb-4" style={{ color: P.muted }}>{String(error).slice(0, 100)}</p>
          <button
            onClick={handleAnalyze}
            className="px-4 py-2 rounded-xl text-sm font-medium transition-all hover:brightness-125"
            style={{ background: "var(--accent-purple-12)", border: "1px solid var(--accent-purple-20)", color: P.purple }}
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: P.bg, border: `1px solid ${P.border}`, boxShadow: "0 0 40px var(--accent-purple-10), inset 0 1px 0 rgba(255,255,255,0.04)" }}>
      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between" style={{ background: P.surface, borderBottom: `1px solid ${P.border}` }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "var(--accent-purple-15)", boxShadow: "0 0 16px var(--accent-purple-30)" }}>
            <Sparkles className="w-5 h-5" style={{ color: P.purple }} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest font-mono" style={{ color: P.muted }}>{t("claudeAnalysis.title")}</p>
            <h3 className="text-base font-bold font-mono text-white/90">{symbolLabel}</h3>
          </div>
        </div>
        <button
          onClick={handleAnalyze}
          className="px-4 py-2 rounded-xl flex items-center gap-2 transition-all hover:brightness-125"
          style={{ background: "var(--accent-purple-12)", border: "1px solid var(--accent-purple-20)" }}
          disabled={isLoading}
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} style={{ color: P.purple }} />
          <span className="text-sm font-mono font-medium" style={{ color: P.purple }}>
            {isLoading ? t("claudeAnalysis.analyzing") : shouldFetch && data ? t("claudeAnalysis.refresh") : t("claudeAnalysis.analyze")}
          </span>
        </button>
      </div>

      <div className="p-5 space-y-4">
        {/* Show last updated time if we have persisted data */}
        {lastUpdated && data && !isLoading && (
          <div className="flex items-center gap-2 text-[10px] font-mono px-3 py-2 rounded-lg" style={{ background: "var(--bg-hover)", color: P.muted }}>
            <Clock className="w-3 h-3" />
            <span>{t("claudeAnalysis.lastAnalysis")}: {new Date(lastUpdated).toLocaleString(locale === "en" ? "en-US" : "tr-TR")}</span>
          </div>
        )}

        {!data && !isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Brain className="w-12 h-12 mb-4 opacity-30" style={{ color: P.purple }} />
            <p className="text-sm font-mono" style={{ color: P.muted }}>{t("claudeAnalysis.ready")}</p>
            <p className="text-xs font-mono mt-1" style={{ color: P.muted }}>{t("claudeAnalysis.apiSaving")}</p>
          </div>
        ) : isLoading ? (
          <div className="space-y-3 animate-pulse">
            <div className="h-12 w-full rounded-xl" style={{ background: "var(--bg-hover)" }} />
            <div className="h-24 w-full rounded-xl" style={{ background: "var(--bg-hover)" }} />
            <div className="h-16 w-full rounded-xl" style={{ background: "var(--bg-hover)" }} />
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 p-4 rounded-xl" style={{ background: "var(--accent-negative-08)", border: "1px solid var(--accent-negative-15)" }}>
            <AlertTriangle className="w-5 h-5" style={{ color: P.red }} />
            <span className="text-sm font-mono" style={{ color: P.red }}>{t("claudeAnalysis.error")}</span>
          </div>
        ) : data ? (
          <>
            {/* ML vs Claude Comparison */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl p-4 text-center" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                <p className="text-[9px] uppercase tracking-widest font-mono mb-3" style={{ color: P.muted }}>ML MODEL</p>
                <DirectionBadge direction={data.ml_prediction.direction} t={t} />
                <p className="text-[10px] font-mono mt-3" style={{ color: P.muted }}>{data.ml_prediction.confidence.toFixed(0)}% {t("mlPrediction.confidence")}</p>
              </div>
              
              <div className="rounded-xl p-4 flex flex-col items-center justify-center" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
                <AgreementBadge agreement={data.claude_analysis.agreement} t={t} />
                <p className="text-[10px] font-mono mt-3" style={{ color: P.muted }}>
                  {data.claude_analysis.agreement ? t("claudeAnalysis.agreement") : t("claudeAnalysis.disagreement")}
                </p>
              </div>
              
              <div className="rounded-xl p-4 text-center" style={{ background: "var(--accent-purple-06)", border: "1px solid var(--accent-purple-12)" }}>
                <p className="text-[9px] uppercase tracking-widest font-mono mb-3" style={{ color: P.purple }}>CLAUDE AI</p>
                <DirectionBadge direction={data.claude_analysis.claude_direction} isClaudeDecision t={t} />
                <p className="text-[10px] font-mono mt-3" style={{ color: P.muted }}>{data.claude_analysis.claude_confidence.toFixed(0)}% {t("mlPrediction.confidence")}</p>
              </div>
            </div>

            {/* Position Recommendation */}
            <div className="flex items-center justify-between px-4 py-3 rounded-xl" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4" style={{ color: P.accent }} />
                <span className="text-xs font-mono" style={{ color: P.muted }}>{t("claudeAnalysis.recommendation")}</span>
              </div>
              <span className="text-xs font-bold font-mono px-3 py-1 rounded-full" style={{
                background: data.claude_analysis.position_size_suggestion === "No Trade" ? "var(--accent-negative-12)" :
                  data.claude_analysis.position_size_suggestion === "Large" ? "var(--accent-positive-12)" :
                  data.claude_analysis.position_size_suggestion === "Medium" ? "var(--accent-info-12)" : "var(--accent-warning-12)",
                color: data.claude_analysis.position_size_suggestion === "No Trade" ? P.red :
                  data.claude_analysis.position_size_suggestion === "Large" ? P.green :
                  data.claude_analysis.position_size_suggestion === "Medium" ? P.accent : P.warn,
                border: `1px solid ${data.claude_analysis.position_size_suggestion === "No Trade" ? "var(--accent-negative-25)" :
                  data.claude_analysis.position_size_suggestion === "Large" ? "var(--accent-positive-25)" :
                  data.claude_analysis.position_size_suggestion === "Medium" ? "var(--accent-info-25)" : "var(--accent-warning-25)"}`,
              }}>
                {data.claude_analysis.position_size_suggestion === "No Trade" ? t("claudeAnalysis.positionSize.noTrade") :
                 data.claude_analysis.position_size_suggestion === "Large" ? t("claudeAnalysis.positionSize.large") :
                 data.claude_analysis.position_size_suggestion === "Medium" ? t("claudeAnalysis.positionSize.medium") : t("claudeAnalysis.positionSize.small")}
              </span>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-3" style={{ background: "var(--accent-positive-04)", border: "1px solid var(--accent-positive-10)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4" style={{ color: P.green }} />
                  <p className="text-xs font-mono font-bold" style={{ color: P.green }}>{t("common.bullish")}</p>
                </div>
                <ul className="space-y-1">
                  {data.claude_analysis.strengths.slice(0, 3).map((s, i) => (
                    <li key={i} className="text-[10px] font-mono flex gap-1" style={{ color: P.muted }}>
                      <span style={{ color: P.green }}>+</span>
                      <span className="line-clamp-2">{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="rounded-xl p-3" style={{ background: "var(--accent-negative-04)", border: "1px solid var(--accent-negative-10)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-4 h-4" style={{ color: P.red }} />
                  <p className="text-xs font-mono font-bold" style={{ color: P.red }}>{t("claudeAnalysis.riskAssessment")}</p>
                </div>
                <ul className="space-y-1">
                  {data.claude_analysis.weaknesses.slice(0, 3).map((w, i) => (
                    <li key={i} className="text-[10px] font-mono flex gap-1" style={{ color: P.muted }}>
                      <span style={{ color: P.red }}>-</span>
                      <span className="line-clamp-2">{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Price Levels */}
            <div className="rounded-xl p-4" style={{ background: "var(--bg-hover)", border: "1px solid var(--border-subtle)" }}>
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4" style={{ color: P.accent }} />
                <p className="text-xs font-mono font-bold" style={{ color: P.muted }}>{t("claudeAnalysis.recommendation")}</p>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg p-2" style={{ background: "var(--accent-info-05)" }}>
                  <p className="text-[9px] font-mono" style={{ color: P.muted }}>Entry</p>
                  <p className="text-sm font-mono font-bold text-white/80">{data.claude_analysis.recommended_entry.toFixed(2)}</p>
                </div>
                <div className="rounded-lg p-2" style={{ background: "var(--accent-positive-05)" }}>
                  <p className="text-[9px] font-mono" style={{ color: P.green }}>Take Profit</p>
                  <p className="text-sm font-mono font-bold" style={{ color: P.green }}>{data.claude_analysis.recommended_tp.toFixed(2)}</p>
                </div>
                <div className="rounded-lg p-2" style={{ background: "var(--accent-negative-05)" }}>
                  <p className="text-[9px] font-mono" style={{ color: P.red }}>Stop Loss</p>
                  <p className="text-sm font-mono font-bold" style={{ color: P.red }}>{data.claude_analysis.recommended_sl.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Expandable Assessment */}
            <div>
              <button
                onClick={() => setExpanded(!expanded)}
                className="w-full text-left px-4 py-3 rounded-xl transition-all hover:brightness-125"
                style={{ background: "var(--accent-purple-06)", border: "1px solid var(--accent-purple-10)" }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4" style={{ color: P.purple }} />
                    <span className="text-xs font-mono font-bold" style={{ color: P.purple }}>{t("claudeAnalysis.reasoning")}</span>
                  </div>
                  <span className="text-[10px] font-mono" style={{ color: P.muted }}>{expanded ? t("claudeAnalysis.showLess") : t("claudeAnalysis.showMore")}</span>
                </div>
              </button>
              
              {expanded && (
                <div className="mt-2 p-4 rounded-xl text-[11px] font-mono leading-relaxed max-h-48 overflow-auto" style={{ background: P.surface, color: P.muted }}>
                  {data.claude_analysis.general_assessment}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between text-[10px] font-mono pt-3" style={{ borderTop: `1px solid ${P.border}`, color: P.muted }}>
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
