"use client";

import { lazy, Suspense } from "react";
import { Loader2, BarChart3, TrendingUp, Layers, Globe2, CalendarDays, Waves } from "lucide-react";
import SharedNavHeader from "../../components/SharedNavHeader";
import Sidebar from "../../components/Sidebar";
import AuthGuard from "../../components/AuthGuard";
import { LazyPanel } from "../../components/LazyPanel";
import { useI18nStore } from "../../lib/i18n/store";

const SMCPanel = lazy(() => import("../../components/panels/SMCPanel"));
const MTFMatrixPanel = lazy(() => import("../../components/panels/MTFMatrixPanel"));
const COTWhalePanel = lazy(() => import("../../components/panels/COTWhalePanel"));
const SeasonalityPanel = lazy(() => import("../../components/panels/SeasonalityPanel"));
const OrderBlockPanelSimple = lazy(() => import("../../components/OrderBlockPanelSimple"));
const WhaleTrackerPanel = lazy(() => import("../../components/WhaleTrackerPanel"));
const InstitutionalDataPanel = lazy(() => import("../../components/InstitutionalDataPanel"));
const AdvancedAnalysisPanel = lazy(() => import("../../components/AdvancedAnalysisPanel"));

const PanelLoader = () => (
    <div className="flex items-center justify-center rounded-xl border border-white/5 bg-white/[0.02] min-h-[200px]">
        <Loader2 className="h-6 w-6 animate-spin text-white/20" />
    </div>
);

export default function AnalysisPage() {
    return (
        <AuthGuard>
            <AnalysisPageContent />
        </AuthGuard>
    );
}

function AnalysisPageContent() {
    const { t } = useI18nStore();

    return (
        <div className="min-h-screen bg-background text-white">
            <Sidebar />
            <div style={{ marginLeft: 72 }}>
                <SharedNavHeader activePage="analysis" />

                <main className="max-w-[1600px] mx-auto p-3 md:p-6 space-y-6">
                    {/* Page Header */}
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/30 to-orange-500/30">
                            <BarChart3 className="h-5 w-5 text-amber-400" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold">Analysis</h1>
                            <p className="text-xs text-textSecondary">SMC, Multi-Timeframe, COT & Market Structure</p>
                        </div>
                    </div>

                    {/* SMC Panel */}
                    <LazyPanel fallbackHeight={350}>
                        <Suspense fallback={<PanelLoader />}>
                            <SMCPanel />
                        </Suspense>
                    </LazyPanel>

                    {/* MTF Matrix */}
                    <LazyPanel fallbackHeight={300}>
                        <Suspense fallback={<PanelLoader />}>
                            <MTFMatrixPanel />
                        </Suspense>
                    </LazyPanel>

                    {/* 2-column: COT + Seasonality */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <COTWhalePanel />
                            </Suspense>
                        </LazyPanel>
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <SeasonalityPanel />
                            </Suspense>
                        </LazyPanel>
                    </div>

                    {/* Order Blocks */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <LazyPanel fallbackHeight={250}>
                            <Suspense fallback={<PanelLoader />}>
                                <OrderBlockPanelSimple symbol="NDX.INDX" symbolLabel="NASDAQ" />
                            </Suspense>
                        </LazyPanel>
                        <LazyPanel fallbackHeight={250}>
                            <Suspense fallback={<PanelLoader />}>
                                <OrderBlockPanelSimple symbol="XAUUSD" symbolLabel="XAUUSD" />
                            </Suspense>
                        </LazyPanel>
                    </div>

                    {/* Whale Tracker + Institutional */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <WhaleTrackerPanel />
                            </Suspense>
                        </LazyPanel>
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <InstitutionalDataPanel />
                            </Suspense>
                        </LazyPanel>
                    </div>

                    {/* Advanced Analysis per symbol */}
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <AdvancedAnalysisPanel symbol="NASDAQ" />
                            </Suspense>
                        </LazyPanel>
                        <LazyPanel fallbackHeight={300}>
                            <Suspense fallback={<PanelLoader />}>
                                <AdvancedAnalysisPanel symbol="XAUUSD" />
                            </Suspense>
                        </LazyPanel>
                    </div>
                </main>
            </div>
        </div>
    );
}
