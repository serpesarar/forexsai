"use client";

/**
 * Canlı Haber Akışı + Kaynak Hız Karnesi.
 * Başlık yapay zekâ beklemeden görünür. Yön etiketi bilinçli olarak YOK: HB-01 olay çalışmasında
 * 2026-03→05 AI yön etiketlerinin 28 hücresinden hiçbiri geçmedi; bu ekran bilgi amaçlıdır.
 */

import { memo, useMemo, useState } from "react";
import { AlertTriangle, ExternalLink, Loader2, Radio, Trophy } from "lucide-react";

import {
  type NewsStory,
  type NewsUrgency,
  type SourceScore,
  useNewsSources,
  useRepoScorecard,
  useNewsStatus,
  useNewsStream,
} from "@/lib/api/newsFeed";

const SYMBOLS: { key: string | null; label: string }[] = [
  { key: null, label: "Tümü" },
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "GDAXI.INDX", label: "DAX" },
  { key: "XAUUSD", label: "Altın" },
  { key: "USOIL.FOREX", label: "Petrol" },
];
const RELEVANCE_LEVELS = [
  { value: 50, label: "İlgili" },
  { value: 75, label: "Yüksek" },
  { value: 85, label: "Yalnız son dakika" },
];
const MIN_RACES_FOR_RANK = 30;
const URGENCY_STYLE: Record<NewsUrgency, string> = {
  breaking: "bg-red-500/20 text-red-300 border-red-500/40",
  high: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  medium: "bg-slate-500/20 text-slate-300 border-slate-500/40",
  low: "bg-slate-800 text-slate-500 border-slate-700",
};
const URGENCY_LABEL: Record<NewsUrgency, string> = { breaking: "SON DAKİKA", high: "YÜKSEK", medium: "ORTA", low: "DÜŞÜK" };
const CONFIRMATION_LABEL: Record<NewsStory["confirmation"], string> = { official: "Resmi", reported: "Haber", unconfirmed: "Teyitsiz" };
const EVENT_LABEL: Record<string, string> = {
  cb_decision: "Faiz kararı", cb_speak: "Merkez bankası", macro_print: "Makro veri", tariff_trade: "Tarife/ticaret",
  energy: "Enerji", metals: "Metal", geopolitics: "Jeopolitik", politics_us: "ABD siyaseti", big_tech: "Büyük teknoloji",
  germany_eu: "Almanya/AB", market_move: "Piyasa", other: "Diğer",
};
const SYMBOL_LABEL: Record<string, string> = { "NDX.INDX": "NDX", "GDAXI.INDX": "DAX", XAUUSD: "XAU", "USOIL.FOREX": "OIL" };

function fmtSec(v: number | null): string {
  if (v === null) return "—";
  return v < 90 ? `${v.toFixed(0)} sn` : `${(v / 60).toFixed(1)} dk`;
}

function fmtClock(iso: string): string {
  return new Date(iso).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

const StoryRow = memo(function StoryRow({ story }: { story: NewsStory }) {
  return (
    <li className="border-b border-white/5 px-4 py-3 last:border-0">
      <div className="mb-1 flex flex-wrap items-center gap-2 text-[11px]">
        <span className={`rounded border px-1.5 py-0.5 font-semibold ${URGENCY_STYLE[story.urgency]}`}>{URGENCY_LABEL[story.urgency]}</span>
        <span className="text-slate-400">{EVENT_LABEL[story.event_type] ?? story.event_type}</span>
        <span className="text-slate-500">{CONFIRMATION_LABEL[story.confirmation]}</span>
        {story.symbols.map((s) => (
          <span key={s} className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300">{SYMBOL_LABEL[s] ?? s}</span>
        ))}
        <span className="ml-auto tabular-nums text-slate-500" title={story.seeded ? "Motor açılmadan önce yayınlandı; saat yayın saatidir" : "Sistemin ilk gördüğü an"}>
          {story.seeded && "yayın "}{fmtClock(story.display_at)}
        </span>
      </div>
      <p className="text-sm leading-snug text-slate-100">
        {story.url ? (
          <a href={story.url} target="_blank" rel="noreferrer noopener" className="hover:text-blue-300">
            {story.headline} <ExternalLink className="ml-0.5 inline h-3 w-3 opacity-50" />
          </a>
        ) : story.headline}
      </p>
      <p className="mt-1 text-[11px] text-slate-500">
        İlk: <span className="text-slate-300">{story.first_source_name}</span>
        {story.n_sources > 1 && <> · {story.n_sources} kaynak teyit etti</>}
      </p>
    </li>
  );
});

function SourceTable({ rows }: { rows: SourceScore[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead className="text-slate-500">
          <tr>
            <th className="px-3 py-2 font-medium">Kaynak</th>
            <th className="px-2 py-2 text-right font-medium" title="Başka bir kaynakla aynı haberi gördüğü yarış sayısı">Yarış</th>
            <th className="px-2 py-2 text-right font-medium">İlk gelme</th>
            <th className="px-2 py-2 text-right font-medium" title="Birinciden farkın medyanı, sorgu beklemesi düzeltilmiş">Gecikme</th>
            <th className="px-2 py-2 text-right font-medium">Sorgu</th>
            <th className="px-3 py-2 text-right font-medium">Sağlık</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const stale = r.last_ok_ago_s === null || r.last_ok_ago_s > 300;
            return (
              <tr key={r.id} className="border-t border-white/5">
                <td className="px-3 py-1.5 text-slate-200" title={`Kaynak depo: ${r.repo}`}>
                  {r.name}{r.unofficial && <span className="ml-1 text-amber-500/80" title="Resmi akış değil; sayfa ayrıştırma">*</span>}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums text-slate-400">{r.races}</td>
                <td className="px-2 py-1.5 text-right tabular-nums text-slate-300">
                  {r.races >= MIN_RACES_FOR_RANK && r.first_rate !== null ? `%${(r.first_rate * 100).toFixed(0)}` : <span className="text-slate-600" title="En az 30 yarış gerekli">az veri</span>}
                </td>
                <td className="px-2 py-1.5 text-right tabular-nums text-slate-300">{r.races >= MIN_RACES_FOR_RANK ? fmtSec(r.lag_adj_p50_s) : "—"}</td>
                <td className="px-2 py-1.5 text-right tabular-nums text-slate-500">{r.interval_s ? `${r.interval_s.toFixed(0)} sn` : "push"}</td>
                <td className="px-3 py-1.5 text-right">
                  {r.last_error && stale ? (
                    <span className="text-red-400" title={r.last_error}>hata</span>
                  ) : stale ? (
                    <span className="text-amber-400">bekliyor</span>
                  ) : (
                    <span className="text-emerald-400">canlı</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const DECISION_STYLE: Record<string, string> = {
  FIKIR_ALINDI: "text-emerald-300",
  ALTERNATIF_KULLANILDI: "text-emerald-300",
  ANAHTAR_BEKLIYOR: "text-sky-300",
  SINANDI: "text-amber-300",
};

function RepoScorecard() {
  const { data, isLoading, isError } = useRepoScorecard();
  if (isLoading) return <div className="flex items-center justify-center gap-2 p-8 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Karne yükleniyor</div>;
  if (isError) return <div className="p-8 text-center text-sm text-red-300">Karne alınamadı.</div>;
  if (!data?.repolar.length) return <div className="p-8 text-center text-sm text-slate-500">Karne henüz üretilmedi.</div>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead className="text-slate-500">
          <tr>
            <th className="px-3 py-2 text-right font-medium" title="Önceliklendirme kılavuzu; kâr tahmini değildir">Puan</th>
            <th className="px-3 py-2 font-medium">Depo</th>
            <th className="px-3 py-2 font-medium">Karar</th>
            <th className="px-3 py-2 font-medium">Ne yapıldı</th>
            <th className="px-3 py-2 font-medium">Kâr kanıtı</th>
          </tr>
        </thead>
        <tbody>
          {data.repolar.map((r) => (
            <tr key={r.repo} className="border-t border-white/5 align-top">
              <td className="px-3 py-2 text-right tabular-nums text-slate-300">{r.puan}</td>
              <td className="px-3 py-2"><a href={r.url} target="_blank" rel="noreferrer noopener" className="text-slate-200 hover:text-blue-300">{r.repo}</a></td>
              <td className={`whitespace-nowrap px-3 py-2 ${DECISION_STYLE[r.karar] ?? "text-slate-500"}`}>{r.karar_tr}</td>
              <td className="min-w-64 px-3 py-2 text-slate-400">{r.kullanim}</td>
              <td className="min-w-48 px-3 py-2 text-slate-400">{r.kar_kaniti}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function NewsFeedPanel() {
  const [symbol, setSymbol] = useState<string | null>(null);
  const [minRelevance, setMinRelevance] = useState(RELEVANCE_LEVELS[0].value);
  const { items, loading, error, live } = useNewsStream(symbol, minRelevance);
  const sources = useNewsSources();
  const status = useNewsStatus();
  const totalRaces = useMemo(() => (sources.data?.sources ?? []).reduce((a, r) => a + r.races, 0), [sources.data]);
  const off = status.data && !status.data.running;

  return (
    <div className="space-y-4">
      <div className="flex gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-200/90">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          Bu akış bilgi içindir, işlem sinyali değildir. Mart–Mayıs 2026 arşivinde yapay zekânın haber yön etiketleri
          kârlı çıkmadı (28 hücrenin 0'ı geçti) ve 5 dakikaya kadar gecikme ölçülebilir fark yaratmadı. Bu yüzden burada yön etiketi gösterilmez.
        </p>
      </div>
      {off && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-200">
          Haber motoru bu sunucuda kapalı. Açmak için <code>NEWSFEED_ENABLED=1</code> gerekir.
        </div>
      )}
      <div className="grid gap-4 xl:grid-cols-[3fr_2fr]">
        <section className="rounded-xl border border-white/10 bg-slate-900/60">
          <header className="flex flex-wrap items-center gap-2 border-b border-white/10 p-3">
            <Radio className={`h-4 w-4 ${live ? "text-emerald-400" : "text-slate-500"}`} />
            <h2 className="text-sm font-semibold text-slate-100">Canlı akış</h2>
            <span className="text-[11px] text-slate-500">{live ? "bağlı" : "bağlanıyor…"}</span>
            {status.data?.in_release_window && <span className="rounded bg-blue-500/20 px-1.5 py-0.5 text-[11px] text-blue-300">Veri penceresi: 8 sn</span>}
            <div className="ml-auto flex flex-wrap gap-1">
              {SYMBOLS.map((s) => (
                <button key={s.label} type="button" onClick={() => setSymbol(s.key)} className={`rounded px-2 py-1 text-[11px] ${symbol === s.key ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}>{s.label}</button>
              ))}
              <select aria-label="İlgi düzeyi" value={minRelevance} onChange={(e) => setMinRelevance(Number(e.target.value))} className="rounded bg-slate-800 px-2 py-1 text-[11px] text-slate-300">
                {RELEVANCE_LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
              </select>
            </div>
          </header>
          {loading ? (
            <div className="flex items-center justify-center gap-2 p-10 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Haberler yükleniyor</div>
          ) : error ? (
            <div className="p-10 text-center text-sm text-red-300">Haberler alınamadı: {error}</div>
          ) : items.length === 0 ? (
            <div className="p-10 text-center text-sm text-slate-500">Bu filtreye uyan haber yok.</div>
          ) : (
            <ul className="max-h-[75vh] overflow-y-auto">{items.map((s) => <StoryRow key={s.id} story={s} />)}</ul>
          )}
        </section>
        <section className="rounded-xl border border-white/10 bg-slate-900/60">
          <header className="flex items-center gap-2 border-b border-white/10 p-3">
            <Trophy className="h-4 w-4 text-amber-400" />
            <h2 className="text-sm font-semibold text-slate-100">Kaynak hız karnesi</h2>
            {status.data && <span className="ml-auto text-[11px] text-slate-500">{status.data.sources_alive}/{status.data.sources_total} canlı · {totalRaces} yarış kaydı</span>}
          </header>
          {sources.isLoading ? (
            <div className="flex items-center justify-center gap-2 p-10 text-sm text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Karne yükleniyor</div>
          ) : sources.isError ? (
            <div className="p-10 text-center text-sm text-red-300">Karne alınamadı.</div>
          ) : (sources.data?.sources.length ?? 0) === 0 ? (
            <div className="p-10 text-center text-sm text-slate-500">Etkin kaynak yok.</div>
          ) : (
            <SourceTable rows={sources.data!.sources} />
          )}
          {(sources.data?.inactive.length ?? 0) > 0 && (
            <div className="border-t border-white/10 p-3 text-[11px] text-slate-500">
              <p className="mb-1 font-medium text-slate-400">Kapalı kaynaklar</p>
              {sources.data!.inactive.map((s) => <p key={s.id}>{s.name}: {s.reason}</p>)}
            </div>
          )}
          <p className="border-t border-white/10 p-3 text-[11px] leading-relaxed text-slate-500">
            Yalnız birden çok kaynağın canlı gördüğü haberler sayılır. Gecikme, kaynağın sorgu beklemesinden arındırılır. Karne yalnız bu kaynakları kıyaslar; dünyanın en hızlı haberini kanıtlamaz. * resmi akış değil.
          </p>
        </section>
      </div>
      <details className="rounded-xl border border-white/10 bg-slate-900/60">
        <summary className="cursor-pointer p-3 text-sm font-semibold text-slate-100">40 GitHub deposunun karnesi</summary>
        <RepoScorecard />
      </details>
    </div>
  );
}
