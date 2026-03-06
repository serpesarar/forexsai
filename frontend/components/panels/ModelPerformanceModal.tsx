"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getApiBase } from "../../lib/api/base";

const API_BASE = getApiBase();
const TF_ORDER = ["all", "5m", "15m", "30m", "1h", "4h", "1d"];

interface HourlyData {
  hour: number;
  total: number;
  wins: number;
  win_rate: number;
  avg_pips: number;
}

interface TFData {
  tf: string;
  total: number;
  active?: number;
  win_rate: number;
  net_pips: number;
  avg_pips: number;
}

interface DailyData {
  date: string;
  total: number;
  wins: number;
  win_rate: number;
  cumulative_pips: number;
}

interface DOWData {
  day: string;
  day_short: string;
  total: number;
  wins: number;
  win_rate: number;
  avg_pips: number;
}

interface RecentSignal {
  id: string;
  date: string;
  direction: string;
  confidence: number;
  status: string;
  pips: number;
  timeframe: string;
}

interface ModelComparisonRow {
  model: string;
  total: number;
  scored_signals?: number;
  completed?: number;
  stopped?: number;
  expired?: number;
  active?: number;
  win_rate: number;
  net_pips: number;
  avg_pips: number;
}

interface AnalyticsMeta {
  requested_model?: string;
  selected_model?: string;
  selected_timeframe?: string;
  available_timeframes?: string[];
  available_models?: string[];
  days?: number;
  all_time?: boolean;
  date_from?: string | null;
  date_to?: string | null;
  scope_total_signals?: number;
  filtered_total_signals?: number;
  traceback?: string;
}

interface AnalyticsData {
  model: string;
  symbol: string;
  overview: {
    total_signals: number;
    win_rate: number;
    completed: number;
    stopped: number;
    expired: number;
    active: number;
    net_pips: number;
    avg_profit_pips: number;
    avg_loss_pips: number;
    risk_reward: number;
    sharpe_ratio: number;
    max_drawdown_pips: number;
    profit_factor: number;
  };
  hourly_heatmap: HourlyData[];
  timeframe_comparison: TFData[];
  daily_accuracy: DailyData[];
  day_of_week: DOWData[];
  tp_hit_rates: Record<string, number>;
  recent_signals: RecentSignal[];
  selected_timeframe?: string;
  available_timeframes?: string[];
  available_models?: string[];
  model_comparison?: ModelComparisonRow[];
  meta?: AnalyticsMeta;
  error?: string;
}

interface ModelPerformanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  model?: string;
}

const T = {
  en: {
    overview: "Overview",
    timeframes: "Timeframes",
    hourly: "Hourly",
    dayOfWeek: "Weekdays",
    insightPulse: "Insight pulse",
    winRate: "Win rate",
    netPips: "Net pips",
    resolved: "Resolved",
    profitFactor: "Profit factor",
    sharpe: "Sharpe",
    maxDrawdown: "Max drawdown",
    edgeQuality: "Edge quality",
    active: "Active",
    completed: "Wins",
    stopped: "Losses",
    expired: "Expired",
    allModels: "All models",
    allTimeframes: "All TF",
    allHistory: "All history",
    filteredScope: "Filtered scope",
    modelBenchmark: "Cross-model benchmark",
    scopeSummary: "Scope summary",
    timeframeDistribution: "Timeframe distribution",
    dailyTrend: "Daily equity curve",
    tpHitRates: "Target hit rates",
    recentSignals: "Recent signals",
    date: "Date",
    direction: "Direction",
    confidence: "Confidence",
    status: "Status",
    pips: "Pips",
    timeframe: "Timeframe",
    totalSignals: "Signals",
    avgPips: "Avg pips",
    bestTimeframe: "Best timeframe",
    bestHour: "Best hour",
    bestDay: "Best day",
    biggestSample: "Largest sample",
    coveredTimeframes: "Covered TF",
    model: "Model",
    bestHoursUtc: "Best hours (UTC)",
    weakHoursUtc: "Weak hours (UTC)",
    noTrades: "No trades",
    signalsLower: "signals",
    strongEdge: "Strong edge",
    mixedEdge: "Mixed edge",
    fragileEdge: "Fragile edge",
    edgeNoteStrong: "Win rate, profit factor and net pips are aligned positively.",
    edgeNoteMixed: "The setup is tradable, but edge quality is uneven across the sample.",
    edgeNoteFragile: "Recent results need caution; size and drawdown should be watched.",
    sampleConfidence: "Sample confidence",
    highConfidence: "High confidence",
    buildingConfidence: "Building confidence",
    limitedSample: "Limited sample",
    benchmarkNote:
      "Overview, hourly and weekday analytics respect the selected timeframe. The benchmark table compares all available timeframes within the current model scope.",
    noData: "No resolved signal history was found for this scope.",
    loading: "Loading analytics…",
    retry: "Retry",
    close: "Close",
    analytics: "Performance analytics",
    selectedScope: "Selected scope",
    availableModels: "Available models",
    refreshing: "Refreshing",
  },
  tr: {
    overview: "Genel Bakış",
    timeframes: "Timeframe'ler",
    hourly: "Saatlik",
    dayOfWeek: "Hafta Günleri",
    insightPulse: "İçgörü özeti",
    winRate: "Başarı oranı",
    netPips: "Net pips",
    resolved: "Sonuçlanan",
    profitFactor: "Kâr faktörü",
    sharpe: "Sharpe",
    maxDrawdown: "Maks. düşüş",
    edgeQuality: "Kenar kalitesi",
    active: "Aktif",
    completed: "Kazanç",
    stopped: "Kayıp",
    expired: "Süresi dolan",
    allModels: "Tüm modeller",
    allTimeframes: "Tüm TF",
    allHistory: "Tüm geçmiş",
    filteredScope: "Filtrelenen kapsam",
    modelBenchmark: "Modeller arası kıyas",
    scopeSummary: "Kapsam özeti",
    timeframeDistribution: "Timeframe dağılımı",
    dailyTrend: "Günlük getiri eğrisi",
    tpHitRates: "Hedef isabet oranları",
    recentSignals: "Son sinyaller",
    date: "Tarih",
    direction: "Yön",
    confidence: "Güven",
    status: "Durum",
    pips: "Pips",
    timeframe: "Timeframe",
    totalSignals: "Sinyal",
    avgPips: "Ort. pips",
    bestTimeframe: "En iyi timeframe",
    bestHour: "En iyi saat",
    bestDay: "En iyi gün",
    biggestSample: "En büyük örneklem",
    coveredTimeframes: "Kapsanan TF",
    model: "Model",
    bestHoursUtc: "En iyi saatler (UTC)",
    weakHoursUtc: "Zayıf saatler (UTC)",
    noTrades: "İşlem yok",
    signalsLower: "sinyal",
    strongEdge: "Güçlü avantaj",
    mixedEdge: "Karışık avantaj",
    fragileEdge: "Kırılgan yapı",
    edgeNoteStrong: "Başarı oranı, kâr faktörü ve net pips birlikte pozitif hizalanıyor.",
    edgeNoteMixed: "Kurgu işlem alınabilir seviyede, ancak örneklem boyunca kalite dalgalı.",
    edgeNoteFragile: "Sonuçlar dikkat gerektiriyor; pozisyon boyutu ve drawdown yakından izlenmeli.",
    sampleConfidence: "Örneklem güveni",
    highConfidence: "Yüksek güven",
    buildingConfidence: "Gelişen güven",
    limitedSample: "Sınırlı örneklem",
    benchmarkNote:
      "Genel bakış, saatlik ve hafta günü analizleri seçili timeframe'e göre filtrelenir. Aşağıdaki benchmark tablosu aynı model kapsamındaki tüm timeframe'leri karşılaştırır.",
    noData: "Bu kapsam için sonuçlanmış sinyal geçmişi bulunamadı.",
    loading: "Analitik yükleniyor…",
    retry: "Tekrar dene",
    close: "Kapat",
    analytics: "Performans analitiği",
    selectedScope: "Seçili kapsam",
    availableModels: "Mevcut modeller",
    refreshing: "Güncelleniyor",
  },
} as const;

type LocaleCopy = (typeof T)[keyof typeof T];

const SYM_DISPLAY: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL",
  "CL.F": "US OIL",
};

const MODEL_DISPLAY: Record<string, string> = {
  all: "All Models",
  ml: "ML Model",
  emel: "EMEL 9-Check",
  pulse1: "Pulse 1 — Algo",
  pulse2: "Pulse 2 — ML",
  pulse3: "Pulse 3 — Scalp",
  emel_inverse: "EMEL Inverse",
  hybrid: "Hybrid",
};

function getLanguage(): "en" | "tr" {
  if (typeof window === "undefined") return "en";
  const saved = localStorage.getItem("language");
  if (saved === "tr" || saved === "en") return saved;
  return navigator.language?.toLowerCase().startsWith("tr") ? "tr" : "en";
}

function sortTimeframes(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => {
    const aIndex = TF_ORDER.indexOf(a);
    const bIndex = TF_ORDER.indexOf(b);
    return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex) || a.localeCompare(b);
  });
}

function wrColor(rate: number) {
  if (rate >= 65) return "var(--accent-positive)";
  if (rate >= 50) return "var(--accent-info)";
  if (rate >= 40) return "var(--accent-warning)";
  return "var(--accent-negative)";
}

function statusColor(status: string) {
  if (status === "completed") return "var(--accent-positive)";
  if (status === "stopped") return "var(--accent-negative)";
  if (status === "active") return "var(--accent-info)";
  if (status === "expired") return "var(--accent-warning)";
  return "var(--text-muted)";
}

function formatPips(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}p`;
}

function formatDateRange(start?: string | null, end?: string | null, lang: "en" | "tr" = "en") {
  if (!start || !end) return "—";
  const locale = lang === "tr" ? "tr-TR" : "en-US";
  const startDate = new Date(start);
  const endDate = new Date(end);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return "—";
  return `${startDate.toLocaleDateString(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })} → ${endDate.toLocaleDateString(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })}`;
}

function formatHour(hour: number) {
  return `${String(hour).padStart(2, "0")}:00`;
}

function emptyAnalytics(symbol: string, model?: string): AnalyticsData {
  return {
    model: model || "all",
    symbol,
    overview: {
      total_signals: 0,
      win_rate: 0,
      completed: 0,
      stopped: 0,
      expired: 0,
      active: 0,
      net_pips: 0,
      avg_profit_pips: 0,
      avg_loss_pips: 0,
      risk_reward: 0,
      sharpe_ratio: 0,
      max_drawdown_pips: 0,
      profit_factor: 0,
    },
    hourly_heatmap: [],
    timeframe_comparison: [],
    daily_accuracy: [],
    day_of_week: [],
    tp_hit_rates: {},
    recent_signals: [],
    available_timeframes: [],
    available_models: [],
    model_comparison: [],
    meta: {
      selected_model: model || "all",
      selected_timeframe: "all",
      filtered_total_signals: 0,
      scope_total_signals: 0,
    },
    selected_timeframe: "all",
  };
}

function hasAnalyticsContent(data?: AnalyticsData | null) {
  return Boolean(
    (data?.overview?.total_signals || 0) > 0 ||
      (data?.timeframe_comparison?.length || 0) > 0 ||
      (data?.model_comparison?.length || 0) > 1 ||
      (data?.recent_signals?.length || 0) > 0
  );
}

function AnalyticsTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: 10,
        padding: "10px 12px",
      }}
    >
      <p style={{ color: "var(--text-muted)", fontSize: 11, marginBottom: 4 }}>{label}</p>
      {payload.map((entry: any, index: number) => (
        <div key={`${entry.name}-${index}`} className="flex items-center gap-2" style={{ marginTop: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 999, background: entry.color }} />
          <span style={{ color: "var(--text-primary)", fontSize: 12 }}>
            {entry.name}: {typeof entry.value === "number" ? entry.value.toFixed(1) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export const ModelPerformanceModal: React.FC<ModelPerformanceModalProps> = ({
  isOpen,
  onClose,
  symbol,
  model,
}) => {
  const lang = useMemo(() => getLanguage(), [isOpen]);
  const copy = T[lang];
  const [activeTab, setActiveTab] = useState<"overview" | "timeframes" | "hourly" | "dayOfWeek">(
    "overview"
  );
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("all");

  useEffect(() => {
    if (!isOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    setActiveTab("overview");
    setSelectedTimeframe("all");
  }, [isOpen, model, symbol]);

  const { data, isLoading, isFetching, error, refetch } = useQuery<AnalyticsData>({
    queryKey: ["model-detail-analytics", model || "all", symbol, selectedTimeframe],
    queryFn: async () => {
      const params = new URLSearchParams({ symbol });
      if (model) params.set("model", model);
      if (selectedTimeframe !== "all") params.set("timeframe", selectedTimeframe);

      const response = await fetch(`${API_BASE}/api/learning/model-detail-analytics?${params.toString()}`);
      const payload = (await response.json().catch(() => null)) as AnalyticsData | null;

      if (!response.ok) {
        throw new Error(payload?.error || "Failed to load analytics");
      }

      const analytics = payload || emptyAnalytics(symbol, model);
      if (analytics.error && !hasAnalyticsContent(analytics)) {
        throw new Error(analytics.error);
      }

      return analytics;
    },
    enabled: isOpen && !!symbol,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });

  if (!isOpen) return null;

  const effectiveModel = data?.meta?.selected_model || data?.model || model || "all";
  const effectiveTimeframe = data?.selected_timeframe || data?.meta?.selected_timeframe || selectedTimeframe;
  const availableTimeframes = sortTimeframes([
    "all",
    ...(data?.available_timeframes || []),
    effectiveTimeframe,
  ]);
  const headerModelLabel =
    effectiveModel === "all" ? copy.allModels : MODEL_DISPLAY[effectiveModel] || effectiveModel;
  const headerSymbolLabel = SYM_DISPLAY[symbol] || symbol;
  const queryError = error instanceof Error ? error.message : undefined;
  const displayWarning = queryError ? undefined : data?.error;
  const overview = data?.overview;
  const hasData = hasAnalyticsContent(data);
  const meta = data?.meta;

  const tabs = [
    { key: "overview" as const, label: copy.overview },
    { key: "timeframes" as const, label: copy.timeframes },
    { key: "hourly" as const, label: copy.hourly },
    { key: "dayOfWeek" as const, label: copy.dayOfWeek },
  ];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        style={{ background: "rgba(0,0,0,0.72)", backdropFilter: "blur(10px)" }}
        onClick={onClose}
      >
        <motion.div
          initial={{ y: 16, scale: 0.98, opacity: 0 }}
          animate={{ y: 0, scale: 1, opacity: 1 }}
          exit={{ y: 16, scale: 0.98, opacity: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 24 }}
          className="w-full max-w-6xl max-h-[92vh] overflow-y-auto rounded-3xl"
          style={{
            background: "var(--bg-primary)",
            border: "1px solid var(--border-subtle)",
            boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
          }}
          onClick={(event) => event.stopPropagation()}
        >
          <div
            className="sticky top-0 z-10"
            style={{
              background: "rgba(8, 12, 20, 0.92)",
              backdropFilter: "blur(12px)",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <div className="px-6 pt-5 pb-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <ScopeBadge label={headerModelLabel} tone="info" />
                    <ScopeBadge
                      label={effectiveTimeframe === "all" ? copy.allTimeframes : effectiveTimeframe.toUpperCase()}
                      tone="neutral"
                    />
                    <ScopeBadge label={meta?.all_time ? copy.allHistory : `${meta?.days || 0}d`} tone="neutral" />
                    {isFetching && !isLoading && <ScopeBadge label={copy.refreshing} tone="warning" />}
                  </div>
                  <h2
                    style={{
                      fontSize: 26,
                      fontWeight: 700,
                      color: "var(--text-primary)",
                      letterSpacing: "-0.03em",
                    }}
                  >
                    {headerSymbolLabel}{" "}
                    <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>{copy.analytics}</span>
                  </h2>
                  <p style={{ marginTop: 6, fontSize: 13, color: "var(--text-muted)" }}>
                    {formatDateRange(meta?.date_from, meta?.date_to, lang)}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="rounded-xl px-3 py-2 transition-colors"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-primary)",
                  }}
                >
                  {copy.close}
                </button>
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-2 overflow-x-auto pb-1">
                {availableTimeframes.map((tf) => {
                  const selected = selectedTimeframe === tf;
                  return (
                    <button
                      key={tf}
                      onClick={() => setSelectedTimeframe(tf)}
                      className="rounded-full px-3 py-1.5 whitespace-nowrap transition-all"
                      style={{
                        background: selected ? "rgba(79,140,255,0.14)" : "var(--bg-card)",
                        border: selected
                          ? "1px solid rgba(79,140,255,0.35)"
                          : "1px solid var(--border-subtle)",
                        color: selected ? "var(--accent-info)" : "var(--text-muted)",
                        fontSize: 12,
                        fontWeight: 600,
                      }}
                    >
                      {tf === "all" ? copy.allTimeframes : tf.toUpperCase()}
                    </button>
                  );
                })}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {tabs.map((tab) => {
                  const selected = activeTab === tab.key;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className="rounded-xl px-3.5 py-2 transition-all"
                      style={{
                        background: selected ? "var(--bg-card)" : "transparent",
                        border: selected
                          ? "1px solid var(--border-subtle)"
                          : "1px solid transparent",
                        color: selected ? "var(--text-primary)" : "var(--text-muted)",
                        fontSize: 12,
                        fontWeight: 700,
                      }}
                    >
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="p-6 space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
              <InfoPill
                label={copy.filteredScope}
                value={`${meta?.filtered_total_signals ?? overview?.total_signals ?? 0}${
                  meta?.scope_total_signals && meta.scope_total_signals !== (meta.filtered_total_signals ?? 0)
                    ? ` / ${meta.scope_total_signals}`
                    : ""
                }`}
              />
              <InfoPill
                label={copy.selectedScope}
                value={`${headerModelLabel} · ${
                  effectiveTimeframe === "all" ? copy.allTimeframes : effectiveTimeframe.toUpperCase()
                }`}
              />
              <InfoPill
                label={copy.availableModels}
                value={`${data?.available_models?.length || (effectiveModel === "all" ? 0 : 1) || 0}`}
              />
            </div>

            {displayWarning && (
              <div
                style={{
                  background: "rgba(245, 158, 11, 0.10)",
                  border: "1px solid rgba(245, 158, 11, 0.22)",
                  color: "var(--text-primary)",
                  borderRadius: 16,
                  padding: 14,
                }}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span style={{ fontSize: 13 }}>{displayWarning}</span>
                  <button onClick={() => refetch()} style={{ color: "var(--accent-warning)", fontSize: 12, fontWeight: 700 }}>
                    {copy.retry}
                  </button>
                </div>
              </div>
            )}

            {isLoading ? (
              <LoadingState label={copy.loading} />
            ) : queryError ? (
              <ErrorState label={queryError} onRetry={() => refetch()} retryLabel={copy.retry} />
            ) : !hasData || !data ? (
              <EmptyState label={copy.noData} onRetry={() => refetch()} retryLabel={copy.retry} />
            ) : activeTab === "overview" ? (
              <OverviewPanel
                data={data}
                copy={copy}
                lang={lang}
                effectiveModel={effectiveModel}
                selectedTimeframe={effectiveTimeframe}
              />
            ) : activeTab === "timeframes" ? (
              <TimeframesPanel data={data.timeframe_comparison} copy={copy} />
            ) : activeTab === "hourly" ? (
              <HourlyPanel data={data.hourly_heatmap} copy={copy} />
            ) : (
              <WeekdayPanel data={data.day_of_week} copy={copy} />
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

function OverviewPanel({
  data,
  copy,
  lang,
  effectiveModel,
  selectedTimeframe,
}: {
  data: AnalyticsData;
  copy: LocaleCopy;
  lang: "en" | "tr";
  effectiveModel: string;
  selectedTimeframe: string;
}) {
  const ov = data.overview;
  const resolved = ov.completed + ov.stopped;
  const modelRows = (data.model_comparison || []).filter((row) => (row.total || 0) > 0);
  const bestTimeframe = [...data.timeframe_comparison]
    .filter((row) => row.total > 0)
    .sort((a, b) => b.win_rate - a.win_rate || b.net_pips - a.net_pips)[0];
  const bestHour = [...data.hourly_heatmap]
    .filter((row) => row.total > 0)
    .sort((a, b) => b.win_rate - a.win_rate || b.avg_pips - a.avg_pips)[0];
  const bestDay = [...data.day_of_week]
    .filter((row) => row.total > 0)
    .sort((a, b) => b.win_rate - a.win_rate || b.avg_pips - a.avg_pips)[0];
  const edgeTone =
    ov.win_rate >= 57 && ov.profit_factor >= 1.4 && ov.net_pips >= 0
      ? {
          label: copy.strongEdge,
          note: copy.edgeNoteStrong,
          accent: "var(--accent-positive)",
        }
      : ov.win_rate >= 48 && ov.profit_factor >= 1
        ? {
            label: copy.mixedEdge,
            note: copy.edgeNoteMixed,
            accent: "var(--accent-warning)",
          }
        : {
            label: copy.fragileEdge,
            note: copy.edgeNoteFragile,
            accent: "var(--accent-negative)",
          };
  const sampleTone =
    resolved >= 40
      ? { label: copy.highConfidence, accent: "var(--accent-positive)" }
      : resolved >= 15
        ? { label: copy.buildingConfidence, accent: "var(--accent-info)" }
        : { label: copy.limitedSample, accent: "var(--accent-warning)" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 xl:grid-cols-6 gap-3">
        <MetricCard
          label={copy.winRate}
          value={`${ov.win_rate.toFixed(1)}%`}
          accent={wrColor(ov.win_rate)}
          sub={`${resolved} ${copy.resolved.toLowerCase()}`}
        />
        <MetricCard
          label={copy.netPips}
          value={formatPips(ov.net_pips)}
          accent={ov.net_pips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)"}
          sub={`${copy.active}: ${ov.active}`}
        />
        <MetricCard
          label={copy.resolved}
          value={`${resolved}`}
          accent="var(--text-primary)"
          sub={`${copy.completed}: ${ov.completed} · ${copy.stopped}: ${ov.stopped}`}
        />
        <MetricCard
          label={copy.profitFactor}
          value={ov.profit_factor.toFixed(2)}
          accent="var(--accent-warning)"
          sub={`R/R ${ov.risk_reward.toFixed(2)}`}
        />
        <MetricCard
          label={copy.sharpe}
          value={ov.sharpe_ratio.toFixed(2)}
          accent="var(--accent-info)"
          sub={`${copy.timeframe}: ${selectedTimeframe === "all" ? copy.allTimeframes : selectedTimeframe.toUpperCase()}`}
        />
        <MetricCard
          label={copy.maxDrawdown}
          value={`-${ov.max_drawdown_pips.toFixed(1)}p`}
          accent="var(--accent-negative)"
          sub={`${copy.expired}: ${ov.expired}`}
        />
      </div>

      <SectionCard title={copy.insightPulse}>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <InsightCard label={copy.edgeQuality} value={edgeTone.label} detail={edgeTone.note} accent={edgeTone.accent} />
          <InsightCard
            label={copy.bestTimeframe}
            value={bestTimeframe ? bestTimeframe.tf.toUpperCase() : "—"}
            detail={bestTimeframe ? `${bestTimeframe.win_rate.toFixed(1)}% · ${formatPips(bestTimeframe.net_pips)}` : copy.noData}
            accent={bestTimeframe ? wrColor(bestTimeframe.win_rate) : "var(--text-muted)"}
          />
          <InsightCard
            label={copy.bestHour}
            value={bestHour ? formatHour(bestHour.hour) : "—"}
            detail={bestHour ? `${bestHour.win_rate.toFixed(1)}% · ${bestHour.total} ${copy.signalsLower}` : copy.noData}
            accent={bestHour ? wrColor(bestHour.win_rate) : "var(--text-muted)"}
          />
          <InsightCard
            label={copy.bestDay}
            value={bestDay ? bestDay.day_short : "—"}
            detail={bestDay ? `${bestDay.win_rate.toFixed(1)}% · ${formatPips(bestDay.avg_pips)}` : copy.noData}
            accent={bestDay ? wrColor(bestDay.win_rate) : "var(--text-muted)"}
          />
        </div>

        <div
          className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-2xl px-4 py-3"
          style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
        >
          <div>
            <p style={{ fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
              {copy.sampleConfidence}
            </p>
            <p style={{ marginTop: 6, fontSize: 16, fontWeight: 800, color: sampleTone.accent }}>{sampleTone.label}</p>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {resolved} {copy.resolved.toLowerCase()} · {ov.total_signals} {copy.totalSignals.toLowerCase()} · {copy.timeframe}:{" "}
            {selectedTimeframe === "all" ? copy.allTimeframes : selectedTimeframe.toUpperCase()}
          </p>
        </div>
      </SectionCard>

      <SectionCard title={copy.scopeSummary}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MiniSummary label={copy.completed} value={ov.completed} color="var(--accent-positive)" />
          <MiniSummary label={copy.stopped} value={ov.stopped} color="var(--accent-negative)" />
          <MiniSummary label={copy.expired} value={ov.expired} color="var(--accent-warning)" />
          <MiniSummary label={copy.active} value={ov.active} color="var(--accent-info)" />
        </div>
      </SectionCard>

      {modelRows.length > 1 && (
        <SectionCard title={copy.modelBenchmark}>
          <div className="overflow-x-auto">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {[copy.model, copy.totalSignals, copy.winRate, copy.netPips, copy.avgPips].map((header) => (
                    <th key={header} style={tableHeadStyle}>
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modelRows.map((row) => {
                  const selected = row.model === effectiveModel;
                  return (
                    <tr
                      key={row.model}
                      style={{
                        background: selected ? "rgba(79,140,255,0.08)" : "transparent",
                        borderBottom: "1px solid var(--border-subtle)",
                      }}
                    >
                      <td style={tableCellStyle}>
                        <span style={{ color: selected ? "var(--accent-info)" : "var(--text-primary)", fontWeight: 700 }}>
                          {MODEL_DISPLAY[row.model] || row.model}
                        </span>
                      </td>
                      <td style={tableCellStyle}>{row.total}</td>
                      <td style={{ ...tableCellStyle, color: wrColor(row.win_rate), fontWeight: 700 }}>
                        {row.win_rate.toFixed(1)}%
                      </td>
                      <td
                        style={{
                          ...tableCellStyle,
                          color: row.net_pips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)",
                          fontWeight: 700,
                        }}
                      >
                        {formatPips(row.net_pips)}
                      </td>
                      <td style={tableCellStyle}>{row.avg_pips.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <SectionCard title={copy.dailyTrend} className="xl:col-span-2">
          {data.daily_accuracy.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data.daily_accuracy}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                  tickFormatter={(value: string) => value.slice(5)}
                />
                <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
                <Tooltip content={<AnalyticsTooltip />} />
                <Line
                  type="monotone"
                  dataKey="cumulative_pips"
                  stroke="var(--accent-info)"
                  strokeWidth={2.5}
                  dot={false}
                  name={copy.netPips}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <MutedEmpty>{copy.noData}</MutedEmpty>
          )}
        </SectionCard>

        <SectionCard title={copy.tpHitRates}>
          <div className="space-y-3">
            {["TP1", "TP2", "TP3", "TP4"].map((tp) => {
              const rate = data.tp_hit_rates?.[tp] || 0;
              return (
                <div key={tp}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span style={{ fontSize: 12, color: "var(--text-primary)", fontWeight: 600 }}>{tp}</span>
                    <span style={{ fontSize: 12, color: wrColor(rate), fontWeight: 700 }}>{rate.toFixed(1)}%</span>
                  </div>
                  <div style={{ height: 8, borderRadius: 999, background: "var(--bg-primary)", overflow: "hidden" }}>
                    <div style={{ width: `${rate}%`, height: "100%", borderRadius: 999, background: wrColor(rate) }} />
                  </div>
                </div>
              );
            })}
          </div>
        </SectionCard>
      </div>

      <SectionCard title={copy.recentSignals}>
        {data.recent_signals.length > 0 ? (
          <div className="overflow-x-auto">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {[copy.date, copy.direction, copy.timeframe, copy.confidence, copy.status, copy.pips].map((header) => (
                    <th key={header} style={tableHeadStyle}>
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.recent_signals.slice(0, 12).map((signal) => (
                  <tr key={`${signal.id}-${signal.date}`} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={tableCellStyle}>
                      {new Date(signal.date || Date.now()).toLocaleString(lang === "tr" ? "tr-TR" : "en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td
                      style={{
                        ...tableCellStyle,
                        color:
                          signal.direction === "BUY"
                            ? "var(--accent-positive)"
                            : signal.direction === "SELL"
                              ? "var(--accent-negative)"
                              : "var(--text-muted)",
                        fontWeight: 700,
                      }}
                    >
                      {signal.direction}
                    </td>
                    <td style={tableCellStyle}>{signal.timeframe.toUpperCase()}</td>
                    <td style={tableCellStyle}>{signal.confidence.toFixed(1)}%</td>
                    <td style={tableCellStyle}>
                      <span
                        style={{
                          background: "var(--bg-primary)",
                          border: "1px solid var(--border-subtle)",
                          color: statusColor(signal.status),
                          borderRadius: 999,
                          padding: "4px 10px",
                          fontSize: 11,
                          fontWeight: 700,
                        }}
                      >
                        {signal.status.toUpperCase()}
                      </span>
                    </td>
                    <td
                      style={{
                        ...tableCellStyle,
                        color: signal.pips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)",
                        fontWeight: 700,
                      }}
                    >
                      {formatPips(signal.pips)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <MutedEmpty>{copy.noData}</MutedEmpty>
        )}
      </SectionCard>
    </div>
  );
}

function TimeframesPanel({ data, copy }: { data: TFData[]; copy: LocaleCopy }) {
  if (!data.length) return <EmptyCard label={copy.noData} />;

  const best = [...data].sort((a, b) => b.win_rate - a.win_rate || b.net_pips - a.net_pips)[0];
  const largest = [...data].sort((a, b) => b.total - a.total)[0];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <MetricCard
          label={copy.bestTimeframe}
          value={best.tf.toUpperCase()}
          accent={wrColor(best.win_rate)}
          sub={`${best.win_rate.toFixed(1)}% · ${formatPips(best.net_pips)}`}
        />
        <MetricCard
          label={copy.biggestSample}
          value={largest.tf.toUpperCase()}
          accent="var(--text-primary)"
          sub={`${largest.total} ${copy.totalSignals.toLowerCase()}`}
        />
        <MetricCard
          label={copy.coveredTimeframes}
          value={`${data.length}`}
          accent="var(--accent-info)"
          sub={copy.timeframeDistribution}
        />
      </div>

      <SectionCard title={copy.timeframeDistribution} subtitle={copy.benchmarkNote}>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey="tf" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
            <YAxis tick={{ fill: "var(--text-muted)", fontSize: 11 }} domain={[0, 100]} />
            <Tooltip content={<AnalyticsTooltip />} />
            <Bar dataKey="win_rate" name={copy.winRate} radius={[8, 8, 0, 0]}>
              {data.map((row) => (
                <Cell key={row.tf} fill={row.tf === best.tf ? "var(--accent-info)" : wrColor(row.win_rate)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </SectionCard>

      <SectionCard title={copy.timeframes}>
        <div className="overflow-x-auto">
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {[copy.timeframe, copy.totalSignals, copy.active, copy.winRate, copy.netPips, copy.avgPips].map((header) => (
                  <th key={header} style={tableHeadStyle}>
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr
                  key={row.tf}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    background: row.tf === best.tf ? "rgba(79,140,255,0.08)" : "transparent",
                  }}
                >
                  <td
                    style={{
                      ...tableCellStyle,
                      color: row.tf === best.tf ? "var(--accent-info)" : "var(--text-primary)",
                      fontWeight: 700,
                    }}
                  >
                    {row.tf.toUpperCase()}
                  </td>
                  <td style={tableCellStyle}>{row.total}</td>
                  <td style={tableCellStyle}>{row.active || 0}</td>
                  <td style={{ ...tableCellStyle, color: wrColor(row.win_rate), fontWeight: 700 }}>
                    {row.win_rate.toFixed(1)}%
                  </td>
                  <td
                    style={{
                      ...tableCellStyle,
                      color: row.net_pips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)",
                      fontWeight: 700,
                    }}
                  >
                    {formatPips(row.net_pips)}
                  </td>
                  <td style={tableCellStyle}>{row.avg_pips.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}

function HourlyPanel({ data, copy }: { data: HourlyData[]; copy: LocaleCopy }) {
  const populated = data.filter((row) => row.total > 0);
  if (!populated.length) return <EmptyCard label={copy.noData} />;

  const best = [...populated].sort((a, b) => b.win_rate - a.win_rate).slice(0, 3);
  const worst = [...populated].sort((a, b) => a.win_rate - b.win_rate).slice(0, 3);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SectionCard title={copy.bestHoursUtc}>
          <div className="space-y-2">
            {best.map((row) => (
              <HourRow key={row.hour} row={row} positive copy={copy} />
            ))}
          </div>
        </SectionCard>
        <SectionCard title={copy.weakHoursUtc}>
          <div className="space-y-2">
            {worst.map((row) => (
              <HourRow key={row.hour} row={row} positive={false} copy={copy} />
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title={copy.hourly}>
        <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-6 gap-3">
          {data.map((row) => (
            <div
              key={row.hour}
              style={{
                background: row.total > 0 ? "var(--bg-card)" : "var(--bg-primary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 14,
                padding: 14,
              }}
            >
              <div className="flex items-center justify-between gap-2">
                <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>
                  {formatHour(row.hour)}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: row.total > 0 ? wrColor(row.win_rate) : "var(--text-muted)",
                    fontWeight: 700,
                  }}
                >
                  {row.total > 0 ? `${row.win_rate.toFixed(1)}%` : "—"}
                </span>
              </div>
              <p style={{ marginTop: 10, fontSize: 11, color: "var(--text-muted)" }}>
                {row.total > 0 ? `${row.wins}/${row.total}` : copy.noTrades}
              </p>
              {row.total > 0 && (
                <p
                  style={{
                    marginTop: 4,
                    fontSize: 12,
                    color: row.avg_pips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)",
                    fontWeight: 700,
                  }}
                >
                  {formatPips(row.avg_pips)}
                </p>
              )}
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

function WeekdayPanel({ data, copy }: { data: DOWData[]; copy: LocaleCopy }) {
  const populated = data.filter((row) => row.total > 0);
  if (!populated.length) return <EmptyCard label={copy.noData} />;

  return (
    <div className="space-y-4">
      <SectionCard title={copy.dayOfWeek}>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={populated} layout="vertical">
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
            <YAxis
              dataKey="day_short"
              type="category"
              tick={{ fill: "var(--text-primary)", fontSize: 12 }}
              width={48}
            />
            <Tooltip content={<AnalyticsTooltip />} />
            <Bar dataKey="win_rate" name={copy.winRate} radius={[0, 8, 8, 0]}>
              {populated.map((row) => (
                <Cell key={row.day} fill={wrColor(row.win_rate)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </SectionCard>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
        {populated.map((row) => (
          <div
            key={row.day}
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 16,
              padding: 16,
            }}
          >
            <div className="flex items-center justify-between gap-3">
              <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{row.day}</span>
              <span style={{ fontSize: 14, fontWeight: 700, color: wrColor(row.win_rate) }}>
                {row.win_rate.toFixed(1)}%
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[12px]" style={{ color: "var(--text-muted)" }}>
              <span>
                {row.total} {copy.totalSignals.toLowerCase()}
              </span>
              <span
                style={{
                  color: row.avg_pips >= 0 ? "var(--accent-positive)" : "var(--accent-negative)",
                  fontWeight: 700,
                }}
              >
                {formatPips(row.avg_pips)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SectionCard({
  title,
  subtitle,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={className}
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: 20,
        padding: 18,
      }}
    >
      <div className="mb-4">
        <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>{title}</p>
        {subtitle && <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent,
  sub,
}: {
  label: string;
  value: string;
  accent: string;
  sub?: string;
}) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 18, padding: 16 }}>
      <p
        style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
        }}
      >
        {label}
      </p>
      <p style={{ marginTop: 8, fontSize: 24, fontWeight: 800, color: accent, letterSpacing: "-0.03em" }}>{value}</p>
      {sub && <p style={{ marginTop: 6, fontSize: 12, color: "var(--text-muted)" }}>{sub}</p>}
    </div>
  );
}

function MiniSummary({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 14, padding: 14 }}>
      <p style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </p>
      <p style={{ marginTop: 6, fontSize: 22, fontWeight: 800, color }}>{value}</p>
    </div>
  );
}

function ScopeBadge({ label, tone }: { label: string; tone: "info" | "neutral" | "warning" }) {
  const styles = {
    info: {
      background: "rgba(79,140,255,0.12)",
      border: "1px solid rgba(79,140,255,0.28)",
      color: "var(--accent-info)",
    },
    neutral: {
      background: "var(--bg-card)",
      border: "1px solid var(--border-subtle)",
      color: "var(--text-muted)",
    },
    warning: {
      background: "rgba(245, 158, 11, 0.10)",
      border: "1px solid rgba(245, 158, 11, 0.22)",
      color: "var(--accent-warning)",
    },
  } as const;

  return (
    <span
      style={{
        ...styles[tone],
        borderRadius: 999,
        padding: "6px 10px",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
      }}
    >
      {label}
    </span>
  );
}

function InfoPill({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 16, padding: "12px 14px" }}>
      <p
        style={{
          fontSize: 10,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
          fontWeight: 700,
        }}
      >
        {label}
      </p>
      <p style={{ marginTop: 6, fontSize: 14, color: "var(--text-primary)", fontWeight: 700 }}>{value}</p>
    </div>
  );
}

function HourRow({ row, positive, copy }: { row: HourlyData; positive: boolean; copy: LocaleCopy }) {
  return (
    <div className="flex items-center justify-between rounded-xl px-3 py-3" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
      <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>{formatHour(row.hour)}</span>
      <div className="text-right">
        <p style={{ color: positive ? "var(--accent-positive)" : "var(--accent-negative)", fontWeight: 700 }}>
          {row.win_rate.toFixed(1)}%
        </p>
        <p style={{ color: "var(--text-muted)", fontSize: 12 }}>{row.total} {copy.signalsLower}</p>
      </div>
    </div>
  );
}

function InsightCard({
  label,
  value,
  detail,
  accent,
}: {
  label: string;
  value: string;
  detail: string;
  accent: string;
}) {
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 16, padding: 14 }}>
      <p style={{ fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
        {label}
      </p>
      <p style={{ marginTop: 8, fontSize: 20, fontWeight: 800, color: accent, letterSpacing: "-0.03em" }}>{value}</p>
      <p style={{ marginTop: 6, fontSize: 12, color: "var(--text-muted)", lineHeight: 1.45 }}>{detail}</p>
    </div>
  );
}

function EmptyState({
  label,
  onRetry,
  retryLabel,
}: {
  label: string;
  onRetry: () => void;
  retryLabel: string;
}) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 20, padding: 36, textAlign: "center" }}>
      <p style={{ color: "var(--text-primary)", fontSize: 15, fontWeight: 600 }}>{label}</p>
      <button
        onClick={onRetry}
        className="mt-4 rounded-xl px-4 py-2"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          color: "var(--text-primary)",
          fontWeight: 700,
          fontSize: 12,
        }}
      >
        {retryLabel}
      </button>
    </div>
  );
}

function ErrorState({
  label,
  onRetry,
  retryLabel,
}: {
  label: string;
  onRetry: () => void;
  retryLabel: string;
}) {
  return (
    <div
      style={{
        background: "rgba(245, 158, 11, 0.10)",
        border: "1px solid rgba(245, 158, 11, 0.22)",
        borderRadius: 20,
        padding: 36,
        textAlign: "center",
      }}
    >
      <p style={{ color: "var(--text-primary)", fontSize: 15, fontWeight: 600 }}>{label}</p>
      <button
        onClick={onRetry}
        className="mt-4 rounded-xl px-4 py-2"
        style={{
          background: "var(--bg-card)",
          border: "1px solid rgba(245, 158, 11, 0.22)",
          color: "var(--text-primary)",
          fontWeight: 700,
          fontSize: 12,
        }}
      >
        {retryLabel}
      </button>
    </div>
  );
}

function EmptyCard({ label }: { label: string }) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 20, padding: 32 }}>
      <MutedEmpty>{label}</MutedEmpty>
    </div>
  );
}

function MutedEmpty({ children }: { children: React.ReactNode }) {
  return <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: 13, padding: 20 }}>{children}</div>;
}

function LoadingState({ label }: { label: string }) {
  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: 20, padding: 32 }}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        {[0, 1, 2].map((item) => (
          <SkeletonCard key={item} height={100} />
        ))}
      </div>
      <SkeletonCard height={220} />
      <p style={{ marginTop: 16, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>{label}</p>
    </div>
  );
}

function SkeletonCard({ height }: { height: number }) {
  return (
    <div
      className="animate-pulse rounded-2xl"
      style={{ height, background: "rgba(255,255,255,0.04)", border: "1px solid var(--border-subtle)" }}
    />
  );
}

const tableHeadStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 12px",
  borderBottom: "1px solid var(--border-subtle)",
  color: "var(--text-muted)",
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
};

const tableCellStyle: React.CSSProperties = {
  padding: "12px",
  color: "var(--text-muted)",
  fontSize: 12,
};