"use client";

/**
 * Bekleyen İşler — unutulan deneyler/bağlantılar/kararlar panosu.
 * 1. Kural gereği her Claude Code oturumu buraya yazar; hiçbir fikir kaybolmaz.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, CircleDashed, ListTodo, Play, Plus, Trash2 } from "lucide-react";

import { type BacklogItem, useAddBacklog, useBacklog, useUpdateBacklog } from "@/lib/api/evolution";
import { Badge, Card, EmptyState, Section, catLabel, timeAgo } from "./ui";

const PRIORITY_TONE = { high: "red", medium: "amber", low: "slate" } as const;
const PRIORITY_LABEL = { high: "yüksek", medium: "orta", low: "düşük" } as const;

function ItemRow({ item }: { item: BacklogItem }) {
  const update = useUpdateBacklog();
  const [open, setOpen] = useState(false);
  const [confirmDrop, setConfirmDrop] = useState(false);
  const done = item.status === "done" || item.status === "dropped";

  // Vazgeç iki adımlı: ilk tık onay ister (3sn), ikinci tık düşürür —
  // tek yanlış tıkla iş kaybolmasın.
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
      layout
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      className={`rounded-xl border px-3 py-2.5 ${
        done ? "border-slate-800/50 bg-transparent opacity-50" : "border-slate-800 bg-[#0d1420]"
      }`}
    >
      <div className="flex items-start gap-2.5">
        <button
          onClick={() => update.mutate({ id: item.id, status: done ? "pending" : "done" })}
          className="mt-0.5 shrink-0 text-slate-500 transition hover:text-emerald-400"
          title={done ? "Yeniden aç" : "Tamamlandı işaretle"}
        >
          {done ? <CheckCircle2 size={16} className="text-emerald-500" /> : <CircleDashed size={16} />}
        </button>
        <div className="min-w-0 flex-1 cursor-pointer" onClick={() => setOpen(!open)}>
          <p className={`text-[13px] font-medium leading-snug ${done ? "line-through" : ""} text-slate-200`}>
            {item.title}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            <Badge tone={PRIORITY_TONE[item.priority] ?? "slate"}>{PRIORITY_LABEL[item.priority] ?? item.priority}</Badge>
            <Badge tone="slate">{catLabel(item.category)}</Badge>
            {item.status === "in_progress" && <Badge tone="blue">devam ediyor</Badge>}
            <span className="text-[10px] text-slate-500">{timeAgo(item.updated_at)}</span>
          </div>
          {open && item.detail && (
            <p className="mt-2 text-[11px] leading-relaxed text-slate-400">{item.detail}</p>
          )}
        </div>
        {!done && item.status !== "in_progress" && (
          <button
            onClick={() => update.mutate({ id: item.id, status: "in_progress" })}
            className="shrink-0 rounded-lg p-1.5 text-slate-500 transition hover:bg-[#4F8CFF]/15 hover:text-[#4F8CFF]"
            title="Başladım"
          >
            <Play size={13} />
          </button>
        )}
        {!done && (
          <button
            onClick={handleDrop}
            className={`shrink-0 rounded-lg p-1.5 transition ${
              confirmDrop
                ? "bg-rose-500/25 text-rose-300 ring-1 ring-rose-500/60"
                : "text-slate-600 hover:bg-rose-500/15 hover:text-rose-400"
            }`}
            title={confirmDrop ? "Emin misin? Tekrar tıkla" : "Vazgeç"}
          >
            <Trash2 size={13} />
          </button>
        )}
      </div>
    </motion.div>
  );
}

export default function BacklogPanel() {
  const { data, isLoading } = useBacklog();
  const add = useAddBacklog();
  const [title, setTitle] = useState("");
  const [showDone, setShowDone] = useState(false);

  const items = data?.items ?? [];
  const active = items.filter((i) => i.status === "pending" || i.status === "in_progress");
  const finished = items.filter((i) => i.status === "done" || i.status === "dropped");

  const submit = () => {
    const t = title.trim();
    if (t.length < 3) return;
    // Input'u ancak kayıt BAŞARILI olunca temizle — hata durumunda yazılan
    // metin kaybolmasın, hata da görünür olsun (aşağıdaki add.isError bloğu).
    add.mutate({ title: t }, { onSuccess: () => setTitle("") });
  };

  return (
    <Section
      id="bekleyen"
      title="Bekleyen & Unutulan İşler"
      icon={<ListTodo size={18} />}
      subtitle={`${active.length} açık iş — her oturum otomatik güncellenir (1. Kural)`}
    >
      <Card>
        <div className="mb-3 flex gap-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Yeni iş / fikir ekle… (Enter)"
            className="flex-1 rounded-lg border border-slate-700 bg-[#0B0F17] px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600 focus:border-[#4F8CFF] focus:outline-none"
          />
          <button
            onClick={submit}
            disabled={add.isPending || title.trim().length < 3}
            className="flex items-center gap-1 rounded-lg bg-[#4F8CFF]/20 px-3 text-xs font-semibold text-[#4F8CFF] transition hover:bg-[#4F8CFF]/35 disabled:opacity-40"
          >
            <Plus size={14} /> Ekle
          </button>
        </div>

        {add.isError && (
          <p className="mb-2 text-[11px] text-rose-400">
            Eklenemedi: {(add.error as Error).message}
          </p>
        )}
        {isLoading && <EmptyState text="Yükleniyor…" />}
        {!isLoading && active.length === 0 && <EmptyState text="Açık iş yok — her şey yapıldı 🎉" />}

        <div className="space-y-2">
          {active.map((i) => (
            <ItemRow key={i.id} item={i} />
          ))}
        </div>

        {finished.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowDone(!showDone)}
              className="text-[11px] text-slate-500 hover:text-slate-300"
            >
              {showDone ? "▾" : "▸"} Tamamlanan/bırakılan ({finished.length})
            </button>
            {showDone && (
              <div className="mt-2 space-y-2">
                {finished.map((i) => (
                  <ItemRow key={i.id} item={i} />
                ))}
              </div>
            )}
          </div>
        )}
      </Card>
    </Section>
  );
}
