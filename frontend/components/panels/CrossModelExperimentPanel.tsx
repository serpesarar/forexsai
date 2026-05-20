"use client";

import { useQuery } from "@tanstack/react-query";
import { crossModelApi } from "../../lib/api/crossModelExperiment";

/**
 * Cross-Model Experiment Panel
 *
 * Shows the NASDAQ-on-XAUUSD experiment: live preview + cumulative stats.
 * Read-only — the MT5 bot does NOT trade these signals.
 */
export default function CrossModelExperimentPanel() {
  const preview = useQuery({
    queryKey: ["cross-model-preview"],
    queryFn: () => crossModelApi.preview(),
    refetchInterval: 90_000,
    staleTime: 60_000,
  });

  const stats = useQuery({
    queryKey: ["cross-model-stats", 14],
    queryFn: () => crossModelApi.stats(14),
    refetchInterval: 120_000,
  });

  const info = useQuery({
    queryKey: ["cross-model-info"],
    queryFn: () => crossModelApi.info(),
    staleTime: 60 * 60 * 1000,
  });

  if (info.data && info.data.enabled === false) {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <div className="text-sm text-textSecondary">
          Cross-Model Experiment kapalı.
          <code className="ml-2 text-xs text-amber-400">CROSS_MODEL_EXPERIMENT_ENABLED=1</code> ile aktif et.
        </div>
      </div>
    );
  }

  const pv = preview.data;
  const st = stats.data;

  return (
    <div className="rounded-xl border border-purple-500/20 bg-gradient-to-br from-purple-500/[0.04] to-fuchsia-500/[0.02] p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-purple-300">
              EXPERIMENT
            </span>
            <h3 className="text-base font-bold text-white">NASDAQ ML × XAUUSD</h3>
          </div>
          <p className="mt-1 text-xs text-textSecondary">
            NDX modeli, altın grafiğine uygulanıyor. MT5 botu bu sinyallere işlem açmaz — sadece izleme.
          </p>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase text-textSecondary">Son tetik</div>
          <div className="text-xs font-mono text-white/80">
            {st?.last_tick_at ? new Date(st.last_tick_at).toLocaleTimeString() : "—"}
          </div>
          <div className="text-[10px] text-textSecondary mt-0.5">{st?.last_tick_status || ""}</div>
        </div>
      </div>

      {/* Live preview */}
      <div className="rounded-lg border border-white/5 bg-black/30 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider text-textSecondary">Canlı tahmin</span>
          {preview.isFetching && (
            <span className="text-[10px] text-purple-300">yenileniyor…</span>
          )}
        </div>
        {preview.isLoading ? (
          <div className="text-sm text-textSecondary">Yükleniyor…</div>
        ) : pv?.error ? (
          <div className="text-sm text-amber-400">Hata: {pv.error}</div>
        ) : pv ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <Stat
              label="Yön"
              value={
                <span
                  className={
                    pv.direction === "BUY"
                      ? "text-emerald-400 font-bold"
                      : pv.direction === "SELL"
                      ? "text-rose-400 font-bold"
                      : "text-textSecondary font-bold"
                  }
                >
                  {pv.direction}
                </span>
              }
            />
            <Stat label="Güven" value={`${pv.confidence?.toFixed(1) ?? "—"}%`} />
            <Stat label="Giriş" value={pv.entry_price?.toFixed(2) ?? "—"} />
            <Stat
              label="TP / SL"
              value={
                <span className="font-mono text-xs">
                  {pv.target_price?.toFixed(2) ?? "—"} /{" "}
                  <span className="text-rose-400">{pv.stop_price?.toFixed(2) ?? "—"}</span>
                </span>
              }
            />
          </div>
        ) : null}
      </div>

      {/* Stats roll-up */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <Stat label="Toplam sinyal" value={st?.total_signals ?? "—"} />
        <Stat label="Aktif" value={st?.active ?? "—"} />
        <Stat
          label="Gerçek WR"
          value={st?.real_win_rate_pct !== undefined && st?.real_win_rate_pct !== null
            ? `${st.real_win_rate_pct.toFixed(1)}%`
            : "—"}
        />
        <Stat
          label="Gerçek TP / SL"
          value={`${st?.real_wins ?? 0} / ${st?.sl_hits ?? 0}`}
        />
        <Stat
          label="Net pip"
          value={
            <span
              className={
                (st?.net_pips ?? 0) > 0
                  ? "text-emerald-400 font-bold"
                  : (st?.net_pips ?? 0) < 0
                  ? "text-rose-400 font-bold"
                  : "text-white"
              }
            >
              {st?.net_pips !== undefined ? (st.net_pips > 0 ? "+" : "") + st.net_pips : "—"}
            </span>
          }
        />
      </div>

      {/* Recent signals */}
      {st?.recent_signals && st.recent_signals.length > 0 && (
        <div className="rounded-lg border border-white/5 bg-black/20 p-3">
          <div className="text-[10px] uppercase tracking-wider text-textSecondary mb-2">
            Son sinyaller
          </div>
          <div className="space-y-1">
            {st.recent_signals.slice(0, 6).map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between text-xs font-mono"
              >
                <span className="text-textSecondary">
                  {new Date(s.created_at).toLocaleString("tr-TR", {
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                <span
                  className={
                    s.direction === "BUY" ? "text-emerald-400" : "text-rose-400"
                  }
                >
                  {s.direction}
                </span>
                <span className="text-white/70">{s.confidence?.toFixed(0)}%</span>
                <span
                  className={
                    s.status === "completed"
                      ? "text-emerald-400"
                      : s.status === "stopped"
                      ? "text-rose-400"
                      : "text-amber-400"
                  }
                >
                  {s.status}
                </span>
                <span className="text-[10px] text-textSecondary truncate max-w-[140px]">
                  {s.resolution || ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-textSecondary">
        {label}
      </div>
      <div className="text-lg text-white">{value}</div>
    </div>
  );
}
