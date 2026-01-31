"use client";

export const dynamic = 'force-dynamic';

import { motion, useInView } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { useRef, useEffect, useState } from "react";

function Counter({ value, label, suffix = "" }: { value: number; label: string; suffix?: string }) {
    const ref = useRef(null);
    const isInView = useInView(ref, { once: true });
    const [count, setCount] = useState(0);

    useEffect(() => {
        if (isInView) {
            const duration = 2000; // 2 seconds
            const steps = 60;
            const stepValue = value / steps;
            let current = 0;

            const timer = setInterval(() => {
                current += stepValue;
                if (current >= value) {
                    setCount(value);
                    clearInterval(timer);
                } else {
                    setCount(Math.floor(current));
                }
            }, duration / steps);

            return () => clearInterval(timer);
        }
    }, [isInView, value]);

    return (
        <div ref={ref} className="text-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
            <div className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-indigo-200 mb-2">
                {count.toLocaleString()}{suffix}
            </div>
            <div className="text-sm font-medium text-emerald-400 uppercase tracking-widest">{label}</div>
        </div>
    );
}

export default function AboutPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto z-10">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="text-center mb-24"
                >
                    <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
                        {t("about.hero.title")}
                    </h1>
                    <p className="text-xl text-[#E5E7EB]/70 max-w-3xl mx-auto font-light leading-relaxed">
                        {t("about.hero.subtitle")}
                    </p>
                </motion.div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-32">
                    <Counter value={49000000} label={t("about.stats.data")} />
                    <Counter value={24} label={t("about.stats.years")} suffix="+" />
                    <Counter value={9} label={t("about.stats.training")} suffix="mo" />
                    <Counter value={78} label={t("about.stats.accuracy")} suffix="%" />
                </div>

                {/* Story Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center mb-24">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                    >
                        <div className="relative">
                            <div className="absolute inset-0 bg-indigo-500/10 blur-3xl -z-10 rounded-full" />
                            <div className="border border-white/10 bg-white/5 p-8 rounded-3xl backdrop-blur-md">
                                <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                                    <span className="w-1 h-8 bg-emerald-500 rounded-full" />
                                    {t("about.story.title")}
                                </h3>
                                <p className="text-[#E5E7EB]/80 leading-relaxed mb-6">
                                    {t("about.story.p1")}
                                </p>
                                <p className="text-[#E5E7EB]/80 leading-relaxed">
                                    {t("about.story.p2")}
                                </p>
                            </div>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="relative h-[400px] rounded-3xl overflow-hidden border border-white/10"
                    >
                        {/* Abstract decorative image representation */}
                        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 to-indigo-950">
                            <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20" />
                            {/* Decorative chart lines */}
                            <svg className="absolute inset-0 w-full h-full opacity-30" viewBox="0 0 100 100" preserveAspectRatio="none">
                                <path d="M0,80 C20,70 40,90 60,60 S80,40 100,20" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-emerald-400" />
                                <path d="M0,90 C30,80 50,85 70,50 S90,30 100,10" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-indigo-400" />
                            </svg>
                            <div className="absolute bottom-6 left-6 right-6">
                                <div className="p-4 rounded-xl bg-black/60 backdrop-blur-md border border-white/10">
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <div className="text-xs text-emerald-400 font-mono mb-1">MODEL V3.4.1</div>
                                            <div className="text-lg font-bold">Training Complete</div>
                                        </div>
                                        <div className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-xs font-bold">78.4% ACCURACY</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
