"use client";

/**
 * Zaman Makinesi Paneli — bir işlem planının (yön, stop, hedef, ufuk) olasılıkları ve ufuk-sonu fiyat aralığı.
 * Yöntem: day-trader-skill / trader-timemachine (MIT) — son 60 seansın aynı gün-saatindeki 5 dk mumlarından simülasyon.
 * Dürüstlük: kendi kalibrasyon karnesi yanında gösterilir (TM-01: olasılık meyilleri tabanı geçmedi; %90 aralık tuttu).
 */

import { useState } from "react";
import { AlertTriangle, BellPlus, Hourglass, Loader2 } from "lucide-react";

import { useCreatePlanAlerts } from "@/lib/api/alerts";
import { type TimeMachineResult, type TmTimeframe, type TradeSide, useTimeMachine, useTimeMachineCalibration } from "@/lib/api/timeMachine";

const SYMBOLS = [
  { key: "NDX", label: "NASDAQ 100" },
  { key: "DAX", label: "DAX 40" },
  { key: "XAUUSD", label: "Altın" },
  { key: "USOIL", label: "Petrol" },
];
const STOP_ATRS = [0.5, 1, 1.5, 2, 3];
const TARGET_RS = [1, 1.5, 2, 3];
const TFS: { key: TmTimeframe; label: string }[] = [
  { key: "5m", label: "5 dk" },
  { key: "15m", label: "15 dk" },
  { key: "1h", label: "1 saat" },
];
const TF_MINUTES: Record<TmTimeframe, number> = { "5m": 5, "15m": 15, "1h": 60 };
/** Ufuk dakika cinsinden; bar sayısı seçilen zaman dilimine göre hesaplanır (API tavanı 287 bar). */
const HORIZONS = [
  { key: 60, label: "1 sa" },
  { key: 120, label: "2 sa" },
  { key: 240, label: "4 sa" },
  { key: 480, label: "8 sa" },
  { key: 1440, label: "1 gün" },
];
const MAX_BARS = 287;

function fmtPrice(v: number): string {
  return v >= 1000 ? v.toFixed(1) : v.toFixed(2);
}

function Chips<T extends string | number>({ label, items, value, onChange }: {
  label: string; items: { key: T; label: string }[]; value: T; onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      <span className="mr-1 text-[11px] text-slate-500">{label}</span>
      {items.map((it) => (
        <button
          key={String(it.key)}
          onClick={() => onChange(it.key)}
          className={`rounded-md px-2.5 py-1 text-xs transition-colors ${value === it.key ? "bg-indigo-600 text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"}`}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

function OddsBar({ target, stop, neither }: { target: number; stop: number; neither: number }) {
  const seg = (v: number, cls: string, txt: string) =>
    v > 0.005 ? <div className={`${cls} flex items-center justify-center text-[11px] font-semibold text-white`} style={{ width: `${v * 100}%` }}>{txt} %{(v * 100).toFixed(1)}</div> : null;
  return (
    <div className="flex h-8 w-full overflow-hidden rounded-lg bg-white/5">
      {seg(target, "bg-green-600", "hedef")}
      {seg(neither, "bg-slate-600", "hiçbiri")}
      {seg(stop, "bg-red-600", "stop")}
    </div>
  );
}

function FanChart({ bands, entry, stop, target }: { bands: number[][]; entry: number; stop: number; target: number }) {
  const W = 1000, H = 200, pad = 10;
  const all = bands.flat().concat([stop, target, entry]);
  const lo = Math.min(...all), hi = Math.max(...all);
  const x = (i: number) => (i / Math.max(bands.length - 1, 1)) * W;
  const y = (v: number) => pad + (1 - (v - lo) / (hi - lo || 1)) * (H - 2 * pad);
  const area = (a: number, b: number) =>
    bands.map((r, i) => `${x(i)},${y(r[a])}`).join(" ") + " " + bands.map((r, i) => `${x(i)},${y(r[b])}`).reverse().join(" ");
  const line = (v: number, color: string, dash = "") => <line x1={0} x2={W} y1={y(v)} y2={y(v)} stroke={color} strokeWidth={2} strokeDasharray={dash} vectorEffect="non-scaling-stroke" />;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="w-full" style={{ height: H }}>
      <polygon points={area(0, 4)} fill="rgba(99,102,241,0.18)" />
      <polygon points={area(1, 3)} fill="rgba(99,102,241,0.35)" />
      <polyline points={bands.map((r, i) => `${x(i)},${y(r[2])}`).join(" ")} fill="none" stroke="#a5b4fc" strokeWidth={2} vectorEffect="non-scaling-stroke" />
      {line(target, "#22c55e", "8 6")}
      {line(stop, "#ef4444", "8 6")}
      {line(entry, "#94a3b8")}
    </svg>
  );
}

function CalibrationCard() {
  const { data } = useTimeMachineCalibration();
  const p = data?.olasilik?.tum;
  const r = data?.aralik?.tum;
  if (!p || !r) return null;
  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-slate-300">
      <div className="mb-1 flex items-center gap-1.5 font-medium text-amber-200"><AlertTriangle className="h-4 w-4" /> Bu aracın geçmiş karnesi ({data?._meta?.test})</div>
      <p>
        <b className="text-green-300">Fiyat aralığı güvenilir:</b> %90 aralık {r.n} geçmiş sorgunun %{r["kapsama90_%"].toFixed(1)}'inde tuttu
        (saat-koşulsuz aralıktan daha dar: %{r["genislik90_medyan_%"].toFixed(2)} vs %{r["saatsiz_genislik90_medyan_%"].toFixed(2)}).
      </p>
      <p className="mt-1">
        <b className="text-red-300">Olasılık meyli güvenilir değil:</b> "hedefe/stopa meyilli" sapmaları sabit %50'den iyi tahmin etmedi
        (Brier {p.brier.toFixed(4)} vs taban {p.brier_iklim.toFixed(4)}, n={p.n}). "Yazı-tura" hükmü doğru; meyilleri gürültü say.
      </p>
    </div>
  );
}

/** Planın stop + hedef + ufuk-sonu zaman alarmlarını kurar (repo trader-alerts `add --from-plan`). */
function PlanAlertButton({ symbol, data, horizonMin }: { symbol: string; data: TimeMachineResult; horizonMin: number }) {
  const create = useCreatePlanAlerts();
  const { side, entry, stop, target } = data.plan;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={() => create.mutate({ symbol, side, entry, stop, target, horizon_min: horizonMin })}
        disabled={create.isPending}
        className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-xs text-slate-200 hover:bg-white/10 disabled:opacity-50"
      >
        <BellPlus className="h-4 w-4" /> {create.isPending ? "Kuruluyor…" : "Bu plan için alarm kur (stop · hedef · ufuk sonu)"}
      </button>
      {create.isSuccess && <span className="text-xs text-green-300">{create.data.created.length} alarm kuruldu — /alerts</span>}
      {create.error && <span className="text-xs text-red-300">{(create.error as Error).message}</span>}
    </div>
  );
}

export default function TimeMachinePanel({ initialSymbol = "NDX" }: { initialSymbol?: string }) {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [side, setSide] = useState<TradeSide>("buy");
  const [stopAtr, setStopAtr] = useState(1);
  const [targetR, setTargetR] = useState(1);
  const [horizonMin, setHorizonMin] = useState(240);
  const [tf, setTf] = useState<TmTimeframe>("5m");
  const bars = Math.min(MAX_BARS, Math.max(1, Math.round(horizonMin / TF_MINUTES[tf])));
  const { data, isLoading, isFetching, error } = useTimeMachine({ symbol, side, stopAtr, targetR, bars, tf });

  return (
    <section className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 shadow-xl backdrop-blur sm:p-6">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Hourglass className="h-5 w-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-white">Zaman Makinesi — kaç pips gidebilir?</h2>
          {isFetching && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
        </div>
        <span className="text-[11px] text-slate-500">yöntem: day-trader-skill / trader-timemachine (MIT)</span>
      </header>

      <div className="mb-4 flex flex-col gap-2">
        <Chips<string> label="Sembol" items={SYMBOLS} value={symbol} onChange={setSymbol} />
        <Chips<TradeSide> label="Yön" items={[{ key: "buy" as TradeSide, label: "AL" }, { key: "sell" as TradeSide, label: "SAT" }]} value={side} onChange={setSide} />
        <Chips<number> label="Stop (ATR)" items={STOP_ATRS.map((v) => ({ key: v, label: `${v}×` }))} value={stopAtr} onChange={setStopAtr} />
        <Chips<number> label="Hedef" items={TARGET_RS.map((v) => ({ key: v, label: `${v}R` }))} value={targetR} onChange={setTargetR} />
        <Chips<TmTimeframe> label="Zaman dilimi" items={TFS} value={tf} onChange={setTf} />
        <Chips<number> label="Ufuk" items={HORIZONS} value={horizonMin} onChange={setHorizonMin} />
      </div>

      {isLoading && <div className="flex h-40 items-center justify-center text-slate-400"><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Simülasyon koşuyor…</div>}
      {error && !data && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          <AlertTriangle className="h-4 w-4" /> {(error as Error).message}
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="grid gap-2 text-xs sm:grid-cols-4">
            <Box label="Giriş (son kapanmış 5 dk)" value={fmtPrice(data.plan.entry)} />
            <Box label="Stop" value={`${fmtPrice(data.plan.stop)} (${fmtPrice(Math.abs(data.plan.entry - data.plan.stop))})`} tone="text-red-300" />
            <Box label="Hedef" value={`${fmtPrice(data.plan.target)} (${fmtPrice(Math.abs(data.plan.target - data.plan.entry))})`} tone="text-green-300" />
            <Box label={`%90 aralık · ${data.mc.bars_left} bar sonra`} value={`${fmtPrice(data.mc.p5_close)} – ${fmtPrice(data.mc.p95_close)}`} tone="text-indigo-200" />
          </div>
          <OddsBar target={data.mc.p_target} stop={data.mc.p_stop} neither={data.mc.p_neither} />
          <div className="rounded-xl border border-white/5 bg-black/20 p-3">
            <div className="mb-1 flex justify-between text-[11px] text-slate-400">
              <span>{data.mc.replays.toLocaleString("tr-TR")} simülasyon · tohum {data.mc.seed} · havuz {data.plan.pool_sessions} seans ({data.plan.pool_from} → {data.plan.pool_to})</span>
              <span>koyu: %25–75 · açık: %5–95 · yeşil hedef · kırmızı stop</span>
            </div>
            <FanChart bands={data.mc.bands} entry={data.plan.entry} stop={data.plan.stop} target={data.plan.target} />
          </div>
          <div className="rounded-xl border border-white/5 bg-black/20 p-3 text-sm text-slate-200">
            <p className="font-medium">{data.verdict}</p>
            {data.notes.map((n) => <p key={n} className="text-xs text-slate-400">{n}</p>)}
            <p className="mt-2 text-xs text-slate-400">
              Geçmişte aynı saatte aynı planla girilseydi ({data.history.sessions} seans): {data.history.trades} işlem —
              {" "}{data.history.target} hedef, {data.history.stop} stop, {data.history.close} hiçbiri; ortalama R {data.history.avg_R ?? "—"}.
              Simülasyon ortalama R {data.mc.avg_R >= 0 ? "+" : ""}{data.mc.avg_R}.
            </p>
          </div>
          <PlanAlertButton symbol={symbol} data={data} horizonMin={horizonMin} />
          <CalibrationCard />
          <p className="text-[11px] text-slate-500">{data.note}</p>
        </div>
      )}
    </section>
  );
}

function Box({ label, value, tone = "text-slate-100" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-0.5 text-sm font-semibold ${tone}`}>{value}</div>
    </div>
  );
}
