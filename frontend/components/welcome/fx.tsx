"use client";

/**
 * fx.tsx — Welcome page animation primitives.
 *
 * Shared, dependency-free (framer-motion only) building blocks used by the
 * landing page: scroll progress bar, magnetic buttons, 3D tilt cards,
 * count-up stats, word-by-word headline reveals and an infinite marquee.
 */

import { ReactNode, useEffect, useRef } from "react";
import {
  motion,
  animate,
  useInView,
  useMotionValue,
  useMotionTemplate,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
} from "framer-motion";

// ── Scroll progress bar (fixed, top) ───────────────────────────────────────
export function ScrollProgressBar() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 30, mass: 0.4 });
  return (
    <motion.div
      style={{ scaleX }}
      className="fixed top-0 left-0 right-0 h-[2px] z-[100] origin-left bg-gradient-to-r from-cyan-400 via-purple-400 to-emerald-400"
      aria-hidden
    />
  );
}

// ── Magnetic hover wrapper ─────────────────────────────────────────────────
export function Magnetic({
  children,
  strength = 0.35,
  className = "",
}: {
  children: ReactNode;
  strength?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 180, damping: 14, mass: 0.3 });
  const sy = useSpring(y, { stiffness: 180, damping: 14, mass: 0.3 });

  const onMove = (e: React.MouseEvent) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    x.set((e.clientX - (r.left + r.width / 2)) * strength);
    y.set((e.clientY - (r.top + r.height / 2)) * strength);
  };
  const onLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{ x: sx, y: sy }}
      className={`inline-block ${className}`}
    >
      {children}
    </motion.div>
  );
}

// ── 3D tilt card with cursor glare ─────────────────────────────────────────
export function TiltCard({
  children,
  className = "",
  maxTilt = 9,
}: {
  children: ReactNode;
  className?: string;
  maxTilt?: number;
}) {
  const px = useMotionValue(0.5);
  const py = useMotionValue(0.5);
  const rX = useSpring(useTransform(py, [0, 1], [maxTilt, -maxTilt]), { stiffness: 160, damping: 18 });
  const rY = useSpring(useTransform(px, [0, 1], [-maxTilt, maxTilt]), { stiffness: 160, damping: 18 });
  const gx = useTransform(px, (v) => v * 100);
  const gy = useTransform(py, (v) => v * 100);
  const glare = useMotionTemplate`radial-gradient(420px circle at ${gx}% ${gy}%, rgba(255,255,255,0.09), transparent 55%)`;

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    px.set((e.clientX - r.left) / r.width);
    py.set((e.clientY - r.top) / r.height);
  };
  const onLeave = () => {
    px.set(0.5);
    py.set(0.5);
  };

  return (
    <motion.div
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{ rotateX: rX, rotateY: rY, transformStyle: "preserve-3d", perspective: 900 }}
      className={`relative ${className}`}
    >
      <motion.div
        style={{ background: glare }}
        className="pointer-events-none absolute inset-0 rounded-2xl z-10"
        aria-hidden
      />
      {children}
    </motion.div>
  );
}

// ── Count-up stat number ───────────────────────────────────────────────────
export function CountUp({
  to,
  suffix = "",
  prefix = "",
  decimals = 0,
  duration = 2.2,
  className = "",
}: {
  to: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  duration?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || !inView) return;
    if (reduced) {
      el.textContent = `${prefix}${to.toFixed(decimals)}${suffix}`;
      return;
    }
    const controls = animate(0, to, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => {
        el.textContent = `${prefix}${v.toFixed(decimals)}${suffix}`;
      },
    });
    return () => controls.stop();
  }, [inView, to, suffix, prefix, decimals, duration, reduced]);

  return (
    <span ref={ref} className={className}>
      {prefix}0{suffix}
    </span>
  );
}

// ── Word-by-word headline reveal ───────────────────────────────────────────
export function WordReveal({
  text,
  className = "",
  wordClassName = "",
  delay = 0,
  once = true,
}: {
  text: string;
  className?: string;
  wordClassName?: string;
  delay?: number;
  once?: boolean;
}) {
  const words = text.split(" ");
  return (
    <motion.span
      className={`inline-block ${className}`}
      initial="hidden"
      whileInView="show"
      viewport={{ once, margin: "-80px" }}
      variants={{ show: { transition: { staggerChildren: 0.07, delayChildren: delay } } }}
    >
      {words.map((w, i) => (
        <span key={`${w}-${i}`} className="inline-block overflow-hidden align-bottom pb-[0.12em] -mb-[0.12em]">
          <motion.span
            className={`inline-block will-change-transform ${wordClassName}`}
            variants={{
              hidden: { y: "115%", opacity: 0, filter: "blur(6px)" },
              show: {
                y: "0%",
                opacity: 1,
                filter: "blur(0px)",
                transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
              },
            }}
          >
            {w}
            {i < words.length - 1 ? " " : ""}
          </motion.span>
        </span>
      ))}
    </motion.span>
  );
}

// ── Per-letter cascade reveal (hero title) ─────────────────────────────────
export function LetterCascade({
  text,
  className = "",
  letterClassName = "",
  delay = 0,
}: {
  text: string;
  className?: string;
  letterClassName?: string;
  delay?: number;
}) {
  return (
    <motion.span
      className={`inline-flex ${className}`}
      initial="hidden"
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.055, delayChildren: delay } } }}
      aria-label={text}
    >
      {text.split("").map((ch, i) => (
        <motion.span
          key={`${ch}-${i}`}
          aria-hidden
          className={`inline-block will-change-transform ${letterClassName}`}
          variants={{
            hidden: { y: 44, opacity: 0, rotateX: 90, filter: "blur(10px)" },
            show: {
              y: 0,
              opacity: 1,
              rotateX: 0,
              filter: "blur(0px)",
              transition: { duration: 0.9, ease: [0.22, 1, 0.36, 1] },
            },
          }}
        >
          {ch === " " ? " " : ch}
        </motion.span>
      ))}
    </motion.span>
  );
}

// ── Infinite marquee (ticker tape) ─────────────────────────────────────────
export function Marquee({
  children,
  duration = 32,
  className = "",
}: {
  children: ReactNode;
  duration?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <div
      className={`overflow-hidden ${className}`}
      style={{
        maskImage: "linear-gradient(90deg, transparent, black 8%, black 92%, transparent)",
        WebkitMaskImage: "linear-gradient(90deg, transparent, black 8%, black 92%, transparent)",
      }}
    >
      <motion.div
        className="flex w-max items-center"
        animate={reduced ? undefined : { x: ["0%", "-50%"] }}
        transition={{ repeat: Infinity, ease: "linear", duration }}
      >
        <div className="flex items-center shrink-0">{children}</div>
        <div className="flex items-center shrink-0" aria-hidden>
          {children}
        </div>
      </motion.div>
    </div>
  );
}

// ── Aurora blob backdrop (section ambience) ────────────────────────────────
export function AuroraBlobs({ className = "" }: { className?: string }) {
  const reduced = useReducedMotion();
  const blobs = [
    { c: "rgba(34,211,238,0.10)", s: 480, x: "8%", y: "12%", d: 22 },
    { c: "rgba(168,85,247,0.09)", s: 560, x: "70%", y: "30%", d: 28 },
    { c: "rgba(16,185,129,0.07)", s: 500, x: "35%", y: "70%", d: 25 },
  ];
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden>
      {blobs.map((b, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full blur-3xl"
          style={{ width: b.s, height: b.s, left: b.x, top: b.y, background: `radial-gradient(circle, ${b.c}, transparent 70%)` }}
          animate={
            reduced
              ? undefined
              : { x: [0, 40, -30, 0], y: [0, -35, 25, 0], scale: [1, 1.15, 0.95, 1] }
          }
          transition={{ repeat: Infinity, duration: b.d, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
