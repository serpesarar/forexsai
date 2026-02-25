"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const SplineViewerClientNoSSR = dynamic(
  () => import("../../../components/welcome/SplineViewerClient"),
  { ssr: false }
);

// ── Scroll-down indicator ──────────────────────────────────────────────────
function ScrollIndicator() {
  return (
    <div className="flex flex-col items-center gap-2 opacity-30">
      <span className="text-[10px] uppercase tracking-[0.4em] text-gray-500">scroll</span>
      <motion.div
        animate={{ y: [0, 8, 0] }}
        transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
        className="w-px h-8 bg-gradient-to-b from-white/30 to-transparent"
      />
    </div>
  );
}

// ── About Section (embedded) ─────────────────────────────────────────────
function AboutSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-150px" });

  const stats = [
    { val: "49M+", label: "Data Points" },
    { val: "24+", label: "Years History" },
    { val: "78%", label: "Accuracy" },
    { val: "3", label: "AI Models" },
  ];

  return (
    <section ref={ref} className="min-h-screen flex items-center py-32 px-8">
      <div className="max-w-6xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-6">About ForexsAI</p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
            {/* Left */}
            <div>
              <h2 className="text-4xl md:text-6xl font-bold mb-8 leading-tight">
                <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent">
                  Built by traders,
                </span>
                <br />
                <span className="font-light text-gray-600">for traders.</span>
              </h2>
              <p className="text-gray-500 font-light leading-relaxed text-base border-l-2 border-cyan-500/30 pl-5 mb-6">
                Retail traders have always faced an unfair intelligence gap. We built ForexsAI to give independent traders the same analytical depth as institutional quant desks — transparent, fast, and continuously improving.
              </p>
              <p className="text-gray-600 font-light leading-relaxed text-sm pl-5">
                Our system runs three parallel model pipelines — EMEL (rule-based precision), PULSE (algorithmic scalp), and ML Hybrid (LightGBM neural) — plus Claude AI news sentiment, to deliver consistent, explainable signals.
              </p>
            </div>

            {/* Right — Stats */}
            <div>
              <div className="grid grid-cols-2 gap-4 mb-8">
                {stats.map((s, i) => (
                  <motion.div
                    key={s.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={inView ? { opacity: 1, y: 0 } : {}}
                    transition={{ delay: 0.3 + i * 0.1 }}
                    className="bg-white/[0.03] border border-white/6 rounded-xl p-6 text-center"
                  >
                    <div className="text-3xl font-bold bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent mb-1">
                      {s.val}
                    </div>
                    <div className="text-xs uppercase tracking-[0.25em] text-gray-600">{s.label}</div>
                  </motion.div>
                ))}
              </div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={inView ? { opacity: 1 } : {}}
                transition={{ delay: 0.6 }}
              >
                <Link
                  href="/about"
                  className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-colors border-b border-white/10 hover:border-white/30 pb-0.5"
                >
                  Full story →
                </Link>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ── Features Section (embedded) ──────────────────────────────────────────
function FeaturesSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  const items = [
    { id: "01", tag: "EMEL", title: "Strategic Analysis", desc: "9 validation checkpoints. Precision over frequency.", accent: "text-cyan-400", border: "border-cyan-500/15" },
    { id: "02", tag: "PULSE", title: "Algorithmic Scalp", desc: "M5 / M15 / M30 momentum confluence.", accent: "text-purple-400", border: "border-purple-500/15" },
    { id: "03", tag: "ML HYBRID", title: "Neural Engine", desc: "LightGBM on 49M+ data points. 78.4% accuracy.", accent: "text-gray-400", border: "border-white/8" },
    { id: "04", tag: "CLAUDE AI", title: "News Sentiment", desc: "Real-time macro bias from Anthropic AI.", accent: "text-amber-400", border: "border-amber-500/15" },
    { id: "05", tag: "ICT / SMC", title: "Smart Money", desc: "Order blocks, FVGs, BOS detection.", accent: "text-emerald-400", border: "border-emerald-500/15" },
    { id: "06", tag: "HARMONICS", title: "Pattern Visualizer", desc: "15+ harmonic patterns with TradingView charts.", accent: "text-pink-400", border: "border-pink-500/15" },
  ];

  return (
    <section ref={ref} className="min-h-screen flex items-center py-32 px-8">
      <div className="max-w-6xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-6">Core Technology</p>
          <h2 className="text-4xl md:text-6xl font-bold mb-16 leading-tight">
            <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent">
              Three models.
            </span>
            <br />
            <span className="font-light text-gray-600">One platform.</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((f, i) => (
              <motion.div
                key={f.id}
                initial={{ opacity: 0, y: 30 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.1 + i * 0.1 }}
                className={`bg-white/[0.03] border rounded-xl p-6 hover:bg-white/[0.05] transition-all ${f.border}`}
              >
                <div className="flex items-baseline gap-3 mb-3">
                  <span className="text-xs font-mono text-gray-700">{f.id}</span>
                  <span className={`text-xs uppercase tracking-[0.25em] ${f.accent}`}>{f.tag}</span>
                </div>
                <h3 className="text-sm font-light text-white mb-2">{f.title}</h3>
                <p className="text-xs text-gray-600 font-light leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={inView ? { opacity: 1 } : {}}
            transition={{ delay: 0.7 }}
            className="mt-10 flex items-center gap-6"
          >
            <Link
              href="/features"
              className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-colors border-b border-white/10 hover:border-white/30 pb-0.5"
            >
              All features →
            </Link>
            <Link href="/signup">
              <button className="bg-gradient-to-r from-gray-700 via-gray-500 to-gray-700 border border-gray-500/40 text-white uppercase tracking-widest text-xs px-8 py-3 rounded-sm hover:shadow-[0_0_20px_rgba(200,200,200,0.2)] transition-all">
                Start Free
              </button>
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

// ── Pricing Section (embedded) ───────────────────────────────────────────
function PricingSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section ref={ref} className="min-h-screen flex items-center py-32 px-8">
      <div className="max-w-5xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 1 }}
        >
          <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-6">Pricing</p>
          <h2 className="text-4xl md:text-6xl font-bold mb-16 leading-tight">
            <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent">
              Simple.
            </span>
            <br />
            <span className="font-light text-gray-600">Transparent.</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
            {/* Free */}
            <div className="bg-white/[0.03] border border-white/8 rounded-2xl p-8">
              <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-6">Free</p>
              <div className="text-5xl font-bold text-white mb-2">€0</div>
              <p className="text-gray-600 text-sm font-light mb-8">forever</p>
              <ul className="space-y-3 mb-8">
                {["NASDAQ + XAUUSD signals", "3 AI models", "Live price ticker", "Community access"].map((f) => (
                  <li key={f} className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="text-[8px] text-gray-600">◆</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/signup">
                <button className="w-full py-3 bg-white/[0.04] border border-white/8 text-gray-400 hover:text-white hover:bg-white/[0.08] rounded-sm text-xs uppercase tracking-widest transition-all">
                  Get Started
                </button>
              </Link>
            </div>

            {/* Pro */}
            <div className="bg-white/[0.05] border border-white/15 rounded-2xl p-8 shadow-[0_0_40px_rgba(6,182,212,0.05)]">
              <div className="flex items-center justify-between mb-6">
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Pro</p>
                <span className="text-xs uppercase tracking-widest text-white/40 border border-white/10 px-2 py-0.5 rounded-full">Popular</span>
              </div>
              <div className="text-5xl font-bold bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent mb-2">€29</div>
              <p className="text-gray-600 text-sm font-light mb-8">/month</p>
              <ul className="space-y-3 mb-8">
                {["Everything in Free", "DAX + US Oil signals", "Claude AI sentiment", "Multi-TF matrix", "Harmonic visualizer", "Priority support"].map((f) => (
                  <li key={f} className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="text-[8px] text-cyan-400/60">◆</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/signup">
                <button className="w-full py-3 bg-gradient-to-r from-gray-700 via-gray-500 to-gray-700 border border-gray-500/40 text-white hover:shadow-[0_0_20px_rgba(200,200,200,0.15)] rounded-sm text-xs uppercase tracking-widest transition-all">
                  Upgrade to Pro
                </button>
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Main Welcome Page (Single-Page Scroll)
// ─────────────────────────────────────────────────────────────────────────
export default function WelcomePage() {
  return (
    <div className="bg-black text-white font-sans">

      {/* ── HERO SCREEN (full viewport) ─────────────────────────────── */}
      <div className="relative w-full h-screen overflow-hidden">
        {/* 3D Spline Background */}
        <SplineViewerClientNoSSR />

        {/* Overlays */}
        <div className="pointer-events-none absolute inset-0 z-10 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay" />
        <div className="pointer-events-none absolute inset-0 z-10 bg-[radial-gradient(circle_at_center,_transparent_0%,_black_100%)] opacity-70" />

        {/* UI Content Layer */}
        <div className="relative z-20 flex flex-col h-full mx-auto max-w-[1400px]">

          {/* Glass Navbar */}
          <nav className="flex items-center justify-between px-8 py-5 backdrop-blur-md border-b border-white/10">
            <div className="flex items-center gap-1">
              <span className="text-xl font-bold tracking-[0.1em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">FOREXS</span>
              <span className="text-xl font-light tracking-[0.1em] text-white/90">AI</span>
            </div>
            <div className="hidden md:flex gap-10">
              <a href="#features" className="uppercase tracking-widest text-xs text-gray-400 hover:text-white transition-colors scroll-smooth">FEATURES</a>
              <a href="#about" className="uppercase tracking-widest text-xs text-gray-400 hover:text-white transition-colors">ABOUT</a>
              <a href="#pricing" className="uppercase tracking-widest text-xs text-gray-400 hover:text-white transition-colors">PRICING</a>
            </div>
            <Link href="/login" className="uppercase tracking-widest text-xs text-gray-300 hover:text-white transition-colors border border-white/20 px-5 py-2.5 rounded hover:bg-white/5">
              LOGIN
            </Link>
          </nav>

          {/* Hero Content */}
          <div className="flex-1 flex flex-col items-end justify-center px-12 pb-20">
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, delay: 0.3 }}
              className="max-w-xl text-right"
            >
              <h1 className="text-6xl md:text-8xl font-sans mb-4 flex flex-col items-end leading-tight">
                <span className="font-bold tracking-[0.2em] bg-gradient-to-r from-gray-100 via-gray-400 to-gray-100 bg-clip-text text-transparent drop-shadow-lg">
                  FOREXS
                </span>
                <span className="font-light tracking-[0.2em] text-white/90">AI</span>
              </h1>
              <p className="text-gray-400 font-light text-xl mb-10 max-w-lg mt-6 ml-auto leading-relaxed border-r-2 border-cyan-500/50 pr-4">
                Advanced algorithmic trading powered by neural networks
              </p>
              <Link href="/signup">
                <motion.button
                  whileHover={{ scale: 1.03, boxShadow: "0 0 30px rgba(200,200,200,0.4)" }}
                  whileTap={{ scale: 0.97 }}
                  className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.3)] transition-all duration-300 text-white uppercase tracking-widest text-sm px-10 py-4 rounded-sm font-medium"
                >
                  START TRADING
                </motion.button>
              </Link>
            </motion.div>
          </div>

          {/* Feature Cards */}
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-5xl px-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { icon: "📡", title: "Live Markets", desc: "Real-time AI analysis", href: "#features", accent: "group-hover:bg-cyan-500/40", defaultBg: "bg-cyan-500/20" },
                { icon: "🧠", title: "AI Analysis", desc: "Deep pattern recognition", href: "#about", accent: "group-hover:bg-purple-500/40", defaultBg: "bg-purple-500/20" },
                { icon: "📊", title: "Portfolio", desc: "Intelligent risk management", href: "#pricing", accent: "group-hover:bg-blue-500/40", defaultBg: "bg-blue-500/20" },
              ].map((card) => (
                <a key={card.title} href={card.href}>
                  <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-5 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-300 cursor-pointer group">
                    <div className={`w-9 h-9 rounded-full ${card.defaultBg} flex items-center justify-center mb-3 ${card.accent} transition-colors`}>
                      <span className="text-base">{card.icon}</span>
                    </div>
                    <h3 className="uppercase tracking-widest text-xs mb-1 text-gray-200">{card.title}</h3>
                    <p className="font-light text-gray-500 text-xs">{card.desc}</p>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── SCROLL SECTIONS ──────────────────────────────────────────── */}

      {/* Divider + scroll hint */}
      <div className="flex flex-col items-center py-16 gap-6">
        <ScrollIndicator />
      </div>

      {/* About */}
      <div id="about" className="bg-black border-t border-white/[0.04]">
        <AboutSection />
      </div>

      {/* Features */}
      <div id="features" className="bg-black border-t border-white/[0.04]">
        <FeaturesSection />
      </div>

      {/* Pricing */}
      <div id="pricing" className="bg-black border-t border-white/[0.04]">
        <PricingSection />
      </div>

      {/* Footer CTA */}
      <div className="border-t border-white/[0.04] py-20 text-center px-8 bg-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Ready to start?</p>
          <h2 className="text-4xl font-light text-white mb-8 tracking-wide">
            <span className="bg-gradient-to-br from-gray-100 to-gray-500 bg-clip-text text-transparent">Join ForexsAI</span>
          </h2>
          <Link href="/signup">
            <button className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.2)] hover:shadow-[0_0_30px_rgba(192,192,192,0.5)] transition-all duration-300 text-white uppercase tracking-widest text-sm px-14 py-4 rounded-sm font-medium">
              Create Free Account
            </button>
          </Link>
          <p className="text-gray-700 text-xs mt-6 font-light">No credit card required</p>
        </motion.div>
      </div>
    </div>
  );
}
