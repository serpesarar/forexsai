"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import Link from "next/link";

const features = [
    {
        id: "01",
        tag: "EMEL Model",
        title: "9-Checkpoint Strategic Analysis",
        desc: "Our rule-based model runs every signal through 9 consecutive validation checkpoints: structure, trend, momentum, volume, HTF, pattern, S/R, macro, and entry timing. All 9 must pass for a signal to generate.",
        detail: "Precision over frequency. Fewer signals, higher conviction.",
        accent: "border-cyan-500/20",
        accentText: "text-cyan-400",
    },
    {
        id: "02",
        tag: "PULSE Model",
        title: "Algorithmic Scalp Detection",
        desc: "Multi-timeframe momentum confluence across M5, M15, and M30. PULSE detects high-probability scalp opportunities using volume profile, EMA alignment, and breakout confirmation.",
        detail: "Designed for speed. Signals in under 200ms from data ingestion.",
        accent: "border-purple-500/20",
        accentText: "text-purple-400",
    },
    {
        id: "03",
        tag: "ML Hybrid",
        title: "LightGBM Neural Engine",
        desc: "Trained on 49M+ data points spanning 24+ years of market history. 150+ technical features including RSI variants, MACD, Bollinger, ATR, Fibonacci levels, and candlestick patterns.",
        detail: "78.4% directional accuracy across XAUUSD, NASDAQ, DAX, and US OIL.",
        accent: "border-white/10",
        accentText: "text-gray-400",
    },
    {
        id: "04",
        tag: "Claude AI",
        title: "Real-Time News Sentiment",
        desc: "Anthropic Claude API analyzes live financial headlines and assigns Bullish / Bearish / Neutral scoring with confidence percentages. Macro bias fed directly into signal generation.",
        detail: "Economic calendar integration. Fed speak, CPI, NFP detection.",
        accent: "border-amber-500/20",
        accentText: "text-amber-400",
    },
    {
        id: "05",
        tag: "MTF Matrix",
        title: "Multi-Timeframe Confluence",
        desc: "Simultaneous analysis across M1, M5, M15, M30, H1, H4, and D1. Our confluence matrix shows where multiple timeframes agree, flagging the strongest trading opportunities.",
        detail: "Color-coded alignment grid. Instant visual confluence insight.",
        accent: "border-blue-500/20",
        accentText: "text-blue-400",
    },
    {
        id: "06",
        tag: "ICT / SMC",
        title: "Smart Money Concepts",
        desc: "Automated detection of Order Blocks, Fair Value Gaps, Break of Structure, Change of Character, and institutional liquidity sweeps across all timeframes.",
        detail: "Tracks where institutions accumulate — before retail catches up.",
        accent: "border-emerald-500/20",
        accentText: "text-emerald-400",
    },
    {
        id: "07",
        tag: "Harmonic Patterns",
        title: "Pattern Visualizer",
        desc: "Detects and visualizes 15+ harmonic patterns (Gartley, Bat, Butterfly, Crab, Cypher) plus classic chart patterns using TradingView Lightweight Charts with SVG overlays.",
        detail: "Galaxy-orange neon glow for major formations, blue for classic patterns.",
        accent: "border-pink-500/20",
        accentText: "text-pink-400",
    },
    {
        id: "08",
        tag: "COT & Whale Tracker",
        title: "Institutional Position Monitor",
        desc: "Commitment of Traders (COT) data visualization showing net positioning of commercials, non-commercials, and small speculators. Whale order flow detection via volume anomaly analysis.",
        detail: "Weekly COT updates with trend divergence alerts.",
        accent: "border-indigo-500/20",
        accentText: "text-indigo-400",
    },
];

const markets = [
    { symbol: "NASDAQ", full: "US Tech 100", desc: "Full ML + EMEL + PULSE coverage" },
    { symbol: "XAUUSD", full: "Gold / US Dollar", desc: "All 3 models + COT tracking" },
    { symbol: "DAX", full: "German Stock Index", desc: "ML Hybrid + Pulse coverage" },
    { symbol: "US OIL", full: "WTI Crude Oil", desc: "ML Hybrid + macro sentiment" },
];

export default function FeaturesPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-transparent text-white font-sans">
            <TopNav />

            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/3 blur-3xl rounded-full" />
                <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-purple-500/3 blur-3xl rounded-full" />
            </div>

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">

                {/* Hero */}
                <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="text-center mb-20">
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Platform Features</p>
                    <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-none">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent tracking-[0.1em]">
                            {t("featuresPage.title") || "INTELLIGENCE"}
                        </span>
                    </h1>
                    <p className="text-gray-500 font-light text-lg max-w-2xl mx-auto">
                        {t("featuresPage.subtitle") || "Three parallel AI models, real-time sentiment analysis, and institutional-grade pattern detection — all in one platform."}
                    </p>
                </motion.div>

                {/* Markets covered */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-20">
                    {markets.map((m, i) => (
                        <motion.div
                            key={m.symbol} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-white/[0.03] border border-white/6 rounded-xl p-5 text-center"
                        >
                            <p className="text-xs font-mono text-cyan-400/60 mb-1 uppercase tracking-widest">{m.symbol}</p>
                            <p className="text-sm font-light text-white mb-2">{m.full}</p>
                            <p className="text-xs text-gray-700 font-light">{m.desc}</p>
                        </motion.div>
                    ))}
                </div>

                {/* Feature cards */}
                <div className="space-y-4">
                    {features.map((f, i) => (
                        <motion.div
                            key={f.id}
                            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.05 }}
                            className={`bg-white/[0.02] border rounded-xl p-8 hover:bg-white/[0.04] transition-all ${f.accent}`}
                        >
                            <div className="flex flex-col md:flex-row gap-6">
                                <div className="shrink-0">
                                    <span className="text-xs font-mono text-gray-700">{f.id}</span>
                                    <p className={`text-xs uppercase tracking-[0.3em] mt-1 ${f.accentText}`}>{f.tag}</p>
                                </div>
                                <div className="flex-1">
                                    <h3 className="text-lg font-light text-white mb-3 tracking-wide">{f.title}</h3>
                                    <p className="text-sm text-gray-500 font-light leading-relaxed mb-4 border-l border-white/8 pl-4">{f.desc}</p>
                                    <p className={`text-xs uppercase tracking-[0.2em] ${f.accentText} opacity-70`}>→ {f.detail}</p>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* CTA */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    className="mt-20 text-center border border-white/6 rounded-2xl p-16 bg-white/[0.02]"
                >
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Ready to trade smarter?</p>
                    <h2 className="text-4xl font-light text-white mb-4 tracking-wide">Access All Features</h2>
                    <p className="text-gray-600 font-light mb-10 max-w-md mx-auto text-sm">Start with the free plan. No credit card required.</p>
                    <Link href="/signup">
                        <button className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.2)] hover:shadow-[0_0_30px_rgba(192,192,192,0.4)] transition-all duration-300 text-white uppercase tracking-widest text-xs px-12 py-4 rounded-sm font-medium">
                            Start Free
                        </button>
                    </Link>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
