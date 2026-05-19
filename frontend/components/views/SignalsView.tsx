"use client";

import { lazy, Suspense } from "react";
import { LoadingIcon, PulseIcon } from "../ui/CustomIcons";
import { LazyPanel } from "../../components/LazyPanel";

// Signals page: analytics-only.
// Per user request 2026-05-19, the per-model live panels (EMEL, EmelInverse,
// Pulse, PulseV3, PulseML) were removed — they belong on the dashboard /
// symbol pages where models are evaluated live. This page is now the
// "Detailed Signals" analytics hub: meta consensus + strategy performance +
// learning dashboard.
const MetaSignalAnalysisPanel = lazy(() => import("../../components/panels/MetaSignalAnalysisPanel"));
const StrategyPerformancePanel = lazy(() => import("../../components/StrategyPerformancePanel"));
const LearningDashboardV2 = lazy(() => import("../../components/panels/LearningDashboardV2"));

const PanelLoader = () => (
    <div className="flex items-center justify-center rounded-xl border border-white/5 bg-white/[0.02] min-h-[200px]">
        <LoadingIcon size={24} className="animate-spin text-white/20" />
    </div>
);

export default function SignalsView() {
    return (
        <div className="w-full text-white animate-in fade-in duration-300">
            <div className="max-w-[1600px] mx-auto p-3 md:p-6 space-y-6">
                {/* Page Header */}
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-red-500/30 to-rose-500/30">
                        <PulseIcon size={20} className="text-red-400" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold">Detailed Signals</h1>
                        <p className="text-xs text-textSecondary">
                            Meta consensus, strategy performance & signal lifecycle analytics
                        </p>
                    </div>
                </div>

                {/* Meta Signal Analysis */}
                <LazyPanel fallbackHeight={380} rootMargin="0px">
                    <Suspense fallback={<PanelLoader />}>
                        <MetaSignalAnalysisPanel />
                    </Suspense>
                </LazyPanel>

                {/* Strategy Performance */}
                <LazyPanel fallbackHeight={350} rootMargin="0px">
                    <Suspense fallback={<PanelLoader />}>
                        <StrategyPerformancePanel />
                    </Suspense>
                </LazyPanel>

                {/* Learning Dashboard / Signal Performance */}
                <LazyPanel fallbackHeight={400} rootMargin="0px">
                    <Suspense fallback={<PanelLoader />}>
                        <LearningDashboardV2 />
                    </Suspense>
                </LazyPanel>
            </div>
        </div>
    );
}
