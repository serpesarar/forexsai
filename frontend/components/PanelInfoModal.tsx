"use client";

import { useEffect, useCallback, useState } from "react";
import { X, Info, Lightbulb, BarChart3, BookOpen } from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";
import { PANEL_INFO_REGISTRY } from "../lib/panelInfoData";

interface PanelInfoModalProps {
    isOpen: boolean;
    onClose: () => void;
    panelId: string;
}

export function PanelInfoModal({ isOpen, onClose, panelId }: PanelInfoModalProps) {
    const { t } = useI18nStore();
    const [isAnimating, setIsAnimating] = useState(false);
    const [isVisible, setIsVisible] = useState(false);

    const panelInfo = PANEL_INFO_REGISTRY[panelId];

    // Handle open/close animations
    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            // Small delay to trigger CSS transition
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setIsAnimating(true);
                });
            });
        } else {
            setIsAnimating(false);
            const timer = setTimeout(() => setIsVisible(false), 300);
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    // Close on ESC key
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        },
        [onClose]
    );

    useEffect(() => {
        if (isOpen) {
            document.addEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "hidden";
        }
        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "";
        };
    }, [isOpen, handleKeyDown]);

    if (!isVisible || !panelInfo) return null;

    const title = t(panelInfo.titleKey);
    const description = t(panelInfo.descriptionKey);
    const usage = t(panelInfo.usageKey);
    const tips = t(panelInfo.tipsKey);
    const dataPoints = t(panelInfo.dataPointsKey);

    const importanceColors: Record<string, string> = {
        critical: "bg-red-500/20 text-red-400 border-red-500/30",
        high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
        medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
        low: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    };

    const importanceLabels: Record<string, string> = {
        critical: t("panelInfo.importance.critical"),
        high: t("panelInfo.importance.high"),
        medium: t("panelInfo.importance.medium"),
        low: t("panelInfo.importance.low"),
    };

    return (
        <div
            className={`fixed inset-0 z-[100] flex items-center justify-center p-4 transition-all duration-300 ${isAnimating ? "opacity-100" : "opacity-0"
                }`}
            onClick={onClose}
        >
            {/* Backdrop with blur */}
            <div
                className={`absolute inset-0 transition-all duration-300 ${isAnimating
                        ? "bg-black/60 backdrop-blur-md"
                        : "bg-black/0 backdrop-blur-none"
                    }`}
            />

            {/* Modal - Slide up animation */}
            <div
                className={`relative w-full max-w-lg max-h-[85vh] overflow-hidden rounded-2xl border border-white/10 shadow-2xl transition-all duration-300 ease-out
          bg-gradient-to-b from-gray-900/98 via-gray-900/95 to-gray-950/98 backdrop-blur-xl
          ${isAnimating ? "translate-y-0 scale-100" : "translate-y-8 scale-95"}
        `}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Top accent line */}
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent to-transparent" />

                {/* Header */}
                <div className="bg-gradient-to-r from-accent/10 via-transparent to-accent/5 px-6 py-5 border-b border-white/10">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                            <span className="text-2xl flex-shrink-0">{panelInfo.icon}</span>
                            <div className="min-w-0">
                                <h3 className="text-lg font-bold text-white truncate">{title}</h3>
                                <span
                                    className={`inline-block text-[10px] px-2 py-0.5 rounded border mt-1 font-semibold tracking-wider uppercase ${importanceColors[panelInfo.importance]
                                        }`}
                                >
                                    {importanceLabels[panelInfo.importance]}
                                </span>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors flex-shrink-0 ml-2"
                        >
                            <X className="w-5 h-5 text-gray-400" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[60vh] space-y-5 custom-scrollbar">
                    {/* Description */}
                    <div className="group">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-blue-500/15">
                                <BookOpen className="w-4 h-4 text-blue-400" />
                            </div>
                            <h4 className="text-sm font-bold text-white tracking-wide">
                                {t("panelInfo.sections.description")}
                            </h4>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed pl-9">
                            {description}
                        </p>
                    </div>

                    {/* Data Points */}
                    <div className="group">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-accent/15">
                                <BarChart3 className="w-4 h-4 text-accent" />
                            </div>
                            <h4 className="text-sm font-bold text-white tracking-wide">
                                {t("panelInfo.sections.dataPoints")}
                            </h4>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed pl-9">
                            {dataPoints}
                        </p>
                    </div>

                    {/* Usage */}
                    <div className="group">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-emerald-500/15">
                                <Info className="w-4 h-4 text-emerald-400" />
                            </div>
                            <h4 className="text-sm font-bold text-white tracking-wide">
                                {t("panelInfo.sections.usage")}
                            </h4>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed pl-9">{usage}</p>
                    </div>

                    {/* Tips */}
                    <div className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 rounded-xl p-4 border border-amber-500/15">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="p-1.5 rounded-lg bg-amber-500/15">
                                <Lightbulb className="w-4 h-4 text-amber-400" />
                            </div>
                            <h4 className="text-sm font-bold text-amber-300 tracking-wide">
                                {t("panelInfo.sections.tips")}
                            </h4>
                        </div>
                        <p className="text-sm text-amber-200/80 leading-relaxed pl-9">
                            {tips}
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="bg-gray-800/50 px-6 py-3 border-t border-white/5">
                    <p className="text-[11px] text-gray-500 text-center">
                        {t("panelInfo.closeHint")}
                    </p>
                </div>
            </div>
        </div>
    );
}

export default PanelInfoModal;
