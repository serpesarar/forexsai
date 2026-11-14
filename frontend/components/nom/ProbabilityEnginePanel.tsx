"use client";

import { memo, useState } from "react";
import { AlertTriangle, Info, Loader2 } from "lucide-react";

import {
  NOM_GEOMETRIES,
  NOM_HORIZONS,
  type NomCalSide,
  type NomContext,
  type NomHorizon,
  type NomSide,
  useNomCalibration,
  useNomProbability,
} from "@/lib/api/nom";

const pct = (x: number | null | undefined, d = 1) => (x == null ? "—" : `%${(100 * x).toFixed(d)}`);
const num = (x: number | null | undefined, d = 2) => (x == null ? "—" : x.toFixed(d));
const LADDER_H = 260;
const LADDER_SPAN_ATR = 3;

function DirectionWarning() {
  return (
    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-xs text-amber-100">
      <div className="mb-1 text-sm font-semibold text-amber-200">LONG − SHORT farkı yön sinyali değildir</div>
      Yön Laboratuvarı (2026-11-14, 8.680 deneme, dört şans tabanı): destek/direnç, EMA, VWAP, bant, pivot, Fibonacci, Ichimoku
      seviyelerinin hiçbiri aynı uzaklıktaki hayalet seviyeden ayrılmıyor — fiyat yakın seviyeye geometri yüzünden önce değer
      (kumarbazın iflası D/(U+D)). Bu motorun ±1 ATR yarışında yön isabeti %49,8–50,3. Tek kalıcı iz 15 dakikalık aşırı uzama dönüşü
      (≈ +2 puan isabet), işlem maliyetinin onda biri. Olasılıkları oynaklık/menzil bilgisi olarak okuyun.
    </div>
  );
}

function StatusBanner({ durum, neden }: { durum: string; neden?: string }) {
  const tone =
    durum === "LONG" ? "border-green-500/50 bg-green-500/10 text-green-300"
    : durum === "SHORT" ? "border-red-500/50 bg-red-500/10 text-red-300"
    : "border-slate-600 bg-slate-800/60 text-slate-300";
  return (
    <div className={`rounded-lg border px-4 py-3 ${tone}`}>
      <div className="text-lg font-semibold">{durum}</div>
      {neden && <div className="text-xs opacity-80">{neden}</div>}
    </div>
  );
}

const SideCard = memo(function SideCard({ side, s }: { side: "long" | "short"; s: NomSide }) {
  const color = side === "long" ? "text-green-400" : "text-red-400";
  const seg = [
    { k: "TP önce", v: s.p_tp_once, c: "bg-green-500" },
    { k: "SL önce", v: s.p_sl_once, c: "bg-red-500" },
    { k: "Zaman aşımı", v: s.p_zaman_asimi, c: "bg-slate-500" },
  ];
  const b = s.p_tp_bandi;
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className={`text-base font-semibold ${color}`}>{side === "long" ? "LONG" : "SHORT"}</span>
        <span className={`rounded px-2 py-0.5 text-[11px] ${s.kanitli ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-300"}`}>
          {s.kanitli ? "kanıtlı hedef" : "kanıtsız — yalnız bilgi"}
        </span>
      </div>
      <div className="flex h-5 w-full overflow-hidden rounded">
        {seg.map((x) => (
          <div key={x.k} className={`${x.c} h-full`} style={{ width: `${Math.max(0, x.v) * 100}%` }} title={`${x.k} ${pct(x.v)}`} />
        ))}
      </div>
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-300">
        {seg.map((x) => (
          <div key={x.k}>
            <div className="text-slate-500">{x.k}</div>
            <div className="text-sm font-medium text-slate-100">{pct(x.v)}</div>
          </div>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div>
          <div className="text-slate-500">Beklenen R (sürtünmeli)</div>
          <div className={`text-sm font-semibold ${s.beklenen_r > 0 ? "text-green-400" : "text-red-400"}`}>{num(s.beklenen_r, 3)}</div>
          <div className="text-slate-500">taban {num(s.taban.beklenen_r, 3)}</div>
        </div>
        <div>
          <div className="text-slate-500">Bu kovada geçmişte gerçekleşen TP</div>
          <div className="text-sm text-slate-100">{b ? `${pct(b.obs)} (%95: ${pct(b.ci_lo)}–${pct(b.ci_hi)})` : "—"}</div>
          <div className="text-slate-500">taban P(TP) {pct(s.taban.p_tp)}</div>
        </div>
      </div>
      <div className="mt-3">
        <div className="mb-1 text-xs font-medium text-slate-400">Neden? (P(TP)'yi en çok etkileyen 5 faktör)</div>
        <ul className="space-y-1 text-xs">
          {s.neden.map((r) => (
            <li key={r.ozellik} className="flex items-start gap-2">
              <span className={`mt-1 inline-block h-2 w-2 shrink-0 rounded-full ${r.katki > 0 ? "bg-green-500" : "bg-red-500"}`} />
              <span className="text-slate-300">{r.metin}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
});

const LevelLadder = memo(function LevelLadder({ c }: { c: NomContext }) {
  const y = (d: number) => LADDER_H / 2 - (d / LADDER_SPAN_ATR) * (LADDER_H / 2);
  const lv = [...c.direncler.map((l) => ({ ...l, t: "R" })), ...c.destekler.map((l) => ({ ...l, t: "S" }))]
    .filter((l) => Math.abs(l.dist_atr) <= LADDER_SPAN_ATR);
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="mb-2 text-sm font-medium text-slate-300">Destek / direnç haritası (±{LADDER_SPAN_ATR} ATR H1)</div>
      <svg viewBox={`0 0 320 ${LADDER_H}`} className="w-full" role="img" aria-label="Destek direnç merdiveni">
        <line x1="10" x2="310" y1={LADDER_H / 2} y2={LADDER_H / 2} stroke="#e2e8f0" strokeWidth="2" />
        <text x="12" y={LADDER_H / 2 - 4} fill="#e2e8f0" fontSize="11">fiyat {c.fiyat.toFixed(1)}</text>
        {lv.map((l, i) => (
          <g key={`${l.t}${i}`}>
            <line x1="10" x2="310" y1={y(l.dist_atr)} y2={y(l.dist_atr)} stroke={l.t === "R" ? "#ef4444" : "#22c55e"}
              strokeDasharray="4 3" strokeWidth={Math.min(1 + l.tests * 0.4, 4)} />
            <text x="308" y={y(l.dist_atr) - 3} textAnchor="end" fill={l.t === "R" ? "#fca5a5" : "#86efac"} fontSize="10">
              {l.price.toFixed(1)} · {l.dist_atr > 0 ? "+" : ""}{l.dist_atr.toFixed(2)} ATR · {l.tests} test · {l.kind}
            </text>
          </g>
        ))}
      </svg>
      {lv.length === 0 && <div className="text-xs text-slate-500">±{LADDER_SPAN_ATR} ATR içinde seviye yok.</div>}
    </div>
  );
});

const ContextCard = memo(function ContextCard({ c }: { c: NomContext }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-xs text-slate-300">
      <div className="mb-2 text-sm font-medium text-slate-300">RSI ve rejim</div>
      <div className="space-y-1.5">
        {Object.entries(c.rsi).map(([tf, r]) => (
          <div key={tf} className="flex items-center gap-2">
            <span className="w-8 text-slate-500">{tf}</span>
            <div className="relative h-2 flex-1 rounded bg-slate-800">
              <div className="absolute inset-y-0 left-[30%] w-px bg-slate-500" />
              <div className="absolute inset-y-0 left-[70%] w-px bg-slate-500" />
              <div className={`absolute top-[-3px] h-3.5 w-1.5 rounded ${r.bolge === "nötr" ? "bg-sky-400" : r.bolge === "aşırı alım" ? "bg-red-400" : "bg-green-400"}`}
                style={{ left: `calc(${r.rsi14}% - 3px)` }} />
            </div>
            <span className="w-28 text-right">{r.rsi14.toFixed(1)} · {r.bolge}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <div>Rejim: <b className="text-slate-100">{c.rejim}</b> (ADX H1 {num(c.trend.h1_adx, 1)})</div>
        <div>ATR rejimi H1: <b className="text-slate-100">{num(c.atr_rejim_h1)}</b>×</div>
        <div>EMA dizilimi H1: <b className="text-slate-100">{num(c.trend.h1_ema_dizilim, 0)}</b></div>
        <div>HH/HL yapısı: <b className="text-slate-100">{num(c.trend.h1_yapi_hh_hl, 0)}</b></div>
        <div>Seans: <b className="text-slate-100">{c.seans}</b></div>
        <div>VIX: <b className="text-slate-100">{c.vix ? `${c.vix.deger} · ${c.vix.rejim}` : "—"}</b></div>
        <div className="col-span-2">
          Yaklaşan olay: <b className="text-slate-100">{c.yaklasan_olay ? `${c.yaklasan_olay.olay} · ${Math.round(c.yaklasan_olay.dakika / 60)} s sonra` : "—"}</b>
        </div>
      </div>
    </div>
  );
});

function ReliabilityChart({ side, s }: { side: string; s: NomCalSide }) {
  const W = 240, Hh = 200, pad = 28;
  const ref = s.wf_referans ?? [];
  const maxP = Math.max(0.05, ...ref.map((r) => Math.max(r.hi, r.ci_hi)), ...(s.kovalar ?? []).map((k) => k.gerceklesen));
  const sx = (v: number) => pad + (v / maxP) * (W - pad - 6);
  const sy = (v: number) => Hh - pad - (v / maxP) * (Hh - pad - 6);
  return (
    <div>
      <div className="mb-1 text-xs text-slate-400">{side} · gri = WF bandı (%95), mavi = canlı</div>
      <svg viewBox={`0 0 ${W} ${Hh}`} className="h-auto w-full max-w-xs" role="img" aria-label={`${side} kalibrasyon grafiği`}>
        <line x1={sx(0)} y1={sy(0)} x2={sx(maxP)} y2={sy(maxP)} stroke="#475569" strokeDasharray="3 3" />
        {ref.map((r, i) => (
          <line key={i} x1={sx(r.pred)} x2={sx(r.pred)} y1={sy(r.ci_lo)} y2={sy(r.ci_hi)} stroke="#64748b" strokeWidth="4" strokeLinecap="round" />
        ))}
        {(s.kovalar ?? []).map((k, i) => (
          <circle key={i} cx={sx(k.beklenen)} cy={sy(k.gerceklesen)} r={Math.min(2 + Math.sqrt(k.n) / 3, 7)}
            fill={k.bant_icinde ? "#38bdf8" : "#f97316"} />
        ))}
        <text x={pad} y={Hh - 6} fill="#94a3b8" fontSize="8">tahmin P(TP)</text>
        <text x="2" y="10" fill="#94a3b8" fontSize="8">gerçekleşen</text>
      </svg>
      <div className="text-[11px] text-slate-400">
        n={s.n} · Brier becerisi {num(s.brier_beceri ?? null, 3)} · ort R {num(s.ort_R ?? null, 3)}
        {s.mezuniyet && <> · {s.mezuniyet.mezun ? "mezun ✓" : `mezun değil (${s.mezuniyet.gun} gün, ${s.mezuniyet.bagimsiz_n} bağımsız)`}</>}
        {s.drift_uyarisi && <span className="ml-1 text-orange-400">· drift uyarısı</span>}
      </div>
    </div>
  );
}

function CalibrationCard({ h, g }: { h: NomHorizon; g: string }) {
  const q = useNomCalibration(h, g);
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="mb-2 text-sm font-medium text-slate-300">Canlı kalibrasyon (gölge kayıtları, son 56 gün)</div>
      {q.isLoading && <div className="flex items-center gap-2 text-xs text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> yükleniyor</div>}
      {q.error && <div className="text-xs text-red-400">Kalibrasyon alınamadı: {(q.error as Error).message}</div>}
      {q.data && q.data.n_satir === 0 && (
        <div className="text-xs text-slate-400">Henüz çözülmüş gölge tahmini yok — gölge modu (NOM_SHADOW_ENABLED=1) veri biriktirdikçe dolacak.
          Mezuniyet ölçütü: {q.data.mezuniyet_olcutu}.</div>
      )}
      {q.data && q.data.n_satir > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          <ReliabilityChart side="LONG" s={q.data.long} />
          <ReliabilityChart side="SHORT" s={q.data.short} />
        </div>
      )}
    </div>
  );
}

export default function ProbabilityEnginePanel({ asof }: { asof?: string | null }) {
  const [h, setH] = useState<NomHorizon>("1h");
  const [g, setG] = useState("1.5x1.0");
  const q = useNomProbability(h, g, asof);
  const d = q.data;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex overflow-hidden rounded-lg border border-slate-700">
          {NOM_HORIZONS.map((x) => (
            <button key={x.key} type="button" onClick={() => setH(x.key)}
              className={`px-3 py-1.5 text-sm ${h === x.key ? "bg-orange-500 text-white" : "bg-slate-900 text-slate-300 hover:bg-slate-800"}`}>
              {x.label}
            </button>
          ))}
        </div>
        <select value={g} onChange={(e) => setG(e.target.value)} aria-label="Geometri (TP x SL, ATR)"
          className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-200">
          {NOM_GEOMETRIES.map((x) => <option key={x} value={x}>TP/SL {x} ATR</option>)}
        </select>
        {d?.atr_ufuk && <span className="text-xs text-slate-400">ATR birimi: {d.atr_ufuk.tf} = {d.atr_ufuk.deger.toFixed(1)} puan</span>}
        {q.isFetching && <Loader2 className="h-4 w-4 animate-spin text-slate-500" />}
        {d?.yeniden_oynatma && (
          <span className="rounded bg-amber-500/20 px-2 py-0.5 text-xs text-amber-300">yeniden oynatma: {new Date(d.yeniden_oynatma).toLocaleString("tr-TR")}</span>
        )}
      </div>

      {q.isLoading && <div className="flex items-center gap-2 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Olasılıklar hesaplanıyor…</div>}
      {q.error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          <AlertTriangle className="h-4 w-4" /> Motor yanıt vermedi: {(q.error as Error).message}
        </div>
      )}
      {d && !d.tahmin && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200">
          <b>{d.durum}</b> {d.aciklama ?? ""} {d.veri && <>· son bar {new Date(d.veri.son_bar_kapanis_utc).toLocaleString("tr-TR")}</>}
        </div>
      )}
      {d?.tahmin && d.baglam && (
        <>
          <StatusBanner durum={d.durum} neden={d.durum_nedeni} />
          <DirectionWarning />
          <div className="grid gap-4 lg:grid-cols-2">
            <SideCard side="long" s={d.tahmin.long} />
            <SideCard side="short" s={d.tahmin.short} />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <LevelLadder c={d.baglam} />
            <ContextCard c={d.baglam} />
          </div>
        </>
      )}
      <CalibrationCard h={h} g={g} />
      {d && (
        <div className="flex items-start gap-2 text-[11px] text-slate-500">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            Model {d.model.surum} (eğitim sonu {d.model.egitim_sonu ?? "?"}; {d.model.veri_surumu}) · veri: {d.veri?.kaynak} ·
            gecikme {d.veri ? Math.round(d.veri.gecikme_sn) : "?"} sn. {d.not} Olasılıklar sürtünme (spread + kayma) dahil
            ATR-ölçekli bariyerler içindir; "kanıtsız" hedeflerde yön önerisi verilmez.
          </span>
        </div>
      )}
    </div>
  );
}
