"use client";

/**
 * ModelDetailModal — click any vote card (or the debate council) and a
 * detail window opens: SMC gets a structure chart (order block, FVG,
 * BOS, liquidity), ML gets feature importances, EMEL its 10-check list,
 * PULSE a timeframe matrix, the council a transcript. Fully localized.
 */

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { DEBATE_AGENTS, CIO_VERDICT, biasWord } from "./DebateLayer";
import { useNeuralLocale, type LFn } from "./i18n";
import type { LiveDebate } from "@/lib/api/neural";

export type DetailKey = "ml" | "emel" | "pulse1" | "pulse2" | "pulse3" | "smc" | "debate";

// ─────────────────────────────────────────────────────────────────────────
// SMC structure chart (mock candles + zones)
// ─────────────────────────────────────────────────────────────────────────

type C = { o: number; h: number; l: number; c: number };
const SMC_CANDLES: C[] = [
  { o: 100, h: 102, l: 99, c: 101.5 }, { o: 101.5, h: 103.2, l: 101, c: 102.8 },
  { o: 102.8, h: 104, l: 102.2, c: 103.6 }, { o: 103.6, h: 105.5, l: 103.2, c: 105 },
  { o: 105, h: 106.2, l: 104.4, c: 105.8 }, { o: 105.8, h: 106.5, l: 104.8, c: 105.2 },
  { o: 105.2, h: 105.6, l: 103.8, c: 104.2 }, { o: 104.2, h: 104.8, l: 102.9, c: 103.3 },
  { o: 103.3, h: 103.9, l: 102.2, c: 102.6 }, { o: 102.6, h: 103.4, l: 102.1, c: 103.1 },
  { o: 103.1, h: 104.6, l: 102.9, c: 104.3 }, { o: 104.3, h: 105.8, l: 104, c: 105.5 },
  { o: 105.5, h: 107.2, l: 105.2, c: 106.9 }, { o: 106.9, h: 108.4, l: 106.5, c: 108 },
  { o: 108, h: 108.6, l: 106.8, c: 107.2 }, { o: 107.2, h: 107.8, l: 106.2, c: 106.6 },
  { o: 106.6, h: 107.4, l: 106.3, c: 107.1 }, { o: 107.1, h: 108.8, l: 106.9, c: 108.5 },
  { o: 108.5, h: 109.6, l: 108.1, c: 109.2 }, { o: 109.2, h: 110.4, l: 108.9, c: 110 },
];

function SmcChart() {
  const { L } = useNeuralLocale();
  const W = 580, H = 240, PAD = 10;
  const lo = Math.min(...SMC_CANDLES.map((c) => c.l)) - 0.8;
  const hi = Math.max(...SMC_CANDLES.map((c) => c.h)) + 1.2;
  const y = (p: number) => PAD + (1 - (p - lo) / (hi - lo)) * (H - PAD * 2);
  const cw = (W - PAD * 2) / SMC_CANDLES.length;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label={L("SMC yapı grafiği", "SMC structure chart")}>
      <motion.rect
        x={PAD + 7.6 * cw} y={y(103.4)} width={cw * 3.4} height={y(102.1) - y(103.4)}
        fill="rgba(20,184,166,0.13)" stroke="#14b8a6" strokeOpacity="0.5" strokeDasharray="4 3" strokeWidth="1"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}
      />
      <motion.text x={PAD + 7.8 * cw} y={y(102.1) + 14} fill="#2dd4bf" fontSize="9" fontFamily="monospace" letterSpacing="0.1em"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.85 }}>
        {L("ORDER BLOCK — talep bölgesi", "ORDER BLOCK — demand zone")}
      </motion.text>

      <motion.rect
        x={PAD + 12.1 * cw} y={y(106.5)} width={cw * 2.2} height={y(105.5) - y(106.5)}
        fill="rgba(168,85,247,0.13)" stroke="#a855f7" strokeOpacity="0.45" strokeDasharray="3 3" strokeWidth="1"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
      />
      <motion.text x={PAD + 12.2 * cw} y={y(106.5) - 5} fill="#c084fc" fontSize="9" fontFamily="monospace" letterSpacing="0.1em"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}>
        FVG
      </motion.text>

      <motion.line x1={PAD + 4 * cw} x2={PAD + 14.5 * cw} y1={y(106.2)} y2={y(106.2)}
        stroke="#22d3ee" strokeOpacity="0.55" strokeWidth="1" strokeDasharray="6 4"
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.2, duration: 0.6 }}
      />
      <motion.text x={PAD + 4 * cw} y={y(106.2) - 6} fill="#22d3ee" fontSize="9" fontFamily="monospace" letterSpacing="0.1em"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.4 }}>
        {L("BOS ↗ yapı kırılımı", "BOS ↗ break of structure")}
      </motion.text>

      <motion.line x1={PAD + 13 * cw} x2={W - PAD} y1={y(110.6)} y2={y(110.6)}
        stroke="#f87171" strokeOpacity="0.6" strokeWidth="1" strokeDasharray="2 4"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}
      />
      <motion.text x={PAD + 13.2 * cw} y={y(110.6) - 5} fill="#f87171" fontSize="9" fontFamily="monospace" letterSpacing="0.1em"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }}>
        {L("LİKİDİTE HAVUZU (stoplar)", "LIQUIDITY POOL (stops)")}
      </motion.text>

      {SMC_CANDLES.map((c, i) => {
        const x = PAD + i * cw + cw / 2;
        const up = c.c >= c.o;
        const col = up ? "#34d399" : "#f87171";
        return (
          <motion.g key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03, duration: 0.3 }}>
            <line x1={x} x2={x} y1={y(c.h)} y2={y(c.l)} stroke={col} strokeOpacity="0.8" strokeWidth="1" />
            <rect x={x - cw * 0.28} y={y(Math.max(c.o, c.c))} width={cw * 0.56} height={Math.max(1.5, Math.abs(y(c.o) - y(c.c)))} fill={col} fillOpacity="0.85" rx="1" />
          </motion.g>
        );
      })}
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Detail bodies
// ─────────────────────────────────────────────────────────────────────────

const ML_FEATURES = [
  { tr: "VIX rejimi", en: "VIX regime", w: 92 },
  { tr: "EMA200'e uzaklık", en: "Distance to EMA200", w: 78 },
  { tr: "RSI (4h)", en: "RSI (4h)", w: 64 },
  { tr: "Hacim z-skoru", en: "Volume z-score", w: 55 },
  { tr: "DXY korelasyonu", en: "DXY correlation", w: 41 },
  { tr: "Seans saati", en: "Session hour", w: 33 },
];

function MlDetail() {
  const { L } = useNeuralLocale();
  return (
    <div>
      <p className="text-[13px] font-light text-gray-400 mb-5 leading-relaxed">
        {L("LightGBM, her tikte", "LightGBM reads")}{" "}
        <span className="text-white">{L("150+ mühendislik özelliği", "150+ engineered features")}</span>{" "}
        {L("okur. Bugünkü kararı en çok etkileyen girdiler:", "per tick. Today's decision was driven most by:")}
      </p>
      <div className="space-y-3.5">
        {ML_FEATURES.map((f, i) => (
          <div key={f.en}>
            <div className="flex justify-between mb-1">
              <span className="font-mono text-[11px] text-gray-300">{L(f.tr, f.en)}</span>
              <span className="font-mono text-[11px] text-blue-300">{(f.w / 100).toFixed(2)}</span>
            </div>
            <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
              <motion.div className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-300"
                initial={{ width: 0 }} animate={{ width: `${f.w}%` }} transition={{ delay: 0.15 + i * 0.08, duration: 0.7 }} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 grid grid-cols-3 gap-3">
        {[
          { v: "%61", l: L("30g isabet", "30d accuracy") },
          { v: "49", l: L("sinyal / 30g", "signals / 30d") },
          { v: "BUY %82", l: L("bugünkü oy", "today's vote") },
        ].map((s) => (
          <div key={s.l} className="rounded-xl border border-white/[0.06] bg-white/[0.02] py-3 text-center">
            <div className="font-mono text-sm font-bold text-white">{s.v}</div>
            <div className="font-mono text-[9px] tracking-[0.2em] text-gray-600 mt-0.5">{s.l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const EMEL_CHECKS = [
  { tr: "Trend yönü (EMA çapraz)", en: "Trend direction (EMA cross)", pass: true, w: 25 },
  { tr: "Çoklu zaman dilimi uyumu", en: "Multi-timeframe alignment", pass: true, w: 20 },
  { tr: "Piyasa rejimi uygunluğu", en: "Market regime fit", pass: true, w: 15 },
  { tr: "Momentum (RSI + MACD)", en: "Momentum (RSI + MACD)", pass: true, w: 20 },
  { tr: "Hacim teyidi", en: "Volume confirmation", pass: false, w: 15 },
  { tr: "Destek/Direnç konumu", en: "Support/Resistance position", pass: true, w: 10 },
  { tr: "Mum formasyonu", en: "Candle pattern", pass: true, w: 15 },
  { tr: "Makro filtre (DXY/VIX)", en: "Macro filter (DXY/VIX)", pass: true, w: 5 },
  { tr: "Seans filtresi", en: "Session filter", pass: true, w: 0 },
  { tr: "Haber kapısı (±30dk)", en: "News gate (±30min)", pass: false, w: 0 },
];

function EmelDetail() {
  const { L } = useNeuralLocale();
  return (
    <div>
      <p className="text-[13px] font-light text-gray-400 mb-5 leading-relaxed">
        {L("EMEL bir sinyali ancak", "EMEL only approves a signal when its")}{" "}
        <span className="text-white">{L("10 kontrol noktasından", "10 checkpoints")}</span>{" "}
        {L("yeterli ağırlıklı puan toplarsa onaylar. Bugün:", "collect enough weighted score. Today:")}{" "}
        <span className="text-emerald-300 font-mono">{L("8/10 olumlu → BUY %79", "8/10 positive → BUY 79%")}</span>
      </p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {EMEL_CHECKS.map((c, i) => (
          <motion.div key={c.en}
            initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}
            className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 ${
              c.pass ? "border-emerald-500/20 bg-emerald-500/[0.04]" : "border-red-500/20 bg-red-500/[0.04]"
            }`}
          >
            <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
              c.pass ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"
            }`}>
              {c.pass ? "✓" : "✗"}
            </span>
            <span className="text-[12px] text-gray-300 flex-1">{L(c.tr, c.en)}</span>
            {c.w > 0 && <span className="font-mono text-[9px] text-gray-600">{c.w}p</span>}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function PulseDetail({ variant }: { variant: "pulse1" | "pulse2" | "pulse3" }) {
  const { L } = useNeuralLocale();
  if (variant === "pulse1") {
    return (
      <div>
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-5 text-center mb-5">
          <div className="font-mono text-lg font-bold text-gray-400 mb-1">{L("DEVRE DIŞI", "DISABLED")}</div>
          <p className="text-[12px] font-light text-gray-500">
            {L("PULSE 1 bir", "PULSE 1 is a")}{" "}
            <span className="text-gray-300">{L("yatay piyasa (ranging) uzmanı", "ranging-market specialist")}</span>.{" "}
            {L(
              "Güçlü trend rejiminde scalp sinyalleri zarar ürettiği için sistem onu otomatik susturur — bu bir hata değil, tasarım.",
              "In strong trend regimes its scalp signals lose money, so the system mutes it automatically — that's design, not a bug."
            )}
          </p>
        </div>
        <p className="text-[12px] font-light text-gray-500 leading-relaxed">
          {L(
            "Rejim RANGING'e dönerse ağırlığı %40'a çıkar ve 6 bileşenli momentum skoruyla (EMA, RSI, hacim, mikro-yapı) yeniden devreye girer.",
            "When the regime turns RANGING its weight rises to 40% and it re-engages with a 6-component momentum score (EMA, RSI, volume, micro-structure)."
          )}
        </p>
      </div>
    );
  }
  const tf = variant === "pulse3"
    ? [
        { n: "5m", dir: "▲", tr: "kısa vade güçlü", en: "short-term strong" },
        { n: "1H", dir: "▲", tr: "ana trend yukarı", en: "main trend up" },
        { n: "4H", dir: "▲", tr: "yapı sağlam", en: "structure intact" },
      ]
    : [
        { n: "M5", dir: "▲", tr: "momentum pozitif", en: "momentum positive" },
        { n: "M15", dir: "▲", tr: "EMA üstünde", en: "above EMA" },
        { n: "M30", dir: "▬", tr: "nötr, izlemede", en: "neutral, watching" },
      ];
  return (
    <div>
      <p className="text-[13px] font-light text-gray-400 mb-5 leading-relaxed">
        {variant === "pulse3"
          ? L(
              "PULSE 3 üç zaman dilimini katmanlı ağırlıkla birleştirir — trend rejiminde 4H %40, 1H %35, 5m %25.",
              "PULSE 3 blends three timeframes with layered weights — in trend regimes 4H 40%, 1H 35%, 5m 25%."
            )
          : L(
              "PULSE 2, ML skorunu klasik teknik teyitle (EMA momentum) harmanlayan hibrit motordur.",
              "PULSE 2 is the hybrid engine blending the ML score with classic technical confirmation (EMA momentum)."
            )}
      </p>
      <div className="grid grid-cols-3 gap-3">
        {tf.map((t, i) => (
          <motion.div key={t.n}
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.12 }}
            className={`rounded-xl border p-4 text-center ${t.dir === "▲" ? "border-emerald-500/25 bg-emerald-500/[0.05]" : "border-white/10 bg-white/[0.03]"}`}
          >
            <div className="font-mono text-[10px] tracking-[0.25em] text-gray-500 mb-1">{t.n}</div>
            <div className={`text-2xl font-bold ${t.dir === "▲" ? "text-emerald-400" : "text-gray-500"}`}>{t.dir}</div>
            <div className="mt-1 text-[10px] font-light text-gray-500">{L(t.tr, t.en)}</div>
          </motion.div>
        ))}
      </div>
      <div className="mt-5 rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3">
        <span className="font-mono text-[11px] text-gray-400">
          {L("Hizalanma", "Alignment")}:{" "}
          <span className="text-emerald-300 font-bold">
            {variant === "pulse3" ? L("3/3 yukarı", "3/3 up") : L("2/3 yukarı", "2/3 up")}
          </span>{" "}
          → {L("oy", "vote")} {variant === "pulse3" ? "BUY %68" : "BUY %74"}
        </span>
      </div>
    </div>
  );
}

function SmcDetail() {
  const { L } = useNeuralLocale();
  return (
    <div>
      <p className="text-[13px] font-light text-gray-400 mb-4 leading-relaxed">
        {L("SMC motoru kurumsal ayak izini arar:", "The SMC engine hunts institutional footprints:")}{" "}
        <span className="text-teal-300">order block</span>{L("'tan dönüş,", " reversal,")}{" "}
        <span className="text-purple-300">FVG</span> {L("boşluğu ve", "gap and a")}{" "}
        <span className="text-cyan-300">BOS</span>{" "}
        {L("kırılımı yukarı yapıyı doğruluyor — ama fiyatın üstünde", "break confirm the bullish structure — but above price it sees a")}{" "}
        <span className="text-red-300">{L("likidite havuzu", "liquidity pool")}</span>{" "}
        {L("görüyor. Bu yüzden oyu", "That's why its vote is")}{" "}
        <span className="font-mono text-red-300">SELL %55</span>:{" "}
        {L("“önce stoplar süpürülebilir.”", "“stops may get swept first.”")}
      </p>
      <div className="rounded-xl border border-white/[0.06] bg-black/40 p-3">
        <SmcChart />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { l: "Order Block", v: "21.760-790", c: "text-teal-300" },
          { l: "FVG", v: "21.802-818", c: "text-purple-300" },
          { l: "BOS", v: "21.795 ↗", c: "text-cyan-300" },
          { l: L("Likidite", "Liquidity"), v: "21.910+", c: "text-red-300" },
        ].map((z) => (
          <div key={z.l} className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2.5 text-center">
            <div className="font-mono text-[9px] tracking-[0.2em] text-gray-600">{z.l}</div>
            <div className={`font-mono text-[12px] mt-0.5 ${z.c}`}>{z.v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DebateDetail({ live }: { live?: LiveDebate }) {
  const { L } = useNeuralLocale();
  const flow = [
    ...DEBATE_AGENTS.map((a) => ({ who: a.name, side: a.side as "bull" | "bear" | "cio", text: a.arg(L) })),
    {
      who: L("Likidite Avcısı → çürütme", "Liquidity Hunter → rebuttal"),
      side: "bear" as const,
      text: L(
        "Boğaların POC desteği güçlü ama 21.910 süpürülmeden rahat yükseliş beklemem.",
        "The bulls' POC support is strong, but I don't expect a clean rally before 21,910 gets swept."
      ),
    },
    {
      who: L("Teknik Boğa → cevap", "Technical Bull → response"),
      side: "bull" as const,
      text: L(
        "Süpürme olsa bile OB 21.760 tutar — yapı bozulmaz, alım fırsatı olur.",
        "Even with a sweep, the 21,760 OB should hold — structure survives and it becomes a buy."
      ),
    },
    {
      who: live ? `CIO · ${live.date ?? ""} ${live.label}` : "CIO",
      side: "cio" as const,
      text: live
        ? `${L("Nihai karar", "Final call")}: ${biasWord(live.bias, L).word}, ${L("güven", "confidence")} %${live.conf}${live.mode ? ` · ${live.mode.replace(/_/g, " ")}` : ""}. ${live.reason}`
        : `${L("Nihai karar", "Final call")}: ${CIO_VERDICT.bias(L)} bias, ${L("güven", "confidence")} %${CIO_VERDICT.conf}. ${L("Geçersizleşme", "Invalidation")}: ${CIO_VERDICT.invalidation(L)}. ${L(
            "Yapı ajanları (SMC/kanal/formasyon) destek seviyelerini teyit etti.",
            "Structure agents (SMC/channel/patterns) confirmed the support levels."
          )}`,
    },
  ];
  const style = {
    bull: "border-emerald-500/25 bg-emerald-500/[0.05]",
    bear: "border-red-500/25 bg-red-500/[0.05] ml-auto",
    cio: "border-amber-500/30 bg-amber-500/[0.06] mx-auto",
  };
  return (
    <div className="space-y-3">
      {flow.map((m, i) => (
        <motion.div key={i}
          initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
          className={`max-w-[85%] rounded-xl border px-4 py-3 ${style[m.side]}`}
        >
          <div className="font-mono text-[9px] tracking-[0.2em] text-gray-500 mb-1 uppercase">{m.who}</div>
          <p className="text-[12px] font-light text-gray-300 leading-relaxed">“{m.text}”</p>
        </motion.div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Modal shell
// ─────────────────────────────────────────────────────────────────────────

function buildMeta(L: LFn): Record<DetailKey, { title: string; badge: string; badgeCls: string; color: string }> {
  return {
    ml: { title: L("ML · LightGBM — Nöral Motor", "ML · LightGBM — Neural Engine"), badge: "BUY %82", badgeCls: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10", color: "#4f8cff" },
    emel: { title: L("EMEL — 10 Kontrollü Stratejist", "EMEL — 10-Check Strategist"), badge: "BUY %79", badgeCls: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10", color: "#a855f7" },
    pulse1: { title: L("PULSE 1 — Scalp Motoru", "PULSE 1 — Scalp Engine"), badge: "HOLD", badgeCls: "text-gray-400 border-white/15 bg-white/[0.05]", color: "#fb923c" },
    pulse2: { title: L("PULSE 2 — ML + Teknik Hibrit", "PULSE 2 — ML + Technical Hybrid"), badge: "BUY %74", badgeCls: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10", color: "#f97316" },
    pulse3: { title: L("PULSE 3 — Çoklu Zaman Dilimi", "PULSE 3 — Multi-Timeframe"), badge: "BUY %68", badgeCls: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10", color: "#ea580c" },
    smc: { title: L("SMC / ICT — Akıllı Para Yapısı", "SMC / ICT — Smart Money Structure"), badge: "SELL %55", badgeCls: "text-red-300 border-red-500/40 bg-red-500/10", color: "#14b8a6" },
    debate: { title: L("Tartışma Konseyi — Tam Transkript", "Debate Council — Full Transcript"), badge: `${CIO_VERDICT.bias(L)} %${CIO_VERDICT.conf}`, badgeCls: "text-amber-300 border-amber-500/40 bg-amber-500/10", color: "#fbbf24" },
  };
}

export default function ModelDetailModal({
  open,
  onClose,
  debateLive,
}: {
  open: DetailKey | null;
  onClose: () => void;
  debateLive?: LiveDebate;
}) {
  const { L } = useNeuralLocale();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const meta = open ? { ...buildMeta(L)[open] } : null;
  if (meta && open === "debate" && debateLive) {
    meta.badge = `${biasWord(debateLive.bias, L).word} %${debateLive.conf}`;
  }

  return (
    <AnimatePresence>
      {open && meta && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="fixed inset-0 z-[90] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4"
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-label={meta.title}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 26 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 14 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-2xl max-h-[86vh] overflow-y-auto rounded-2xl border border-white/10 bg-[#080c16]"
            style={{ boxShadow: `0 0 60px -20px ${meta.color}55, 0 50px 120px -30px rgba(0,0,0,1)` }}
          >
            <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-white/[0.07] bg-[#080c16]/95 backdrop-blur px-5 py-4">
              <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: meta.color, boxShadow: `0 0 10px ${meta.color}` }} />
              <h2 className="text-sm font-bold tracking-wide text-white flex-1">{meta.title}</h2>
              <span className={`rounded-md border px-2.5 py-1 font-mono text-[10px] font-bold tracking-[0.15em] ${meta.badgeCls}`}>
                {meta.badge}
              </span>
              <button
                onClick={onClose}
                aria-label={L("Kapat", "Close")}
                className="flex items-center justify-center rounded-lg border border-white/10 text-gray-400 transition-colors hover:text-white hover:bg-white/[0.06]"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-5 md:p-6">
              {open === "ml" && <MlDetail />}
              {open === "emel" && <EmelDetail />}
              {(open === "pulse1" || open === "pulse2" || open === "pulse3") && <PulseDetail variant={open} />}
              {open === "smc" && <SmcDetail />}
              {open === "debate" && <DebateDetail live={debateLive} />}
              <p className="mt-6 text-center font-mono text-[9px] tracking-[0.25em] text-gray-700">
                {L("DEMO GÖRÜNÜM — CANLIDA GERÇEK MOTOR ÇIKTISI AKAR", "DEMO VIEW — LIVE ENGINE OUTPUT WHEN WIRED")}
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
