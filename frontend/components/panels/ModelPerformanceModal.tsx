"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
const API_BASE = "https://upbeat-flow-production.up.railway.app";
import { motion, AnimatePresence } from "framer-motion";
import {
    CloseIcon as X,
    ClockIcon as Clock,
    ArrowUpIcon as TrendingUp,
    ActivityIcon as Activity,
    TargetIcon as Target,
    ChartsIcon as BarChart2,
    CheckCircleIcon as CheckCircle2,
    CloseIcon as XCircle,
    AlertIcon as AlertCircle
} from "../ui/CustomIcons";

import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Legend
} from "recharts";

interface Signal {
    id: string;
    date: string;
    symbol: string;
    prediction: "buy" | "sell" | "hold";
    actual: "up" | "down" | "flat";
    accuracy: number;
    profit: number;
    result: "win" | "loss" | "pending";
}

interface ModelPerformance {
    modelId: string;
    modelName: string;
    accuracy: number;
    totalSignals: number;
    timeSeriesData: {
        date: string;
        prediction: "buy" | "sell" | "hold";
        actual: "up" | "down" | "flat";
        accuracy: number;
        profit: number;
        equity: number;
    }[];
    hourlyPerformance: {
        hour: number;
        day: string;
        accuracy: number;
        sampleSize: number;
    }[];
    comparisonMetrics: {
        accuracy: number;
        speed: number;
        profit: number;
        riskControl: number;
        trendFollowing: number;
    };
    recentSignals: Signal[];
}

interface ModelPerformanceModalProps {
    isOpen: boolean;
    onClose: () => void;
    symbol: string;
    model?: string;
}

// ── Compute real Sharpe & Drawdown from equity curve data ──
function computeAdvancedStats(timeSeriesData: ModelPerformance["timeSeriesData"] | undefined) {
    if (!timeSeriesData || timeSeriesData.length < 2) {
        return { sharpe: null, maxDrawdown: null };
    }
    // Daily returns from equity
    const returns: number[] = [];
    for (let i = 1; i < timeSeriesData.length; i++) {
        const prev = timeSeriesData[i - 1].equity;
        const curr = timeSeriesData[i].equity;
        if (prev > 0) returns.push((curr - prev) / prev);
    }
    // Sharpe ratio (annualized, assuming daily data)
    let sharpe: number | null = null;
    if (returns.length >= 2) {
        const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
        const variance = returns.reduce((a, r) => a + (r - mean) ** 2, 0) / (returns.length - 1);
        const stdDev = Math.sqrt(variance);
        sharpe = stdDev > 0 ? (mean / stdDev) * Math.sqrt(252) : null;
    }
    // Max drawdown from equity curve
    let maxDrawdown: number | null = null;
    let peak = timeSeriesData[0].equity;
    let maxDD = 0;
    for (const d of timeSeriesData) {
        if (d.equity > peak) peak = d.equity;
        const dd = peak > 0 ? (peak - d.equity) / peak : 0;
        if (dd > maxDD) maxDD = dd;
    }
    maxDrawdown = maxDD * 100; // percentage
    return { sharpe, maxDrawdown };
}

export const ModelPerformanceModal: React.FC<ModelPerformanceModalProps> = ({
    isOpen,
    onClose,
    symbol,
    model,
}) => {
    // Detect language from localStorage or browser (no LanguageContext in this project)
    const lang = typeof window !== "undefined"
        ? (localStorage.getItem("language") || navigator.language?.startsWith("tr") ? "tr" : "en")
        : "en";

    // Symbol display names
    const SYM_DISPLAY: Record<string, string> = {
        "NDX.INDX": "NASDAQ", "GDAXI.INDX": "DAX",
        "USOIL.FOREX": "US OIL", "CL.F": "US OIL",
        "CL.COMM": "US OIL",
    };
    const symbolDisplay = SYM_DISPLAY[symbol] || symbol;

    const MODEL_DISPLAY: Record<string, string> = {
        ml: "ML Model", emel: "EMEL 9-Check AI",
        pulse1: "Pulse 1 — Algo", pulse2: "Pulse 2 — ML Hybrid",
        pulse3: "Pulse 3 — Scalp",
    };
    const modelDisplay = model ? (MODEL_DISPLAY[model] || model) : "All Models";

    const translations: Record<string, Record<string, string>> = {
        en: {
            active: "Active",
            accuracy: "Accuracy",
            totalSignals: "Total Signals",
            success: "Success Rate",
            avgReturn: "Avg Return",
            sharpe: "Sharpe Ratio",
            maxDrawdown: "Max Drawdown",
            performance: "Performance",
            session: "Session",
            comparison: "Comparison",
            equityCurve: "Equity Curve",
            accuracyChart: "Accuracy",
            speed: "Speed",
            profit: "Profit",
            riskControl: "Risk Control",
            trendFollowing: "Trend Following",
            recentSignals: "Recent Signals",
            date: "Date",
            symbolCol: "Symbol",
            signal: "Signal",
            result: "Result",
            returnCol: "Return",
            win: "Win",
            loss: "Loss",
            noData: "No recent signals found for this instrument.",
            sessionPlaceholder: "Session analysis heatmap is being prepared from historical data.",
            sessionTitle: "Session Analysis Heatmap",
        },
        tr: {
            active: "Aktif",
            accuracy: "Doğruluk",
            totalSignals: "Toplam Sinyal",
            success: "Başarı Oranı",
            avgReturn: "Ort. Getiri",
            sharpe: "Sharpe Oranı",
            maxDrawdown: "Maks. Düşüş",
            performance: "Performans",
            session: "Seans",
            comparison: "Karşılaştırma",
            equityCurve: "Bakiye Eğrisi",
            accuracyChart: "Doğruluk",
            speed: "Hız",
            profit: "Kâr",
            riskControl: "Risk Kontrolü",
            trendFollowing: "Trend Takibi",
            recentSignals: "Son Sinyaller",
            date: "Tarih",
            symbolCol: "Sembol",
            signal: "Sinyal",
            result: "Sonuç",
            returnCol: "Getiri",
            win: "Kazanç",
            loss: "Kayıp",
            noData: "Bu enstrüman için sinyal bulunamadı.",
            sessionPlaceholder: "Seans analiz haritası geçmiş verilerden hazırlanıyor.",
            sessionTitle: "Seans Analiz Haritası",
        },
    };
    const tr = translations[lang] || translations.en;
    const t = (key: string) => tr[key] || key;
    const [activeTab, setActiveTab] = useState<"performance" | "session" | "comparison">("performance");

    const { data: rawData, isLoading, isError } = useQuery({
        queryKey: ["historical-signals", symbol, model],
        queryFn: async () => {
            const params = new URLSearchParams({ symbol });
            if (model) params.append("model", model);
            const response = await fetch(`${API_BASE}/api/learning/historical-signals?${params.toString()}`);
            if (!response.ok) throw new Error("Failed to fetch historical signals");
            return response.json();
        },
        enabled: isOpen && !!symbol,
    });

    const data = rawData as ModelPerformance | undefined;

    if (!isOpen) return null;

    // Custom tooltips
    const CustomPerformanceTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-[#141C2B] border border-white/10 p-3 rounded-lg shadow-2xl">
                    <p className="text-[#9AA4B2] text-xs mb-2 font-medium">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 mb-1">
                            <div
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-[#E6EDF3] text-sm font-medium">
                                {entry.name}:{" "}
                                {entry.name.includes("Equity") || entry.name.includes("Bakiye")
                                    ? `$${entry.value.toFixed(2)}`
                                    : `${entry.value.toFixed(1)}%`}
                            </span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                {/* Backdrop */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/60 backdrop-blur-md"
                />

                {/* Modal Content */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className="relative w-full max-w-6xl max-h-[90vh] bg-[#0B0F17] rounded-2xl border border-white/10 shadow-2xl overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-white/5 bg-[#141C2B]">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                <Activity className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-[#E6EDF3] tracking-tight">
                                    {data?.modelName || `${modelDisplay} — ${symbolDisplay} Predictor`}
                                </h2>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                        {t("modelPerformance.summary.active")}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-[#6B7280] hover:text-[#E6EDF3] hover:bg-white/5 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5" style={{ width: 20, height: 20 }} />
                        </button>
                    </div>

                    <div className="p-6 overflow-y-auto custom-scrollbar flex-1 relative">
                        {/* Loading Overlay */}
                        {isLoading && (
                            <div className="absolute inset-0 bg-[#0B0F17]/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center">
                                <div className="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4" />
                                <p className="text-[#9AA4B2] font-medium">Loading historical performance...</p>
                            </div>
                        )}

                        {/* Error Overlay */}
                        {isError && (
                            <div className="absolute inset-0 bg-[#0B0F17]/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center">
                                <AlertCircle className="w-10 h-10 text-rose-500 mb-4" />
                                <p className="text-rose-400 font-medium">Failed to load data. Please try again later.</p>
                            </div>
                        )}

                        {data && (
                            <>
                                {/* Top Grid */}
                                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
                                    {/* Main KPI */}
                                    <div className="lg:col-span-1 bg-[#141C2B] rounded-xl p-6 border border-white/5 flex flex-col justify-center items-center relative overflow-hidden group">
                                        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                        <div className="relative z-10 text-center">
                                            <div className="text-[#6B7280] text-xs font-medium tracking-wider uppercase mb-2">
                                                {t("accuracy")}
                                            </div>
                                            <div className="text-5xl font-bold text-[#E6EDF3] tracking-tighter mb-2 drop-shadow-[0_0_15px_rgba(56,189,248,0.3)]">
                                                {data?.accuracy || 0}%
                                            </div>
                                            <div className="text-sm font-medium text-[#9AA4B2]">
                                                {data?.totalSignals || 0} {t("totalSignals")}
                                            </div>
                                        </div>
                                        {/* Circular Progress Ring Background (CSS pure) */}
                                        <svg className="absolute w-32 h-32 -rotate-90 pointer-events-none opacity-20">
                                            <circle
                                                cx="64"
                                                cy="64"
                                                r="60"
                                                stroke="currentColor"
                                                strokeWidth="4"
                                                fill="none"
                                                className="text-white/10"
                                            />
                                            <circle
                                                cx="64"
                                                cy="64"
                                                r="60"
                                                stroke="currentColor"
                                                strokeWidth="4"
                                                fill="none"
                                                strokeDasharray={377}
                                                strokeDashoffset={377 - (377 * (data?.accuracy || 0)) / 100}
                                                className="text-blue-400"
                                            />
                                        </svg>
                                    </div>

                                    {/* Quick Stats — computed from real data */}
                                    {(() => {
                                        const advanced = computeAdvancedStats(data?.timeSeriesData);
                                        const statsItems = [
                                            {
                                                label: t("success"),
                                                value: `${Math.round(((data?.totalSignals || 0) * (data?.accuracy || 0)) / 100)}/${data?.totalSignals || 0}`,
                                                trend: "Current",
                                                color: "emerald",
                                                iconColor: "#10B981",
                                                iconBg: "rgba(16,185,129,0.1)",
                                            },
                                            {
                                                label: t("avgReturn"),
                                                value: data?.comparisonMetrics?.profit ? `+${data.comparisonMetrics.profit}%` : "—",
                                                trend: "Avg",
                                                color: "blue",
                                                iconColor: "#4F8CFF",
                                                iconBg: "rgba(79,140,255,0.1)",
                                            },
                                            {
                                                label: t("sharpe"),
                                                value: advanced.sharpe !== null ? advanced.sharpe.toFixed(2) : "—",
                                                trend: advanced.sharpe !== null ? (advanced.sharpe >= 1 ? "Good" : "Low") : "N/A",
                                                color: "purple",
                                                iconColor: "#A78BFA",
                                                iconBg: "rgba(167,139,250,0.1)",
                                            },
                                            {
                                                label: t("maxDrawdown"),
                                                value: advanced.maxDrawdown !== null ? `-${advanced.maxDrawdown.toFixed(1)}%` : "—",
                                                trend: "Max",
                                                color: "rose",
                                                iconColor: "#F43F5E",
                                                iconBg: "rgba(244,63,94,0.1)",
                                            },
                                        ];
                                        return (
                                            <div className="lg:col-span-3 grid grid-cols-2 lg:grid-cols-4 gap-4">
                                                {statsItems.map((stat, i) => (
                                                    <div
                                                        key={i}
                                                        className="bg-[#141C2B] rounded-xl p-5 border border-white/5 hover:border-white/10 transition-colors"
                                                    >
                                                        <div className="flex items-center justify-between mb-4">
                                                            <div className="p-2 rounded-lg" style={{ background: stat.iconBg }}>
                                                                <Activity className="w-4 h-4" style={{ color: stat.iconColor, width: 16, height: 16 }} />
                                                            </div>
                                                            <span className="text-xs font-semibold px-2 py-1 rounded" style={{ color: stat.iconColor, background: stat.iconBg }}>
                                                                {stat.trend}
                                                            </span>
                                                        </div>
                                                        <div className="text-2xl font-bold text-[#E6EDF3] tracking-tight mb-1">
                                                            {stat.value}
                                                        </div>
                                                        <div className="text-xs font-medium text-[#6B7280]">
                                                            {stat.label}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        );
                                    })()}
                                </div>

                                {/* Tabs & Main Chart */}
                                <div className="bg-[#141C2B] rounded-xl border border-white/5 mb-8">
                                    <div className="flex border-b border-white/5">
                                        {[
                                            { id: "performance", label: t("performance") },
                                            { id: "session", label: t("session") },
                                            { id: "comparison", label: t("comparison") },
                                        ].map((tab) => (
                                            <button
                                                key={tab.id}
                                                onClick={() => setActiveTab(tab.id as any)}
                                                className={`px-6 py-4 text-sm font-medium transition-colors relative ${activeTab === tab.id
                                                    ? "text-[#E6EDF3]"
                                                    : "text-[#6B7280] hover:text-[#9AA4B2]"
                                                    }`}
                                            >
                                                {tab.label}
                                                {activeTab === tab.id && (
                                                    <motion.div
                                                        layoutId="activeTab"
                                                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500"
                                                    />
                                                )}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="p-6">
                                        {activeTab === "performance" && (
                                            <div className="h-[300px] w-full">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <AreaChart data={data?.timeSeriesData || []}>
                                                        <defs>
                                                            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                                                                <stop offset="5%" stopColor="#16C784" stopOpacity={0.2} />
                                                                <stop offset="95%" stopColor="#16C784" stopOpacity={0} />
                                                            </linearGradient>
                                                        </defs>
                                                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
                                                        <XAxis
                                                            dataKey="date"
                                                            stroke="#6B7280"
                                                            fontSize={12}
                                                            tickLine={false}
                                                            axisLine={false}
                                                            minTickGap={30}
                                                        />
                                                        <YAxis
                                                            yAxisId="left"
                                                            stroke="#6B7280"
                                                            fontSize={12}
                                                            tickLine={false}
                                                            axisLine={false}
                                                            tickFormatter={(val) => `$${val}`}
                                                        />
                                                        <YAxis
                                                            yAxisId="right"
                                                            orientation="right"
                                                            stroke="#6B7280"
                                                            fontSize={12}
                                                            tickLine={false}
                                                            axisLine={false}
                                                            tickFormatter={(val) => `${val}%`}
                                                        />
                                                        <Tooltip content={<CustomPerformanceTooltip />} />
                                                        <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "20px" }} />
                                                        <Area
                                                            yAxisId="left"
                                                            type="monotone"
                                                            dataKey="equity"
                                                            name={t("equityCurve")}
                                                            stroke="#16C784"
                                                            strokeWidth={2}
                                                            fillOpacity={1}
                                                            fill="url(#equityGradient)"
                                                        />
                                                        <Line
                                                            yAxisId="right"
                                                            type="monotone"
                                                            dataKey="accuracy"
                                                            name={t("accuracyChart")}
                                                            stroke="#4F8CFF"
                                                            strokeWidth={2}
                                                            dot={false}
                                                        />
                                                    </AreaChart>
                                                </ResponsiveContainer>
                                            </div>
                                        )}

                                        {activeTab === "comparison" && (
                                            <div className="h-[300px] w-full flex justify-center">
                                                <div className="w-full max-w-[500px] h-full">
                                                    <ResponsiveContainer width="100%" height="100%">
                                                        <RadarChart
                                                            cx="50%"
                                                            cy="50%"
                                                            outerRadius="70%"
                                                            data={[
                                                                { subject: t("accuracyChart"), A: data?.comparisonMetrics?.accuracy || 0, fullMark: 100 },
                                                                { subject: t("speed"), A: data?.comparisonMetrics?.speed || 0, fullMark: 100 },
                                                                { subject: t("profit"), A: data?.comparisonMetrics?.profit || 0, fullMark: 100 },
                                                                { subject: t("riskControl"), A: data?.comparisonMetrics?.riskControl || 0, fullMark: 100 },
                                                                { subject: t("trendFollowing"), A: data?.comparisonMetrics?.trendFollowing || 0, fullMark: 100 },
                                                            ]}
                                                        >
                                                            <PolarGrid stroke="#ffffff1a" />
                                                            <PolarAngleAxis dataKey="subject" tick={{ fill: "#9AA4B2", fontSize: 12, fontWeight: 500 }} />
                                                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                                            <Radar
                                                                name="Current Model"
                                                                dataKey="A"
                                                                stroke="#4F8CFF"
                                                                strokeWidth={2}
                                                                fill="#4F8CFF"
                                                                fillOpacity={0.3}
                                                            />
                                                            <Tooltip
                                                                contentStyle={{ backgroundColor: "#141C2B", borderColor: "#ffffff1a", borderRadius: "8px" }}
                                                                itemStyle={{ color: "#E6EDF3" }}
                                                            />
                                                        </RadarChart>
                                                    </ResponsiveContainer>
                                                </div>
                                            </div>
                                        )}

                                        {activeTab === "session" && (
                                            <div className="flex flex-col items-center justify-center h-[300px] text-center">
                                                <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
                                                    <Clock className="w-8 h-8" style={{ color: "#6B7280", width: 32, height: 32 }} />
                                                </div>
                                                <h3 className="text-[#E6EDF3] font-medium text-lg mb-2">{t("sessionTitle")}</h3>
                                                <p className="text-[#9AA4B2] text-sm max-w-sm">
                                                    {t("sessionPlaceholder")}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Recent Signals Table */}
                                <div>
                                    <h3 className="text-[#E6EDF3] font-semibold mb-4 text-lg">
                                        {t("recentSignals")}
                                    </h3>
                                    <div className="overflow-x-auto rounded-xl border border-white/5 bg-[#141C2B]">
                                        <table className="w-full text-left text-sm">
                                            <thead className="bg-white/5 border-b border-white/5 text-[#9AA4B2] text-xs font-semibold uppercase tracking-wider">
                                                <tr>
                                                    <th className="px-6 py-4">{t("date")}</th>
                                                    <th className="px-6 py-4">{t("symbolCol")}</th>
                                                    <th className="px-6 py-4">{t("signal")}</th>
                                                    <th className="px-6 py-4">{t("result")}</th>
                                                    <th className="px-6 py-4 text-right">{t("returnCol")}</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-white/5">
                                                {(data?.recentSignals || []).length > 0 ? (data?.recentSignals || []).map((signal) => (
                                                    <tr key={signal.id} className="hover:bg-white/[0.02] transition-colors group">
                                                        <td className="px-6 py-4 font-medium text-[#9AA4B2]">
                                                            {signal.date}
                                                        </td>
                                                        <td className="px-6 py-4 font-bold text-[#E6EDF3]">
                                                            {signal.symbol}
                                                        </td>
                                                        <td className="px-6 py-4">
                                                            <span
                                                                className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${signal.prediction === "buy"
                                                                    ? "bg-emerald-500/10 text-emerald-400"
                                                                    : signal.prediction === "sell"
                                                                        ? "bg-rose-500/10 text-rose-400"
                                                                        : "bg-white/10 text-[#E6EDF3]"
                                                                    }`}
                                                            >
                                                                {signal.prediction}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4">
                                                            {signal.result === "win" ? (
                                                                <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                                                                    <CheckCircle2 className="w-4 h-4" style={{ width: 16, height: 16 }} />
                                                                    {t("win")}
                                                                </div>
                                                            ) : signal.result === "loss" ? (
                                                                <div className="flex items-center gap-1.5 text-rose-400 font-medium">
                                                                    <XCircle className="w-4 h-4" style={{ width: 16, height: 16 }} />
                                                                    {t("loss")}
                                                                </div>
                                                            ) : (
                                                                <div className="flex items-center gap-1.5 text-[#9AA4B2] font-medium">
                                                                    <AlertCircle className="w-4 h-4" style={{ width: 16, height: 16 }} />
                                                                    {lang === "tr" ? "Beklemede" : "Pending"}
                                                                </div>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 text-right">
                                                            <span
                                                                className={`font-semibold ${signal.profit > 0
                                                                    ? "text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]"
                                                                    : "text-rose-400"
                                                                    }`}
                                                            >
                                                                {signal.profit > 0 ? "+" : ""}
                                                                {signal.profit.toFixed(1)}p
                                                            </span>
                                                        </td>
                                                    </tr>
                                                )) : (
                                                    <tr>
                                                        <td colSpan={5} className="px-6 py-8 text-center text-[#9AA4B2]">
                                                            {t("noData")}
                                                        </td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
