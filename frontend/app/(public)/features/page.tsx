"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { Layers, Brain, CandlestickChart, Activity } from "lucide-react";

export default function FeaturesPage() {
    const { t } = useI18n();

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
                    {[
                        {
                            key: "mtf",
                            icon: Layers,
                            color: "text-indigo-400",
                            bg: "bg-indigo-500/10",
                            image: "/mtf-demo.png" // Placeholder
                        },
                        {
                            key: "patterns",
                            icon: CandlestickChart,
                            color: "text-emerald-400",
                            bg: "bg-emerald-500/10",
                            image: "/patterns-demo.png"
                        },
                        {
                            key: "ai",
                            icon: Brain,
                            color: "text-purple-400",
                            bg: "bg-purple-500/10",
                            image: "/ai-demo.png"
                        }
                    ].map((feature, i) => (
                        <motion.div
                            key={feature.key}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-100px" }}
                            transition={{ duration: 0.7 }}
                            className={`flex flex-col ${i % 2 === 1 ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-12 md:gap-20`}
                        >
                            <div className="flex-1 space-y-6">
                                <div className={`w-16 h-16 rounded-2xl ${feature.bg} flex items-center justify-center mb-6`}>
                                    <feature.icon className={`w-8 h-8 ${feature.color}`} />
                                </div>
                                <h2 className="text-3xl font-bold text-white">{t(`featuresPage.items.${feature.key}.title`)}</h2>
                                <p className="text-lg text-[#E5E7EB]/70 leading-relaxed">
                                    {t(`featuresPage.items.${feature.key}.description`)}
                                </p>
                                <ul className="space-y-3 mt-4">
                                    {(Array.isArray(t(`featuresPage.items.${feature.key}.bullets`)) ? t(`featuresPage.items.${feature.key}.bullets`) : []).map((bullet: string, j: number) => (
                                        <li key={j} className="flex items-start gap-3 text-[#E5E7EB]/80">
                                            <Activity className={`w-5 h-5 mt-1 shrink-0 ${feature.color}`} />
                                            <span>{bullet}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div className="flex-1 w-full">
                                <div className="aspect-video rounded-3xl bg-white/5 border border-white/10 backdrop-blur-sm flex items-center justify-center overflow-hidden relative group">
                                    <div className={`absolute inset-0 bg-gradient-to-br ${feature.bg} opacity-20 group-hover:opacity-30 transition-opacity`} />
                                    {/* Placeholder for visual */}
                                    <feature.icon className={`w-24 h-24 ${feature.color} opacity-20`} />
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
