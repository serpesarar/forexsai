"use client";

/**
 * Dersler — analiz çıktılarından damıtılıp motorlara enjekte edilen bilgiler.
 */

import { Archive, GraduationCap } from "lucide-react";
import { motion } from "framer-motion";

import { useArchiveLesson, useLessons } from "@/lib/api/evolution";
import { Badge, EmptyState, GlassCard, Section, stagger, timeAgo } from "./ui";

const TARGET_LABELS: Record<string, string> = {
  bias_debate: "Ajan Tartışması",
  claude_decider: "Claude Decider",
  panel: "Panel",
};

export default function LessonsPanel() {
  const { data } = useLessons();
  const archive = useArchiveLesson();
  const lessons = data?.lessons ?? [];

  return (
    <Section id="dersler" title="Öğrenilen Dersler" subtitle="Öğret düğmesiyle motorlara işlenmiş bilgiler" accent="#F9A8D4" icon={<GraduationCap size={22} />}>
      <GlassCard>
        {lessons.length === 0 && <EmptyState text="Henüz ders yok — bir analiz çalıştırıp 'Öğret'e bas." icon={<GraduationCap size={22} />} />}
        <div className="space-y-2.5">
          {lessons.map((l, i) => (
            <motion.div {...stagger(i)} key={l.id} layout className="group rounded-2xl border border-white/[0.07] bg-white/[0.02] p-3.5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-slate-200">{l.title}</p>
                <button
                  onClick={() => archive.mutate({ id: l.id, status: "archived" })}
                  className="shrink-0 rounded-lg p-1.5 text-slate-600 opacity-0 transition hover:bg-white/5 hover:text-slate-300 group-hover:opacity-100"
                  title="Arşivle (motorlardan geri çek)"
                >
                  <Archive size={13} />
                </button>
              </div>
              <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-400">{l.summary}</p>
              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                {l.targets.map((t) => (
                  <Badge key={t} tone="purple">
                    → {TARGET_LABELS[t] ?? t}
                  </Badge>
                ))}
                {l.symbol && <Badge tone="blue">{l.symbol}</Badge>}
                <span className="text-[10px] text-slate-600">{timeAgo(l.created_at)}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassCard>
    </Section>
  );
}
