"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { BookOpen, Clock, ArrowRight, TrendingUp, Brain, BarChart3, Sparkles } from "lucide-react";
import Link from "next/link";

const blogPosts = [
    {
        id: 1,
        title: "Yapay Zeka ile Teknik Analiz: Geleceğin Ticaret Stratejileri",
        excerpt: "Makine öğrenmesi modellerinin finansal piyasalarda nasıl kullanıldığını ve geleneksel teknik analizden farkını keşfedin.",
        category: "AI & Trading",
        readTime: "8 dk",
        date: "28 Ocak 2025",
        icon: Brain,
        color: "purple",
        featured: true
    },
    {
        id: 2,
        title: "NASDAQ-100: Teknoloji Hisselerine Yatırım Rehberi",
        excerpt: "ABD'nin en büyük teknoloji şirketlerini içeren NASDAQ-100 endeksi hakkında bilmeniz gereken her şey.",
        category: "Piyasa Analizi",
        readTime: "6 dk",
        date: "25 Ocak 2025",
        icon: TrendingUp,
        color: "emerald"
    },
    {
        id: 3,
        title: "Altın Yatırımı: XAU/USD Analiz Teknikleri",
        excerpt: "Güvenli liman varlığı olarak altının temel ve teknik analiz yöntemlerini öğrenin.",
        category: "Emtia",
        readTime: "7 dk",
        date: "22 Ocak 2025",
        icon: Sparkles,
        color: "amber"
    },
    {
        id: 4,
        title: "Risk Yönetimi: Stop-Loss ve Take-Profit Stratejileri",
        excerpt: "Profesyonel traderların kullandığı risk yönetimi teknikleri ve pozisyon boyutlandırma yöntemleri.",
        category: "Eğitim",
        readTime: "10 dk",
        date: "18 Ocak 2025",
        icon: BarChart3,
        color: "cyan"
    }
];

const colorClasses = {
    purple: {
        bg: "from-purple-500/20 to-indigo-500/20",
        border: "border-purple-500/30",
        text: "text-purple-400",
        badge: "bg-purple-500/20 text-purple-400"
    },
    emerald: {
        bg: "from-emerald-500/20 to-teal-500/20",
        border: "border-emerald-500/30",
        text: "text-emerald-400",
        badge: "bg-emerald-500/20 text-emerald-400"
    },
    amber: {
        bg: "from-amber-500/20 to-orange-500/20",
        border: "border-amber-500/30",
        text: "text-amber-400",
        badge: "bg-amber-500/20 text-amber-400"
    },
    cyan: {
        bg: "from-cyan-500/20 to-blue-500/20",
        border: "border-cyan-500/30",
        text: "text-cyan-400",
        badge: "bg-cyan-500/20 text-cyan-400"
    }
};

export default function BlogPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto z-10">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 mb-6">
                        <BookOpen className="w-10 h-10 text-indigo-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">{t("blog.title")}</h1>
                    <p className="text-lg text-[#E5E7EB]/60 max-w-2xl mx-auto">
                        {t("blog.subtitle")}
                    </p>
                </div>

                {/* Coming Soon Banner */}
                <div className="glass-premium p-8 rounded-3xl mb-12 text-center border-2 border-dashed border-indigo-500/30">
                    <Sparkles className="w-12 h-12 text-indigo-400 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-2">{t("blog.comingSoon")}</h2>
                    <p className="text-[#E5E7EB]/60 max-w-lg mx-auto">
                        {t("blog.comingSoonText")}
                    </p>
                </div>

                {/* Featured Post */}
                {blogPosts.filter(p => p.featured).map(post => {
                    const colors = colorClasses[post.color as keyof typeof colorClasses];
                    return (
                        <div key={post.id} className="glass-premium p-8 rounded-3xl mb-8 relative overflow-hidden group cursor-pointer hover:border-indigo-500/30 transition-all">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-full blur-3xl -z-10" />
                            <div className="flex flex-col md:flex-row gap-6">
                                <div className={`flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br ${colors.bg} border ${colors.border} flex-shrink-0`}>
                                    <post.icon className={`w-10 h-10 ${colors.text}`} />
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-3">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colors.badge}`}>
                                            {post.category}
                                        </span>
                                        <span className="text-xs text-[#E5E7EB]/40">{t("blog.featured")}</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-white mb-3 group-hover:text-indigo-400 transition-colors">
                                        {post.title}
                                    </h2>
                                    <p className="text-[#E5E7EB]/60 mb-4">{post.excerpt}</p>
                                    <div className="flex items-center gap-4 text-sm text-[#E5E7EB]/40">
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-4 h-4" />
                                            {post.readTime}
                                        </span>
                                        <span>{post.date}</span>
                                    </div>
                                </div>
                                <div className="flex items-center">
                                    <ArrowRight className="w-6 h-6 text-[#E5E7EB]/40 group-hover:text-indigo-400 group-hover:translate-x-2 transition-all" />
                                </div>
                            </div>
                        </div>
                    );
                })}

                {/* Post Grid */}
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {blogPosts.filter(p => !p.featured).map(post => {
                        const colors = colorClasses[post.color as keyof typeof colorClasses];
                        return (
                            <div key={post.id} className="glass-premium p-6 rounded-2xl group cursor-pointer hover:border-white/20 transition-all">
                                <div className={`flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${colors.bg} border ${colors.border} mb-4`}>
                                    <post.icon className={`w-6 h-6 ${colors.text}`} />
                                </div>
                                <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${colors.badge} mb-3`}>
                                    {post.category}
                                </span>
                                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-indigo-400 transition-colors line-clamp-2">
                                    {post.title}
                                </h3>
                                <p className="text-sm text-[#E5E7EB]/60 mb-4 line-clamp-2">{post.excerpt}</p>
                                <div className="flex items-center justify-between text-xs text-[#E5E7EB]/40">
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {post.readTime}
                                    </span>
                                    <span>{post.date}</span>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Newsletter */}
                <div className="mt-16 glass-premium p-8 rounded-3xl text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">{t("blog.newsletter.title")}</h2>
                    <p className="text-[#E5E7EB]/60 mb-6 max-w-lg mx-auto">
                        {t("blog.newsletter.subtitle")}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                        <input
                            type="email"
                            placeholder={t("blog.newsletter.placeholder") as string}
                            className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:border-indigo-500/50"
                            disabled
                        />
                        <button
                            className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold opacity-50 cursor-not-allowed"
                            disabled
                        >
                            {t("blog.newsletter.button")}
                        </button>
                    </div>
                </div>
            </div>
            <Footer />
        </main>
    );
}
