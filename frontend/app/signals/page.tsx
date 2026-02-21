"use client";

import { lazy, Suspense } from "react";
import { Loader2, Activity, Zap } from "lucide-react";
import SharedNavHeader from "../../components/SharedNavHeader";
import Sidebar from "../../components/Sidebar";
import AuthGuard from "../../components/AuthGuard";
import { LazyPanel } from "../../components/LazyPanel";
import { useI18nStore } from "../../lib/i18n/store";

const EmelPanel = lazy(() => import("../../components/panels/EmelPanel"));
const PulsePanel = lazy(() => import("../../components/panels/PulsePanel"));
const PulseV3Panel = lazy(() => import("../../components/panels/PulseV3Panel"));
const PulseMLPanel = lazy(() => import("../../components/panels/PulseMLPanel"));
const StrategyPerformancePanel = lazy(() => import("../../components/StrategyPerformancePanel"));
const LearningDashboardV2 = lazy(() => import("../../components/panels/LearningDashboardV2"));

const PanelLoader = () => (
    <div className="flex items-center justify-center rounded-xl border border-white/5 bg-white/[0.02] min-h-[200px]">
        <Loader2 className="h-6 w-6 animate-spin text-white/20" />
    </div>
);

export default function SignalsPage() {
    return (
        <AuthGuard>
            <SignalsPageContent />
        </AuthGuard>
    );
}

function SignalsPageContent() {
    const { t } = useI18nStore();

    return (
        <div className="min-h-screen bg-background text-white">
            <Sidebar />
            <div style={{ marginLeft: 72 }}>
                <SharedNavHeader activePage="signals" />

                <main className="max-w-[1600px] mx-auto p-3 md:p-6 space-y-6">
                    {/* Page Header */}
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-red-500/30 to-rose-500/30">
                            <Activity className="h-5 w-5 text-red-400" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold">Detailed Signals</h1>
                            <p className="text-xs text-textSecondary">Pulse, EMEL, ML Signals & Strategy Performance</p>
                        </div>
                    </div>

                    {/* EMEL Panel */}
                    <LazyPanel fallbackHeight={350}>
                        <Suspense fallback={<PanelLoader />}>
                            <EmelPanel />
                        </Suspense>
                    </LazyPanel>

                    {/* Pulse Panels - 2 column */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <PulsePanel />
                            </Suspense>
                        </LazyPanel>
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <PulseV3Panel />
                            </Suspense>
                        </LazyPanel>
                    </div>

                    {/* Pulse ML */}
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <PulseMLPanel />
                        </Suspense>
                    </LazyPanel>

                    {/* Strategy Performance */}
                    <LazyPanel fallbackHeight={350}>
                        <Suspense fallback={<PanelLoader />}>
                            <StrategyPerformancePanel />
                        </Suspense>
                    </LazyPanel>

                    {/* Learning Dashboard */}
                    <LazyPanel fallbackHeight={400}>
                        <Suspense fallback={<PanelLoader />}>
                            <LearningDashboardV2 />
                        </Suspense>
                    </LazyPanel>
                </main>
            </div>
        </div>
    );
}
