"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { Layers, Brain, CandlestickChart, Activity, Zap, Signal, BarChart2, Target, Lock, TrendingUp } from "lucide-react";

// --- Visual Components ---

const MtfVisual = () => {
    return (
        <div className="relative w-full h-full flex items-center justify-center p-8">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

            {/* Stacked Charts */}
            {[0, 1, 2].map((i) => (
                <motion.div
                    key={i}
                    initial={{ y: 20 * (2 - i), opacity: 0.5, scale: 0.9 }}
                    animate={{
                        y: [20 * (2 - i), 10 * (2 - i), 20 * (2 - i)],
                        scale: [0.9, 0.95, 0.9],
                        opacity: i === 2 ? 1 : 0.6
                    }}
                    transition={{ duration: 4, repeat: Infinity, delay: i * 0.5 }}
                    className={`absolute w-3/4 h-3/5 rounded-xl border border-white/10 backdrop-blur-md flex flex-col overflow-hidden shadow-2xl origin-bottom
                    ${i === 0 ? 'bg-indigo-900/40 z-10 bottom-8 scale-90' : ''}
                    ${i === 1 ? 'bg-indigo-800/40 z-20 bottom-16 scale-95' : ''}
                    ${i === 2 ? 'bg-indigo-600/20 z-30 bottom-24 border-indigo-400/30' : ''}
                    `}
                    style={{ left: '12.5%' }}
                >
                    {/* Header */}
                    <div className="h-8 border-b border-white/5 flex items-center px-4 gap-2">
                        <div className="w-2 h-2 rounded-full bg-white/20" />
                        <div className="w-2 h-2 rounded-full bg-white/20" />
                        <div className="ml-auto text-xs font-mono text-white/40">
                            {['M15', 'H4', 'D1'][i]}
                        </div>
                    </div>
                    {/* Chart Area */}
                    <div className="flex-1 relative p-4">
                        <svg className="w-full h-full" viewBox="0 0 100 50" preserveAspectRatio="none">
                            <path
                                d="M0,40 Q25,35 50,20 T100,5"
                                fill="none"
                                stroke={i === 2 ? "#818cf8" : "rgba(255,255,255,0.2)"}
                                strokeWidth="2"
                            />
                            {i === 2 && (
                                <motion.circle
                                    cx="0" cy="40" r="3" fill="#818cf8"
                                    animate={{ offsetDistance: "100%" }}
                                >
                                    <animateMotion path="M0,40 Q25,35 50,20 T100,5" dur="3s" repeatCount="indefinite" />
                                </motion.circle>
                            )}
                        </svg>
                    </div>
                </motion.div>
            ))}

            {/* Connecting Line */}
            <motion.div
                className="absolute inset-0 z-40 flex items-center justify-center pointer-events-none"
                animate={{ opacity: [0, 1, 0] }}
                transition={{ duration: 3, repeat: Infinity, delay: 2 }}
            >
                <div className="h-[120%] w-[1px] bg-gradient-to-b from-transparent via-emerald-400 to-transparent" />
            </motion.div>
        </div>
    );
};

const PatternsVisual = () => {
    return (
        <div className="relative w-full h-full flex items-center justify-center bg-slate-900/20">
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

            {/* Chart */}
            <div className="w-4/5 h-3/5 border border-white/5 rounded-lg relative">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 200 100">
                    {/* Head and Shoulders Path */}
                    <motion.path
                        d="M0,80 L30,40 L50,70 L80,10 L110,70 L130,40 L160,80"
                        fill="none"
                        stroke="#34d399"
                        strokeWidth="2"
                        initial={{ pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{ duration: 3, repeat: Infinity }}
                    />
                    {/* Neckline */}
                    <motion.line
                        x1="0" y1="80" x2="160" y2="80"
                        stroke="rgba(255,255,255,0.3)"
                        strokeWidth="1"
                        strokeDasharray="4 4"
                    />
                </svg>

                {/* Labels */}
                <motion.div
                    className="absolute top-[30%] left-[38%] px-2 py-1 bg-emerald-500/20 border border-emerald-500/50 rounded text-xs text-emerald-400 whitespace-nowrap"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1, duration: 0.5, repeat: Infinity, repeatDelay: 2.5 }}
                >
                    Head & Shoulders
                </motion.div>
            </div>
        </div>
    );
};

const AiVisual = () => {
    return (
        <div className="relative w-full h-full flex items-center justify-center">
            {/* Brain/Network Nodes */}
            <div className="relative w-48 h-48">
                {[...Array(8)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute w-3 h-3 bg-purple-400 rounded-full box-shadow-glow"
                        style={{
                            top: `${50 + 35 * Math.sin(i * Math.PI / 4)}%`,
                            left: `${50 + 35 * Math.cos(i * Math.PI / 4)}%`,
                        }}
                        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 2, delay: i * 0.1, repeat: Infinity }}
                    />
                ))}

                {/* Central Processing Unit */}
                <motion.div
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 bg-purple-500/20 border border-purple-500/50 rounded-full flex items-center justify-center backdrop-blur-md"
                    animate={{ boxShadow: ["0 0 0px rgba(168,85,247,0)", "0 0 20px rgba(168,85,247,0.4)", "0 0 0px rgba(168,85,247,0)"] }}
                    transition={{ duration: 3, repeat: Infinity }}
                >
                    <Brain className="w-8 h-8 text-purple-400" />
                </motion.div>

                {/* Connecting Lines */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {[...Array(8)].map((_, i) => (
                        <motion.line
                            key={i}
                            x1="50%" y1="50%"
                            x2={`${50 + 35 * Math.cos(i * Math.PI / 4)}%`}
                            y2={`${50 + 35 * Math.sin(i * Math.PI / 4)}%`}
                            stroke="rgba(168,85,247,0.3)"
                            strokeWidth="1"
                        />
                    ))}
                </svg>
            </div>
        </div>
    );
};

const RealtimeVisual = () => {
    return (
        <div className="relative w-full h-full flex flex-col items-center justify-center p-8 overflow-hidden">
            {/* Scrolling Ticker Tape Effect */}
            <div className="absolute top-10 w-full overflow-hidden whitespace-nowrap opacity-30">
                <motion.div
                    className="inline-block text-xs font-mono text-amber-400"
                    animate={{ x: "-50%" }}
                    transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                >
                    NASDAQ: 18,450.25 ▲ | XAUUSD: 2,340.10 ▼ | EURUSD: 1.0850 ▲ | &nbsp;
                    NASDAQ: 18,450.25 ▲ | XAUUSD: 2,340.10 ▼ | EURUSD: 1.0850 ▲ | &nbsp;
                </motion.div>
            </div>

            {/* Radar Scan */}
            <div className="relative w-40 h-40 rounded-full border border-amber-500/20 bg-amber-900/5">
                <div className="absolute inset-0 rounded-full border border-amber-500/10 scale-75" />
                <div className="absolute inset-0 rounded-full border border-amber-500/5 scale-50" />

                <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-500/20 to-transparent w-1/2 h-1/2 origin-bottom-right top-0 left-0 rounded-tl-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                    style={{ transformOrigin: "100% 100%" }}
                />

                <motion.div
                    className="absolute top-1/3 left-1/3 w-2 h-2 bg-amber-400 rounded-full shadow-[0_0_10px_rgba(245,158,11,0.8)]"
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ duration: 1, repeat: Infinity }}
                />
            </div>

            <div className="mt-6 flex items-center gap-2 px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full">
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-xs font-medium text-amber-400">LIVE SCANNING</span>
            </div>
        </div>
    );
};

const SignalsVisual = () => {
    return (
        <div className="relative w-full h-full flex items-center justify-center p-8">
            <motion.div
                className="w-64 bg-[#131B2D] border border-cyan-500/30 rounded-2xl p-5 shadow-2xl relative overflow-hidden"
                initial={{ y: 20 }}
                animate={{ y: 0 }}
                transition={{ duration: 0.5 }}
            >
                {/* Glow Effect */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/20 blur-3xl -mr-10 -mt-10" />

                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                            <span className="text-orange-400 font-bold">Gold</span>
                        </div>
                        <div>
                            <h4 className="text-white font-bold">XAUUSD</h4>
                            <span className="text-emerald-400 text-xs font-bold">STRONG BUY</span>
                        </div>
                    </div>
                    <div className="px-2 py-1 rounded bg-white/5 border border-white/10 text-xs text-white/60">
                        M15
                    </div>
                </div>

                <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                        <span className="text-white/40">Entry</span>
                        <span className="text-white font-mono">2345.50</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-white/40">Target</span>
                        <span className="text-emerald-400 font-mono">2360.00</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden mt-2">
                        <motion.div
                            className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                            initial={{ width: "0%" }}
                            animate={{ width: "92%" }}
                            transition={{ duration: 1, delay: 0.5 }}
                        />
                    </div>
                    <div className="text-right text-xs text-cyan-400 mt-1">
                        Confidence Score: 92/100
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default function FeaturesPage() {
    const { t } = useI18n();

    const features = [
        { key: "mtf", icon: Layers, color: "text-indigo-400", bg: "bg-indigo-500/10", visual: MtfVisual },
        { key: "patterns", icon: CandlestickChart, color: "text-emerald-400", bg: "bg-emerald-500/10", visual: PatternsVisual },
        { key: "ai", icon: Brain, color: "text-purple-400", bg: "bg-purple-500/10", visual: AiVisual },
        { key: "realtime", icon: Zap, color: "text-amber-400", bg: "bg-amber-500/10", visual: RealtimeVisual },
        { key: "signals", icon: Signal, color: "text-cyan-400", bg: "bg-cyan-500/10", visual: SignalsVisual }
    ];

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto z-10">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-20"
                >
                    <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                        {t("featuresPage.title")}
                    </h1>
                    <p className="text-xl text-[#E5E7EB]/70 max-w-2xl mx-auto">
                        {t("featuresPage.subtitle")}
                    </p>
                </motion.div>

                <div className="space-y-32">
                    {features.map((feature, i) => (
                        <motion.div
                            key={feature.key}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-100px" }}
                            transition={{ duration: 0.7 }}
                            className={`flex flex-col ${i % 2 === 1 ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-12 md:gap-20`}
                        >
                            <div className="flex-1 space-y-6">
                                <div className={`w-16 h-16 rounded-2xl ${feature.bg} flex items-center justify-center mb-6 ring-1 ring-white/10`}>
                                    <feature.icon className={`w-8 h-8 ${feature.color}`} />
                                </div>
                                <h2 className="text-3xl font-bold text-white">{t(`featuresPage.items.${feature.key}.title`)}</h2>
                                <p className="text-lg text-[#E5E7EB]/70 leading-relaxed">
                                    {t(`featuresPage.items.${feature.key}.description`)}
                                </p>
                                <ul className="space-y-3 mt-4">
                                    {(Array.isArray(t(`featuresPage.items.${feature.key}.bullets`)) ? t(`featuresPage.items.${feature.key}.bullets`) : []).map((bullet: string, j: number) => (
                                        <li key={j} className="flex items-start gap-3 text-[#E5E7EB]/80">
                                            <div className={`mt-1.5 w-1.5 h-1.5 rounded-full ${feature.color.replace('text-', 'bg-')}`} />
                                            <span>{bullet}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="flex-1 w-full relative">
                                {/* Decorative Glow */}
                                <div className={`absolute -inset-4 bg-gradient-to-r ${feature.bg.replace('bg-', 'from-').replace('/10', '/30')} to-transparent blur-2xl opacity-40 rounded-full`} />

                                <div className="aspect-[4/3] rounded-3xl bg-[#0F1623] border border-white/10 overflow-hidden relative group shadow-2xl">
                                    <feature.visual />
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
            <Footer />
        </main>
    );
}
