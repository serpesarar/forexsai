"use client";

import { lazy, Suspense } from "react";
import { TrendingUp, Layers, Globe2, CalendarDays, Waves } from "lucide-react";
import { LoadingIcon, SignalsIcon, AdvancedAnalysisIcon, EmelIcon } from "../ui/CustomIcons";
import AuthGuard from "../../components/AuthGuard";
import { LazyPanel } from "../../components/LazyPanel";
import { useI18nStore } from "../../lib/i18n/store";
import ErrorBoundary from "../ErrorBoundary";

const MTFMatrixPanel = lazy(() => import("../../components/panels/MTFMatrixPanel"));
const COTWhalePanel = lazy(() => import("../../components/panels/COTWhalePanel"));
const SeasonalityPanel = lazy(() => import("../../components/panels/SeasonalityPanel"));
const OrderBlockPanelUnified = lazy(() => import("../../components/OrderBlockPanelUnified"));
const WhaleTrackerPanel = lazy(() => import("../../components/WhaleTrackerPanel"));
const InstitutionalDataPanel = lazy(() => import("../../components/InstitutionalDataPanel"));
const AdvancedAnalysisPanel = lazy(() => import("../../components/AdvancedAnalysisPanel"));

const PanelLoader = () => (
    <div className="flex items-center justify-center rounded-xl border border-white/5 bg-white/[0.02] min-h-[200px]">
        <LoadingIcon size={24} className="animate-spin text-white/20" />
    </div>
);

export default function AnalysisView() {
    const { t } = useI18nStore();

    return (
        <div className="w-full text-white animate-in fade-in duration-300">
            <div className="max-w-[1600px] mx-auto p-3 md:p-6 space-y-6">
                {/* Page Header */}
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/30 to-orange-500/30">
                        <SignalsIcon size={20} className="text-amber-400" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold">Analysis</h1>
                        <p className="text-xs text-textSecondary">SMC, Multi-Timeframe, COT & Market Structure</p>
                    </div>
                </div>

                {/* MTF Matrix */}
                <LazyPanel fallbackHeight={300}>
                    <Suspense fallback={<PanelLoader />}>
                        <ErrorBoundary>
                            <MTFMatrixPanel />
                        </ErrorBoundary>
                    </Suspense>
                </LazyPanel>

                {/* 2-column: COT + Seasonality */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <ErrorBoundary>
                                <COTWhalePanel />
                            </ErrorBoundary>
                        </Suspense>
                    </LazyPanel>
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <ErrorBoundary>
                                <SeasonalityPanel />
                            </ErrorBoundary>
                        </Suspense>
                    </LazyPanel>
                </div>

                {/* Smart Money Zones - Unified Panel (4 Symbols) */}
                <LazyPanel fallbackHeight={400}>
                    <Suspense fallback={<PanelLoader />}>
                        <ErrorBoundary>
                            <OrderBlockPanelUnified />
                        </ErrorBoundary>
                    </Suspense>
                </LazyPanel>

                {/* Whale Tracker + Institutional */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <ErrorBoundary>
                                <WhaleTrackerPanel />
                            </ErrorBoundary>
                        </Suspense>
                    </LazyPanel>
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <ErrorBoundary>
                                <InstitutionalDataPanel />
                            </ErrorBoundary>
                        </Suspense>
                    </LazyPanel>
                </div>

                {/* Advanced Analysis - Unified Panel with Symbol Selector */}
                <div className="w-full">
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <ErrorBoundary>
                                <AdvancedAnalysisPanel />
                            </ErrorBoundary>
                        </Suspense>
                    </LazyPanel>
                </div>
            </div>
        </div>
    );
}
