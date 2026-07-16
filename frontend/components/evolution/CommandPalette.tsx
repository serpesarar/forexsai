"use client";

/**
 * ⌘K Komut Paleti — panelin her yerine klavyeden ulaş.
 * Bölümlere atla, 32 analiz aracını ara ve DOĞRUDAN çalıştır.
 */

import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight,
  Command,
  CornerDownLeft,
  GraduationCap,
  History,
  ListTodo,
  Network,
  Play,
  Plus,
  Search,
  Terminal,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { useAddBacklog, useAnalyses, useStartRun } from "@/lib/api/evolution";
import { toast } from "./toast";
import { cx } from "./ui";

interface PaletteItem {
  id: string;
  kind: "section" | "analysis" | "backlog";
  label: string;
  hint?: string;
  icon: ReactNode;
  disabled?: boolean;
  action: () => void;
}

const SECTIONS = [
  { id: "performans", label: "Performans", icon: <TrendingUp size={15} /> },
  { id: "analiz", label: "Analiz & Öğret", icon: <Terminal size={15} /> },
  { id: "canli-bot", label: "Canlı Bot & Decider", icon: <Terminal size={15} /> },
  { id: "bekleyen", label: "Bekleyen İşler", icon: <ListTodo size={15} /> },
  { id: "harita", label: "Sistem Haritası", icon: <Network size={15} /> },
  { id: "degisiklik", label: "Değişiklik Akışı", icon: <History size={15} /> },
  { id: "dersler", label: "Dersler", icon: <GraduationCap size={15} /> },
];

export default function CommandPalette({ onOpenRun }: { onOpenRun?: (runId: string) => void }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: analysesData } = useAnalyses();
  const startRun = useStartRun();
  const addBacklog = useAddBacklog();

  // ⌘K / Ctrl+K aç-kapa, Esc kapat
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 60);
    }
  }, [open]);

  const runAnalysis = useCallback(
    (id: string, name: string) => {
      setOpen(false);
      startRun.mutate(
        { analysisId: id },
        {
          onSuccess: (run) => {
            toast.success(`"${name}" başlatıldı`);
            onOpenRun?.(run.run_id);
          },
          onError: (e) => toast.error(`Başlatılamadı: ${(e as Error).message}`),
        }
      );
    },
    [startRun, onOpenRun]
  );

  const quickAdd = useCallback(
    (text: string) => {
      setOpen(false);
      addBacklog.mutate(
        { title: text },
        {
          onSuccess: () => toast.success(`Backlog'a eklendi: "${text.slice(0, 40)}"`),
          onError: (e) => toast.error(`Eklenemedi: ${(e as Error).message}`),
        }
      );
    },
    [addBacklog]
  );

  const items = useMemo<PaletteItem[]>(() => {
    // "+ fikir metni" → doğrudan backlog'a hızlı ekleme
    if (query.trimStart().startsWith("+")) {
      const text = query.trimStart().slice(1).trim();
      return [
        {
          id: "quick-add",
          kind: "backlog" as const,
          label: text.length >= 3 ? `Backlog'a ekle: "${text}"` : "Eklemek için en az 3 karakter yaz…",
          hint: "hızlı iş ekle",
          icon: <Plus size={15} />,
          disabled: text.length < 3,
          action: () => text.length >= 3 && quickAdd(text),
        },
      ];
    }
    const q = query.trim().toLowerCase();
    const sectionItems: PaletteItem[] = SECTIONS.filter((s) => !q || s.label.toLowerCase().includes(q)).map((s) => ({
      id: `sec-${s.id}`,
      kind: "section",
      label: s.label,
      hint: "bölüme git",
      icon: s.icon,
      action: () => {
        setOpen(false);
        document.getElementById(s.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
      },
    }));
    const analyses = analysesData?.analyses ?? [];
    const analysisItems: PaletteItem[] = analyses
      .filter((a) => !q || a.name.toLowerCase().includes(q) || a.what_it_does.toLowerCase().includes(q))
      .slice(0, q ? 12 : 5)
      .map((a) => ({
        id: `an-${a.id}`,
        kind: "analysis",
        label: a.name,
        hint: a.runnable_here === false ? "MT5 kutusunda çalıştır" : "çalıştır",
        icon: <Play size={15} />,
        action: () => runAnalysis(a.id, a.name),
      }));
    return [...sectionItems, ...analysisItems];
  }, [query, analysesData, runAnalysis, quickAdd]);

  // Aktif indeksi liste değişince sınırla
  useEffect(() => {
    setActive((a) => Math.min(a, Math.max(0, items.length - 1)));
  }, [items.length]);

  const onInputKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      items[active]?.action();
    }
  };

  return (
    <>
      {/* Header tetikleyicisi */}
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] font-medium text-slate-400 transition hover:border-white/20 hover:text-slate-200"
        title="Komut paleti"
      >
        <Search size={12} />
        <span className="hidden sm:inline">Ara / çalıştır</span>
        <kbd className="flex items-center gap-0.5 rounded-md border border-white/10 bg-white/[0.05] px-1.5 py-0.5 text-[9px] text-slate-500">
          <Command size={9} />K
        </kbd>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] flex items-start justify-center bg-black/60 p-4 pt-[12vh] backdrop-blur-sm"
            onClick={() => setOpen(false)}
          >
            <motion.div
              initial={{ y: -16, opacity: 0, scale: 0.98 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -16, opacity: 0, scale: 0.98 }}
              transition={{ type: "spring", damping: 26, stiffness: 340 }}
              className="w-full max-w-xl overflow-hidden rounded-3xl border border-white/10 bg-[#0B0F17] shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 border-b border-white/[0.07] px-4 py-3.5">
                <Search size={16} className="shrink-0 text-slate-500" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setActive(0);
                  }}
                  onKeyDown={onInputKey}
                  placeholder={`Bölüm/analiz ara… ("+ fikir" yazarak backlog'a ekle)`}
                  className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
                />
                <kbd className="rounded-md border border-white/10 px-1.5 py-0.5 text-[9px] text-slate-500">ESC</kbd>
              </div>

              <div className="max-h-[46vh] overflow-y-auto p-2">
                {items.length === 0 && <p className="px-3 py-6 text-center text-xs text-slate-500">Eşleşme yok.</p>}
                {items.map((it, i) => (
                  <button
                    key={it.id}
                    onMouseEnter={() => setActive(i)}
                    onClick={it.action}
                    disabled={it.disabled}
                    className={cx(
                      "flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-colors",
                      i === active ? "bg-violet-500/15" : "hover:bg-white/[0.04]",
                      it.disabled && "opacity-45"
                    )}
                  >
                    <span
                      className={cx(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl",
                        it.kind === "analysis" && "bg-rose-400/10 text-rose-300",
                        it.kind === "section" && "bg-sky-400/10 text-sky-300",
                        it.kind === "backlog" && "bg-indigo-400/10 text-indigo-300"
                      )}
                    >
                      {it.icon}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-[13px] text-slate-200">{it.label}</span>
                    <span className="flex shrink-0 items-center gap-1 text-[10px] text-slate-500">
                      {it.hint}
                      {i === active && !it.disabled && <CornerDownLeft size={11} />}
                      {it.kind === "section" && <ArrowRight size={11} />}
                    </span>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
