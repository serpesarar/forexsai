"use client";

/**
 * Mum Benzerlik Paneli — son N mumu geçmişteki görsel olarak en benzer N mumlarla otomatik eşleştirir ve
 * eşlerin SONRASINDA ne olduğunu gösterir. Benzerlik = oto-ölçekli grafikte her mumun açılış/yüksek/düşük/kapanış
 * konumu (gövde + fitil), fiyat düzeyinden ve hareketin yüzdesinden bağımsız.
 * Dürüstlük: geriye-dönük karne (reliability) her zaman yanında gösterilir; yön isabeti tabandan farksızdır.
 */

import { memo, useMemo, useState } from "react";
import { AlertTriangle, Loader2, ScanSearch } from "lucide-react";

import {
  type HorizonSummary,
  type NormCandle,
  type Reliability,
  type SimilarityMatch,
  useCandleSimilarity,
} from "@/lib/api/candleSimilarity";

const SYMBOLS = [
  { key: "NDX", label: "NASDAQ 100" },
  { key: "DAX", label: "DAX 40" },
  { key: "XAUUSD", label: "Altın" },
  { key: "USOIL", label: "Petrol" },
];
const TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h"];
const WINDOWS = [20, 30, 50, 75, 100, 150];
const TF_LABEL: Record<string, string> = { "5m": "5 dk", "15m": "15 dk", "30m": "30 dk", "1h": "1 saat", "4h": "4 saat" };
const TF_MIN: Record<string, number> = { "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240 };
const UP = "#22c55e";
const DOWN = "#ef4444";

function fmtPct(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleString("tr-TR", { year: "2-digit", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "UTC" });
}

function horizonLabel(bars: number, tf: string): string {
  const m = bars * TF_MIN[tf];
  return m >= 1440 ? `${(m / 1440).toFixed(m % 1440 ? 1 : 0)} gün` : m >= 60 ? `${(m / 60).toFixed(m % 60 ? 1 : 0)} sa` : `${m} dk`;
}

// ─────────────────────────────── mum çizimi ───────────────────────────────
interface CandleChartProps {
  window: NormCandle[];
  future?: NormCandle[];
  height?: number;
  compact?: boolean;
}

const CandleChart = memo(function CandleChart({ window, future = [], height = 220, compact = false }: CandleChartProps) {
  const all = [...window, ...future];
  const lo = Math.min(...all.map((c) => c[2]));
  const hi = Math.max(...all.map((c) => c[1]));
  const W = 1000;
  const slot = W / Math.max(all.length, 1);
  const pad = compact ? 2 : 8;
  const y = (v: number) => pad + (1 - (v - lo) / (hi - lo || 1)) * (height - 2 * pad);
  const body = Math.max(slot * 0.62, 1);
  return (
    <svg viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none" className="w-full" style={{ height }}>
      {future.length > 0 && (
        <>
          <rect x={window.length * slot} y={0} width={future.length * slot} height={height} fill="rgba(148,163,184,0.07)" />
          <line x1={window.length * slot} x2={window.length * slot} y1={0} y2={height} stroke="#94a3b8" strokeDasharray="6 6" strokeWidth={2} />
        </>
      )}
      {all.map(([o, h, l, c], i) => {
        const color = c >= o ? UP : DOWN;
        const x = i * slot + slot / 2;
        const isFuture = i >= window.length;
        return (
          <g key={i} opacity={isFuture ? 0.55 : 1}>
            <line x1={x} x2={x} y1={y(h)} y2={y(l)} stroke={color} strokeWidth={compact ? 1.5 : 2} vectorEffect="non-scaling-stroke" />
            <rect x={x - body / 2} y={Math.min(y(o), y(c))} width={body} height={Math.max(Math.abs(y(o) - y(c)), 1)} fill={color} />
          </g>
        );
      })}
    </svg>
  );
});

// ─────────────────────────────── alt bileşenler ───────────────────────────────
function HorizonTable({ horizons, bars, tf, price }: { horizons: Record<string, HorizonSummary>; bars: number[]; tf: string; price?: number }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead className="text-slate-400">
          <tr className="border-b border-white/10">
            <th className="py-2 text-left font-medium">Sonraki</th>
            <th className="text-right font-medium">Eşler yukarı</th>
            <th className="text-right font-medium">Taban yukarı</th>
            <th className="text-right font-medium">Eş medyan</th>
            <th className="text-right font-medium">≈ puan</th>
            <th className="text-right font-medium">Tipik hareket (saat)</th>
            <th className="text-right font-medium">p</th>
          </tr>
        </thead>
        <tbody>
          {bars.map((b) => {
            const h = horizons[String(b)];
            if (!h) return null;
            const sig = (h.p_value_vs_base ?? 1) < 0.05;
            return (
              <tr key={b} className="border-b border-white/5 text-slate-200">
                <td className="py-2">{b} mum <span className="text-slate-500">({horizonLabel(b, tf)})</span></td>
                <td className={`text-right font-semibold ${(h.up_pct ?? 50) >= 50 ? "text-green-400" : "text-red-400"}`}>%{h.up_pct?.toFixed(0)}</td>
                <td className="text-right text-slate-400">%{h.base_up_pct.toFixed(0)}</td>
                <td className="text-right">{fmtPct(h.median_pct)}</td>
                <td className="text-right text-slate-300">{h.median_points !== null && price ? h.median_points.toFixed(price > 1000 ? 0 : 2) : "—"}</td>
                <td className="text-right text-amber-300">±{(h.hour_median_abs_pct ?? h.base_median_abs_pct ?? 0).toFixed(2)}%</td>
                <td className={`text-right ${sig ? "text-amber-300" : "text-slate-500"}`}>{h.p_value_vs_base?.toFixed(2)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ReliabilityCard({ r }: { r?: Reliability | null }) {
  if (!r) {
    return <p className="text-xs text-slate-500">Bu ayar için geçmiş isabet karnesi yok (karne yalnız 50 ve 100 mum için hesaplandı).</p>;
  }
  const tone = r.verdict === "tabanı aşıyor" ? "text-green-400" : r.verdict === "tabanın altında" ? "text-red-400" : "text-amber-300";
  return (
    <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
      <Stat label="Eşleşme yön isabeti" value={`%${r.direction_hit_pct.toFixed(1)}`} />
      <Stat label="Rastgele komşu" value={`%${r.random_neighbors_hit_pct.toFixed(1)}`} />
      <Stat label="Hep çoğunluk yönü" value={`%${r.always_majority_hit_pct.toFixed(1)}`} />
      <Stat label="Karar" value={r.verdict} className={tone} />
      <p className="col-span-2 text-slate-500 sm:col-span-4">
        {r.n_queries} geçmiş sorgu ({fmtDate(r.test_from)} sonrası, sızıntısız), {r.horizon_bars} mum ufku. Büyüklük ilişkisi:
        eşleşme {r.magnitude_corr_matches?.toFixed(2) ?? "—"} · saatin tipik hareketi {r.magnitude_corr_hour_typical?.toFixed(2) ?? "—"}.
      </p>
    </div>
  );
}

function Stat({ label, value, className = "text-slate-100" }: { label: string; value: string; className?: string }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-0.5 text-sm font-semibold ${className}`}>{value}</div>
    </div>
  );
}

function Selector<T extends string | number>({ items, value, onChange, label }: { items: { key: T; label: string }[]; value: T; onChange: (v: T) => void; label: string }) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      <span className="mr-1 text-[11px] text-slate-500">{label}</span>
      {items.map((it) => (
        <button
          key={String(it.key)}
          onClick={() => onChange(it.key)}
          className={`rounded-md px-2.5 py-1 text-xs transition-colors ${value === it.key ? "bg-blue-600 text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

// ─────────────────────────────── ana panel ───────────────────────────────
export default function CandleSimilarityPanel({ initialSymbol = "NDX" }: { initialSymbol?: string }) {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [tf, setTf] = useState("1h");
  const [n, setN] = useState(50);
  const [sel, setSel] = useState(0);
  const { data, isLoading, isFetching, error } = useCandleSimilarity(symbol, tf, n);

  const charted = useMemo(() => (data?.matches ?? []).filter((m): m is SimilarityMatch & { chart: NonNullable<SimilarityMatch["chart"]> } => !!m.chart), [data]);
  const active = charted[Math.min(sel, Math.max(charted.length - 1, 0))];

  return (
    <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 shadow-xl backdrop-blur sm:p-6">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ScanSearch className="h-5 w-5 text-teal-400" />
          <h2 className="text-lg font-semibold text-white">Mum Benzerlik Tarayıcısı</h2>
          {isFetching && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
        </div>
        {data?.library && (
          <span className="text-[11px] text-slate-500">
            Kütüphane {fmtDate(data.library.start)} → {fmtDate(data.library.end)} · {data.library.candidates.toLocaleString("tr-TR")} aday pencere ·
            sorgu: {data.source === "canli" ? "canlı mumlar" : "arşivin son mumları"}
          </span>
        )}
      </header>

      <div className="mb-4 flex flex-col gap-2">
        <Selector label="Sembol" items={SYMBOLS} value={symbol} onChange={(v) => { setSymbol(v); setSel(0); }} />
        <Selector label="Zaman" items={TIMEFRAMES.map((t) => ({ key: t, label: TF_LABEL[t] }))} value={tf} onChange={(v) => { setTf(v); setSel(0); }} />
        <Selector label="Mum sayısı" items={WINDOWS.map((w) => ({ key: w, label: String(w) }))} value={n} onChange={(v) => { setN(v); setSel(0); }} />
      </div>

      {isLoading && (
        <div className="flex h-64 items-center justify-center text-slate-400"><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Geçmiş taranıyor…</div>
      )}
      {error && !data && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          <AlertTriangle className="h-4 w-4" /> Tarama yapılamadı: {(error as Error).message}
        </div>
      )}
      {data?.error && <p className="rounded-lg bg-white/5 p-3 text-sm text-slate-300">Sonuç yok: {data.error}</p>}

      {data?.query && data.horizons && data.horizons_bars && (
        <div className="space-y-5">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-white/5 bg-black/20 p-3">
              <div className="mb-1 flex justify-between text-xs text-slate-400">
                <span>Şimdi — son {n} mum ({TF_LABEL[tf]})</span>
                <span>{fmtDate(data.query.start)} → {fmtDate(data.query.end)}</span>
              </div>
              <CandleChart window={data.query.chart} />
            </div>
            <div className="rounded-xl border border-white/5 bg-black/20 p-3">
              {active ? (
                <>
                  <div className="mb-1 flex justify-between text-xs text-slate-400">
                    <span>#{active.rank} eş · benzerlik <b className="text-teal-300">{active.similarity.toFixed(0)}</b> · sonrası gri alanda</span>
                    <span>{fmtDate(active.start)} → {fmtDate(active.end)}</span>
                  </div>
                  <CandleChart window={active.chart.window} future={active.chart.future} />
                </>
              ) : (
                <p className="text-sm text-slate-500">Gösterilecek eş yok.</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            {charted.map((m, i) => (
              <button
                key={m.rank}
                onClick={() => setSel(i)}
                className={`rounded-lg border p-1.5 text-left transition-colors ${i === sel ? "border-teal-400/70 bg-teal-500/10" : "border-white/5 bg-black/20 hover:border-white/20"}`}
              >
                <CandleChart window={m.chart.window} future={m.chart.future} height={70} compact />
                <div className="mt-1 flex justify-between text-[10px] text-slate-400">
                  <span>#{m.rank} · {m.similarity.toFixed(0)}</span>
                  <span className={(m.fwd_pct[String(data.horizons_bars?.[1])] ?? 0) >= 0 ? "text-green-400" : "text-red-400"}>
                    {fmtPct(m.fwd_pct[String(data.horizons_bars?.[1])], 2)}
                  </span>
                </div>
              </button>
            ))}
          </div>

          <div className="rounded-xl border border-white/5 bg-black/20 p-3">
            <h3 className="mb-2 text-sm font-medium text-slate-200">Eşlerden sonra ne oldu? ({data.matches?.length} eş)</h3>
            <HorizonTable horizons={data.horizons} bars={data.horizons_bars} tf={tf} price={data.price} />
          </div>

          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-amber-200">
              <AlertTriangle className="h-4 w-4" /> Bu ayarın geçmiş isabet karnesi
            </h3>
            <ReliabilityCard r={data.reliability} />
            {data.note && <p className="mt-2 text-[11px] text-slate-400">{data.note}</p>}
          </div>
        </div>
      )}
    </section>
  );
}
