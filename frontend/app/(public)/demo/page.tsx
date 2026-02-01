"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { Info, X, ChevronRight, Maximize2, Sparkles, Calendar, Activity, TrendingUp, Brain } from "lucide-react";
import Image from "next/image";

// Hotspot Type Definition
type Hotspot = {
    id: string;
    x: number; // Percentage
    y: number; // Percentage
    width?: number; // vh/vw or px for click area
    height?: number;
    labelKey: string;
    icon?: any;
    targetScene?: string; // If clicking navigates to another view
};

// Scene Definition
type Scene = {
    id: string;
    image: string;
    hotspots: Hotspot[];
};

export default function DemoPage() {
    const { t } = useI18n();
    const [activeSceneId, setActiveSceneId] = useState("dashboard");
    const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

    // Define Scenes based on uploaded screenshots
    const scenes: Record<string, Scene> = {
        dashboard: {
            id: "dashboard",
            image: "/demo-assets/dashboard-main.png",
            hotspots: [
                { id: "trend", x: 28, y: 45, labelKey: "demo.tour.trend", icon: TrendingUp },
                { id: "patterns", x: 50, y: 45, labelKey: "demo.tour.patterns", icon: Maximize2, targetScene: "pattern_detail" },
                { id: "sentiment", x: 72, y: 45, labelKey: "demo.tour.sentiment", icon: Brain },
                { id: "earnings", x: 88, y: 30, labelKey: "demo.tour.earnings", icon: Calendar },
                { id: "ml", x: 85, y: 20, labelKey: "demo.tour.ml", icon: Sparkles, targetScene: "ml_panel" },
                { id: "rhythm", x: 15, y: 70, labelKey: "demo.tour.rhythm", icon: Activity } // Hypothetical position, adjust based on real image
            ]
        },
        pattern_detail: {
            id: "pattern_detail",
            image: "/demo-assets/pattern-popup.png",
            hotspots: [
                { id: "popup_info", x: 50, y: 50, labelKey: "demo.tour.popup", icon: Info },
                { id: "close_popup", x: 64, y: 24, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" }
            ]
        },
        ml_panel: {
            id: "ml_panel",
            image: "/demo-assets/ml-panel.png",
            hotspots: [
                { id: "ml_model", x: 30, y: 50, labelKey: "demo.tour.ml", icon: Sparkles }, // Left panel
                { id: "back_to_dash", x: 95, y: 5, labelKey: "demo.ui.back", icon: X, targetScene: "dashboard" } // Hypothetical close/back area
            ]
        }
    };

    const activeScene = scenes[activeSceneId];

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans flex flex-col overflow-hidden">
            <TopNav />
            <AnimatedBackground />

            {/* Main Content Area */}
            <div className="relative flex-grow flex items-center justify-center p-4 pt-24 pb-8 z-10 w-full h-[calc(100vh-80px)]">

                {/* Intro / Header Overlay (Fades out when interacting?) or kept minimal */}
                <div className="absolute top-24 left-1/2 -translate-x-1/2 z-20 pointer-events-none text-center">
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-black/40 backdrop-blur-md border border-white/10 px-6 py-2 rounded-full inline-flex items-center gap-2"
                    >
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-sm font-medium text-white/90">{t("demo.subtitle")}</span>
                    </motion.div>
                </div>

                {/* Interactive Image Container */}
                <motion.div
                    key={activeSceneId}
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4 }}
                    className="relative w-full max-w-[90vw] h-[85vh] bg-[#0F1623] border border-white/10 rounded-xl shadow-2xl overflow-hidden group"
                >
                    {/* The Screenshot */}
                    <div className="relative w-full h-full">
                        <Image
                            src={activeScene.image}
                            alt="Dashboard Demo"
                            fill
                            className="object-contain"
                            priority
                        />

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
                                            className="absolute bottom-full mb-4 w-72 bg-[#131B2D]/95 backdrop-blur-xl border border-indigo-500/30 p-4 rounded-xl shadow-[0_0_30px_rgba(0,0,0,0.5)] z-50 text-left pointer-events-auto"
                                        >
                                            <div className="flex items-center gap-2 mb-2 text-indigo-400">
                                                {hotspot.icon && <hotspot.icon className="w-4 h-4" />}
                                                <h4 className="font-bold text-sm tracking-wide">
                                                    {t(`${hotspot.labelKey}.title`)}
                                                </h4>
                                            </div>
                                            <p className="text-xs text-white/70 leading-relaxed mb-3">
                                                {t(`${hotspot.labelKey}.desc`)}
                                            </p>
                                            {hotspot.targetScene && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setActiveSceneId(hotspot.targetScene!);
                                                        setActiveTooltip(null);
                                                    }}
                                                    className="w-full py-1.5 bg-indigo-500 hover:bg-indigo-600 rounded text-xs font-bold text-white transition-colors flex items-center justify-center gap-1"
                                                >
                                                    {hotspot.labelKey === 'demo.ui.back' ? t("demo.ui.back") : t("demo.ui.clickToExplore")}
                                                    {hotspot.labelKey !== 'demo.ui.back' && <ChevronRight className="w-3 h-3" />}
                                                </button>
                                            )}
                                        </motion.div>
                                    )}
                                </AnimatePresence>

                                {/* Trigger Button (Pulse) */}
                                <button
                                    onClick={() => setActiveTooltip(activeTooltip === hotspot.id ? null : hotspot.id)}
                                    className="relative group/marker"
                                >
                                    <span className={`absolute inset-0 rounded-full animate-ping opacity-75 ${activeTooltip === hotspot.id ? 'bg-indigo-400' : 'bg-white'}`} />
                                    <div className={`relative w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-lg transition-all
                                        ${activeTooltip === hotspot.id
                                            ? 'bg-indigo-500 border-indigo-300 scale-110'
                                            : 'bg-black/40 border-white/50 hover:bg-indigo-500 hover:border-indigo-400'
                                        }`}
                                    >
                                        {hotspot.icon ? <hotspot.icon className="w-4 h-4 text-white" /> : <Info className="w-4 h-4 text-white" />}
                                    </div>
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Navigation Hints / Footer inside the container */}
                    <div className="absolute bottom-6 left-0 right-0 flex justify-center z-20 pointer-events-none">
                        <div className="bg-black/60 backdrop-blur text-white/50 text-xs px-4 py-2 rounded-full border border-white/5">
                            {t("demo.ui.clickToExplore")}
                        </div>
                    </div>

                    {/* Back Button (If not main dashboard) */}
                    {activeSceneId !== 'dashboard' && (
                        <button
                            onClick={() => setActiveSceneId('dashboard')}
                            className="absolute top-6 left-6 z-40 bg-black/50 hover:bg-black/80 text-white px-4 py-2 rounded-lg border border-white/10 backdrop-blur flex items-center gap-2 text-sm font-medium transition-colors"
                        >
                            <X className="w-4 h-4" />
                            {t("demo.ui.back")}
                        </button>
                    )}

                </motion.div>
            </div>

        </main>
    );
}
