"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRightLeft } from "lucide-react";
import { getApiBase } from "../../lib/api/base";
import { useRefreshAge } from "../../hooks/useRefreshAge";
import { PanelHeader } from "../PanelHeader";
import {
  ArrowUpRightIcon as ArrowUpRight,
  ArrowDownRightIcon as ArrowDownRight,
  MinusIcon as Minus,
  SignalsIcon,
  ActivityIcon as Activity,
  TargetIcon as Target,
} from "../ui/CustomIcons";

const API_BASE = getApiBase();
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

interface SignalItem {
  id: string;
  symbol?: string;
  timeframe?: string;
  ml_direction?: string;
  ml_confidence?: number;
  ml_entry_price?: number;
  ml_target_price?: number;
  ml_stop_price?: number;
  exit_price?: number;
  created_at?: string;
  status?: string;
  pnl_pips?: number | null;
  duration_minutes?: number | null;
}

interface RecentSignalsResponse {
  signals?: SignalItem[];
  error?: string;
}

interface EmelInversePanelProps {
  symbol?: string;
}

const SYMBOLS = [{ key: "NDX.INDX", label: "NASDAQ" }];
const TIMEFRAMES = ["ALL", "5m", "15m", "1h", "4h"];

const theme = {
  bg: "var(--bg-primary)",
  surface: "var(--bg-surface)",
  card: "var(--bg-card)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
  purple: "var(--accent-purple)",
};

function toneMix(color: string, opacity: number) {
  return `color-mix(in srgb, ${color} ${opacity}%, transparent)`;
}

function normalizeConfidence(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value <= 1 ? value * 100 : value;
}

function formatPrice(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "--";
  return value.toFixed(2);
}

function formatPips(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "--";
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
}

function formatWhen(value?: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function statusTone(status?: string) {
  const normalized = (status || "").toLowerCase();
  if (normalized === "completed") return { color: theme.green, bg: toneMix(theme.green, 15), border: toneMix(theme.green, 30) };
  if (normalized === "stopped") return { color: theme.red, bg: toneMix(theme.red, 15), border: toneMix(theme.red, 30) };
  if (normalized === "active") return { color: theme.accent, bg: toneMix(theme.accent, 15), border: toneMix(theme.accent, 30) };
  return { color: theme.warn, bg: toneMix(theme.warn, 15), border: toneMix(theme.warn, 30) };
}

function directionTone(direction?: string) {
  const normalized = (direction || "").toUpperCase();
  if (normalized === "BUY") return { color: theme.green, Icon: ArrowUpRight };
  if (normalized === "SELL") return { color: theme.red, Icon: ArrowDownRight };
  return { color: theme.warn, Icon: Minus };
}

function MetricCard({
  label,
  value,
  tone,
  sublabel,
}: {
  label: string;
  value: string;
  tone: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded-xl p-4" style={{ background: theme.surface, border: `1px solid ${theme.border}` }}>
      <div className="text-[10px] uppercase tracking-[0.18em] mb-2" style={{ color: theme.muted }}>
        {label}
      </div>
      <div className="text-[28px] leading-none font-bold font-mono" style={{ color: tone }}>
        {value}
      </div>
      {sublabel ? (
        <div className="text-[11px] mt-2" style={{ color: theme.muted }}>
          {sublabel}
        </div>
      ) : null}
    </div>
  );
}

export default function EmelInversePanel({ symbol: initialSymbol = "NDX.INDX" }: EmelInversePanelProps) {
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState("ALL");
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { refreshAge: signalAge, markRefreshed } = useRefreshAge();

  const fetchData = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        model: "emel_inverse",
        symbol: activeSymbol,
        limit: "14",
        days: "30",
        include_active: "true",
      });
      const res = await fetch(`${API_BASE}/api/learning/signals/recent?${params.toString()}`);
      const json = (await res.json().catch(() => null)) as RecentSignalsResponse | null;

      if (!res.ok || !json || typeof json !== "object") {
        setSignals([]);
        setError(`http_${res.status}`);
        return;
      }
      if (json.error) {
        setSignals([]);
        setError(json.error);
        return;
      }

      const nextSignals = Array.isArray(json.signals) ? json.signals : [];
      setSignals(nextSignals);
      if (nextSignals[0]?.created_at) {
        markRefreshed(nextSignals[0].created_at);
      }
    } catch (err) {
      console.error("EMEL Inverse fetch error:", err);
      setSignals([]);
      setError("fetch_error");
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [activeSymbol, markRefreshed]);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    const interval = setInterval(() => fetchData(false), 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const handler = () => fetchData(true);
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [fetchData]);

  const filteredSignals = useMemo(() => {
    if (timeframe === "ALL") return signals;
    return signals.filter((signal) => (signal.timeframe || "").toLowerCase() === timeframe.toLowerCase());
  }, [signals, timeframe]);

  const stats = useMemo(() => {
    const resolved = filteredSignals.filter((signal) => {
      const status = (signal.status || "").toLowerCase();
      return status === "completed" || status === "stopped";
    });
    const wins = resolved.filter((signal) => (signal.status || "").toLowerCase() === "completed").length;
    const active = filteredSignals.filter((signal) => (signal.status || "").toLowerCase() === "active").length;
    const netPips = filteredSignals.reduce((sum, signal) => {
      return typeof signal.pnl_pips === "number" && Number.isFinite(signal.pnl_pips) ? sum + signal.pnl_pips : sum;
    }, 0);
    return {
      latest: filteredSignals[0] || null,
      total: filteredSignals.length,
      resolved: resolved.length,
      active,
      wins,
      winRate: resolved.length > 0 ? (wins / resolved.length) * 100 : 0,
      netPips,
    };
  }, [filteredSignals]);

  if (loading && signals.length === 0) {
    return (
      <div className="animate-pulse p-6 rounded-xl" style={{ background: theme.bg, border: `1px solid ${theme.border}` }}>
        <div className="h-12 w-1/3 rounded-lg mb-6" style={{ background: "rgba(255,255,255,0.05)" }} />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-24 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          ))}
        </div>
        <div className="h-56 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
      </div>
    );
  }

  const latestSignalTone = directionTone(stats.latest?.ml_direction);
  const latestConfidence = normalizeConfidence(stats.latest?.ml_confidence);
  const LatestSignalIcon = latestSignalTone.Icon;

  return (
    <div className="flex flex-col rounded-xl overflow-hidden" style={{ background: theme.bg, border: `1px solid ${theme.border}`, fontFamily: FONT }}>
      <PanelHeader
        title="EMEL INVERSE"
        subtitle="REVERSE SIGNAL FEED"
        icon={<ArrowRightLeft size={22} strokeWidth={2.4} />}
        iconBg="color-mix(in srgb, var(--accent-purple) 16%, transparent)"
        iconBorder="color-mix(in srgb, var(--accent-purple) 30%, var(--border-subtle))"
        iconColor="var(--accent-purple)"
        symbols={SYMBOLS}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        timeframes={TIMEFRAMES}
        loading={loading}
        panelId="emel-inverse-panel"
        signalAge={signalAge}
        extraContent={stats.latest ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{ background: toneMix(latestSignalTone.color, 15), border: `1px solid ${toneMix(latestSignalTone.color, 30)}` }}>
              <LatestSignalIcon className="w-4 h-4" style={{ color: latestSignalTone.color }} />
              <span className="text-sm font-bold font-mono" style={{ color: latestSignalTone.color }}>
                {stats.latest?.ml_direction || "--"}
              </span>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider" style={{ color: theme.muted }}>
                Last confidence
              </div>
              <div className="text-[24px] leading-none font-bold font-mono" style={{ color: theme.text }}>
                {typeof latestConfidence === "number" ? `${latestConfidence.toFixed(0)}%` : "--"}
              </div>
            </div>
          </div>
        ) : undefined}
      />

      <div className="p-4 md:p-5 flex flex-col gap-4" style={{ background: theme.card }}>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <MetricCard
            label="Latest signal"
            value={stats.latest?.ml_direction || "--"}
            tone={latestSignalTone.color}
            sublabel={stats.latest ? `${(stats.latest.timeframe || "--").toUpperCase()} • ${formatWhen(stats.latest.created_at)}` : "No recent inverse signal"}
          />
          <MetricCard
            label="Win rate"
            value={stats.resolved > 0 ? `${stats.winRate.toFixed(1)}%` : "--"}
            tone={stats.winRate >= 60 ? theme.green : stats.winRate >= 45 ? theme.warn : theme.red}
            sublabel={`Resolved: ${stats.resolved} • Wins: ${stats.wins}`}
          />
          <MetricCard
            label="Net pips"
            value={stats.total > 0 ? formatPips(stats.netPips) : "--"}
            tone={stats.netPips > 0 ? theme.green : stats.netPips < 0 ? theme.red : theme.warn}
            sublabel={`Active: ${stats.active} • Shown: ${stats.total}`}
          />
          <MetricCard
            label="Signal scope"
            value={timeframe === "ALL" ? "ALL" : timeframe.toUpperCase()}
            tone={theme.accent}
            sublabel="Model: EMEL Inverse • Source: prediction_logs"
          />
        </div>

        {error ? (
          <div className="rounded-xl p-4 text-sm" style={{ background: toneMix(theme.red, 8), border: `1px solid ${toneMix(theme.red, 20)}`, color: theme.red }}>
            {error}
          </div>
        ) : null}

        <div className="rounded-xl overflow-hidden" style={{ border: `1px solid ${theme.border}`, background: theme.surface }}>
          <div className="grid grid-cols-[1.2fr,0.9fr,0.9fr,0.9fr,1fr,1fr,1fr] gap-3 px-4 py-3 text-[10px] uppercase tracking-[0.18em]" style={{ color: theme.muted, borderBottom: `1px solid ${theme.border}` }}>
            <div>Signal</div>
            <div>TF</div>
            <div>Status</div>
            <div>Pips</div>
            <div>Entry</div>
            <div>Target / Stop</div>
            <div>Time</div>
          </div>

          {filteredSignals.length > 0 ? (
            <div className="divide-y" style={{ borderColor: theme.border }}>
              {filteredSignals.slice(0, 8).map((signal) => {
                const tone = directionTone(signal.ml_direction);
                const status = statusTone(signal.status);
                const confidence = normalizeConfidence(signal.ml_confidence);
                const SignalIcon = tone.Icon;
                return (
                  <div key={signal.id} className="grid grid-cols-[1.2fr,0.9fr,0.9fr,0.9fr,1fr,1fr,1fr] gap-3 px-4 py-3 items-center text-sm">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: toneMix(tone.color, 15), border: `1px solid ${toneMix(tone.color, 25)}` }}>
                        <SignalIcon className="w-4 h-4" style={{ color: tone.color }} />
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold" style={{ color: tone.color }}>
                          {signal.ml_direction || "--"}
                        </div>
                        <div className="text-[11px] truncate" style={{ color: theme.muted }}>
                          {typeof confidence === "number" ? `${confidence.toFixed(0)}% confidence` : "No confidence"}
                        </div>
                      </div>
                    </div>
                    <div className="font-mono text-sm" style={{ color: theme.text }}>{(signal.timeframe || "--").toUpperCase()}</div>
                    <div>
                      <span className="inline-flex px-2.5 py-1 rounded-lg text-[11px] font-semibold" style={{ color: status.color, background: status.bg, border: `1px solid ${status.border}` }}>
                        {(signal.status || "unknown").toUpperCase()}
                      </span>
                    </div>
                    <div className="font-mono text-sm" style={{ color: typeof signal.pnl_pips === "number" ? (signal.pnl_pips >= 0 ? theme.green : theme.red) : theme.muted }}>
                      {formatPips(signal.pnl_pips)}
                    </div>
                    <div className="font-mono text-sm" style={{ color: theme.text }}>
                      {formatPrice(signal.ml_entry_price)}
                    </div>
                    <div className="text-[11px] leading-relaxed font-mono">
                      <div style={{ color: theme.green }}>
                        <Target className="inline w-3 h-3 mr-1" />
                        {formatPrice(signal.ml_target_price)}
                      </div>
                      <div style={{ color: theme.red }}>
                        <SignalsIcon className="inline w-3 h-3 mr-1" />
                        {formatPrice(signal.ml_stop_price)}
                      </div>
                    </div>
                    <div className="text-[11px] leading-relaxed">
                      <div style={{ color: theme.text }}>{formatWhen(signal.created_at)}</div>
                      <div style={{ color: theme.muted }}>
                        {typeof signal.duration_minutes === "number" ? `${Math.round(signal.duration_minutes)} min` : "--"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="px-4 py-10 text-center">
              <div className="mx-auto mb-3 w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: toneMix(theme.purple, 12), border: `1px solid ${toneMix(theme.purple, 20)}`, color: theme.purple }}>
                <Activity className="w-5 h-5" />
              </div>
              <div className="text-sm font-semibold mb-1" style={{ color: theme.text }}>
                No EMEL Inverse signals in this filter
              </div>
              <div className="text-xs" style={{ color: theme.muted }}>
                Current backend logging creates EMEL Inverse history from reversed EMEL signals.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
