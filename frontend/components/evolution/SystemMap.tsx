"use client";

/**
 * Sistem Haritası — tüm motor/ajan/servislerin kategorili kataloğu.
 * "Sistemde ne var, ne iş yapıyor, canlı mı" tek bakışta.
 */

import { useMemo, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, BrainCircuit, ChevronDown, Cpu, Database, GraduationCap, Network, Shield, Wrench } from "lucide-react";

import { type RegistryComponent, useRegistry } from "@/lib/api/evolution";
import { Badge, EmptyState, GlassCard, Section, catLabel, cx, stagger } from "./ui";

const CAT_ICONS: Record<string, ReactNode> = {
  signal_engine: <Cpu size={15} />,
  agent: <BrainCircuit size={15} />,
  learning: <GraduationCap size={15} />,
  gate: <Shield size={15} />,
  data: <Database size={15} />,
  bot: <Bot size={15} />,
  infra: <Wrench size={15} />,
};

const CAT_COLORS: Record<string, string> = {
  signal_engine: "#60A5FA",
  agent: "#C4B5FD",
  learning: "#34D399",
  gate: "#FB7185",
  data: "#38BDF8",
  bot: "#FB923C",
  infra: "#94A3B8",
};

function ComponentCard({ comp, index }: { comp: RegistryComponent; index: number }) {
  const [open, setOpen] = useState(false);
  const color = CAT_COLORS[comp.category] ?? "#94A3B8";

  return (
    <motion.button
      {...stagger(index)}
      layout
      onClick={() => setOpen(!open)}
      className="w-full rounded-2xl border border-white/[0.07] bg-white/[0.02] p-3.5 text-left transition hover:border-white/15 hover:bg-white/[0.04]"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2.5 text-[13px] font-semibold text-slate-100">
          <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: color, boxShadow: `0 0 8px ${color}` }} />
          {comp.name}
        </span>
        <ChevronDown size={14} className={cx("shrink-0 text-slate-500 transition-transform", open && "rotate-180")} />
      </div>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22 }} className="overflow-hidden">
            <p className="mt-2.5 text-[11px] leading-relaxed text-slate-400">{comp.purpose}</p>
            <p className="mt-2 font-mono text-[10px] text-slate-600">{comp.file}</p>
            {comp.agents && comp.agents.length > 0 && (
              <div className="mt-2.5 space-y-1 rounded-xl bg-violet-500/[0.06] p-2.5">
                <p className="text-[10px] font-semibold text-violet-300">İçindeki ajanlar:</p>
                {comp.agents.map((a) => (
                  <p key={a.id} className="text-[10px] text-slate-400">
                    <span className="font-medium text-slate-300">{a.id}</span> — {a.role}
                  </p>
                ))}
              </div>
            )}
            <p className="mt-2.5 text-[10px] text-slate-500">
              <span className="font-semibold text-slate-400">Canlılık:</span> {comp.status_hint}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}

export default function SystemMap() {
  const { data } = useRegistry();
  const [activeCat, setActiveCat] = useState<string>("signal_engine");

  const grouped = useMemo(() => {
    const g: Record<string, RegistryComponent[]> = {};
    for (const c of data?.components ?? []) (g[c.category] ??= []).push(c);
    return g;
  }, [data]);

  const cats = Object.keys(grouped).sort((a, b) => (grouped[b]?.length ?? 0) - (grouped[a]?.length ?? 0));

  return (
    <Section
      id="harita"
      title="Sistem Haritası"
      subtitle={`${data?.components.length ?? 0} bileşen — motorlar, ajanlar, kapılar, veri`}
      accent="#38BDF8"
      icon={<Network size={22} />}
    >
      <GlassCard>
        <div className="mb-4 flex flex-wrap gap-2">
          {cats.map((cat) => {
            const active = activeCat === cat;
            const color = CAT_COLORS[cat] ?? "#94A3B8";
            return (
              <button
                key={cat}
                onClick={() => setActiveCat(cat)}
                className={cx("flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[12px] font-medium transition", active ? "text-white" : "bg-white/[0.04] text-slate-400 hover:text-slate-200")}
                style={active ? { background: `${color}22`, boxShadow: `inset 0 0 0 1px ${color}55` } : undefined}
              >
                <span style={{ color: active ? color : undefined }}>{CAT_ICONS[cat]}</span>
                {catLabel(cat)}
                <span className="opacity-60">{grouped[cat].length}</span>
              </button>
            );
          })}
        </div>
        {cats.length === 0 && <EmptyState text="Harita yükleniyor…" />}
        <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
          {(grouped[activeCat] ?? []).map((c, i) => (
            <ComponentCard key={c.id} comp={c} index={i} />
          ))}
        </div>
      </GlassCard>
    </Section>
  );
}
