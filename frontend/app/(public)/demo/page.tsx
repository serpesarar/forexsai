"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { LineChart, ArrowUpRight, ArrowRight, ShieldCheck, Zap, Activity, BarChart2, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export default function DemoPage() {
    const { t } = useI18n();
    const [step, setStep] = useState(0); // 0: Intro, 1: Select, 2: Analyzing, 3: Signal, 4: Result, 5: CTA
    const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

    // Mock Chart Data Animation
    const [chartData, setChartData] = useState<number[]>([100, 102, 101, 104, 103, 105, 108, 106, 110]);

    // Step Auto-progression logic for "Analyzing" phase
    useEffect(() => {
        if (step === 2) {
            const timer = setTimeout(() => {
                setStep(3);
            }, 3000); // 3 seconds of "analyzing"
            return () => clearTimeout(timer);
        }
    }, [step]);

    const handleStart = () => setStep(1);

    const handleSelectAsset = (asset: string) => {
        setSelectedAsset(asset);
        setStep(2);
    };

    const handleExecute = () => {
        setStep(4);
    };

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans flex flex-col">
            <TopNav />
            <AnimatedBackground />

            <div className="flex-grow relative z-10 flex flex-col items-center justify-center p-4 pt-32 pb-20">

                {/* Intro Screen */}
                <AnimatePresence mode="wait">
                    {step === 0 && (
                        <motion.div
                            key="intro"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="text-center max-w-2xl px-4"
                        >
                            <div className="w-20 h-20 bg-indigo-500/10 rounded-2xl flex items-center justify-center mx-auto mb-8 border border-indigo-500/20 shadow-[0_0_30px_rgba(99,102,241,0.2)]">
                                <Zap className="w-10 h-10 text-indigo-400" />
                            </div>
                            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                                {t("demo.title")}
                            </h1>
                            <p className="text-xl text-[#E5E7EB]/70 mb-10">
                                {t("demo.subtitle")}
                            </p>
                            <button
                                onClick={handleStart}
                                className="px-8 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl text-white font-bold text-lg hover:shadow-[0_0_30px_rgba(99,102,241,0.4)] transition-shadow flex items-center gap-2 mx-auto"
                            >
                                {t("demo.start")} <ArrowRight className="w-5 h-5" />
                            </button>
                        </motion.div>
                    )}

                    {/* Simulation UI */}
                    {step > 0 && step < 5 && (
                        <motion.div
                            key="sim"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.05 }}
                            className="w-full max-w-5xl aspect-video bg-[#0F1623] border border-white/10 rounded-2xl shadow-2xl flex overflow-hidden relative"
                        >
                            {/* Start Over Button */}
                            <button
                                onClick={() => setStep(0)}
                                className="absolute top-4 right-4 z-50 text-xs text-white/30 hover:text-white"
                            >
                                EXIT DEMO
                            </button>

                            {/* Sidebar Mock */}
                            <div className="w-64 border-r border-white/5 bg-[#0B1220]/50 p-4 hidden md:flex flex-col gap-4">
                                <div className="h-8 w-24 bg-white/10 rounded mb-8" />
                                {[1, 2, 3, 4].map(i => (
                                    <div key={i} className="h-10 w-full bg-white/5 rounded-lg" />
                                ))}
                            </div>

                            {/* Main Content */}
                            <div className="flex-1 p-6 relative flex flex-col">
                                {/* Top Bar Mock */}
                                <div className="h-12 border-b border-white/5 flex items-center justify-between mb-6">
                                    <div className="h-4 w-32 bg-white/10 rounded" />
                                    <div className="h-8 w-8 rounded-full bg-white/10" />
                                </div>

                                {/* Dynamic Content based on Step */}
                                <div className="flex-1 relative">

                                    {/* Step 1: Select Asset */}
                                    {step === 1 && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <h2 className="text-2xl font-bold text-white mb-8">{t("demo.steps.select.title")}</h2>
                                            <div className="flex gap-6">
                                                {['NASDAQ', 'XAUUSD', 'EURUSD'].map((asset) => (
                                                    <button
                                                        key={asset}
                                                        onClick={() => handleSelectAsset(asset)}
                                                        className="w-40 h-32 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 hover:border-indigo-500/50 transition-all flex flex-col items-center justify-center gap-2 group"
                                                    >
                                                        <span className="text-lg font-bold text-white">{asset}</span>
                                                        <Activity className="w-6 h-6 text-white/30 group-hover:text-indigo-400" />
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Step 2: Analyzing */}
                                    {step === 2 && (
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <div className="relative w-32 h-32 mb-8">
                                                <motion.div
                                                    className="absolute inset-0 border-4 border-indigo-500/30 rounded-full"
                                                />
                                                <motion.div
                                                    className="absolute inset-0 border-4 border-indigo-500 rounded-full border-t-transparent"
                                                    animate={{ rotate: 360 }}
                                                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                                />
                                                <div className="absolute inset-0 flex items-center justify-center font-mono text-indigo-400 font-bold">
                                                    AI
                                                </div>
                                            </div>
                                            <h3 className="text-xl font-bold text-white mb-2">{t("demo.steps.analyzing.title")}</h3>
                                            <p className="text-white/50">{t("demo.steps.analyzing.text")}</p>
                                        </div>
                                    )}

                                    {/* Step 3 & 4: Signal & Result */}
                                    {(step === 3 || step === 4) && (
                                        <div className="flex flex-col h-full">
                                            {/* Simulate Chart */}
                                            <div className="flex-1 bg-white/5 rounded-xl mb-4 relative overflow-hidden flex items-end p-4 gap-2">
                                                {/* Simple CSS Bar Chart for visual */}
                                                {[40, 65, 45, 70, 85, 60, 75, 90, 80, 95, 110].map((h, i) => (
                                                    <motion.div
                                                        key={i}
                                                        initial={{ height: 0 }}
                                                        animate={{ height: `${h}%` }}
                                                        transition={{ duration: 0.5, delay: i * 0.1 }}
                                                        className={`flex-1 rounded-t-sm ${i > 8 ? 'bg-emerald-500' : 'bg-white/10'}`}
                                                    />
                                                ))}
                                                {/* Signal Overlay */}
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.8 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#0B1220]/90 backdrop-blur-xl border border-emerald-500/50 p-6 rounded-2xl shadow-2xl text-center min-w-[300px]"
                                                >
                                                    {step === 3 ? (
                                                        <>
                                                            <div className="text-emerald-400 font-bold text-sm tracking-widest mb-2 flex items-center justify-center gap-2">
                                                                <Zap className="w-4 h-4 fill-current" /> {t("demo.ui.analyze")} COMPLETE
                                                            </div>
                                                            <div className="text-4xl font-bold text-white mb-1">BUY</div>
                                                            <div className="text-2xl text-white/50 font-mono mb-4">{selectedAsset}</div>

                                                            <div className="flex justify-between text-sm border-t border-white/10 pt-4 mb-6">
                                                                <div className="flex flex-col">
                                                                    <span className="text-white/40 mb-1">{t("demo.ui.confidence")}</span>
                                                                    <span className="text-indigo-400 font-bold">96%</span>
                                                                </div>
                                                                <div className="flex flex-col text-right">
                                                                    <span className="text-white/40 mb-1">{t("demo.ui.target")}</span>
                                                                    <span className="text-emerald-400 font-bold font-mono">+12.5%</span>
                                                                </div>
                                                            </div>

                                                            <button
                                                                onClick={handleExecute}
                                                                className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-bold transition-colors shadow-lg shadow-emerald-500/20"
                                                            >
                                                                {t("demo.ui.buy")}
                                                            </button>
                                                        </>
                                                    ) : (
                                                        <div className="py-8">
                                                            <motion.div
                                                                initial={{ scale: 0 }}
                                                                animate={{ scale: 1 }}
                                                                className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4"
                                                            >
                                                                <CheckCircle2 className="w-8 h-8 text-white" />
                                                            </motion.div>
                                                            <h3 className="text-2xl font-bold text-white mb-2">{t("demo.ui.success")}!</h3>
                                                            <p className="text-emerald-400 font-bold text-lg mb-6">+$458.20 Profit</p>
                                                            <button
                                                                onClick={() => setStep(5)}
                                                                className="text-white/50 hover:text-white text-sm underline"
                                                            >
                                                                Continue
                                                            </button>
                                                        </div>
                                                    )}
                                                </motion.div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Step 5: CTA */}
                    {step === 5 && (
                        <motion.div
                            key="cta"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-center max-w-2xl px-4"
                        >
                            <h2 className="text-4xl font-bold text-white mb-6">
                                {t("demo.cta.title")}
                            </h2>
                            <p className="text-lg text-[#E5E7EB]/70 mb-10">
                                {t("demo.subtitle")}
                            </p>
                            <Link href="/signup">
                                <button className="px-8 py-4 bg-white text-black rounded-xl font-bold text-lg hover:bg-gray-100 transition-colors">
                                    {t("demo.cta.button")}
                                </button>
                            </Link>
                        </motion.div>
                    )}

                </AnimatePresence>
            </div>

            <Footer />
        </main>
    );
}
