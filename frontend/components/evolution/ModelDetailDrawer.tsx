"use client";

/**
 * Model Detay Çekmecesi — performans panosunda bir modele tıklayınca açılır.
 * Sembol bazlı WR kırılımı + BUY/SELL yön ayrımı + son sinyaller.
 * Veri: /api/learning/model-symbol-breakdown (accuracy-by-model ile aynı
 * classify_signal kuralları — iki görünüm asla çelişmez).
 */

import { AnimatePresence, motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, Clock, X } from "lucide-react";

import { useModelDetail } from "@/lib/api/evolution";
import { Badge, ProgressBar, Ring, Skeleton, cx, modelColor, timeAgo } from "./ui";

function wrColor(pct: number | null): string {
  if (pct === null) return "#64748B";
  if (pct >= 55) return "#34D399";
  if (pct >= 45) return "#FBBF24";
  return "#FB7185";
}

const OUTCOME_LABEL: Record<string, { text: string; tone: "green" | "red" | "slate" | "amber" }> = {
  completed: { text: "kazandı", tone: "green" },
  stopped: { text: "kaybetti", tone: "red" },
  flip_closed: { text: "flip (nötr)", tone: "amber" },
  expired: { text: "süresi doldu", tone: "slate" },
};

export default function ModelDetailDrawer({
  strategy,
  days,
  onClose,
}: {
  strategy: string;
  days: number;
  onClose: () => void;
}) {
  const { data, isLoading, isError } = useModelDetail(strategy, days);
  const color = modelColor(strategy);
  const symbols = Object.entries(data?.by_symbol ?? {}).sort((a, b) => b[1].total - a[1].total);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-3 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 40, opacity: 0, scale: 0.98 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: 40, opacity: 0, scale: 0.98 }}
        transition={{ type: "spring", damping: 28, stiffness: 320 }}
        className="flex max-h-[86vh] w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#0B0F17] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Başlık */}
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <span className="h-3 w-3 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
            <span className="text-sm font-semibold text-slate-100">{strategy}</span>
            <Badge tone="slate">son {days} gün</Badge>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto px-5 py-4">
          {isError && (
            <p className="rounded-xl border border-rose-400/20 bg-rose-400/[0.06] p-3 text-center text-[12px] text-rose-300">
              Detay yüklenemedi — backend çalışıyor mu?
            </p>
          )}
          {isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-3/4" />
            </div>
          )}

          {data && (
            <>
              {/* Özet şerit */}
              <div className="mb-5 flex items-center gap-5">
                <Ring pct={data.win_rate ?? 0} color={wrColor(data.win_rate)} size={96} stroke={8}>
                  <span className="text-2xl font-bold tabular-nums text-white">
                    {data.win_rate !== null ? `%${Math.round(data.win_rate)}` : "—"}
                  </span>
                </Ring>
                <div className="grid flex-1 grid-cols-2 gap-x-6 gap-y-1.5 text-[12px] sm:grid-cols-4">
                  <div><span className="block text-lg font-bold tabular-nums text-emerald-300">{data.wins}</span><span className="text-slate-500">kazanç</span></div>
                  <div><span className="block text-lg font-bold tabular-nums text-rose-300">{data.losses}</span><span className="text-slate-500">kayıp</span></div>
                  <div><span className="block text-lg font-bold tabular-nums text-amber-300">{data.flips}</span><span className="text-slate-500">flip (nötr)</span></div>
                  <div><span className="block text-lg font-bold tabular-nums text-slate-300">{data.expired}</span><span className="text-slate-500">süresi doldu</span></div>
                </div>
              </div>

              {data.total === 0 && (
                <p className="rounded-xl border border-dashed border-white/10 p-4 text-center text-[12px] text-slate-500">
                  Bu pencerede sinyal yok — gün aralığını genişletmeyi dene.
                </p>
              )}

              {/* Sembol kırılımı */}
              {symbols.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Sembol kırılımı</h4>
                  {symbols.map(([sym, s], i) => (
                    <motion.div
                      key={sym}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-3.5"
                    >
                      <div className="mb-2 flex items-baseline justify-between">
                        <span className="text-[13px] font-semibold text-slate-200">{sym}</span>
                        <span className="text-xs tabular-nums text-slate-500">
                          <span className="text-sm font-bold" style={{ color: wrColor(s.win_rate) }}>
                            {s.win_rate !== null ? `%${Math.round(s.win_rate)}` : "—"}
                          </span>{" "}
                          · {s.total} sinyal
                        </span>
                      </div>
                      <ProgressBar pct={s.win_rate ?? 0} color={wrColor(s.win_rate)} />
                      <div className="mt-2.5 flex flex-wrap gap-1.5">
                        {Object.entries(s.by_direction)
                          .sort((a, b) => b[1].total - a[1].total)
                          .map(([dir, d]) => (
                            <span
                              key={dir}
                              className={cx(
                                "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1",
                                dir === "BUY"
                                  ? "bg-emerald-400/10 text-emerald-300 ring-emerald-400/20"
                                  : dir === "SELL"
                                    ? "bg-rose-400/10 text-rose-300 ring-rose-400/20"
                                    : "bg-white/[0.06] text-slate-300 ring-white/10"
                              )}
                            >
                              {dir === "BUY" ? <ArrowUpRight size={11} /> : dir === "SELL" ? <ArrowDownRight size={11} /> : null}
                              {dir} {d.win_rate !== null ? `%${Math.round(d.win_rate)}` : "—"} ({d.wins}K/{d.losses}Z)
                            </span>
                          ))}
                        {s.flips > 0 && <Badge tone="amber">{s.flips} flip</Badge>}
                        {s.expired > 0 && <Badge tone="slate">{s.expired} süresi doldu</Badge>}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Son sinyaller */}
              {data.recent.length > 0 && (
                <div className="mt-5">
                  <h4 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    <Clock size={11} /> Son sinyaller
                  </h4>
                  <div className="space-y-0.5">
                    {data.recent.map((r, i) => {
                      const o = OUTCOME_LABEL[r.outcome] ?? { text: r.outcome, tone: "slate" as const };
                      return (
                        <div key={i} className="flex items-center justify-between rounded-lg px-2.5 py-1.5 text-[11px] odd:bg-white/[0.02]">
                          <span className="flex items-center gap-2 text-slate-300">
                            <span className={cx("font-semibold", r.direction === "BUY" ? "text-emerald-300" : "text-rose-300")}>
                              {r.direction}
                            </span>
                            {r.symbol}
                          </span>
                          <span className="flex items-center gap-2.5 text-slate-500">
                            {r.profit_pips !== null && (
                              <span className={cx("tabular-nums", r.profit_pips >= 0 ? "text-emerald-300/80" : "text-rose-300/80")}>
                                {r.profit_pips >= 0 ? "+" : ""}{r.profit_pips} pip
                              </span>
                            )}
                            <Badge tone={o.tone}>{o.text}</Badge>
                            {timeAgo(r.created_at)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
