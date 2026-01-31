"use client";

export const dynamic = 'force-dynamic';

import { motion, useInView } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { useRef, useEffect, useState } from "react";
import { Target, Eye, Lightbulb, Shield, Database, Clock, Zap, TrendingUp } from "lucide-react";

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

    const values = [
        { key: "transparency", icon: Eye, color: "text-cyan-400", bg: "from-cyan-500/20 to-blue-500/20" },
        { key: "accuracy", icon: Target, color: "text-emerald-400", bg: "from-emerald-500/20 to-teal-500/20" },
        { key: "education", icon: Lightbulb, color: "text-amber-400", bg: "from-amber-500/20 to-orange-500/20" },
        { key: "innovation", icon: Zap, color: "text-purple-400", bg: "from-purple-500/20 to-indigo-500/20" }
    ];

    const techItems = [
        { key: "data", icon: Database, color: "text-indigo-400" },
        { key: "training", icon: Clock, color: "text-emerald-400" },
        { key: "realtime", icon: Zap, color: "text-amber-400" },
        { key: "accuracy", icon: TrendingUp, color: "text-cyan-400" }
    ];

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
                    <Counter value={49000000} label={t("about.stats.data") as string} />
                    <Counter value={24} label={t("about.stats.years") as string} suffix="+" />
                    <Counter value={9} label={t("about.stats.training") as string} suffix="mo" />
                    <Counter value={78} label={t("about.stats.accuracy") as string} suffix="%" />
                </div>

                {/* Story Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-32">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                    >
                        <div className="relative">
                            <div className="absolute inset-0 bg-indigo-500/10 blur-3xl -z-10 rounded-full" />
                            <div className="glass-premium p-8 rounded-3xl">
                                <h3 className="text-3xl font-bold text-white mb-6 flex items-center gap-3">
                                    <span className="w-1 h-10 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full" />
                                    {t("about.story.title")}
                                </h3>
                                <p className="text-[#E5E7EB]/80 leading-relaxed mb-6 text-lg">
                                    {t("about.story.p1")}
                                </p>
                                <p className="text-[#E5E7EB]/80 leading-relaxed text-lg">
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
                        className="relative h-[450px] rounded-3xl overflow-hidden border border-white/10"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 to-indigo-950">
                            <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20" />
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

                {/* Mission & Vision */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-32">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="glass-premium p-8 rounded-3xl"
                    >
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center">
                                <Target className="w-7 h-7 text-emerald-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">{t("about.mission.title")}</h3>
                        </div>
                        <p className="text-[#E5E7EB]/70 leading-relaxed text-lg">
                            {t("about.mission.text")}
                        </p>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.1 }}
                        className="glass-premium p-8 rounded-3xl"
                    >
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center">
                                <Eye className="w-7 h-7 text-indigo-400" />
                            </div>
                            <h3 className="text-2xl font-bold text-white">{t("about.vision.title")}</h3>
                        </div>
                        <p className="text-[#E5E7EB]/70 leading-relaxed text-lg">
                            {t("about.vision.text")}
                        </p>
                    </motion.div>
                </div>

                {/* Values */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="mb-32"
                >
                    <h2 className="text-3xl font-bold text-white text-center mb-12">{t("about.values.title")}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {values.map((value, idx) => (
                            <motion.div
                                key={value.key}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.5, delay: idx * 0.1 }}
                                className="glass-premium p-6 rounded-2xl text-center"
                            >
                                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${value.bg} border border-white/10 flex items-center justify-center mx-auto mb-4`}>
                                    <value.icon className={`w-8 h-8 ${value.color}`} />
                                </div>
                                <h4 className="text-lg font-bold text-white mb-2">{t(`about.values.${value.key}.title`)}</h4>
                                <p className="text-sm text-[#E5E7EB]/60">{t(`about.values.${value.key}.text`)}</p>
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
                    className="glass-premium p-10 rounded-3xl"
                >
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold text-white mb-4">{t("about.technology.title")}</h2>
                        <p className="text-[#E5E7EB]/60 max-w-2xl mx-auto">{t("about.technology.description")}</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {techItems.map((item, idx) => (
                            <div key={item.key} className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
                                <item.icon className={`w-10 h-10 ${item.color} mx-auto mb-4`} />
                                <h4 className="text-xl font-bold text-white mb-2">{t(`about.technology.items.${item.key}.title`)}</h4>
                                <p className="text-sm text-[#E5E7EB]/60">{t(`about.technology.items.${item.key}.text`)}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
