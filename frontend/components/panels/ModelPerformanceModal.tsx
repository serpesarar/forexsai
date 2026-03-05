"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://upbeat-flow-production.up.railway.app";

/* ═══════════════════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════════════════ */

interface HourlyData { hour: number; total: number; wins: number; win_rate: number; avg_pips: number; }
interface TFData { tf: string; total: number; win_rate: number; net_pips: number; avg_pips: number; }
interface DailyData { date: string; total: number; wins: number; win_rate: number; cumulative_pips: number; }
interface DOWData { day: string; day_short: string; total: number; wins: number; win_rate: number; avg_pips: number; }
interface RecentSignal { id: string; date: string; direction: string; confidence: number; status: string; pips: number; timeframe: string; }

interface AnalyticsData {
    model: string;
    symbol: string;
    overview: {
        total_signals: number; win_rate: number; completed: number; stopped: number;
        expired: number; active: number; net_pips: number; avg_profit_pips: number;
        avg_loss_pips: number; risk_reward: number; sharpe_ratio: number;
        max_drawdown_pips: number; profit_factor: number;
    };
    hourly_heatmap: HourlyData[];
    timeframe_comparison: TFData[];
    daily_accuracy: DailyData[];
    day_of_week: DOWData[];
    tp_hit_rates: Record<string, number>;
    recent_signals: RecentSignal[];
}

interface ModelPerformanceModalProps {
    isOpen: boolean;
    onClose: () => void;
    symbol: string;
    model?: string;
}

/* ═══════════════════════════════════════════════════════════════════
   I18N
   ═══════════════════════════════════════════════════════════════════ */

const T: Record<string, Record<string, string>> = {
    en: {
        overview: "Overview", hourly: "Hourly Heatmap", timeframe: "Timeframe Analysis",
        dayOfWeek: "Day Analysis", winRate: "Win Rate", totalSignals: "Total Signals",
        netPips: "Net Pips", riskReward: "R:R Ratio", sharpe: "Sharpe Ratio",
        maxDD: "Max Drawdown", profitFactor: "Profit Factor", completed: "Wins",
        stopped: "Losses", tpHitRates: "Target Hit Rates", dailyAccuracy: "Daily Accuracy",
        cumPips: "Cumulative Pips", recentSignals: "Recent Signals", date: "Date",
        direction: "Direction", confidence: "Confidence", status: "Status", pips: "Pips",
        tf: "TF", bestHours: "Best Trading Hours", worstHours: "Worst Hours",
        signals: "signals", noData: "No signal data available for this combination.",
        avgPips: "Avg Pips", close: "Close",
    },
    tr: {
        overview: "Genel Bakış", hourly: "Saatlik Performans", timeframe: "Zaman Dilimi Analizi",
        dayOfWeek: "Gün Analizi", winRate: "Başarı Oranı", totalSignals: "Toplam Sinyal",
        netPips: "Net Pips", riskReward: "R:R Oranı", sharpe: "Sharpe Oranı",
        maxDD: "Maks. Düşüş", profitFactor: "Kâr Faktörü", completed: "Kazanç",
        stopped: "Kayıp", tpHitRates: "Hedef İsabet Oranları", dailyAccuracy: "Günlük Doğruluk",
        cumPips: "Kümülatif Pips", recentSignals: "Son Sinyaller", date: "Tarih",
        direction: "Yön", confidence: "Güven", status: "Durum", pips: "Pips",
        tf: "ZD", bestHours: "En İyi İşlem Saatleri", worstHours: "Kötü Saatler",
        signals: "sinyal", noData: "Bu kombinasyon için sinyal verisi bulunamadı.",
        avgPips: "Ort. Pips", close: "Kapat",
    },
};

const SYM_DISPLAY: Record<string, string> = {
    "NDX.INDX": "NASDAQ", "GDAXI.INDX": "DAX", "USOIL.FOREX": "US OIL", "CL.F": "US OIL",
};
const MODEL_DISPLAY: Record<string, string> = {
    ml: "ML Model", emel: "EMEL 9-Check", pulse1: "Pulse 1 — Algo", pulse2: "Pulse 2 — ML",
    pulse3: "Pulse 3 — Scalp", emel_inverse: "EMEL Inverse",
};

/* ═══════════════════════════════════════════════════════════════════
   HELPER: Color Scales
   ═══════════════════════════════════════════════════════════════════ */

function wrColor(wr: number): string {
    if (wr >= 70) return "#00F0FF";
    if (wr >= 55) return "#16C784";
    if (wr >= 45) return "#F5A623";
    if (wr >= 30) return "#EA3943";
    return "#6B7280";
}

function wrBg(wr: number, total: number): string {
    if (total === 0) return "rgba(255,255,255,0.02)";
    if (wr >= 70) return "rgba(0,240,255,0.15)";
    if (wr >= 55) return "rgba(22,199,132,0.15)";
    if (wr >= 45) return "rgba(245,166,35,0.12)";
    if (wr >= 30) return "rgba(234,57,67,0.12)";
    return "rgba(107,114,128,0.08)";
}

function statusColor(s: string): string {
    if (s === "completed") return "#16C784";
    if (s === "stopped") return "#EA3943";
    if (s === "active") return "#00F0FF";
    return "#6B7280";
}

/* ═══════════════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════════════ */

export const ModelPerformanceModal: React.FC<ModelPerformanceModalProps> = ({
    isOpen, onClose, symbol, model,
}) => {
    const lang = typeof window !== "undefined"
        ? (localStorage.getItem("language") || (navigator.language?.startsWith("tr") ? "tr" : "en"))
        : "en";
    const t = (key: string) => (T[lang]?.[key] || T.en[key] || key);

    const [activeTab, setActiveTab] = useState<"overview" | "hourly" | "timeframe" | "dayOfWeek">("overview");

    const { data, isLoading } = useQuery<AnalyticsData>({
        queryKey: ["model-detail-analytics", model, symbol],
        queryFn: async () => {
            const params = new URLSearchParams({ symbol });
            if (model) params.append("model", model);
            const res = await fetch(`${API_BASE}/api/learning/model-detail-analytics?${params}`);
            if (!res.ok) throw new Error("fetch failed");
            return res.json();
        },
        enabled: isOpen && !!symbol,
    });

    if (!isOpen) return null;

    const symDisplay = SYM_DISPLAY[symbol] || symbol;
    const modelDisplay = model ? (MODEL_DISPLAY[model] || model) : "All";
    const ov = data?.overview;

    /* ── Custom Tooltip ── */
    const CyberTooltip = ({ active, payload, label }: any) => {
        if (!active || !payload?.length) return null;
        return (
            <div style={{
                background: "rgba(11,15,23,0.95)", border: "1px solid rgba(0,240,255,0.3)",
                borderRadius: 8, padding: "10px 14px", backdropFilter: "blur(12px)",
                boxShadow: "0 0 20px rgba(0,240,255,0.15)",
            }}>
                <p style={{ color: "#9AA4B2", fontSize: 11, marginBottom: 4 }}>{label}</p>
                {payload.map((e: any, i: number) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: e.color }} />
                        <span style={{ color: "#E6EDF3", fontSize: 12 }}>
                            {e.name}: {typeof e.value === "number" ? e.value.toFixed(1) : e.value}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    /* ── Tabs ── */
    const tabs = [
        { key: "overview" as const, label: t("overview") },
        { key: "hourly" as const, label: t("hourly") },
        { key: "timeframe" as const, label: t("timeframe") },
        { key: "dayOfWeek" as const, label: t("dayOfWeek") },
    ];

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center p-4"
                    style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ scale: 0.92, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.92, opacity: 0 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl"
                        style={{
                            background: "linear-gradient(145deg, #0B0F17 0%, #111827 50%, #0D1117 100%)",
                            border: "1px solid rgba(0,240,255,0.15)",
                            boxShadow: "0 0 40px rgba(0,240,255,0.08), 0 0 80px rgba(0,240,255,0.04)",
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* ── HEADER ── */}
                        <div className="relative px-6 pt-5 pb-4" style={{ borderBottom: "1px solid rgba(0,240,255,0.1)" }}>
                            {/* Scan line effect */}
                            <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ opacity: 0.03 }}>
                                {Array.from({ length: 20 }).map((_, i) => (
                                    <div key={i} style={{ height: 1, background: "#00F0FF", marginBottom: 3 }} />
                                ))}
                            </div>
                            <div className="flex items-center justify-between relative">
                                <div>
                                    <p style={{ fontSize: 11, fontWeight: 500, color: "#00F0FF", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                                        {modelDisplay}
                                    </p>
                                    <h2 style={{ fontSize: 22, fontWeight: 700, color: "#E6EDF3", letterSpacing: "-0.02em" }}>
                                        {symDisplay} <span style={{ color: "#9AA4B2", fontSize: 14, fontWeight: 400 }}>Performance Analytics</span>
                                    </h2>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="w-8 h-8 rounded-lg flex items-center justify-center transition-all"
                                    style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }}
                                    onMouseEnter={(e) => e.currentTarget.style.background = "rgba(234,57,67,0.2)"}
                                    onMouseLeave={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
                                >
                                    <span style={{ color: "#9AA4B2", fontSize: 16 }}>✕</span>
                                </button>
                            </div>
                            {/* Tab Bar */}
                            <div className="flex gap-1 mt-4" style={{ background: "rgba(255,255,255,0.03)", borderRadius: 10, padding: 3 }}>
                                {tabs.map((tab) => (
                                    <button
                                        key={tab.key}
                                        onClick={() => setActiveTab(tab.key)}
                                        style={{
                                            flex: 1, padding: "8px 12px", borderRadius: 8, fontSize: 12, fontWeight: 600,
                                            transition: "all 0.2s",
                                            background: activeTab === tab.key ? "rgba(0,240,255,0.12)" : "transparent",
                                            color: activeTab === tab.key ? "#00F0FF" : "#6B7280",
                                            border: activeTab === tab.key ? "1px solid rgba(0,240,255,0.25)" : "1px solid transparent",
                                        }}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* ── BODY ── */}
                        <div className="p-6">
                            {isLoading ? (
                                <div className="flex flex-col items-center justify-center py-16">
                                    <div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: "rgba(0,240,255,0.2)", borderTopColor: "#00F0FF" }} />
                                    <p style={{ color: "#6B7280", fontSize: 12, marginTop: 12 }}>Loading analytics...</p>
                                </div>
                            ) : !data || data.overview?.total_signals === 0 ? (
                                <div className="text-center py-16">
                                    <p style={{ color: "#6B7280", fontSize: 14 }}>{t("noData")}</p>
                                </div>
                            ) : (
                                <>
                                    {activeTab === "overview" && ov && <OverviewTab ov={ov} tpRates={data.tp_hit_rates} daily={data.daily_accuracy} recent={data.recent_signals} tfData={data.timeframe_comparison} t={t} />}
                                    {activeTab === "hourly" && <HourlyTab data={data.hourly_heatmap} t={t} />}
                                    {activeTab === "timeframe" && <TimeframeTab data={data.timeframe_comparison} t={t} tooltip={CyberTooltip} />}
                                    {activeTab === "dayOfWeek" && <DOWTab data={data.day_of_week} t={t} tooltip={CyberTooltip} />}
                                </>
                            )}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   TAB 1: OVERVIEW
   ═══════════════════════════════════════════════════════════════════ */

function OverviewTab({ ov, tpRates, daily, recent, tfData, t }: {
    ov: AnalyticsData["overview"]; tpRates: Record<string, number>;
    daily: DailyData[]; recent: RecentSignal[]; tfData: TFData[];
    t: (k: string) => string;
}) {
    return (
        <div className="space-y-5">
            {/* KPI Grid */}
            <div className="grid grid-cols-3 gap-3">
                <KPICard label={t("winRate")} value={`${ov.win_rate}%`} color={wrColor(ov.win_rate)} glow />
                <KPICard label={t("totalSignals")} value={`${ov.total_signals}`} color="#E6EDF3" sub={`${ov.completed}W / ${ov.stopped}L`} />
                <KPICard label={t("netPips")} value={`${ov.net_pips >= 0 ? "+" : ""}${ov.net_pips}`} color={ov.net_pips >= 0 ? "#16C784" : "#EA3943"} />
                <KPICard label={t("riskReward")} value={`${ov.risk_reward}`} color="#F5A623" />
                <KPICard label={t("sharpe")} value={`${ov.sharpe_ratio}`} color="#8B5CF6" />
                <KPICard label={t("maxDD")} value={`-${ov.max_drawdown_pips}p`} color="#EA3943" />
            </div>

            {/* Timeframe Breakdown Mini */}
            {tfData.length > 0 && (
                <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                    <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>
                        {t("timeframe")}
                    </p>
                    <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.min(tfData.length, 6)}, 1fr)` }}>
                        {tfData.map((tf) => (
                            <div key={tf.tf} style={{
                                background: wrBg(tf.win_rate, tf.total), borderRadius: 8, padding: "10px 8px",
                                border: `1px solid ${wrColor(tf.win_rate)}20`, textAlign: "center",
                            }}>
                                <p style={{ fontSize: 11, fontWeight: 700, color: "#E6EDF3", textTransform: "uppercase" }}>{tf.tf}</p>
                                <p style={{ fontSize: 18, fontWeight: 700, color: wrColor(tf.win_rate), marginTop: 4 }}>{tf.win_rate}%</p>
                                <p style={{ fontSize: 10, color: "#6B7280" }}>{tf.total} {t("signals")}</p>
                                <p style={{ fontSize: 10, color: tf.net_pips >= 0 ? "#16C784" : "#EA3943", marginTop: 2 }}>
                                    {tf.net_pips >= 0 ? "+" : ""}{tf.net_pips}p
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* TP Hit Rates */}
            <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>
                    {t("tpHitRates")}
                </p>
                <div className="space-y-2">
                    {["TP1", "TP2", "TP3", "TP4"].map((tp) => {
                        const rate = tpRates[tp] || 0;
                        return (
                            <div key={tp} className="flex items-center gap-3">
                                <span style={{ fontSize: 12, fontWeight: 600, color: "#E6EDF3", width: 32 }}>{tp}</span>
                                <div style={{ flex: 1, height: 8, borderRadius: 4, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                                    <div style={{
                                        width: `${rate}%`, height: "100%", borderRadius: 4,
                                        background: `linear-gradient(90deg, ${wrColor(rate)}, ${wrColor(rate)}90)`,
                                        boxShadow: rate > 50 ? `0 0 8px ${wrColor(rate)}40` : "none",
                                        transition: "width 0.8s ease-out",
                                    }} />
                                </div>
                                <span style={{ fontSize: 12, fontWeight: 600, color: wrColor(rate), width: 44, textAlign: "right" }}>{rate}%</span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Daily Cumulative Pips Chart */}
            {daily.length > 0 && (
                <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                    <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>
                        {t("cumPips")}
                    </p>
                    <ResponsiveContainer width="100%" height={160}>
                        <LineChart data={daily}>
                            <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                            <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6B7280" }} tickFormatter={(v: string) => v.slice(5)} />
                            <YAxis tick={{ fontSize: 10, fill: "#6B7280" }} />
                            <Tooltip content={({ active, payload, label }: any) => {
                                if (!active || !payload?.length) return null;
                                return (
                                    <div style={{ background: "rgba(11,15,23,0.95)", border: "1px solid rgba(0,240,255,0.3)", borderRadius: 8, padding: "8px 12px" }}>
                                        <p style={{ color: "#9AA4B2", fontSize: 11 }}>{label}</p>
                                        <p style={{ color: "#00F0FF", fontSize: 13, fontWeight: 600 }}>{payload[0].value} pips</p>
                                    </div>
                                );
                            }} />
                            <Line type="monotone" dataKey="cumulative_pips" stroke="#00F0FF" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Recent Signals Table */}
            {recent.length > 0 && (
                <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                    <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>
                        {t("recentSignals")}
                    </p>
                    <div className="overflow-x-auto">
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                                <tr>
                                    {[t("date"), t("direction"), t("tf"), t("confidence"), t("status"), t("pips")].map((h) => (
                                        <th key={h} style={{ fontSize: 10, fontWeight: 600, color: "#6B7280", textAlign: "left", padding: "6px 8px", borderBottom: "1px solid rgba(255,255,255,0.06)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {recent.slice(0, 10).map((s, i) => (
                                    <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                                        <td style={{ fontSize: 11, color: "#9AA4B2", padding: "6px 8px" }}>{s.date.slice(5, 16)}</td>
                                        <td style={{ fontSize: 11, fontWeight: 600, color: s.direction === "BUY" ? "#16C784" : s.direction === "SELL" ? "#EA3943" : "#6B7280", padding: "6px 8px" }}>
                                            {s.direction}
                                        </td>
                                        <td style={{ fontSize: 10, color: "#9AA4B2", padding: "6px 8px" }}>{s.timeframe}</td>
                                        <td style={{ fontSize: 11, color: "#E6EDF3", padding: "6px 8px" }}>{s.confidence}%</td>
                                        <td style={{ padding: "6px 8px" }}>
                                            <span style={{
                                                fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 6,
                                                background: `${statusColor(s.status)}15`, color: statusColor(s.status),
                                                border: `1px solid ${statusColor(s.status)}30`,
                                            }}>
                                                {s.status === "completed" ? "WIN" : s.status === "stopped" ? "LOSS" : s.status.toUpperCase()}
                                            </span>
                                        </td>
                                        <td style={{ fontSize: 11, fontWeight: 600, color: s.pips >= 0 ? "#16C784" : "#EA3943", padding: "6px 8px" }}>
                                            {s.pips >= 0 ? "+" : ""}{s.pips}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   TAB 2: HOURLY HEATMAP
   ═══════════════════════════════════════════════════════════════════ */

function HourlyTab({ data, t }: { data: HourlyData[]; t: (k: string) => string }) {
    const bestHours = [...data].filter(h => h.total > 0).sort((a, b) => b.win_rate - a.win_rate).slice(0, 3);
    const worstHours = [...data].filter(h => h.total > 0).sort((a, b) => a.win_rate - b.win_rate).slice(0, 3);

    return (
        <div className="space-y-5">
            {/* Best / Worst Hours Badges */}
            <div className="grid grid-cols-2 gap-3">
                <div style={{ background: "rgba(0,240,255,0.06)", borderRadius: 12, border: "1px solid rgba(0,240,255,0.15)", padding: 14 }}>
                    <p style={{ fontSize: 10, fontWeight: 600, color: "#00F0FF", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
                        🏆 {t("bestHours")}
                    </p>
                    {bestHours.map((h) => (
                        <div key={h.hour} className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                            <span style={{ fontSize: 13, fontWeight: 600, color: "#E6EDF3" }}>{String(h.hour).padStart(2, "0")}:00</span>
                            <span style={{ fontSize: 12, fontWeight: 700, color: "#16C784" }}>{h.win_rate}% ({h.total})</span>
                        </div>
                    ))}
                </div>
                <div style={{ background: "rgba(234,57,67,0.06)", borderRadius: 12, border: "1px solid rgba(234,57,67,0.15)", padding: 14 }}>
                    <p style={{ fontSize: 10, fontWeight: 600, color: "#EA3943", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8 }}>
                        ⚠️ {t("worstHours")}
                    </p>
                    {worstHours.map((h) => (
                        <div key={h.hour} className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                            <span style={{ fontSize: 13, fontWeight: 600, color: "#E6EDF3" }}>{String(h.hour).padStart(2, "0")}:00</span>
                            <span style={{ fontSize: 12, fontWeight: 700, color: "#EA3943" }}>{h.win_rate}% ({h.total})</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* 24-Hour Heatmap Grid */}
            <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 14 }}>
                    24-Hour Performance Grid (UTC)
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 6 }}>
                    {data.map((h) => (
                        <div key={h.hour} style={{
                            background: wrBg(h.win_rate, h.total),
                            borderRadius: 8, padding: "10px 6px", textAlign: "center",
                            border: `1px solid ${h.total > 0 ? wrColor(h.win_rate) + "20" : "rgba(255,255,255,0.03)"}`,
                            boxShadow: h.win_rate >= 70 && h.total > 0 ? `0 0 12px ${wrColor(h.win_rate)}25` : "none",
                            transition: "all 0.3s",
                        }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: "#E6EDF3", fontFamily: "monospace" }}>
                                {String(h.hour).padStart(2, "0")}:00
                            </p>
                            <p style={{
                                fontSize: 16, fontWeight: 700, marginTop: 4,
                                color: h.total > 0 ? wrColor(h.win_rate) : "#333",
                            }}>
                                {h.total > 0 ? `${h.win_rate}%` : "—"}
                            </p>
                            <p style={{ fontSize: 9, color: "#6B7280", marginTop: 2 }}>
                                {h.total > 0 ? `${h.wins}/${h.total}` : "—"}
                            </p>
                            {h.total > 0 && (
                                <p style={{ fontSize: 9, color: h.avg_pips >= 0 ? "#16C784" : "#EA3943", marginTop: 1 }}>
                                    {h.avg_pips >= 0 ? "+" : ""}{h.avg_pips}p
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   TAB 3: TIMEFRAME ANALYSIS
   ═══════════════════════════════════════════════════════════════════ */

function TimeframeTab({ data, t, tooltip }: { data: TFData[]; t: (k: string) => string; tooltip: any }) {
    if (data.length === 0) return <p style={{ color: "#6B7280", textAlign: "center", padding: 40 }}>{t("noData")}</p>;

    const best = data.reduce((a, b) => a.win_rate > b.win_rate ? a : b);

    return (
        <div className="space-y-5">
            {/* Bar Chart */}
            <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>
                    {t("winRate")} by {t("timeframe")}
                </p>
                <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={data}>
                        <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                        <XAxis dataKey="tf" tick={{ fontSize: 12, fill: "#9AA4B2", fontWeight: 600 }} />
                        <YAxis tick={{ fontSize: 10, fill: "#6B7280" }} domain={[0, 100]} />
                        <Tooltip content={tooltip} />
                        <Bar dataKey="win_rate" name={t("winRate")} radius={[6, 6, 0, 0]}>
                            {data.map((entry, i) => (
                                <Cell
                                    key={i}
                                    fill={entry.tf === best.tf ? "#00F0FF" : wrColor(entry.win_rate)}
                                    style={entry.tf === best.tf ? { filter: "drop-shadow(0 0 6px rgba(0,240,255,0.4))" } : {}}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Comparison Table */}
            <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr>
                            {[t("tf"), t("totalSignals"), t("winRate"), t("netPips"), t("avgPips")].map((h) => (
                                <th key={h} style={{ fontSize: 10, fontWeight: 600, color: "#6B7280", textAlign: "left", padding: "8px 10px", borderBottom: "1px solid rgba(255,255,255,0.06)", textTransform: "uppercase" }}>
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row) => (
                            <tr key={row.tf} style={{
                                borderBottom: "1px solid rgba(255,255,255,0.03)",
                                background: row.tf === best.tf ? "rgba(0,240,255,0.05)" : "transparent",
                            }}>
                                <td style={{ padding: "8px 10px", fontSize: 13, fontWeight: 700, color: row.tf === best.tf ? "#00F0FF" : "#E6EDF3" }}>
                                    {row.tf.toUpperCase()} {row.tf === best.tf && "⭐"}
                                </td>
                                <td style={{ padding: "8px 10px", fontSize: 12, color: "#9AA4B2" }}>{row.total}</td>
                                <td style={{ padding: "8px 10px", fontSize: 13, fontWeight: 700, color: wrColor(row.win_rate) }}>{row.win_rate}%</td>
                                <td style={{ padding: "8px 10px", fontSize: 12, fontWeight: 600, color: row.net_pips >= 0 ? "#16C784" : "#EA3943" }}>
                                    {row.net_pips >= 0 ? "+" : ""}{row.net_pips}
                                </td>
                                <td style={{ padding: "8px 10px", fontSize: 12, color: "#9AA4B2" }}>{row.avg_pips}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   TAB 4: DAY OF WEEK
   ═══════════════════════════════════════════════════════════════════ */

function DOWTab({ data, t, tooltip }: { data: DOWData[]; t: (k: string) => string; tooltip: any }) {
    const workDays = data.filter((d) => d.total > 0);
    if (workDays.length === 0) return <p style={{ color: "#6B7280", textAlign: "center", padding: 40 }}>{t("noData")}</p>;

    return (
        <div className="space-y-5">
            {/* Horizontal Bars */}
            <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)", padding: 16 }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: "#9AA4B2", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 14 }}>
                    {t("winRate")} by Day
                </p>
                <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={workDays} layout="vertical">
                        <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 10, fill: "#6B7280" }} domain={[0, 100]} />
                        <YAxis dataKey="day_short" type="category" tick={{ fontSize: 12, fill: "#E6EDF3", fontWeight: 600 }} width={40} />
                        <Tooltip content={tooltip} />
                        <Bar dataKey="win_rate" name={t("winRate")} radius={[0, 6, 6, 0]}>
                            {workDays.map((entry, i) => (
                                <Cell key={i} fill={wrColor(entry.win_rate)} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Day Cards */}
            <div className="grid grid-cols-2 gap-3">
                {workDays.map((d) => (
                    <div key={d.day} style={{
                        background: wrBg(d.win_rate, d.total), borderRadius: 10,
                        border: `1px solid ${wrColor(d.win_rate)}20`, padding: 14,
                    }}>
                        <div className="flex items-center justify-between">
                            <p style={{ fontSize: 13, fontWeight: 700, color: "#E6EDF3" }}>{d.day}</p>
                            <p style={{ fontSize: 16, fontWeight: 700, color: wrColor(d.win_rate) }}>{d.win_rate}%</p>
                        </div>
                        <div className="flex items-center gap-4 mt-2">
                            <span style={{ fontSize: 10, color: "#6B7280" }}>{d.total} {t("signals")}</span>
                            <span style={{ fontSize: 10, color: "#16C784" }}>{d.wins}W</span>
                            <span style={{ fontSize: 10, color: "#EA3943" }}>{d.total - d.wins}L</span>
                            <span style={{ fontSize: 10, color: d.avg_pips >= 0 ? "#16C784" : "#EA3943", marginLeft: "auto" }}>
                                {d.avg_pips >= 0 ? "+" : ""}{d.avg_pips}p
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════
   KPI CARD
   ═══════════════════════════════════════════════════════════════════ */

function KPICard({ label, value, color, sub, glow }: { label: string; value: string; color: string; sub?: string; glow?: boolean }) {
    return (
        <div style={{
            background: "rgba(255,255,255,0.03)", borderRadius: 12, padding: "14px 16px",
            border: `1px solid ${color}18`,
            boxShadow: glow ? `0 0 20px ${color}15` : "none",
        }}>
            <p style={{ fontSize: 10, fontWeight: 500, color: "#6B7280", letterSpacing: "0.06em", textTransform: "uppercase" }}>{label}</p>
            <p style={{ fontSize: 24, fontWeight: 700, color, marginTop: 4, letterSpacing: "-0.5px", fontFamily: "'JetBrains Mono', monospace" }}>{value}</p>
            {sub && <p style={{ fontSize: 10, color: "#6B7280", marginTop: 2 }}>{sub}</p>}
        </div>
    );
}
