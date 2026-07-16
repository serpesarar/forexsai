"use client";

/**
 * Evrim Paneli — tasarım sistemi (aurora glass).
 * Sakin, modern, animasyonlu. Yoğun tablo hissi yerine nefes alan cam kartlar,
 * yumuşak gradyanlar ve spring geçişleri.
 *
 * Renk kodu (CLAUDE.md ile tutarlı): ml=mavi, emel=mor, pulse=turuncu,
 * smc=teal, ai_panel=amber, meta=pembe.
 */

import { motion, type MotionProps } from "framer-motion";
import { useEffect, useRef, useState, type ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function modelColor(name: string): string {
  const n = name.toLowerCase();
  if (n.startsWith("ml")) return "#60A5FA";
  if (n.includes("emel")) return "#C4B5FD";
  if (n.includes("pulse")) return "#FDBA74";
  if (n.includes("smc")) return "#5EEAD4";
  if (n.includes("ai_panel")) return "#FCD34D";
  if (n.includes("meta")) return "#F9A8D4";
  return "#94A3B8";
}

export const CATEGORY_LABELS: Record<string, string> = {
  signal_engine: "Sinyal Motorları",
  agent: "AI Ajanları",
  learning: "Öğrenme & Analiz",
  gate: "Güvenlik Kapıları",
  data: "Veri Katmanı",
  bot: "Canlı Bot (MT5)",
  infra: "Altyapı",
  error_analysis: "Hata Analizi",
  performance: "Performans",
  backtest: "Backtest",
  pattern_mining: "Örüntü Madenciliği",
  calibration: "Kalibrasyon / Eğitim",
  data_repair: "Veri Onarımı",
  other: "Diğer",
};

export function catLabel(cat: string): string {
  return CATEGORY_LABELS[cat] ?? cat;
}

// ── Animasyon varyantları ────────────────────────────────────────────────

export const fadeUp: MotionProps = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-40px" },
  transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
};

export const stagger = (i: number): MotionProps => ({
  initial: { opacity: 0, y: 16, scale: 0.98 },
  whileInView: { opacity: 1, y: 0, scale: 1 },
  viewport: { once: true, margin: "-30px" },
  transition: { duration: 0.45, delay: Math.min(i * 0.05, 0.4), ease: [0.22, 1, 0.36, 1] },
});

// ── Bölüm ─────────────────────────────────────────────────────────────────

export function Section({
  id,
  title,
  icon,
  subtitle,
  accent = "#8B7CF6",
  children,
}: {
  id: string;
  title: string;
  icon: ReactNode;
  subtitle?: string;
  accent?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-28">
      <motion.div {...fadeUp} className="mb-5 flex items-center gap-4">
        <span
          className="flex h-12 w-12 items-center justify-center rounded-2xl text-white shadow-lg"
          style={{
            background: `linear-gradient(135deg, ${accent}, ${accent}99)`,
            boxShadow: `0 8px 24px -6px ${accent}80`,
          }}
        >
          {icon}
        </span>
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">{title}</h2>
          {subtitle && <p className="mt-0.5 text-sm text-slate-400">{subtitle}</p>}
        </div>
      </motion.div>
      {children}
    </section>
  );
}

// ── Cam kart ────────────────────────────────────────────────────────────

export function GlassCard({
  children,
  className = "",
  hover = false,
  glow,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: string;
}) {
  // Spotlight: fare kartın üzerinde gezerken yumuşak bir ışık takip eder
  // (yalnız CSS değişkeni günceller — reflow/re-render yok, ucuz).
  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty("--spot-x", `${e.clientX - r.left}px`);
    e.currentTarget.style.setProperty("--spot-y", `${e.clientY - r.top}px`);
  };
  return (
    <div
      onMouseMove={onMove}
      className={cx(
        "group/card relative overflow-hidden rounded-3xl border border-white/[0.07] bg-white/[0.025] p-5",
        "shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset]",
        hover && "transition-all duration-300 hover:border-white/15 hover:bg-white/[0.045] hover:-translate-y-0.5",
        className
      )}
      style={glow ? { boxShadow: `0 0 0 1px ${glow}20, 0 12px 40px -16px ${glow}40` } : undefined}
    >
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover/card:opacity-100"
        style={{
          background: "radial-gradient(340px circle at var(--spot-x, 50%) var(--spot-y, 50%), rgba(139,124,246,0.08), transparent 70%)",
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}

/** Yükleme iskeleti — parıltılı placeholder (boş 'Yükleniyor…' yazısı yerine). */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={cx("relative overflow-hidden rounded-xl bg-white/[0.04]", className)}>
      <motion.span
        aria-hidden
        className="absolute inset-0"
        style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent)" }}
        animate={{ x: ["-100%", "100%"] }}
        transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}

// ── Rozet ─────────────────────────────────────────────────────────────────

const TONES: Record<string, string> = {
  slate: "bg-white/[0.06] text-slate-300 ring-white/10",
  green: "bg-emerald-400/10 text-emerald-300 ring-emerald-400/20",
  red: "bg-rose-400/10 text-rose-300 ring-rose-400/20",
  amber: "bg-amber-400/10 text-amber-300 ring-amber-400/20",
  blue: "bg-sky-400/10 text-sky-300 ring-sky-400/20",
  purple: "bg-violet-400/10 text-violet-300 ring-violet-400/20",
  teal: "bg-teal-400/10 text-teal-300 ring-teal-400/20",
};

export function Badge({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: keyof typeof TONES;
}) {
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1", TONES[tone])}>
      {children}
    </span>
  );
}

// ── Gradyan ilerleme çubuğu ────────────────────────────────────────────────

export function ProgressBar({ pct, color, delay = 0 }: { pct: number; color: string; delay?: number }) {
  const clamped = Math.max(2, Math.min(100, pct));
  return (
    <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/[0.05]">
      <motion.div
        initial={{ width: 0 }}
        whileInView={{ width: `${clamped}%` }}
        viewport={{ once: true }}
        transition={{ duration: 1, delay, ease: [0.22, 1, 0.36, 1] }}
        className="h-full rounded-full"
        style={{
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          boxShadow: `0 0 12px ${color}66`,
        }}
      />
    </div>
  );
}

// ── Dairesel ilerleme (gauge) ──────────────────────────────────────────────

export function Ring({
  pct,
  size = 132,
  stroke = 10,
  color = "#8B7CF6",
  children,
}: {
  pct: number;
  size?: number;
  stroke?: number;
  color?: string;
  children?: ReactNode;
}) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          whileInView={{ strokeDashoffset: circ - (circ * clamped) / 100 }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 6px ${color}aa)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">{children}</div>
    </div>
  );
}

// ── Sayaç animasyonu ───────────────────────────────────────────────────────

export function AnimatedNumber({ value, className = "" }: { value: number; className?: string }) {
  const [display, setDisplay] = useState(0);
  const fromRef = useRef(0);

  useEffect(() => {
    const from = fromRef.current;
    const to = value;
    if (from === to) return;
    const dur = 900;
    let raf = 0;
    let start: number | null = null;
    const tick = (t: number) => {
      if (start === null) start = t;
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      const cur = Math.round(from + (to - from) * eased);
      setDisplay(cur);
      fromRef.current = cur;
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = to;
    };
    raf = requestAnimationFrame(tick);
    // Emniyet: rAF kısıtlanırsa (arka plan sekme / bazı gömülü tarayıcılar)
    // süre sonunda kesin değeri göster — sayı asla yanlış kalmasın.
    const safety = setTimeout(() => {
      setDisplay(to);
      fromRef.current = to;
    }, dur + 120);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(safety);
    };
  }, [value]);

  return <span className={className}>{display.toLocaleString("tr-TR")}</span>;
}

// ── Canlı nabız ─────────────────────────────────────────────────────────────

export function PulseDot({ color = "#34D399" }: { color?: string }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-70" style={{ backgroundColor: color }} />
      <span className="relative inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
    </span>
  );
}

export function EmptyState({ text, icon }: { text: string; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-white/10 py-10 text-center text-sm text-slate-500">
      {icon && <span className="text-slate-600">{icon}</span>}
      {text}
    </div>
  );
}

export function timeAgo(iso: string): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const mins = Math.round((Date.now() - then) / 60_000);
  if (mins < 1) return "az önce";
  if (mins < 60) return `${mins} dk önce`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours} sa önce`;
  return `${Math.round(hours / 24)} gün önce`;
}
