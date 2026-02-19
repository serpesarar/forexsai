"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
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
  Brain,
  Signal,
  Sparkles,
  ArrowRight,
  ChevronRight,
  Info,
} from "lucide-react";
import { useFullscreen } from "../../hooks/useFullscreen";
import styles from "./strategy-optimizer.module.css";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

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

// ═══════════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════════

const SYMBOL_EMOJI: Record<string, string> = {
  "NDX.INDX": "🇺🇸",
  XAUUSD: "🥇",
  "GDAXI.INDX": "🇩🇪",
  "CL.COMM": "🛢️",
};

const STRATEGY_LABELS: Record<string, { name: string; icon: typeof Shield; color: string; desc: string }> = {
  ultra_safe: { name: "Ultra Safe", icon: Shield, color: "#10b981", desc: "Minimal risk" },
  balanced: { name: "Balanced", icon: Target, color: "#3b82f6", desc: "Steady growth" },
  full_power: { name: "Full Power", icon: Zap, color: "#eab308", desc: "Max potential" },
  aggressive: { name: "Aggressive", icon: Flame, color: "#ef4444", desc: "High risk/reward" },
  nasdaq_precision: { name: "NASDAQ Precision", icon: Crosshair, color: "#06b6d4", desc: "Index optimized" },
};

const COMPONENT_ICONS: Record<string, typeof Activity> = {
  vix: Eye,
  trend: TrendingUp,
  volatility: Activity,
  choppiness: BarChart3,
  session: Clock,
  news: Newspaper,
};

const RISK_ZONES = [
  { min: 0, max: 25, label: "EXTREME FEAR", color: "#ef4444", bg: "#7f1d1d", desc: "Avoid trading" },
  { min: 25, max: 45, label: "FEAR", color: "#f97316", bg: "#7c2d12", desc: "High caution" },
  { min: 45, max: 55, label: "NEUTRAL", color: "#eab308", bg: "#713f12", desc: "Mixed signals" },
  { min: 55, max: 75, label: "OPTIMAL", color: "#22c55e", bg: "#14532d", desc: "Good conditions" },
  { min: 75, max: 100, label: "EXTREME OPTIMAL", color: "#00ff88", bg: "#064e3b", desc: "Perfect setup" },
];

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

function getRiskZone(score: number) {
  return RISK_ZONES.find((z) => score >= z.min && score < z.max) || RISK_ZONES[2];
}

function getRiskColor(score: number): string {
  if (score >= 75) return "#00ff88";
  if (score >= 55) return "#22c55e";
  if (score >= 45) return "#eab308";
  if (score >= 25) return "#f97316";
  return "#ef4444";
}

function getRiskGradient(score: number): string {
  if (score >= 75) return "linear-gradient(135deg, #00ff88, #10b981)";
  if (score >= 55) return "linear-gradient(135deg, #22c55e, #16a34a)";
  if (score >= 45) return "linear-gradient(135deg, #eab308, #ca8a04)";
  if (score >= 25) return "linear-gradient(135deg, #f97316, #ea580c)";
  return "linear-gradient(135deg, #ef4444, #dc2626)";
}

function getLevelStyle(level: string): { bg: string; color: string; border: string; glow: string } {
  switch (level) {
    case "OPTIMAL":
      return { bg: "rgba(0,255,136,0.15)", color: "#00ff88", border: "rgba(0,255,136,0.4)", glow: "0 0 20px rgba(0,255,136,0.3)" };
    case "FAVORABLE":
      return { bg: "rgba(34,197,94,0.12)", color: "#22c55e", border: "rgba(34,197,94,0.35)", glow: "0 0 15px rgba(34,197,94,0.2)" };
    case "MODERATE":
      return { bg: "rgba(234,179,8,0.12)", color: "#eab308", border: "rgba(234,179,8,0.35)", glow: "0 0 15px rgba(234,179,8,0.2)" };
    case "HIGH_RISK":
      return { bg: "rgba(249,115,22,0.12)", color: "#f97316", border: "rgba(249,115,22,0.35)", glow: "0 0 15px rgba(249,115,22,0.2)" };
    case "DANGER":
      return { bg: "rgba(239,68,68,0.2)", color: "#ef4444", border: "rgba(239,68,68,0.5)", glow: "0 0 25px rgba(239,68,68,0.4)" };
    default:
      return { bg: "rgba(255,255,255,0.06)", color: "#888", border: "rgba(255,255,255,0.1)", glow: "none" };
  }
}

function formatSession(session: string): string {
  const map: Record<string, string> = {
    asia: "Asia",
    london: "London",
    overlap_london_ny: "LON/NY",
    newyork: "New York",
    xetra: "XETRA",
    xetra_us_overlap: "XETRA/US",
    nymex: "NYMEX",
    london_oil: "London Oil",
    nymex_eia_window: "EIA",
    closed: "Closed",
  };
  return map[session] || session;
}

function formatPositionSize(pct: number): string {
  if (pct <= 0) return "NO TRADE";
  if (pct < 0.5) return `${Math.round(pct * 100)}% Mini`;
  if (pct < 0.8) return `${Math.round(pct * 100)}% Reduced`;
  if (pct <= 1.1) return `${Math.round(pct * 100)}% Normal`;
  return `${Math.round(pct * 100)}% Increased`;
}

function useCountdown(targetMinutes: number = 5) {
  const [seconds, setSeconds] = useState(targetMinutes * 60);

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds((s) => (s > 0 ? s - 1 : targetMinutes * 60));
    }, 1000);
    return () => clearInterval(interval);
  }, [targetMinutes]);

  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

function FearGreedGauge({ score, size = "large" }: { score: number; size?: "small" | "large" }) {
  const zone = getRiskZone(score);
  const percentage = Math.min(Math.max(score, 0), 100);

  if (size === "small") {
    return (
      <div className={styles.miniGauge}>
        <div className={styles.miniGaugeTrack}>
          <div
            className={styles.miniGaugeFill}
            style={{
              width: `${percentage}%`,
              background: getRiskGradient(score),
            }}
          />
        </div>
        <span className={styles.miniGaugeValue} style={{ color: zone.color }}>
          {Math.round(score)}
        </span>
      </div>
    );
  }

  return (
    <div className={styles.fearGreedGauge}>
      <div className={styles.gaugeBarContainer}>
        <div className={styles.gaugeZones}>
          {RISK_ZONES.map((z, i) => (
            <div
              key={z.label}
              className={styles.gaugeZone}
              style={{
                flex: z.max - z.min,
                background: `linear-gradient(180deg, ${z.bg}40, ${z.bg}20)`,
                borderTop: `2px solid ${z.color}`,
              }}
            >
              <span className={styles.zoneLabel} style={{ color: z.color }}>
                {z.label}
              </span>
              <span className={styles.zoneDesc}>{z.desc}</span>
            </div>
          ))}
        </div>

        <div
          className={styles.gaugeIndicator}
          style={{
            left: `${percentage}%`,
            borderColor: zone.color,
            boxShadow: `0 0 20px ${zone.color}, 0 0 40px ${zone.color}60`,
          }}
        >
          <div className={styles.gaugeIndicatorValue} style={{ background: zone.color }}>
            {Math.round(score)}
          </div>
        </div>

        <div className={styles.gaugeGrid}>
          {[0, 25, 50, 75, 100].map((mark) => (
            <div key={mark} className={styles.gaugeGridLine} style={{ left: `${mark}%` }}>
              <span className={styles.gaugeGridLabel}>{mark}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.gaugeScoreDisplay}>
        <div className={styles.gaugeScoreMain} style={{ color: zone.color, textShadow: `0 0 30px ${zone.color}50` }}>
          {Math.round(score)}
        </div>
        <div className={styles.gaugeScoreLabel} style={{ color: zone.color }}>
          {zone.label}
        </div>
      </div>
    </div>
  );
}

function ComponentBreakdown({ components }: { components: RiskComponent[] }) {
  if (!components || components.length === 0) {
    return (
      <div className={styles.noComponents}>
        <Info size={12} />
        <span>Risk components loading...</span>
      </div>
    );
  }

  return (
    <div className={styles.componentsGrid}>
      {components.map((comp) => {
        const CompIcon = COMPONENT_ICONS[comp.name] || Activity;
        const zone = getRiskZone(comp.score);
        return (
          <div key={comp.name} className={styles.componentCard}>
            <div className={styles.componentHeader}>
              <CompIcon size={12} style={{ color: zone.color }} />
              <span className={styles.componentNameSmall}>
                {comp.name === "vix" ? "VIX" : comp.name === "choppiness" ? "CHOP" : comp.name.toUpperCase()}
              </span>
              <span className={styles.componentScoreSmall} style={{ color: zone.color }}>
                {Math.round(comp.score)}
              </span>
            </div>
            <div className={styles.componentBar}>
              <div
                className={styles.componentBarFill}
                style={{
                  width: `${Math.min(comp.score, 100)}%`,
                  background: getRiskGradient(comp.score),
                }}
              />
            </div>
            <span className={styles.componentLabelSmall}>{comp.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function SymbolRiskCard({ data, strategyScores }: { data: SymbolData; strategyScores?: StrategyScoreData[] }) {
  const levelStyle = getLevelStyle(data.risk_level);
  const stratConfig = STRATEGY_LABELS[data.recommended_strategy];
  const StratIcon = stratConfig?.icon || Target;
  const recommended = strategyScores?.find((s) => s.is_recommended);
  const zone = getRiskZone(data.overall_score);

  return (
    <div className={styles.riskCard} style={{ boxShadow: levelStyle.glow }}>
      <div className={styles.riskCardHeader}>
        <div className={styles.symbolIdentity}>
          <span className={styles.symbolEmojiLarge}>{SYMBOL_EMOJI[data.symbol] || "📊"}</span>
          <div className={styles.symbolInfo}>
            <span className={styles.symbolLabel}>{data.label}</span>
            <span className={styles.symbolSession}>{formatSession(data.session)}</span>
          </div>
        </div>
        <div className={styles.symbolScoreBadge} style={{ borderColor: zone.color }}>
          <span className={styles.scoreNumber} style={{ color: zone.color }}>
            {Math.round(data.overall_score)}
          </span>
          <span className={styles.scoreMax}>/100</span>
        </div>
      </div>

      <FearGreedGauge score={data.overall_score} size="small" />

      <div className={styles.statusRow}>
        <span
          className={styles.statusBadge}
          style={{
            background: levelStyle.bg,
            color: levelStyle.color,
            borderColor: levelStyle.border,
          }}
        >
          {data.risk_level.replace("_", " ")}
        </span>
        <span
          className={styles.trendBadge}
          style={{
            color: data.trend_direction === "BULLISH" ? "#00ff88" : data.trend_direction === "BEARISH" ? "#ef4444" : "#888",
          }}
        >
          {data.trend_direction === "BULLISH" ? "▲ BULLISH" : data.trend_direction === "BEARISH" ? "▼ BEARISH" : "◆ NEUTRAL"}
        </span>
        <span className={styles.regimeBadge}>{data.regime.replace(/_/g, " ")}</span>
      </div>

      <ComponentBreakdown components={data.components} />

      <div className={styles.strategyRec}>
        <div className={styles.recSection}>
          <span className={styles.recLabelSmall}>Best Strategy</span>
          <div className={styles.recValue} style={{ color: stratConfig?.color || "#00ff88" }}>
            <StratIcon size={14} />
            {stratConfig?.name || data.recommended_strategy}
          </div>
          {stratConfig?.desc && <span className={styles.recDesc}>{stratConfig.desc}</span>}
        </div>
        <div className={styles.recSection}>
          <span className={styles.recLabelSmall}>Position</span>
          <div
            className={styles.recValue}
            style={{
              color: data.recommended_position_pct <= 0 ? "#ef4444" : data.recommended_position_pct < 0.7 ? "#f97316" : zone.color,
            }}
          >
            {formatPositionSize(data.recommended_position_pct)}
          </div>
        </div>
        {recommended && recommended.total_signals > 0 && (
          <div className={styles.recSection}>
            <span className={styles.recLabelSmall}>Win Rate</span>
            <div
              className={styles.recValue}
              style={{ color: recommended.win_rate >= 55 ? "#00ff88" : recommended.win_rate >= 45 ? "#eab308" : "#ef4444" }}
            >
              {recommended.win_rate.toFixed(1)}%
              <span className={styles.signalCount}>({recommended.total_signals})</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PANEL
// ═══════════════════════════════════════════════════════════════════════════════

async function fetchOptimizer(days: number): Promise<OptimizerResponse> {
  const res = await fetch(`${API_BASE}/api/optimizer/run?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch optimizer data");
  return res.json();
}

export default function StrategyOptimizerPanel() {
  const [days, setDays] = useState(14);
  const { isFullscreen, toggleFullscreen } = useFullscreen();
  const countdown = useCountdown(5);

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

  const globalScore = data?.global_risk_score ?? 50;
  const globalZone = getRiskZone(globalScore);
  const globalLevelStyle = getLevelStyle(data?.global_risk_level ?? "MODERATE");

  return (
    <div className={`${styles.panel} ${isFullscreen ? styles.panelFullscreen : ""}`}>
      {/* Header */}
      <div className={styles.panelHeader}>
        <div className={styles.headerMain}>
          <div className={styles.headerIcon}>
            <Brain size={24} />
            <div className={styles.iconPulse} />
          </div>
          <div className={styles.headerText}>
            <h3 className={styles.panelTitle}>Strategy Auto-Optimization Loop</h3>
            <p className={styles.panelSubtitle}>
              Real-time risk scoring & strategy selection via Bayesian optimization
            </p>
          </div>
        </div>

        <div className={styles.headerControls}>
          <div className={styles.updateTimer}>
            <Clock size={12} />
            <span>Update in {countdown}</span>
          </div>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className={styles.daysSelect}
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
          <button onClick={() => refetch()} className={styles.controlBtn} title="Refresh">
            <RefreshCw size={14} className={isFetching ? styles.spin : ""} />
          </button>
          <button onClick={toggleFullscreen} className={styles.controlBtn}>
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {/* Fear & Greed Gauge */}
      {data && !data.error && (
        <div className={styles.gaugeSection}>
          <div className={styles.gaugeHeader}>
            <div className={styles.gaugeTitle}>
              <Gauge size={16} />
              <span>Market Risk Index</span>
            </div>
            {data.vix_price != null && (
              <div className={styles.vixChip}>
                <Eye size={12} />
                VIX {data.vix_price.toFixed(2)}
              </div>
            )}
            {!data.market_open && (
              <div className={styles.marketClosedChip}>
                <AlertTriangle size={12} />
                MARKET CLOSED
              </div>
            )}
          </div>

          <FearGreedGauge score={globalScore} size="large" />

          <div className={styles.globalStats}>
            <div className={styles.statBox} style={{ borderColor: globalZone.color }}>
              <span className={styles.statLabel}>Risk Level</span>
              <span className={styles.statValue} style={{ color: globalZone.color }}>
                {data.global_risk_level.replace("_", " ")}
              </span>
            </div>
            <div className={styles.statBox}>
              <span className={styles.statLabel}>VIX Regime</span>
              <span className={styles.statValue}>{data.vix_regime}</span>
            </div>
            <div className={styles.statBox}>
              <span className={styles.statLabel}>Symbols</span>
              <span className={styles.statValue}>{data.symbols?.length || 0}</span>
            </div>
            <div className={styles.statBox}>
              <span className={styles.statLabel}>Last Update</span>
              <span className={styles.statValue}>
                {new Date(data.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}>
            <Cpu size={32} className={styles.spin} />
          </div>
          <span>Calculating risk scores & optimizing strategies...</span>
        </div>
      ) : error ? (
        <div className={styles.errorState}>
          <AlertTriangle size={24} />
          <span>Failed to load optimizer data</span>
          <button onClick={() => refetch()} className={styles.retryBtn}>
            Retry
          </button>
        </div>
      ) : data && !data.error ? (
        <>
          {/* Symbol Cards Grid */}
          <div className={styles.symbolsSection}>
            <div className={styles.sectionHeader}>
              <Signal size={14} />
              <span>Per-Symbol Risk Analysis</span>
            </div>
            <div className={styles.riskCardsGrid}>
              {data.symbols.map((sym) => (
                <SymbolRiskCard
                  key={sym.symbol}
                  data={sym}
                  strategyScores={data.strategy_scores[sym.symbol]}
                />
              ))}
            </div>
          </div>

          {/* Notes */}
          {data.optimization_notes.length > 0 && (
            <div className={styles.notesSection}>
              {data.optimization_notes.map((note, i) => (
                <div key={i} className={styles.noteItem}>
                  <Sparkles size={12} />
                  <span>{note}</span>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className={styles.errorState}>
          <AlertTriangle size={24} />
          <span>{data?.error || "Unknown error"}</span>
        </div>
      )}
    </div>
  );
}
