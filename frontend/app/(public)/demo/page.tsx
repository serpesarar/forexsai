"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { Info, X, ChevronRight, Maximize2, Sparkles, Calendar, Activity, TrendingUp, Brain, ArrowLeft } from "lucide-react";
import Image from "next/image";

// Scene Definition
type SceneId = "dashboard" | "pattern_detail" | "ml_panel" | "sentiment" | "rhythm";

type Hotspot = {
    id: string;
    x: number;
    y: number;
    labelKey: string;
    icon?: any;
    targetScene?: SceneId;
    pulse?: boolean;
};

type Scene = {
    id: SceneId;
    image: string;
    hotspots: Hotspot[];
    focusArea?: string; // CSS clip-path or transform origin for zooming effect
};

export default function DemoPage() {
    const { t } = useI18n();
    const [activeSceneId, setActiveSceneId] = useState<SceneId>("dashboard");
    const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

    // Scenes with 5 distinct views
    const scenes: Record<SceneId, Scene> = {
        dashboard: {
            id: "dashboard",
            image: "/demo-assets/dashboard-main.png",
            hotspots: [
                { id: "trend", x: 28, y: 45, labelKey: "demo.tour.dashboard", icon: TrendingUp },
                { id: "patterns", x: 50, y: 45, labelKey: "demo.tour.patterns", icon: Maximize2, targetScene: "pattern_detail", pulse: true },
                { id: "sentiment", x: 72, y: 45, labelKey: "demo.tour.sentiment", icon: Brain, targetScene: "sentiment" },
                { id: "ml", x: 88, y: 30, labelKey: "demo.tour.ml", icon: Sparkles, targetScene: "ml_panel" },
                { id: "rhythm", x: 85, y: 80, labelKey: "demo.tour.rhythm", icon: Activity, targetScene: "rhythm" } // Bottom right area
            ]
        },
        pattern_detail: {
            id: "pattern_detail",
            image: "/demo-assets/pattern-popup.png",
            hotspots: [
                { id: "popup_info", x: 50, y: 50, labelKey: "demo.tour.popup", icon: Info },
                { id: "back_dash_1", x: 95, y: 5, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        ml_panel: {
            id: "ml_panel",
            image: "/demo-assets/ml-panel.png",
            hotspots: [
                { id: "ml_info", x: 30, y: 40, labelKey: "demo.tour.ml", icon: Sparkles },
                { id: "back_dash_2", x: 95, y: 5, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        sentiment: {
            id: "sentiment",
            image: "/demo-assets/sentiment-analysis.png",
            hotspots: [
                { id: "sent_info", x: 70, y: 40, labelKey: "demo.tour.sentiment", icon: Brain },
                { id: "back_dash_3", x: 95, y: 5, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        rhythm: {
            id: "rhythm",
            image: "/demo-assets/rhythm-detector.png",
            hotspots: [
                { id: "rhythm_info", x: 50, y: 50, labelKey: "demo.tour.rhythm", icon: Activity },
                { id: "back_dash_4", x: 95, y: 5, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        }
    };

    const activeScene = scenes[activeSceneId];

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans flex flex-col overflow-hidden">
            <TopNav />
            <AnimatedBackground />

            {/* Header Area */}
            <div className="absolute top-24 left-0 right-0 z-20 flex justify-center pointer-events-none">
                <motion.div
                    key={activeSceneId}
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-black/60 backdrop-blur-md border border-white/10 px-6 py-2 rounded-full flex items-center gap-3 shadow-xl"
                >
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-sm font-medium text-white/90">
                        {activeSceneId === 'dashboard' ? t("demo.subtitle") : t(`demo.tour.${activeSceneId === 'pattern_detail' ? 'patterns' : activeSceneId === 'ml_panel' ? 'ml' : activeSceneId}.title`)}
                    </span>
                </motion.div>
            </div>

            {/* Main Interactive Stage */}
            <div className="relative flex-grow flex items-center justify-center p-4 pt-32 pb-12 z-10 w-full h-screen">

                <motion.div
                    layoutId="demo-container"
                    className="relative w-full max-w-6xl aspect-[16/10] bg-[#0F1623] border border-white/10 rounded-2xl shadow-2xl overflow-hidden group transition-all duration-500 hover:shadow-indigo-500/10"
                >
                    {/* Image Container with "Crop" Effect via Object Position/Fit to hide OS UI if needed */}
                    {/* We assume images are cleaner now, but 'object-cover' + specific positioning can zoom into app area */}
                    <div className="relative w-full h-full bg-[#0B1220]">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeSceneId}
                                initial={{ opacity: 0, scale: 1.05 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.4 }}
                                className="relative w-full h-full"
                            >
                                <Image
                                    src={activeScene.image}
                                    alt="Dashboard Demo"
                                    fill
                                    className="object-cover object-center" // Zoom to cover, focusing on center (usually hides heavy browser chrome if properly ratioed)
                                    priority
                                    quality={100}
                                />

                                {/* Dark overlay that lightens on hover to focus user */}
                                <div className="absolute inset-0 bg-black/10 pointer-events-none" />
                            </motion.div>
                        </AnimatePresence>

                        {/* Hotspots Layer */}
                        {activeScene.hotspots.map((hotspot) => (
                            <div
                                key={hotspot.id}
                                className="absolute -translate-x-1/2 -translate-y-1/2 z-30 flex items-center justify-center"
                                style={{
                                    left: `${hotspot.x}%`,
                                    top: `${hotspot.y}%`,
                                }}
                            >
                                {/* Tooltip Popup */}
                                <AnimatePresence>
                                    {activeTooltip === hotspot.id && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10, scale: 0.9 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            exit={{ opacity: 0, y: 10, scale: 0.9 }}
                                            className="absolute bottom-full mb-4 w-72 md:w-96 bg-[#0F1623]/95 backdrop-blur-xl border border-indigo-500/30 p-5 rounded-xl shadow-[0_0_50px_rgba(0,0,0,0.6)] z-50 text-left pointer-events-auto"
                                        >
                                            <div className="flex items-center gap-3 mb-3 border-b border-white/10 pb-2">
                                                <div className="p-2 bg-indigo-500/10 rounded-lg">
                                                    {hotspot.icon ? <hotspot.icon className="w-5 h-5 text-indigo-400" /> : <Info className="w-5 h-5 text-indigo-400" />}
                                                </div>
                                                <h4 className="font-bold text-base text-white tracking-wide">
                                                    {t(`${hotspot.labelKey}.title`)}
                                                </h4>
                                            </div>

                                            <p className="text-sm text-white/80 leading-relaxed mb-4 font-light">
                                                {t(`${hotspot.labelKey}.desc`)}
                                            </p>

                                            {hotspot.targetScene && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setActiveSceneId(hotspot.targetScene!);
                                                        setActiveTooltip(null);
                                                    }}
                                                    className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 rounded-lg text-sm font-bold text-white transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 group/btn"
                                                >
                                                    {hotspot.labelKey === 'demo.ui.back' ? t("demo.ui.back") : t("demo.ui.clickToExplore")}
                                                    {hotspot.labelKey !== 'demo.ui.back' && <ChevronRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />}
                                                </button>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* Trigger Button */}
                                <button
                                    onClick={() => setActiveTooltip(activeTooltip === hotspot.id ? null : hotspot.id)}
                                    className="relative group/marker focus:outline-none"
                                >
                                    {(hotspot.pulse || !activeTooltip) && (
                                        <span className={`absolute inset-0 rounded-full animate-ping opacity-50 duration-1000 ${activeTooltip === hotspot.id ? 'bg-indigo-400' : 'bg-white'}`} />
                                    )}
                                    <div className={`relative w-8 h-8 md:w-12 md:h-12 rounded-full border-2 flex items-center justify-center shadow-[0_0_20px_rgba(0,0,0,0.3)] transition-all duration-300
                                        ${activeTooltip === hotspot.id
                                            ? 'bg-indigo-600 border-indigo-300 scale-110 rotate-0'
                                            : 'bg-black/40 border-white/30 backdrop-blur-sm hover:bg-indigo-500 hover:border-indigo-400 hover:scale-105'
                                        }`}
                                    >
                                        {activeTooltip === hotspot.id ? (
                                            <X className="w-5 h-5 text-white" />
                                        ) : (
                                            hotspot.icon ? <hotspot.icon className="w-4 h-4 md:w-6 md:h-6 text-white" /> : <Info className="w-4 h-4 md:w-6 md:h-6 text-white" />
                                        )}
                                    </div>
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Back Button (Floating) */}
                    <AnimatePresence>
                        {activeSceneId !== 'dashboard' && (
                            <motion.button
                                initial={{ x: -20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: -20, opacity: 0 }}
                                onClick={() => setActiveSceneId('dashboard')}
                                className="absolute top-6 left-6 z-40 bg-black/60 hover:bg-black/80 text-white px-5 py-2.5 rounded-full border border-white/10 backdrop-blur-lg flex items-center gap-2 text-sm font-medium transition-all group shadow-xl"
                            >
                                <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                                {t("demo.ui.back")}
                            </motion.button>
                        )}
                    </AnimatePresence>

                    {/* Footer Hint */}
                    <div className="absolute bottom-6 left-0 right-0 flex justify-center z-20 pointer-events-none">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0, transition: { delay: 1 } }}
                            className="bg-black/60 backdrop-blur text-white/50 text-xs px-4 py-2 rounded-full border border-white/5 flex items-center gap-2"
                        >
                            <Info className="w-3 h-3" />
                            {t("demo.ui.clickToExplore")}
                        </motion.div>
                    </div>

                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
