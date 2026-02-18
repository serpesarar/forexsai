"use client";

import { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Cpu,
  RefreshCw,
  Shield,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Newspaper,
  BarChart3,
  Zap,
  AlertTriangle,
  Maximize2,
  Minimize2,
  Eye,
  Gauge,
  Target,
  Flame,
  Crosshair,
} from "lucide-react";
import { useFullscreen } from "../../hooks/useFullscreen";
import styles from "./strategy-optimizer.module.css";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

// ─── Types ───────────────────────────────────────────────────

interface RiskComponent {
  name: string;
  score: number;
  weight: number;
  label: string;
  detail: string;
}

interface SymbolData {
  symbol: string;
  label: string;
  overall_score: number;
  risk_level: string;
  regime: string;
  session: string;
  recommended_strategy: string;
  recommended_position_pct: number;
  trend_direction: string;
  components: RiskComponent[];
}

interface StrategyScoreData {
  strategy: string;
  win_rate: number;
  total_signals: number;
  wins: number;
  losses: number;
  avg_profit_pips: number;
  avg_loss_pips: number;
  profit_factor: number;
  max_consecutive_losses: number;
  composite_score: number;
  is_recommended: boolean;
}

interface OptimizerResponse {
  timestamp: string;
  global_risk_score: number;
  global_risk_level: string;
  vix_price: number | null;
  vix_regime: string;
  market_open: boolean;
  optimization_notes: string[];
  symbols: SymbolData[];
  strategy_scores: Record<string, StrategyScoreData[]>;
  error?: string;
}

// ─── Constants ───────────────────────────────────────────────

const SYMBOL_EMOJI: Record<string, string> = {
  "NDX.INDX": "🇺🇸",
  XAUUSD: "🥇",
  "GDAXI.INDX": "🇩🇪",
  "CL.COMM": "🛢️",
};

const STRATEGY_LABELS: Record<string, { name: string; icon: typeof Shield; color: string }> = {
  ultra_safe: { name: "Ultra Safe", icon: Shield, color: "#10b981" },
  balanced: { name: "Balanced", icon: Target, color: "#3b82f6" },
  full_power: { name: "Full Power", icon: Zap, color: "#eab308" },
  aggressive: { name: "Aggressive", icon: Flame, color: "#ef4444" },
  nasdaq_precision: { name: "NASDAQ Precision", icon: Crosshair, color: "#06b6d4" },
};

const COMPONENT_ICONS: Record<string, typeof Activity> = {
  vix: Eye,
  trend: TrendingUp,
  volatility: Activity,
  choppiness: BarChart3,
  session: Clock,
  news: Newspaper,
};

// ─── Utility Functions ───────────────────────────────────────

function getRiskColor(score: number): string {
  if (score >= 75) return "#00ff88";
  if (score >= 60) return "#22d3ee";
  if (score >= 42) return "#eab308";
  if (score >= 25) return "#f97316";
  return "#ef4444";
}

function getRiskGradient(score: number): string {
  if (score >= 75) return "linear-gradient(90deg, #00ff88, #10b981)";
  if (score >= 60) return "linear-gradient(90deg, #22d3ee, #06b6d4)";
  if (score >= 42) return "linear-gradient(90deg, #eab308, #f59e0b)";
  if (score >= 25) return "linear-gradient(90deg, #f97316, #ea580c)";
  return "linear-gradient(90deg, #ef4444, #dc2626)";
}

function getLevelStyle(level: string): { bg: string; color: string; border: string } {
  switch (level) {
    case "OPTIMAL":
      return { bg: "rgba(0,255,136,0.12)", color: "#00ff88", border: "rgba(0,255,136,0.3)" };
    case "FAVORABLE":
      return { bg: "rgba(34,211,238,0.12)", color: "#22d3ee", border: "rgba(34,211,238,0.3)" };
    case "MODERATE":
      return { bg: "rgba(234,179,8,0.12)", color: "#eab308", border: "rgba(234,179,8,0.3)" };
    case "HIGH_RISK":
      return { bg: "rgba(249,115,22,0.12)", color: "#f97316", border: "rgba(249,115,22,0.3)" };
    case "DANGER":
      return { bg: "rgba(239,68,68,0.15)", color: "#ef4444", border: "rgba(239,68,68,0.35)" };
    default:
      return { bg: "rgba(255,255,255,0.06)", color: "#888", border: "rgba(255,255,255,0.1)" };
  }
}

function getVixStyle(regime: string): { bg: string; color: string } {
  switch (regime) {
    case "LOW":
    case "EXTREME_LOW":
      return { bg: "rgba(0,255,136,0.1)", color: "#00ff88" };
    case "NORMAL":
      return { bg: "rgba(34,211,238,0.1)", color: "#22d3ee" };
    case "ELEVATED":
      return { bg: "rgba(234,179,8,0.1)", color: "#eab308" };
    case "HIGH":
    case "VERY_HIGH":
      return { bg: "rgba(249,115,22,0.12)", color: "#f97316" };
    case "EXTREME":
      return { bg: "rgba(239,68,68,0.15)", color: "#ef4444" };
    default:
      return { bg: "rgba(255,255,255,0.06)", color: "#888" };
  }
}

function formatSession(session: string): string {
  const map: Record<string, string> = {
    asia: "Asia",
    london: "London",
    overlap_london_ny: "LON/NY Overlap",
    newyork: "New York",
    xetra: "XETRA",
    xetra_us_overlap: "XETRA/US",
    nymex: "NYMEX",
    london_oil: "London Oil",
    nymex_eia_window: "EIA Window",
    closed: "Closed",
  };
  return map[session] || session;
}

function formatPositionSize(pct: number): string {
  if (pct <= 0) return "NO TRADE";
  if (pct < 0.5) return `${Math.round(pct * 100)}% (Mini)`;
  if (pct < 0.8) return `${Math.round(pct * 100)}% (Reduced)`;
  if (pct <= 1.1) return `${Math.round(pct * 100)}% (Normal)`;
  return `${Math.round(pct * 100)}% (Increased)`;
}

// ─── Component: Risk Bar ─────────────────────────────────────

function RiskBar({ score, height = 6 }: { score: number; height?: number }) {
  return (
    <div className={styles.riskBarTrack} style={{ height }}>
      <div
        className={styles.riskBarFill}
        style={{
          width: `${Math.min(score, 100)}%`,
          background: getRiskGradient(score),
          boxShadow: `0 0 8px ${getRiskColor(score)}40`,
        }}
      />
    </div>
  );
}

// ─── Component: Symbol Card ──────────────────────────────────

function SymbolCard({ data, strategyScores }: { data: SymbolData; strategyScores?: StrategyScoreData[] }) {
  const levelStyle = getLevelStyle(data.risk_level);
  const stratConfig = STRATEGY_LABELS[data.recommended_strategy];
  const StratIcon = stratConfig?.icon || Target;
  const recommended = strategyScores?.find((s) => s.is_recommended);

  return (
    <div className={styles.symbolCard}>
      {/* Top color strip */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 2,
          background: getRiskGradient(data.overall_score),
        }}
      />

      {/* Header: Symbol name + Score */}
      <div className={styles.symbolCardHeader}>
        <div className={styles.symbolName}>
          <span className={styles.symbolEmoji}>{SYMBOL_EMOJI[data.symbol] || "📊"}</span>
          {data.label}
        </div>
        <div className={styles.symbolScore} style={{ color: getRiskColor(data.overall_score) }}>
          {Math.round(data.overall_score)}
        </div>
      </div>

      {/* Risk bar */}
      <div className={styles.riskBarContainer}>
        <RiskBar score={data.overall_score} />
        <div className={styles.riskBarLabels}>
          <span>DANGER</span>
          <span
            className={styles.levelBadge}
            style={{
              background: levelStyle.bg,
              color: levelStyle.color,
              border: `1px solid ${levelStyle.border}`,
            }}
          >
            {data.risk_level.replace("_", " ")}
          </span>
          <span>OPTIMAL</span>
        </div>
      </div>

      {/* Component breakdown */}
      <div className={styles.components}>
        {data.components.map((comp) => {
          const CompIcon = COMPONENT_ICONS[comp.name] || Activity;
          return (
            <div key={comp.name} className={styles.componentRow}>
              <div className={styles.componentIcon}>
                <CompIcon size={10} />
              </div>
              <span className={styles.componentName}>
                {comp.name === "vix" ? "VIX" : comp.name === "choppiness" ? "Chop" : comp.name.charAt(0).toUpperCase() + comp.name.slice(1)}
              </span>
              <div className={styles.componentTrack}>
                <div
                  className={styles.componentFill}
                  style={{
                    width: `${Math.min(comp.score, 100)}%`,
                    background: getRiskGradient(comp.score),
                  }}
                />
              </div>
              <span className={styles.componentScore} style={{ color: getRiskColor(comp.score) }}>
                {Math.round(comp.score)}
              </span>
              <span className={styles.componentLabel}>{comp.label}</span>
            </div>
          );
        })}
      </div>

      {/* Tags: regime, session, trend */}
      <div className={styles.tags}>
        <span
          className={styles.tag}
          style={{
            color: data.trend_direction === "BULLISH" ? "#00ff88" : data.trend_direction === "BEARISH" ? "#ef4444" : "#888",
            borderColor:
              data.trend_direction === "BULLISH"
                ? "rgba(0,255,136,0.2)"
                : data.trend_direction === "BEARISH"
                ? "rgba(239,68,68,0.2)"
                : "rgba(255,255,255,0.06)",
          }}
        >
          {data.trend_direction === "BULLISH" ? "▲" : data.trend_direction === "BEARISH" ? "▼" : "◆"} {data.trend_direction}
        </span>
        <span className={styles.tag}>{data.regime.replace(/_/g, " ")}</span>
        <span className={styles.tag}>
          <Clock size={8} style={{ display: "inline", marginRight: 2 }} />
          {formatSession(data.session)}
        </span>
      </div>

      {/* Recommendation */}
      <div className={styles.recommendation}>
        <div>
          <div className={styles.recLabel}>Best Strategy</div>
          <div className={styles.recStrategy} style={{ color: stratConfig?.color || "#00ff88" }}>
            <StratIcon size={11} style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }} />
            {stratConfig?.name || data.recommended_strategy}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className={styles.recLabel}>Position</div>
          <div
            className={styles.recPosition}
            style={{
              color: data.recommended_position_pct <= 0 ? "#ef4444" : data.recommended_position_pct < 0.7 ? "#f97316" : getRiskColor(data.overall_score),
            }}
          >
            {formatPositionSize(data.recommended_position_pct)}
          </div>
        </div>
        {recommended && recommended.total_signals > 0 && (
          <div style={{ textAlign: "right" }}>
            <div className={styles.recLabel}>Win Rate</div>
            <div className={styles.recPosition} style={{ color: recommended.win_rate >= 55 ? "#00ff88" : recommended.win_rate >= 45 ? "#eab308" : "#ef4444" }}>
              {recommended.win_rate.toFixed(1)}%
              <span style={{ fontSize: 8, color: "rgba(255,255,255,0.3)", marginLeft: 3 }}>({recommended.total_signals})</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Panel ──────────────────────────────────────────────

async function fetchOptimizer(days: number): Promise<OptimizerResponse> {
  const res = await fetch(`${API_BASE}/api/optimizer/run?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch optimizer data");
  return res.json();
}

export default function StrategyOptimizerPanel() {
  const [days, setDays] = useState(14);
  const { isFullscreen, toggleFullscreen } = useFullscreen();

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["strategy-optimizer", days],
    queryFn: () => fetchOptimizer(days),
    staleTime: 120000,
    refetchInterval: 300000,
    refetchIntervalInBackground: false,
  });

  useEffect(() => {
    const handler = () => refetch();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [refetch]);

  const globalScore = data?.global_risk_score ?? 0;
  const globalLevel = data?.global_risk_level ?? "MODERATE";
  const globalLevelStyle = getLevelStyle(globalLevel);
  const vixStyle = getVixStyle(data?.vix_regime ?? "UNKNOWN");

  return (
    <div className={`${styles.panel} ${isFullscreen ? styles.panelFullscreen : ""}`}>
      {/* ═══ HEADER ═══ */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <Cpu size={18} className={styles.iconGlow} />
          <div>
            <h3 className={styles.title}>Strategy Auto-Optimization Loop</h3>
            <p className={styles.subtitle}>
              Real-time risk scoring & strategy selection • {data?.symbols?.length || 4} symbols
            </p>
          </div>
        </div>

        <div className={styles.headerControls}>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            style={{
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 6,
              color: "#d1d4dc",
              padding: "4px 8px",
              fontSize: 11,
              cursor: "pointer",
              outline: "none",
            }}
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>

          <button onClick={() => refetch()} className={styles.refreshBtn} title="Refresh">
            <RefreshCw size={14} className={isFetching ? styles.spin : ""} />
          </button>
          <button onClick={toggleFullscreen} className={styles.refreshBtn} title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {/* ═══ GLOBAL RISK BAR ═══ */}
      {data && !data.error && (
        <div className={styles.globalBar}>
          <span className={styles.globalLabel}>
            <Gauge size={12} style={{ display: "inline", marginRight: 4, verticalAlign: "middle" }} />
            Market Risk
          </span>

          <div className={styles.globalTrack}>
            <div
              className={styles.globalFill}
              style={{
                width: `${Math.min(globalScore, 100)}%`,
                background: getRiskGradient(globalScore),
                boxShadow: `0 0 12px ${getRiskColor(globalScore)}50`,
              }}
            />
          </div>

          <span className={styles.globalScore} style={{ color: getRiskColor(globalScore) }}>
            {Math.round(globalScore)}
          </span>

          <span
            className={`${styles.globalLevel} ${globalLevel === "DANGER" ? styles.pulseDanger : ""}`}
            style={{
              background: globalLevelStyle.bg,
              color: globalLevelStyle.color,
              border: `1px solid ${globalLevelStyle.border}`,
            }}
          >
            {globalLevel.replace("_", " ")}
          </span>

          {/* VIX badge */}
          {data.vix_price != null && (
            <span
              className={styles.vixBadge}
              style={{
                background: vixStyle.bg,
                color: vixStyle.color,
                border: `1px solid ${vixStyle.color}30`,
              }}
            >
              <Eye size={10} />
              VIX {data.vix_price.toFixed(1)} ({data.vix_regime})
            </span>
          )}

          {!data.market_open && (
            <span
              className={styles.vixBadge}
              style={{ background: "rgba(239,68,68,0.1)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.2)" }}
            >
              MARKET CLOSED
            </span>
          )}
        </div>
      )}

      {/* ═══ CONTENT ═══ */}
      {isLoading ? (
        <div className={styles.loading}>
          <RefreshCw size={16} className={styles.spin} />
          Calculating risk scores & optimizing strategies...
        </div>
      ) : error ? (
        <div className={styles.error}>
          <AlertTriangle size={16} />
          Failed to load optimizer data
          <button onClick={() => refetch()} style={{ color: "#22d3ee", background: "none", border: "none", cursor: "pointer", fontSize: 11 }}>
            Retry
          </button>
        </div>
      ) : data && !data.error ? (
        <>
          {/* ═══ SYMBOL GRID ═══ */}
          <div className={styles.symbolGrid}>
            {data.symbols.map((sym) => (
              <SymbolCard key={sym.symbol} data={sym} strategyScores={data.strategy_scores[sym.symbol]} />
            ))}
          </div>

          {/* ═══ NOTES ═══ */}
          {data.optimization_notes.length > 0 && (
            <div className={styles.notes}>
              {data.optimization_notes.map((note, i) => (
                <span key={i} className={styles.note}>
                  <AlertTriangle size={10} />
                  {note}
                </span>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className={styles.error}>
          <AlertTriangle size={16} />
          {data?.error || "Unknown error"}
        </div>
      )}
    </div>
  );
}
