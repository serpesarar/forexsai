"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBase } from "../../lib/api/base";
import { useSignalCountdown } from "../../hooks/useSignalCountdown";
import { PanelHeader } from "../PanelHeader";
import {
  TargetIcon as Target,
  TrendingUpIcon as TrendUp,
  TrendingDownIcon as TrendDown,
  ActivityIcon as Activity,
} from "../ui/CustomIcons";

const API_BASE = getApiBase();
const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";

// Types
interface ReboundLeg {
  label?: string;
  is_high_probability?: boolean;
  score?: number;
  threshold?: number;
  mandatory_hits?: number;
  mandatory_required?: number;
  expected_bounce_to?: number;
  expected_drop_to?: number;
  invalidation?: number;
  reasons?: string[];
  bonus_confirmations?: string[];
  zone?: {
    type?: string;
    low?: number | null;
    high?: number | null;
  };
}

interface ReboundResponse {
  symbol?: string;
  timeframe?: string;
  timestamp?: string;
  price?: number;
  rebound_long?: ReboundLeg;
  rebound_short?: ReboundLeg;
  context?: {
    regime?: string;
    session?: string;
    rsi?: number;
    adx?: number;
    divergence?: string;
  };
  error?: string;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "USOIL.FOREX", label: "US Oil" },
];

const TIMEFRAMES = ["5m", "15m", "30m", "1H", "4H"];

// Signal Card Component
function SignalCard({
  title,
  direction,
  data,
}: {
  title: string;
  direction: "up" | "down";
  data?: ReboundLeg;
}) {
  const isGreen = direction === "up";
  const colorClass = isGreen ? "#10b981" : "#ef4444";
  const bgClass = isGreen ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)";
  const borderClass = isGreen ? "rgba(16,185,129,0.25)" : "rgba(239,68,68,0.25)";

  const label = data?.label || "NO_SIGNAL";
  const score = data?.score ?? 0;
  const hits = data?.mandatory_hits ?? 0;
  const required = data?.mandatory_required ?? 2;

  const getStatusColor = () => {
    if (label === "HIGH_PROBABILITY") return colorClass;
    if (label === "WATCH") return "#f59e0b";
    return "#6b7280";
  };

  const targetPrice = isGreen ? data?.expected_bounce_to : data?.expected_drop_to;
  const invalidation = data?.invalidation;

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: `2px solid ${getStatusColor()}`,
        borderRadius: "12px",
        padding: "16px",
        fontFamily: FONT,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
        <div
          style={{
            width: "40px",
            height: "40px",
            borderRadius: "10px",
            background: bgClass,
            border: `1px solid ${borderClass}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: colorClass,
          }}
        >
          {isGreen ? <TrendUp size={20} /> : <TrendDown size={20} />}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {title}
          </div>
          <div style={{ fontSize: "16px", fontWeight: 700, color: getStatusColor() }}>
            {label.replace(/_/g, " ")}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "28px", fontWeight: 800, color: getStatusColor(), fontFamily: "monospace" }}>
            {score.toFixed(0)}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ marginBottom: "12px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)", marginBottom: "4px" }}>
          <span>Checks</span>
          <span>{hits}/{required}</span>
        </div>
        <div style={{ height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
          <div
            style={{
              height: "100%",
              width: `${Math.min(100, (hits / required) * 100)}%`,
              background: getStatusColor(),
              borderRadius: "3px",
            }}
          />
        </div>
      </div>

      {/* Prices */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "12px" }}>
        <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px", borderRadius: "8px", textAlign: "center" }}>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>
            {isGreen ? "Bounce To" : "Drop To"}
          </div>
          <div style={{ fontSize: "14px", fontWeight: 700, color: colorClass, fontFamily: "monospace" }}>
            {targetPrice?.toFixed(2) ?? "--"}
          </div>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px", borderRadius: "8px", textAlign: "center" }}>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Stop</div>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#f59e0b", fontFamily: "monospace" }}>
            {invalidation?.toFixed(2) ?? "--"}
          </div>
        </div>
      </div>

      {/* Zone */}
      {data?.zone && data.zone.type !== "none" && (
        <div style={{ background: bgClass, border: `1px solid ${borderClass}`, padding: "8px 12px", borderRadius: "8px", marginBottom: "10px", fontSize: "11px" }}>
          <span style={{ color: "var(--text-muted)" }}>Zone: </span>
          <span style={{ color: colorClass, fontWeight: 600 }}>
            {data.zone.type?.replace(/_/g, " ")}
          </span>
          {data.zone.low && data.zone.high && (
            <span style={{ color: "var(--text-muted)", marginLeft: "8px" }}>
              {data.zone.low.toFixed(1)} - {data.zone.high.toFixed(1)}
            </span>
          )}
        </div>
      )}

      {/* Reasons */}
      {data?.reasons && data.reasons.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {data.reasons.slice(0, 2).map((reason, i) => (
            <div key={i} style={{ fontSize: "11px", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ color: colorClass }}>●</span>
              {reason}
            </div>
          ))}
        </div>
      )}

      {(!data?.reasons || data.reasons.length === 0) && (
        <div style={{ fontSize: "12px", color: "var(--text-muted)", textAlign: "center", padding: "8px" }}>
          Waiting for setup...
        </div>
      )}
    </div>
  );
}

// Context pill
function ContextPill({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.05)", padding: "6px 12px", borderRadius: "20px", fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{value}</span>
    </div>
  );
}

export default function ReboundDetectionPanel({ symbol: initialSymbol = "NDX.INDX" }: { symbol?: string }) {
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState("5m");
  const [data, setData] = useState<ReboundResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { markRefreshed } = useSignalCountdown("rebound", 300, data?.timestamp);

  const fetchData = useCallback(async (showLoading = false, forceRefresh = false) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const params = new URLSearchParams({ timeframe });
      if (forceRefresh) params.set("refresh", "true");
      const res = await fetch(`${API_BASE}/api/panel/rebound/${activeSymbol}?${params.toString()}`);
      const json = await res.json().catch(() => null);

      if (!res.ok) {
        setError(json?.error || `HTTP ${res.status}`);
        setData(null);
      } else if (json?.error) {
        setError(json.error);
        setData(null);
      } else {
        setData(json as ReboundResponse);
        markRefreshed();
      }
    } catch (err) {
      setError("Network error");
      setData(null);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [activeSymbol, timeframe, markRefreshed]);

  useEffect(() => { fetchData(true); }, [fetchData]);
  useEffect(() => { const interval = setInterval(() => fetchData(false), 60000); return () => clearInterval(interval); }, [fetchData]);
  useEffect(() => {
    const handler = () => fetchData(true, true);
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div className="animate-pulse" style={{ background: "var(--bg-primary)", border: "1px solid var(--border-subtle)", borderRadius: "12px", padding: "20px" }}>
        <div style={{ height: "200px", background: "rgba(255,255,255,0.05)", borderRadius: "8px" }} />
      </div>
    );
  }

  return (
    <div style={{ background: "var(--bg-primary)", border: "1px solid var(--border-subtle)", borderRadius: "12px", overflow: "hidden", fontFamily: FONT }}>
      <PanelHeader
        title="REBOUND"
        subtitle="DIP & PEAK BOUNCE DETECTOR"
        icon={<Target size={22} />}
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
        signalCountdown={{
          modelKey: "rebound",
          refreshIntervalSeconds: 300,
          signalTimestamp: data?.timestamp,
        }}
        extraContent={data?.price ? (
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Price</div>
            <div style={{ fontSize: "22px", fontWeight: 700, fontFamily: "monospace", color: "var(--text-primary)" }}>
              {data.price.toFixed(2)}
            </div>
          </div>
        ) : undefined}
      />

      <div style={{ padding: "16px" }}>
        {error && !data && (
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "12px", padding: "24px", textAlign: "center" }}>
            <Activity size={32} style={{ color: "var(--accent-warning)", opacity: 0.5, marginBottom: "12px" }} />
            <div style={{ color: "var(--text-primary)", fontWeight: 600, marginBottom: "4px" }}>Rebound data unavailable</div>
            <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>{error}</div>
          </div>
        )}

        {data && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
              <SignalCard title="Bounce Up (Long)" direction="up" data={data.rebound_long} />
              <SignalCard title="Bounce Down (Short)" direction="down" data={data.rebound_short} />
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", justifyContent: "center" }}>
              <ContextPill label="Regime" value={data.context?.regime || "--"} />
              <ContextPill label="Session" value={data.context?.session || "--"} />
              <ContextPill label="RSI" value={data.context?.rsi?.toFixed(1) || "--"} />
              <ContextPill label="ADX" value={data.context?.adx?.toFixed(1) || "--"} />
              <ContextPill label="Div" value={data.context?.divergence || "None"} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
