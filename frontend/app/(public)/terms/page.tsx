"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

const sections = [
    {
        tag: "01",
        title: "Service Description",
        items: [
            { h: "What ForexsAI Is", p: "An AI-powered market analysis platform providing trading signals, pattern detection, and sentiment analysis for educational and informational purposes." },
            { h: "Acceptance of Terms", p: "By creating an account or using ForexsAI, you agree to be bound by these terms. If you do not agree, do not use the service." },
            { h: "Age Requirement", p: "You must be at least 18 years old to use ForexsAI. By using the service, you confirm you meet this requirement." },
        ],
    },
    {
        tag: "02",
        title: "Financial Disclaimer",
        items: [
            { h: "Not Financial Advice", p: "ForexsAI provides analysis for informational and educational purposes only. Nothing constitutes financial, investment, or trading advice." },
            { h: "No Guarantee of Results", p: "Past signal performance does not guarantee future results. Trading involves significant risk of loss. You may lose all capital invested." },
            { h: "User Responsibility", p: "You are solely responsible for all trading decisions. We expressly disclaim any liability for losses arising from use of our signals." },
        ],
    },
    {
        tag: "03",
        title: "Prohibited Activities",
        items: [
            { h: "No Automation / Scraping", p: "You may not use bots, scrapers, or automated tools to access the service or extract data at scale." },
            { h: "Account Sharing", p: "Accounts are non-transferable. Sharing credentials or accessing another user's account is strictly prohibited." },
            { h: "Abuse & Manipulation", p: "Any activity that disrupts service availability, attempts to circumvent security measures, or harms other users is prohibited." },
            { h: "Commercial Resale", p: "You may not resell, redistribute, or commercialize ForexsAI signals or analysis without explicit written consent." },
        ],
    },
    {
        tag: "04",
        title: "Payments",
        items: [
            { h: "Free Tier", p: "The free plan includes limited access to signals and features. No payment information is required to create a free account." },
            { h: "Pro Plan", p: "Pro subscriptions are billed monthly. Prices may change with 30 days notice. Payments processed securely via Stripe." },
            { h: "Refund Policy", p: "No refunds for partial months. If you cancel, access continues until end of billing period." },
        ],
    },
    {
        tag: "05",
        title: "Account & Termination",
        items: [
            { h: "Account Security", p: "You are responsible for maintaining the security of your credentials. Report unauthorized access immediately." },
            { h: "Suspension", p: "We may suspend or terminate accounts that violate these terms, with or without notice, at our discretion." },
            { h: "Account Deletion", p: "You may delete your account at any time from Settings. All your data will be permanently removed within 30 days." },
        ],
    },
    {
        tag: "06",
        title: "Intellectual Property",
        items: [
            { h: "Ownership", p: "All content, models, algorithms, and interfaces are the exclusive property of ForexsAI. All rights reserved." },
            { h: "Limited License", p: "You receive a limited, non-exclusive, non-transferable license to use the service for personal, non-commercial purposes." },
            { h: "Feedback", p: "Any feedback or suggestions you provide may be used by us to improve the service without obligation or compensation." },
        ],
    },
    {
        tag: "07",
        title: "Governing Law",
        items: [
            { h: "Applicable Law", p: "These terms are governed by the laws of Turkey. Any disputes shall be resolved in Turkish courts." },
            { h: "Jurisdiction", p: "You consent to the exclusive jurisdiction of courts in Istanbul, Turkey for any disputes arising from these terms." },
            { h: "Good Faith Resolution", p: "Before legal action, both parties agree to attempt good-faith resolution through direct communication." },
        ],
    },
];

export default function TermsPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-transparent text-white font-sans">
            <TopNav />

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
                {/* Hero */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }} className="mb-20">
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Legal</p>
                    <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-none">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent tracking-[0.1em]">
                            {t("legal.terms.title") || "TERMS OF SERVICE"}
                        </span>
                    </h1>
                    <p className="text-xs text-gray-600 font-light uppercase tracking-widest">{t("legal.terms.lastUpdate") || "Last updated: February 2025"}</p>
                </motion.div>

                {/* Warning */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-6 mb-8 flex gap-4"
                >
                    <span className="text-amber-400/60 text-xl mt-0.5 shrink-0">⚠</span>
                    <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-amber-400/60 mb-1.5">{t("legal.terms.warning.title") || "Important Notice"}</p>
                        <p className="text-sm text-gray-500 font-light leading-relaxed">
                            {t("legal.terms.warning.text") || "ForexsAI provides AI analysis for informational purposes only. This is NOT financial advice. Trading involves substantial risk of loss."}
                        </p>
                    </div>
                </motion.div>

                {/* Sections */}
                <div className="space-y-4">
                    {sections.map((section, i) => (
                        <motion.div
                            key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }} transition={{ delay: i * 0.05 }}
                            className="bg-white/[0.02] border border-white/6 rounded-xl p-8 hover:border-white/10 transition-colors"
                        >
                            <div className="flex items-baseline gap-4 mb-6">
                                <span className="text-xs font-mono text-gray-700">{section.tag}</span>
                                <h2 className="text-base font-light text-white uppercase tracking-[0.2em]">{section.title}</h2>
                            </div>
                            <div className="space-y-5">
                                {section.items.map((item, j) => (
                                    <div key={j} className="pl-5 border-l border-white/5">
                                        <h3 className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-1.5">{item.h}</h3>
                                        <p className="text-sm text-gray-600 font-light leading-relaxed">{item.p}</p>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Acceptance */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    className="mt-8 border border-white/6 rounded-xl p-8 bg-white/[0.02] text-center"
                >
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3">{t("legal.terms.acceptance.title") || "Acceptance"}</p>
                    <p className="text-gray-500 font-light text-sm max-w-md mx-auto leading-relaxed">
                        {t("legal.terms.acceptance.text") || "By using ForexsAI, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service."}
                    </p>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
