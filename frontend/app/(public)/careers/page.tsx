"use client";

export const dynamic = 'force-dynamic';

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

const benefits = [
    { icon: "🌍", title: "Remote First", description: "Work from anywhere in the world, on your own schedule." },
    { icon: "⚡", title: "Fast Growth", description: "Startup pace with real impact on the product." },
    { icon: "🧠", title: "Deep Learning", description: "Constant exposure to AI, ML and fintech innovation." },
    { icon: "🏥", title: "Health Cover", description: "Full private health insurance included." },
    { icon: "💻", title: "Equipment", description: "Home office setup and hardware budget provided." },
    { icon: "📈", title: "Equity", description: "Early team members get meaningful ownership." },
];

const positions = [
    {
        title: "Senior Full-Stack Engineer",
        dept: "Engineering",
        location: "Remote",
        type: "Full-time",
        color: "text-cyan-400 border-cyan-500/20",
        desc: "Build and scale the core platform using Next.js, FastAPI, and PostgreSQL.",
        req: ["5+ years full-stack experience", "Next.js / FastAPI expertise", "PostgreSQL & Redis", "CI/CD & cloud (AWS/GCP)"],
    },
    {
        title: "Machine Learning Engineer",
        dept: "AI & Data",
        location: "Remote",
        type: "Full-time",
        color: "text-purple-400 border-purple-500/20",
        desc: "Develop and improve financial prediction models trained on market time-series data.",
        req: ["3+ years ML/DL experience", "Python, LightGBM, PyTorch", "Time-series forecasting", "Finance background preferred"],
    },
    {
        title: "Quantitative Analyst",
        dept: "Research",
        location: "Remote",
        type: "Full-time",
        color: "text-amber-400 border-amber-500/20",
        desc: "Design, backtest, and optimize algorithmic trading strategies.",
        req: ["Finance or Math degree", "Statistical analysis in Python", "Algorithmic trading knowledge", "Strong market understanding"],
    },
];

export default function CareersPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-black text-white font-sans">
            <TopNav />

            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-purple-500/3 blur-3xl rounded-full" />
            </div>

            <div className="relative pt-36 pb-24 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
                {/* Hero */}
                <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="text-center mb-24">
                    <p className="text-xs uppercase tracking-[0.4em] text-gray-600 mb-4">Join the team</p>
                    <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-none">
                        <span className="bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent tracking-[0.1em]">
                            {t("careers.title") || "CAREERS"}
                        </span>
                    </h1>
                    <p className="text-gray-500 font-light text-lg max-w-xl mx-auto leading-relaxed border-l-2 border-white/10 pl-5 text-left mx-auto">
                        {t("careers.subtitle") || "We're building the future of algorithmic trading analysis. If you love markets, AI, and building things that matter — let's talk."}
                    </p>
                </motion.div>

                {/* Mission */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    className="bg-white/[0.02] border border-white/6 rounded-2xl p-10 mb-20 text-center"
                >
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-4">Mission</p>
                    <p className="text-xl font-light text-gray-300 max-w-3xl mx-auto leading-relaxed">
                        {t("careers.mission.text") || "To democratize institutional-grade trading intelligence for independent traders worldwide. Every line of code makes markets more fair."}
                    </p>
                </motion.div>

                {/* Benefits */}
                <div className="mb-20">
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3 text-center">Why us</p>
                    <h2 className="text-2xl font-light text-white text-center mb-12">{t("careers.whyUs") || "What you get"}</h2>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {benefits.map((b, i) => (
                            <motion.div
                                key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                                className="bg-white/[0.03] border border-white/6 rounded-xl p-6 hover:border-white/12 transition-colors"
                            >
                                <span className="text-2xl mb-4 block">{b.icon}</span>
                                <h3 className="text-sm uppercase tracking-[0.2em] text-white mb-2 font-light">{b.title}</h3>
                                <p className="text-xs text-gray-600 font-light leading-relaxed">{b.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Positions */}
                <div className="mb-20">
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3 text-center">Open roles</p>
                    <h2 className="text-2xl font-light text-white text-center mb-12">{t("careers.openPositions") || "Open Positions"}</h2>
                    <div className="space-y-4">
                        {positions.map((p, i) => (
                            <motion.div
                                key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                                className={`bg-white/[0.03] border rounded-xl p-8 hover:bg-white/[0.05] transition-all ${p.color.split(" ")[1]}`}
                            >
                                <div className="flex flex-col lg:flex-row lg:items-start gap-6">
                                    <div className="flex-1">
                                        <div className="flex flex-wrap items-center gap-4 mb-3">
                                            <h3 className="text-lg font-light text-white">{p.title}</h3>
                                            <span className={`text-xs uppercase tracking-widest ${p.color.split(" ")[0]}`}>{p.dept}</span>
                                        </div>
                                        <div className="flex gap-4 text-xs text-gray-600 uppercase tracking-wider mb-4">
                                            <span>◆ {p.location}</span>
                                            <span>◆ {p.type}</span>
                                        </div>
                                        <p className="text-sm text-gray-500 font-light mb-5 leading-relaxed border-l border-white/8 pl-4">{p.desc}</p>
                                        <div className="grid md:grid-cols-2 gap-2">
                                            {p.req.map((r, j) => (
                                                <div key={j} className="flex items-center gap-2 text-xs text-gray-600">
                                                    <span className={`text-[8px] ${p.color.split(" ")[0]}`}>◆</span>
                                                    {r}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="shrink-0">
                                        <a
                                            href="mailto:careers@forexsai.com"
                                            className="inline-flex items-center gap-2 px-6 py-3 rounded-sm bg-white/[0.04] border border-white/8 hover:bg-white/[0.08] hover:border-white/16 text-gray-400 hover:text-white transition-all text-xs uppercase tracking-widest"
                                        >
                                            Apply →
                                        </a>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Open application */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    className="text-center border border-white/6 rounded-2xl p-12 bg-white/[0.02]"
                >
                    <p className="text-xs uppercase tracking-[0.3em] text-gray-600 mb-3">Don&apos;t see your role?</p>
                    <h2 className="text-2xl font-light text-white mb-4">{t("careers.noPosition.title") || "Open Application"}</h2>
                    <p className="text-gray-600 font-light mb-8 max-w-md mx-auto text-sm leading-relaxed">
                        {t("careers.noPosition.text") || "If you're passionate about markets, AI, and building great products — we want to hear from you."}
                    </p>
                    <a
                        href="mailto:careers@forexsai.com"
                        className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-gray-700 via-gray-500 to-gray-700 border border-gray-500/40 rounded-sm text-white text-xs uppercase tracking-widest hover:shadow-[0_0_20px_rgba(200,200,200,0.15)] transition-all"
                    >
                        careers@forexsai.com
                    </a>
                </motion.div>
            </div>

            <Footer />
        </main>
    );
}
