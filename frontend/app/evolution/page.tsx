"use client";

/**
 * EVRİM PANELİ — kendi kendini besleyen sistemin tek kontrol merkezi.
 * Aurora glass tema: sakin, modern, akıcı animasyonlar.
 */

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Dna,
  GraduationCap,
  History,
  ListTodo,
  Network,
  Sparkles,
  Terminal,
  TrendingUp,
} from "lucide-react";

import { useOverview } from "@/lib/api/evolution";
import AnalysisRunner from "@/components/evolution/AnalysisRunner";
import BacklogPanel from "@/components/evolution/BacklogPanel";
import ChangelogFeed from "@/components/evolution/ChangelogFeed";
import LessonsPanel from "@/components/evolution/LessonsPanel";
import PerformanceBoard from "@/components/evolution/PerformanceBoard";
import SystemMap from "@/components/evolution/SystemMap";
import { AnimatedNumber, PulseDot } from "@/components/evolution/ui";

const NAV = [
  { id: "performans", label: "Performans", icon: <TrendingUp size={14} /> },
  { id: "analiz", label: "Analiz & Öğret", icon: <Terminal size={14} /> },
  { id: "bekleyen", label: "Bekleyen İşler", icon: <ListTodo size={14} /> },
  { id: "harita", label: "Sistem Haritası", icon: <Network size={14} /> },
  { id: "degisiklik", label: "Değişiklik", icon: <History size={14} /> },
  { id: "dersler", label: "Dersler", icon: <GraduationCap size={14} /> },
];

function StatTile({
  value,
  label,
  accent,
  warn,
}: {
  value: number;
  label: string;
  accent: string;
  warn?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-2xl border border-white/[0.07] bg-white/[0.03] px-5 py-4"
    >
      <div className="text-3xl font-bold tabular-nums" style={{ color: warn ? "#FBBF24" : accent }}>
        <AnimatedNumber value={value} />
      </div>
      <div className="mt-1 text-xs font-medium text-slate-400">{label}</div>
    </motion.div>
  );
}

export default function EvolutionPage() {
  const { data: overview } = useOverview(30);
  const counts = overview?.counts;
  const activeRuns = overview?.active_runs ?? [];

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#070A11] text-slate-200">
      {/* ── Aurora arka plan (sabit, blur'lu — scroll'da kompozitörü kilitlemez) ── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <motion.div
          animate={{ x: [0, 40, 0], y: [0, -30, 0] }}
          transition={{ duration: 24, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-40 -left-32 h-[520px] w-[520px] rounded-full bg-violet-600/20 blur-[130px]"
        />
        <motion.div
          animate={{ x: [0, -50, 0], y: [0, 40, 0] }}
          transition={{ duration: 30, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/3 -right-40 h-[560px] w-[560px] rounded-full bg-sky-600/15 blur-[140px]"
        />
        <motion.div
          animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
          transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-0 left-1/4 h-[480px] w-[480px] rounded-full bg-emerald-600/12 blur-[130px]"
        />
      </div>

      {/* ── Sticky nav ── */}
      <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#070A11]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-5 py-3">
          <Link href="/" className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white" title="Ana sayfa">
            <ArrowLeft size={18} />
          </Link>
          <Dna size={20} className="text-violet-400" />
          <span className="text-sm font-semibold text-white">Evrim Paneli</span>
          {activeRuns.length > 0 && (
            <span className="ml-2 flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-1 text-[11px] font-medium text-emerald-300">
              <PulseDot /> {activeRuns.length} çalışıyor
            </span>
          )}
          <nav className="ml-auto hidden items-center gap-1 md:flex">
            {NAV.map((n) => (
              <a
                key={n.id}
                href={`#${n.id}`}
                className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-medium text-slate-400 transition hover:bg-white/[0.06] hover:text-white"
              >
                {n.icon} {n.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      {/* ── İçerik ── */}
      <main className="relative z-10 mx-auto max-w-7xl px-5 pb-24 pt-10">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="mb-12"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3.5 py-1.5 text-[12px] font-medium text-violet-300">
            <Sparkles size={13} /> Kendi kendini besleyen sistem
          </div>
          <h1 className="max-w-2xl text-4xl font-bold leading-[1.1] tracking-tight text-white sm:text-5xl">
            Sinyal <span className="bg-gradient-to-r from-sky-300 via-violet-300 to-emerald-300 bg-clip-text text-transparent">→</span> sonuç{" "}
            <span className="bg-gradient-to-r from-sky-300 via-violet-300 to-emerald-300 bg-clip-text text-transparent">→</span> analiz{" "}
            <span className="bg-gradient-to-r from-sky-300 via-violet-300 to-emerald-300 bg-clip-text text-transparent">→</span> öğren
          </h1>
          <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-slate-400">
            Tüm motorların ve ajanların tek yerden. Neyin yanlış gittiğini gör, tek tıkla
            çalıştır, "Öğret" ile modellere işlet. Unuttuğun hiçbir deney kaybolmaz.
          </p>

          {/* İstatistik tile'ları */}
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile value={counts?.registry ?? 0} label="motor & ajan" accent="#818CF8" />
            <StatTile value={counts?.analyses ?? 0} label="analiz aracı" accent="#5EEAD4" />
            <StatTile value={counts?.backlog_pending ?? 0} label="bekleyen iş" accent="#818CF8" warn={(counts?.backlog_pending ?? 0) > 0} />
            <StatTile value={counts?.lessons_active ?? 0} label="aktif ders" accent="#F9A8D4" />
          </div>
        </motion.div>

        <div className="space-y-16">
          <PerformanceBoard overview={overview} />
          <AnalysisRunner />
          <BacklogPanel />
          <SystemMap />
          <div className="grid gap-6 lg:grid-cols-2">
            <ChangelogFeed />
            <LessonsPanel />
          </div>
        </div>

        <footer className="mt-20 flex items-center justify-center gap-2 border-t border-white/[0.06] pt-8 text-center text-[12px] text-slate-600">
          <Dna size={13} /> 1. Kural: her oturum değişikliklerini bu panele yazar — hiçbir fikir kaybolmaz.
        </footer>
      </main>
    </div>
  );
}
