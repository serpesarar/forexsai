"use client";

/**
 * DebateLayer — the adversarial "Tartışma Konseyi / Debate Council"
 * (mirrors the real bias_debate_engine: bull vs bear agents in rounds,
 * a CIO rules, the verdict flows into the Core as the daily macro bias).
 * Speakers take turns; the active agent lights up with typing dots.
 * Clicking the layer opens the full transcript modal. Fully localized.
 */

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scale, Swords } from "lucide-react";
import { useNeuralLocale, type LFn } from "./i18n";
import type { LiveDebate } from "@/lib/api/neural";

/** Localize a raw CIO bias string coming from bias_test (up/down/neutral/bullish/bearish/choppy). */
export function biasWord(bias: string, L: LFn): { word: string; cls: string } {
  const b = bias.toLowerCase();
  if (b.includes("up") || b.includes("bull") || b.includes("long"))
    return { word: L("YUKARI", "UP"), cls: "text-emerald-300" };
  if (b.includes("down") || b.includes("bear") || b.includes("short"))
    return { word: L("AŞAĞI", "DOWN"), cls: "text-red-300" };
  if (b.includes("chop") || b.includes("wait"))
    return { word: L("KARIŞIK", "CHOPPY"), cls: "text-amber-300" };
  return { word: L("NÖTR", "NEUTRAL"), cls: "text-gray-300" };
}

export interface DebateAgent {
  name: string;
  model: string;
  side: "bull" | "bear";
  arg: (L: LFn) => string;
}

export const DEBATE_AGENTS: DebateAgent[] = [
  {
    name: "Makro Boğa", model: "Kimi", side: "bull",
    arg: (L) => L("Fed indirim patikası korunuyor, VIX sakin — risk iştahı güçlü.", "Fed cut path intact, VIX calm — risk appetite is strong."),
  },
  {
    name: "Teknik Boğa", model: "DeepSeek", side: "bull",
    arg: (L) => L("EMA dizilimi ders kitabı gibi; 21.760 POC güçlü destek.", "Textbook EMA stack; 21,760 POC is strong support."),
  },
  {
    name: "Makro Ayı", model: "Kimi", side: "bear",
    arg: (L) => L("10Y faiz sürünerek yükseliyor, bugünkü tahvil ihalesi zayıftı.", "10Y yield keeps grinding up; today's bond auction was weak."),
  },
  {
    name: "Likidite Avcısı", model: "DeepSeek", side: "bear",
    arg: (L) => L("21.910 üstünde stop havuzu var — süpürme riski masada.", "Stop pool sits above 21,910 — a sweep is on the table."),
  },
];

export const CIO_VERDICT = {
  bias: (L: LFn) => L("YUKARI", "UP"),
  conf: 71,
  invalidation: (L: LFn) => L("21.640 altında saatlik kapanış", "hourly close below 21,640"),
  round: (L: LFn) => L("3/3 tur tamamlandı", "3/3 rounds complete"),
};

function TypingDots() {
  return (
    <span className="inline-flex gap-0.5 ml-1.5" aria-hidden>
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1 w-1 rounded-full bg-current"
          animate={{ opacity: [0.2, 1, 0.2] }}
          transition={{ repeat: Infinity, duration: 1, delay: i * 0.18 }}
        />
      ))}
    </span>
  );
}

function AgentChip({ a, active }: { a: DebateAgent; active: boolean }) {
  const { L } = useNeuralLocale();
  const bull = a.side === "bull";
  return (
    <motion.div
      animate={{ scale: active ? 1.03 : 1, opacity: active ? 1 : 0.6 }}
      transition={{ duration: 0.4 }}
      className={`rounded-xl border px-4 py-3 ${
        bull ? "border-emerald-500/30 bg-emerald-500/[0.05]" : "border-red-500/30 bg-red-500/[0.05]"
      } ${active ? (bull ? "shadow-[0_0_24px_rgba(52,211,153,0.15)]" : "shadow-[0_0_24px_rgba(248,113,113,0.15)]") : ""}`}
    >
      <div className="flex items-center gap-2">
        <span className={`h-1.5 w-1.5 rounded-full ${bull ? "bg-emerald-400" : "bg-red-400"}`} />
        <span className="font-mono text-[11px] tracking-[0.15em] text-gray-200">{a.name}</span>
        <span className="font-mono text-[8px] tracking-[0.2em] text-gray-600 border border-white/10 rounded px-1.5 py-0.5">{a.model}</span>
        {active && <span className={bull ? "text-emerald-400" : "text-red-400"}><TypingDots /></span>}
      </div>
      <AnimatePresence mode="wait">
        {active && (
          <motion.p
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.35 }}
            className="mt-1.5 text-[11px] font-light leading-snug text-gray-400 overflow-hidden"
          >
            “{a.arg(L)}”
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function DebateLayer({ onOpen, live }: { onOpen: () => void; live?: LiveDebate }) {
  const { L } = useNeuralLocale();
  const [speaker, setSpeaker] = useState(0);
  const liveBias = live ? biasWord(live.bias, L) : null;

  useEffect(() => {
    const t = setInterval(() => setSpeaker((s) => (s + 1) % DEBATE_AGENTS.length), 3000);
    return () => clearInterval(t);
  }, []);

  const bulls = DEBATE_AGENTS.filter((a) => a.side === "bull");
  const bears = DEBATE_AGENTS.filter((a) => a.side === "bear");

  return (
    <motion.section
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className="relative"
    >
      {/* connector up to the Core */}
      <div className="flex justify-center" aria-hidden>
        <div className="relative h-10 w-px bg-gradient-to-t from-cyan-500/40 to-transparent">
          <motion.span
            className="absolute left-1/2 -translate-x-1/2 h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.9)]"
            animate={{ top: ["90%", "-10%"], opacity: [0, 1, 0] }}
            transition={{ repeat: Infinity, duration: 1.6, ease: "easeIn" }}
          />
        </div>
      </div>

      <button
        onClick={onOpen}
        className="group block w-full text-left rounded-2xl border border-white/[0.07] bg-[#0a0f1c]/80 backdrop-blur-md px-5 py-5 md:px-7 transition-all hover:border-cyan-400/25 hover:shadow-[0_0_40px_rgba(34,211,238,0.07)]"
      >
        <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-amber-400">
            <Swords size={14} />
          </span>
          <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-gray-400">
            {L("Tartışma Konseyi — 8 Ajan Her Sabah Kapışıyor", "Debate Council — 8 Agents Clash Every Morning")}
          </span>
          <span className="font-mono text-[9px] tracking-[0.2em] text-gray-600 border border-white/[0.08] rounded-full px-2.5 py-1">
            {live ? `${live.date ?? ""} · ${live.label}` : CIO_VERDICT.round(L)}
          </span>
          {live && (
            <span className="flex items-center gap-1.5 font-mono text-[9px] tracking-[0.25em] text-emerald-500/90">
              <motion.span
                className="h-1.5 w-1.5 rounded-full bg-emerald-400"
                animate={{ opacity: [1, 0.25, 1] }}
                transition={{ repeat: Infinity, duration: 1.8 }}
              />
              {L("CANLI", "LIVE")}
            </span>
          )}
          <span className="ml-auto font-mono text-[9px] tracking-[0.25em] text-cyan-500/70 opacity-0 group-hover:opacity-100 transition-opacity">
            {L("TIKLA — TAM TRANSKRİPT ↗", "CLICK — FULL TRANSCRIPT ↗")}
          </span>
        </div>

        <div className="grid grid-cols-1 items-center gap-4 lg:grid-cols-[1fr_auto_1fr]">
          <div className="space-y-2.5">
            <div className="font-mono text-[9px] tracking-[0.3em] text-emerald-500/80 mb-1">{L("BOĞA TARAFI", "BULL SIDE")}</div>
            {bulls.map((a) => (
              <AgentChip key={a.name} a={a} active={DEBATE_AGENTS[speaker].name === a.name} />
            ))}
          </div>

          <div className="flex flex-col items-center gap-2 px-2 lg:px-6">
            <motion.div
              animate={{ boxShadow: ["0 0 0px rgba(251,191,36,0)", "0 0 28px rgba(251,191,36,0.25)", "0 0 0px rgba(251,191,36,0)"] }}
              transition={{ repeat: Infinity, duration: 3 }}
              className="flex h-16 w-16 items-center justify-center rounded-full border border-amber-400/40 bg-amber-500/[0.07]"
            >
              <Scale size={22} className="text-amber-300" />
            </motion.div>
            <div className="text-center">
              <div className="font-mono text-[9px] tracking-[0.3em] text-gray-500">{L("CIO KARARI", "CIO VERDICT")}</div>
              <div className={`mt-1 font-mono text-sm font-bold ${liveBias ? liveBias.cls : "text-amber-300"}`}>
                {liveBias ? liveBias.word : CIO_VERDICT.bias(L)} · %{live ? live.conf : CIO_VERDICT.conf}
              </div>
              <div className="mt-0.5 font-mono text-[9px] text-gray-600">
                {live?.mode
                  ? `${L("mod", "mode")}: ${live.mode.replace(/_/g, " ")}`
                  : `${L("geçersiz", "invalid")}: ${CIO_VERDICT.invalidation(L)}`}
              </div>
            </div>
          </div>

          <div className="space-y-2.5">
            <div className="font-mono text-[9px] tracking-[0.3em] text-red-500/80 mb-1 lg:text-right">{L("AYI TARAFI", "BEAR SIDE")}</div>
            {bears.map((a) => (
              <AgentChip key={a.name} a={a} active={DEBATE_AGENTS[speaker].name === a.name} />
            ))}
          </div>
        </div>

        {live?.reason && (
          <p className="mt-4 rounded-xl border border-amber-500/15 bg-amber-500/[0.04] px-4 py-3 text-[12px] font-light leading-relaxed text-gray-400">
            <span className="font-mono text-[9px] tracking-[0.25em] text-amber-500/80 mr-2">{L("CIO GEREKÇESİ", "CIO REASONING")}:</span>
            “{live.reason.length > 260 ? `${live.reason.slice(0, 260)}…` : live.reason}”
          </p>
        )}
        <p className="mt-4 text-[11px] font-light text-gray-600 leading-relaxed">
          <span className="text-cyan-500/70 mr-1.5">◆</span>
          {L(
            "Karşılıklı çürütme 3 tur sürer; 3 yapı ajanı (SMC · kanal · formasyon) gerçek motor çıktısını okur. CIO'nun günlük bias'ı Core'a yumuşak katman olarak akar — sinyalleri tek başına açmaz, hizalıyı güçlendirir, karşıtı frenler.",
            "Rebuttals run for 3 rounds; 3 structure agents (SMC · channel · patterns) read real engine output. The CIO's daily bias flows into the Core as a soft layer — it never opens trades alone, it boosts aligned signals and brakes opposing ones."
          )}
        </p>
      </button>
    </motion.section>
  );
}
