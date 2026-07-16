"use client";

/**
 * Veri Akışı Şeridi — MT5 → Redis → DataHub → 6 Model → Lifecycle → Supabase
 * boru hattının canlı animasyonu. Sistem Haritası'nın üstünde "veri nereden
 * nereye akıyor"u tek bakışta anlatır.
 */

import { motion } from "framer-motion";
import { Boxes, Cpu, Database, HardDrive, Radio, RefreshCcw } from "lucide-react";

const STAGES = [
  { label: "MT5", sub: "tick + bar", icon: <Radio size={15} />, color: "#FB923C" },
  { label: "Redis", sub: "pub/sub", icon: <Boxes size={15} />, color: "#F87171" },
  { label: "DataHub", sub: "tek kaynak", icon: <HardDrive size={15} />, color: "#38BDF8" },
  { label: "6 Model", sub: "sinyal üretimi", icon: <Cpu size={15} />, color: "#C4B5FD" },
  { label: "Lifecycle", sub: "TP / SL takip", icon: <RefreshCcw size={15} />, color: "#34D399" },
  { label: "Supabase", sub: "kalıcı kayıt", icon: <Database size={15} />, color: "#5EEAD4" },
];

function FlowDots({ delay }: { delay: number }) {
  return (
    <div className="relative hidden h-px min-w-6 flex-1 self-center bg-white/[0.08] sm:block">
      {[0, 1].map((k) => (
        <motion.span
          key={k}
          className="absolute top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-sky-300"
          style={{ boxShadow: "0 0 8px 2px #38BDF877" }}
          animate={{ left: ["0%", "100%"], opacity: [0, 1, 1, 0] }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            delay: delay + k * 0.9,
            ease: "linear",
            times: [0, 0.15, 0.85, 1],
          }}
        />
      ))}
    </div>
  );
}

export default function DataFlowRibbon() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-30px" }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mb-5 flex flex-wrap items-stretch gap-2 rounded-3xl border border-white/[0.07] bg-white/[0.02] px-4 py-3.5 sm:flex-nowrap sm:gap-0"
      aria-label="Veri akışı: MT5'ten Supabase'e"
    >
      {STAGES.map((s, i) => (
        <div key={s.label} className="flex flex-1 items-center sm:flex-none">
          <div className="flex items-center gap-2.5 rounded-2xl px-2 py-1">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border"
              style={{ color: s.color, background: `${s.color}14`, borderColor: `${s.color}35` }}
            >
              {s.icon}
            </span>
            <span className="leading-tight">
              <span className="block text-[12px] font-semibold text-slate-200">{s.label}</span>
              <span className="block text-[10px] text-slate-500">{s.sub}</span>
            </span>
          </div>
          {i < STAGES.length - 1 && <FlowDots delay={i * 0.3} />}
        </div>
      ))}
    </motion.div>
  );
}
