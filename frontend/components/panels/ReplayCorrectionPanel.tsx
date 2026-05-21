"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { replayApi, type ReplayScope } from "../../lib/api/replay";

/**
 * Replay Correction Panel
 *
 * Surfaces the 2026-05-21 historical TP/SL replay operation: dashboard
 * (original) win-rates vs the honest, 1m-bar-replayed corrected win-rates.
 * Read-only — prediction_logs is never touched; this reads
 * prediction_replay_corrections.
 */

const SYMBOL_COLORS: Record<string, string> = {
  "XAUUSD": "text-amber-300",
  "NDX.INDX": "text-blue-300",
  "GDAXI.INDX": "text-purple-300",
  "USOIL.FOREX": "text-emerald-300",
};

function wrColor(wr: number | null): string {
  if (wr == null) return "text-white/40";
  if (wr >= 60) return "text-green-400";
  if (wr >= 50) return "text-yellow-400";
  return "text-red-400";
}

function fmtPct(v: number | null): string {
  return v == null ? "—" : `${v.toFixed(1)}%`;
}

interface SymbolAgg {
  symbol: string;
  n: number;
  oc: number; os: number; cc: number; cs: number;
  flipped: number;
  pnl: number;
}

export default function ReplayCorrectionPanel() {
  const [sortBy, setSortBy] = useState<"impact" | "drop" | "n">("impact");

  const report = useQuery({
    queryKey: ["replay-report", 120],
    queryFn: () => replayApi.report(120),
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
  });

  const { perSymbol, scopes } = useMemo(() => {
    const sc = report.data?.scopes ?? [];
    const bySym = new Map<string, SymbolAgg>();
    for (const s of sc) {
      const a = bySym.get(s.symbol) ?? {
        symbol: s.symbol, n: 0, oc: 0, os: 0, cc: 0, cs: 0, flipped: 0, pnl: 0,
      };
      a.n += s.n;
      a.oc += s.orig_completed; a.os += s.orig_stopped;
      a.cc += s.corr_completed; a.cs += s.corr_stopped;
      a.flipped += s.flipped;
      a.pnl += s.pnl_delta_pips_total;
      bySym.set(s.symbol, a);
    }
    const sorted = [...sc].sort((a, b) => {
      if (sortBy === "n") return b.n - a.n;
      if (sortBy === "drop") {
        const da = (a.orig_win_rate ?? 0) - (a.corr_win_rate ?? 0);
        const db = (b.orig_win_rate ?? 0) - (b.corr_win_rate ?? 0);
        return db - da;
      }
      return a.pnl_delta_pips_total - b.pnl_delta_pips_total; // most negative first
    });
    return { perSymbol: [...bySym.values()].sort((a, b) => b.n - a.n), scopes: sorted };
  }, [report.data, sortBy]);

  if (report.isLoading) {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 min-h-[200px] flex items-center justify-center">
        <span className="text-sm text-white/30">Replay raporu yükleniyor…</span>
      </div>
    );
  }

  if (report.isError) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/[0.04] p-5">
        <div className="text-sm text-red-300">
          Replay raporu yüklenemedi: {String((report.error as Error)?.message ?? "")}
        </div>
      </div>
    );
  }

  if (!scopes.length) {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
        <div className="text-sm text-white/40">
          Henüz replay düzeltmesi yok. <code className="text-amber-400">/api/replay/run</code> çalıştırılmalı.
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/[0.04] to-sky-500/[0.02] p-5 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-cyan-300">
              GROUND TRUTH
            </span>
            <h3 className="text-base font-bold text-white">Düzeltilmiş Performans</h3>
          </div>
          <p className="mt-1 text-xs text-textSecondary">
            Geçmiş sinyaller 1 dakikalık MT5 mumlarına karşı yeniden oynatıldı.
            Panel (orijinal) win-rate vs gerçek win-rate. {report.data?.rows.toLocaleString()} kayıt.
          </p>
        </div>
      </div>

      {/* Per-symbol summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        {perSymbol.map((a) => {
          const owr = a.oc + a.os > 0 ? (100 * a.oc) / (a.oc + a.os) : null;
          const cwr = a.cc + a.cs > 0 ? (100 * a.cc) / (a.cc + a.cs) : null;
          const drop = owr != null && cwr != null ? owr - cwr : 0;
          return (
            <div key={a.symbol} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
              <div className={`text-xs font-bold ${SYMBOL_COLORS[a.symbol] ?? "text-white"}`}>
                {a.symbol}
              </div>
              <div className="mt-1.5 flex items-baseline gap-1.5">
                <span className="text-[11px] text-white/40 line-through">{fmtPct(owr)}</span>
                <span className="text-white/30">→</span>
                <span className={`text-lg font-bold ${wrColor(cwr)}`}>{fmtPct(cwr)}</span>
              </div>
              <div className="mt-0.5 text-[10px] text-red-400/80">
                {drop > 0 ? `−${drop.toFixed(1)} puan şişirme` : "doğru"}
              </div>
              <div className="mt-1 text-[10px] text-white/35">
                {a.n.toLocaleString()} sinyal · {a.flipped.toLocaleString()} verdict değişti
              </div>
            </div>
          );
        })}
      </div>

      {/* Sort control */}
      <div className="flex items-center gap-2 text-[11px]">
        <span className="text-white/30">Sırala:</span>
        {([
          ["impact", "Etki (pip)"],
          ["drop", "WR düşüşü"],
          ["n", "Hacim"],
        ] as const).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setSortBy(k)}
            className={`rounded px-2 py-0.5 transition-colors ${
              sortBy === k
                ? "bg-cyan-500/20 text-cyan-300"
                : "bg-white/[0.03] text-white/40 hover:text-white/60"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Scope table */}
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-left text-white/30 border-b border-white/5">
              <th className="py-1.5 pr-2 font-medium">Sembol</th>
              <th className="py-1.5 px-2 font-medium">Model</th>
              <th className="py-1.5 px-2 font-medium">Yön</th>
              <th className="py-1.5 px-2 font-medium text-right">n</th>
              <th className="py-1.5 px-2 font-medium text-right">Panel WR</th>
              <th className="py-1.5 px-2 font-medium text-right">Gerçek WR</th>
              <th className="py-1.5 px-2 font-medium text-right">Flip %</th>
              <th className="py-1.5 pl-2 font-medium text-right">pip Δ</th>
            </tr>
          </thead>
          <tbody>
            {scopes.slice(0, 40).map((s: ReplayScope, i) => (
              <tr key={`${s.symbol}-${s.model_type}-${s.direction}-${i}`}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                <td className={`py-1.5 pr-2 font-medium ${SYMBOL_COLORS[s.symbol] ?? "text-white"}`}>
                  {s.symbol.replace(".INDX", "").replace(".FOREX", "")}
                </td>
                <td className="py-1.5 px-2 text-white/60">{s.model_type ?? "—"}</td>
                <td className={`py-1.5 px-2 font-medium ${
                  s.direction === "BUY" ? "text-green-400/80" : "text-red-400/80"
                }`}>
                  {s.direction ?? "—"}
                </td>
                <td className="py-1.5 px-2 text-right text-white/50">{s.n}</td>
                <td className="py-1.5 px-2 text-right text-white/40 line-through">
                  {fmtPct(s.orig_win_rate)}
                </td>
                <td className={`py-1.5 px-2 text-right font-bold ${wrColor(s.corr_win_rate)}`}>
                  {fmtPct(s.corr_win_rate)}
                </td>
                <td className="py-1.5 px-2 text-right text-white/50">
                  {s.flip_rate_pct.toFixed(0)}%
                </td>
                <td className={`py-1.5 pl-2 text-right font-medium ${
                  s.pnl_delta_pips_total < 0 ? "text-red-400" : "text-green-400"
                }`}>
                  {s.pnl_delta_pips_total > 0 ? "+" : ""}
                  {Math.round(s.pnl_delta_pips_total).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {scopes.length > 40 && (
          <div className="mt-2 text-[10px] text-white/25">
            İlk 40 scope gösteriliyor ({scopes.length} toplam).
          </div>
        )}
      </div>
    </div>
  );
}
