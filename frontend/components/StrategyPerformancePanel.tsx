"use client";

import { useState, useEffect, useCallback, lazy, Suspense, type ComponentType } from "react";
import { useQuery } from "@tanstack/react-query";
import { List, Crosshair } from "lucide-react";

import { getApiBase } from "@/lib/api/base";
import { PanelInfoButton } from "./PanelInfoButton";
import { ModelPerformanceModal } from "./panels/ModelPerformanceModal";
import {
  ChartsIcon as BarChart3,
  RotateIcon as RefreshCw,
  TrophyIcon as Trophy,
  TargetIcon as Target,
  CloseIcon as XCircle,
  SecurityShieldIcon as Shield,
  ZapIcon as Zap,
  AggressiveIcon as Flame,
  ArrowUpIcon as TrendingUp,
  AlertIcon as AlertTriangle,
} from "./ui/CustomIcons";

const SignalDetailModal = lazy(() => import("./SignalDetailModal"));

const API_BASE = getApiBase();
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
const TARGET_LEVELS = ["TP1", "TP2", "TP3", "TP4"] as const;

const P = {
  bg: "var(--bg-primary)",
  card: "var(--bg-card)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  textSec: "var(--text-secondary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
};

type LeaderKey = "quality" | "scalping" | "long_term";

interface StrategyData {
  scope: string;
  total_predictions: number;
  scored_signals: number;
  resolved_signals: number;
  with_outcome: number;
  correct: number;
  completed: number;
  stopped: number;
  expired: number;
  active: number;
  accuracy: number | null;
  win_rate: number | null;
  target_hits: number;
  stop_hits: number;
  target_hit_rate: number | null;
  stop_hit_rate: number | null;
  avg_confidence: number;
  net_pips: number;
  avg_pips: number;
  tp_breakdown: Record<string, number>;
  tp_hit_rates: Record<string, number | null>;
  avg_duration_minutes: number | null;
  avg_win_duration_minutes: number | null;
  avg_loss_duration_minutes: number | null;
  quality_score: number;
  scalp_score: number;
  long_term_score: number;
}

interface LeaderData {
  scope: string | null;
  score: number | null;
  resolved_signals: number;
  win_rate: number | null;
  net_pips: number | null;
  avg_duration_minutes: number | null;
}

interface SymbolSummary {
  available_scopes: string[];
  total_predictions: number;
  resolved_signals: number;
  leaders: {
    quality: LeaderData;
    scalping: LeaderData;
    long_term: LeaderData;
  };
}

interface StrategyPerformanceResponse {
  period_days: number;
  predictions_count: number;
  ml_predictions_count: number;
  outcomes_count: number;
  eligible_outcomes_count: number;
  strategies: Record<string, Record<string, StrategyData>>;
  symbols: Record<string, SymbolSummary>;
  best_strategies: Record<string, { strategy: string | null; accuracy: number | null }>;
  strategy_order: string[];
  strategy_descriptions: Record<string, string>;
  overall_summary: {
    total_predictions: number;
    resolved_signals: number;
    leaders: {
      quality: LeaderData;
      scalping: LeaderData;
      long_term: LeaderData;
    };
  };
  error?: string;
}

interface SmcPerformanceResponse {
  period_days: number;
  smc_predictions_count: number;
  outcomes_count: number;
  eligible_outcomes_count: number;
  timeframes: Record<string, Record<string, StrategyData>>;
  symbols: Record<string, SymbolSummary>;
  timeframe_order: string[];
  timeframe_descriptions: Record<string, string>;
  overall_summary: {
    total_predictions: number;
    resolved_signals: number;
    leaders: {
      quality: LeaderData;
      scalping: LeaderData;
      long_term: LeaderData;
    };
  };
  error?: string;
}

interface Signal {
  id: string;
  symbol: string;
  timeframe?: string;
  ml_direction: string;
  ml_confidence: number;
  status: string;
  created_at: string;
  pnl_pips?: number | null;
  duration_minutes?: number | null;
  normalized_model?: string;
  strategy_scope?: string | null;
}

interface RecentSignalsResponse {
  signals: Signal[];
  count: number;
  symbol?: string;
  strategy_scope?: string;
}

const STRATEGY_CONFIG: Record<string, { name: string; nameEn: string; icon: ComponentType<any>; color: string }> = {
  main: { name: "Ham ML", nameEn: "Main ML", icon: TrendingUp, color: "#60A5FA" },
  ultra_safe: { name: "Ultra Güvenli", nameEn: "Ultra Safe", icon: Shield, color: P.green },
  balanced: { name: "Dengeli", nameEn: "Balanced", icon: Target, color: P.accent },
  full_power: { name: "Full Power", nameEn: "Full Power", icon: Zap, color: P.warn },
  aggressive: { name: "Agresif", nameEn: "Aggressive", icon: Flame, color: P.red },
  nasdaq_precision: { name: "NASDAQ Precision", nameEn: "NASDAQ Precision", icon: Crosshair, color: "#22D3EE" },
};
const SMC_TIMEFRAME_CONFIG: Record<string, { name: string; nameEn: string; icon: ComponentType<any>; color: string }> = {
  "5m": { name: "5m", nameEn: "5m", icon: Zap, color: "#A855F7" },
  "15m": { name: "15m", nameEn: "15m", icon: Target, color: "#8B5CF6" },
  "1h": { name: "1h", nameEn: "1h", icon: TrendingUp, color: "#60A5FA" },
  "4h": { name: "4h", nameEn: "4h", icon: Crosshair, color: "#22D3EE" },
};

const LEADER_META: Record<LeaderKey, { label: string; color: string }> = {
  quality: { label: "Quality", color: P.accent },
  scalping: { label: "Scalp", color: P.warn },
  long_term: { label: "Long", color: P.green },
};

const SYMBOL_META = [
  { key: "NDX.INDX", label: "NASDAQ", icon: "📈", color: P.green },
  { key: "XAUUSD", label: "XAU/USD", icon: "⭐", color: P.warn },
  { key: "GDAXI.INDX", label: "DAX", icon: "🏛", color: P.accent },
  { key: "USOIL.FOREX", label: "US Oil", icon: "🛢", color: "#FB923C" },
];

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return `${Number.isInteger(value) ? value : value.toFixed(1)}%`;
}

function formatPips(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(1)} pips`;
}

function formatDuration(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  if (value < 60) return `${Math.round(value)}m`;
  const hours = value / 60;
  return `${hours < 10 ? hours.toFixed(1) : Math.round(hours)}h`;
}

function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return value.toFixed(1);
}

function getScopeLabel(scope?: string | null, locale: "tr" | "en" = "tr") {
  if (!scope) return "—";
  const config = STRATEGY_CONFIG[scope];
  if (!config) return scope;
  return locale === "en" ? config.nameEn : config.name;
}

function getSmcTimeframeLabel(timeframe?: string | null, locale: "tr" | "en" = "tr") {
  if (!timeframe) return "—";
  const config = SMC_TIMEFRAME_CONFIG[timeframe];
  if (!config) return timeframe;
  return locale === "en" ? config.nameEn : config.name;
}

function getOrderedScopes(scopes?: string[]) {
  const source = scopes && scopes.length > 0 ? scopes : Object.keys(STRATEGY_CONFIG);
  const seen = new Set<string>();
  return source.filter((scope) => {
    if (!STRATEGY_CONFIG[scope] || seen.has(scope)) return false;
    seen.add(scope);
    return true;
  });
}

function getEmptyStrategyData(scope: string): StrategyData {
  return {
    scope,
    total_predictions: 0,
    scored_signals: 0,
    resolved_signals: 0,
    with_outcome: 0,
    correct: 0,
    completed: 0,
    stopped: 0,
    expired: 0,
    active: 0,
    accuracy: 0,
    win_rate: 0,
    target_hits: 0,
    stop_hits: 0,
    target_hit_rate: null,
    stop_hit_rate: null,
    avg_confidence: 0,
    net_pips: 0,
    avg_pips: 0,
    tp_breakdown: { TP1: 0, TP2: 0, TP3: 0, TP4: 0 },
    tp_hit_rates: { TP1: null, TP2: null, TP3: null, TP4: null },
    avg_duration_minutes: null,
    avg_win_duration_minutes: null,
    avg_loss_duration_minutes: null,
    quality_score: 0,
    scalp_score: 0,
    long_term_score: 0,
  };
}

function scoreColor(value: number) {
  if (value >= 70) return P.green;
  if (value >= 45) return P.warn;
  return P.textSec;
}

async function fetchStrategyPerformance(days: number): Promise<StrategyPerformanceResponse> {
  const res = await fetch(`${API_BASE}/api/learning/strategy-performance?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch strategy performance");
  return res.json();
}

async function fetchSmcPerformance(days: number): Promise<SmcPerformanceResponse> {
  const res = await fetch(`${API_BASE}/api/learning/smc-performance?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch SMC performance");
  return res.json();
}

async function fetchRecentSignals(days: number, symbol?: string, strategyScope?: string): Promise<RecentSignalsResponse> {
  const params = new URLSearchParams();
  params.set("days", String(days));
  params.set("limit", "20");
  params.set("include_active", "true");
  params.set("model", "ml");
  if (symbol) params.set("symbol", symbol);
  if (strategyScope) params.set("strategy_scope", strategyScope);

  const res = await fetch(`${API_BASE}/api/learning/signals/recent?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch signals");
  return res.json();
}

function AccuracyBar({ value, color }: { value: number | null; color: string }) {
  if (value === null) return <span style={{ fontFamily: FONT, fontSize: 12, color: P.muted }}>—</span>;

  return (
    <div className="flex items-center gap-2.5" style={{ minWidth: 120 }}>
      <div className="flex-1 rounded-full overflow-hidden" style={{ height: 6, background: "rgba(255,255,255,0.06)" }}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(value, 100)}%`, background: color, opacity: 0.85 }} />
      </div>
      <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color, width: 44, textAlign: "right" as const }}>
        {formatPercent(value)}
      </span>
    </div>
  );
}

function StatCard({ label, value, tone = P.text }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="rounded-xl px-4 py-3" style={{ background: P.surface, border: `1px solid ${P.border}` }}>
      <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontFamily: FONT, fontSize: 20, fontWeight: 700, color: tone, marginTop: 6 }}>{value}</div>
    </div>
  );
}

function LeaderCard({
  title,
  leader,
  labelFormatter,
}: {
  title: string;
  leader: LeaderData;
  labelFormatter?: (scope?: string | null) => string;
}) {
  return (
    <div className="rounded-xl p-4" style={{ background: P.surface, border: `1px solid ${P.border}` }}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>{title}</div>
          <div style={{ fontFamily: FONT, fontSize: 16, fontWeight: 700, color: P.text, marginTop: 6 }}>
            {(labelFormatter || ((scope?: string | null) => getScopeLabel(scope)))(leader.scope)}
          </div>
        </div>
        <div className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1" style={{ background: `${P.accent}10`, border: `1px solid ${P.accent}18` }}>
          <Trophy className="w-3 h-3" style={{ color: P.accent }} />
          <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 700, color: P.accent }}>Score {formatScore(leader.score)}</span>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 mt-4">
        <div>
          <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>Win Rate</div>
          <div style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.text }}>{formatPercent(leader.win_rate)}</div>
        </div>
        <div>
          <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>Net Pips</div>
          <div style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.text }}>{formatPips(leader.net_pips)}</div>
        </div>
        <div>
          <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>Avg Duration</div>
          <div style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.text }}>{formatDuration(leader.avg_duration_minutes)}</div>
        </div>
      </div>
    </div>
  );
}

function ScorePill({ label, value }: { label: string; value: number }) {
  const color = scoreColor(value);
  return (
    <span className="inline-flex items-center gap-1 rounded-md px-2 py-1" style={{ background: `${color}12`, border: `1px solid ${color}20` }}>
      <span style={{ fontFamily: FONT, fontSize: 9, color, fontWeight: 700 }}>{label}</span>
      <span style={{ fontFamily: FONT, fontSize: 11, color: P.text, fontWeight: 600 }}>{formatScore(value)}</span>
    </span>
  );
}

function StrategyRow({
  strategy,
  data,
  locale,
  leaderBadges,
}: {
  strategy: string;
  data: StrategyData;
  locale: "tr" | "en";
  leaderBadges: LeaderKey[];
}) {
  const config = STRATEGY_CONFIG[strategy];
  if (!config) return null;

  const Icon = config.icon;
  const accColor = data.accuracy !== null && data.accuracy >= 60 ? P.green : data.accuracy !== null && data.accuracy >= 50 ? P.warn : P.red;
  const highlighted = leaderBadges.length > 0;

  return (
    <tr
      style={{
        borderBottom: `1px solid ${P.border}`,
        background: highlighted ? `${config.color}06` : "transparent",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = highlighted ? `${config.color}10` : "rgba(255,255,255,0.015)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = highlighted ? `${config.color}06` : "transparent")}
    >
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="flex items-start gap-3">
          <div className="rounded-md flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: `${config.color}10`, border: `1px solid ${config.color}18` }}>
            <Icon className="w-3.5 h-3.5" style={{ color: config.color }} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.text }}>{locale === "en" ? config.nameEn : config.name}</span>
              {leaderBadges.map((badge) => (
                <span key={badge} className="inline-flex items-center gap-1 rounded px-1.5 py-0.5" style={{ background: `${LEADER_META[badge].color}14`, border: `1px solid ${LEADER_META[badge].color}22` }}>
                  <span style={{ fontFamily: FONT, fontSize: 9, color: LEADER_META[badge].color, fontWeight: 700 }}>{LEADER_META[badge].label}</span>
                </span>
              ))}
            </div>
            <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 4 }}>
              {data.total_predictions} signals · {data.resolved_signals} resolved · {data.expired} expired · {data.active} active
            </div>
          </div>
        </div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="space-y-2">
          <AccuracyBar value={data.accuracy} color={accColor} />
          <div style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>
            TP {formatPercent(data.target_hit_rate)} · SL {formatPercent(data.stop_hit_rate)}
          </div>
        </div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="flex flex-wrap gap-1.5">
          <ScorePill label="Q" value={data.quality_score} />
          <ScorePill label="S" value={data.scalp_score} />
          <ScorePill label="L" value={data.long_term_score} />
        </div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: data.net_pips >= 0 ? P.green : P.red }}>{formatPips(data.net_pips)}</div>
        <div style={{ fontFamily: FONT, fontSize: 11, color: P.textSec, marginTop: 4 }}>Avg {formatPips(data.avg_pips)}</div>
        <div style={{ fontFamily: FONT, fontSize: 11, color: P.muted, marginTop: 2 }}>Duration {formatDuration(data.avg_duration_minutes)}</div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="flex flex-wrap gap-1.5" style={{ maxWidth: 290 }}>
          {TARGET_LEVELS.map((tpKey) => (
            <span key={tpKey} className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5" style={{ background: `${P.green}10`, border: `1px solid ${P.green}18` }}>
              <span style={{ fontFamily: FONT, fontSize: 9, fontWeight: 700, color: P.green }}>{tpKey}</span>
              <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, color: P.textSec }}>{formatPercent(data.tp_hit_rates?.[tpKey])}</span>
              <span style={{ fontFamily: FONT, fontSize: 9, color: P.muted }}>({data.tp_breakdown?.[tpKey] ?? 0})</span>
            </span>
          ))}
        </div>
      </td>
      <td style={{ padding: "12px 14px", textAlign: "right" as const, verticalAlign: "top" }}>
        <div style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.textSec }}>{formatPercent(data.avg_confidence)}</div>
        <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 4 }}>{data.completed}W / {data.stopped}L</div>
      </td>
    </tr>
  );
}

function SmcTimeframeRow({
  timeframe,
  data,
  locale,
  leaderBadges,
}: {
  timeframe: string;
  data: StrategyData;
  locale: "tr" | "en";
  leaderBadges: LeaderKey[];
}) {
  const config = SMC_TIMEFRAME_CONFIG[timeframe];
  if (!config) return null;

  const Icon = config.icon;
  const accColor = data.accuracy !== null && data.accuracy >= 60 ? P.green : data.accuracy !== null && data.accuracy >= 50 ? P.warn : P.red;
  const highlighted = leaderBadges.length > 0;

  return (
    <tr
      style={{
        borderBottom: `1px solid ${P.border}`,
        background: highlighted ? `${config.color}06` : "transparent",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = highlighted ? `${config.color}10` : "rgba(255,255,255,0.015)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = highlighted ? `${config.color}06` : "transparent")}
    >
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="flex items-start gap-3">
          <div className="rounded-md flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: `${config.color}10`, border: `1px solid ${config.color}18` }}>
            <Icon className="w-3.5 h-3.5" style={{ color: config.color }} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.text }}>{locale === "en" ? config.nameEn : config.name}</span>
              {leaderBadges.map((badge) => (
                <span key={badge} className="inline-flex items-center gap-1 rounded px-1.5 py-0.5" style={{ background: `${LEADER_META[badge].color}14`, border: `1px solid ${LEADER_META[badge].color}22` }}>
                  <span style={{ fontFamily: FONT, fontSize: 9, color: LEADER_META[badge].color, fontWeight: 700 }}>{LEADER_META[badge].label}</span>
                </span>
              ))}
            </div>
            <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 4 }}>
              {data.total_predictions} signals · {data.resolved_signals} resolved · {data.expired} expired · {data.active} active
            </div>
          </div>
        </div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="space-y-2">
          <AccuracyBar value={data.accuracy} color={accColor} />
          <div style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>
            TP {formatPercent(data.target_hit_rate)} · SL {formatPercent(data.stop_hit_rate)}
          </div>
        </div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="flex flex-wrap gap-1.5">
          <ScorePill label="Q" value={data.quality_score} />
          <ScorePill label="S" value={data.scalp_score} />
          <ScorePill label="L" value={data.long_term_score} />
        </div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: data.net_pips >= 0 ? P.green : P.red }}>{formatPips(data.net_pips)}</div>
        <div style={{ fontFamily: FONT, fontSize: 11, color: P.textSec, marginTop: 4 }}>Avg {formatPips(data.avg_pips)}</div>
        <div style={{ fontFamily: FONT, fontSize: 11, color: P.muted, marginTop: 2 }}>Duration {formatDuration(data.avg_duration_minutes)}</div>
      </td>
      <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
        <div className="flex flex-wrap gap-1.5" style={{ maxWidth: 290 }}>
          {TARGET_LEVELS.map((tpKey) => (
            <span key={tpKey} className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5" style={{ background: `${P.green}10`, border: `1px solid ${P.green}18` }}>
              <span style={{ fontFamily: FONT, fontSize: 9, fontWeight: 700, color: P.green }}>{tpKey}</span>
              <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, color: P.textSec }}>{formatPercent(data.tp_hit_rates?.[tpKey])}</span>
              <span style={{ fontFamily: FONT, fontSize: 9, color: P.muted }}>({data.tp_breakdown?.[tpKey] ?? 0})</span>
            </span>
          ))}
        </div>
      </td>
      <td style={{ padding: "12px 14px", textAlign: "right" as const, verticalAlign: "top" }}>
        <div style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: P.textSec }}>{formatPercent(data.avg_confidence)}</div>
        <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 4 }}>{data.completed}W / {data.stopped}L</div>
      </td>
    </tr>
  );
}

function SignalRow({ signal, onClick }: { signal: Signal; onClick: () => void }) {
  const isBuy = signal.ml_direction === "BUY";
  const statusColor = signal.status === "completed" ? P.green : signal.status === "stopped" ? P.red : signal.status === "active" ? P.accent : P.muted;
  const pnlColor = signal.pnl_pips === null || signal.pnl_pips === undefined ? P.muted : signal.pnl_pips > 0 ? P.green : signal.pnl_pips < 0 ? P.red : P.muted;
  const scope = signal.strategy_scope || "main";
  const config = STRATEGY_CONFIG[scope] || STRATEGY_CONFIG.main;

  return (
    <tr onClick={onClick} className="cursor-pointer hover:bg-white/5 transition-colors" style={{ borderBottom: `1px solid ${P.border}` }}>
      <td style={{ padding: "12px 14px" }}>
        <div className="flex items-center gap-2.5">
          <span style={{ color: isBuy ? P.green : P.red, fontWeight: 600, fontSize: 12 }}>{isBuy ? "▲" : "▼"} {signal.ml_direction}</span>
          <div>
            <div style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: P.text }}>{signal.symbol}</div>
            <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>{signal.timeframe || "—"} · {(signal.normalized_model || "ml").toUpperCase()}</div>
          </div>
        </div>
      </td>
      <td style={{ padding: "12px 14px" }}>
        <span className="inline-flex items-center gap-1 rounded-md px-2 py-1" style={{ background: `${config.color}12`, border: `1px solid ${config.color}20` }}>
          <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 700, color: config.color }}>{getScopeLabel(scope)}</span>
        </span>
      </td>
      <td style={{ padding: "12px 14px" }}>
        <span style={{ fontFamily: FONT, fontSize: 11, color: statusColor, textTransform: "capitalize" }}>{signal.status}</span>
      </td>
      <td style={{ padding: "12px 14px", textAlign: "right" }}>
        <span style={{ fontFamily: FONT, fontSize: 12, color: pnlColor, fontWeight: signal.pnl_pips !== undefined ? 600 : 400 }}>{formatPips(signal.pnl_pips)}</span>
      </td>
      <td style={{ padding: "12px 14px", textAlign: "right" }}>
        <span style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>{formatDuration(signal.duration_minutes)}</span>
      </td>
      <td style={{ padding: "12px 14px", textAlign: "right" }}>
        <span style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>{new Date(signal.created_at).toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</span>
      </td>
    </tr>
  );
}

export default function StrategyPerformancePanel() {
  const [days, setDays] = useState(30);
  const [selectedSymbol, setSelectedSymbol] = useState<string | undefined>();
  const [selectedStrategyScope, setSelectedStrategyScope] = useState<string | undefined>();
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isModelPerformanceModalOpen, setIsModelPerformanceModalOpen] = useState(false);
  const [selectedModelPerformanceSymbol, setSelectedModelPerformanceSymbol] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"performance" | "signals">("performance");
  const locale: "tr" | "en" = "tr";

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["strategy-performance", days],
    queryFn: () => fetchStrategyPerformance(days),
    staleTime: 60000,
    refetchInterval: 300000,
  });

  const {
    data: smcData,
    isLoading: smcLoading,
    error: smcError,
    refetch: refetchSmc,
  } = useQuery({
    queryKey: ["smc-performance", days],
    queryFn: () => fetchSmcPerformance(days),
    staleTime: 60000,
    refetchInterval: 300000,
  });

  const {
    data: signalsData,
    isLoading: signalsLoading,
    refetch: refetchSignals,
  } = useQuery({
    queryKey: ["recent-signals", days, selectedSymbol, selectedStrategyScope],
    queryFn: () => fetchRecentSignals(days, selectedSymbol, selectedStrategyScope),
    staleTime: 30000,
    refetchInterval: 60000,
    enabled: activeTab === "signals",
  });

  const handleRefresh = useCallback(() => {
    refetch();
    refetchSmc();
    if (activeTab === "signals") {
      refetchSignals();
    }
  }, [activeTab, refetch, refetchSignals, refetchSmc]);

  useEffect(() => {
    window.addEventListener("dashboard-refresh", handleRefresh);
    return () => window.removeEventListener("dashboard-refresh", handleRefresh);
  }, [handleRefresh]);

  const allOrderedScopes = getOrderedScopes(data?.strategy_order);
  const selectedSymbolScopes = selectedSymbol ? data?.symbols?.[selectedSymbol]?.available_scopes || [] : [];
  const selectedScopeDescription = selectedStrategyScope ? data?.strategy_descriptions?.[selectedStrategyScope] : undefined;

  const handleSignalClick = (signalId: string) => {
    setSelectedSignalId(signalId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedSignalId(null);
  };

  if (error) {
    return (
      <div className="rounded-xl" style={{ background: P.card, border: `1px solid ${P.border}`, padding: 24 }}>
        <div className="flex items-center gap-3" style={{ color: P.red }}>
          <AlertTriangle className="w-5 h-5" />
          <span style={{ fontFamily: FONT, fontSize: 14, color: P.red }}>Strategy data unavailable</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-xl overflow-hidden" style={{ fontFamily: FONT, background: P.bg, border: `1px solid ${P.border}` }}>
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4" style={{ background: P.surface, borderBottom: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: `${P.accent}12`, border: `1px solid ${P.accent}20` }}>
              <BarChart3 className="w-4.5 h-4.5" style={{ color: P.accent, width: 18, height: 18 }} />
            </div>
            <div>
              <h3 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text, letterSpacing: "-0.01em" }}>Strategy Performance Analysis</h3>
              <p style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>Real ML preset scopes + raw main flow. Compare quality, scalping edge and long-term durability.</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1 mr-2" style={{ background: P.bg, borderRadius: 8, padding: 2 }}>
              <button
                aria-label="Performance Tab"
                onClick={() => setActiveTab("performance")}
                className="px-3 py-1.5 rounded-md text-xs font-medium transition-all"
                style={{ background: activeTab === "performance" ? `${P.accent}20` : "transparent", color: activeTab === "performance" ? P.accent : P.muted }}
              >
                <BarChart3 className="w-3.5 h-3.5 inline mr-1" />
                Performance
              </button>
              <button
                aria-label="Signals Tab"
                onClick={() => setActiveTab("signals")}
                className="px-3 py-1.5 rounded-md text-xs font-medium transition-all"
                style={{ background: activeTab === "signals" ? `${P.accent}20` : "transparent", color: activeTab === "signals" ? P.accent : P.muted }}
              >
                <List className="w-3.5 h-3.5 inline mr-1" />
                Signals
              </button>
            </div>

            <select
              aria-label="Days Filter"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="rounded-lg appearance-none cursor-pointer"
              style={{ fontFamily: FONT, fontSize: 11, fontWeight: 500, padding: "6px 10px", background: P.surface, color: P.textSec, border: `1px solid ${P.border}` }}
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
              <option value={0}>All time</option>
            </select>

            <button
              onClick={handleRefresh}
              className="rounded-lg flex items-center justify-center transition-all duration-150"
              style={{ width: 32, height: 32, background: `${P.accent}08`, border: `1px solid ${P.accent}15` }}
              onMouseEnter={(e) => (e.currentTarget.style.background = `${P.accent}15`)}
              onMouseLeave={(e) => (e.currentTarget.style.background = `${P.accent}08`)}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} style={{ color: P.accent }} />
            </button>
            <PanelInfoButton panelId="strategy-performance" />
          </div>
        </div>

        {(isLoading || smcLoading) && activeTab === "performance" ? (
          <div className="p-16 flex items-center justify-center" style={{ background: P.bg }}>
            <RefreshCw className="w-5 h-5 animate-spin" style={{ color: P.accent }} />
          </div>
        ) : activeTab === "performance" && data && !data.error ? (
          <div className="p-5 space-y-6" style={{ background: P.bg }}>
            <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3">
              <StatCard label="ML Predictions" value={data.ml_predictions_count} tone={P.text} />
              <StatCard label="Resolved Signals" value={data.overall_summary.resolved_signals} tone={P.accent} />
              <StatCard label="Eligible Outcomes" value={data.eligible_outcomes_count} tone={P.warn} />
              <LeaderCard title="Best Signal Quality" leader={data.overall_summary.leaders.quality} />
              <LeaderCard title="Best Scalping Scope" leader={data.overall_summary.leaders.scalping} />
              <LeaderCard title="Best Long-Term Scope" leader={data.overall_summary.leaders.long_term} />
            </div>

            {SYMBOL_META.map(({ key: symKey, label, icon }) => {
              const symbolSummary = data.symbols?.[symKey];
              const symbolStrategies = data.strategies?.[symKey] || {};
              const orderedScopes = allOrderedScopes;

              return (
                <div key={symKey} className="space-y-3">
                  <div
                    className="flex flex-wrap items-center gap-3 cursor-pointer group hover:bg-white/5 p-2 -mx-2 rounded-lg transition-colors border border-transparent hover:border-white/5"
                    onClick={() => {
                      setSelectedModelPerformanceSymbol(symKey);
                      setIsModelPerformanceModalOpen(true);
                    }}
                  >
                    <span style={{ fontSize: 16 }}>{icon}</span>
                    <div>
                      <h4 className="group-hover:text-blue-400 transition-colors" style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text }}>{label}</h4>
                      <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 2 }}>
                        {symbolSummary?.total_predictions ?? 0} ML signals · {symbolSummary?.resolved_signals ?? 0} resolved
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 ml-auto">
                      {(["quality", "scalping", "long_term"] as LeaderKey[]).map((leaderKey) => {
                        const leader = symbolSummary?.leaders?.[leaderKey];
                        return (
                          <span key={leaderKey} className="inline-flex items-center gap-1 rounded px-2 py-1" style={{ background: `${LEADER_META[leaderKey].color}10`, border: `1px solid ${LEADER_META[leaderKey].color}18` }}>
                            <span style={{ fontFamily: FONT, fontSize: 9, fontWeight: 700, color: LEADER_META[leaderKey].color }}>{LEADER_META[leaderKey].label}</span>
                            <span style={{ fontFamily: FONT, fontSize: 10, color: P.text }}>{getScopeLabel(leader?.scope)}</span>
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  <div className="overflow-x-auto rounded-lg" style={{ border: `1px solid ${P.border}` }}>
                    <table className="w-full" style={{ minWidth: 980 }}>
                      <thead>
                        <tr style={{ background: P.surface }}>
                          {["Scope", "Win Rate", "Edge Scores", "Pips / Duration", "TP Ladder", "Confidence"].map((header, index) => (
                            <th
                              key={header}
                              style={{
                                padding: "10px 14px",
                                textAlign: index === 5 ? "right" as const : "left" as const,
                                fontFamily: FONT,
                                fontSize: 10,
                                fontWeight: 500,
                                color: P.muted,
                                letterSpacing: "0.08em",
                                textTransform: "uppercase",
                                borderBottom: `1px solid ${P.border}`,
                              }}
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {orderedScopes.length > 0 ? (
                          orderedScopes.map((scope) => {
                            const strategyData = symbolStrategies[scope] || getEmptyStrategyData(scope);
                            const leaderBadges = (["quality", "scalping", "long_term"] as LeaderKey[]).filter(
                              (leaderKey) => symbolSummary?.leaders?.[leaderKey]?.scope === scope
                            );

                            return (
                              <StrategyRow
                                key={`${symKey}-${scope}`}
                                strategy={scope}
                                data={strategyData}
                                locale={locale}
                                leaderBadges={leaderBadges}
                              />
                            );
                          })
                        ) : (
                          <tr>
                            <td colSpan={6} className="text-center py-8" style={{ color: P.muted, fontFamily: FONT, fontSize: 13 }}>
                              No ML strategy history found for this symbol yet.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}

            <div style={{ paddingTop: 12, borderTop: `1px solid ${P.border}` }}>
              <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
                Strategy Scope Descriptions
              </p>
              <div className="flex flex-wrap gap-x-6 gap-y-2">
                {(data.strategy_order || []).map((key) => {
                  const config = STRATEGY_CONFIG[key];
                  const desc = data.strategy_descriptions?.[key];
                  if (!desc) return null;
                  return (
                    <div key={key} className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full" style={{ background: config?.color || P.muted }} />
                      <span style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>
                        <strong style={{ color: P.text }}>{getScopeLabel(key)}</strong> — {desc}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {smcData && !smcData.error ? (
              <div className="space-y-6" style={{ paddingTop: 12, borderTop: `1px solid ${P.border}` }}>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: `#A855F712`, border: `1px solid #A855F720` }}>
                    <Crosshair className="w-4.5 h-4.5" style={{ color: "#A855F7", width: 18, height: 18 }} />
                  </div>
                  <div>
                    <h4 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text, letterSpacing: "-0.01em" }}>Smart Money Zones Performance</h4>
                    <p style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>All Smart Money Zones symbols and timeframes with the same TP/SL and lifecycle scoring logic.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3">
                  <StatCard label="SMC Predictions" value={smcData.smc_predictions_count} tone={P.text} />
                  <StatCard label="Resolved Signals" value={smcData.overall_summary.resolved_signals} tone={P.accent} />
                  <StatCard label="Eligible Outcomes" value={smcData.eligible_outcomes_count} tone={P.warn} />
                  <LeaderCard title="Best Signal Quality" leader={smcData.overall_summary.leaders.quality} labelFormatter={(scope) => getSmcTimeframeLabel(scope, locale)} />
                  <LeaderCard title="Best Scalping Timeframe" leader={smcData.overall_summary.leaders.scalping} labelFormatter={(scope) => getSmcTimeframeLabel(scope, locale)} />
                  <LeaderCard title="Best Long-Term Timeframe" leader={smcData.overall_summary.leaders.long_term} labelFormatter={(scope) => getSmcTimeframeLabel(scope, locale)} />
                </div>

                {SYMBOL_META.map(({ key: symKey, label, icon }) => {
                  const symbolSummary = smcData.symbols?.[symKey];
                  const symbolTimeframes = smcData.timeframes?.[symKey] || {};
                  const orderedTimeframes = smcData.timeframe_order || Object.keys(SMC_TIMEFRAME_CONFIG);

                  return (
                    <div key={`smc-${symKey}`} className="space-y-3">
                      <div className="flex flex-wrap items-center gap-3 p-2 -mx-2 rounded-lg" style={{ background: "rgba(255,255,255,0.015)" }}>
                        <span style={{ fontSize: 16 }}>{icon}</span>
                        <div>
                          <h4 style={{ fontFamily: FONT, fontSize: 15, fontWeight: 600, color: P.text }}>{label}</h4>
                          <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, marginTop: 2 }}>
                            {symbolSummary?.total_predictions ?? 0} SMC signals · {symbolSummary?.resolved_signals ?? 0} resolved
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 ml-auto">
                          {(["quality", "scalping", "long_term"] as LeaderKey[]).map((leaderKey) => {
                            const leader = symbolSummary?.leaders?.[leaderKey];
                            return (
                              <span key={leaderKey} className="inline-flex items-center gap-1 rounded px-2 py-1" style={{ background: `${LEADER_META[leaderKey].color}10`, border: `1px solid ${LEADER_META[leaderKey].color}18` }}>
                                <span style={{ fontFamily: FONT, fontSize: 9, fontWeight: 700, color: LEADER_META[leaderKey].color }}>{LEADER_META[leaderKey].label}</span>
                                <span style={{ fontFamily: FONT, fontSize: 10, color: P.text }}>{getSmcTimeframeLabel(leader?.scope, locale)}</span>
                              </span>
                            );
                          })}
                        </div>
                      </div>

                      <div className="overflow-x-auto rounded-lg" style={{ border: `1px solid ${P.border}` }}>
                        <table className="w-full" style={{ minWidth: 980 }}>
                          <thead>
                            <tr style={{ background: P.surface }}>
                              {["Timeframe", "Win Rate", "Edge Scores", "Pips / Duration", "TP Ladder", "Confidence"].map((header, index) => (
                                <th
                                  key={`${symKey}-${header}`}
                                  style={{
                                    padding: "10px 14px",
                                    textAlign: index === 5 ? "right" as const : "left" as const,
                                    fontFamily: FONT,
                                    fontSize: 10,
                                    fontWeight: 500,
                                    color: P.muted,
                                    letterSpacing: "0.08em",
                                    textTransform: "uppercase",
                                    borderBottom: `1px solid ${P.border}`,
                                  }}
                                >
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {orderedTimeframes.length > 0 ? (
                              orderedTimeframes.map((timeframe) => {
                                const timeframeData = symbolTimeframes[timeframe] || getEmptyStrategyData(timeframe);
                                const leaderBadges = (["quality", "scalping", "long_term"] as LeaderKey[]).filter(
                                  (leaderKey) => symbolSummary?.leaders?.[leaderKey]?.scope === timeframe
                                );

                                return (
                                  <SmcTimeframeRow
                                    key={`${symKey}-${timeframe}`}
                                    timeframe={timeframe}
                                    data={timeframeData}
                                    locale={locale}
                                    leaderBadges={leaderBadges}
                                  />
                                );
                              })
                            ) : (
                              <tr>
                                <td colSpan={6} className="text-center py-8" style={{ color: P.muted, fontFamily: FONT, fontSize: 13 }}>
                                  No Smart Money Zones history found for this symbol yet.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  );
                })}

                <div>
                  <p style={{ fontFamily: FONT, fontSize: 10, fontWeight: 500, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
                    Smart Money Zones Timeframe Descriptions
                  </p>
                  <div className="flex flex-wrap gap-x-6 gap-y-2">
                    {(smcData.timeframe_order || []).map((key) => {
                      const config = SMC_TIMEFRAME_CONFIG[key];
                      const desc = smcData.timeframe_descriptions?.[key];
                      if (!desc) return null;
                      return (
                        <div key={`smc-desc-${key}`} className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ background: config?.color || P.muted }} />
                          <span style={{ fontFamily: FONT, fontSize: 11, color: P.textSec }}>
                            <strong style={{ color: P.text }}>{getSmcTimeframeLabel(key, locale)}</strong> — {desc}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : smcError ? (
              <div className="rounded-xl px-4 py-3" style={{ background: P.surface, border: `1px solid ${P.border}` }}>
                <span style={{ fontFamily: FONT, fontSize: 12, color: P.red }}>Smart Money Zones performance data unavailable.</span>
              </div>
            ) : null}
          </div>
        ) : activeTab === "signals" ? (
          <div className="p-5 space-y-4" style={{ background: P.bg }}>
            <div className="rounded-xl p-4 space-y-3" style={{ background: P.surface, border: `1px solid ${P.border}` }}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div style={{ fontFamily: FONT, fontSize: 10, color: P.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>Signal Analysis Scopes</div>
                  <div style={{ fontFamily: FONT, fontSize: 12, color: P.textSec, marginTop: 6 }}>
                    Main ML stays above Ultra Safe so you can inspect the raw/original ML flow separately from preset-filtered scopes.
                  </div>
                </div>

                <span className="inline-flex items-center gap-1 rounded-md px-2.5 py-1" style={{ background: `${P.accent}10`, border: `1px solid ${P.accent}18` }}>
                  <span style={{ fontFamily: FONT, fontSize: 10, color: P.muted }}>Active Scope</span>
                  <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 700, color: P.accent }}>
                    {selectedStrategyScope ? getScopeLabel(selectedStrategyScope) : "All Scopes"}
                  </span>
                </span>
              </div>

              <div data-testid="signal-scope-tabs" className="flex flex-wrap gap-2">
                <button
                  aria-label="All Scopes Tab"
                  onClick={() => setSelectedStrategyScope(undefined)}
                  className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 transition-all"
                  style={{
                    background: selectedStrategyScope ? P.bg : `${P.accent}18`,
                    border: `1px solid ${selectedStrategyScope ? P.border : `${P.accent}30`}`,
                    color: selectedStrategyScope ? P.textSec : P.accent,
                  }}
                >
                  <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 700 }}>All Scopes</span>
                </button>

                {allOrderedScopes.map((scope) => {
                  const config = STRATEGY_CONFIG[scope] || STRATEGY_CONFIG.main;
                  const Icon = config.icon;
                  const isActive = selectedStrategyScope === scope;
                  const hasSelectedSymbolHistory = !selectedSymbol || selectedSymbolScopes.includes(scope);

                  return (
                    <button
                      key={scope}
                      aria-label={`${getScopeLabel(scope)} Scope Tab`}
                      onClick={() => setSelectedStrategyScope(scope)}
                      className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 transition-all"
                      style={{
                        background: isActive ? `${config.color}18` : P.bg,
                        border: `1px solid ${isActive ? `${config.color}35` : P.border}`,
                        color: isActive ? config.color : P.textSec,
                        opacity: hasSelectedSymbolHistory ? 1 : 0.7,
                      }}
                    >
                      <Icon className="w-3.5 h-3.5" style={{ color: isActive ? config.color : P.textSec }} />
                      <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 700 }}>{getScopeLabel(scope)}</span>
                      {scope === "main" ? (
                        <span className="rounded px-1.5 py-0.5" style={{ fontFamily: FONT, fontSize: 9, fontWeight: 700, color: config.color, background: `${config.color}12` }}>
                          RAW
                        </span>
                      ) : null}
                    </button>
                  );
                })}
              </div>

              <p style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>
                {selectedStrategyScope
                  ? `${getScopeLabel(selectedStrategyScope)} — ${selectedScopeDescription || "Resolved scope filter is applied to recent ML signals."}${selectedSymbol && !selectedSymbolScopes.includes(selectedStrategyScope) ? " Current symbol has no recorded history for this scope yet." : ""}`
                  : "Showing recent ML signals across all resolved scopes. Use Main ML to inspect the raw/original signal flow."}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                aria-label="Signal Symbol Filter"
                value={selectedSymbol || ""}
                onChange={(e) => setSelectedSymbol(e.target.value || undefined)}
                className="rounded-lg appearance-none cursor-pointer"
                style={{ fontFamily: FONT, fontSize: 11, padding: "6px 10px", background: P.surface, color: P.textSec, border: `1px solid ${P.border}` }}
              >
                <option value="">All Symbols</option>
                {SYMBOL_META.map(({ key, label }) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>

              <select
                aria-label="Strategy Scope Filter"
                value={selectedStrategyScope || ""}
                onChange={(e) => setSelectedStrategyScope(e.target.value || undefined)}
                className="rounded-lg appearance-none cursor-pointer"
                style={{ fontFamily: FONT, fontSize: 11, padding: "6px 10px", background: P.surface, color: P.textSec, border: `1px solid ${P.border}` }}
              >
                <option value="">All Scopes</option>
                {allOrderedScopes.map((scope) => (
                  <option key={scope} value={scope}>{getScopeLabel(scope)}</option>
                ))}
              </select>

              <span style={{ fontFamily: FONT, fontSize: 11, color: P.muted }}>Recent ML signals only · grouped by resolved strategy scope</span>
            </div>

            <div className="overflow-x-auto rounded-lg" style={{ border: `1px solid ${P.border}` }}>
              <table className="w-full" style={{ minWidth: 820 }}>
                <thead>
                  <tr style={{ background: P.surface }}>
                    {["Signal", "Scope", "Status", "Result", "Duration", "Time"].map((header, index) => (
                      <th
                        key={header}
                        style={{
                          padding: "10px 14px",
                          textAlign: index >= 3 ? "right" as const : "left" as const,
                          fontFamily: FONT,
                          fontSize: 10,
                          fontWeight: 500,
                          color: P.muted,
                          letterSpacing: "0.08em",
                          textTransform: "uppercase",
                          borderBottom: `1px solid ${P.border}`,
                        }}
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {signalsLoading ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto" style={{ color: P.accent }} />
                      </td>
                    </tr>
                  ) : signalsData?.signals && signalsData.signals.length > 0 ? (
                    signalsData.signals.map((signal) => (
                      <SignalRow key={signal.id} signal={signal} onClick={() => handleSignalClick(signal.id)} />
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="text-center py-8" style={{ color: P.muted, fontFamily: FONT, fontSize: 13 }}>
                        No ML signals found for the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <p className="text-xs" style={{ color: P.muted, fontFamily: FONT }}>
              Click any signal to inspect lifecycle details, TP/SL structure and post-trade diagnostics.
            </p>
          </div>
        ) : (
          <div className="text-center py-12" style={{ background: P.bg }}>
            <p style={{ fontFamily: FONT, fontSize: 14, color: P.muted }}>No data available</p>
          </div>
        )}
      </div>

      <Suspense fallback={null}>
        <SignalDetailModal signalId={selectedSignalId} isOpen={isModalOpen} onClose={handleCloseModal} />
      </Suspense>

      <ModelPerformanceModal
        isOpen={isModelPerformanceModalOpen}
        onClose={() => setIsModelPerformanceModalOpen(false)}
        symbol={selectedModelPerformanceSymbol}
        model="all"
        days={days}
      />
    </>
  );
}
