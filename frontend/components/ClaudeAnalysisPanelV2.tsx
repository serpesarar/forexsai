"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Brain,
  Clock3,
  RefreshCw,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";
import {
  FullAnalysisData,
  PanelBias,
  PanelDirection,
  PanelSignal,
  useAIAnalysis,
} from "../lib/api/aiAnalysis";
import { useClaudeAnalysisStore } from "../lib/claudeAnalysisStore";
import { useI18nStore } from "../lib/i18n/store";

type Props = {
  symbol: string;
  symbolLabel: string;
};

const P = {
  bg: "var(--bg-primary)",
  surface: "var(--bg-surface)",
  hover: "var(--bg-hover)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  purple: "var(--accent-purple)",
};

const directionTone: Record<PanelDirection, { color: string; bg: string; border: string }> = {
  BUY: { color: P.green, bg: "var(--accent-positive-08)", border: "var(--accent-positive-15)" },
  SELL: { color: P.red, bg: "var(--accent-negative-08)", border: "var(--accent-negative-15)" },
  HOLD: { color: P.warn, bg: "var(--accent-warning-08)", border: "var(--accent-warning-15)" },
  NO_TRADE: { color: P.warn, bg: "var(--accent-warning-08)", border: "var(--accent-warning-15)" },
};

const riskTone: Record<string, { color: string; bg: string; border: string }> = {
  LOW: { color: P.green, bg: "var(--accent-positive-08)", border: "var(--accent-positive-15)" },
  MEDIUM: { color: P.warn, bg: "var(--accent-warning-08)", border: "var(--accent-warning-15)" },
  HIGH: { color: P.red, bg: "var(--accent-negative-08)", border: "var(--accent-negative-15)" },
};

function getDirectionLabel(direction: PanelDirection, t: (key: string) => string) {
  if (direction === "BUY") return t("directions.buy");
  if (direction === "SELL") return t("directions.sell");
  if (direction === "NO_TRADE") return t("claudeAnalysis.noTrade");
  return t("directions.hold");
}

function getDirectionIcon(direction: PanelDirection) {
  if (direction === "BUY") return TrendingUp;
  if (direction === "SELL") return TrendingDown;
  return Brain;
}

function getBiasNotes(bias: PanelBias, fallback: string[]) {
  return (bias.reasoning?.length ? bias.reasoning : fallback).filter(Boolean).slice(0, 2);
}

function legacyToPanel(data: FullAnalysisData): PanelSignal {
  const ai = data.claude_analysis;
  const direction = (ai.claude_direction as PanelDirection) || "HOLD";
  const fallbackDirection = (data.ml_prediction.direction as PanelDirection) || "HOLD";
  return {
    headline: ai.general_assessment || `${symbolLabelFromData(data)} ${direction}`,
    scalp_bias: {
      direction: (ai.scalp_direction as PanelDirection) || direction,
      confidence: ai.scalp_confidence || Math.max(35, ai.claude_confidence - 5),
      expected_behavior: "range",
      summary: ai.general_assessment || "",
      time_horizon: "15-90m",
      reasoning: ai.key_observations || [],
    },
    intraday_bias: {
      direction,
      confidence: ai.claude_confidence,
      expected_behavior: "range",
      summary: ai.general_assessment || "",
      time_horizon: "rest_of_session",
      reasoning: ai.key_observations || [],
    },
    market_behavior: {
      state: "range",
      summary: ai.general_assessment || "",
      expected_volatility: "MEDIUM",
    },
    entry_plan: {
      strategy: direction === "BUY" ? "buy_dips" : direction === "SELL" ? "sell_rips" : "wait",
      preferred_entry: ai.recommended_entry ?? data.ml_prediction.entry_price ?? null,
      entry_zone: null,
      stop_loss: ai.recommended_sl ?? data.ml_prediction.stop_price ?? null,
      take_profit: ai.recommended_tp ?? data.ml_prediction.target_price ?? null,
      risk_reward: data.ml_prediction.risk_reward ?? null,
      invalidation: (ai.risk_factors || [])[0] || "",
    },
    key_levels: (data.ml_prediction.key_levels || []).map((level) => ({
      label: level.type,
      price: level.price,
      kind: "trigger",
      source: "ml",
      distance: level.distance,
    })),
    bull_case: direction === "SELL" ? ai.weaknesses || [] : ai.strengths || [],
    bear_case: direction === "SELL" ? ai.strengths || [] : ai.weaknesses || [],
    macro_risk: {
      level: "MEDIUM",
      summary: (ai.risk_factors || []).join(" ") || ai.general_assessment || "",
      drivers: ai.risk_factors || [],
    },
    event_risk: {
      level: "MEDIUM",
      summary: (ai.risk_factors || []).join(" ") || "",
      events: [],
    },
    invalidation: ai.risk_factors || [],
    confidence_reasoning: ai.general_assessment || "",
    top_factors: ai.key_observations || ai.strengths || [],
    counter_factors: ai.risk_factors || ai.weaknesses || [],
    data_quality: {
      level: "MEDIUM",
      missing_inputs: [],
      notes: [fallbackDirection === direction ? ai.general_assessment : "Legacy payload mapped into the new panel."].filter(Boolean) as string[],
    },
  };
}

function symbolLabelFromData(data: FullAnalysisData) {
  return data.claude_analysis.symbol || data.ml_prediction.symbol || "";
}

function IdeaCard({
  title,
  bias,
  notes,
  t,
}: {
  title: string;
  bias: PanelBias;
  notes: string[];
  t: (key: string) => string;
}) {
  const Icon = getDirectionIcon(bias.direction);
  const tone = directionTone[bias.direction];
  return (
    <div className="rounded-3xl p-5 md:p-6" style={{ background: tone.bg, border: `1px solid ${tone.border}` }}>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{title}</p>
          <div className="mt-3 flex items-center gap-3">
            <Icon className="h-7 w-7" style={{ color: tone.color }} />
            <p className="text-3xl font-black tracking-tight md:text-4xl" style={{ color: tone.color }}>
              {getDirectionLabel(bias.direction, t)}
            </p>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-semibold" style={{ color: P.muted }}>
            <span className="rounded-full px-3 py-1" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${tone.border}` }}>
              {bias.time_horizon}
            </span>
            <span className="rounded-full px-3 py-1" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${tone.border}` }}>
              {bias.confidence.toFixed(0)}%
            </span>
          </div>
        </div>
        <div className="rounded-2xl px-4 py-3 text-right" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${tone.border}` }}>
          <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.recommendation")}</p>
          <p className="mt-1 text-base font-bold" style={{ color: tone.color }}>{getDirectionLabel(bias.direction, t)}</p>
        </div>
      </div>

      <p className="text-base font-semibold leading-7 md:text-lg" style={{ color: P.text }}>{bias.summary || "—"}</p>

      <div className="mt-4 space-y-2">
        {notes.map((item, index) => (
          <div key={`${title}-${index}`} className="rounded-2xl px-4 py-3 text-sm leading-6" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${tone.border}`, color: P.text }}>
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function LevelCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-3xl px-4 py-4" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{label}</p>
      <p className="mt-3 text-2xl font-black tracking-tight md:text-[2rem]" style={{ color: P.text }}>{value}</p>
    </div>
  );
}

export default function ClaudeAnalysisPanelV2({ symbol, symbolLabel }: Props) {
  const { t, locale } = useI18nStore();
  const { getAnalysis, getLastUpdated, setAnalysis } = useClaudeAnalysisStore();
  const [refreshNonce, setRefreshNonce] = useState(0);
  const { data: fetchedData, isLoading, isFetching, error } = useAIAnalysis(symbol, true, refreshNonce);

  const persistedData = getAnalysis(symbol);
  const storedUpdatedAt = getLastUpdated(symbol);
  const data = fetchedData || persistedData;

  useEffect(() => {
    if (fetchedData) {
      setAnalysis(symbol, fetchedData);
    }
  }, [fetchedData, setAnalysis, symbol]);

  const panel = useMemo(() => {
    if (!data) return null;
    return data.claude_analysis.panel_signal || legacyToPanel(data);
  }, [data]);

  const analysisMeta = data?.claude_analysis.analysis_meta;
  const marketContext = data?.claude_analysis.market_context;

  const formatter = useMemo(
    () =>
      new Intl.NumberFormat(locale === "tr" ? "tr-TR" : "en-US", {
        maximumFractionDigits: 2,
      }),
    [locale],
  );

  const formatPrice = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) return "—";
    return formatter.format(value);
  };

  const risk = panel?.event_risk || { level: "LOW", summary: "", events: [] };
  const riskStyle = riskTone[risk.level] || riskTone.MEDIUM;
  const showStoredWarning = Boolean(error && data);
  const scalpNotes = panel ? getBiasNotes(panel.scalp_bias, panel.top_factors) : [];
  const intradayNotes = panel ? getBiasNotes(panel.intraday_bias, panel.top_factors) : [];
  const visibleKeyLevels = (panel?.key_levels || []).slice(0, 4);
  const invalidationText = panel?.entry_plan.invalidation || panel?.invalidation[0] || "—";

  const handleRefresh = () => {
    setRefreshNonce((current) => current + 1);
  };

  if (error && !data) {
    return (
      <div className="rounded-2xl p-6" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl" style={{ background: "var(--accent-purple-15)" }}>
            <Sparkles className="h-5 w-5" style={{ color: P.purple }} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em]" style={{ color: P.muted }}>{t("claudeAnalysis.title")}</p>
            <h3 className="text-base font-bold" style={{ color: P.text }}>{symbolLabel}</h3>
          </div>
        </div>
        <div className="rounded-2xl p-5 text-center" style={{ background: "var(--accent-negative-08)", border: "1px solid var(--accent-negative-15)" }}>
          <AlertTriangle className="mx-auto mb-3 h-9 w-9" style={{ color: P.red }} />
          <p className="mb-2 text-sm font-semibold" style={{ color: P.text }}>{t("claudeAnalysis.error")}</p>
          <p className="mb-4 text-xs" style={{ color: P.muted }}>{String(error).slice(0, 180)}</p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold"
            style={{ background: "var(--accent-purple-12)", border: "1px solid var(--accent-purple-20)", color: P.purple }}
          >
            <RefreshCw className="h-4 w-4" />
            {t("claudeAnalysis.refresh")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl font-sans" style={{ background: P.bg, border: `1px solid ${P.border}`, boxShadow: "0 0 32px var(--accent-purple-08), inset 0 1px 0 rgba(255,255,255,0.04)" }}>
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4" style={{ background: P.surface, borderBottom: `1px solid ${P.border}` }}>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl" style={{ background: "var(--accent-purple-15)" }}>
            <Sparkles className="h-5 w-5" style={{ color: P.purple }} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em]" style={{ color: P.muted }}>{t("claudeAnalysis.title")}</p>
            <h3 className="text-lg font-black tracking-tight" style={{ color: P.text }}>{symbolLabel}</h3>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="rounded-full px-3 py-1 text-[11px] font-semibold" style={{ background: analysisMeta?.market_open ? "var(--accent-positive-08)" : "var(--accent-warning-08)", border: `1px solid ${analysisMeta?.market_open ? "var(--accent-positive-15)" : "var(--accent-warning-15)"}`, color: analysisMeta?.market_open ? P.green : P.warn }}>
            {analysisMeta?.market_open ? t("claudeAnalysis.sessionOpen") : t("claudeAnalysis.sessionClosed")}
          </div>
          <div className="rounded-full px-3 py-1 text-[11px] font-semibold" style={{ background: analysisMeta?.cache_hit ? "var(--accent-info-08)" : "var(--accent-purple-12)", border: `1px solid ${analysisMeta?.cache_hit ? "var(--accent-info-15)" : "var(--accent-purple-20)"}`, color: analysisMeta?.cache_hit ? P.accent : P.purple }}>
            {analysisMeta?.cache_hit ? t("claudeAnalysis.cached") : t("claudeAnalysis.fresh")}
          </div>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all hover:brightness-125"
            style={{ background: "var(--accent-purple-12)", border: "1px solid var(--accent-purple-20)", color: P.purple }}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            {isLoading || isFetching ? t("claudeAnalysis.analyzing") : t("claudeAnalysis.refresh")}
          </button>
        </div>
      </div>

      <div className="space-y-4 p-5">
        {storedUpdatedAt && data && (
          <div className="flex flex-wrap items-center gap-2 text-[11px]" style={{ color: P.muted }}>
            <Clock3 className="h-3.5 w-3.5" />
            <span>
              {t("claudeAnalysis.lastAnalysis")}: {new Date(storedUpdatedAt).toLocaleString(locale === "tr" ? "tr-TR" : "en-US")}
            </span>
          </div>
        )}

        {showStoredWarning && (
          <div className="flex items-start gap-3 rounded-2xl p-4" style={{ background: "var(--accent-warning-08)", border: "1px solid var(--accent-warning-15)" }}>
            <TriangleAlert className="mt-0.5 h-4 w-4" style={{ color: P.warn }} />
            <div>
              <p className="text-sm font-semibold" style={{ color: P.text }}>{t("claudeAnalysis.usingStored")}</p>
              <p className="mt-1 text-xs" style={{ color: P.muted }}>{String(error).slice(0, 160)}</p>
            </div>
          </div>
        )}

        {!data && isLoading && (
          <div className="space-y-3 animate-pulse">
            <div className="h-24 rounded-3xl" style={{ background: P.hover }} />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="h-64 rounded-3xl" style={{ background: P.hover }} />
              <div className="h-64 rounded-3xl" style={{ background: P.hover }} />
            </div>
            <div className="h-44 rounded-3xl" style={{ background: P.hover }} />
          </div>
        )}

        {!data && !isLoading && (
          <div className="rounded-3xl p-8 text-center" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
            <Brain className="mx-auto mb-3 h-10 w-10" style={{ color: P.purple, opacity: 0.65 }} />
            <p className="text-sm font-semibold" style={{ color: P.text }}>{t("claudeAnalysis.analyzing")}</p>
            <p className="mt-2 text-xs" style={{ color: P.muted }}>{t("claudeAnalysis.liveContext")}</p>
          </div>
        )}

        {data && panel && (
          <>
            <div className="rounded-3xl p-5 md:p-6" style={{ background: "var(--accent-purple-06)", border: "1px solid var(--accent-purple-12)" }}>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.headline")}</p>
                  <h4 className="mt-2 text-xl font-black tracking-tight md:text-[1.7rem]" style={{ color: P.text }}>{panel.headline}</h4>
                </div>
                <div className="rounded-xl px-3 py-2 text-sm font-semibold" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                  {t("claudeAnalysis.eventRisk")}: {risk.level}
                </div>
              </div>
              <p className="text-base leading-7 md:text-lg" style={{ color: P.muted }}>{panel.confidence_reasoning}</p>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <IdeaCard title={t("claudeAnalysis.scalpBias")} bias={panel.scalp_bias} notes={scalpNotes} t={t} />
              <IdeaCard title={t("claudeAnalysis.intradayBias")} bias={panel.intraday_bias} notes={intradayNotes} t={t} />
            </div>

            <div className="rounded-3xl p-5 md:p-6" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
              <div className="mb-5 flex items-center gap-2">
                  <Target className="h-4 w-4" style={{ color: P.accent }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.entryPlan")}</p>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <LevelCard label={t("claudeAnalysis.preferredEntry")} value={formatPrice(panel.entry_plan.preferred_entry)} />
                <LevelCard label={t("claudeAnalysis.stopLoss")} value={formatPrice(panel.entry_plan.stop_loss)} />
                <LevelCard label={t("claudeAnalysis.takeProfit")} value={formatPrice(panel.entry_plan.take_profit)} />
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="rounded-3xl px-4 py-4" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.invalidation")}</p>
                  <p className="mt-3 text-base font-semibold leading-7" style={{ color: P.text }}>{invalidationText}</p>
                </div>
                <div className="rounded-3xl px-4 py-4" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.keyLevels")}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {visibleKeyLevels.map((level, index) => (
                      <div key={`${level.label}-${index}`} className="rounded-full px-3 py-2 text-sm font-semibold" style={{ background: P.hover, border: `1px solid ${P.border}`, color: P.text }}>
                        {level.label}: {formatPrice(level.price)}
                      </div>
                    ))}
                    {!visibleKeyLevels.length && (
                      <div className="rounded-full px-3 py-2 text-sm" style={{ background: P.hover, border: `1px solid ${P.border}`, color: P.muted }}>
                        {t("claudeAnalysis.noLevels")}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-3xl p-5" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.eventRisk")}</p>
                  <div className="rounded-full px-3 py-1 text-xs font-bold" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                    {risk.level}
                  </div>
                </div>
                <p className="text-base leading-7" style={{ color: P.text }}>{risk.summary || "—"}</p>
              </div>

              <div className="rounded-3xl p-5" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.reasoningSummary")}</p>
                <p className="mt-3 text-base font-semibold leading-7" style={{ color: P.text }}>
                  {marketContext?.session_name ? `${marketContext.session_name} · ${marketContext.phase || ""}` : analysisMeta?.market_session || symbolLabel}
                </p>
                {marketContext?.ny_time && (
                  <p className="mt-2 text-sm" style={{ color: P.muted }}>{marketContext.ny_time}</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
