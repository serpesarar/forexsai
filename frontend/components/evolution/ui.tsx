"use client";

/**
 * Evrim Paneli — ortak küçük UI parçaları.
 * Renk kodu (CLAUDE.md ile tutarlı): ml=mavi, emel=mor, pulse=turuncu,
 * smc=teal, ai_panel=amber, meta=pembe.
 */

import { motion } from "framer-motion";
import type { ReactNode } from "react";

export function modelColor(name: string): string {
  const n = name.toLowerCase();
  if (n.startsWith("ml")) return "#4F8CFF";
  if (n.includes("emel")) return "#A78BFA";
  if (n.includes("pulse")) return "#FB923C";
  if (n.includes("smc")) return "#2DD4BF";
  if (n.includes("ai_panel")) return "#FBBF24";
  if (n.includes("meta")) return "#F472B6";
  return "#94A3B8";
}

export const CATEGORY_LABELS: Record<string, string> = {
  signal_engine: "Sinyal Motorları",
  agent: "AI Ajanları",
  learning: "Öğrenme & Analiz",
  gate: "Güvenlik Kapıları",
  data: "Veri Katmanı",
  bot: "Canlı Bot (MT5)",
  infra: "Altyapı",
  error_analysis: "Hata Analizi",
  performance: "Performans",
  backtest: "Backtest",
  pattern_mining: "Örüntü Madenciliği",
  calibration: "Kalibrasyon / Eğitim",
  data_repair: "Veri Onarımı",
  other: "Diğer",
};

export function catLabel(cat: string): string {
  return CATEGORY_LABELS[cat] ?? cat;
}

export function Section({
  id,
  title,
  icon,
  subtitle,
  children,
}: {
  id: string;
  title: string;
  icon: ReactNode;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="scroll-mt-24"
    >
      <div className="mb-4 flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#4F8CFF]/15 text-[#4F8CFF]">
          {icon}
        </span>
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>
      </div>
      {children}
    </motion.section>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border border-slate-800/80 bg-[#111827] p-4 ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: "slate" | "green" | "red" | "amber" | "blue" | "purple";
}) {
  const tones: Record<string, string> = {
    slate: "bg-slate-700/40 text-slate-300",
    green: "bg-emerald-500/15 text-emerald-400",
    red: "bg-rose-500/15 text-rose-400",
    amber: "bg-amber-500/15 text-amber-400",
    blue: "bg-[#4F8CFF]/15 text-[#4F8CFF]",
    purple: "bg-violet-500/15 text-violet-400",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

/** Animasyonlu yatay oran çubuğu (0-100). */
export function RateBar({ pct, color }: { pct: number; color: string }) {
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
      <motion.div
        initial={{ width: 0 }}
        whileInView={{ width: `${clamped}%` }}
        viewport={{ once: true }}
        transition={{ duration: 0.9, ease: "easeOut" }}
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
      />
    </div>
  );
}

/** Canlı nabız noktası (çalışan run'lar için). */
export function PulseDot({ color = "#34D399" }: { color?: string }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span
        className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
        style={{ backgroundColor: color }}
      />
      <span className="relative inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
    </span>
  );
}

export function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

export function timeAgo(iso: string): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const mins = Math.round((Date.now() - then) / 60_000);
  if (mins < 1) return "az önce";
  if (mins < 60) return `${mins} dk önce`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours} sa önce`;
  return `${Math.round(hours / 24)} gün önce`;
}
