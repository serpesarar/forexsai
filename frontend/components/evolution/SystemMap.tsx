"use client";

/**
 * Sistem Haritası — tüm motor/ajan/servislerin kategorili kataloğu.
 * "Sistemde ne var, ne iş yapıyor, canlı mı nasıl anlarım" tek bakışta.
 */

import { useMemo, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, BrainCircuit, ChevronDown, Cpu, Database, GraduationCap, Network, Shield, Wrench } from "lucide-react";

import { type RegistryComponent, useRegistry } from "@/lib/api/evolution";
import { Badge, Card, EmptyState, Section, catLabel } from "./ui";

const CAT_ICONS: Record<string, ReactNode> = {
  signal_engine: <Cpu size={14} />,
  agent: <BrainCircuit size={14} />,
  learning: <GraduationCap size={14} />,
  gate: <Shield size={14} />,
  data: <Database size={14} />,
  bot: <Bot size={14} />,
  infra: <Wrench size={14} />,
};

const CAT_COLORS: Record<string, string> = {
  signal_engine: "#4F8CFF",
  agent: "#A78BFA",
  learning: "#34D399",
  gate: "#F87171",
  data: "#38BDF8",
  bot: "#FB923C",
  infra: "#94A3B8",
};

function ComponentCard({ comp }: { comp: RegistryComponent }) {
  const [open, setOpen] = useState(false);
  const color = CAT_COLORS[comp.category] ?? "#94A3B8";

  return (
    <motion.button
      layout
      onClick={() => setOpen(!open)}
      className="w-full rounded-xl border border-slate-800 bg-[#0d1420] p-3 text-left transition hover:border-slate-600"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-[13px] font-semibold text-slate-200">
          <span
            className="inline-block h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}66` }}
          />
          {comp.name}
        </span>
        <ChevronDown size={14} className={`shrink-0 text-slate-500 transition-transform ${open ? "rotate-180" : ""}`} />
      </div>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <p className="mt-2 text-[11px] leading-relaxed text-slate-400">{comp.purpose}</p>
            <p className="mt-2 font-mono text-[10px] text-slate-500">{comp.file}</p>
            {comp.agents && comp.agents.length > 0 && (
              <div className="mt-2 space-y-1 rounded-lg bg-violet-500/5 p-2">
                <p className="text-[10px] font-semibold text-violet-400">İçindeki ajanlar:</p>
                {comp.agents.map((a) => (
                  <p key={a.id} className="text-[10px] text-slate-400">
                    <span className="font-medium text-slate-300">{a.id}</span> — {a.role}
                  </p>
                ))}
              </div>
            )}
            <p className="mt-2 text-[10px] text-slate-500">
              <span className="font-semibold text-slate-400">Canlılık:</span> {comp.status_hint}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}

export default function SystemMap() {
  const { data, isLoading } = useRegistry();
  const [activeCat, setActiveCat] = useState<string>("signal_engine");

  const grouped = useMemo(() => {
    const g: Record<string, RegistryComponent[]> = {};
    for (const c of data?.components ?? []) (g[c.category] ??= []).push(c);
    return g;
  }, [data]);

  const cats = Object.keys(grouped).sort(
    (a, b) => (grouped[b]?.length ?? 0) - (grouped[a]?.length ?? 0)
  );

  return (
    <Section
      id="harita"
      title="Sistem Haritası"
      icon={<Network size={18} />}
      subtitle={`${data?.components.length ?? 0} kayıtlı bileşen — motorlar, ajanlar, kapılar, veri katmanı`}
    >
      {isLoading && <EmptyState text="Harita yükleniyor…" />}
      {!isLoading && (
        <Card>
          <div className="mb-3 flex flex-wrap gap-1.5">
            {cats.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCat(cat)}
                className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium transition ${
                  activeCat === cat
                    ? "bg-[#4F8CFF]/20 text-[#4F8CFF] ring-1 ring-[#4F8CFF]/40"
                    : "bg-slate-800/70 text-slate-400 hover:text-slate-200"
                }`}
              >
                {CAT_ICONS[cat]} {catLabel(cat)}
                <Badge tone={activeCat === cat ? "blue" : "slate"}>{grouped[cat].length}</Badge>
              </button>
            ))}
          </div>
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {(grouped[activeCat] ?? []).map((c) => (
              <ComponentCard key={c.id} comp={c} />
            ))}
          </div>
        </Card>
      )}
    </Section>
  );
}
