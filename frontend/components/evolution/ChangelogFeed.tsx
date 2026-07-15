"use client";

/**
 * Değişiklik Akışı — git commit'leri + Claude Code oturum notları +
 * commit'lenmemiş worktree özeti tek zaman çizelgesinde (1. Kural'ın vitrini).
 */

import { GitCommitHorizontal, History, Laptop, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

import { type ChangelogEntry, useChangelog } from "@/lib/api/evolution";
import { Badge, Card, EmptyState, Section, timeAgo } from "./ui";

function EntryIcon({ kind }: { kind: ChangelogEntry["kind"] }) {
  if (kind === "commit")
    return (
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#4F8CFF]/15 text-[#4F8CFF]">
        <GitCommitHorizontal size={14} />
      </span>
    );
  if (kind === "session")
    return (
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-violet-400">
        <Sparkles size={14} />
      </span>
    );
  return (
    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-500/15 text-amber-400">
      <Laptop size={14} />
    </span>
  );
}

export default function ChangelogFeed() {
  const { data, isLoading } = useChangelog(50);
  const entries = data?.entries ?? [];

  return (
    <Section
      id="degisiklik"
      title="Değişiklik Akışı"
      icon={<History size={18} />}
      subtitle="Git geçmişi + Claude Code oturum notları — proje nasıl evriliyor"
    >
      <Card>
        {isLoading && <EmptyState text="Akış yükleniyor…" />}
        {!isLoading && entries.length === 0 && <EmptyState text="Kayıt yok." />}
        <div className="relative space-y-0">
          {entries.map((e, idx) => (
            <motion.div
              key={`${e.kind}-${e.id}-${idx}`}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.25, delay: Math.min(idx * 0.02, 0.3) }}
              className="relative flex gap-3 pb-4"
            >
              {idx < entries.length - 1 && (
                <span className="absolute left-3.5 top-8 h-full w-px bg-slate-800" />
              )}
              <EntryIcon kind={e.kind} />
              <div className="min-w-0 flex-1 pt-0.5">
                <p className="text-[13px] leading-snug text-slate-200">{e.summary}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-[10px] text-slate-500">
                  {e.kind === "commit" && <Badge tone="blue">commit {e.id}</Badge>}
                  {e.kind === "session" && <Badge tone="purple">Claude oturumu</Badge>}
                  {e.kind === "worktree" && <Badge tone="amber">commit'lenmemiş</Badge>}
                  <span>{e.author}</span>
                  <span>{timeAgo(e.ts)}</span>
                </div>
                {e.files && e.files.length > 0 && (
                  <p className="mt-1 truncate font-mono text-[10px] text-slate-600">
                    {e.files.slice(0, 5).join(" · ")}
                    {e.files.length > 5 ? ` +${e.files.length - 5}` : ""}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </Card>
    </Section>
  );
}
