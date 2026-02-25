"use client";

export const dynamic = 'force-dynamic';

import Link from "next/link";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

function PriceCard({
    title, price, period, features, cta, href,
    highlight = false, delay = 0
}: {
    title: string; price: string; period?: string; features: string[];
    cta: string; href: string; highlight?: boolean; delay?: number
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay }}
            className={`relative p-8 rounded-2xl border flex flex-col h-full ${highlight
                    ? "bg-white/[0.05] border-white/15 shadow-[0_0_40px_rgba(6,182,212,0.06)]"
                    : "bg-white/[0.02] border-white/6"
                }`}
        >
            {highlight && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-white/10 border border-white/20 text-white text-xs uppercase tracking-widest rounded-full backdrop-blur-md">
                    Most Popular
                </div>
            )}

            <div className="mb-8">
                <p className={`text-xs uppercase tracking-[0.3em] mb-4 ${highlight ? "text-cyan-400/70" : "text-gray-600"}`}>
                    {title}
                </p>
                <div className="flex items-baseline gap-1">
                    <span className="text-5xl font-bold bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">{price}</span>
                    {period && <span className="text-gray-600 font-light ml-2 text-sm">{period}</span>}
                </div>
            </div>

            <ul className="space-y-4 mb-10 flex-1">
                {features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-gray-500 font-light">
                        <span className={`mt-1 text-[8px] ${highlight ? "text-cyan-400/60" : "text-gray-600"}`}>◆</span>
                        <span>{feature}</span>
                    </li>
                ))}
            </ul>

            <Link href={href}>
                <button className={`w-full py-3.5 rounded-sm transition-all duration-300 uppercase tracking-widest text-xs font-medium ${highlight
                        ? "bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 text-white shadow-[0_0_15px_rgba(192,192,192,0.2)] hover:shadow-[0_0_25px_rgba(192,192,192,0.4)]"
                        : "bg-white/[0.03] border border-white/8 text-gray-400 hover:bg-white/[0.06] hover:text-white"
                    }`}>
                    {cta}
                </button>
            </Link>
        </motion.div>
    );
}

export default function PricingPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-black text-white font-sans">
            <TopNav />

            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-cyan-500/3 blur-3xl rounded-full" />
            </div>

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
                <div className="text-center mb-20">
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Simple Pricing</p>
                    <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-[0.1em]">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent">
                            {t("pricingPage.title") || "Choose Your Plan"}
                        </span>
                    </h1>
                    <p className="text-gray-500 font-light text-lg max-w-md mx-auto">
                        {t("pricingPage.subtitle") || "Start free. Upgrade when you need more power."}
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
                    <PriceCard
                        title={t("pricingPage.free.title") || "Free"}
                        price={t("pricingPage.free.price") || "€0"}
                        period={t("pricingPage.free.period") || "forever"}
                        features={Array.isArray(t("pricingPage.free.features")) ? (t("pricingPage.free.features") as string[]) : [
                            "Live NASDAQ & XAUUSD signals",
                            "Basic AI analysis (3 models)",
                            "Real-time price ticker",
                            "Pattern detection (limited)",
                            "Community access",
                        ]}
                        cta={t("pricingPage.free.cta") || "Get Started Free"}
                        href="/signup"
                        highlight={true}
                        delay={0.1}
                    />
                    <PriceCard
                        title={t("pricingPage.pro.title") || "Pro"}
                        price={t("pricingPage.pro.price") || "€29"}
                        period="/month"
                        features={Array.isArray(t("pricingPage.pro.features")) ? (t("pricingPage.pro.features") as string[]) : [
                            "Everything in Free",
                            "DAX & US Oil signals",
                            "Claude AI news sentiment",
                            "Multi-timeframe matrix (M1–H4)",
                            "Whale & COT tracker",
                            "Harmonic pattern visualizer",
                            "Signal performance analytics",
                            "Priority support",
                        ]}
                        cta={t("pricingPage.pro.cta") || "Upgrade to Pro"}
                        href="/signup"
                        highlight={false}
                        delay={0.2}
                    />
                </div>

                {/* FAQ */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="mt-20 text-center"
                >
                    <p className="text-gray-700 text-sm font-light tracking-wide">
                        Questions?{" "}
                        <Link href="/about" className="text-gray-500 hover:text-white transition-colors">
                            Learn more about ForexsAI →
                        </Link>
                    </p>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
