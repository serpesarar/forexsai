"use client";

import { useEffect, useState, useCallback } from "react";
import { PanelInfoButton } from "./PanelInfoButton";
import {
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Activity,
  Users,
  BarChart3,
  Gauge,
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  Zap,
  Eye,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

// ═══════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════

interface WhaleAlert {
  symbol: string;
  alert_type: string;
  direction: string;
  severity: string;
  message: string;
  impact_score: number;
  detected_at: string;
  details: Record<string, any>;
}

interface SymbolSnapshot {
  symbol: string;
  whale_pressure: number;
  pressure_label: string;
  commercials_net: number;
  commercials_net_change: number;
  speculators_net: number;
  speculators_net_change: number;
  spec_long_percent: number;
  spec_positioning_percentile: number;
  total_open_interest: number;
  oi_change_pct: number;
  crowded_trade_risk: boolean;
  whale_accumulation: boolean;
  smart_money_direction: string;
  cot_signal: string;
  cot_reason: string;
  confidence_adjustment: number;
  active_alerts: WhaleAlert[];
  report_date: string;
  data_source: string;
  last_updated: string;
}

interface WhaleDashboard {
  symbols: Record<string, SymbolSnapshot>;
  alerts: WhaleAlert[];
  tracked_symbols: string[];
  last_updated: string;
}

// ═══════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════

function pressureColor(p: number): string {
  if (p >= 0.5) return "text-emerald-400";
  if (p >= 0.2) return "text-green-400";
  if (p <= -0.5) return "text-red-400";
  if (p <= -0.2) return "text-orange-400";
  return "text-gray-400";
}

function pressureBg(p: number): string {
  if (p >= 0.5) return "bg-emerald-500/20 border-emerald-500/30";
  if (p >= 0.2) return "bg-green-500/10 border-green-500/20";
  if (p <= -0.5) return "bg-red-500/20 border-red-500/30";
  if (p <= -0.2) return "bg-orange-500/10 border-orange-500/20";
  return "bg-gray-800/50 border-gray-600/30";
}

function signalBadge(signal: string) {
  const map: Record<string, { bg: string; text: string }> = {
    BULLISH: { bg: "bg-green-500/20", text: "text-green-400" },
    BEARISH: { bg: "bg-red-500/20", text: "text-red-400" },
    TREND_EXHAUSTION: { bg: "bg-orange-500/20", text: "text-orange-400" },
    NEUTRAL: { bg: "bg-gray-500/20", text: "text-gray-400" },
  };
  const s = map[signal] || map.NEUTRAL;
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${s.bg} ${s.text}`}>
      {signal.replace("_", " ")}
    </span>
  );
}

function formatNet(val: number): string {
  const sign = val >= 0 ? "+" : "";
  if (Math.abs(val) >= 1000) {
    return `${sign}${(val / 1000).toFixed(0)}K`;
  }
  return `${sign}${val.toLocaleString()}`;
}

function alertIcon(type: string) {
  switch (type) {
    case "CROWDED_TRADE": return <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />;
    case "EXTREME_PESSIMISM": return <TrendingUp className="w-3.5 h-3.5 text-green-400" />;
    case "OI_SURGE": return <Zap className="w-3.5 h-3.5 text-yellow-400" />;
    case "SMART_MONEY_SHIFT": return <Shield className="w-3.5 h-3.5 text-purple-400" />;
    default: return <Eye className="w-3.5 h-3.5 text-blue-400" />;
  }
}

function alertSeverityColor(severity: string): string {
  switch (severity) {
    case "critical": return "border-red-500/40 bg-red-500/10";
    case "high": return "border-orange-500/30 bg-orange-500/10";
    case "medium": return "border-yellow-500/20 bg-yellow-500/5";
    default: return "border-gray-600/30 bg-gray-800/50";
  }
}

// ═══════════════════════════════════════════════════════════════════
// Pressure Gauge Component
// ═══════════════════════════════════════════════════════════════════

function PressureGauge({ pressure, label }: { pressure: number; label: string }) {
  // Map -1..+1 to 0..100 for the bar
  const pct = ((pressure + 1) / 2) * 100;
  const clampedPct = Math.max(2, Math.min(98, pct));

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">Whale Pressure</span>
        <span className={`text-sm font-bold ${pressureColor(pressure)}`}>
          {pressure >= 0 ? "+" : ""}{pressure.toFixed(2)} — {label}
        </span>
      </div>
      {/* Gradient bar */}
      <div className="relative h-3 rounded-full overflow-hidden bg-gradient-to-r from-red-500/30 via-gray-600/30 to-green-500/30 border border-white/10">
        {/* Indicator */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-white rounded-full shadow-[0_0_6px_rgba(255,255,255,0.5)] transition-all duration-500"
          style={{ left: `${clampedPct}%`, transform: "translateX(-50%)" }}
        />
        {/* Center line */}
        <div className="absolute top-0 bottom-0 left-1/2 w-px bg-white/20" />
      </div>
      <div className="flex justify-between text-[9px] text-gray-600">
        <span>Bearish</span>
        <span>Neutral</span>
        <span>Bullish</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// Symbol Card Component
// ═══════════════════════════════════════════════════════════════════

function SymbolCard({ snap }: { snap: SymbolSnapshot }) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useI18nStore();

  const symbolLabel: Record<string, string> = {
    XAUUSD: "Gold",
    SILVER: "Silver",
    NASDAQ: "NASDAQ-100",
    SP500: "S&P 500",
    DAX: "DAX 40",
    USOIL: "WTI Oil",
    CL: "WTI Oil",
    "CL.COMM": "WTI Oil",
  };

  const symbolIcon: Record<string, string> = {
    XAUUSD: "🥇",
    SILVER: "🥈",
    NASDAQ: "📊",
    SP500: "📈",
    DAX: "🇩🇪",
    USOIL: "🛢️",
    CL: "🛢️",
    "CL.COMM": "🛢️",
  };

  return (
    <div className={`rounded-xl border ${pressureBg(snap.whale_pressure)} transition-all duration-300`}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors rounded-xl"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-lg">{symbolIcon[snap.symbol] || "📊"}</span>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white">{symbolLabel[snap.symbol] || snap.symbol}</span>
              {signalBadge(snap.cot_signal)}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-xs font-mono font-bold ${pressureColor(snap.whale_pressure)}`}>
                {snap.whale_pressure >= 0 ? "+" : ""}{snap.whale_pressure.toFixed(2)}
              </span>
              <span className="text-[10px] text-gray-500">{snap.pressure_label}</span>
              {snap.crowded_trade_risk && (
                <span className="text-[9px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded-full font-bold">
                  CROWDED
                </span>
              )}
              {snap.whale_accumulation && (
                <span className="text-[9px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded-full font-bold">
                  ACCUMULATING
                </span>
              )}
            </div>
          </div>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-white/5 pt-3">
          {/* Pressure Gauge */}
          <PressureGauge pressure={snap.whale_pressure} label={snap.pressure_label} />

          {/* COT Positioning Grid */}
          <div className="grid grid-cols-2 gap-2">
            {/* Commercials (Smart Money) */}
            <div className="bg-slate-800/60 rounded-lg p-2.5 border border-white/5">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Shield className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-[10px] text-gray-400 font-medium">Commercials</span>
              </div>
              <div className={`text-base font-bold font-mono ${snap.commercials_net > 0 ? "text-green-400" : "text-red-400"}`}>
                {formatNet(snap.commercials_net)}
              </div>
              {snap.commercials_net_change !== 0 && (
                <div className="flex items-center gap-1 mt-0.5">
                  {snap.commercials_net_change > 0
                    ? <ArrowUpRight className="w-3 h-3 text-green-400" />
                    : <ArrowDownRight className="w-3 h-3 text-red-400" />}
                  <span className={`text-[10px] font-mono ${snap.commercials_net_change > 0 ? "text-green-400" : "text-red-400"}`}>
                    {formatNet(snap.commercials_net_change)} WoW
                  </span>
                </div>
              )}
            </div>

            {/* Speculators (Crowd) */}
            <div className="bg-slate-800/60 rounded-lg p-2.5 border border-white/5">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Users className="w-3.5 h-3.5 text-purple-400" />
                <span className="text-[10px] text-gray-400 font-medium">Speculators</span>
              </div>
              <div className={`text-base font-bold font-mono ${snap.speculators_net > 0 ? "text-green-400" : "text-red-400"}`}>
                {formatNet(snap.speculators_net)}
              </div>
              {snap.speculators_net_change !== 0 && (
                <div className="flex items-center gap-1 mt-0.5">
                  {snap.speculators_net_change > 0
                    ? <ArrowUpRight className="w-3 h-3 text-green-400" />
                    : <ArrowDownRight className="w-3 h-3 text-red-400" />}
                  <span className={`text-[10px] font-mono ${snap.speculators_net_change > 0 ? "text-green-400" : "text-red-400"}`}>
                    {formatNet(snap.speculators_net_change)} WoW
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-slate-800/40 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-gray-500">Spec Long</div>
              <div className="text-sm font-bold text-white">{snap.spec_long_percent.toFixed(0)}%</div>
              <div className="text-[9px] text-gray-600">P{snap.spec_positioning_percentile.toFixed(0)}</div>
            </div>
            <div className="bg-slate-800/40 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-gray-500">Open Interest</div>
              <div className="text-sm font-bold text-white">{(snap.total_open_interest / 1000).toFixed(0)}K</div>
              <div className={`text-[9px] font-mono ${snap.oi_change_pct > 0 ? "text-green-400" : snap.oi_change_pct < 0 ? "text-red-400" : "text-gray-600"}`}>
                {snap.oi_change_pct > 0 ? "+" : ""}{snap.oi_change_pct.toFixed(1)}%
              </div>
            </div>
            <div className="bg-slate-800/40 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-gray-500">Smart Money</div>
              <div className="flex items-center justify-center gap-1">
                {snap.smart_money_direction === "buying" && <ArrowUpRight className="w-3.5 h-3.5 text-green-400" />}
                {snap.smart_money_direction === "selling" && <ArrowDownRight className="w-3.5 h-3.5 text-red-400" />}
                {snap.smart_money_direction === "neutral" && <Activity className="w-3.5 h-3.5 text-gray-400" />}
                <span className={`text-xs font-bold capitalize ${snap.smart_money_direction === "buying" ? "text-green-400" :
                    snap.smart_money_direction === "selling" ? "text-red-400" : "text-gray-400"
                  }`}>
                  {snap.smart_money_direction}
                </span>
              </div>
            </div>
          </div>

          {/* COT Reason */}
          <div className="text-[11px] text-gray-400 bg-slate-800/30 rounded-lg p-2 border border-white/5">
            <span className="text-gray-500 font-medium">Analysis: </span>
            {snap.cot_reason}
          </div>

          {/* Alerts for this symbol */}
          {snap.active_alerts.length > 0 && (
            <div className="space-y-1.5">
              {snap.active_alerts.map((alert, i) => (
                <div key={i} className={`flex items-start gap-2 p-2 rounded-lg border ${alertSeverityColor(alert.severity)}`}>
                  {alertIcon(alert.alert_type)}
                  <span className="text-[11px] text-gray-300 leading-tight">{alert.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* Meta */}
          <div className="flex items-center justify-between text-[9px] text-gray-600 pt-1 border-t border-white/5">
            <span>Report: {snap.report_date}</span>
            <span className={snap.data_source === "live" ? "text-green-500" : "text-yellow-500"}>
              {snap.data_source === "live" ? "● Live CFTC" : "● Fallback"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// Main Panel
// ═══════════════════════════════════════════════════════════════════

interface WhaleTrackerPanelProps {
  className?: string;
}

export default function WhaleTrackerPanel({ className = "" }: WhaleTrackerPanelProps) {
  const { t } = useI18nStore();
  const [data, setData] = useState<WhaleDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/whale/dashboard`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (json.success) {
        setData(json.data);
        setLastUpdate(new Date());
        setError(null);
      } else {
        throw new Error(json.error || "Unknown error");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch whale data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // COT updates weekly; refresh every 5 minutes
    const interval = setInterval(fetchData, 300_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4 ${className}`}>
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
        </div>
      </div>
    );
  }

  const symbols = data?.symbols || {};
  const alerts = data?.alerts || [];

  return (
    <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/50 via-indigo-900/40 to-blue-900/50 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <span className="text-xl">🐋</span>
              {alerts.length > 0 && (
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full border border-gray-900 flex items-center justify-center">
                  <span className="text-[7px] font-bold text-white">{alerts.length}</span>
                </span>
              )}
            </div>
            <div>
              <span className="font-semibold text-white text-sm">{t("whale.title")}</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-gray-400">COT + Whale Pressure</span>
                {data?.last_updated && (
                  <span className="text-[9px] text-gray-600">
                    {new Date(data.last_updated).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={fetchData}
              className="p-1.5 hover:bg-gray-700/50 rounded-lg transition-colors"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? "animate-spin" : ""}`} />
            </button>
            <PanelInfoButton panelId="whale-tracker" />
          </div>
        </div>
      </div>

      <div className="p-3 space-y-2.5">
        {/* Global Alerts */}
        {alerts.length > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 mb-1">
              <Zap className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[10px] text-gray-400 uppercase tracking-wider font-medium">{t("whale.activeAlerts")}</span>
            </div>
            {alerts.slice(0, 3).map((alert, i) => (
              <div key={i} className={`flex items-start gap-2 p-2 rounded-lg border ${alertSeverityColor(alert.severity)}`}>
                {alertIcon(alert.alert_type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-bold text-white">{alert.symbol}</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${alert.direction === "bullish" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                      }`}>
                      {alert.direction.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-400 leading-tight mt-0.5">{alert.message}</p>
                </div>
                <div className="flex-shrink-0">
                  <div className="h-5 w-5 rounded-full bg-gray-700/50 flex items-center justify-center">
                    <span className="text-[9px] font-bold text-white">{alert.impact_score}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Symbol Cards */}
        {Object.values(symbols).map((snap) => (
          <SymbolCard key={snap.symbol} snap={snap} />
        ))}

        {/* Empty state */}
        {Object.keys(symbols).length === 0 && !loading && (
          <div className="text-center py-6 text-gray-500 text-sm">
            {error ? `Error: ${error}` : t("whale.noData")}
          </div>
        )}

        {/* Legend */}
        <div className="text-[9px] text-gray-600 text-center pt-2 border-t border-gray-700/30">
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <span>📊 CFTC Weekly (Free)</span>
            <span>|</span>
            <span>⚡ {t("whale.updatesEveryFriday")}</span>
            <span>|</span>
            <span>🐋 {t("whale.pressureRange")}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
