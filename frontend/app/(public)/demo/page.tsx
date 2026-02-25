"use client";

export const dynamic = 'force-dynamic';

import Link from "next/link";
import { motion } from "framer-motion";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

const features = [
    {
        label: "EMEL Model",
        tag: "Rule-Based",
        desc: "9-checkpoint strategic analysis with strict institutional logic. Precision over frequency.",
        accent: "text-cyan-400",
        border: "border-cyan-500/15",
    },
    {
        label: "PULSE Model",
        tag: "Algorithmic",
        desc: "Ultra-fast scalp detection across M5, M15, M30. Momentum + volume confluence.",
        accent: "text-purple-400",
        border: "border-purple-500/15",
    },
    {
        label: "ML Hybrid",
        tag: "Neural",
        desc: "LightGBM trained on 30M+ candles. 150+ technical features, layered confidence scoring.",
        accent: "text-gray-400",
        border: "border-white/8",
    },
    {
        label: "Claude AI",
        tag: "Sentiment",
        desc: "Real-time news analysis via Anthropic Claude. Bullish / Bearish / Neutral with probability scores.",
        accent: "text-amber-400",
        border: "border-amber-500/15",
    },
];

const markets = [
    { symbol: "NASDAQ", price: "18,450.25", change: "+1.2%", trend: "up" },
    { symbol: "XAU/USD", price: "2,340.10", change: "-0.4%", trend: "down" },
    { symbol: "DAX", price: "18,204.80", change: "+0.8%", trend: "up" },
    { symbol: "US OIL", price: "82.45", change: "+0.6%", trend: "up" },
];

export default function DemoPage() {
    return (
        <main className="min-h-screen bg-black text-white font-sans">
            <TopNav />

            {/* Fixed bg */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-cyan-500/3 blur-3xl rounded-full" />
            </div>

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">

                {/* Hero */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="text-center mb-20"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/5 mb-8">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                        <span className="text-xs uppercase tracking-[0.3em] text-cyan-400/70">Live Demo Preview</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-none">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent tracking-[0.1em]">
                            SEE FOREXS
                        </span>
                        <span className="font-light text-white/60 ml-3 tracking-[0.15em]">AI</span>
                        <br />
                        <span className="font-light text-gray-600 text-3xl tracking-[0.2em]">in action</span>
                    </h1>

                    <p className="text-gray-500 font-light text-lg max-w-xl mx-auto leading-relaxed mb-10">
                        Institutional-grade market analysis. Three model pipelines running simultaneously on NASDAQ, XAUUSD, DAX, and US Oil.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link href="/signup">
                            <button className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.2)] hover:shadow-[0_0_30px_rgba(192,192,192,0.4)] transition-all duration-300 text-white uppercase tracking-widest text-xs px-10 py-4 rounded-sm font-medium">
                                Start Free — No Credit Card
                            </button>
                        </Link>
                        <Link href="/login">
                            <button className="border border-white/10 hover:border-white/20 bg-white/[0.03] hover:bg-white/[0.06] transition-all text-gray-400 hover:text-white uppercase tracking-widest text-xs px-10 py-4 rounded-sm">
                                Sign In
                            </button>
                        </Link>
                    </div>
                </motion.div>

                {/* Live market ticker preview */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-16"
                >
                    {markets.map((m) => (
                        <div key={m.symbol} className="bg-white/[0.03] border border-white/8 rounded-xl p-5 text-center">
                            <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-2">{m.symbol}</p>
                            <p className="text-xl font-mono font-light text-white mb-1">{m.price}</p>
                            <p className={`text-xs font-mono ${m.trend === "up" ? "text-emerald-400" : "text-red-400"}`}>
                                {m.change}
                            </p>
                        </div>
                    ))}
                </motion.div>

                {/* Signal card preview */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.5 }}
                    className="mb-20"
                >
                    <div className="text-center mb-10">
                        <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-2">Signal Output</p>
                        <h2 className="text-2xl font-light text-white">Sample AI Signal Card</h2>
                    </div>

                    {/* Mock signal card */}
                    <div className="max-w-2xl mx-auto bg-white/[0.03] border border-white/8 rounded-2xl p-8 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/3 blur-3xl" />
                        <div className="flex items-start justify-between mb-6">
                            <div>
                                <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-1">XAUUSD · M15</p>
                                <p className="text-2xl font-light text-white">2,340.50</p>
                            </div>
                            <div className="px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-400 text-xs uppercase tracking-widest">
                                STRONG BUY
                            </div>
                        </div>
                        <div className="space-y-3 mb-6">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 font-light uppercase tracking-wider text-xs">Confidence</span>
                                <span className="text-white font-mono">92%</span>
                            </div>
                            <div className="h-0.5 w-full bg-white/5 rounded overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-gray-600 via-gray-300 to-gray-600 rounded" style={{ width: "92%" }} />
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 font-light uppercase tracking-wider text-xs">Target</span>
                                <span className="text-emerald-400 font-mono">2,360.00</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-600 font-light uppercase tracking-wider text-xs">Stop Loss</span>
                                <span className="text-red-400 font-mono">2,325.00</span>
                            </div>
                        </div>
                        <div className="pt-4 border-t border-white/5">
                            <p className="text-xs text-gray-600 font-light">ML Model · EMEL 9/9 · PULSE Confirmed</p>
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm rounded-2xl">
                            <div className="text-center">
                                <p className="text-sm text-gray-400 font-light mb-4 tracking-wide">Sign up to access live signals</p>
                                <Link href="/signup">
                                    <button className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.3)] hover:shadow-[0_0_25px_rgba(192,192,192,0.5)] transition-all duration-300 text-white uppercase tracking-widest text-xs px-8 py-3 rounded-sm font-medium">
                                        Get Free Access
                                    </button>
                                </Link>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Three models */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.7 }}
                    className="mb-20"
                >
                    <div className="text-center mb-12">
                        <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-2">Core Technology</p>
                        <h2 className="text-2xl font-light text-white">Three Parallel Intelligence Pipelines</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {features.map((f, i) => (
                            <motion.div
                                key={f.label}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: i * 0.1 }}
                                className={`bg-white/[0.03] border rounded-xl p-6 ${f.border}`}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <p className={`text-sm font-light tracking-wide ${f.accent}`}>{f.label}</p>
                                    </div>
                                    <span className="text-xs uppercase tracking-widest text-gray-700 border border-white/5 px-2 py-0.5 rounded">
                                        {f.tag}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600 font-light leading-relaxed">{f.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>

                {/* CTA */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center border border-white/6 rounded-3xl p-16 bg-white/[0.02]"
                >
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Ready to start?</p>
                    <h2 className="text-4xl font-light text-white mb-4 tracking-wide">Join ForexsAI</h2>
                    <p className="text-gray-600 font-light mb-10 max-w-md mx-auto">Free forever plan. No credit card required. Upgrade to Pro when you need more.</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link href="/signup">
                            <button className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.2)] hover:shadow-[0_0_30px_rgba(192,192,192,0.4)] transition-all duration-300 text-white uppercase tracking-widest text-xs px-12 py-4 rounded-sm font-medium">
                                Create Free Account
                            </button>
                        </Link>
                        <Link href="/pricing">
                            <button className="border border-white/10 hover:border-white/20 bg-white/[0.03] hover:bg-white/[0.06] transition-all text-gray-400 hover:text-white uppercase tracking-widest text-xs px-12 py-4 rounded-sm">
                                View Pricing
                            </button>
                        </Link>
                    </div>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
