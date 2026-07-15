"use client";

/**
 * Dersler — analiz çıktılarından damıtılıp motorlara enjekte edilen bilgiler.
 * Hangi motor neyi "öğrendi" burada görünür; arşivle ile geri alınabilir.
 */

import { Archive, GraduationCap } from "lucide-react";
import { motion } from "framer-motion";

import { useArchiveLesson, useLessons } from "@/lib/api/evolution";
import { Badge, Card, EmptyState, Section, timeAgo } from "./ui";

const TARGET_LABELS: Record<string, string> = {
  bias_debate: "Ajan Tartışması",
  claude_decider: "Claude Decider",
  panel: "Panel",
};

export default function LessonsPanel() {
  const { data, isLoading } = useLessons();
  const archive = useArchiveLesson();
  const lessons = data?.lessons ?? [];

  return (
    <Section
      id="dersler"
      title="Öğrenilen Dersler"
      icon={<GraduationCap size={18} />}
      subtitle="Öğret düğmesiyle motorlara enjekte edilen damıtılmış bilgiler"
    >
      <Card>
        {isLoading && <EmptyState text="Yükleniyor…" />}
        {!isLoading && lessons.length === 0 && (
          <EmptyState text="Henüz ders yok — bir analiz çalıştırıp 'Öğret' düğmesini kullan." />
        )}
        <div className="space-y-2.5">
          {lessons.map((l) => (
            <motion.div
              key={l.id}
              layout
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-xl border border-slate-800 bg-[#0d1420] p-3"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold text-slate-200">{l.title}</p>
                <button
                  onClick={() => archive.mutate({ id: l.id, status: "archived" })}
                  className="shrink-0 rounded-lg p-1.5 text-slate-600 transition hover:bg-slate-700/50 hover:text-slate-300"
                  title="Arşivle (motorlardan geri çek)"
                >
                  <Archive size={13} />
                </button>
              </div>
              <p className="mt-1.5 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-400">
                {l.summary}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                {l.targets.map((t) => (
                  <Badge key={t} tone="purple">
                    → {TARGET_LABELS[t] ?? t}
                  </Badge>
                ))}
                {l.symbol && <Badge tone="blue">{l.symbol}</Badge>}
                <span className="text-[10px] text-slate-500">{timeAgo(l.created_at)}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>
    </Section>
  );
}
