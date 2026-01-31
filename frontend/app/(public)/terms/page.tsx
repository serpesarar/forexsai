"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { FileText, CheckCircle, XCircle, Scale, CreditCard, Ban, RefreshCw, Gavel, Globe } from "lucide-react";

export default function TermsPage() {
    const { t } = useI18n();

    const sections = [
        {
            icon: CheckCircle,
            title: t("legal.terms.sections.service.title"),
            content: [
                { subtitle: t("legal.terms.sections.service.description.title"), text: t("legal.terms.sections.service.description.text") },
                { subtitle: t("legal.terms.sections.service.acceptance.title"), text: t("legal.terms.sections.service.acceptance.text") },
                { subtitle: t("legal.terms.sections.service.age.title"), text: t("legal.terms.sections.service.age.text") }
            ]
        },
        {
            icon: Scale,
            title: t("legal.terms.sections.disclaimer.title"),
            content: [
                { subtitle: t("legal.terms.sections.disclaimer.notAdvice.title"), text: t("legal.terms.sections.disclaimer.notAdvice.text") },
                { subtitle: t("legal.terms.sections.disclaimer.noGuarantee.title"), text: t("legal.terms.sections.disclaimer.noGuarantee.text") },
                { subtitle: t("legal.terms.sections.disclaimer.liability.title"), text: t("legal.terms.sections.disclaimer.liability.text") }
            ]
        },
        {
            icon: Ban,
            title: t("legal.terms.sections.prohibited.title"),
            content: [
                { subtitle: t("legal.terms.sections.prohibited.automation.title"), text: t("legal.terms.sections.prohibited.automation.text") },
                { subtitle: t("legal.terms.sections.prohibited.sharing.title"), text: t("legal.terms.sections.prohibited.sharing.text") },
                { subtitle: t("legal.terms.sections.prohibited.abuse.title"), text: t("legal.terms.sections.prohibited.abuse.text") },
                { subtitle: t("legal.terms.sections.prohibited.commercial.title"), text: t("legal.terms.sections.prohibited.commercial.text") }
            ]
        },
        {
            icon: CreditCard,
            title: t("legal.terms.sections.payments.title"),
            content: [
                { subtitle: t("legal.terms.sections.payments.free.title"), text: t("legal.terms.sections.payments.free.text") },
                { subtitle: t("legal.terms.sections.payments.premium.title"), text: t("legal.terms.sections.payments.premium.text") },
                { subtitle: t("legal.terms.sections.payments.refund.title"), text: t("legal.terms.sections.payments.refund.text") }
            ]
        },
        {
            icon: RefreshCw,
            title: t("legal.terms.sections.account.title"),
            content: [
                { subtitle: t("legal.terms.sections.account.security.title"), text: t("legal.terms.sections.account.security.text") },
                { subtitle: t("legal.terms.sections.account.suspension.title"), text: t("legal.terms.sections.account.suspension.text") },
                { subtitle: t("legal.terms.sections.account.deletion.title"), text: t("legal.terms.sections.account.deletion.text") }
            ]
        },
        {
            icon: FileText,
            title: t("legal.terms.sections.ip.title"),
            content: [
                { subtitle: t("legal.terms.sections.ip.content.title"), text: t("legal.terms.sections.ip.content.text") },
                { subtitle: t("legal.terms.sections.ip.license.title"), text: t("legal.terms.sections.ip.license.text") },
                { subtitle: t("legal.terms.sections.ip.feedback.title"), text: t("legal.terms.sections.ip.feedback.text") }
            ]
        },
        {
            icon: Gavel,
            title: t("legal.terms.sections.disputes.title"),
            content: [
                { subtitle: t("legal.terms.sections.disputes.law.title"), text: t("legal.terms.sections.disputes.law.text") },
                { subtitle: t("legal.terms.sections.disputes.jurisdiction.title"), text: t("legal.terms.sections.disputes.jurisdiction.text") },
                { subtitle: t("legal.terms.sections.disputes.mediation.title"), text: t("legal.terms.sections.disputes.mediation.text") }
            ]
        },
        {
            icon: Globe,
            title: t("legal.terms.sections.changes.title"),
            content: [
                { subtitle: t("legal.terms.sections.changes.modifications.title"), text: t("legal.terms.sections.changes.modifications.text") },
                { subtitle: t("legal.terms.sections.changes.continued.title"), text: t("legal.terms.sections.changes.continued.text") },
                { subtitle: t("legal.terms.sections.changes.validity.title"), text: t("legal.terms.sections.changes.validity.text") }
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
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 mb-6">
                        <FileText className="w-10 h-10 text-indigo-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">{t("legal.terms.title")}</h1>
                    <p className="text-lg text-[#E5E7EB]/60">{t("legal.terms.lastUpdate")}</p>
                </div>

                {/* Important Notice */}
                <div className="glass-premium p-8 rounded-3xl mb-8 border-l-4 border-amber-500">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                            <Scale className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-amber-400 mb-2">{t("legal.terms.warning.title")}</h3>
                            <p className="text-[#E5E7EB]/70 leading-relaxed">
                                {t("legal.terms.warning.text")}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Sections */}
                <div className="space-y-6">
                    {sections.map((section, idx) => (
                        <div key={idx} className="glass-premium p-8 rounded-3xl">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                                    <section.icon className="w-6 h-6 text-indigo-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                            </div>
                            <div className="space-y-6 pl-16">
                                {section.content.map((item, itemIdx) => (
                                    <div key={itemIdx}>
                                        <h3 className="text-lg font-semibold text-cyan-400 mb-2">{item.subtitle}</h3>
                                        <p className="text-[#E5E7EB]/70 leading-relaxed">{item.text}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Acceptance */}
                <div className="mt-8 glass-premium p-8 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-4 mb-4">
                        <CheckCircle className="w-8 h-8 text-emerald-400" />
                        <h2 className="text-xl font-bold text-white">{t("legal.terms.acceptance.title")}</h2>
                    </div>
                    <p className="text-[#E5E7EB]/70 leading-relaxed">
                        {t("legal.terms.acceptance.text")}
                    </p>
                </div>
            </div>
            <Footer />
        </main>
    );
}
