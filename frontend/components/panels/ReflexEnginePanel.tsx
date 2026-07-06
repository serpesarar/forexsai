"use client";

import { Activity, RefreshCw, ShieldCheck } from "lucide-react";
import { useReflexPerformance, useReflexSignals, ReflexSignal } from "../../lib/api/reflexEngine";

// NDX-only engine (the only validated NDX edge: momentum-continuation + 15m time-stop).
const REFLEX_SYMBOL = "NDX.INDX";

function statusClass(s: string): string {
  if (s === "closed_win") return "text-emerald-400";
  if (s === "closed_loss") return "text-rose-400";
  if (s === "active") return "text-sky-400";
  return "text-slate-400";
}
function statusLabel(s: string): string {
  return { active: "AÇIK", closed_win: "KAZANÇ", closed_loss: "KAYIP", closed_flat: "NÖTR", error: "HATA" }[s] || s;
}
function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}
function pct(x: number | null): string {
  return x == null ? "—" : `${(x * 100).toFixed(0)}%`;
}
function rColor(x: number | null): string {
  if (x == null) return "text-slate-400";
  return x > 0 ? "text-emerald-400" : x < 0 ? "text-rose-400" : "text-slate-400";
}

function Stat({ label, value, tone = "slate" }: { label: string; value: string; tone?: string }) {
  const toneMap: Record<string, string> = {
    sky: "text-sky-400", emerald: "text-emerald-400", amber: "text-amber-400",
    rose: "text-rose-400", slate: "text-slate-200",
  };
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`font-mono text-lg font-black ${toneMap[tone]}`}>{value}</div>
    </div>
  );
}

export default function ReflexEnginePanel({ symbol }: { symbol: string }) {
  // Engine is NDX-only; on other symbols show a short note.
  if (symbol !== REFLEX_SYMBOL) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">
        Reflex Engine yalnızca NASDAQ (NDX) için çalışır — bu enstrümanda kanıtlanmış tek edge budur.
      </div>
    );
  }

  const perf = useReflexPerformance(REFLEX_SYMBOL, 30);
  const sig = useReflexSignals(REFLEX_SYMBOL, 7, 50);
  const p = perf.data;
  const signals: ReflexSignal[] = sig.data?.signals ?? [];
  const mode = signals[0]?.mode ?? "shadow";

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/50">
      {/* header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-sky-400" />
          <span className="text-sm font-semibold text-slate-200">Reflex Engine</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
            momentum · 15dk time-stop
          </span>
          <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
            mode === "live" ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"}`}>
            {mode === "live" ? "CANLI" : "GÖZLEM"}
          </span>
        </div>
        {(perf.isFetching || sig.isFetching) && <RefreshCw className="h-3.5 w-3.5 animate-spin text-slate-500" />}
      </div>

      {/* honesty note */}
      <div className="flex items-start gap-2 border-b border-slate-800/60 bg-slate-950/40 px-3 py-1.5 text-[11px] text-slate-500">
        <ShieldCheck className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500/70" />
        <span>Yön tahmini yok — momentum sürüklenmesini asimetrik ödemeyle yakalar. WR ~%45, EV pozitif. Sızıntısız (leak-free) doğrulandı.</span>
      </div>

      {/* performance strip */}
      {perf.isLoading ? (
        <div className="p-4 text-sm text-slate-400">Yükleniyor…</div>
      ) : perf.isError ? (
        <div className="m-3 rounded border border-rose-900/50 bg-rose-950/20 p-3 text-sm text-rose-300">
          Performans yüklenemedi.
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2 p-3 sm:grid-cols-6">
          <Stat label="Win rate" value={pct(p?.win_rate ?? null)} tone={(p?.win_rate ?? 0) >= 0.45 ? "emerald" : "amber"} />
          <Stat label="EV (R)" value={p?.ev_r != null ? `${p.ev_r >= 0 ? "+" : ""}${p.ev_r.toFixed(3)}` : "—"}
                tone={(p?.ev_r ?? 0) > 0 ? "emerald" : "rose"} />
          <Stat label="Profit factor" value={p?.profit_factor != null ? p.profit_factor.toFixed(2) : "—"}
                tone={(p?.profit_factor ?? 0) >= 1 ? "emerald" : "rose"} />
          <Stat label="Toplam R" value={p?.total_r != null ? `${p.total_r >= 0 ? "+" : ""}${p.total_r.toFixed(1)}` : "—"}
                tone={(p?.total_r ?? 0) >= 0 ? "emerald" : "rose"} />
          <Stat label="Max DD (R)" value={p?.max_drawdown_r != null ? p.max_drawdown_r.toFixed(1) : "—"} tone="amber" />
          <Stat label="Açık / Çözülen" value={`${p?.active ?? 0} / ${p?.n ?? 0}`} tone="sky" />
        </div>
      )}

      {/* signals table */}
      <div className="border-t border-slate-800">
        {sig.isLoading ? (
          <div className="p-4 text-sm text-slate-400">Yükleniyor…</div>
        ) : sig.isError ? (
          <div className="m-3 rounded border border-rose-900/50 bg-rose-950/20 p-3 text-sm text-rose-300">
            Sinyaller yüklenemedi.
          </div>
        ) : (
          <div className="max-h-72 overflow-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-900/95 text-[10px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-2 py-1.5 text-left">Saat</th>
                  <th className="px-2 py-1.5 text-left">Yön</th>
                  <th className="px-2 py-1.5 text-left">Rejim</th>
                  <th className="px-2 py-1.5 text-right">Giriş</th>
                  <th className="px-2 py-1.5 text-right">Çıkış</th>
                  <th className="px-2 py-1.5 text-center">Durum</th>
                  <th className="px-2 py-1.5 text-right">R</th>
                </tr>
              </thead>
              <tbody>
                {signals.length === 0 ? (
                  <tr><td colSpan={7} className="px-2 py-4 text-center text-slate-500">Kayıt yok</td></tr>
                ) : (
                  signals.map((s) => (
                    <tr key={s.id} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                      <td className="px-2 py-1.5 text-slate-400">{fmtTime(s.entry_time || s.event_time)}</td>
                      <td className={`px-2 py-1.5 font-semibold ${s.direction === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
                        {s.direction}
                      </td>
                      <td className="px-2 py-1.5 text-slate-400">{s.regime ?? "—"}</td>
                      <td className="px-2 py-1.5 text-right font-mono text-slate-300">
                        {s.entry_price != null ? s.entry_price.toFixed(1) : "—"}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono text-slate-300">
                        {s.exit_price != null ? s.exit_price.toFixed(1) : "—"}
                      </td>
                      <td className={`px-2 py-1.5 text-center font-semibold ${statusClass(s.status)}`}>
                        {statusLabel(s.status)}
                      </td>
                      <td className={`px-2 py-1.5 text-right font-mono font-bold ${rColor(s.r_multiple)}`}>
                        {s.r_multiple != null ? `${s.r_multiple >= 0 ? "+" : ""}${s.r_multiple.toFixed(2)}` : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
