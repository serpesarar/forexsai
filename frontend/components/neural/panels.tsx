"use client";

/**
 * panels.tsx — Neural panel building blocks.
 * Every card follows one rule: BÜYÜK değer + TEK cümlelik sade yorum.
 * The user should understand each box in under two seconds.
 */

import { ReactNode, useState } from "react";
import { motion } from "framer-motion";
import { useNeuralLocale } from "./i18n";

// ── Types (mirror backend payload shapes for easy wiring later) ────────────
export type Dir = "BUY" | "SELL" | "HOLD";

export interface ModelVote {
  id: string;
  label: string;
  dir: Dir;
  conf: number; // 0-100
  note: string; // tek cümle
  color: string; // hex accent
}

export interface IndicatorItem {
  name: string;
  value: string;
  pct: number; // 0-100 bar position
  status: "ok" | "warn" | "bad" | "neutral";
  comment: string;
}

export interface PriceLevel {
  price: string;
  label: string; // kaynağı: POC, VAH, Fib...
  kind: "resistance" | "support";
  distancePct: string;
}

export interface NewsItem {
  time: string;
  title: string;
  sentiment: "pos" | "neg" | "neu";
  impact: 1 | 2 | 3;
  source: string;
}

export interface SessionInfo {
  name: string;
  open: boolean;
  range: string;
}

// ── Card shell ─────────────────────────────────────────────────────────────
export function NeuralCard({
  title,
  icon,
  children,
  className = "",
  live = false,
  delay = 0,
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
  className?: string;
  live?: boolean;
  delay?: number;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 26 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`relative overflow-hidden rounded-2xl border border-white/[0.07] bg-[#0a0f1c]/80 backdrop-blur-md ${className}`}
    >
      {/* top energy line */}
      <motion.div
        aria-hidden
        className="absolute top-0 left-0 h-px w-full"
        style={{ background: "linear-gradient(90deg, transparent, rgba(34,211,238,0.5), transparent)" }}
        animate={{ x: ["-100%", "100%"] }}
        transition={{ repeat: Infinity, duration: 4.5, ease: "easeInOut", repeatDelay: 2 }}
      />
      <header className="flex items-center justify-between px-5 pt-4 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-cyan-400">
            {icon}
          </span>
          <h3 className="font-mono text-[11px] uppercase tracking-[0.3em] text-gray-400">{title}</h3>
        </div>
        {live && <LiveBadge />}
      </header>
      <div className="px-5 pb-5">{children}</div>
    </motion.section>
  );
}

function LiveBadge() {
  const { L } = useNeuralLocale();
  return (
    <span className="flex items-center gap-1.5">
      <motion.span
        className="h-1.5 w-1.5 rounded-full bg-emerald-400"
        animate={{ opacity: [1, 0.25, 1] }}
        transition={{ repeat: Infinity, duration: 1.8 }}
      />
      <span className="font-mono text-[9px] tracking-[0.25em] text-gray-600">{L("CANLI", "LIVE")}</span>
    </span>
  );
}

// ── Plain-language comment line ────────────────────────────────────────────
export function Comment({ children, tone = "neutral" }: { children: ReactNode; tone?: "pos" | "neg" | "neutral" }) {
  const color = tone === "pos" ? "text-emerald-400/90" : tone === "neg" ? "text-red-400/90" : "text-gray-400";
  return (
    <p className={`mt-3 text-[13px] leading-relaxed font-light ${color}`}>
      <span className="mr-1.5 text-cyan-500/70">◆</span>
      {children}
    </p>
  );
}

// ── VIX gauge ──────────────────────────────────────────────────────────────
const VIX_ZONES = [
  { to: 17, tr: "SAKİN", en: "CALM", color: "#34d399" },
  { to: 24, tr: "NORMAL", en: "NORMAL", color: "#22d3ee" },
  { to: 32, tr: "GERGİN", en: "TENSE", color: "#fbbf24" },
  { to: 45, tr: "PANİK", en: "PANIC", color: "#f87171" },
];

export function VixGauge({ value, change, comment, tone }: { value: number; change: string; comment: string; tone: "pos" | "neg" | "neutral" }) {
  const { L } = useNeuralLocale();
  const MIN = 10;
  const MAX = 45;
  const pct = Math.min(100, Math.max(0, ((value - MIN) / (MAX - MIN)) * 100));
  const zone = VIX_ZONES.find((z) => value < z.to) ?? VIX_ZONES[VIX_ZONES.length - 1];

  return (
    <div>
      <div className="flex items-end justify-between mb-4">
        <div>
          <span className="text-4xl font-bold font-mono text-white">{value.toFixed(1)}</span>
          <span className="ml-2 font-mono text-xs text-gray-500">{change}</span>
        </div>
        <span
          className="rounded-md border px-2.5 py-1 font-mono text-[10px] tracking-[0.25em]"
          style={{ color: zone.color, borderColor: `${zone.color}55`, background: `${zone.color}14` }}
        >
          {L(zone.tr, zone.en)}
        </span>
      </div>
      {/* zone bar */}
      <div className="relative h-2.5 rounded-full overflow-hidden flex">
        {VIX_ZONES.map((z, i) => {
          const from = i === 0 ? MIN : VIX_ZONES[i - 1].to;
          const w = ((Math.min(z.to, MAX) - from) / (MAX - MIN)) * 100;
          return <div key={z.tr} style={{ width: `${w}%`, background: `${z.color}40` }} />;
        })}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 h-4 w-4 rounded-full border-2 border-white bg-black shadow-[0_0_12px_rgba(255,255,255,0.5)]"
          initial={{ left: "0%" }}
          whileInView={{ left: `calc(${pct}% - 8px)` }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <div className="mt-1.5 flex justify-between font-mono text-[9px] text-gray-600">
        <span>10</span><span>17</span><span>24</span><span>32</span><span>45+</span>
      </div>
      <Comment tone={tone}>{comment}</Comment>
    </div>
  );
}

// ── Macro tiles ────────────────────────────────────────────────────────────
export function MacroTiles({
  items,
  comment,
  tone,
}: {
  items: { label: string; value: string; change: string; up: boolean }[];
  comment: string;
  tone: "pos" | "neg" | "neutral";
}) {
  return (
    <div>
      <div className="grid grid-cols-3 gap-2.5">
        {items.map((m) => (
          <div key={m.label} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-3 text-center">
            <div className="font-mono text-[9px] tracking-[0.25em] text-gray-600 mb-1">{m.label}</div>
            <div className="font-mono text-sm text-white">{m.value}</div>
            <div className={`font-mono text-[10px] mt-0.5 ${m.up ? "text-emerald-400" : "text-red-400"}`}>
              {m.up ? "▲" : "▼"} {m.change}
            </div>
          </div>
        ))}
      </div>
      <Comment tone={tone}>{comment}</Comment>
    </div>
  );
}

// ── Indicator rows ─────────────────────────────────────────────────────────
const STATUS_COLOR = { ok: "#34d399", warn: "#fbbf24", bad: "#f87171", neutral: "#22d3ee" };

export function IndicatorList({ items }: { items: IndicatorItem[] }) {
  return (
    <div className="space-y-4">
      {items.map((it, i) => (
        <div key={it.name}>
          <div className="flex items-baseline justify-between mb-1.5">
            <span className="font-mono text-[11px] tracking-[0.15em] text-gray-300">{it.name}</span>
            <span className="font-mono text-sm font-bold" style={{ color: STATUS_COLOR[it.status] }}>
              {it.value}
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: `linear-gradient(90deg, ${STATUS_COLOR[it.status]}55, ${STATUS_COLOR[it.status]})` }}
              initial={{ width: "0%" }}
              whileInView={{ width: `${it.pct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
          <p className="mt-1 text-[11px] font-light text-gray-500">{it.comment}</p>
        </div>
      ))}
    </div>
  );
}

// ── Price level ladder ─────────────────────────────────────────────────────
export function LevelLadder({ levels, price, priceNote }: { levels: PriceLevel[]; price: string; priceNote: string }) {
  const { L } = useNeuralLocale();
  const res = levels.filter((l) => l.kind === "resistance");
  const sup = levels.filter((l) => l.kind === "support");

  const Row = ({ l, i }: { l: PriceLevel; i: number }) => (
    <motion.div
      initial={{ opacity: 0, x: l.kind === "resistance" ? 16 : -16 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay: i * 0.08, duration: 0.5 }}
      className="flex items-center gap-3"
    >
      <span className={`font-mono text-sm w-20 ${l.kind === "resistance" ? "text-red-300" : "text-emerald-300"}`}>{l.price}</span>
      <div className={`h-px flex-1 ${l.kind === "resistance" ? "bg-red-500/25" : "bg-emerald-500/25"}`} />
      <span className="font-mono text-[9px] tracking-[0.2em] text-gray-500 uppercase">{l.label}</span>
      <span className="font-mono text-[10px] text-gray-600 w-12 text-right">{l.distancePct}</span>
    </motion.div>
  );

  return (
    <div className="space-y-2.5">
      {res.map((l, i) => (
        <Row key={l.price} l={l} i={res.length - 1 - i} />
      ))}
      {/* current price */}
      <div className="relative flex items-center gap-3 py-1">
        <motion.span
          className="font-mono text-base font-bold text-cyan-300 w-20"
          animate={{ opacity: [1, 0.65, 1] }}
          transition={{ repeat: Infinity, duration: 2.4 }}
        >
          {price}
        </motion.span>
        <div className="relative h-[2px] flex-1 bg-cyan-400/60 rounded-full overflow-hidden">
          <motion.div
            className="absolute inset-y-0 w-1/4 bg-gradient-to-r from-transparent via-white/80 to-transparent"
            animate={{ left: ["-25%", "100%"] }}
            transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
          />
        </div>
        <span className="font-mono text-[9px] tracking-[0.2em] text-cyan-500 uppercase">{L("ŞU AN", "NOW")}</span>
      </div>
      {sup.map((l, i) => (
        <Row key={l.price} l={l} i={i} />
      ))}
      <Comment>{priceNote}</Comment>
    </div>
  );
}

// ── News feed ──────────────────────────────────────────────────────────────
const SENT = {
  pos: { icon: "▲", cls: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  neg: { icon: "▼", cls: "text-red-400 border-red-500/30 bg-red-500/10" },
  neu: { icon: "◆", cls: "text-gray-400 border-white/10 bg-white/[0.04]" },
};

export function NewsList({ items }: { items: NewsItem[] }) {
  return (
    <div className="space-y-3">
      {items.map((n, i) => (
        <motion.article
          key={n.title}
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.09, duration: 0.5 }}
          className="flex items-start gap-3 rounded-xl border border-white/[0.05] bg-white/[0.02] p-3 hover:bg-white/[0.04] transition-colors"
        >
          <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border text-[10px] ${SENT[n.sentiment].cls}`}>
            {SENT[n.sentiment].icon}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-[13px] leading-snug text-gray-200">{n.title}</p>
            <div className="mt-1 flex items-center gap-2.5 font-mono text-[9px] tracking-[0.15em] text-gray-600">
              <span>{n.time}</span>
              <span>·</span>
              <span>{n.source}</span>
              <span className="ml-auto flex gap-0.5">
                {[1, 2, 3].map((d) => (
                  <span key={d} className={`h-1 w-1 rounded-full ${d <= n.impact ? "bg-amber-400" : "bg-white/10"}`} />
                ))}
              </span>
            </div>
          </div>
        </motion.article>
      ))}
    </div>
  );
}

// ── Active signal ──────────────────────────────────────────────────────────
export function ActiveSignal({
  dir,
  entry,
  current,
  pips,
  conf,
  targets,
  sl,
  comment,
}: {
  dir: Dir;
  entry: string;
  current: string;
  pips: string;
  conf: number;
  targets: { price: string; hit: boolean }[];
  sl: string;
  comment: string;
}) {
  const buy = dir === "BUY";
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span
          className={`px-3 py-1.5 rounded-lg font-mono text-xs font-bold tracking-[0.2em] border ${
            buy ? "text-emerald-300 border-emerald-500/40 bg-emerald-500/10" : "text-red-300 border-red-500/40 bg-red-500/10"
          }`}
        >
          {buy ? "▲ BUY" : "▼ SELL"} · %{conf}
        </span>
        <div className="text-right">
          <div className={`font-mono text-lg font-bold ${pips.startsWith("+") ? "text-emerald-400" : "text-red-400"}`}>{pips}</div>
          <div className="font-mono text-[9px] tracking-[0.2em] text-gray-600">ANLIK K/Z</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2.5 mb-4">
        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
          <div className="font-mono text-[9px] tracking-[0.2em] text-gray-600">GİRİŞ</div>
          <div className="font-mono text-sm text-white">{entry}</div>
        </div>
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/[0.05] px-3 py-2">
          <div className="font-mono text-[9px] tracking-[0.2em] text-cyan-500">ŞU AN</div>
          <div className="font-mono text-sm text-cyan-200">{current}</div>
        </div>
      </div>

      {/* TP ladder */}
      <div className="space-y-2">
        {targets.map((t, i) => (
          <div key={t.price} className="flex items-center gap-3">
            <span className={`flex h-5 w-9 items-center justify-center rounded font-mono text-[9px] tracking-wider border ${
              t.hit ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-300" : "border-white/10 bg-white/[0.03] text-gray-500"
            }`}>
              TP{i + 1}
            </span>
            <div className="h-1 flex-1 rounded-full bg-white/[0.05] overflow-hidden">
              {t.hit && (
                <motion.div
                  className="h-full bg-gradient-to-r from-emerald-600 to-emerald-300"
                  initial={{ width: "0%" }}
                  whileInView={{ width: "100%" }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, delay: i * 0.15 }}
                />
              )}
            </div>
            <span className={`font-mono text-xs w-16 text-right ${t.hit ? "text-emerald-300" : "text-gray-400"}`}>{t.price}</span>
            {t.hit ? <span className="text-emerald-400 text-xs">✓</span> : <span className="w-3.5" />}
          </div>
        ))}
        <div className="flex items-center gap-3 pt-1">
          <span className="flex h-5 w-9 items-center justify-center rounded font-mono text-[9px] tracking-wider border border-red-500/30 bg-red-500/10 text-red-400">
            SL
          </span>
          <div className="h-px flex-1 bg-red-500/20" />
          <span className="font-mono text-xs w-16 text-right text-red-300">{sl}</span>
          <span className="w-3.5" />
        </div>
      </div>
      <Comment tone={buy ? "pos" : "neg"}>{comment}</Comment>
    </div>
  );
}

// ── Session strip + next event ─────────────────────────────────────────────
export function SessionStrip({ sessions, nextEvent, gateWarning }: { sessions: SessionInfo[]; nextEvent: string; gateWarning?: string }) {
  return (
    <div>
      <div className="grid grid-cols-4 gap-2">
        {sessions.map((s) => (
          <div
            key={s.name}
            className={`rounded-xl border px-2 py-2.5 text-center ${
              s.open ? "border-emerald-500/30 bg-emerald-500/[0.06]" : "border-white/[0.05] bg-white/[0.02]"
            }`}
          >
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <span className={`h-1.5 w-1.5 rounded-full ${s.open ? "bg-emerald-400" : "bg-gray-700"}`} />
              <span className={`font-mono text-[10px] tracking-[0.15em] ${s.open ? "text-emerald-300" : "text-gray-500"}`}>{s.name}</span>
            </div>
            <div className="font-mono text-[9px] text-gray-600">{s.range}</div>
          </div>
        ))}
      </div>
      <Comment>{nextEvent}</Comment>
      {gateWarning && (
        <p className="mt-2 flex items-center gap-2 rounded-lg border border-amber-500/25 bg-amber-500/[0.07] px-3 py-2 text-[12px] text-amber-300/90">
          <span className="text-amber-400">⚠</span> {gateWarning}
        </p>
      )}
    </div>
  );
}

// ── Decision timeline (Core'un gün içi karar akışı) ────────────────────────
export function DecisionTimeline({ points }: { points: { t: string; dir: Dir; conf: number }[] }) {
  const chip = (d: Dir) =>
    d === "BUY"
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
      : d === "SELL"
      ? "border-red-500/40 bg-red-500/10 text-red-300"
      : "border-white/15 bg-white/[0.04] text-gray-400";
  return (
    <div>
      <div className="relative flex items-start justify-between gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {/* connecting line */}
        <div className="absolute left-0 right-0 top-[9px] h-px bg-gradient-to-r from-transparent via-cyan-500/25 to-cyan-500/50" aria-hidden />
        {points.map((p, i) => {
          const last = i === points.length - 1;
          return (
            <motion.div
              key={p.t}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="relative flex min-w-[70px] flex-col items-center gap-2"
            >
              <span className={`relative z-10 h-[18px] w-[18px] rounded-full border-2 ${last ? "border-cyan-300 bg-cyan-500/30" : "border-white/20 bg-[#0a0f1c]"}`}>
                {last && (
                  <motion.span
                    className="absolute inset-[-6px] rounded-full border border-cyan-400/50"
                    animate={{ scale: [1, 1.5], opacity: [0.8, 0] }}
                    transition={{ repeat: Infinity, duration: 1.6 }}
                  />
                )}
              </span>
              <span className="font-mono text-[9px] tracking-[0.15em] text-gray-600">{p.t}</span>
              <span className={`rounded-md border px-2 py-0.5 font-mono text-[10px] font-bold ${chip(p.dir)}`}>
                {p.dir}
                {p.dir !== "HOLD" && ` %${p.conf}`}
              </span>
            </motion.div>
          );
        })}
      </div>
      <TimelineNote />
    </div>
  );
}

function TimelineNote() {
  const { L } = useNeuralLocale();
  return (
    <Comment>
      {L(
        "Core gün boyunca kararını yeniden değerlendirir — çizgideki tutarlılık, sinyalin arkasındaki kararlılığı gösterir.",
        "The Core keeps re-evaluating its call through the day — consistency along this line shows conviction behind the signal."
      )}
    </Comment>
  );
}

// ── Position size calculator (interaktif) ──────────────────────────────────
export function PositionCalc({ slPoints, symbolNote }: { slPoints: number; symbolNote: string }) {
  const { L } = useNeuralLocale();
  const [balance, setBalance] = useState(10000);
  const [risk, setRisk] = useState(1.0);
  const riskUsd = (balance * risk) / 100;
  const lots = riskUsd / slPoints; // demo varsayımı: 1 lot = 1$/puan

  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
      <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.3em] text-gray-500">
        {L("Pozisyon Hesaplayıcı", "Position Calculator")}
      </div>

      {/* balance presets */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {[5000, 10000, 25000, 50000].map((b) => (
          <button
            key={b}
            onClick={() => setBalance(b)}
            className={`rounded-lg border px-3 py-1.5 font-mono text-[10px] transition-all ${
              balance === b
                ? "border-cyan-400/50 bg-cyan-500/10 text-cyan-300"
                : "border-white/[0.07] text-gray-500 hover:text-gray-300"
            }`}
          >
            ${(b / 1000).toFixed(0)}k
          </button>
        ))}
      </div>

      {/* risk slider */}
      <div className="mb-1 flex items-center justify-between">
        <span className="font-mono text-[10px] text-gray-500">{L("RİSK", "RISK")}</span>
        <span className="font-mono text-xs font-bold text-cyan-300">%{risk.toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={0.25}
        max={3}
        step={0.25}
        value={risk}
        onChange={(e) => setRisk(parseFloat(e.target.value))}
        className="w-full accent-cyan-400"
        aria-label="Risk yüzdesi"
      />

      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] py-2">
          <div className="font-mono text-[9px] text-gray-600">{L("RİSK $", "RISK $")}</div>
          <div className="font-mono text-sm font-bold text-white">${riskUsd.toFixed(0)}</div>
        </div>
        <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] py-2">
          <div className="font-mono text-[9px] text-gray-600">{L("SL MESAFE", "SL DISTANCE")}</div>
          <div className="font-mono text-sm font-bold text-white">{slPoints}p</div>
        </div>
        <div className="rounded-lg bg-cyan-500/[0.07] border border-cyan-400/25 py-2">
          <div className="font-mono text-[9px] text-cyan-500">{L("ÖNERİLEN", "SUGGESTED")}</div>
          <div className="font-mono text-sm font-bold text-cyan-300">{lots.toFixed(2)} lot</div>
        </div>
      </div>
      <p className="mt-2.5 text-[10px] font-light text-gray-600 leading-relaxed">{symbolNote}</p>
    </div>
  );
}

// ── Whale / COT positioning (all symbols) ──────────────────────────────────
export function WhaleCotPanel({
  pressure,
  label,
  specLongPct,
  specNet,
  commNet,
}: {
  pressure: number; // -1..+1
  label: string;
  specLongPct: number;
  specNet: number;
  commNet: number;
}) {
  const { L } = useNeuralLocale();
  const pct = Math.min(100, Math.max(0, (pressure + 1) * 50));
  const bull = pressure > 0.1;
  const bear = pressure < -0.1;
  const fmtNet = (n: number) =>
    `${n >= 0 ? "+" : "−"}${Math.abs(n) >= 1000 ? `${(Math.abs(n) / 1000).toFixed(0)}k` : Math.abs(n).toFixed(0)}`;

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <span className={`text-3xl font-bold font-mono ${bull ? "text-emerald-300" : bear ? "text-red-300" : "text-gray-200"}`}>
            {pressure >= 0 ? "+" : ""}{pressure.toFixed(2)}
          </span>
          <span className="ml-2 font-mono text-[10px] tracking-[0.2em] text-gray-600">{L("BALİNA BASKISI", "WHALE PRESSURE")}</span>
        </div>
        <span className={`rounded-md border px-2.5 py-1 font-mono text-[10px] tracking-[0.25em] ${
          bull ? "text-emerald-300 border-emerald-500/40 bg-emerald-500/10" : bear ? "text-red-300 border-red-500/40 bg-red-500/10" : "text-gray-400 border-white/15 bg-white/[0.04]"
        }`}>
          {label.toUpperCase()}
        </span>
      </div>

      {/* -1 .. +1 pressure bar */}
      <div className="relative h-2.5 rounded-full overflow-hidden bg-gradient-to-r from-red-500/35 via-white/[0.06] to-emerald-500/35">
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 h-4 w-4 rounded-full border-2 border-white bg-black shadow-[0_0_12px_rgba(255,255,255,0.5)]"
          initial={{ left: "50%" }}
          whileInView={{ left: `calc(${pct}% - 8px)` }}
          viewport={{ once: true }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <div className="mt-1.5 flex justify-between font-mono text-[9px] text-gray-600">
        <span>{L("AYI −1", "BEAR −1")}</span><span>0</span><span>{L("BOĞA +1", "BULL +1")}</span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2.5">
        {[
          { l: L("SPEC LONG", "SPEC LONG"), v: `%${specLongPct.toFixed(1)}`, c: specLongPct >= 55 ? "text-emerald-300" : specLongPct <= 45 ? "text-red-300" : "text-gray-200" },
          { l: L("SPEKÜLATÖR NET", "SPECULATOR NET"), v: fmtNet(specNet), c: specNet >= 0 ? "text-emerald-300" : "text-red-300" },
          { l: L("TİCARİ NET", "COMMERCIAL NET"), v: fmtNet(commNet), c: commNet >= 0 ? "text-emerald-300" : "text-red-300" },
        ].map((t) => (
          <div key={t.l} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-2 py-2.5 text-center">
            <div className="font-mono text-[8px] tracking-[0.15em] text-gray-600 mb-1">{t.l}</div>
            <div className={`font-mono text-sm font-bold ${t.c}`}>{t.v}</div>
          </div>
        ))}
      </div>

      <Comment tone={bull ? "pos" : bear ? "neg" : "neutral"}>
        {bull
          ? L("Büyük oyuncular alım tarafında yığılmış — kurumsal para yukarıyı destekliyor (CFTC COT verisi, haftalık).", "Big players are stacked on the long side — institutional money backs the upside (CFTC COT data, weekly).")
          : bear
          ? L("Büyük oyuncular satış tarafında — kurumsal para aşağı yönü destekliyor (CFTC COT verisi, haftalık).", "Big players lean short — institutional money backs the downside (CFTC COT data, weekly).")
          : L("Kurumsal konumlanma dengede — COT tarafından net bir yön sinyali yok.", "Institutional positioning is balanced — no clear directional signal from COT.")}
      </Comment>
    </div>
  );
}

// ── Oil physical-market intelligence (USOIL) ───────────────────────────────
export function OilIntelPanel({
  regime,
  bias,
  conf,
  recession,
  bdti,
  bcti,
  storage,
  physical,
  summary,
  mapHref = "/oil",
}: {
  regime: string;
  bias: string;
  conf: number;
  recession: number;
  bdti: number;
  bcti: number;
  storage: number;
  physical: number;
  summary: string;
  mapHref?: string;
}) {
  const { L } = useNeuralLocale();
  const bull = bias.toLowerCase().includes("bull");
  const contango = regime.toLowerCase().includes("contango");

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className={`rounded-md border px-2.5 py-1 font-mono text-[10px] tracking-[0.25em] ${
          contango ? "text-amber-300 border-amber-500/40 bg-amber-500/10" : "text-emerald-300 border-emerald-500/40 bg-emerald-500/10"
        }`}>
          {regime.toUpperCase()}
        </span>
        <span className={`rounded-md border px-2.5 py-1 font-mono text-[10px] tracking-[0.25em] ${
          bull ? "text-emerald-300 border-emerald-500/40 bg-emerald-500/10" : "text-red-300 border-red-500/40 bg-red-500/10"
        }`}>
          {L("FİZİKSEL BIAS", "PHYSICAL BIAS")}: {bias.toUpperCase()} %{conf}
        </span>
        <a
          href={mapHref}
          className="ml-auto font-mono text-[9px] tracking-[0.25em] text-cyan-400/80 hover:text-cyan-300 transition-colors border-b border-cyan-500/30 pb-0.5"
        >
          {L("GEMİ HARİTASINI AÇ ↗", "OPEN SHIP MAP ↗")}
        </a>
      </div>

      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        {[
          { l: L("BDTI (KİRLİ TANKER)", "BDTI (DIRTY TANKER)"), v: bdti.toFixed(1) },
          { l: L("BCTI (TEMİZ TANKER)", "BCTI (CLEAN TANKER)"), v: bcti.toFixed(1) },
          { l: L("YÜZEN DEPOLAMA", "FLOATING STORAGE"), v: `%${storage}` },
          { l: L("RESESYON OLASILIĞI", "RECESSION PROB."), v: `%${recession}` },
        ].map((t) => (
          <div key={t.l} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-2 py-2.5 text-center">
            <div className="font-mono text-[8px] tracking-[0.12em] text-gray-600 mb-1">{t.l}</div>
            <div className="font-mono text-sm font-bold text-gray-100">{t.v}</div>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <div className="flex justify-between mb-1.5">
          <span className="font-mono text-[10px] tracking-[0.2em] text-gray-500">{L("FİZİKSEL PİYASA SKORU", "PHYSICAL MARKET SCORE")}</span>
          <span className="font-mono text-xs font-bold text-cyan-300">{physical}/100</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-cyan-300"
            initial={{ width: 0 }}
            whileInView={{ width: `${Math.min(100, Math.max(0, physical))}%` }}
            viewport={{ once: true }}
            transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
      </div>

      <Comment tone={bull ? "pos" : "neg"}>
        {L(
          `Tanker navlunları + yüzen depolama + vadeli eğri birlikte okunuyor. Motor özeti: ${summary}`,
          `Tanker freight + floating storage + the futures curve read together. Engine summary: ${summary}`
        )}
      </Comment>
    </div>
  );
}

// ── Core activity log ──────────────────────────────────────────────────────
export function CoreLog({ lines }: { lines: { t: string; msg: string }[] }) {
  return (
    <div className="font-mono text-[11px] space-y-1.5">
      {lines.map((l, i) => (
        <motion.div
          key={`${l.t}-${i}`}
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.12, duration: 0.4 }}
          className="flex gap-3"
        >
          <span className="text-cyan-600 shrink-0">{l.t}</span>
          <span className="text-gray-400">{l.msg}</span>
        </motion.div>
      ))}
    </div>
  );
}
