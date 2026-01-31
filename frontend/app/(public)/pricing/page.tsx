"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { Check, Star } from "lucide-react";
import { AnimatedButton } from "@/components/welcome/ui/Button";

function PriceCard({
    title,
    price,
    period,
    features,
    cta,
    highlight = false,
    delay = 0
}: {
    title: string;
    price: string;
    period?: string;
    features: string[];
    cta: string;
    highlight?: boolean;
    delay?: number
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay }}
            className={`relative p-8 rounded-3xl border backdrop-blur-sm flex flex-col h-full ${highlight
                    ? "bg-white/10 border-emerald-500/50 shadow-[0_0_50px_rgba(16,185,129,0.1)]"
                    : "bg-white/5 border-white/10"
                }`}
        >
            {highlight && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-emerald-500 text-black text-xs font-bold rounded-full uppercase tracking-wider shadow-lg">
                    Best Value
                </div>
            )}

            <div className="mb-8">
                <h3 className={`text-lg font-medium mb-4 ${highlight ? "text-emerald-400" : "text-white/60"}`}>{title}</h3>
                <div className="flex items-baseline">
                    <span className="text-5xl font-bold text-white tracking-tight">{price}</span>
                    {period && <span className="text-white/40 ml-2">{period}</span>}
                </div>
            </div>

            <ul className="space-y-4 mb-10 flex-1">
                {features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-[#E5E7EB]/80">
                        <Check className={`w-5 h-5 shrink-0 ${highlight ? "text-emerald-400" : "text-white/30"}`} />
                        <span>{feature}</span>
                    </li>
                ))}
            </ul>

            <AnimatedButton
                href={highlight ? "/signup" : "#"}
                variant={highlight ? "primary" : "secondary"}
                className="w-full justify-center"
            >
                {cta}
            </AnimatedButton>
        </motion.div>
    );
}

export default function PricingPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto z-10">
                <div className="text-center mb-20">
                    <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                        {t("pricingPage.title")}
                    </h1>
                    <p className="text-xl text-[#E5E7EB]/70">
                        {t("pricingPage.subtitle")}
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    <PriceCard
                        title={t("pricingPage.free.title")}
                        price={t("pricingPage.free.price")}
                        period={t("pricingPage.free.period")}
                        features={t("pricingPage.free.features") as unknown as string[]} // Type assertion needed for array from translation
                        cta={t("pricingPage.free.cta")}
                        highlight={true}
                        delay={0.1}
                    />
                    <PriceCard
                        title={t("pricingPage.pro.title")}
                        price={t("pricingPage.pro.price")}
                        features={t("pricingPage.pro.features") as unknown as string[]}
                        cta={t("pricingPage.pro.cta")}
                        highlight={false}
                        delay={0.2}
                    />
                </div>
            </div>

            <Footer />
        </main>
    );
}
