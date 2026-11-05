"use client";

/**
 * 60 dk fiyat bandı satırı — "Risk & Pozisyon" kartı için.
 * Kaynak yöntem: day-trader-skill / trader-timemachine (MIT). DTS-03: %90 bant tüm TF/sembollerde kalibre (A).
 * Bant YÖN söylemez; aktif sinyalin TP1/SL'sinin banda göre konumunu gösterir (DTS-06: panel sinyallerinde
 * "TP1 %90 bandın dışında" zayıf olumsuz işaret — yalnız bilgi).
 */

import { useRangeBand } from "@/lib/api/timeMachine";

interface ActiveSignal {
  dir: string;
  entry: number;
  tps: number[];
  sl: number;
}

const fmt = (v: number) => (v >= 1000 ? v.toFixed(1) : v.toFixed(2));

export default function RangeBandRow({ symbol, active }: { symbol: string; active?: ActiveSignal | null }) {
  const { data, isLoading, error } = useRangeBand(symbol, "5m", 60);
  if (isLoading) return <div className="mb-3 h-10 animate-pulse rounded-xl bg-white/[0.03]" />;
  if (error || !data) return null;

  const long = active?.dir === "BUY";
  const entry = active?.entry || 0;
  const tp1 = active?.tps?.[0];
  const p5 = entry ? entry * data.rel_p5 : 0;
  const p95 = entry ? entry * data.rel_p95 : 0;
  const p25 = entry ? entry * data.rel_p25 : 0;
  const p75 = entry ? entry * data.rel_p75 : 0;
  const tpOutside = active && tp1 ? (long ? tp1 > p95 : tp1 < p5) : null;
  const slInside = active && active.sl ? active.sl >= p25 && active.sl <= p75 : null;

  return (
    <div className="mb-3 rounded-xl border border-indigo-500/15 bg-indigo-500/[0.04] px-4 py-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-indigo-300">60 dk %90 fiyat bandı</span>
        <span className="font-mono text-xs text-slate-200">
          {fmt(data.p5)} – {fmt(data.p95)} <span className="text-slate-500">(±%{(data.width_pct / 2).toFixed(2)})</span>
        </span>
      </div>
      {active && tp1 ? (
        <div className="mt-1.5 flex flex-wrap gap-3 text-[11px]">
          <span className={tpOutside ? "text-amber-300" : "text-emerald-300"}>
            TP1 {tpOutside ? "bandın dışında — 60 dk içinde nadir" : "bandın içinde"}
          </span>
          {slInside !== null && (
            <span className={slInside ? "text-amber-300" : "text-slate-400"}>
              SL {slInside ? "%50 gürültü bandında" : "gürültü bandının dışında"}
            </span>
          )}
        </div>
      ) : null}
      <p className="mt-1 text-[10px] text-slate-500">Son 60 seansın aynı saatinden; yön söylemez. {data.calibration}</p>
    </div>
  );
}
