"use client";

import { useAdminMetrics, useAdminReports } from "@/lib/api";
import { Loader2, Users, Activity, MessageSquareWarning, Search, Filter, AlertCircle } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";
import AuthGuard from "@/components/AuthGuard";

export default function AdminDashboard() {
    return (
        <AuthGuard>
            <AdminDashboardContent />
        </AuthGuard>
    );
}

function AdminDashboardContent() {
    const { data: metrics, isLoading: metricsLoading } = useAdminMetrics();
    const { data: reports, isLoading: reportsLoading } = useAdminReports();
    const [filter, setFilter] = useState("all");

    if (metricsLoading || reportsLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-[#0B1220]">
                <Loader2 className="w-8 h-8 text-[#00E0C6] animate-spin" />
            </div>
        );
    }

    const statCards = [
        { label: "Toplam Kullanıcı", value: metrics?.total_users || 0, icon: Users, color: "text-blue-500" },
        { label: "Aktif (24s)", value: metrics?.active_users_24h || 0, icon: Activity, color: "text-green-500" },
        { label: "Bekleyen Rapor", value: metrics?.pending_reports || 0, icon: AlertCircle, color: "text-amber-500" },
        { label: "Toplam Bildirim", value: metrics?.total_reports || 0, icon: MessageSquareWarning, color: "text-gray-400" },
    ];

    return (
        <div className="min-h-screen bg-[#0B1220] text-gray-200 p-8 pt-24">
            <div className="max-w-7xl mx-auto space-y-8">
                <header>
                    <h1 className="text-3xl font-bold text-white mb-2">Admin Dashboard</h1>
                    <p className="text-gray-400">Sistem durumu ve kullanıcı bildirimleri.</p>
                </header>

                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {statCards.map((stat, i) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col justify-between"
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-400">{stat.label}</p>
                                    <h3 className="text-3xl font-bold text-white mt-1">{stat.value}</h3>
                                </div>
                                <div className={`p-3 rounded-xl bg-white/5 ${stat.color}`}>
                                    <stat.icon className="w-6 h-6" />
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Reports Section */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold text-white">Gelen Bildirimler</h2>
                        <div className="flex gap-2">
                            {["all", "pending", "resolved"].map((f) => (
                                <button
                                    key={f}
                                    onClick={() => setFilter(f)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
                                        }`}
                                >
                                    {f === "all" ? "Tümü" : f === "pending" ? "Bekleyen" : "Çözülen"}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-black/20 text-gray-400 text-sm">
                                    <tr>
                                        <th className="px-6 py-4 font-medium">Tip</th>
                                        <th className="px-6 py-4 font-medium">Mesaj</th>
                                        <th className="px-6 py-4 font-medium">Kullanıcı / Email</th>
                                        <th className="px-6 py-4 font-medium">Tarih</th>
                                        <th className="px-6 py-4 font-medium">Durum</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5 text-sm">
                                    {reports?.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                                                Henüz rapor bulunmuyor.
                                            </td>
                                        </tr>
                                    ) : (
                                        reports?.map((report: any) => (
                                            <tr key={report.id} className="hover:bg-white/5 transition-colors">
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${report.type === "bug"
                                                                ? "bg-red-500/10 border-red-500/20 text-red-500"
                                                                : report.type === "feature"
                                                                    ? "bg-blue-500/10 border-blue-500/20 text-blue-500"
                                                                    : "bg-gray-500/10 border-gray-500/20 text-gray-400"
                                                            }`}
                                                    >
                                                        {report.type === "bug" ? <BugIcon className="w-3 h-3" /> : null}
                                                        {report.type.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-white max-w-sm truncate" title={report.message}>
                                                    {report.message}
                                                </td>
                                                <td className="px-6 py-4 text-gray-300">
                                                    {report.email || report.user_id || "Anonim"}
                                                </td>
                                                <td className="px-6 py-4 text-gray-400">
                                                    {new Date(report.created_at).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 rounded text-xs ${report.status === 'pending' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-green-500/20 text-green-500'}`}>
                                                        {report.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function BugIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="m8 2 1.88 1.88" />
            <path d="M14.12 3.88 16 2" />
            <path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" />
            <path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6" />
            <path d="M12 20v-9" />
            <path d="M6.53 9C4.6 8.8 3 7.1 3 5" />
            <path d="M6 13H2" />
            <path d="M3 21c0-2.1 1.7-3.9 3.8-4" />
            <path d="M20.97 5c0 2.1-1.6 3.8-3.5 4" />
            <path d="M22 13h-4" />
            <path d="M17.2 17c2.1.1 3.8 1.9 3.8 4" />
        </svg>
    )
}
