"use client";

/**
 * Pandemic Sensitivity Index (PSI) Panel
 * =======================================
 * Macro-overlay early-warning gauge. Inspired by the 2020 observation that a
 * small basket of names (Moderna, Zoom, Abbott, Honeywell, Thermo Fisher)
 * moved 4-8 weeks before the broader market priced in COVID-19.
 *
 * The panel is divided into:
 *   1. Hero gauge   — composite PSI 0-100 with risk-level badge
 *   2. Market impact — per-instrument trading guidance
 *   3. Basket grid  — six basket scores with their top contributors
 *   4. Sparkline    — 90-day reconstructed PSI history
 */

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  RefreshCw,
  ShieldAlert,
  Activity,
  Stethoscope,
  Syringe,
  Wifi,
  Plane,
  Gauge,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Info,
} from "lucide-react";
import { fetcher } from "../../lib/api";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Contributor {
  ticker: string;
  label: string;
  last_price: number;
  return_5d: number;
  return_20d: number;
  rel_return_20d: number;
  volume_z: number;
  breakout_50d: boolean;
  score: number;
  direction_sign: number;
}

interface Basket {
  key: string;
  label: string;
  weight: number;
  score: number;
  rationale: string;
  avg_rel_return_20d: number;
  avg_volume_z: number;
  breakout_pct: number;
  contributors: Contributor[];
}

interface PSIData {
  psi_score: number;
  risk_level: "NORMAL" | "ELEVATED" | "WARNING" | "HIGH_RISK" | "CRITICAL";
  risk_color: string;
  summary: string;
  market_impact: Record<string, string>;
  baskets: Basket[];
  historical_percentile: number | null;
  generated_at: string;
  age_minutes: number;
}

interface PSIResponse {
  success: boolean;
  data: PSIData;
  error?: string;
}

interface HistoryPoint {
  date: string;
  psi: number;
  risk_level: string;
}

interface HistoryResponse {
  success: boolean;
  series: HistoryPoint[];
}

// ─── Visual helpers ──────────────────────────────────────────────────────────

const BASKET_ICON: Record<string, typeof Syringe> = {
  vaccine_therapeutics: Syringe,
  diagnostics_testing: Stethoscope,
  remote_economy: Wifi,
  ppe_defensive: ShieldAlert,
  inverse_travel_leisure: Plane,
  macro_risk: Activity,
};

const SYMBOL_LABEL: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "GDAXI.INDX": "DAX",
  XAUUSD: "GOLD",
  "USOIL.FOREX": "OIL",
};

const SYMBOL_EMOJI: Record<string, string> = {
  "NDX.INDX": "🇺🇸",
  "GDAXI.INDX": "🇩🇪",
  XAUUSD: "🥇",
  "USOIL.FOREX": "🛢️",
};

function riskTextColor(level: string): string {
  switch (level) {
    case "CRITICAL": return "text-red-400";
    case "HIGH_RISK": return "text-orange-400";
    case "WARNING": return "text-yellow-400";
    case "ELEVATED": return "text-amber-300";
    default: return "text-emerald-400";
  }
}

function riskBgClass(level: string): string {
  switch (level) {
    case "CRITICAL": return "bg-red-500/20 border-red-500/40";
    case "HIGH_RISK": return "bg-orange-500/15 border-orange-500/30";
    case "WARNING": return "bg-yellow-500/15 border-yellow-500/30";
    case "ELEVATED": return "bg-amber-500/10 border-amber-500/25";
    default: return "bg-emerald-500/10 border-emerald-500/25";
  }
}

function basketColor(score: number): string {
  if (score >= 70) return "#dc2626";
  if (score >= 50) return "#ea580c";
  if (score >= 30) return "#f59e0b";
  if (score >= 15) return "#eab308";
  return "#16a34a";
}

function impactBadge(text: string): string {
  const upper = text.toUpperCase();
  if (upper.startsWith("STRONG SELL")) return "bg-red-500/25 text-red-300 border-red-500/40";
  if (upper.startsWith("STRONG BUY")) return "bg-emerald-500/25 text-emerald-300 border-emerald-500/40";
  if (upper.startsWith("SELL")) return "bg-red-500/15 text-red-300 border-red-500/30";
  if (upper.startsWith("BUY")) return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
  return "bg-gray-500/15 text-gray-300 border-gray-500/30";
}

function impactHeadline(text: string): string {
  const m = text.match(/^(STRONG SELL|STRONG BUY|SELL|BUY|NEUTRAL|No PSI signal)/i);
  return m ? m[1].toUpperCase() : "NEUTRAL";
}

function formatAge(minutes: number): string {
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${Math.round(minutes)}m ago`;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h ${m}m ago`;
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function HeroGauge({ score, level, color }: { score: number; level: string; color: string }) {
  const pct = Math.max(0, Math.min(100, score));
  const angle = (pct / 100) * 180 - 90; // -90deg .. +90deg

  return (
    <div className="relative flex flex-col items-center justify-center w-full">
      <div className="relative w-full max-w-[280px] aspect-[2/1]">
        {/* Arc background */}
        <svg viewBox="0 0 200 110" className="absolute inset-0 w-full h-full">
          <defs>
            <linearGradient id="psiGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#16a34a" />
              <stop offset="25%" stopColor="#eab308" />
              <stop offset="50%" stopColor="#f59e0b" />
              <stop offset="75%" stopColor="#ea580c" />
              <stop offset="100%" stopColor="#dc2626" />
            </linearGradient>
          </defs>
          <path
            d="M 15 100 A 85 85 0 0 1 185 100"
            fill="none"
            stroke="url(#psiGrad)"
            strokeWidth="14"
            strokeLinecap="round"
            opacity="0.85"
          />
          {/* Tick marks at 20/40/60/80 */}
          {[20, 40, 60, 80].map((v) => {
            const a = (v / 100) * Math.PI - Math.PI;
            const x1 = 100 + Math.cos(a) * 78;
            const y1 = 100 + Math.sin(a) * 78;
            const x2 = 100 + Math.cos(a) * 92;
            const y2 = 100 + Math.sin(a) * 92;
            return (
              <line
                key={v}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="rgba(255,255,255,0.35)"
                strokeWidth="1.5"
              />
            );
          })}
          {/* Needle */}
          <g transform={`rotate(${angle} 100 100)`}>
            <line
              x1="100" y1="100" x2="100" y2="22"
              stroke={color}
              strokeWidth="3"
              strokeLinecap="round"
              style={{ filter: `drop-shadow(0 0 6px ${color})` }}
            />
            <circle cx="100" cy="100" r="6" fill={color} />
          </g>
        </svg>

        {/* Score & label */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center pb-1">
          <div className="text-5xl font-extrabold tabular-nums" style={{ color }}>
            {Math.round(score)}
          </div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-gray-400 mt-0.5">
            Pandemic Sensitivity
          </div>
        </div>
      </div>
      <div
        className={`mt-2 px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full border ${riskBgClass(level)} ${riskTextColor(level)}`}
      >
        {level.replace("_", " ")}
      </div>
    </div>
  );
}

function Sparkline({ series }: { series: HistoryPoint[] }) {
  if (series.length < 2) {
    return <div className="text-[11px] text-gray-500">History building... (need 60+ trading days)</div>;
  }
  const w = 320;
  const h = 60;
  const min = 0;
  const max = 100;
  const points = series.map((p, i) => {
    const x = (i / (series.length - 1)) * w;
    const y = h - ((p.psi - min) / (max - min)) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const path = `M ${points.join(" L ")}`;
  const lastPsi = series[series.length - 1]?.psi ?? 0;
  const firstPsi = series[0]?.psi ?? 0;
  const delta = lastPsi - firstPsi;

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <div className="text-[11px] uppercase tracking-wider text-gray-400">
          {series.length}d PSI History
        </div>
        <div className={`text-[11px] tabular-nums ${delta >= 0 ? "text-orange-300" : "text-emerald-300"}`}>
          {delta >= 0 ? "+" : ""}{delta.toFixed(1)} vs start
        </div>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-14">
        {/* threshold guides */}
        {[20, 40, 60, 80].map((t) => {
          const y = h - (t / 100) * h;
          return (
            <line key={t} x1="0" x2={w} y1={y} y2={y}
              stroke="rgba(255,255,255,0.06)" strokeDasharray="2,3" />
          );
        })}
        <path d={path} fill="none" stroke="#a78bfa" strokeWidth="1.5" />
        {/* dot at last point */}
        <circle
          cx={(w * (series.length - 1)) / Math.max(1, series.length - 1)}
          cy={h - (lastPsi / 100) * h}
          r="2.5"
          fill="#a78bfa"
        />
      </svg>
    </div>
  );
}

function BasketCard({ basket }: { basket: Basket }) {
  const [open, setOpen] = useState(false);
  const Icon = BASKET_ICON[basket.key] || Activity;
  const color = basketColor(basket.score);

  return (
    <div className="bg-gray-900/50 border border-gray-700/40 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full px-3 py-2.5 flex items-center gap-3 hover:bg-gray-800/40 transition-colors"
      >
        <div
          className="w-9 h-9 rounded-md flex items-center justify-center shrink-0"
          style={{ background: `${color}25`, color }}
        >
          <Icon className="w-4.5 h-4.5" />
        </div>
        <div className="flex-1 min-w-0 text-left">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-100 truncate">{basket.label}</span>
            <span className="text-[10px] text-gray-500 tabular-nums">
              w{(basket.weight * 100).toFixed(0)}%
            </span>
          </div>
          <div className="text-[11px] text-gray-400 truncate">{basket.rationale}</div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right">
            <div className="text-lg font-bold tabular-nums" style={{ color }}>
              {Math.round(basket.score)}
            </div>
            <div className="text-[9px] uppercase tracking-wider text-gray-500">score</div>
          </div>
          {open ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
        </div>
      </button>

      {/* Score bar */}
      <div className="h-1 bg-gray-800/60">
        <div
          className="h-full transition-all duration-500"
          style={{ width: `${basket.score}%`, background: color }}
        />
      </div>

      {open && (
        <div className="px-3 py-2.5 border-t border-gray-700/40 bg-gray-950/40 space-y-1.5">
          <div className="grid grid-cols-3 gap-2 text-[10px] uppercase tracking-wider text-gray-500 mb-1">
            <span>Avg 20d Rel. Ret</span>
            <span>Avg Vol Z</span>
            <span>Breakout %</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs tabular-nums mb-2">
            <span className={basket.avg_rel_return_20d >= 0 ? "text-emerald-300" : "text-red-300"}>
              {basket.avg_rel_return_20d >= 0 ? "+" : ""}{basket.avg_rel_return_20d}%
            </span>
            <span className={basket.avg_volume_z >= 0 ? "text-amber-300" : "text-gray-400"}>
              {basket.avg_volume_z >= 0 ? "+" : ""}{basket.avg_volume_z}σ
            </span>
            <span className="text-gray-300">{basket.breakout_pct}%</span>
          </div>
          <div className="space-y-1">
            {basket.contributors.map((c) => (
              <div
                key={c.ticker}
                className="flex items-center justify-between gap-2 px-2 py-1.5 bg-gray-900/60 rounded text-[11px]"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-mono font-bold text-gray-200 w-12 shrink-0">{c.ticker}</span>
                  <span className="text-gray-500 truncate">{c.label}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span
                    className={`tabular-nums ${
                      c.return_20d * c.direction_sign >= 0 ? "text-emerald-300" : "text-red-300"
                    }`}
                    title="20-day return"
                  >
                    {c.return_20d >= 0 ? "+" : ""}{c.return_20d.toFixed(1)}%
                  </span>
                  {c.breakout_50d && (
                    <span className="text-amber-400" title="50-day breakout">
                      {c.direction_sign > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    </span>
                  )}
                  <span
                    className="font-bold tabular-nums w-8 text-right"
                    style={{ color: basketColor(c.score) }}
                  >
                    {Math.round(c.score)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main ────────────────────────────────────────────────────────────────────

export default function PandemicSensitivityPanel() {
  const [data, setData] = useState<PSIData | null>(null);
  const [series, setSeries] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetcher<PSIResponse>("/api/pandemic-sensitivity");
      if (!res.success) throw new Error(res.error || "Failed to load PSI");
      setData(res.data);
    } catch (e: any) {
      setError(e?.message || "Failed to load PSI");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetcher<HistoryResponse>("/api/pandemic-sensitivity/history?days=90");
      if (res.success) setSeries(res.series);
    } catch {
      /* sparkline is best-effort */
    }
  }, []);

  useEffect(() => {
    load();
    loadHistory();
    // PSI updates every 6h on the backend; refresh the panel every 30 min so
    // the elapsed-time clock stays accurate.
    const id = setInterval(() => {
      load();
      loadHistory();
    }, 30 * 60 * 1000);
    return () => clearInterval(id);
  }, [load, loadHistory]);

  const sortedBaskets = useMemo(() => {
    if (!data) return [];
    return [...data.baskets].sort((a, b) => b.score - a.score);
  }, [data]);

  return (
    <div className="bg-gradient-to-br from-gray-900 via-gray-900 to-purple-950/30 border border-purple-500/20 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-purple-500/15 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-purple-500/20 flex items-center justify-center">
            <Gauge className="w-4 h-4 text-purple-300" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-gray-100 tracking-wide">PANDEMIC SENSITIVITY INDEX</h3>
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <div className="text-[10px] uppercase tracking-wider text-gray-500">
              6-basket health-crisis early-warning gauge
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {data && (
            <span className="text-[10px] text-gray-500 tabular-nums">
              {formatAge(data.age_minutes)}
            </span>
          )}
          <button
            type="button"
            onClick={() => { load(); loadHistory(); }}
            className="p-1.5 rounded hover:bg-gray-800 text-gray-400 transition-colors"
            disabled={loading}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-4">
        {error && (
          <div className="px-3 py-2 bg-red-500/10 border border-red-500/30 rounded text-[12px] text-red-300">
            {error}
          </div>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center py-10 text-gray-500 text-sm">
            <RefreshCw className="w-4 h-4 animate-spin mr-2" /> Loading PSI baskets…
          </div>
        )}

        {data && (
          <>
            {/* Hero gauge + summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <HeroGauge score={data.psi_score} level={data.risk_level} color={data.risk_color} />
              <div className="flex flex-col justify-center gap-2">
                <div className={`text-[12px] leading-relaxed px-3 py-2.5 rounded-lg border ${riskBgClass(data.risk_level)} text-gray-200`}>
                  <div className="flex items-start gap-2">
                    <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 opacity-70" />
                    <span>{data.summary}</span>
                  </div>
                </div>
                <Sparkline series={series} />
              </div>
            </div>

            {/* Market impact */}
            {data.market_impact && Object.keys(data.market_impact).length > 0 && (
              <div className="bg-gray-900/40 border border-gray-700/40 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-gray-500 mb-2">
                  Market Impact
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {Object.entries(data.market_impact).map(([sym, txt]) => (
                    <div
                      key={sym}
                      className="flex items-start gap-2 p-2 bg-gray-950/50 border border-gray-800 rounded"
                    >
                      <div className="text-base shrink-0">{SYMBOL_EMOJI[sym] ?? "•"}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-bold text-gray-200">
                            {SYMBOL_LABEL[sym] ?? sym}
                          </span>
                          <span
                            className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${impactBadge(txt)}`}
                          >
                            {impactHeadline(txt)}
                          </span>
                        </div>
                        <div className="text-[11px] text-gray-400 leading-tight">
                          {txt.replace(/^[A-Z\s]+—\s*/, "")}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Basket grid */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="text-[10px] uppercase tracking-[0.2em] text-gray-500">
                  Basket Breakdown ({sortedBaskets.length})
                </div>
                <div className="text-[10px] text-gray-500">click to expand</div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                {sortedBaskets.map((b) => <BasketCard key={b.key} basket={b} />)}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
