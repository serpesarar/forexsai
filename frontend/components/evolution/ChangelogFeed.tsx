"use client";

/**
 * Değişiklik Akışı — git commit'leri + oturum notları + worktree tek zaman
 * çizelgesinde (1. Kural'ın vitrini).
 */

import { GitCommitHorizontal, History, Laptop, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

import { type ChangelogEntry, useChangelog } from "@/lib/api/evolution";
import { Badge, EmptyState, GlassCard, Section, cx, timeAgo } from "./ui";

const KIND = {
  commit: { icon: <GitCommitHorizontal size={14} />, tone: "text-sky-300", bg: "bg-sky-400/12" },
  session: { icon: <Sparkles size={14} />, tone: "text-violet-300", bg: "bg-violet-400/12" },
  worktree: { icon: <Laptop size={14} />, tone: "text-amber-300", bg: "bg-amber-400/12" },
} as const;

export default function ChangelogFeed() {
  const { data } = useChangelog(50);
  const entries = data?.entries ?? [];

  return (
    <Section id="degisiklik" title="Değişiklik Akışı" subtitle="Git + oturum notları — proje nasıl evriliyor" accent="#60A5FA" icon={<History size={22} />}>
      <GlassCard>
        {entries.length === 0 && <EmptyState text="Akış yükleniyor…" />}
        <div className="relative">
          {entries.map((e, idx) => {
            const k = KIND[e.kind] ?? KIND.commit;
            return (
              <motion.div
                key={`${e.kind}-${e.id}-${idx}`}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: Math.min(idx * 0.02, 0.3) }}
                className="relative flex gap-3 pb-4 last:pb-0"
              >
                {idx < entries.length - 1 && <span className="absolute left-[15px] top-9 h-full w-px bg-white/[0.07]" />}
                <span className={cx("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", k.bg, k.tone)}>{k.icon}</span>
                <div className="min-w-0 flex-1 pt-1">
                  <p className="text-[13px] leading-snug text-slate-200">{e.summary}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-slate-500">
                    {e.kind === "commit" && <Badge tone="blue">commit {e.id}</Badge>}
                    {e.kind === "session" && <Badge tone="purple">Claude oturumu</Badge>}
                    {e.kind === "worktree" && <Badge tone="amber">commit'lenmemiş</Badge>}
                    <span>{e.author}</span>
                    <span>{timeAgo(e.ts)}</span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </GlassCard>
    </Section>
  );
}
