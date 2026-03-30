"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import {
  AlertTriangle,
  Anchor,
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
import { useRefreshAge } from "../hooks/useRefreshAge";
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

function clampStyle(lines: number): CSSProperties {
  return {
    display: "-webkit-box",
    WebkitLineClamp: lines,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
    overflowWrap: "anywhere",
    wordBreak: "break-word",
  };
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
  const directionLabel = getDirectionLabel(bias.direction, t);
  return (
    <div className="h-full min-w-0 overflow-hidden rounded-3xl p-5 md:p-6" style={{ background: tone.bg, border: `1px solid ${tone.border}` }}>
      <div className="flex h-full flex-col">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{title}</p>
            <div className="mt-4 flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl" style={{ background: "rgba(255,255,255,0.05)", border: `1px solid ${tone.border}` }}>
                <Icon className="h-5 w-5" style={{ color: tone.color }} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[1.9rem] font-black leading-none tracking-tight md:text-[2.25rem]" style={{ ...clampStyle(2), color: tone.color }}>
                  {directionLabel}
                </p>
                <p className="mt-3 text-sm font-medium leading-6 md:text-[15px]" style={{ ...clampStyle(3), color: P.text }}>
                  {bias.summary || "—"}
                </p>
              </div>
            </div>
          </div>
          <div className="shrink-0 rounded-2xl px-3 py-2 text-right" style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${tone.border}` }}>
            <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.recommendation")}</p>
            <p className="mt-1 text-lg font-black leading-none" style={{ color: tone.color }}>{bias.confidence.toFixed(0)}%</p>
          </div>
        </div>

        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          <div className="rounded-2xl px-3 py-3" style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${tone.border}` }}>
            <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.recommendation")}</p>
            <p className="mt-2 text-sm font-bold" style={{ ...clampStyle(2), color: tone.color }}>{directionLabel}</p>
          </div>
          <div className="rounded-2xl px-3 py-3" style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${tone.border}` }}>
            <p className="text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.entryPlan")}</p>
            <p className="mt-2 text-sm font-bold" style={{ ...clampStyle(2), color: P.text }}>{bias.time_horizon}</p>
          </div>
        </div>

        <div className="mt-5 space-y-2">
          {(notes.length ? notes : [bias.summary || "—"]).map((item, index) => (
            <div key={`${title}-${index}`} className="min-w-0 rounded-2xl px-4 py-3 text-sm leading-6" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${tone.border}`, color: P.text }}>
              <p style={clampStyle(3)}>{item}</p>
            </div>
          ))}
        </div>
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
    <div className="min-w-0 rounded-3xl px-4 py-4" style={{ minHeight: 112, background: P.bg, border: `1px solid ${P.border}` }}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{label}</p>
      <p className="mt-3 text-[1.65rem] font-black leading-tight tracking-tight md:text-[1.9rem]" style={{ ...clampStyle(2), color: P.text }}>{value}</p>
    </div>
  );
}

function physicalBiasLabel(value: number | string | undefined | null, threshold: number, invertedLogic: boolean = false): { label: string; color: string; arrow: string } {
  const num = typeof value === "number" ? value : parseFloat(String(value ?? "50"));
  if (Number.isNaN(num)) return { label: "—", color: "var(--text-muted)", arrow: "" };
  const high = invertedLogic ? num <= (100 - threshold) : num >= threshold;
  const low = invertedLogic ? num >= threshold : num <= (100 - threshold);
  if (high) return { label: "SELL", color: "var(--accent-negative)", arrow: "↘" };
  if (low) return { label: "BUY", color: "var(--accent-positive)", arrow: "↗" };
  return { label: "NEUTRAL", color: "var(--accent-warning)", arrow: "→" };
}

function PhysicalOilSummary({ data, t }: { data: any; t: (key: string) => string }) {
  if (!data || !data.oil_bias) return null;

  const overallBias = String(data.oil_bias || "").toLowerCase();
  const overallColor = overallBias === "bullish" ? P.green : overallBias === "bearish" ? P.red : P.warn;
  const overallLabel = overallBias === "bullish" ? "BUY" : overallBias === "bearish" ? "SELL" : "NEUTRAL";
  const overallArrow = overallBias === "bullish" ? "↗" : overallBias === "bearish" ? "↘" : "→";

  const metrics = [
    {
      key: "bcti_weakness",
      label: t("claudeAnalysis.physical.bctiWeakness"),
      desc: t("claudeAnalysis.physical.bctiDesc"),
      ...physicalBiasLabel(data.bcti_weakness, 70),
      raw: data.bcti_weakness,
    },
    {
      key: "contango_pressure",
      label: t("claudeAnalysis.physical.contangoPressure"),
      desc: t("claudeAnalysis.physical.contangoDesc"),
      ...physicalBiasLabel(data.contango_pressure, 65),
      raw: data.contango_pressure,
    },
    {
      key: "storage_pressure",
      label: t("claudeAnalysis.physical.storagePressure"),
      desc: t("claudeAnalysis.physical.storageDesc"),
      ...physicalBiasLabel(data.storage_pressure, 65),
      raw: data.storage_pressure,
    },
    {
      key: "recession_probability",
      label: t("claudeAnalysis.physical.recessionRisk"),
      desc: t("claudeAnalysis.physical.recessionDesc"),
      ...physicalBiasLabel(data.recession_probability, 60),
      raw: data.recession_probability,
    },
    {
      key: "refinery_stress",
      label: t("claudeAnalysis.physical.refineryStress"),
      desc: t("claudeAnalysis.physical.refineryDesc"),
      ...physicalBiasLabel(data.refinery_stress, 65),
      raw: data.refinery_stress,
    },
  ];

  const chokepoints = (data.chokepoints || []).filter((cp: any) => cp && cp.label);

  return (
    <div className="rounded-3xl p-5 md:p-6" style={{ background: "var(--accent-info-06, rgba(79,140,255,0.06))", border: "1px solid var(--accent-info-12, rgba(79,140,255,0.12))" }}>
      <div className="mb-5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Anchor className="h-4 w-4" style={{ color: P.accent }} />
          <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.physical.title")}</p>
        </div>
        <div className="flex items-center gap-2 rounded-full px-3 py-1" style={{ background: overallColor === P.green ? "var(--accent-positive-08)" : overallColor === P.red ? "var(--accent-negative-08)" : "var(--accent-warning-08)", border: `1px solid ${overallColor === P.green ? "var(--accent-positive-15)" : overallColor === P.red ? "var(--accent-negative-15)" : "var(--accent-warning-15)"}` }}>
          <span className="text-lg font-black leading-none" style={{ color: overallColor }}>{overallArrow}</span>
          <span className="text-[11px] font-bold" style={{ color: overallColor }}>{overallLabel}</span>
          <span className="ml-1 text-[11px] font-semibold" style={{ color: P.muted }}>{typeof data.physical_score === "number" ? `${data.physical_score.toFixed(0)}%` : ""}</span>
        </div>
      </div>

      <p className="mb-4 text-xs leading-5" style={{ color: P.muted }}>{t("claudeAnalysis.physical.description")}</p>

      <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
        {metrics.map((m) => (
          <div key={m.key} className="flex items-center justify-between gap-3 rounded-2xl px-4 py-3" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${P.border}` }}>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold" style={{ color: P.text }}>{m.label}</p>
              <p className="mt-0.5 text-[10px]" style={{ color: P.muted }}>{m.desc}</p>
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <span className="text-[10px] font-medium" style={{ color: P.muted }}>{typeof m.raw === "number" ? m.raw.toFixed(0) : "—"}</span>
              <span className="text-base font-black" style={{ color: m.color }}>{m.arrow}</span>
              <span className="text-[11px] font-bold" style={{ color: m.color }}>{m.label === "—" ? "" : m.label}</span>
            </div>
          </div>
        ))}
      </div>

      {chokepoints.length > 0 && (
        <div className="mt-3">
          <p className="mb-2 text-[10px] uppercase tracking-[0.18em]" style={{ color: P.muted }}>{t("claudeAnalysis.physical.chokepoints")}</p>
          <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
            {chokepoints.map((cp: any) => {
              const cpColor = cp.bias === "bullish" ? P.green : cp.bias === "bearish" ? P.red : P.warn;
              const cpArrow = cp.bias === "bullish" ? "↗" : cp.bias === "bearish" ? "↘" : "→";
              return (
                <div key={cp.label} className="flex items-center justify-between gap-2 rounded-2xl px-3 py-2" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${P.border}` }}>
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold" style={{ color: P.text }}>{cp.label}</p>
                    <p className="text-[10px]" style={{ color: P.muted }}>{cp.vessel_count ? `${cp.vessel_count} ${t("claudeAnalysis.physical.vessels")}` : cp.signal}</p>
                  </div>
                  <span className="text-base font-black" style={{ color: cpColor }}>{cpArrow}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
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
  const lastAnalysisAt =
    data?.claude_analysis?.analysis_meta?.generated_at ||
    data?.claude_analysis?.timestamp ||
    storedUpdatedAt ||
    null;
  const { refreshAge, markRefreshed } = useRefreshAge(lastAnalysisAt ? new Date(lastAnalysisAt) : null);
  const servedAt = data?.claude_analysis?.analysis_meta?.served_at || lastAnalysisAt || null;
  const { refreshAge: servedAge, markRefreshed: markServed } = useRefreshAge(servedAt ? new Date(servedAt) : null);

  useEffect(() => {
    if (fetchedData) {
      setAnalysis(symbol, fetchedData);
    }
  }, [fetchedData, setAnalysis, symbol]);

  useEffect(() => {
    if (lastAnalysisAt) {
      markRefreshed(lastAnalysisAt);
    }
  }, [lastAnalysisAt, markRefreshed]);

  useEffect(() => {
    if (servedAt) {
      markServed(servedAt);
    }
  }, [servedAt, markServed]);

  const panel = useMemo(() => {
    if (!data) return null;
    return data.claude_analysis.panel_signal || legacyToPanel(data);
  }, [data]);

  const analysisMeta = data?.claude_analysis.analysis_meta;
  const marketContext = data?.claude_analysis.market_context;
  const dataSources = data?.claude_analysis.data_sources;
  const hasPhysicalOil = Boolean(dataSources?.physical_oil);

  // Extract physical oil context from the panel signal's prompt payload if available
  const physicalOilData = useMemo(() => {
    if (!data || !hasPhysicalOil) return null;
    // Physical oil data comes through the panel_signal or directly
    const ps = (data as any)?.physical_oil_intelligence;
    if (ps && ps.oil_bias) return ps;
    // Try from claude_analysis extended fields  
    const ca = (data.claude_analysis as any)?.physical_oil_intelligence;
    if (ca && ca.oil_bias) return ca;
    return null;
  }, [data, hasPhysicalOil]);

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
  const riskRewardValue = panel?.entry_plan.risk_reward ? panel.entry_plan.risk_reward.toFixed(2) : "—";
  const isStaleCache = Boolean(analysisMeta?.stale_cache);
  const isCacheHit = Boolean(analysisMeta?.cache_hit);
  const showServedAt = Boolean(servedAt && servedAt !== lastAnalysisAt);
  const cacheBadgeStyle = isStaleCache
    ? { background: "var(--accent-warning-08)", border: "1px solid var(--accent-warning-15)", color: P.warn }
    : isCacheHit
      ? { background: "var(--accent-info-08)", border: "1px solid var(--accent-info-15)", color: P.accent }
      : { background: "var(--accent-purple-12)", border: "1px solid var(--accent-purple-20)", color: P.purple };
  const cacheBadgeLabel = isStaleCache
    ? t("claudeAnalysis.staleCached")
    : isCacheHit
      ? t("claudeAnalysis.cached")
      : t("claudeAnalysis.fresh");

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
          {hasPhysicalOil && (
            <div className="rounded-full px-3 py-1 text-[11px] font-semibold" style={{ background: "var(--accent-info-08)", border: "1px solid var(--accent-info-15)", color: P.accent }}>
              ⚓ {t("claudeAnalysis.physical.contextActive")}
            </div>
          )}
          <div className="rounded-full px-3 py-1 text-[11px] font-semibold" style={cacheBadgeStyle}>
            {cacheBadgeLabel}
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
        {lastAnalysisAt && data && (
          <div className="flex flex-wrap items-center gap-2 text-[11px]" style={{ color: P.muted }}>
            <Clock3 className="h-3.5 w-3.5" />
            <span>
              {t("claudeAnalysis.lastAnalysis")}: {new Date(lastAnalysisAt).toLocaleString(locale === "tr" ? "tr-TR" : "en-US")}
            </span>
            <span className="rounded-full px-2 py-0.5 font-semibold" style={{ background: "var(--accent-purple-06)", border: "1px solid var(--accent-purple-12)", color: P.purple }}>
              {refreshAge}
            </span>
          </div>
        )}

        {showServedAt && data && (
          <div className="flex flex-wrap items-center gap-2 text-[11px]" style={{ color: P.muted }}>
            <Clock3 className="h-3.5 w-3.5" />
            <span>
              {t("claudeAnalysis.cacheServed")}: {new Date(servedAt!).toLocaleString(locale === "tr" ? "tr-TR" : "en-US")}
            </span>
            <span className="rounded-full px-2 py-0.5 font-semibold" style={{ background: "var(--accent-info-06)", border: "1px solid var(--accent-info-15)", color: P.accent }}>
              {servedAge}
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
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.headline")}</p>
                  <h4 className="mt-2 text-xl font-black tracking-tight md:text-[1.7rem]" style={{ ...clampStyle(3), color: P.text }}>{panel.headline}</h4>
                </div>
                <div className="rounded-xl px-3 py-2 text-sm font-semibold" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                  {t("claudeAnalysis.eventRisk")}: {risk.level}
                </div>
              </div>
              <p className="text-base leading-7 md:text-lg" style={{ ...clampStyle(4), color: P.muted }}>{panel.confidence_reasoning}</p>
            </div>

            <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
              <IdeaCard title={t("claudeAnalysis.scalpBias")} bias={panel.scalp_bias} notes={scalpNotes} t={t} />
              <IdeaCard title={t("claudeAnalysis.intradayBias")} bias={panel.intraday_bias} notes={intradayNotes} t={t} />
            </div>

            <div className="rounded-3xl p-5 md:p-6" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
              <div className="mb-5 flex items-center gap-2">
                  <Target className="h-4 w-4" style={{ color: P.accent }} />
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.entryPlan")}</p>
              </div>
              <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
                <LevelCard label={t("claudeAnalysis.preferredEntry")} value={formatPrice(panel.entry_plan.preferred_entry)} />
                <LevelCard label={t("claudeAnalysis.stopLoss")} value={formatPrice(panel.entry_plan.stop_loss)} />
                <LevelCard label={t("claudeAnalysis.takeProfit")} value={formatPrice(panel.entry_plan.take_profit)} />
                <LevelCard label={t("claudeAnalysis.riskReward")} value={riskRewardValue} />
              </div>

              <div className="mt-4 grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                <div className="min-w-0 rounded-3xl px-4 py-4" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.invalidation")}</p>
                  <p className="mt-3 text-base font-semibold leading-7" style={{ ...clampStyle(4), color: P.text }}>{invalidationText}</p>
                </div>
                <div className="min-w-0 rounded-3xl px-4 py-4" style={{ background: P.bg, border: `1px solid ${P.border}` }}>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.keyLevels")}</p>
                  <div className="mt-3 grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))" }}>
                    {visibleKeyLevels.map((level, index) => (
                      <div key={`${level.label}-${index}`} className="min-w-0 rounded-2xl px-3 py-3 text-sm font-semibold" style={{ background: P.hover, border: `1px solid ${P.border}`, color: P.text }}>
                        <p className="text-[10px] uppercase tracking-[0.18em]" style={{ ...clampStyle(1), color: P.muted }}>{level.label}</p>
                        <p className="mt-2 text-base font-black tracking-tight" style={{ ...clampStyle(2), color: P.text }}>{formatPrice(level.price)}</p>
                      </div>
                    ))}
                    {!visibleKeyLevels.length && (
                      <div className="rounded-2xl px-3 py-3 text-sm" style={{ background: P.hover, border: `1px solid ${P.border}`, color: P.muted }}>
                        {t("claudeAnalysis.noLevels")}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
              <div className="min-w-0 rounded-3xl p-5" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.eventRisk")}</p>
                  <div className="rounded-full px-3 py-1 text-xs font-bold" style={{ background: riskStyle.bg, border: `1px solid ${riskStyle.border}`, color: riskStyle.color }}>
                    {risk.level}
                  </div>
                </div>
                <p className="text-base leading-7" style={{ ...clampStyle(4), color: P.text }}>{risk.summary || "—"}</p>
              </div>

              <div className="min-w-0 rounded-3xl p-5" style={{ background: P.hover, border: `1px solid ${P.border}` }}>
                <p className="text-[10px] uppercase tracking-[0.22em]" style={{ color: P.muted }}>{t("claudeAnalysis.reasoningSummary")}</p>
                <p className="mt-3 text-base font-semibold leading-7" style={{ ...clampStyle(3), color: P.text }}>
                  {marketContext?.session_name ? `${marketContext.session_name} · ${marketContext.phase || ""}` : analysisMeta?.market_session || symbolLabel}
                </p>
                {marketContext?.ny_time && (
                  <p className="mt-2 text-sm" style={{ color: P.muted }}>{marketContext.ny_time}</p>
                )}
              </div>
            </div>

            {physicalOilData && (
              <PhysicalOilSummary data={physicalOilData} t={t} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
