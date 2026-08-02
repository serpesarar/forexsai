"use client";

/**
 * ForexSAI ana panel — Neural tasarım.
 * Eski 30+ panelli dashboard'un yerini alan giriş ekranı: her sembol
 * kendi Neural sayfasına açılır (canlı fiyat + yön kartlarıyla),
 * altta hızlı erişim kartları (Gemi Haritası, Evrim Paneli).
 * Eski sürüm: .backup/legacy_panels_20260715/app/page.tsx
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, LineChart, Newspaper, Radar, Ship } from "lucide-react";

import AuthGuard from "@/components/AuthGuard";
import NeuralNav from "@/components/neural/NeuralNav";
import { useNeuralLocale } from "@/components/neural/i18n";
import { buildApiUrl } from "@/lib/api/base";

// ── canlı fiyat çekimi (hafif — 4 sembol, 30sn) ───────────────────────────

interface Quote { price?: string; changePct?: number; up?: boolean }

const SYMBOLS = [
  { slug: "ndx", code: "NDX.INDX", name: "NASDAQ 100", nameTr: "", accent: "#4f8cff" },
  { slug: "dax", code: "GDAXI.INDX", name: "DAX 40", nameTr: "", accent: "#a855f7" },
  { slug: "xauusd", code: "XAUUSD", name: "GOLD / USD", nameTr: "ALTIN / USD", accent: "#fbbf24" },
  { slug: "usoil", code: "USOIL.FOREX", name: "WTI CRUDE", nameTr: "WTI PETROL", accent: "#14b8a6" },
] as const;

function useQuotes(): Record<string, Quote> {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  useEffect(() => {
    let alive = true;
    const load = async () => {
      const entries = await Promise.all(
        SYMBOLS.map(async (s) => {
          try {
            const ctrl = new AbortController();
            const t = setTimeout(() => ctrl.abort(), 8000);
            const res = await fetch(buildApiUrl(`/api/data/cached/${encodeURIComponent(s.code)}`), {
              signal: ctrl.signal,
            });
            clearTimeout(t);
            if (!res.ok) return [s.code, {}] as const;
            const j = await res.json();
            const snap = j?.data?.ta_snapshot ?? j?.data ?? {};
            const p = Number(snap?.current_price);
            const chg = Number(snap?.change_pct ?? 0);
            if (!Number.isFinite(p) || p <= 0) return [s.code, {}] as const;
            return [
              s.code,
              {
                price: p >= 1000 ? p.toLocaleString("en-US", { maximumFractionDigits: 1 }) : p.toFixed(2),
                changePct: chg,
                up: chg >= 0,
              },
            ] as const;
          } catch {
            return [s.code, {}] as const;
          }
        })
      );
      if (alive) setQuotes(Object.fromEntries(entries));
    };
    load();
    const t = setInterval(load, 30_000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);
  return quotes;
}

// ── sembol kartı ───────────────────────────────────────────────────────────

function SymbolCard({ s, q, i }: { s: (typeof SYMBOLS)[number]; q: Quote; i: number }) {
  const { L } = useNeuralLocale();
  const name = s.nameTr ? L(s.nameTr, s.name) : s.name;
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 + i * 0.1, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
    >
      <Link
        href={`/neural/${s.slug}`}
        className="group relative block overflow-hidden rounded-2xl border border-white/[0.07] bg-[#0a0f1c]/80 p-6 backdrop-blur-md transition-all duration-300 hover:border-cyan-400/30 hover:shadow-[0_0_40px_rgba(34,211,238,0.1)] hover:-translate-y-1"
      >
        {/* accent glow */}
        <div
          className="pointer-events-none absolute -top-16 -right-16 h-40 w-40 rounded-full blur-3xl opacity-20 group-hover:opacity-40 transition-opacity duration-500"
          style={{ background: s.accent }}
          aria-hidden
        />
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="text-base font-bold tracking-wide text-white">{name}</div>
            <div className="mt-1 font-mono text-[9px] tracking-[0.25em] text-gray-600">{s.code}</div>
          </div>
          <motion.span
            className="h-2 w-2 rounded-full"
            style={{ background: s.accent, boxShadow: `0 0 10px ${s.accent}` }}
            animate={{ opacity: [1, 0.35, 1] }}
            transition={{ repeat: Infinity, duration: 2 + i * 0.3 }}
          />
        </div>

        <div className="flex items-end justify-between">
          <div>
            <div className="font-mono text-2xl font-bold text-white">{q.price ?? "—"}</div>
            {q.changePct !== undefined ? (
              <div className={`mt-1 font-mono text-sm ${q.up ? "text-emerald-400" : "text-red-400"}`}>
                {q.up ? "▲" : "▼"} {q.changePct >= 0 ? "+" : ""}
                {q.changePct.toFixed(2)}%
              </div>
            ) : (
              <div className="mt-1 font-mono text-[10px] tracking-[0.2em] text-gray-600">
                {L("BAĞLANIYOR…", "CONNECTING…")}
              </div>
            )}
          </div>
          <span className="flex items-center gap-1.5 font-mono text-[9px] tracking-[0.25em] text-gray-600 transition-colors group-hover:text-cyan-400">
            {L("PANELE GİT", "OPEN PANEL")}
            <ArrowRight size={12} className="transition-transform duration-300 group-hover:translate-x-1" />
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

// ── sayfa ──────────────────────────────────────────────────────────────────

function HomeInner() {
  const { L } = useNeuralLocale();
  const quotes = useQuotes();

  const quick = [
    {
      href: "/oil",
      icon: <Ship size={18} />,
      title: L("Gemi Haritası", "Ship Map"),
      desc: L(
        "Kanallardan geçen tankerler + fiziksel petrol piyasası istihbaratı.",
        "Tankers passing the chokepoints + physical oil-market intelligence."
      ),
      accent: "text-teal-400",
    },
    {
      href: "/evolution",
      icon: <Radar size={18} />,
      title: L("Evrim Paneli", "Evolution Panel"),
      desc: L(
        "Sistem haritası, model başarıları, değişiklik akışı ve bekleyen işler.",
        "System map, model performance, change feed and pending work."
      ),
      accent: "text-purple-400",
    },
    {
      href: "/neural/ndx",
      icon: <LineChart size={18} />,
      title: L("Sinyal Haritası", "Signal Map"),
      desc: L(
        "Sistemin mum mum ne dediğini gösteren canlı sinyal dalgası.",
        "The live signal wave showing what the system said, candle by candle."
      ),
      accent: "text-cyan-400",
    },
    {
      href: "/news-correlation",
      icon: <Newspaper size={18} />,
      title: L("Haber Radarı", "News Radar"),
      desc: L(
        "Haberleri grafikteki fiyat hareketleriyle eşleştiren korelasyon paneli.",
        "The correlation panel matching news to price moves on the chart."
      ),
      accent: "text-amber-400",
    },
  ];

  return (
    <div className="min-h-screen bg-[#05070d] font-sans text-white">
      <div className="pointer-events-none fixed inset-0" aria-hidden>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(34,211,238,0.08),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_50%_40%_at_80%_110%,rgba(168,85,247,0.05),transparent)]" />
      </div>

      <NeuralNav />

      <main className="relative mx-auto max-w-[1200px] px-4 pb-16 md:px-8">
        {/* başlık */}
        <div className="pb-10 pt-12 text-center md:pt-16">
          <motion.p
            initial={{ opacity: 0, letterSpacing: "0.8em" }}
            animate={{ opacity: 1, letterSpacing: "0.45em" }}
            transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
            className="font-mono text-[10px] uppercase text-cyan-500/70"
          >
            {L("Komuta Merkezi", "Command Center")}
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.8 }}
            className="mt-3 text-3xl font-light text-gray-300 md:text-4xl"
          >
            {L("Bir sembol seç — ", "Pick a symbol — the ")}
            <span className="font-bold text-white">Core</span>
            {L(" seni bekliyor", " is waiting")}
          </motion.h1>
        </div>

        {/* sembol kartları */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {SYMBOLS.map((s, i) => (
            <SymbolCard key={s.slug} s={s} q={quotes[s.code] ?? {}} i={i} />
          ))}
        </div>

        {/* hızlı erişim */}
        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {quick.map((qk, i) => (
            <motion.div
              key={qk.href + qk.title}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 + i * 0.12, duration: 0.6 }}
            >
              <Link
                href={qk.href}
                className="group flex items-start gap-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 transition-all hover:border-white/[0.12] hover:bg-white/[0.04]"
              >
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] ${qk.accent}`}>
                  {qk.icon}
                </span>
                <span>
                  <span className="block text-sm font-medium text-white">{qk.title}</span>
                  <span className="mt-1 block text-xs font-light leading-relaxed text-gray-500">{qk.desc}</span>
                </span>
              </Link>
            </motion.div>
          ))}
        </div>

        <p className="mt-12 text-center font-mono text-[9px] tracking-[0.25em] text-gray-700">
          {L("6 MODEL · 4 SEMBOL · TEK ÇEKİRDEK", "6 MODELS · 4 SYMBOLS · ONE CORE")}
        </p>
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <AuthGuard>
      <HomeInner />
    </AuthGuard>
  );
}
