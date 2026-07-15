"use client";

/**
 * EVRİM PANELİ — kendi kendini besleyen sistemin tek kontrol merkezi.
 *
 * Bölümler: Performans (model + ajan karnesi) → Analiz Çalıştırıcı
 * (Çalıştır → Öğret) → Bekleyen İşler → Sistem Haritası → Değişiklik Akışı →
 * Dersler. Veri: /api/evolution/* (lib/api/evolution.ts).
 */

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowLeft,
  Dna,
  GraduationCap,
  History,
  ListTodo,
  Network,
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
import { PulseDot } from "@/components/evolution/ui";

const NAV = [
  { id: "performans", label: "Performans", icon: <TrendingUp size={13} /> },
  { id: "analiz", label: "Analiz & Öğret", icon: <Terminal size={13} /> },
  { id: "bekleyen", label: "Bekleyen İşler", icon: <ListTodo size={13} /> },
  { id: "harita", label: "Sistem Haritası", icon: <Network size={13} /> },
  { id: "degisiklik", label: "Değişiklik Akışı", icon: <History size={13} /> },
  { id: "dersler", label: "Dersler", icon: <GraduationCap size={13} /> },
];

function StatChip({ label, value, tone }: { label: string; value: number | string; tone?: "warn" }) {
  return (
    <div className="flex items-center gap-1.5 rounded-full border border-slate-800 bg-[#111827]/80 px-3 py-1">
      <span className={`text-sm font-bold tabular-nums ${tone === "warn" ? "text-amber-400" : "text-slate-100"}`}>
        {value}
      </span>
      <span className="text-[10px] text-slate-500">{label}</span>
    </div>
  );
}

export default function EvolutionPage() {
  const { data: overview, isLoading } = useOverview(30);
  const counts = overview?.counts;
  const activeRuns = overview?.active_runs ?? [];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-200">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#0B0F17]">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
          <Link href="/" className="text-slate-500 transition hover:text-slate-200" title="Ana sayfa">
            <ArrowLeft size={18} />
          </Link>
          <motion.div
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2.5"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#4F8CFF] to-violet-500 shadow-lg shadow-[#4F8CFF]/25">
              <Dna size={18} className="text-white" />
            </span>
            <div>
              <h1 className="text-base font-bold leading-tight text-slate-100">Evrim Paneli</h1>
              <p className="text-[10px] text-slate-500">kendi kendini besleyen sistem · ForexSAI</p>
            </div>
          </motion.div>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            {activeRuns.length > 0 && (
              <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium text-emerald-400">
                <PulseDot /> {activeRuns.length} analiz çalışıyor
              </div>
            )}
            <StatChip label="motor/ajan" value={counts?.registry ?? "…"} />
            <StatChip label="analiz aracı" value={counts?.analyses ?? "…"} />
            <StatChip
              label="bekleyen iş"
              value={counts?.backlog_pending ?? "…"}
              tone={(counts?.backlog_pending ?? 0) > 0 ? "warn" : undefined}
            />
            <StatChip label="aktif ders" value={counts?.lessons_active ?? "…"} />
          </div>
        </div>

        {/* Bölüm navigasyonu */}
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-2">
          {NAV.map((n) => (
            <a
              key={n.id}
              href={`#${n.id}`}
              className="flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
            >
              {n.icon} {n.label}
            </a>
          ))}
        </nav>
      </header>

      {/* İçerik */}
      <main className="mx-auto max-w-7xl space-y-10 px-4 py-8">
        <PerformanceBoard overview={overview} loading={isLoading} />
        <AnalysisRunner />
        <BacklogPanel />
        <SystemMap />
        <div className="grid gap-10 lg:grid-cols-2 lg:gap-6">
          <ChangelogFeed />
          <LessonsPanel />
        </div>

        <footer className="flex items-center justify-center gap-2 border-t border-slate-800/60 pt-6 pb-4 text-[10px] text-slate-600">
          <Activity size={11} />
          Döngü: sinyal → sonuç → analiz → ders → daha akıllı motorlar — 1. Kural ile her oturum buraya yazar.
        </footer>
      </main>
    </div>
  );
}
