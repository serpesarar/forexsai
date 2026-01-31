"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AlertTriangle, TrendingDown, Zap, Brain, BarChart3, Shield, XCircle, AlertOctagon } from "lucide-react";

export default function RiskPage() {
    const { t } = useI18n();

    const riskSections = [
        {
            icon: TrendingDown,
            title: t("legal.risk.sections.general.title"),
            color: "red",
            content: [
                { subtitle: t("legal.risk.sections.general.capital.title"), text: t("legal.risk.sections.general.capital.text") },
                { subtitle: t("legal.risk.sections.general.leverage.title"), text: t("legal.risk.sections.general.leverage.text") },
                { subtitle: t("legal.risk.sections.general.volatility.title"), text: t("legal.risk.sections.general.volatility.text") }
            ]
        },
        {
            icon: Brain,
            title: t("legal.risk.sections.ai.title"),
            color: "purple",
            content: [
                { subtitle: t("legal.risk.sections.ai.errors.title"), text: t("legal.risk.sections.ai.errors.text") },
                { subtitle: t("legal.risk.sections.ai.past.title"), text: t("legal.risk.sections.ai.past.text") },
                { subtitle: t("legal.risk.sections.ai.technical.title"), text: t("legal.risk.sections.ai.technical.text") }
            ]
        },
        {
            icon: XCircle,
            title: t("legal.risk.sections.notAdvice.title"),
            color: "amber",
            content: [
                { subtitle: t("legal.risk.sections.notAdvice.info.title"), text: t("legal.risk.sections.notAdvice.info.text") },
                { subtitle: t("legal.risk.sections.notAdvice.notLicensed.title"), text: t("legal.risk.sections.notAdvice.notLicensed.text") },
                { subtitle: t("legal.risk.sections.notAdvice.responsibility.title"), text: t("legal.risk.sections.notAdvice.responsibility.text") }
            ]
        },
        {
            icon: BarChart3,
            title: t("legal.risk.sections.market.title"),
            color: "cyan",
            content: [
                { subtitle: t("legal.risk.sections.market.nasdaq.title"), text: t("legal.risk.sections.market.nasdaq.text") },
                { subtitle: t("legal.risk.sections.market.gold.title"), text: t("legal.risk.sections.market.gold.text") },
                { subtitle: t("legal.risk.sections.market.liquidity.title"), text: t("legal.risk.sections.market.liquidity.text") }
            ]
        },
        {
            icon: Shield,
            title: t("legal.risk.sections.protection.title"),
            color: "emerald",
            content: [
                { subtitle: t("legal.risk.sections.protection.education.title"), text: t("legal.risk.sections.protection.education.text") },
                { subtitle: t("legal.risk.sections.protection.riskMgmt.title"), text: t("legal.risk.sections.protection.riskMgmt.text") },
                { subtitle: t("legal.risk.sections.protection.emotional.title"), text: t("legal.risk.sections.protection.emotional.text") },
                { subtitle: t("legal.risk.sections.protection.professional.title"), text: t("legal.risk.sections.protection.professional.text") }
            ]
        }
    ];

    const colorClasses = {
        red: {
            bg: "from-red-500/20 to-rose-500/20",
            border: "border-red-500/30",
            icon: "text-red-400",
            subtitle: "text-red-400"
        },
        purple: {
            bg: "from-purple-500/20 to-indigo-500/20",
            border: "border-purple-500/30",
            icon: "text-purple-400",
            subtitle: "text-purple-400"
        },
        amber: {
            bg: "from-amber-500/20 to-orange-500/20",
            border: "border-amber-500/30",
            icon: "text-amber-400",
            subtitle: "text-amber-400"
        },
        cyan: {
            bg: "from-cyan-500/20 to-blue-500/20",
            border: "border-cyan-500/30",
            icon: "text-cyan-400",
            subtitle: "text-cyan-400"
        },
        emerald: {
            bg: "from-emerald-500/20 to-teal-500/20",
            border: "border-emerald-500/30",
            icon: "text-emerald-400",
            subtitle: "text-emerald-400"
        }
    };

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto z-10">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-red-500/20 to-rose-500/20 border border-red-500/30 mb-6 animate-pulse">
                        <AlertTriangle className="w-10 h-10 text-red-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">{t("legal.risk.title")}</h1>
                    <p className="text-lg text-[#E5E7EB]/60">{t("legal.risk.subtitle")}</p>
                </div>

                {/* Critical Warning Banner */}
                <div className="glass-premium p-6 rounded-3xl mb-8 bg-gradient-to-r from-red-500/20 to-rose-500/20 border-2 border-red-500/40">
                    <div className="flex items-center gap-4">
                        <AlertOctagon className="w-12 h-12 text-red-400 flex-shrink-0" />
                        <div>
                            <h2 className="text-xl font-bold text-red-400 mb-2">{t("legal.risk.critical.title")}</h2>
                            <p className="text-white/90 leading-relaxed">
                                {t("legal.risk.critical.text")}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Risk Sections */}
                <div className="space-y-6">
                    {riskSections.map((section, idx) => {
                        const colors = colorClasses[section.color as keyof typeof colorClasses];
                        return (
                            <div key={idx} className="glass-premium p-8 rounded-3xl">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className={`flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${colors.bg} border ${colors.border}`}>
                                        <section.icon className={`w-6 h-6 ${colors.icon}`} />
                                    </div>
                                    <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                                </div>
                                <div className="space-y-6 pl-16">
                                    {section.content.map((item, itemIdx) => (
                                        <div key={itemIdx}>
                                            <h3 className={`text-lg font-semibold ${colors.subtitle} mb-2`}>{item.subtitle}</h3>
                                            <p className="text-[#E5E7EB]/70 leading-relaxed">{item.text}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Acknowledgment Box */}
                <div className="mt-8 glass-premium p-8 rounded-3xl bg-gradient-to-r from-red-500/10 to-amber-500/10 border-2 border-red-500/30">
                    <div className="flex items-start gap-4">
                        <AlertTriangle className="w-8 h-8 text-red-400 flex-shrink-0 mt-1" />
                        <div>
                            <h2 className="text-xl font-bold text-white mb-4">{t("legal.risk.acknowledgment.title")}</h2>
                            <p className="text-[#E5E7EB]/80 leading-relaxed mb-4">
                                {t("legal.risk.acknowledgment.intro")}
                            </p>
                            <ul className="space-y-2 text-[#E5E7EB]/70">
                                {(t("legal.risk.acknowledgment.items") as unknown as string[])?.map?.((item: string, idx: number) => (
                                    <li key={idx} className="flex items-start gap-2">
                                        <span className="text-red-400">•</span>
                                        {item}
                                    </li>
                                )) || null}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
