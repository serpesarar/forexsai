"use client";

export const dynamic = 'force-dynamic';

import { useRef, useEffect, useState } from "react";
import { motion, useInView } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

function Counter({ value, label, suffix = "" }: { value: number; label: string; suffix?: string }) {
    const ref = useRef(null);
    const isInView = useInView(ref, { once: true });
    const [count, setCount] = useState(0);

    useEffect(() => {
        if (isInView) {
            const duration = 2000;
            const steps = 60;
            const stepValue = value / steps;
            let current = 0;
            const timer = setInterval(() => {
                current += stepValue;
                if (current >= value) { setCount(value); clearInterval(timer); }
                else { setCount(Math.floor(current)); }
            }, duration / steps);
            return () => clearInterval(timer);
        }
    }, [isInView, value]);

    return (
        <div ref={ref} className="text-center p-6 rounded-xl bg-white/[0.03] border border-white/8 backdrop-blur-sm">
            <div className="text-4xl md:text-5xl font-bold bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent mb-2 tracking-tight">
                {count.toLocaleString()}{suffix}
            </div>
            <div className="text-xs font-light uppercase tracking-[0.3em] text-gray-500">{label}</div>
        </div>
    );
}

const values = [
    {
        key: "transparency",
        icon: (
            <svg className="w-8 h-8 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
        ),
        title: "Transparency",
        text: "Every signal explained with confidence metrics and reasoning. No black box decisions.",
        color: "border-cyan-500/20 bg-cyan-500/5",
    },
    {
        key: "accuracy",
        icon: (
            <svg className="w-8 h-8 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" /><line x1="12" y1="2" x2="12" y2="5" /><line x1="12" y1="19" x2="12" y2="22" /><line x1="2" y1="12" x2="5" y2="12" /><line x1="19" y1="12" x2="22" y2="12" /></svg>
        ),
        title: "Precision",
        text: "78.4% directional accuracy across 49M+ analyzed data points from 24+ years of market history.",
        color: "border-white/10 bg-white/[0.03]",
    },
    {
        key: "education",
        icon: (
            <svg className="w-8 h-8 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>
        ),
        title: "Education",
        text: "Embedded learning dashboard showing why patterns succeed or fail — develop as a trader.",
        color: "border-amber-500/20 bg-amber-500/5",
    },
    {
        key: "innovation",
        icon: (
            <svg className="w-8 h-8 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
        ),
        title: "Innovation",
        text: "Three parallel model pipelines: EMEL, PULSE, and ML Hybrid — always improving.",
        color: "border-purple-500/20 bg-purple-500/5",
    },
];

const techStack = [
    { label: "LightGBM", desc: "Gradient boosting ML models trained on 30M+ candles" },
    { label: "Claude AI", desc: "Real-time news sentiment analysis via Anthropic" },
    { label: "FastAPI", desc: "Sub-50ms backend signal processing pipeline" },
    { label: "WebSocket", desc: "Live market data broadcast to all active sessions" },
    { label: "Multi-TF", desc: "M1, M5, M15, M30, H1, H4 timeframe confluence" },
    { label: "ICT / SMC", desc: "Smart Money Concepts & Order Block detection" },
];

export default function AboutPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-black text-white font-sans">
            <TopNav />

            {/* Subtle background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-cyan-500/3 blur-3xl rounded-full" />
                <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-purple-500/3 blur-3xl rounded-full" />
            </div>

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">

                {/* Hero */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1 }}
                    className="text-center mb-28"
                >
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-6">About ForexsAi</p>
                    <h1 className="text-5xl md:text-8xl font-bold mb-8 leading-none">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent tracking-[0.1em]">
                            FOREXS
                        </span>
                        <span className="font-light text-white/60 tracking-[0.15em] ml-3">AI</span>
                    </h1>
                    <p className="text-lg text-gray-500 max-w-2xl mx-auto font-light leading-relaxed border-l-2 border-cyan-500/30 pl-5 text-left mx-auto">
                        {t("about.hero.subtitle") || "Built by traders, for traders. We combine decades of market history with modern machine learning to give independent traders institutional-grade analysis."}
                    </p>
                </motion.div>

                {/* Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-28">
                    <Counter value={49000000} label="Data Points Analyzed" />
                    <Counter value={24} label="Years Market History" suffix="+" />
                    <Counter value={9} label="Months Training" suffix="mo" />
                    <Counter value={78} label="Directional Accuracy" suffix="%" />
                </div>

                {/* Story */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-28">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                    >
                        <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-4">The Story</p>
                        <h3 className="text-3xl font-light text-white mb-8 leading-tight">
                            {t("about.story.title") || "Why we built this"}
                        </h3>
                        <div className="space-y-5 text-gray-500 font-light leading-relaxed text-base">
                            <p className="border-l border-white/10 pl-5">
                                {t("about.story.p1") || "Retail traders have always faced an unfair advantage gap. Institutional desks run sophisticated quantitative models, real-time sentiment engines, and multi-timeframe risk frameworks — while individual traders scroll through charts manually."}
                            </p>
                            <p className="border-l border-white/10 pl-5">
                                {t("about.story.p2") || "ForexsAI was built to close that gap. Our system combines three independent model pipelines — EMEL (rule-based precision), PULSE (algorithmic scalp detection), and ML Hybrid (LightGBM neural) — to deliver consistent, explainable signals."}
                            </p>
                            <p className="border-l border-white/10 pl-5">
                                We track NASDAQ, XAU/USD, DAX, and US Oil with real-time WebSocket feeds, Claude AI news sentiment, and ICT/SMC order block detection.
                            </p>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="relative h-[400px] rounded-2xl overflow-hidden border border-white/8"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-black to-gray-950">
                            <div className="absolute inset-0 opacity-10"
                                style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.3) 1px, transparent 1px)`, backgroundSize: '40px 40px' }} />
                            <svg className="absolute inset-0 w-full h-full opacity-20" viewBox="0 0 100 100" preserveAspectRatio="none">
                                <path d="M0,80 C20,70 40,90 60,60 S80,40 100,20" fill="none" stroke="#06b6d4" strokeWidth="0.5" />
                                <path d="M0,90 C30,80 50,85 70,50 S90,30 100,10" fill="none" stroke="#9ca3af" strokeWidth="0.5" />
                            </svg>
                            <div className="absolute bottom-6 left-6 right-6">
                                <div className="p-4 rounded-xl bg-black/70 backdrop-blur-md border border-white/8">
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <div className="text-xs text-cyan-400 font-mono mb-1 uppercase tracking-wider">Model V3.4.1</div>
                                            <div className="text-base font-light text-white">Training Complete</div>
                                        </div>
                                        <div className="px-3 py-1 bg-white/5 border border-white/10 text-gray-400 rounded text-xs font-mono">78.4% ACC</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* Mission & Vision */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-28">
                    {[
                        {
                            tag: "Mission",
                            title: t("about.mission.title") || "Our Mission",
                            text: t("about.mission.text") || "Democratize institutional-grade market analysis for independent traders worldwide through explainable AI and real-time intelligence.",
                            accent: "border-l-2 border-cyan-500/40",
                        },
                        {
                            tag: "Vision",
                            title: t("about.vision.title") || "Our Vision",
                            text: t("about.vision.text") || "A world where every trader has access to the same analytical power as professional quant desks — transparent, fast, and continuously learning.",
                            accent: "border-l-2 border-purple-500/30",
                        },
                    ].map((item) => (
                        <motion.div
                            key={item.tag}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6 }}
                            className="bg-white/[0.03] backdrop-blur-sm border border-white/8 rounded-2xl p-8"
                        >
                            <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-4">{item.tag}</p>
                            <h3 className="text-xl font-light text-white mb-5">{item.title}</h3>
                            <p className={`text-gray-500 font-light leading-relaxed pl-4 ${item.accent}`}>{item.text}</p>
                        </motion.div>
                    ))}
                </div>

                {/* Values */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="mb-28"
                >
                    <div className="text-center mb-14">
                        <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3">Core Values</p>
                        <h2 className="text-3xl font-light text-white">{t("about.values.title") || "What drives us"}</h2>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                        {values.map((v, i) => (
                            <motion.div
                                key={v.key}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: i * 0.1 }}
                                className={`rounded-2xl border p-6 text-center ${v.color}`}
                            >
                                <div className="flex justify-center mb-5">{v.icon}</div>
                                <h4 className="text-sm uppercase tracking-[0.2em] text-white mb-3 font-light">{v.title}</h4>
                                <p className="text-xs text-gray-600 font-light leading-relaxed">{v.text}</p>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>

                {/* Technology */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="bg-white/[0.02] backdrop-blur-sm border border-white/8 rounded-3xl p-10"
                >
                    <div className="text-center mb-12">
                        <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3">Under the Hood</p>
                        <h2 className="text-3xl font-light text-white">{t("about.technology.title") || "Technology Stack"}</h2>
                        <p className="text-gray-600 font-light mt-3 max-w-lg mx-auto text-sm">
                            {t("about.technology.description") || "Every layer optimized for speed, accuracy, and explainability."}
                        </p>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {techStack.map((item) => (
                            <div key={item.label} className="flex items-start gap-4 p-5 rounded-xl bg-white/[0.03] border border-white/6 hover:border-white/12 transition-colors">
                                <span className="text-xs font-mono uppercase tracking-wider text-cyan-400/70 mt-0.5 shrink-0 w-20">{item.label}</span>
                                <p className="text-xs text-gray-600 font-light leading-relaxed">{item.desc}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
