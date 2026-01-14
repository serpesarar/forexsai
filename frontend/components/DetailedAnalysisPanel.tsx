"use client";

import { useState } from "react";
import {
  Brain,
  RefreshCw,
  AlertTriangle,
  ShieldAlert,
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Newspaper,
  Globe,
  Activity,
} from "lucide-react";
import { useDetailedAIAnalysis } from "../lib/api/detailedAiAnalysis";

type Props = {
  symbol: string;
  symbolLabel: string;
};

function DecisionBadge({ decision }: { decision: string }) {
  const config =
    {
      BUY: { bg: "bg-success/20", text: "text-success", icon: TrendingUp, label: "ALIŞ" },
      SELL: { bg: "bg-danger/20", text: "text-danger", icon: TrendingDown, label: "SATIŞ" },
      HOLD: { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, label: "BEKLE" },
    }[decision] || { bg: "bg-white/10", text: "text-textSecondary", icon: Minus, label: decision };

  const Icon = config.icon;
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}>
      <Icon className={`w-4 h-4 ${config.text}`} />
      <span className={`text-sm font-semibold ${config.text}`}>{config.label}</span>
    </div>
  );
}

function fmtNum(v: any, digits = 2) {
  const n = typeof v === "number" ? v : v == null ? null : Number(v);
  if (n == null || Number.isNaN(n)) return "-";
  return n.toLocaleString("tr-TR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtPct(v: any, digits = 2) {
  const n = typeof v === "number" ? v : v == null ? null : Number(v);
  if (n == null || Number.isNaN(n)) return "-";
  return `${n.toFixed(digits)}%`;
}

function mlLabel(direction: string) {
  if (!direction) return "-";
  const d = String(direction).toUpperCase();
  if (d === "BUY") return "ALIŞ";
  if (d === "SELL") return "SATIŞ";
  if (d === "HOLD") return "BEKLE";
  return d;
}

export default function DetailedAnalysisPanel({ symbol, symbolLabel }: Props) {
  const { data, isLoading, isFetching, error, refetch } = useDetailedAIAnalysis(symbol);
  const [showContext, setShowContext] = useState(false);

  const analysis = (data?.analysis || {}) as any;
  const context = (data?.context || {}) as any;
  const ml = (context?.ml_prediction || {}) as any;

  const decision = analysis.final_decision || "HOLD";
  const confidence = analysis.confidence;

  const keyLevels = analysis.key_levels || {};
  const marketRegime = analysis.market_regime || {};
  const macroView = analysis.macro_view || {};
  const newsImpact = analysis.news_impact || {};
  const rm = analysis.risk_management || {};
  const redFlags = Array.isArray(analysis.red_flags) ? analysis.red_flags : [];
  const thesis = Array.isArray(analysis.thesis) ? analysis.thesis : [];

  const emaD = keyLevels.ema_distances_pct || {};
  const ns = keyLevels.nearest_support || {};
  const nr = keyLevels.nearest_resistance || {};

  return (
    <div className="glass-card p-8 space-y-6 rounded-2xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/30 to-sky-500/30">
            <Brain className="h-6 w-6 text-sky-400" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-textSecondary">DETAYLI ANALİZ</p>
            <h3 className="text-xl font-bold">{symbolLabel}</h3>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="p-3 rounded-xl hover:bg-white/10 transition"
            disabled={isFetching}
          >
            <RefreshCw className={`w-5 h-5 ${isFetching ? "animate-spin text-sky-400" : "text-textSecondary"}`} />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="skeleton h-12 w-full rounded-xl" />
          <div className="skeleton h-24 w-full rounded-xl" />
          <div className="skeleton h-28 w-full rounded-xl" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 bg-danger/10 rounded-xl text-danger">
          <AlertTriangle className="w-5 h-5" />
          <span className="text-sm">Detaylı analiz alınamadı</span>
        </div>
      ) : data ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white/5 rounded-2xl p-5 border border-white/5">
            <div className="flex flex-wrap items-center gap-3">
              <DecisionBadge decision={decision} />
              <div className="text-sm text-textSecondary">
                <span className="font-medium">Claude Güven:</span> {typeof confidence === "number" ? `${confidence.toFixed(0)}%` : "-"}
              </div>

              <div className="hidden sm:block h-6 w-px bg-white/10" />

              <div className="text-sm text-textSecondary">
                <span className="font-medium">ML:</span> {mlLabel(ml.direction)}
                <span className="text-textSecondary"> · </span>
                <span className="font-medium">Güven:</span> {typeof ml.confidence === "number" ? `${Number(ml.confidence).toFixed(0)}%` : "-"}
              </div>
            </div>
            <div className="text-xs text-textSecondary">
              {analysis.model_used ? String(analysis.model_used) : ""}
            </div>
          </div>

          {analysis.summary && (
            <div className="bg-white/5 rounded-2xl p-5 border border-white/5 text-sm text-textSecondary leading-relaxed">
              {String(analysis.summary)}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-accent" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">Seviyeler & Uzaklıklar</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">En Yakın Destek</p>
                  <p className="font-mono font-semibold">{fmtNum(ns.price, 2)}</p>
                  <p className="text-[11px] text-textSecondary">Uzaklık: {fmtPct(ns.distance_pct, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">En Yakın Direnç</p>
                  <p className="font-mono font-semibold">{fmtNum(nr.price, 2)}</p>
                  <p className="text-[11px] text-textSecondary">Uzaklık: {fmtPct(nr.distance_pct, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">EMA20 Uzaklık</p>
                  <p className="font-mono font-semibold">{fmtPct(emaD.ema20, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">EMA50 / EMA200</p>
                  <p className="font-mono font-semibold">{fmtPct(emaD.ema50, 2)} / {fmtPct(emaD.ema200, 2)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-cyan-400" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">Piyasa Rejimi</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">Trend</p>
                  <p className="font-semibold">{marketRegime.trend ? String(marketRegime.trend) : "-"}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">Volatilite</p>
                  <p className="font-semibold">{marketRegime.volatility ? String(marketRegime.volatility) : "-"}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5 col-span-2">
                  <p className="text-[10px] text-textSecondary">Hacim Teyidi</p>
                  <p className="font-semibold">{marketRegime.volume_confirmation ? String(marketRegime.volume_confirmation) : "-"}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-emerald-400" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">Makro Proxy</p>
              </div>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">DXY</p>
                  <p className="font-mono font-semibold">{fmtNum(macroView.dxy?.price, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">VIX</p>
                  <p className="font-mono font-semibold">{fmtNum(macroView.vix?.price, 2)}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <p className="text-[10px] text-textSecondary">USDTRY</p>
                  <p className="font-mono font-semibold">{fmtNum(macroView.usdtry?.price, 4)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
              <div className="flex items-center gap-2 mb-3">
                <Newspaper className="w-4 h-4 text-amber-400" />
                <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">Haber Etkisi</p>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="text-textSecondary">Başlık sayısı</div>
                <div className="font-mono font-semibold">{typeof newsImpact.headline_count === "number" ? newsImpact.headline_count : "-"}</div>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <div className="text-textSecondary">Tone</div>
                <div className="font-semibold">{newsImpact.tone ? String(newsImpact.tone) : "-"}</div>
              </div>
              {Array.isArray(newsImpact.notes) && newsImpact.notes.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {newsImpact.notes.slice(0, 3).map((n: any, i: number) => (
                    <li key={i} className="text-xs text-textSecondary">
                      {String(n)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="bg-white/5 rounded-2xl p-5 border border-white/5">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-accent" />
              <p className="text-xs font-semibold uppercase tracking-wider text-textSecondary">Risk Yönetimi</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-textSecondary">Entry</p>
                <p className="font-mono font-semibold">{fmtNum(rm.recommended_entry, 2)}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-success">TP</p>
                <p className="font-mono font-semibold text-success">{fmtNum(rm.recommended_tp, 2)}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-danger">SL</p>
                <p className="font-mono font-semibold text-danger">{fmtNum(rm.recommended_sl, 2)}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-center">
                <p className="text-[10px] text-textSecondary">Boyut</p>
                <p className="font-semibold">{rm.position_size ? String(rm.position_size) : "-"}</p>
              </div>
            </div>
            {rm.invalidation && (
              <div className="mt-3 text-xs text-textSecondary leading-relaxed">
                <span className="font-semibold">Invalidation:</span> {String(rm.invalidation)}
              </div>
            )}
          </div>

          {(thesis.length > 0 || redFlags.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-success/5 rounded-2xl p-5 border border-success/10">
                <div className="flex items-center gap-2 mb-3">
                  <ShieldAlert className="w-4 h-4 text-success" />
                  <p className="text-xs font-semibold uppercase tracking-wider text-success">Tez</p>
                </div>
                <ul className="space-y-1">
                  {thesis.slice(0, 6).map((t: any, i: number) => (
                    <li key={i} className="text-xs text-textSecondary">{String(t)}</li>
                  ))}
                </ul>
              </div>

              <div className="bg-danger/5 rounded-2xl p-5 border border-danger/10">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-danger" />
                  <p className="text-xs font-semibold uppercase tracking-wider text-danger">Red Flags</p>
                </div>
                <ul className="space-y-1">
                  {redFlags.slice(0, 6).map((r: any, i: number) => (
                    <li key={i} className="text-xs text-textSecondary">{String(r)}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-[10px] text-textSecondary pt-2 border-t border-white/5">
            <button
              onClick={() => setShowContext(!showContext)}
              className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition text-xs"
            >
              {showContext ? "Context Gizle" : "Context Göster"}
            </button>
            <span>
              {analysis.timestamp ? new Date(String(analysis.timestamp)).toLocaleTimeString("tr-TR") : ""}
            </span>
          </div>

          {showContext && (
            <div className="p-3 bg-white/5 rounded-xl text-xs text-textSecondary leading-relaxed max-h-64 overflow-auto">
              <pre className="whitespace-pre-wrap break-words">{JSON.stringify(context, null, 2)}</pre>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
