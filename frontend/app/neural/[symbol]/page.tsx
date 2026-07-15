"use client";

/**
 * NEURAL PANEL — sembol başına tek büyük komuta ekranı.
 * Core (elektronik beyin) + 6 model sinapsı + Tartışma Konseyi +
 * sinyal-dalga grafiği + formasyon penceresi. Çoklu dil (TR/EN).
 *
 * CANLI VERİ: lib/api/neural.ts üzerinden gerçek backend'e bağlanır
 * (fiyat, rejim, model oyları, VIX/makro, haber işaretleri, aktif sinyal,
 * mumlar + sinyal geçmişi). Ulaşılamayan her kaynak demo değerinde kalır —
 * header'daki sayaç kaç kaynağın canlı olduğunu gösterir.
 */

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  CalendarClock,
  Gauge,
  History,
  Layers,
  LineChart,
  Newspaper,
  Radio,
  Shapes,
  TrendingUp,
} from "lucide-react";

import ModelSynapses from "@/components/neural/ModelSynapses";
import NeuralNav from "@/components/neural/NeuralNav";
import DebateLayer from "@/components/neural/DebateLayer";
import ModelDetailModal, { type DetailKey } from "@/components/neural/ModelDetailModal";
import SignalHistoryChart from "@/components/neural/SignalHistoryChart";
import PatternsPanel, { mapLivePatterns } from "@/components/neural/PatternsPanel";
import { useHydrateLocale, useNeuralLocale, type LFn } from "@/components/neural/i18n";
import { useNeuralLive } from "@/lib/api/neural";
import {
  Comment,
  CoreLog,
  DecisionTimeline,
  IndicatorList,
  LevelLadder,
  MacroTiles,
  NeuralCard,
  NewsList,
  OilIntelPanel,
  PositionCalc,
  SessionStrip,
  VixGauge,
  WhaleCotPanel,
  type Dir,
  type IndicatorItem,
  type ModelVote,
  type NewsItem,
  type PriceLevel,
  type SessionInfo,
} from "@/components/neural/panels";

// ─────────────────────────────────────────────────────────────────────────
// Localized demo data factory (live values overlay on top)
// ─────────────────────────────────────────────────────────────────────────

interface SymbolData {
  slug: string;
  code: string;
  name: string;
  price: string;
  change: string;
  up: boolean;
  regime: { label: string; tone: "pos" | "neg" | "neutral"; comment: string };
  verdict: { dir: Dir; confidence: number };
  votes: ModelVote[];
  vix: { value: number; change: string; comment: string; tone: "pos" | "neg" | "neutral" };
  macro: { items: { label: string; value: string; change: string; up: boolean }[]; comment: string; tone: "pos" | "neg" | "neutral" };
  indicators: IndicatorItem[];
  levels: PriceLevel[];
  levelNote: string;
  news: NewsItem[];
  sessions: SessionInfo[];
  nextEvent: string;
  gateWarning?: string;
  log: { t: string; msg: string }[];
}

function makeNdx(L: LFn): SymbolData {
  return {
    slug: "ndx",
    code: "NDX.INDX",
    name: "NASDAQ 100",
    price: "21,847.2",
    change: "+0.84%",
    up: true,
    regime: {
      label: L("GÜÇLÜ YÜKSELİŞ TRENDİ", "STRONG UPTREND"),
      tone: "pos",
      comment: L(
        "Piyasa net bir yükseliş trendinde — geri çekilmeler alım fırsatı olarak değerlendiriliyor, SELL sinyalleri bastırılıyor.",
        "The market is in a clear uptrend — pullbacks are treated as buying opportunities and SELL signals are suppressed."
      ),
    },
    verdict: { dir: "BUY", confidence: 84 },
    votes: [
      { id: "ml", label: "ML · LightGBM", dir: "BUY", conf: 82, note: L("150+ göstergeden öğrenen model yukarı yönü destekliyor.", "The model trained on 150+ features backs the upside."), color: "#4f8cff" },
      { id: "emel", label: "EMEL", dir: "BUY", conf: 79, note: L("10 kontrol noktasından 8'i olumlu — güçlü stratejik onay.", "8 of 10 checkpoints positive — strong strategic approval."), color: "#a855f7" },
      { id: "pulse1", label: "PULSE 1", dir: "HOLD", conf: 0, note: L("Trend rejiminde scalp modeli devre dışı (tasarım gereği).", "Scalp model muted in trend regime (by design)."), color: "#fb923c" },
      { id: "pulse2", label: "PULSE 2", dir: "BUY", conf: 74, note: L("ML + teknik hibrit modeli momentumu teyit ediyor.", "The ML + technical hybrid confirms momentum."), color: "#f97316" },
      { id: "pulse3", label: "PULSE 3", dir: "BUY", conf: 68, note: L("5m / 1H / 4H üç zaman dilimi aynı yönde hizalı.", "5m / 1H / 4H all aligned in the same direction."), color: "#ea580c" },
      { id: "smc", label: "SMC / ICT", dir: "SELL", conf: 55, note: L("Üstte likidite bölgesi görüyor — tek muhalif ses, izlemede.", "Sees a liquidity zone above — the lone dissenter, watching."), color: "#14b8a6" },
    ],
    vix: {
      value: 16.4,
      change: L("−2.1% bugün", "−2.1% today"),
      comment: L(
        "Korku endeksi sakin bölgede — endeks trendleri için elverişli ortam, ani sert dönüş riski düşük.",
        "The fear index sits in the calm zone — friendly for index trends, low risk of a violent reversal."
      ),
      tone: "pos",
    },
    macro: {
      items: [
        { label: "DXY", value: "104.21", change: "0.08%", up: true },
        { label: "US10Y", value: "4.21%", change: "0.02", up: true },
        { label: "EURUSD", value: "1.0842", change: "0.12%", up: false },
      ],
      comment: L(
        "Dolar ve tahvil faizi hafif yukarı ama endeksi baskılayacak seviyede değil — makro rüzgar nötr.",
        "Dollar and yields drift up but not enough to pressure the index — macro wind is neutral."
      ),
      tone: "neutral",
    },
    indicators: [
      { name: "RSI (14)", value: "62", pct: 62, status: "ok", comment: L("Güçlü momentum, henüz aşırı alım bölgesinde değil.", "Strong momentum, not yet overbought.") },
      { name: "MACD", value: L("POZİTİF", "POSITIVE"), pct: 72, status: "ok", comment: L("Alıcılar kontrolde, histogram genişliyor.", "Buyers in control, histogram expanding.") },
      { name: "ADX (14)", value: "28", pct: 56, status: "ok", comment: L("Trend belirgin ve güçleniyor (25 üzeri = gerçek trend).", "Trend is clear and strengthening (above 25 = real trend).") },
      { name: "ATR %", value: "0.9%", pct: 30, status: "neutral", comment: L("Volatilite normal — stoplar standart mesafede güvenli.", "Volatility is normal — standard stop distances are safe.") },
      { name: L("EMA DİZİLİMİ", "EMA STACK"), value: "20>50>200", pct: 100, status: "ok", comment: L("Fiyat üç ortalamanın da üzerinde — ders kitabı yükseliş dizilimi.", "Price above all three averages — textbook bullish stack.") },
      { name: L("GÜNLÜK RANJ (ADR)", "DAILY RANGE (ADR)"), value: L("%62 kullanıldı", "62% used"), pct: 62, status: "warn", comment: L("Günün tipik hareketinin yarıdan fazlası tamamlandı — geç girişte hedef daralt.", "More than half of a typical day's move is done — trim targets on late entries.") },
    ],
    levels: [
      { price: "22,240", label: "Fib %161.8", kind: "resistance", distancePct: "+1.8%" },
      { price: "22,050", label: L("Dünkü yüksek", "Prev. high"), kind: "resistance", distancePct: "+0.9%" },
      { price: "21,910", label: "VAH", kind: "resistance", distancePct: "+0.3%" },
      { price: "21,760", label: "POC", kind: "support", distancePct: "−0.4%" },
      { price: "21,640", label: "VAL", kind: "support", distancePct: "−0.9%" },
      { price: "21,510", label: "EMA50 + Fib %38", kind: "support", distancePct: "−1.5%" },
    ],
    levelNote: L(
      "Fiyat, hacim profili tepesinin (VAH) hemen altında — 21,910 kırılırsa yol 22,050'ye açılır.",
      "Price sits just under the value-area high (VAH) — a break of 21,910 opens the road to 22,050."
    ),
    news: [
      { time: "16:42", title: L("Nvidia yeni AI çip ailesini duyurdu; teknoloji hisselerinde alım dalgası", "Nvidia unveils new AI chip family; tech stocks catch a bid"), sentiment: "pos", impact: 3, source: "Reuters" },
      { time: "15:10", title: L("Fed üyesi Waller: 'Enflasyon hedefe yaklaşıyor, faiz indirimi masada'", "Fed's Waller: 'Inflation nearing target, a cut is on the table'"), sentiment: "pos", impact: 3, source: "Bloomberg" },
      { time: "13:55", title: L("ABD 10 yıllık tahvil ihalesi beklentiden zayıf geçti", "US 10-year auction comes in weaker than expected"), sentiment: "neg", impact: 2, source: "CNBC" },
      { time: "11:30", title: L("Apple tedarik zinciri raporu: iPhone üretimi planlanan seviyede", "Apple supply-chain report: iPhone output on plan"), sentiment: "neu", impact: 1, source: "WSJ" },
    ],
    sessions: [
      { name: "SYD", open: false, range: "22-07" },
      { name: "TOK", open: false, range: "00-09" },
      { name: "LON", open: true, range: "08-17" },
      { name: "NY", open: true, range: "13:30-20" },
    ],
    nextEvent: L(
      "Londra–New York çakışması aktif: günün en likit saatleri. NY kapanışına 3s 12dk var.",
      "London–New York overlap active: the most liquid hours of the day. 3h 12m to NY close."
    ),
    gateWarning: L(
      "21:00'de FOMC üyesi konuşması — ±30 dk sinyal üretimi otomatik duraklatılacak (takvim kapısı).",
      "FOMC speaker at 21:00 — signal generation auto-pauses for ±30 min (calendar gate)."
    ),
    log: [
      { t: "16:45", msg: L("Ensemble taraması tamamlandı — 6/6 model yanıt verdi, karar: BUY %84", "Ensemble sweep complete — 6/6 models responded, verdict: BUY 84%") },
      { t: "16:44", msg: L("SMC muhalefeti not edildi: 21,910 üstünde likidite bölgesi işaretli", "SMC dissent noted: liquidity zone flagged above 21,910") },
      { t: "16:30", msg: L("VIX rejimi güncellendi: SAKİN (16.4) — trend stratejileri ağırlıkta", "VIX regime updated: CALM (16.4) — trend strategies weighted up") },
      { t: "16:15", msg: L("Haber etkisi işlendi: Nvidia duyurusu → pozitif momentum teyidi", "News impact processed: Nvidia headline → positive momentum confirmation") },
      { t: "15:45", msg: L("Aktif sinyal korunuyor: BUY 21,812 → anlık +35.2 puan", "Active signal held: BUY 21,812 → +35.2 points unrealized") },
    ],
  };
}

const CODES: Record<string, { code: string; name: (L: LFn) => string; price: string; change: string; up: boolean }> = {
  ndx: { code: "NDX.INDX", name: () => "NASDAQ 100", price: "21,847.2", change: "+0.84%", up: true },
  dax: { code: "GDAXI.INDX", name: () => "DAX 40", price: "24,186.5", change: "−0.31%", up: false },
  xauusd: { code: "XAUUSD", name: (L) => L("ALTIN / USD", "GOLD / USD"), price: "3,412.80", change: "+0.42%", up: true },
  usoil: { code: "USOIL.FOREX", name: (L) => L("WTI PETROL", "WTI CRUDE"), price: "68.42", change: "+1.12%", up: true },
};

const TIMELINE = [
  { t: "09:30", dir: "BUY" as Dir, conf: 72 },
  { t: "10:15", dir: "BUY" as Dir, conf: 78 },
  { t: "11:00", dir: "HOLD" as Dir, conf: 48 },
  { t: "13:30", dir: "BUY" as Dir, conf: 81 },
  { t: "15:45", dir: "BUY" as Dir, conf: 83 },
  { t: "16:45", dir: "BUY" as Dir, conf: 84 },
];

// ─────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────

export default function NeuralSymbolPage() {
  useHydrateLocale();
  const { L, locale } = useNeuralLocale();
  const params = useParams<{ symbol: string }>();
  const slug = (params?.symbol ?? "ndx").toLowerCase();
  const meta = CODES[slug] ?? CODES.ndx;

  const demo = useMemo(() => {
    const base = makeNdx(L);
    return { ...base, slug, code: meta.code, name: meta.name(L), price: meta.price, change: meta.change, up: meta.up };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale, slug]);

  const live = useNeuralLive(meta.code);
  const [detail, setDetail] = useState<DetailKey | null>(null);

  // ── live overlays (fall back to demo when a source is missing) ─────────
  const price = live.price?.text ?? demo.price;
  const changeText = live.price ? `${live.price.changePct >= 0 ? "+" : ""}${live.price.changePct.toFixed(2)}%` : demo.change;
  const up = live.price?.up ?? demo.up;

  const regimeLabel = live.regime
    ? live.regime.raw.replace(/_/g, " ").toUpperCase()
    : demo.regime.label;

  const regimeComment = useMemo(() => {
    if (!live.regime) return demo.regime.comment;
    const r = live.regime.raw.toUpperCase();
    if (r.includes("TREND_UP") || r.includes("UPTREND"))
      return L(
        "Piyasa net bir yükseliş trendinde — geri çekilmeler alım fırsatı olarak değerlendiriliyor, SELL sinyalleri bastırılıyor.",
        "The market is in a clear uptrend — pullbacks are treated as buying opportunities and SELL signals are suppressed."
      );
    if (r.includes("TREND_DOWN") || r.includes("DOWNTREND"))
      return L(
        "Piyasa düşüş trendinde — tepkiler satış fırsatı olarak değerlendiriliyor, BUY sinyalleri bastırılıyor.",
        "The market is in a downtrend — bounces are treated as selling opportunities and BUY signals are suppressed."
      );
    if (r.includes("RANG"))
      return L(
        "Piyasa yatay bantta — kenarlardan dönüş stratejileri öne çıkıyor, scalp modelinin ağırlığı artıyor.",
        "The market is ranging — mean-reversion off the edges leads, and the scalp model's weight increases."
      );
    return L(
      "Piyasa geçiş aşamasında — yön henüz net değil, sistem pozisyon boyutlarını küçük tutup teyit bekliyor.",
      "The market is in transition — direction isn't settled yet; the system keeps size small and waits for confirmation."
    );
  }, [live.regime, demo.regime.comment, L]);

  const votes: ModelVote[] = demo.votes.map((v) => {
    const lv = live.votes?.[v.id];
    return lv ? { ...v, dir: lv.dir as Dir, conf: lv.conf } : v;
  });

  // client-side ensemble from votes (until meta endpoint is wired)
  const verdict = useMemo(() => {
    if (!live.votes) return demo.verdict;
    let buy = 0, sell = 0, n = 0;
    for (const v of votes) {
      if (v.dir === "BUY") { buy += Math.max(v.conf, 40); n++; }
      if (v.dir === "SELL") { sell += Math.max(v.conf, 40); n++; }
    }
    if (!n) return { dir: "HOLD" as Dir, confidence: 50 };
    const dir: Dir = buy === sell ? "HOLD" : buy > sell ? "BUY" : "SELL";
    const confidence = Math.min(96, Math.round((Math.max(buy, sell) / (buy + sell)) * 100));
    return { dir, confidence };
  }, [live.votes, votes, demo.verdict]);

  const vix = live.vix
    ? { ...demo.vix, value: live.vix.value, change: live.vix.changeText }
    : demo.vix;
  const macroItems = live.macroTiles?.length ? live.macroTiles : demo.macro.items;

  const news: NewsItem[] = live.news?.length
    ? live.news.map((n) => ({
        time: n.time,
        title: locale === "tr" ? n.title : n.titleEn || n.title,
        sentiment: n.sentiment,
        impact: n.impact,
        source: n.source,
      }))
    : demo.news;

  const activeOverlay = live.active
    ? { dir: live.active.dir as any, entry: live.active.entry, tps: live.active.tps, sl: live.active.sl }
    : live.active === null
    ? null
    : undefined; // undefined → chart uses its demo overlay

  const chartCandles = live.candles?.map(({ o, h, l, c }) => ({ o, h, l, c }));
  const chartSegments = live.segments;
  const slPoints = live.active && live.active.entry && live.active.sl
    ? Math.max(1, Math.round(Math.abs(live.active.entry - live.active.sl)))
    : 122;

  // live chart patterns → DetectedPattern list for PatternsPanel
  const livePatterns = useMemo(() => {
    if (!live.patterns?.length || !live.patternCandles?.length) return undefined;
    const mapped = mapLivePatterns(live.patterns, live.patternCandles);
    return mapped.length ? mapped : undefined;
  }, [live.patterns, live.patternCandles]);

  // indicators: overlay live RSI / EMA stack / trend onto the demo list
  const indicators = useMemo(() => {
    const list = demo.indicators.map((it) => ({ ...it }));
    const ta = live.ta;
    if (!ta) return list;
    if (ta.rsi14 !== undefined) {
      const rsiComment =
        ta.rsi14 >= 70
          ? L("Aşırı alım bölgesi — geri çekilme riski artıyor.", "Overbought zone — pullback risk rising.")
          : ta.rsi14 <= 30
          ? L("Aşırı satım bölgesi — tepki yükselişi gelebilir.", "Oversold zone — a relief bounce may come.")
          : ta.rsi14 >= 55
          ? L("Güçlü momentum, henüz aşırı alım bölgesinde değil.", "Strong momentum, not yet overbought.")
          : ta.rsi14 >= 45
          ? L("Momentum nötr — piyasa yön arıyor.", "Momentum neutral — the market seeks direction.")
          : L("Momentum zayıf — satıcılar hafif önde.", "Momentum weak — sellers slightly ahead.");
      list[0] = {
        ...list[0],
        value: String(ta.rsi14),
        pct: ta.rsi14,
        status: ta.rsi14 >= 70 || ta.rsi14 <= 30 ? "warn" : ta.rsi14 >= 55 ? "ok" : "neutral",
        comment: rsiComment,
      };
    }
    if (ta.emaText) {
      list[4] = {
        ...list[4],
        value: ta.emaText,
        pct: ta.emaBullStack ? 100 : ta.emaText.includes("▼") ? 10 : 50,
        status: ta.emaBullStack ? "ok" : ta.emaText.includes("▼") ? "bad" : "warn",
        comment: ta.emaBullStack
          ? L("Fiyat üç ortalamanın da üzerinde — ders kitabı yükseliş dizilimi.", "Price above all three averages — textbook bullish stack.")
          : ta.emaText.includes("▼")
          ? L("Fiyat ortalamaların altında — düşüş dizilimi hâkim.", "Price below the averages — bearish stack dominates.")
          : L("Ortalamalar iç içe — net dizilim yok, geçiş bölgesi.", "Averages intertwined — no clean stack, transition zone."),
      };
    }
    return list;
  }, [demo.indicators, live.ta, L]);

  const liveCount = live.sourcesOk;

  return (
    <div className="min-h-screen bg-[#05070d] text-white font-sans">
      {/* ambient backdrop */}
      <div className="pointer-events-none fixed inset-0" aria-hidden>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(34,211,238,0.08),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_40%_at_80%_110%,rgba(168,85,247,0.05),transparent)]" />
      </div>

      {/* ── Ana sekme çubuğu + sembol alt-başlığı ───────────────────── */}
      <NeuralNav />
      <header className="border-b border-white/[0.05] bg-[#070b14]/70 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-x-5 gap-y-2 px-4 py-2.5 md:px-8">
          <div className="flex items-center gap-3">
            <BrainCircuit size={16} className="text-cyan-400" />
            <div>
              <div className="text-sm font-bold tracking-wide">{demo.name}</div>
              <div className="font-mono text-[9px] tracking-[0.25em] text-gray-600">{demo.code} · NEURAL PANEL</div>
            </div>
          </div>

          <div className="flex items-baseline gap-2.5">
            <motion.span key={price} initial={{ opacity: 0.4 }} animate={{ opacity: 1 }} className="font-mono text-xl font-bold text-white">
              {price}
            </motion.span>
            <span className={`font-mono text-sm ${up ? "text-emerald-400" : "text-red-400"}`}>
              {up ? "▲" : "▼"} {changeText}
            </span>
          </div>

          {/* sistem nabzı + canlı kaynak sayacı */}
          <div className="ml-auto hidden md:flex items-center gap-4 rounded-full border border-white/[0.06] bg-white/[0.02] px-4 py-2">
            <span className="flex items-center gap-1.5">
              <motion.span
                className={`h-1.5 w-1.5 rounded-full ${liveCount > 0 ? "bg-emerald-400" : "bg-amber-400"}`}
                animate={{ opacity: [1, 0.35, 1] }}
                transition={{ repeat: Infinity, duration: 2.2 }}
              />
              <span className="font-mono text-[9px] tracking-[0.2em] text-gray-500">
                {live.loading
                  ? L("BAĞLANIYOR…", "CONNECTING…")
                  : `${L("CANLI KAYNAK", "LIVE SOURCES")} ${liveCount}/${live.sourcesTotal}`}
              </span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`h-1.5 w-1.5 rounded-full ${liveCount > 0 ? "bg-emerald-400" : "bg-gray-700"}`} />
              <span className="font-mono text-[9px] tracking-[0.2em] text-gray-500">MT5</span>
            </span>
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-[1500px] px-4 pb-16 md:px-8">
        {/* ── THE CORE ────────────────────────────────────────────────── */}
        <section className="pt-10 pb-6 md:pt-14">
          <div className="mb-8 text-center">
            <motion.p
              initial={{ opacity: 0, letterSpacing: "0.8em" }}
              animate={{ opacity: 1, letterSpacing: "0.45em" }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              className="font-mono text-[10px] uppercase text-cyan-500/70"
            >
              {L("Yapay Zekâ Çekirdeği", "Artificial Intelligence Core")}
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.8 }}
              className="mt-2 text-2xl md:text-3xl font-light text-gray-300"
            >
              {L("6 model analiz etti, ", "6 models analyzed, the ")}
              <span className="font-bold text-white">Core</span>
              {L(" kararını verdi", " made the call")}
            </motion.h1>
          </div>

          <ModelSynapses
            votes={votes}
            direction={verdict.dir}
            confidence={verdict.confidence}
            onSelect={(id) => setDetail(id as DetailKey)}
          />

          {/* regime banner */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.7 }}
            className="mx-auto mt-8 max-w-3xl rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.05] px-5 py-4 text-center"
          >
            <div className="font-mono text-[10px] tracking-[0.3em] text-emerald-400 mb-1">
              {L("PİYASA REJİMİ", "MARKET REGIME")} · {regimeLabel}
            </div>
            <p className="text-[13px] font-light text-gray-400 leading-relaxed">{regimeComment}</p>
          </motion.div>

          {/* Tartışma Konseyi — CIO bias'ı Core'a akar */}
          <div className="mt-10">
            <DebateLayer onOpen={() => setDetail("debate")} live={live.debate} />
          </div>
        </section>

        {/* ── Row 0: Bugünün karar akışı ─────────────────────────────── */}
        <NeuralCard title={L("Bugünün Karar Akışı", "Today's Decision Flow")} icon={<History size={14} />} live>
          <DecisionTimeline points={TIMELINE} />
        </NeuralCard>

        {/* ── Row 1: VIX · Makro · Seans ─────────────────────────────── */}
        <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          <NeuralCard title={L("VIX — Korku Endeksi", "VIX — Fear Index")} icon={<Gauge size={14} />} live>
            <VixGauge {...vix} />
          </NeuralCard>

          <NeuralCard title={L("Makro Ortam", "Macro Environment")} icon={<Activity size={14} />} live delay={0.1}>
            <MacroTiles items={macroItems} comment={demo.macro.comment} tone={demo.macro.tone} />
          </NeuralCard>

          <NeuralCard title={L("Seanslar & Takvim", "Sessions & Calendar")} icon={<CalendarClock size={14} />} delay={0.2} className="md:col-span-2 xl:col-span-1">
            <SessionStrip sessions={demo.sessions} nextEvent={demo.nextEvent} gateWarning={demo.gateWarning} />
          </NeuralCard>
        </div>

        {/* ── Row 2: Göstergeler · Seviyeler ─────────────────────────── */}
        <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
          <NeuralCard title={L("Göstergeler — Tek Bakışta", "Indicators — At a Glance")} icon={<TrendingUp size={14} />} live>
            <IndicatorList items={indicators} />
          </NeuralCard>

          <NeuralCard title={L("Kritik Seviyeler", "Key Levels")} icon={<Layers size={14} />} live delay={0.1}>
            <LevelLadder levels={demo.levels} price={price} priceNote={demo.levelNote} />
          </NeuralCard>
        </div>

        {/* ── Row 3: SİNYAL GRAFİĞİ (yeni aktif sinyal paneli) ───────── */}
        <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[2fr_1fr]">
          <NeuralCard title={L("Sinyal Haritası — Sistem Ne Zaman Ne Dedi?", "Signal Map — What Did The System Say, When?")} icon={<LineChart size={14} />} live>
            <SignalHistoryChart
              candles={chartCandles}
              segments={chartSegments as any}
              active={activeOverlay as any}
              isLive={Boolean(chartCandles && chartSegments)}
            />
          </NeuralCard>

          <NeuralCard title={L("Risk & Pozisyon", "Risk & Position")} icon={<Shapes size={14} />} delay={0.1}>
            {live.active && (
              <div className="mb-4 flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3">
                <span className={`font-mono text-xs font-bold tracking-[0.15em] ${live.active.dir === "BUY" ? "text-emerald-300" : "text-red-300"}`}>
                  {live.active.dir === "BUY" ? "▲ BUY" : "▼ SELL"} · %{live.active.conf}
                </span>
                <span className="font-mono text-[9px] tracking-[0.2em] text-gray-600 uppercase">{live.active.model}</span>
              </div>
            )}
            <PositionCalc
              slPoints={slPoints}
              symbolNote={L(
                "Demo varsayımı: 1 lot ≈ 1$/puan. Canlıda sembolün gerçek pip değeriyle hesaplanır.",
                "Demo assumption: 1 lot ≈ $1/point. Live uses the symbol's real pip value."
              )}
            />
          </NeuralCard>
        </div>

        {/* ── Row 4: Haberler · Formasyonlar ─────────────────────────── */}
        <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
          <NeuralCard title={L(`${demo.name} Haber Akışı`, `${demo.name} News Feed`)} icon={<Newspaper size={14} />} live>
            <NewsList items={news} />
            <Comment>
              {L("Sarı noktalar etki gücü — 3 nokta piyasayı oynatabilecek haber demek.", "Amber dots show impact — 3 dots means a market-moving headline.")}
            </Comment>
          </NeuralCard>

          <NeuralCard title={L("Tespit Edilen Formasyonlar", "Detected Patterns")} icon={<Shapes size={14} />} live delay={0.1}>
            <PatternsPanel live={livePatterns} />
          </NeuralCard>
        </div>

        {/* ── Row 4.5: Sembol-özel istihbarat ────────────────────────── */}
        {(live.whale || live.oil) && (
          <div className={`mt-5 grid grid-cols-1 gap-5 ${live.whale && live.oil ? "xl:grid-cols-2" : ""}`}>
            {live.whale && (
              <NeuralCard title={L("Kurumsal Konum — COT & Whale", "Institutional Positioning — COT & Whale")} icon={<Activity size={14} />} live>
                <WhaleCotPanel
                  pressure={live.whale.pressure}
                  label={live.whale.label}
                  specLongPct={live.whale.specLongPct}
                  specNet={live.whale.specNet}
                  commNet={live.whale.commNet}
                />
              </NeuralCard>
            )}
            {live.oil && (
              <NeuralCard title={L("Tanker & Fiziksel Piyasa İstihbaratı", "Tanker & Physical Market Intelligence")} icon={<Radio size={14} />} live delay={0.1}>
                <OilIntelPanel {...live.oil} />
              </NeuralCard>
            )}
          </div>
        )}

        {/* ── Row 5: Core günlüğü ────────────────────────────────────── */}
        <div className="mt-5">
          <NeuralCard title={L("Core Günlüğü — Beyin Ne Yapıyor?", "Core Log — What Is The Brain Doing?")} icon={<Radio size={14} />}>
            <CoreLog lines={demo.log} />
            <Comment>{L("Sistemin arka planda attığı her adım burada — kara kutu yok.", "Every step the system takes is here — no black box.")}</Comment>
          </NeuralCard>
        </div>

        {/* durum notu */}
        <p className="mt-10 text-center font-mono text-[10px] tracking-[0.25em] text-gray-700">
          {live.loading
            ? L("CANLI KAYNAKLARA BAĞLANIYOR…", "CONNECTING TO LIVE SOURCES…")
            : liveCount > 0
            ? L(`CANLI VERİ AKTİF — ${liveCount}/${live.sourcesTotal} KAYNAK · KALANLAR DEMO`, `LIVE DATA ACTIVE — ${liveCount}/${live.sourcesTotal} SOURCES · REST IS DEMO`)
            : L("BACKEND KAPALI — TÜM VERİLER DEMO", "BACKEND OFFLINE — ALL DATA IS DEMO")}
        </p>
      </main>

      {/* detay pencereleri */}
      <ModelDetailModal open={detail} onClose={() => setDetail(null)} debateLive={live.debate} />
    </div>
  );
}
