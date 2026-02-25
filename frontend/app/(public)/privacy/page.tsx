"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

const sections = [
    {
        tag: "01",
        title: "Data We Collect",
        items: [
            { h: "Account Information", p: "Email address and optional profile name when you register. We never collect payment details directly — handled by Stripe." },
            { h: "Usage Analytics", p: "Anonymous page views, feature interactions, and session duration to improve the product. No personal identifiers." },
            { h: "Technical Data", p: "Browser type, IP address (anonymized), and device type solely for security and fraud prevention." },
        ],
    },
    {
        tag: "02",
        title: "How We Use Data",
        items: [
            { h: "Service Delivery", p: "Providing AI-powered trading analysis signals, managing your account, and personalizing the experience." },
            { h: "Communications", p: "Sending product updates, security alerts, and support responses. You can opt out at any time." },
            { h: "Improvements", p: "Aggregated analytics to improve model accuracy and user experience. Never resold." },
        ],
    },
    {
        tag: "03",
        title: "Data Security",
        items: [
            { h: "Encryption", p: "All data transmitted via TLS 1.3. Passwords stored with bcrypt hashing. Database encrypted at rest." },
            { h: "Infrastructure", p: "Hosted on Railway (EU region) and Supabase with enterprise-grade security and access controls." },
            { h: "Access Controls", p: "Only authorized team members access production data. MFA required for all admin operations." },
        ],
    },
    {
        tag: "04",
        title: "Third Parties",
        items: [
            { h: "Service Providers", p: "Supabase (database), Railway (hosting), Anthropic (AI analysis), EODHD (market data). All GDPR compliant." },
            { h: "Legal Requirements", p: "We may disclose data if legally required by court order or regulatory authority." },
            { h: "No Data Sales", p: "We never sell, rent, or trade your personal data. Period." },
        ],
    },
    {
        tag: "05",
        title: "Your Rights",
        items: [
            { h: "Access & Portability", p: "Request a full export of your personal data at any time by emailing privacy@forexsai.com." },
            { h: "Correction", p: "Update inaccurate information directly in your profile settings or contact us." },
            { h: "Deletion", p: 'Delete your account and all associated data from Settings → Account → Delete Account. Takes effect within 30 days.' },
        ],
    },
    {
        tag: "06",
        title: "Cookies",
        items: [
            { h: "Essential Cookies", p: "Session authentication. These cannot be disabled as they're required for the service to function." },
            { h: "Analytics Cookies", p: "Anonymous usage analytics (Plausible Analytics — no cross-site tracking). Opt-out available." },
            { h: "Preferences", p: "Language and theme preferences stored locally in your browser." },
        ],
    },
];

export default function PrivacyPage() {
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
                            {t("legal.privacy.title") || "PRIVACY POLICY"}
                        </span>
                    </h1>
                    <p className="text-xs text-gray-600 font-light uppercase tracking-widest">{t("legal.privacy.lastUpdate") || "Last updated: February 2025"}</p>
                </motion.div>

                {/* Intro */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="bg-white/[0.03] border border-white/8 rounded-xl p-8 mb-8"
                >
                    <p className="text-gray-400 font-light leading-relaxed text-base border-l-2 border-cyan-500/30 pl-5">
                        {t("legal.privacy.intro") || "ForexsAI is committed to protecting your privacy. This policy explains exactly what data we collect, why we collect it, and the controls you have over it."}
                    </p>
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

                {/* Contact */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    className="mt-8 border border-white/6 rounded-xl p-8 bg-white/[0.02] text-center"
                >
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3">{t("legal.privacy.sections.contact.title") || "Contact"}</p>
                    <p className="text-gray-500 font-light text-sm mb-6 max-w-md mx-auto">
                        {t("legal.privacy.sections.contact.text") || "For privacy-related requests, data exports, or deletion requests:"}
                    </p>
                    <a href="mailto:privacy@forexsai.com" className="text-gray-300 hover:text-white transition-colors font-light tracking-wide text-sm border-b border-white/20 pb-0.5">
                        privacy@forexsai.com
                    </a>
                    <p className="text-xs text-gray-700 mt-4">{t("legal.privacy.sections.contact.response") || "We respond within 48 hours."}</p>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
