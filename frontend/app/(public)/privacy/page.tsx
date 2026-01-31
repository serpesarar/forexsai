"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { Shield, Lock, Eye, Database, Globe, Mail, FileText } from "lucide-react";

export default function PrivacyPage() {
    const { t } = useI18n();

    const sections = [
        {
            icon: Database,
            title: t("legal.privacy.sections.data.title"),
            content: [
                { subtitle: t("legal.privacy.sections.data.account.title"), text: t("legal.privacy.sections.data.account.text") },
                { subtitle: t("legal.privacy.sections.data.usage.title"), text: t("legal.privacy.sections.data.usage.text") },
                { subtitle: t("legal.privacy.sections.data.analytics.title"), text: t("legal.privacy.sections.data.analytics.text") }
            ]
        },
        {
            icon: Eye,
            title: t("legal.privacy.sections.purpose.title"),
            content: [
                { subtitle: t("legal.privacy.sections.purpose.service.title"), text: t("legal.privacy.sections.purpose.service.text") },
                { subtitle: t("legal.privacy.sections.purpose.communication.title"), text: t("legal.privacy.sections.purpose.communication.text") },
                { subtitle: t("legal.privacy.sections.purpose.development.title"), text: t("legal.privacy.sections.purpose.development.text") }
            ]
        },
        {
            icon: Lock,
            title: t("legal.privacy.sections.security.title"),
            content: [
                { subtitle: t("legal.privacy.sections.security.encryption.title"), text: t("legal.privacy.sections.security.encryption.text") },
                { subtitle: t("legal.privacy.sections.security.infrastructure.title"), text: t("legal.privacy.sections.security.infrastructure.text") },
                { subtitle: t("legal.privacy.sections.security.access.title"), text: t("legal.privacy.sections.security.access.text") }
            ]
        },
        {
            icon: Globe,
            title: t("legal.privacy.sections.thirdParty.title"),
            content: [
                { subtitle: t("legal.privacy.sections.thirdParty.providers.title"), text: t("legal.privacy.sections.thirdParty.providers.text") },
                { subtitle: t("legal.privacy.sections.thirdParty.legal.title"), text: t("legal.privacy.sections.thirdParty.legal.text") },
                { subtitle: t("legal.privacy.sections.thirdParty.noSale.title"), text: t("legal.privacy.sections.thirdParty.noSale.text") }
            ]
        },
        {
            icon: FileText,
            title: t("legal.privacy.sections.rights.title"),
            content: [
                { subtitle: t("legal.privacy.sections.rights.access.title"), text: t("legal.privacy.sections.rights.access.text") },
                { subtitle: t("legal.privacy.sections.rights.correction.title"), text: t("legal.privacy.sections.rights.correction.text") },
                { subtitle: t("legal.privacy.sections.rights.deletion.title"), text: t("legal.privacy.sections.rights.deletion.text") },
                { subtitle: t("legal.privacy.sections.rights.portability.title"), text: t("legal.privacy.sections.rights.portability.text") },
                { subtitle: t("legal.privacy.sections.rights.objection.title"), text: t("legal.privacy.sections.rights.objection.text") }
            ]
        },
        {
            icon: Shield,
            title: t("legal.privacy.sections.cookies.title"),
            content: [
                { subtitle: t("legal.privacy.sections.cookies.required.title"), text: t("legal.privacy.sections.cookies.required.text") },
                { subtitle: t("legal.privacy.sections.cookies.analytics.title"), text: t("legal.privacy.sections.cookies.analytics.text") },
                { subtitle: t("legal.privacy.sections.cookies.preferences.title"), text: t("legal.privacy.sections.cookies.preferences.text") }
            ]
        }
    ];

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto z-10">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 mb-6">
                        <Shield className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">{t("legal.privacy.title")}</h1>
                    <p className="text-lg text-[#E5E7EB]/60">{t("legal.privacy.lastUpdate")}</p>
                </div>

                {/* Intro */}
                <div className="glass-premium p-8 rounded-3xl mb-8">
                    <p className="text-lg text-[#E5E7EB]/80 leading-relaxed">
                        {t("legal.privacy.intro")}
                    </p>
                </div>

                {/* Sections */}
                <div className="space-y-6">
                    {sections.map((section, idx) => (
                        <div key={idx} className="glass-premium p-8 rounded-3xl">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 border border-purple-500/30">
                                    <section.icon className="w-6 h-6 text-purple-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                            </div>
                            <div className="space-y-6 pl-16">
                                {section.content.map((item, itemIdx) => (
                                    <div key={itemIdx}>
                                        <h3 className="text-lg font-semibold text-emerald-400 mb-2">{item.subtitle}</h3>
                                        <p className="text-[#E5E7EB]/70 leading-relaxed">{item.text}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Contact */}
                <div className="mt-8 glass-premium p-8 rounded-3xl">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
                            <Mail className="w-6 h-6 text-cyan-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white">{t("legal.privacy.sections.contact.title")}</h2>
                    </div>
                    <div className="pl-16">
                        <p className="text-[#E5E7EB]/70 leading-relaxed mb-4">
                            {t("legal.privacy.sections.contact.text")}
                        </p>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <p className="text-white font-medium">{t("legal.privacy.sections.contact.email")}</p>
                            <p className="text-[#E5E7EB]/60 text-sm mt-2">{t("legal.privacy.sections.contact.response")}</p>
                        </div>
                    </div>
                </div>
            </div>
            <Footer />
        </main>
    );
}
