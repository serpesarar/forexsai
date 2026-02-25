"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

const riskSections = [
    {
        id: "01",
        title: "General Market Risk",
        items: [
            { h: "Capital Risk", p: "Trading financial instruments involves substantial risk. You can lose all of your invested capital. Never trade with money you cannot afford to lose." },
            { h: "Leverage Risk", p: "Leveraged products amplify both gains and losses. A small adverse move can result in losses exceeding your initial deposit." },
            { h: "Volatility", p: "Financial markets can move rapidly and unpredictably. News events, economic data, and geopolitical developments can cause extreme price swings." },
        ],
    },
    {
        id: "02",
        title: "AI Model Risk",
        items: [
            { h: "Model Errors", p: "AI models can generate incorrect signals or fail to account for unprecedented market conditions. No model is infallible." },
            { h: "Historical Limitations", p: "Past performance of AI signals does not guarantee future results. Market regimes change and historical patterns may not repeat." },
            { h: "Technical Failures", p: "System outages, data feed delays, or API failures may affect signal delivery. Always have manual risk management in place." },
        ],
    },
    {
        id: "03",
        title: "Not Financial Advice",
        items: [
            { h: "Informational Only", p: "All signals, analysis, and content on ForexsAI are for informational and educational purposes only. Nothing constitutes financial advice." },
            { h: "Not Licensed", p: "ForexsAI is not a licensed investment advisor, broker, or financial institution. We do not hold any regulatory licenses for financial advice." },
            { h: "Your Responsibility", p: "All trading decisions are solely your responsibility. Consult a qualified financial advisor before making investment decisions." },
        ],
    },
    {
        id: "04",
        title: "Market-Specific Risks",
        items: [
            { h: "NASDAQ / US Equities", p: "Sensitive to Federal Reserve policy, earnings reports, tech sector news, and geopolitical risk. High correlation to risk-off/risk-on cycles." },
            { h: "XAU/USD (Gold)", p: "Affected by USD strength, inflation expectations, central bank buying, and safe-haven demand. Can move sharply on CPI or NFP data." },
            { h: "Liquidity Risk", p: "During off-hours or market open/close, spreads widen and liquidity decreases. Signals executed during these periods carry higher slippage risk." },
        ],
    },
];

export default function RiskPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-black text-white font-sans">
            <TopNav />

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
                {/* Hero */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }} className="mb-20">
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Legal</p>
                    <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-none">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent tracking-[0.1em]">
                            {t("legal.risk.title") || "RISK DISCLOSURE"}
                        </span>
                    </h1>
                    <p className="text-xs text-gray-600 font-light uppercase tracking-widest">{t("legal.risk.subtitle") || "Please read carefully before using our platform"}</p>
                </motion.div>

                {/* Critical banner */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="bg-red-500/5 border border-red-500/20 rounded-xl p-6 mb-8"
                >
                    <div className="flex gap-4">
                        <span className="text-red-400 text-xl shrink-0 mt-0.5">⚠</span>
                        <div>
                            <p className="text-xs uppercase tracking-[0.2em] text-red-400/60 mb-1.5">{t("legal.risk.critical.title") || "Critical Warning"}</p>
                            <p className="text-sm text-gray-500 font-light leading-relaxed">
                                {t("legal.risk.critical.text") || "Trading in financial markets carries a high level of risk and may not be suitable for all investors. The possibility exists that you could sustain a loss of some or all of your initial investment."}
                            </p>
                        </div>
                    </div>
                </motion.div>

                {/* Sections */}
                <div className="space-y-4">
                    {riskSections.map((section, i) => (
                        <motion.div
                            key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }} transition={{ delay: i * 0.05 }}
                            className="bg-white/[0.02] border border-white/6 rounded-xl p-8 hover:border-white/10 transition-colors"
                        >
                            <div className="flex items-baseline gap-4 mb-6">
                                <span className="text-xs font-mono text-gray-700">{section.id}</span>
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

                {/* Acknowledgment */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    className="mt-8 border border-red-500/15 rounded-xl p-8 bg-red-500/3"
                >
                    <p className="text-xs uppercase tracking-[0.3em] text-red-400/50 mb-3">{t("legal.risk.acknowledgment.title") || "Acknowledgment"}</p>
                    <p className="text-sm text-gray-500 font-light leading-relaxed">
                        {t("legal.risk.acknowledgment.intro") || "By using ForexsAI, you acknowledge that you have read and understood these risk disclosures, and that trading involves substantial risk of financial loss."}
                    </p>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
