"use client";

import { Activity, RefreshCw } from "lucide-react";
import { useLifecycleResults, type LifecycleSignalRow } from "../../lib/api/learning";

interface Props {
  symbol: string;
  hours?: number;
}

const TP_REASONS = new Set(["tp4_hit", "tp1_3_hit_then_sl", "window_resolve_positive"]);
const SL_REASONS = new Set(["sl_hit", "window_resolve_negative"]);

function reasonLabel(reason: string | null): string {
  if (!reason) return "—";
  return reason.replace(/_/g, " ");
}

function reasonClass(reason: string | null): string {
  if (!reason) return "text-slate-400";
  if (TP_REASONS.has(reason)) return "text-emerald-400";
  if (SL_REASONS.has(reason)) return "text-rose-400";
  if (reason === "direction_flip") return "text-amber-400";
  return "text-slate-300";
}

function statusClass(status: string | null): string {
  if (status === "completed") return "text-emerald-400";
  if (status === "stopped") return "text-rose-400";
  if (status === "active") return "text-sky-400";
  return "text-slate-400";
}

function fmtPrice(v: number | null): string {
  if (v == null) return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function fmtAge(h: number | null): string {
  if (h == null) return "—";
  if (h < 1) return `${Math.round(h * 60)}d`;
  if (h < 48) return `${h.toFixed(1)}s`;
  return `${(h / 24).toFixed(1)}g`;
}

function Row({ r }: { r: LifecycleSignalRow }) {
  return (
    <tr className="border-b border-slate-800/60 hover:bg-slate-800/30">
      <td className="px-2 py-1.5 font-mono text-[11px] text-slate-400">{r.model_type ?? "—"}</td>
      <td className={`px-2 py-1.5 font-semibold ${r.direction === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
        {r.direction ?? "—"}
      </td>
      <td className={`px-2 py-1.5 ${statusClass(r.status)}`}>{r.status ?? "—"}</td>
      <td className={`px-2 py-1.5 capitalize ${reasonClass(r.resolution_reason)}`}>
        {reasonLabel(r.resolution_reason)}
      </td>
      <td className="px-2 py-1.5 text-right font-mono text-slate-300">{fmtPrice(r.entry_price)}</td>
      <td className="px-2 py-1.5 text-right font-mono text-slate-300">{fmtPrice(r.exit_price)}</td>
      <td className="px-2 py-1.5 text-right font-mono text-emerald-400">
        {r.profit_pips != null ? r.profit_pips.toFixed(1) : "—"}
      </td>
      <td className="px-2 py-1.5 text-right font-mono text-slate-400">{fmtAge(r.age_hours)}</td>
    </tr>
  );
}

export function LifecycleResultsTable({ symbol, hours = 48 }: Props) {
  const { data, isLoading, isFetching, error } = useLifecycleResults(symbol, hours, 25);

  if (isLoading) {
    return <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">Yükleniyor…</div>;
  }
  if (error || data?.error) {
    return (
      <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-300">
        Lifecycle verisi alınamadı{data?.error ? `: ${data.error}` : ""}
      </div>
    );
  }
  if (!data) return null;

  const realPct =
    data.resolved_count > 0 ? Math.round((data.real_tp_sl_resolved / data.resolved_count) * 100) : 0;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2.5">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Activity className="h-4 w-4 text-sky-400" />
          Canlı Lifecycle Sonuçları
          <span className="text-xs font-normal text-slate-500">son {data.window_hours}s</span>
        </div>
        {isFetching && <RefreshCw className="h-3.5 w-3.5 animate-spin text-slate-500" />}
      </div>

      {/* Stat strip */}
      <div className="grid grid-cols-2 gap-px bg-slate-800 sm:grid-cols-4">
        <Stat label="Aktif (bekleyen)" value={data.active_count} tone="sky" />
        <Stat label="Çözülen" value={data.resolved_count} tone="slate" />
        <Stat label="Gerçek TP/SL" value={`${data.real_tp_sl_resolved} (%${realPct})`} tone="emerald" />
        <Stat label="Direction flip" value={data.direction_flip_resolved} tone="amber" />
      </div>

      {/* Reason distribution */}
      {Object.keys(data.reason_counts).length > 0 && (
        <div className="flex flex-wrap gap-1.5 border-t border-slate-800 px-4 py-2">
          {Object.entries(data.reason_counts).map(([reason, count]) => (
            <span
              key={reason}
              className={`rounded px-1.5 py-0.5 text-[11px] font-medium capitalize ${reasonClass(reason)} bg-slate-800/60`}
            >
              {reasonLabel(reason)}: {count}
            </span>
          ))}
        </div>
      )}

      {/* Oldest active backlog */}
      {data.oldest_active.length > 0 && (
        <TableBlock title={`En eski aktif sinyaller (${data.active_count})`} rows={data.oldest_active} />
      )}

      {/* Recently resolved */}
      <TableBlock title="Son çözülenler" rows={data.recent_resolved} />
    </div>
  );
}

function TableBlock({ title, rows }: { title: string; rows: LifecycleSignalRow[] }) {
  return (
    <div className="border-t border-slate-800">
      <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</div>
      <div className="max-h-72 overflow-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-slate-900/95 text-[10px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-2 py-1.5 text-left">Model</th>
              <th className="px-2 py-1.5 text-left">Yön</th>
              <th className="px-2 py-1.5 text-left">Durum</th>
              <th className="px-2 py-1.5 text-left">Sebep</th>
              <th className="px-2 py-1.5 text-right">Giriş</th>
              <th className="px-2 py-1.5 text-right">Çıkış</th>
              <th className="px-2 py-1.5 text-right">Pip</th>
              <th className="px-2 py-1.5 text-right">Yaş</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-2 py-4 text-center text-slate-500">
                  Kayıt yok
                </td>
              </tr>
            ) : (
              rows.map((r) => <Row key={r.id} r={r} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const TONE: Record<string, string> = {
  sky: "text-sky-400",
  emerald: "text-emerald-400",
  amber: "text-amber-400",
  slate: "text-slate-200",
};

function Stat({ label, value, tone }: { label: string; value: number | string; tone: string }) {
  return (
    <div className="bg-slate-900/80 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-lg font-bold ${TONE[tone] ?? "text-slate-200"}`}>{value}</div>
    </div>
  );
}

export default LifecycleResultsTable;
