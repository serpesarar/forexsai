"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Brain,
  ChevronDown,
  ChevronUp,
  Clock3,
  Database,
  Layers3,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";
import {
  FullAnalysisData,
  PanelBehavior,
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

const directionTone: Record<PanelDirection | "ML", { color: string; bg: string; border: string }> = {
  BUY: { color: P.green, bg: "var(--accent-positive-08)", border: "var(--accent-positive-15)" },
  SELL: { color: P.red, bg: "var(--accent-negative-08)", border: "var(--accent-negative-15)" },
  HOLD: { color: P.warn, bg: "var(--accent-warning-08)", border: "var(--accent-warning-15)" },
  NO_TRADE: { color: P.warn, bg: "var(--accent-warning-08)", border: "var(--accent-warning-15)" },
  ML: { color: P.accent, bg: "var(--accent-info-08)", border: "var(--accent-info-15)" },
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

function getBehaviorLabel(behavior: PanelBehavior, t: (key: string) => string) {
  const keyMap: Record<PanelBehavior, string> = {
    uptrend: "claudeAnalysis.behaviors.uptrend",
    downtrend: "claudeAnalysis.behaviors.downtrend",
    range: "claudeAnalysis.behaviors.range",
    mean_reversion: "claudeAnalysis.behaviors.meanReversion",
    volatile: "claudeAnalysis.behaviors.volatile",
  };
  return t(keyMap[behavior]);
}

function getQualityLabel(level: string, t: (key: string) => string) {
  if (level === "HIGH") return t("claudeAnalysis.qualityHigh");
  if (level === "LOW") return t("claudeAnalysis.qualityLow");
  return t("claudeAnalysis.qualityMedium");
}

function formatRelativeMinutes(minutes: number | null) {
  if (minutes === null || Number.isNaN(minutes)) return "—";
  if (minutes === 0) return "T0";
  if (minutes > 0) return `T-${minutes}m`;
  return `T+${Math.abs(minutes)}m`;
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

function BiasCard({
  title,
  bias,
  t,
}: {
  title: string;
  bias: PanelBias;
  t: (key: string) => string;
}) {
  const Icon = getDirectionIcon(bias.direction);
  const tone = directionTone[bias.direction];
  return (
    <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{title}</p>
          <p className="mt-1 text-sm font-semibold" style={{ color: P.text }}>{getBehaviorLabel(bias.expected_behavior, t)}</p>
        </div>
        <div className="rounded-xl px-3 py-2" style={{ background: tone.bg, border: `1px solid ${tone.border}` }}>
          <div className="flex items-center gap-2">
            <Icon className="h-4 w-4" style={{ color: tone.color }} />
            <span className="text-sm font-bold" style={{ color: tone.color }}>{getDirectionLabel(bias.direction, t)}</span>
          </div>
        </div>
      </div>
      <div className="mb-3 text-xs" style={{ color: P.muted }}>{bias.summary}</div>
      <div className="flex items-center justify-between text-[11px]" style={{ color: P.muted }}>
        <span>{bias.time_horizon}</span>
        <span>{bias.confidence.toFixed(0)}%</span>
      </div>
    </div>
  );
}

export default function ClaudeAnalysisPanelV2({ symbol, symbolLabel }: Props) {
  const { t, locale } = useI18nStore();
  const { getAnalysis, getLastUpdated, setAnalysis } = useClaudeAnalysisStore();
  const [refreshNonce, setRefreshNonce] = useState(0);
  const { data: fetchedData, isLoading, isFetching, error } = useAIAnalysis(symbol, true, refreshNonce);
  const [expanded, setExpanded] = useState(false);

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
  const dataSources = data?.claude_analysis.data_sources;

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
  const qualityStyle = riskTone[(panel?.data_quality.level || "MEDIUM") as keyof typeof riskTone] || riskTone.MEDIUM;
  const positionSize = data?.claude_analysis.position_size_suggestion || t("claudeAnalysis.positionSize.small");
  const showStoredWarning = Boolean(error && data);

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
    <div className="overflow-hidden rounded-2xl" style={{ background: P.bg, border: `1px solid ${P.border}`, boxShadow: "0 0 40px var(--accent-purple-10), inset 0 1px 0 rgba(255,255,255,0.04)" }}>
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4" style={{ background: P.surface, borderBottom: `1px solid ${P.border}` }}>
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl" style={{ background: "var(--accent-purple-15)" }}>
            <Sparkles className="h-5 w-5" style={{ color: P.purple }} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em]" style={{ color: P.muted }}>{t("claudeAnalysis.title")}</p>
            <h3 className="text-base font-bold" style={{ color: P.text }}>{symbolLabel}</h3>
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
            <div className="h-14 rounded-2xl" style={{ background: P.hover }} />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="h-36 rounded-2xl" style={{ background: P.hover }} />
              <div className="h-36 rounded-2xl" style={{ background: P.hover }} />
              <div className="h-36 rounded-2xl" style={{ background: P.hover }} />
            </div>
            <div className="h-40 rounded-2xl" style={{ background: P.hover }} />
          </div>
        )}

        {!data && !isLoading && (
          <div className="rounded-2xl p-8 text-center" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
            <Brain className="mx-auto mb-3 h-10 w-10" style={{ color: P.purple, opacity: 0.65 }} />
            <p className="text-sm font-semibold" style={{ color: P.text }}>{t("claudeAnalysis.analyzing")}</p>
            <p className="mt-2 text-xs" style={{ color: P.muted }}>{t("claudeAnalysis.liveContext")}</p>
          </div>
        )}

        {data && panel && (
          <>
            <div className="rounded-2xl p-4" style={{ background: "var(--accent-purple-06)", border: "1px solid var(--accent-purple-12)" }}>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.headline")}</p>
                  <h4 className="mt-1 text-base font-semibold" style={{ color: P.text }}>{panel.headline}</h4>
                </div>
                <div className="rounded-xl px-3 py-2 text-sm font-semibold" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                  {t("claudeAnalysis.eventRisk")}: {risk.level}
                </div>
              </div>
              <p className="text-sm leading-6" style={{ color: P.muted }}>{panel.confidence_reasoning}</p>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.mlDecision")}</p>
                  <Database className="h-4 w-4" style={{ color: P.accent }} />
                </div>
                <div className="rounded-xl px-3 py-3" style={{ background: directionTone.ML.bg, border: `1px solid ${directionTone.ML.border}` }}>
                  <div className="mb-1 text-sm font-bold" style={{ color: directionTone.ML.color }}>{data.ml_prediction.direction}</div>
                  <div className="text-xs" style={{ color: P.muted }}>{data.ml_prediction.confidence.toFixed(0)}%</div>
                </div>
                <div className="mt-3 text-xs" style={{ color: P.muted }}>{data.ml_prediction.reasoning?.[0] || panel.top_factors[0] || ""}</div>
              </div>

              <BiasCard title={t("claudeAnalysis.scalpBias")} bias={panel.scalp_bias} t={t} />
              <BiasCard title={t("claudeAnalysis.intradayBias")} bias={panel.intraday_bias} t={t} />

              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.marketBehavior")}</p>
                  <Layers3 className="h-4 w-4" style={{ color: P.purple }} />
                </div>
                <div className="text-sm font-semibold" style={{ color: P.text }}>{getBehaviorLabel(panel.market_behavior.state, t)}</div>
                <div className="mt-1 text-xs" style={{ color: P.muted }}>{panel.market_behavior.summary}</div>
                <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-xl px-3 py-2" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                    {positionSize}
                  </div>
                  <div className="rounded-xl px-3 py-2" style={{ background: qualityStyle.bg, border: `1px solid ${qualityStyle.border}`, color: qualityStyle.color }}>
                    {getQualityLabel(panel.data_quality.level, t)}
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" style={{ color: P.green }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.bullCase")}</p>
                </div>
                <div className="space-y-2">
                  {(panel.bull_case.length ? panel.bull_case : ["—"]).map((item, index) => (
                    <div key={`${item}-${index}`} className="rounded-xl px-3 py-2 text-sm" style={{ background: "var(--accent-positive-08)", border: "1px solid var(--accent-positive-15)", color: P.text }}>
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center gap-2">
                  <TrendingDown className="h-4 w-4" style={{ color: P.red }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.bearCase")}</p>
                </div>
                <div className="space-y-2">
                  {(panel.bear_case.length ? panel.bear_case : ["—"]).map((item, index) => (
                    <div key={`${item}-${index}`} className="rounded-xl px-3 py-2 text-sm" style={{ background: "var(--accent-negative-08)", border: "1px solid var(--accent-negative-15)", color: P.text }}>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-4 flex items-center gap-2">
                  <Target className="h-4 w-4" style={{ color: P.accent }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.entryPlan")}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
                  <div className="rounded-xl px-3 py-3" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.preferredEntry")}</p>
                    <p className="mt-1 font-semibold" style={{ color: P.text }}>{formatPrice(panel.entry_plan.preferred_entry)}</p>
                  </div>
                  <div className="rounded-xl px-3 py-3" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.stopLoss")}</p>
                    <p className="mt-1 font-semibold" style={{ color: P.text }}>{formatPrice(panel.entry_plan.stop_loss)}</p>
                  </div>
                  <div className="rounded-xl px-3 py-3" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.takeProfit")}</p>
                    <p className="mt-1 font-semibold" style={{ color: P.text }}>{formatPrice(panel.entry_plan.take_profit)}</p>
                  </div>
                  <div className="rounded-xl px-3 py-3" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.entryZone")}</p>
                    <p className="mt-1 font-semibold" style={{ color: P.text }}>
                      {panel.entry_plan.entry_zone
                        ? `${formatPrice(panel.entry_plan.entry_zone.low)} - ${formatPrice(panel.entry_plan.entry_zone.high)}`
                        : "—"}
                    </p>
                  </div>
                  <div className="rounded-xl px-3 py-3" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.riskReward")}</p>
                    <p className="mt-1 font-semibold" style={{ color: P.text }}>{panel.entry_plan.risk_reward ? panel.entry_plan.risk_reward.toFixed(2) : "—"}</p>
                  </div>
                  <div className="rounded-xl px-3 py-3" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                    <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.recommendation")}</p>
                    <p className="mt-1 font-semibold" style={{ color: P.text }}>{panel.entry_plan.strategy.replaceAll("_", " ")}</p>
                  </div>
                </div>
                <div className="mt-4 rounded-xl px-3 py-3 text-sm" style={{ background: "var(--accent-info-08)", border: "1px solid var(--accent-info-15)", color: P.text }}>
                  {panel.entry_plan.invalidation || panel.invalidation[0] || "—"}
                </div>
              </div>

              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-4 flex items-center gap-2">
                  <Layers3 className="h-4 w-4" style={{ color: P.purple }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.keyLevels")}</p>
                </div>
                <div className="space-y-2">
                  {(panel.key_levels.length ? panel.key_levels : []).slice(0, 8).map((level, index) => (
                    <div key={`${level.label}-${index}`} className="flex items-center justify-between rounded-xl px-3 py-2 text-sm" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                      <div>
                        <p style={{ color: P.text }}>{level.label}</p>
                        <p className="text-[11px] uppercase" style={{ color: P.muted }}>{level.kind}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold" style={{ color: P.text }}>{formatPrice(level.price)}</p>
                        <p className="text-[11px]" style={{ color: P.muted }}>{level.source}</p>
                      </div>
                    </div>
                  ))}
                  {!panel.key_levels.length && (
                    <div className="rounded-xl px-3 py-3 text-sm" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.muted }}>
                      {t("claudeAnalysis.noLevels")}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4" style={{ color: riskTone[panel.macro_risk.level]?.color || P.warn }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.macroRisk")}</p>
                </div>
                <div className="mb-3 rounded-xl px-3 py-2 text-sm font-semibold" style={{ background: riskTone[panel.macro_risk.level]?.bg || riskTone.MEDIUM.bg, border: `1px solid ${riskTone[panel.macro_risk.level]?.border || riskTone.MEDIUM.border}`, color: riskTone[panel.macro_risk.level]?.color || P.warn }}>
                  {panel.macro_risk.level}
                </div>
                <p className="text-sm" style={{ color: P.text }}>{panel.macro_risk.summary}</p>
                <div className="mt-3 space-y-2">
                  {panel.macro_risk.drivers.slice(0, 4).map((driver, index) => (
                    <div key={`${driver}-${index}`} className="rounded-xl px-3 py-2 text-xs" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.muted }}>
                      {driver}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" style={{ color: riskStyle.color }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.eventRisk")}</p>
                </div>
                <div className="mb-3 rounded-xl px-3 py-2 text-sm font-semibold" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                  {risk.level}
                </div>
                <p className="text-sm" style={{ color: P.text }}>{risk.summary}</p>
                <div className="mt-3 space-y-2">
                  {(risk.events.length ? risk.events : []).map((event, index) => (
                    <div key={`${event.event_name}-${index}`} className="flex items-center justify-between rounded-xl px-3 py-2 text-xs" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                      <div>
                        <p style={{ color: P.text }}>{event.event_name}</p>
                        <p style={{ color: P.muted }}>{event.impact}</p>
                      </div>
                      <span style={{ color: P.muted }}>{formatRelativeMinutes(event.minutes_until)}</span>
                    </div>
                  ))}
                  {!risk.events.length && (
                    <div className="rounded-xl px-3 py-3 text-sm" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.muted }}>
                      {t("claudeAnalysis.noEvents")}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={() => setExpanded((current) => !current)}
              className="flex w-full items-center justify-between rounded-2xl px-4 py-3 text-left"
              style={{ background: P.hover, border: `1px solid ${P.border}` }}
            >
              <div>
                <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.reasoningSummary")}</p>
                <p className="mt-1 text-sm font-semibold" style={{ color: P.text }}>{analysisMeta?.model || data.claude_analysis.model_used || "DeepSeek Reasoner"}</p>
              </div>
              {expanded ? <ChevronUp className="h-4 w-4" style={{ color: P.muted }} /> : <ChevronDown className="h-4 w-4" style={{ color: P.muted }} />}
            </button>

            {expanded && (
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                  <p className="mb-3 text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.topFactors")}</p>
                  <div className="space-y-2">
                    {panel.top_factors.map((item, index) => (
                      <div key={`${item}-${index}`} className="rounded-xl px-3 py-2 text-sm" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.text }}>
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                  <p className="mb-3 text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.counterFactors")}</p>
                  <div className="space-y-2">
                    {panel.counter_factors.map((item, index) => (
                      <div key={`${item}-${index}`} className="rounded-xl px-3 py-2 text-sm" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.text }}>
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                  <p className="mb-3 text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.invalidation")}</p>
                  <div className="space-y-2">
                    {panel.invalidation.map((item, index) => (
                      <div key={`${item}-${index}`} className="rounded-xl px-3 py-2 text-sm" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.text }}>
                        {item}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl p-4" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                  <p className="mb-3 text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.dataQuality")}</p>
                  <div className="mb-3 rounded-xl px-3 py-2 text-sm font-semibold" style={{ background: qualityStyle.bg, border: `1px solid ${qualityStyle.border}`, color: qualityStyle.color }}>
                    {getQualityLabel(panel.data_quality.level, t)}
                  </div>
                  <div className="space-y-2 text-sm" style={{ color: P.text }}>
                    {panel.data_quality.notes.map((item, index) => (
                      <div key={`${item}-${index}`} className="rounded-xl px-3 py-2" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                        {item}
                      </div>
                    ))}
                    {panel.data_quality.missing_inputs.length > 0 && (
                      <div className="rounded-xl px-3 py-2 text-xs" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.muted }}>
                        {panel.data_quality.missing_inputs.join(", ")}
                      </div>
                    )}
                  </div>
                </div>

                <div className="rounded-2xl p-4 lg:col-span-2" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                  <p className="mb-3 text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.dataSources")}</p>
                  <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                    {Object.entries(dataSources || {}).map(([key, enabled]) => (
                      <div key={key} className="rounded-xl px-3 py-2 text-xs capitalize" style={{ background: enabled ? "var(--accent-positive-08)" : P.bg, border: `1px solid ${enabled ? "var(--accent-positive-15)" : P.border}`, color: enabled ? P.green : P.muted }}>
                        {key.replaceAll("_", " ")}
                      </div>
                    ))}
                  </div>
                  {marketContext?.session_name && (
                    <div className="mt-3 rounded-xl px-3 py-2 text-xs" style={{ background: P.bg, border: `1px solid ${P.border}`, color: P.muted }}>
                      {marketContext.session_name} · {marketContext.phase || ""} · {marketContext.ny_time || ""}
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
