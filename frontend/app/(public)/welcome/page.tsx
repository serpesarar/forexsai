"use client";

/**
 * ForexSAI Welcome / Landing — "The Machine That Watches Markets".
 * Max-animation single-page scroll: self-drawing market canvas hero,
 * neural ensemble pipeline, live signal simulator, tilt feature cards,
 * count-up stats, conic-border pricing and magnetic CTAs.
 */

import Link from "next/link";
import { ReactNode, useRef, useState } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useMotionValueEvent,
  useReducedMotion,
} from "framer-motion";
import { TypeAnimation } from "react-type-animation";
import {
  ArrowRight,
  Brain,
  Eye,
  Layers,
  MessagesSquare,
  Radar,
  Zap,
} from "lucide-react";

import LiveMarketCanvas from "@/components/welcome/LiveMarketCanvas";
import NeuralPipeline from "@/components/welcome/NeuralPipeline";
import SignalSimulator from "@/components/welcome/SignalSimulator";
import {
  AuroraBlobs,
  CountUp,
  LetterCascade,
  Magnetic,
  Marquee,
  ScrollProgressBar,
  TiltCard,
  WordReveal,
} from "@/components/welcome/fx";

// ─────────────────────────────────────────────────────────────────────────
// Small shared pieces
// ─────────────────────────────────────────────────────────────────────────

function SectionTag({ children }: { children: ReactNode }) {
  return (
    <motion.p
      initial={{ opacity: 0, letterSpacing: "0.9em" }}
      whileInView={{ opacity: 1, letterSpacing: "0.45em" }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
      className="text-[10px] md:text-xs uppercase text-cyan-500/70 mb-6 font-mono"
    >
      {children}
    </motion.p>
  );
}

function ConicBorder({ children, className = "", radius = "rounded-2xl", innerRadius = "rounded-[15px]" }: {
  children: ReactNode;
  className?: string;
  radius?: string;
  innerRadius?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <div className={`relative ${radius} p-px overflow-hidden ${className}`}>
      <motion.div
        aria-hidden
        className="absolute inset-[-100%]"
        style={{
          background:
            "conic-gradient(from 0deg, transparent 0deg, rgba(34,211,238,0.9) 55deg, transparent 115deg, transparent 180deg, rgba(168,85,247,0.9) 235deg, transparent 300deg)",
        }}
        animate={reduced ? undefined : { rotate: 360 }}
        transition={{ repeat: Infinity, duration: 5.5, ease: "linear" }}
      />
      <div className={`relative ${innerRadius} bg-[#070b14]`}>{children}</div>
    </div>
  );
}

function ScrollIndicator() {
  return (
    <div className="flex flex-col items-center gap-2 opacity-40">
      <span className="text-[9px] uppercase tracking-[0.5em] text-gray-500 font-mono">scroll</span>
      <motion.div
        animate={{ y: [0, 9, 0], opacity: [0.9, 0.2, 0.9] }}
        transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
        className="w-px h-9 bg-gradient-to-b from-cyan-400/70 to-transparent"
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Navbar — glass, condenses on scroll
// ─────────────────────────────────────────────────────────────────────────

function Navbar() {
  const { scrollY } = useScroll();
  const [scrolled, setScrolled] = useState(false);
  useMotionValueEvent(scrollY, "change", (v) => setScrolled(v > 40));

  const links = [
    { href: "#engine", label: "ENGINE" },
    { href: "#features", label: "FEATURES" },
    { href: "#signals", label: "SIGNALS" },
    { href: "#pricing", label: "PRICING" },
  ];

  return (
    <motion.nav
      initial={{ y: -70, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? "backdrop-blur-xl bg-black/60 border-b border-white/10 py-3" : "bg-transparent border-b border-transparent py-5"
      }`}
    >
      <div className="mx-auto max-w-[1400px] flex items-center justify-between px-4 sm:px-6 md:px-8">
        <Link href="/welcome" className="flex items-center gap-1 group">
          <motion.span
            className="text-lg md:text-xl font-bold tracking-[0.12em] bg-gradient-to-r from-cyan-300 via-white to-purple-300 bg-clip-text text-transparent bg-[length:200%_auto]"
            animate={{ backgroundPosition: ["0% center", "200% center"] }}
            transition={{ repeat: Infinity, duration: 5, ease: "linear" }}
          >
            FOREXS
          </motion.span>
          <span className="text-lg md:text-xl font-light tracking-[0.12em] text-white/90">AI</span>
        </Link>

        <div className="hidden md:flex gap-9">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="relative uppercase tracking-[0.25em] text-[11px] text-gray-400 hover:text-white transition-colors group"
            >
              {l.label}
              <span className="absolute -bottom-1.5 left-0 h-px w-0 bg-gradient-to-r from-cyan-400 to-purple-400 transition-all duration-300 group-hover:w-full" />
            </a>
          ))}
        </div>

        <Link
          href="/login"
          className="uppercase tracking-[0.25em] text-[10px] md:text-[11px] text-gray-300 hover:text-white transition-all border border-white/20 hover:border-cyan-400/50 hover:shadow-[0_0_18px_rgba(34,211,238,0.25)] px-4 py-2 md:px-5 md:py-2.5 rounded"
        >
          LOGIN
        </Link>
      </div>
    </motion.nav>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Hero
// ─────────────────────────────────────────────────────────────────────────

const HUD_CHIPS = [
  { text: "NDX ▲ +0.84%", cls: "text-emerald-400", top: "24%", left: "7%", delay: 1.4, dur: 5.5 },
  { text: "REGIME · TREND ↑", cls: "text-cyan-400", top: "62%", left: "10%", delay: 1.8, dur: 6.4 },
  { text: "SIGNAL · BUY 84%", cls: "text-purple-300", top: "30%", left: "84%", delay: 2.2, dur: 5.8 },
  { text: "6 MODELS ONLINE", cls: "text-amber-300", top: "68%", left: "82%", delay: 2.6, dur: 6.1 },
];

function HeroSection() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const contentY = useTransform(scrollYProgress, [0, 1], [0, 140]);
  const contentOpacity = useTransform(scrollYProgress, [0, 0.65], [1, 0]);
  const canvasScale = useTransform(scrollYProgress, [0, 1], [1, 1.12]);

  return (
    <div ref={ref} className="relative w-full h-[100svh] overflow-hidden">
      <motion.div style={{ scale: canvasScale }} className="absolute inset-0">
        <LiveMarketCanvas />
      </motion.div>

      {/* vignette + bottom fade into page */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,rgba(0,0,0,0.75)_100%)]" />
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-black" />

      {/* floating HUD chips */}
      {HUD_CHIPS.map((c) => (
        <motion.div
          key={c.text}
          initial={{ opacity: 0, scale: 0.6, filter: "blur(8px)" }}
          animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
          transition={{ delay: c.delay, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          style={{ top: c.top, left: c.left }}
          className="absolute z-20 hidden lg:block -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, -12, 0] }}
            transition={{ repeat: Infinity, duration: c.dur, ease: "easeInOut" }}
            className={`rounded-full border border-white/10 bg-black/50 backdrop-blur-md px-4 py-2 font-mono text-[10px] tracking-[0.25em] ${c.cls} shadow-[0_0_25px_rgba(0,0,0,0.6)]`}
          >
            {c.text}
          </motion.div>
        </motion.div>
      ))}

      {/* content */}
      <motion.div
        style={{ y: contentY, opacity: contentOpacity }}
        className="relative z-20 flex h-full flex-col items-center justify-center px-5 text-center"
      >
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="mb-7 flex items-center gap-2.5 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 backdrop-blur-md"
        >
          <motion.span
            className="h-1.5 w-1.5 rounded-full bg-emerald-400"
            animate={{ opacity: [1, 0.25, 1], scale: [1, 1.5, 1] }}
            transition={{ repeat: Infinity, duration: 1.8 }}
          />
          <span className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.35em] text-gray-400">
            live · 6 models · 4 markets
          </span>
        </motion.div>

        <h1 className="mb-2 leading-none" style={{ perspective: 700 }}>
          <LetterCascade
            text="FOREXS"
            delay={0.35}
            className="text-[17vw] sm:text-7xl md:text-8xl lg:text-9xl font-bold tracking-[0.14em]"
            letterClassName="bg-gradient-to-b from-white via-gray-200 to-gray-500 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(34,211,238,0.25)]"
          />
          <LetterCascade
            text="AI"
            delay={0.85}
            className="ml-3 md:ml-4 text-[17vw] sm:text-7xl md:text-8xl lg:text-9xl font-light tracking-[0.14em]"
            letterClassName="bg-gradient-to-b from-cyan-200 to-cyan-500 bg-clip-text text-transparent"
          />
        </h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5, duration: 1 }}
          className="mb-10 h-8 font-mono text-sm sm:text-base md:text-lg text-gray-400"
        >
          <TypeAnimation
            sequence={[
              "Neural networks watching NASDAQ.", 2400,
              "Six models. One signal.", 2400,
              "Smart-money concepts, decoded live.", 2400,
              "Regime-aware. Risk-first. Explainable.", 2400,
            ]}
            speed={55}
            deletionSpeed={80}
            repeat={Infinity}
            cursor
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.8, duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6"
        >
          <Magnetic>
            <Link href="/signup">
              <ConicBorder radius="rounded-lg" innerRadius="rounded-[7px]">
                <span className="block px-9 sm:px-11 py-4 font-medium uppercase tracking-[0.3em] text-xs sm:text-sm text-white bg-white/[0.03] hover:bg-cyan-500/10 transition-colors rounded-[7px]">
                  Start Trading
                </span>
              </ConicBorder>
            </Link>
          </Magnetic>
          <Magnetic strength={0.25}>
            <a
              href="#engine"
              className="group inline-flex items-center gap-2 px-6 py-4 text-[11px] sm:text-xs uppercase tracking-[0.3em] text-gray-400 hover:text-white transition-colors"
            >
              Watch the engine
              <ArrowRight size={14} className="transition-transform duration-300 group-hover:translate-x-1.5" />
            </a>
          </Magnetic>
        </motion.div>
      </motion.div>

      <div className="absolute bottom-6 left-1/2 z-20 -translate-x-1/2">
        <ScrollIndicator />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Ticker tape
// ─────────────────────────────────────────────────────────────────────────

const TICKS = [
  { s: "NASDAQ 100", p: "21,847.2", c: "+0.84%", up: true },
  { s: "XAU / USD", p: "3,412.80", c: "+0.42%", up: true },
  { s: "DAX 40", p: "24,186.5", c: "−0.31%", up: false },
  { s: "WTI OIL", p: "68.42", c: "+1.12%", up: true },
  { s: "VIX", p: "16.4", c: "−2.10%", up: false },
  { s: "DXY", p: "104.21", c: "+0.08%", up: true },
  { s: "US10Y", p: "4.21%", c: "+0.02", up: true },
];

function TickerTape() {
  return (
    <div className="relative border-y border-white/[0.06] bg-black/60 py-3.5 backdrop-blur">
      <Marquee duration={36}>
        {TICKS.map((t) => (
          <span key={t.s} className="mx-7 inline-flex items-center gap-3 font-mono text-[11px] tracking-[0.15em]">
            <span className="text-gray-500 uppercase">{t.s}</span>
            <span className="text-gray-200">{t.p}</span>
            <span className={t.up ? "text-emerald-400" : "text-red-400"}>
              {t.up ? "▲" : "▼"} {t.c}
            </span>
            <span className="ml-7 text-[7px] text-gray-700">◆</span>
          </span>
        ))}
      </Marquee>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Engine (neural pipeline) section
// ─────────────────────────────────────────────────────────────────────────

function EngineSection() {
  return (
    <section id="engine" className="relative py-24 md:py-36 px-5 sm:px-6 md:px-8 overflow-hidden">
      <AuroraBlobs />
      <div className="relative mx-auto max-w-6xl">
        <SectionTag>The Engine</SectionTag>
        <h2 className="mb-6 text-4xl sm:text-5xl md:text-6xl font-bold leading-[1.05]">
          <WordReveal
            text="Six minds."
            wordClassName="bg-gradient-to-br from-white via-gray-200 to-gray-500 bg-clip-text text-transparent"
          />
          <br />
          <WordReveal text="One decision." delay={0.25} wordClassName="font-light text-gray-600" />
        </h2>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="mb-14 max-w-2xl border-l-2 border-cyan-500/30 pl-5 text-sm md:text-base font-light leading-relaxed text-gray-500"
        >
          Every tick flows through six independent model pipelines — machine learning, momentum
          algorithms, strategic checklists and smart-money structure. A regime-aware ensemble
          weighs them in real time and fires a single, explainable signal.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.97 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: "-120px" }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
          className="rounded-3xl border border-white/[0.07] bg-black/40 p-4 md:p-8 backdrop-blur-sm shadow-[0_40px_80px_-30px_rgba(0,0,0,0.9)]"
        >
          <NeuralPipeline />
        </motion.div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Stats band
// ─────────────────────────────────────────────────────────────────────────

const STATS = [
  { to: 49, suffix: "M+", label: "Data points analyzed" },
  { to: 24, suffix: "+", label: "Years of market history" },
  { to: 150, suffix: "+", label: "ML features per tick" },
  { to: 6, suffix: "", label: "AI models in ensemble" },
];

function StatsBand() {
  return (
    <section className="relative border-y border-white/[0.05] py-16 md:py-20 px-5">
      <div className="mx-auto grid max-w-5xl grid-cols-2 gap-10 md:grid-cols-4">
        {STATS.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ delay: i * 0.12, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="text-center"
          >
            <div className="mb-2 font-mono text-4xl md:text-5xl font-bold">
              <CountUp
                to={s.to}
                suffix={s.suffix}
                className="bg-gradient-to-b from-white to-gray-500 bg-clip-text text-transparent"
              />
            </div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-gray-600">{s.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Features grid
// ─────────────────────────────────────────────────────────────────────────

const FEATURES = [
  { id: "01", tag: "ML HYBRID", title: "Neural Engine", desc: "LightGBM trained on 49M+ data points, 150+ engineered features per tick.", Icon: Brain, color: "text-blue-400", ring: "group-hover:border-blue-500/40", glow: "rgba(96,165,250,0.14)" },
  { id: "02", tag: "PULSE", title: "Algorithmic Scalp", desc: "Three momentum engines across M5 / M15 / M30 with confluence scoring.", Icon: Zap, color: "text-orange-400", ring: "group-hover:border-orange-500/40", glow: "rgba(251,146,60,0.14)" },
  { id: "03", tag: "EMEL", title: "Strategic Analysis", desc: "Ten validation checkpoints per signal. Precision over frequency.", Icon: Layers, color: "text-purple-400", ring: "group-hover:border-purple-500/40", glow: "rgba(192,132,252,0.14)" },
  { id: "04", tag: "SMC / ICT", title: "Smart Money", desc: "Order blocks, fair-value gaps, BOS & CHoCH structure detection.", Icon: Eye, color: "text-teal-400", ring: "group-hover:border-teal-500/40", glow: "rgba(45,212,191,0.14)" },
  { id: "05", tag: "AI DEBATE", title: "Adversarial Bias", desc: "Eight AI agents argue bull vs bear every morning — a CIO model rules.", Icon: MessagesSquare, color: "text-amber-400", ring: "group-hover:border-amber-500/40", glow: "rgba(251,191,36,0.14)" },
  { id: "06", tag: "REGIME", title: "Market Radar", desc: "Trend / ranging / transition detection re-weights every model live.", Icon: Radar, color: "text-cyan-400", ring: "group-hover:border-cyan-500/40", glow: "rgba(34,211,238,0.14)" },
];

function FeaturesSection() {
  return (
    <section id="features" className="relative py-24 md:py-36 px-5 sm:px-6 md:px-8 overflow-hidden">
      <div className="mx-auto max-w-6xl">
        <SectionTag>Core Technology</SectionTag>
        <h2 className="mb-14 md:mb-20 text-4xl sm:text-5xl md:text-6xl font-bold leading-[1.05]">
          <WordReveal
            text="Built like a"
            wordClassName="bg-gradient-to-br from-white via-gray-200 to-gray-500 bg-clip-text text-transparent"
          />
          <br />
          <WordReveal text="quant desk." delay={0.25} wordClassName="font-light text-gray-600" />
        </h2>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3" style={{ perspective: 1200 }}>
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.id}
              initial={{ opacity: 0, y: 60, rotateX: -8 }}
              whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ delay: (i % 3) * 0.14 + Math.floor(i / 3) * 0.1, duration: 0.85, ease: [0.22, 1, 0.36, 1] }}
            >
              <TiltCard className="group h-full">
                <div
                  className={`relative h-full overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] p-7 transition-colors duration-500 ${f.ring}`}
                >
                  <div
                    className="pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full opacity-0 blur-3xl transition-opacity duration-700 group-hover:opacity-100"
                    style={{ background: f.glow }}
                    aria-hidden
                  />
                  <div className="mb-6 flex items-center justify-between">
                    <motion.div
                      whileHover={{ rotate: 8, scale: 1.1 }}
                      className={`flex h-11 w-11 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] ${f.color}`}
                    >
                      <f.Icon size={20} strokeWidth={1.6} />
                    </motion.div>
                    <span className="font-mono text-xs text-gray-700">{f.id}</span>
                  </div>
                  <p className={`mb-2 font-mono text-[10px] uppercase tracking-[0.3em] ${f.color}`}>{f.tag}</p>
                  <h3 className="mb-2.5 text-base font-medium text-white">{f.title}</h3>
                  <p className="text-xs font-light leading-relaxed text-gray-500">{f.desc}</p>
                </div>
              </TiltCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Signals demo section
// ─────────────────────────────────────────────────────────────────────────

function SignalsSection() {
  return (
    <section id="signals" className="relative py-24 md:py-36 px-5 sm:px-6 md:px-8 overflow-hidden">
      <AuroraBlobs />
      <div className="relative mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-2 lg:gap-20">
        <div>
          <SectionTag>Live Output</SectionTag>
          <h2 className="mb-6 text-4xl sm:text-5xl md:text-6xl font-bold leading-[1.05]">
            <WordReveal
              text="Signals that"
              wordClassName="bg-gradient-to-br from-white via-gray-200 to-gray-500 bg-clip-text text-transparent"
            />
            <br />
            <WordReveal text="explain themselves." delay={0.25} wordClassName="font-light text-gray-600" />
          </h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ delay: 0.45, duration: 0.8 }}
            className="mb-8 max-w-lg border-l-2 border-purple-500/30 pl-5 text-sm md:text-base font-light leading-relaxed text-gray-500"
          >
            No black boxes. Every signal ships with its entry, staged take-profits, a hard stop and
            the confidence the ensemble actually voted — so you always know <em>why</em>, not just
            <em> what</em>.
          </motion.p>
          <motion.ul
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-60px" }}
            variants={{ show: { transition: { staggerChildren: 0.14, delayChildren: 0.5 } } }}
            className="space-y-3.5"
          >
            {["Multi-target TP ladder with hard stop-loss", "Regime & session gates filter low-quality hours", "Full lifecycle tracking — every outcome graded"].map((t) => (
              <motion.li
                key={t}
                variants={{
                  hidden: { opacity: 0, x: -22 },
                  show: { opacity: 1, x: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
                }}
                className="flex items-center gap-3 text-xs text-gray-400"
              >
                <span className="text-[8px] text-cyan-400">◆</span> {t}
              </motion.li>
            ))}
          </motion.ul>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 60, scale: 0.95 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        >
          <SignalSimulator />
        </motion.div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Pricing
// ─────────────────────────────────────────────────────────────────────────

function PricingSection() {
  return (
    <section id="pricing" className="relative py-24 md:py-36 px-5 sm:px-6 md:px-8">
      <div className="mx-auto max-w-5xl">
        <SectionTag>Pricing</SectionTag>
        <h2 className="mb-14 md:mb-20 text-4xl sm:text-5xl md:text-6xl font-bold leading-[1.05]">
          <WordReveal
            text="Simple."
            wordClassName="bg-gradient-to-br from-white via-gray-200 to-gray-500 bg-clip-text text-transparent"
          />
          <br />
          <WordReveal text="Transparent." delay={0.2} wordClassName="font-light text-gray-600" />
        </h2>

        <div className="mx-auto grid max-w-3xl grid-cols-1 gap-6 md:grid-cols-2 md:mx-0">
          {/* Free */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            whileHover={{ y: -6 }}
            className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-8 transition-shadow hover:shadow-[0_30px_60px_-25px_rgba(0,0,0,0.9)]"
          >
            <p className="mb-6 text-[10px] uppercase tracking-[0.35em] text-gray-600 font-mono">Free</p>
            <div className="mb-1 text-5xl font-bold text-white">€0</div>
            <p className="mb-8 text-sm font-light text-gray-600">forever</p>
            <ul className="mb-8 space-y-3">
              {["NASDAQ + XAUUSD signals", "3 AI models", "Live price ticker", "Community access"].map((f) => (
                <li key={f} className="flex items-center gap-3 text-xs text-gray-500">
                  <span className="text-[8px] text-gray-600">◆</span> {f}
                </li>
              ))}
            </ul>
            <Link href="/signup">
              <button className="w-full rounded-lg border border-white/[0.09] bg-white/[0.03] py-3 text-[11px] uppercase tracking-[0.3em] text-gray-400 transition-all hover:bg-white/[0.08] hover:text-white">
                Get Started
              </button>
            </Link>
          </motion.div>

          {/* Pro */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.8, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
            whileHover={{ y: -6 }}
          >
            <ConicBorder>
              <div className="relative p-8">
                <div className="mb-6 flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-[0.35em] text-gray-400 font-mono">Pro</p>
                  <motion.span
                    animate={{ boxShadow: ["0 0 0px rgba(34,211,238,0)", "0 0 18px rgba(34,211,238,0.35)", "0 0 0px rgba(34,211,238,0)"] }}
                    transition={{ repeat: Infinity, duration: 2.6 }}
                    className="rounded-full border border-cyan-400/30 px-2.5 py-0.5 text-[9px] uppercase tracking-[0.25em] text-cyan-300"
                  >
                    Popular
                  </motion.span>
                </div>
                <div className="mb-1 text-5xl font-bold bg-gradient-to-br from-white to-gray-400 bg-clip-text text-transparent">€29</div>
                <p className="mb-8 text-sm font-light text-gray-600">/month</p>
                <ul className="mb-8 space-y-3">
                  {["Everything in Free", "DAX + US Oil signals", "Claude AI sentiment", "Multi-TF matrix", "Harmonic visualizer", "Priority support"].map((f) => (
                    <li key={f} className="flex items-center gap-3 text-xs text-gray-500">
                      <span className="text-[8px] text-cyan-400/70">◆</span> {f}
                    </li>
                  ))}
                </ul>
                <Link href="/signup">
                  <button className="w-full rounded-lg bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-cyan-500/20 border border-cyan-400/30 py-3 text-[11px] uppercase tracking-[0.3em] text-white transition-all hover:shadow-[0_0_30px_rgba(34,211,238,0.25)]">
                    Upgrade to Pro
                  </button>
                </Link>
              </div>
            </ConicBorder>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Footer CTA + mini footer
// ─────────────────────────────────────────────────────────────────────────

function FooterCTA() {
  return (
    <section className="relative overflow-hidden border-t border-white/[0.05] py-28 md:py-36 px-6 text-center">
      <AuroraBlobs />
      <div className="relative">
        <SectionTag>Ready when you are</SectionTag>
        <h2 className="mx-auto mb-10 max-w-3xl text-5xl md:text-7xl font-bold leading-[1.02]">
          <WordReveal
            text="Stop guessing."
            wordClassName="bg-gradient-to-br from-white via-gray-200 to-gray-500 bg-clip-text text-transparent"
          />
          <br />
          <WordReveal text="Start reading the market." delay={0.3} wordClassName="font-light text-gray-600" />
        </h2>
        <Magnetic>
          <Link href="/signup">
            <ConicBorder radius="rounded-lg" innerRadius="rounded-[7px]" className="inline-block">
              <span className="block px-12 py-4 md:px-14 md:py-5 font-medium uppercase tracking-[0.3em] text-xs md:text-sm text-white bg-white/[0.03] hover:bg-cyan-500/10 transition-colors rounded-[7px]">
                Create Free Account
              </span>
            </ConicBorder>
          </Link>
        </Magnetic>
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="mt-6 text-xs font-light text-gray-700"
        >
          No credit card required
        </motion.p>
      </div>
    </section>
  );
}

function MiniFooter() {
  return (
    <footer className="border-t border-white/[0.05] px-6 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 md:flex-row">
        <p className="font-mono text-[10px] tracking-[0.2em] text-gray-700">© 2026 FOREXSAI — ALL RIGHTS RESERVED</p>
        <div className="flex gap-6">
          {[
            { href: "/privacy", label: "Privacy" },
            { href: "/terms", label: "Terms" },
            { href: "/risk", label: "Risk Disclosure" },
          ].map((l) => (
            <Link key={l.href} href={l.href} className="text-[10px] uppercase tracking-[0.25em] text-gray-600 transition-colors hover:text-gray-300">
              {l.label}
            </Link>
          ))}
        </div>
      </div>
      <p className="mx-auto mt-6 max-w-3xl text-center text-[9px] leading-relaxed text-gray-800">
        Trading foreign exchange, indices and commodities carries a high level of risk and may not be suitable
        for all investors. Signals are informational only and do not constitute financial advice.
      </p>
    </footer>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────

export default function WelcomePage() {
  return (
    <div className="bg-transparent font-sans text-white">
      <ScrollProgressBar />
      <Navbar />
      <HeroSection />
      <TickerTape />
      <EngineSection />
      <StatsBand />
      <FeaturesSection />
      <SignalsSection />
      <PricingSection />
      <FooterCTA />
      <MiniFooter />
    </div>
  );
}
