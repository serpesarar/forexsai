"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBase } from "../../lib/api/base";
import { useRefreshAge } from "../../hooks/useRefreshAge";
import { PanelHeader } from "../PanelHeader";
import {
  TargetIcon as Target,
  ArrowUpIcon as ArrowUp,
  ArrowDownIcon as ArrowDown,
  ActivityIcon as Activity,
  CheckCircleIcon as CheckCircle,
  AlertIcon as AlertTriangle,
} from "../ui/CustomIcons";

const API_BASE = getApiBase();
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

interface ReboundLeg {
  label?: string;
  is_high_probability?: boolean;
  is_exit_trigger?: boolean;
  score?: number;
  threshold?: number;
  mandatory_hits?: number;
  mandatory_required?: number;
  expected_bounce_to?: number;
  take_profit_zone?: number;
  invalidation?: number;
  short_invalidation?: number;
  reasons?: string[];
  bonus_confirmations?: string[];
}

interface ReboundZone {
  type?: string;
  low?: number | null;
  high?: number | null;
  touch_count?: number;
  fresh?: boolean;
  score?: number;
}

interface ReboundResponse {
  symbol?: string;
  timeframe?: string;
  timestamp?: string;
  price?: number;
  rebound_long?: ReboundLeg & { zone?: ReboundZone };
  rebound_exit?: ReboundLeg & { reversal_zone?: ReboundZone };
  context?: {
    regime?: string;
    session?: string;
    is_ath?: boolean;
    rsi?: number;
    adx?: number;
    divergence?: string;
  };
  error?: string;
}

interface ReboundDetectionPanelProps {
  symbol?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US Oil" },
];

const TIMEFRAMES = ["5m", "15m", "30m", "1H", "4H"];

const theme = {
  bg: "var(--bg-primary)",
  surface: "var(--bg-surface)",
  border: "var(--border-subtle)",
  text: "var(--text-primary)",
  muted: "var(--text-muted)",
  green: "var(--accent-positive)",
  red: "var(--accent-negative)",
  warn: "var(--accent-warning)",
  accent: "var(--accent-info)",
};

function scoreColor(score: number | undefined, threshold: number | undefined, positiveColor: string) {
  if (typeof score !== "number") return theme.muted;
  if (typeof threshold === "number" && score >= threshold) return positiveColor;
  return theme.warn;
}

function MetricCard({
  title,
  value,
  tone,
}: {
  title: string;
  value: string;
  tone: string;
}) {
  return (
    <div
      className="rounded-lg px-3 py-2"
      style={{ background: `${tone}10`, border: `1px solid ${tone}20` }}
    >
      <div className="text-[10px] uppercase tracking-wider" style={{ color: theme.muted }}>
        {title}
      </div>
      <div className="text-[12px] font-mono font-bold" style={{ color: tone }}>
        {value}
      </div>
    </div>
  );
}

function ReboundLegCard({
  title,
  leg,
  isEntry,
}: {
  title: string;
  leg?: ReboundResponse["rebound_long"] | ReboundResponse["rebound_exit"];
  isEntry: boolean;
}) {
  const isPositive = isEntry ? leg?.is_high_probability : leg?.is_exit_trigger;
  const tone = isEntry ? (isPositive ? theme.green : theme.warn) : (isPositive ? theme.red : theme.warn);
  const primaryTarget = isEntry ? leg?.expected_bounce_to : leg?.take_profit_zone;
  const invalidation = isEntry ? leg?.invalidation : leg?.short_invalidation;
  const Icon = isEntry ? ArrowUp : ArrowDown;

  return (
    <div className="rounded-xl p-4" style={{ background: theme.surface, border: `1px solid ${theme.border}` }}>
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: `${tone}12`, border: `1px solid ${tone}20`, color: tone }}
          >
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-widest font-bold" style={{ color: theme.muted }}>
              {title}
            </div>
            <div className="text-sm font-semibold" style={{ color: theme.text }}>
              {leg?.label || "NO_SIGNAL"}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider" style={{ color: theme.muted }}>
            Score
          </div>
          <div className="text-[26px] leading-none font-bold font-mono" style={{ color: scoreColor(leg?.score, leg?.threshold, tone) }}>
            {typeof leg?.score === "number" ? leg.score.toFixed(0) : "--"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <MetricCard
          title="Threshold"
          value={typeof leg?.threshold === "number" ? leg.threshold.toFixed(0) : "--"}
          tone={theme.accent}
        />
        <MetricCard
          title="Hits"
          value={typeof leg?.mandatory_hits === "number" && typeof leg?.mandatory_required === "number" ? `${leg.mandatory_hits}/${leg.mandatory_required}` : "--"}
          tone={tone}
        />
        <MetricCard
          title={isEntry ? "Bounce Target" : "Take Profit"}
          value={typeof primaryTarget === "number" ? primaryTarget.toFixed(2) : "--"}
          tone={isEntry ? theme.green : theme.red}
        />
        <MetricCard
          title="Invalidation"
          value={typeof invalidation === "number" ? invalidation.toFixed(2) : "--"}
          tone={theme.warn}
        />
      </div>

      <div className="space-y-1.5">
        {(leg?.reasons || []).slice(0, 3).map((reason, index) => (
          <div key={index} className="flex items-start gap-2 text-[11px]" style={{ color: theme.text }}>
            <CheckCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{ color: tone }} />
            <span className="opacity-85">{reason}</span>
          </div>
        ))}
        {(!leg?.reasons || leg.reasons.length === 0) && (
          <div className="flex items-start gap-2 text-[11px]" style={{ color: theme.muted }}>
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>No confluence reasons returned yet.</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ReboundDetectionPanel({ symbol: initialSymbol = "NDX.INDX" }: ReboundDetectionPanelProps) {
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState("5m");
  const [data, setData] = useState<ReboundResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { refreshAge: signalAge, markRefreshed } = useRefreshAge();

  const fetchData = useCallback(async (showLoading = false, forceRefresh = false) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const params = new URLSearchParams({ timeframe });
      if (forceRefresh) params.set("refresh", "true");
      const res = await fetch(`${API_BASE}/api/panel/rebound/${activeSymbol}?${params.toString()}`);
      const json = await res.json().catch(() => null);

      if (!res.ok) {
        setError((json && typeof json === "object" && "error" in json && typeof json.error === "string") ? json.error : `http_${res.status}`);
        setData(null);
      } else if (!json || typeof json !== "object") {
        setError("invalid_response");
        setData(null);
      } else if ("error" in json && json.error) {
        setError(typeof json.error === "string" ? json.error : "panel_error");
        setData(null);
      } else {
        const payload = json as ReboundResponse;
        setData(payload);
        markRefreshed(payload.timestamp);
      }
    } catch (err) {
      console.error("Rebound panel fetch error:", err);
      setError("fetch_error");
      setData(null);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [activeSymbol, timeframe, markRefreshed]);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    const interval = setInterval(() => fetchData(false), 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const handler = () => fetchData(true, true);
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div className="animate-pulse p-6 rounded-xl" style={{ background: theme.bg, border: `1px solid ${theme.border}` }}>
        <div className="h-12 w-1/3 rounded-lg mb-6" style={{ background: "rgba(255,255,255,0.05)" }} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="h-52 rounded-xl" style={{ background: "rgba(255,255,255,0.05)" }} />
          <div className="h-52 rounded-xl" style={{ background: "rgba(255,255,255,0.05)" }} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-xl overflow-hidden" style={{ background: theme.bg, border: `1px solid ${theme.border}`, fontFamily: FONT }}>
      <PanelHeader
        title="REBOUND"
        subtitle="ENTRY / EXIT CONFLUENCE"
        icon={<Target size={24} strokeWidth={2.5} />}
        iconBg="var(--accent-cyan-08)"
        iconBorder="var(--accent-cyan-15)"
        iconColor="var(--accent-cyan)"
        symbols={SYMBOLS}
        activeSymbol={activeSymbol}
        onSymbolChange={setActiveSymbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
        timeframes={TIMEFRAMES}
        loading={loading}
        panelId="rebound-detection"
        signalAge={signalAge}
        extraContent={data ? (
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-widest" style={{ color: theme.muted }}>Price</div>
            <div className="text-[24px] font-bold tracking-tight font-mono" style={{ color: theme.text }}>
              {typeof data.price === "number" ? data.price.toFixed(2) : "--"}
            </div>
          </div>
        ) : undefined}
      />

      <div className="p-4 space-y-4">
        {error && !data && (
          <div className="rounded-xl p-6 text-center" style={{ background: theme.surface, border: `1px solid ${theme.border}` }}>
            <Activity className="w-10 h-10 mx-auto mb-3" style={{ color: theme.warn, opacity: 0.5 }} />
            <div className="text-sm font-semibold mb-1" style={{ color: theme.text }}>Rebound data unavailable</div>
            <div className="text-xs" style={{ color: theme.muted }}>{error}</div>
          </div>
        )}

        {data && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <ReboundLegCard title="Rebound Entry" leg={data.rebound_long} isEntry />
              <ReboundLegCard title="Rebound Exit" leg={data.rebound_exit} isEntry={false} />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              <MetricCard title="Regime" value={data.context?.regime || "--"} tone={theme.accent} />
              <MetricCard title="Session" value={data.context?.session || "--"} tone={theme.warn} />
              <MetricCard title="RSI" value={typeof data.context?.rsi === "number" ? data.context.rsi.toFixed(1) : "--"} tone={theme.accent} />
              <MetricCard title="ADX" value={typeof data.context?.adx === "number" ? data.context.adx.toFixed(1) : "--"} tone={theme.accent} />
              <MetricCard title="Divergence" value={data.context?.divergence || "--"} tone={theme.warn} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
