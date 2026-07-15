"use client";

/**
 * Bekleyen İşler — unutulan deneyler/bağlantılar/kararlar.
 * 1. Kural gereği her oturum buraya yazar; hiçbir fikir kaybolmaz.
 */

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Circle, ListTodo, Play, Plus, Trash2 } from "lucide-react";

import { type BacklogItem, useAddBacklog, useBacklog, useUpdateBacklog } from "@/lib/api/evolution";
import { Badge, EmptyState, GlassCard, Section, catLabel, cx, stagger, timeAgo } from "./ui";

const PRIORITY_TONE = { high: "red", medium: "amber", low: "slate" } as const;
const PRIORITY_LABEL = { high: "yüksek", medium: "orta", low: "düşük" } as const;

function ItemRow({ item, index }: { item: BacklogItem; index: number }) {
  const update = useUpdateBacklog();
  const [open, setOpen] = useState(false);
  const [confirmDrop, setConfirmDrop] = useState(false);
  const done = item.status === "done" || item.status === "dropped";

  const handleDrop = () => {
    if (!confirmDrop) {
      setConfirmDrop(true);
      setTimeout(() => setConfirmDrop(false), 3000);
      return;
    }
    setConfirmDrop(false);
    update.mutate({ id: item.id, status: "dropped" });
  };

  return (
    <motion.div
      {...stagger(index)}
      layout
      className={cx(
        "group rounded-2xl border px-4 py-3 transition-colors",
        done ? "border-white/[0.04] opacity-45" : "border-white/[0.07] bg-white/[0.02] hover:border-white/12"
      )}
    >
      <div className="flex items-start gap-3">
        <button
          onClick={() => update.mutate({ id: item.id, status: done ? "pending" : "done" })}
          className="mt-0.5 shrink-0 transition hover:scale-110"
          title={done ? "Yeniden aç" : "Tamamlandı"}
        >
          {done ? <CheckCircle2 size={17} className="text-emerald-400" /> : <Circle size={17} className="text-slate-600 group-hover:text-emerald-400/60" />}
        </button>
        <div className="min-w-0 flex-1 cursor-pointer" onClick={() => setOpen(!open)}>
          <p className={cx("text-[13px] font-medium leading-snug text-slate-200", done && "line-through")}>{item.title}</p>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <Badge tone={PRIORITY_TONE[item.priority] ?? "slate"}>{PRIORITY_LABEL[item.priority] ?? item.priority}</Badge>
            <Badge tone="slate">{catLabel(item.category)}</Badge>
            {item.status === "in_progress" && <Badge tone="blue">devam ediyor</Badge>}
            <span className="text-[10px] text-slate-600">{timeAgo(item.updated_at)}</span>
          </div>
          <AnimatePresence>
            {open && item.detail && (
              <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="mt-2 overflow-hidden text-[11px] leading-relaxed text-slate-400">
                {item.detail}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
        {!done && (
          <div className="flex shrink-0 gap-0.5 opacity-0 transition group-hover:opacity-100">
            {item.status !== "in_progress" && (
              <button onClick={() => update.mutate({ id: item.id, status: "in_progress" })} className="rounded-lg p-1.5 text-slate-500 transition hover:bg-sky-400/15 hover:text-sky-300" title="Başladım">
                <Play size={13} />
              </button>
            )}
            <button
              onClick={handleDrop}
              className={cx("rounded-lg p-1.5 transition", confirmDrop ? "bg-rose-400/25 text-rose-300 ring-1 ring-rose-400/60" : "text-slate-600 hover:bg-rose-400/15 hover:text-rose-300")}
              title={confirmDrop ? "Emin misin? Tekrar tıkla" : "Vazgeç"}
            >
              <Trash2 size={13} />
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function BacklogPanel() {
  const { data } = useBacklog();
  const add = useAddBacklog();
  const [title, setTitle] = useState("");
  const [showDone, setShowDone] = useState(false);

  const items = data?.items ?? [];
  const active = items.filter((i) => i.status === "pending" || i.status === "in_progress");
  const finished = items.filter((i) => i.status === "done" || i.status === "dropped");

  const submit = () => {
    const t = title.trim();
    if (t.length < 3) return;
    add.mutate({ title: t }, { onSuccess: () => setTitle("") });
  };

  return (
    <Section
      id="bekleyen"
      title="Bekleyen & Unutulan İşler"
      subtitle={`${active.length} açık iş — her oturum otomatik güncellenir`}
      accent="#818CF8"
      icon={<ListTodo size={22} />}
    >
      <GlassCard>
        <div className="mb-4 flex gap-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Yeni iş / fikir ekle… (Enter)"
            className="flex-1 rounded-2xl border border-white/[0.07] bg-white/[0.03] px-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 transition focus:border-violet-400/50 focus:outline-none"
          />
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={submit}
            disabled={add.isPending || title.trim().length < 3}
            className="flex items-center gap-1 rounded-2xl bg-gradient-to-r from-indigo-500 to-violet-500 px-4 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 transition disabled:opacity-40"
          >
            <Plus size={14} /> Ekle
          </motion.button>
        </div>

        {add.isError && <p className="mb-2 text-[11px] text-rose-300">Eklenemedi: {(add.error as Error).message}</p>}
        {active.length === 0 && <EmptyState text="Açık iş yok — her şey yapıldı 🎉" />}

        <div className="space-y-2">
          {active.map((i, idx) => (
            <ItemRow key={i.id} item={i} index={idx} />
          ))}
        </div>

        {finished.length > 0 && (
          <div className="mt-3">
            <button onClick={() => setShowDone(!showDone)} className="text-[11px] text-slate-500 transition hover:text-slate-300">
              {showDone ? "▾" : "▸"} Tamamlanan/bırakılan ({finished.length})
            </button>
            {showDone && (
              <div className="mt-2 space-y-2">
                {finished.map((i, idx) => (
                  <ItemRow key={i.id} item={i} index={idx} />
                ))}
              </div>
            )}
          </div>
        )}
      </GlassCard>
    </Section>
  );
}
