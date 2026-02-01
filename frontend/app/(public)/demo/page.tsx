"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { Info, X, ChevronRight, Maximize2, Sparkles, Calendar, Activity, TrendingUp, Brain, ArrowLeft, Monitor } from "lucide-react";
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
    scale?: number; // Custom zoom level per scene
    yOffset?: number; // Custom vertical offset to center content
};

export default function DemoPage() {
    const { t } = useI18n();
    const [activeSceneId, setActiveSceneId] = useState<SceneId>("dashboard");
    const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

    // Scenes with aggressively cropped settings to hide OS UI
    const scenes: Record<SceneId, Scene> = {
        dashboard: {
            id: "dashboard",
            image: "/demo-assets/dashboard-refined.png", // Using the newest, likely better/cleaner shot
            scale: 1.35, // Zoom in to hide browser bar & dock
            yOffset: 0,
            hotspots: [
                { id: "trend", x: 28, y: 45, labelKey: "demo.tour.dashboard", icon: TrendingUp },
                { id: "patterns", x: 50, y: 45, labelKey: "demo.tour.patterns", icon: Maximize2, targetScene: "pattern_detail", pulse: true },
                { id: "sentiment", x: 72, y: 45, labelKey: "demo.tour.sentiment", icon: Brain, targetScene: "sentiment" },
                { id: "ml", x: 88, y: 30, labelKey: "demo.tour.ml", icon: Sparkles, targetScene: "ml_panel" },
                { id: "rhythm", x: 85, y: 80, labelKey: "demo.tour.rhythm", icon: Activity, targetScene: "rhythm" }
            ]
        },
        pattern_detail: {
            id: "pattern_detail",
            image: "/demo-assets/pattern-popup.png",
            scale: 1.4,
            yOffset: -5,
            hotspots: [
                { id: "popup_info", x: 50, y: 50, labelKey: "demo.tour.popup", icon: Info },
                { id: "back_dash_1", x: 92, y: 8, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        ml_panel: {
            id: "ml_panel",
            image: "/demo-assets/ml-panel.png",
            scale: 1.35,
            yOffset: 0,
            hotspots: [
                { id: "ml_info", x: 30, y: 40, labelKey: "demo.tour.ml", icon: Sparkles },
                { id: "back_dash_2", x: 92, y: 8, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        sentiment: {
            id: "sentiment",
            image: "/demo-assets/sentiment-analysis.png",
            scale: 1.35,
            yOffset: 0,
            hotspots: [
                { id: "sent_info", x: 70, y: 40, labelKey: "demo.tour.sentiment", icon: Brain },
                { id: "back_dash_3", x: 92, y: 8, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        rhythm: {
            id: "rhythm",
            image: "/demo-assets/rhythm-detector.png",
            scale: 1.35,
            yOffset: 0,
            hotspots: [
                { id: "rhythm_info", x: 50, y: 50, labelKey: "demo.tour.rhythm", icon: Activity },
                { id: "back_dash_4", x: 92, y: 8, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        }
    };

    const activeScene = scenes[activeSceneId];

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans flex flex-col overflow-hidden">
            <TopNav />
            <AnimatedBackground />

            {/* Header / Mode Indicator */}
            <div className="absolute top-24 left-0 right-0 z-20 flex justify-center pointer-events-none">
                <motion.div
                    key={activeSceneId}
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[#0F1623]/80 backdrop-blur-md border border-white/10 px-6 py-2 rounded-full flex items-center gap-3 shadow-2xl"
                >
                    <div className={`w-2 h-2 rounded-full ${activeSceneId === 'dashboard' ? 'bg-emerald-500' : 'bg-indigo-500'} animate-pulse`} />
                    <span className="text-sm font-medium text-white tracking-wide">
                        {activeSceneId === 'dashboard' ? "Interactive Demo" : t(`demo.tour.${activeSceneId === 'pattern_detail' ? 'patterns' : activeSceneId === 'ml_panel' ? 'ml' : activeSceneId}.title`)}
                    </span>
                </motion.div>
            </div>

            {/* Main Interactive Stage */}
            <div className="relative flex-grow flex items-center justify-center p-4 pt-32 pb-12 z-10 w-full h-screen">

                <motion.div
                    layoutId="demo-container"
                    className="relative w-full max-w-6xl aspect-[16/10] bg-[#000000] border-4 border-[#1F2937] rounded-xl shadow-[0_0_100px_rgba(79,70,229,0.15)] overflow-hidden group"
                >
                    {/* Image Container with "Smart Crop" */}
                    <div className="relative w-full h-full overflow-hidden">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeSceneId}
                                initial={{ opacity: 0, scale: 1.1 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.5, ease: "circOut" }}
                                className="relative w-full h-full"
                            >
                                {/* The actual image, scaled up to push OS chrome out of view */}
                                <div
                                    className="w-full h-full relative"
                                    style={{
                                        transform: `scale(${activeScene.scale || 1}) translateY(${activeScene.yOffset || 0}%)`,
                                        transformOrigin: "center center",
                                        transition: "transform 0.5s ease-out"
                                    }}
                                >
                                    <Image
                                        src={activeScene.image}
                                        alt="Dashboard Demo"
                                        fill
                                        className="object-contain" // Changed from cover to contain BUT zooming via parent div
                                        priority
                                        quality={100}
                                    />
                                </div>

                                {/* Overlay Gradient for Depth */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/10 pointer-events-none" />
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
                                            initial={{ opacity: 0, y: 15, scale: 0.95 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                            className="absolute bottom-full mb-6 w-80 md:w-96 bg-[#111827]/95 backdrop-blur-2xl border border-indigo-500/40 p-6 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 text-left pointer-events-auto"
                                        >
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400">
                                                    {hotspot.icon ? <hotspot.icon className="w-5 h-5" /> : <Info className="w-5 h-5" />}
                                                </div>
                                                <h4 className="font-bold text-lg text-white tracking-tight">
                                                    {t(`${hotspot.labelKey}.title`)}
                                                </h4>
                                            </div>

                                            <p className="text-sm text-gray-300 leading-relaxed mb-5 font-normal">
                                                {t(`${hotspot.labelKey}.desc`)}
                                            </p>

                                            {hotspot.targetScene && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setActiveSceneId(hotspot.targetScene!);
                                                        setActiveTooltip(null);
                                                    }}
                                                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm font-semibold text-white transition-all shadow-lg hover:shadow-indigo-500/25 flex items-center justify-center gap-2"
                                                >
                                                    {hotspot.labelKey === 'demo.ui.back' ? t("demo.ui.back") : t("demo.ui.clickToExplore")}
                                                    {hotspot.labelKey !== 'demo.ui.back' && <ChevronRight className="w-4 h-4" />}
                                                </button>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* Trigger Button */}
                                <button
                                    onClick={() => setActiveTooltip(activeTooltip === hotspot.id ? null : hotspot.id)}
                                    className="relative group/btn focus:outline-none"
                                >
                                    {(hotspot.pulse || (!activeTooltip && activeSceneId === 'dashboard')) && (
                                        <span className={`absolute inset-0 rounded-full animate-ping opacity-75 duration-1000 ${activeTooltip === hotspot.id ? 'bg-indigo-500' : 'bg-white'}`} />
                                    )}
                                    <div className={`relative w-8 h-8 md:w-10 md:h-10 rounded-full border-2 flex items-center justify-center shadow-lg transition-all duration-300
                                        ${activeTooltip === hotspot.id
                                            ? 'bg-indigo-600 border-white scale-110'
                                            : 'bg-black/50 border-white/50 hover:bg-indigo-600 hover:border-indigo-400 hover:scale-110'
                                        }`}
                                    >
                                        {activeTooltip === hotspot.id ? <X className="w-5 h-5 text-white" /> : <div className="w-3 h-3 rounded-full bg-white" />}
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
                                className="absolute top-6 left-6 z-40 bg-black/60 hover:bg-black/80 text-white px-4 py-2 rounded-lg border border-white/10 backdrop-blur-lg flex items-center gap-2 text-sm font-medium transition-all group"
                            >
                                <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                                {t("demo.ui.back")}
                            </motion.button>
                        )}
                    </AnimatePresence>

                    {/* Hint / Footer */}
                    <div className="absolute bottom-4 left-0 right-0 flex justify-center z-20 pointer-events-none">
                        <div className="bg-black/40 backdrop-blur-md text-white/40 text-[10px] uppercase font-bold tracking-widest px-3 py-1.5 rounded-full border border-white/5">
                            {t("demo.ui.clickToExplore")}
                        </div>
                    </div>

                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
