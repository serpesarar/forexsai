"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { Users, MapPin, Briefcase, Code, Brain, BarChart3, Rocket, Heart, Coffee, Zap, Globe, Clock } from "lucide-react";

const benefits = [
    { icon: Globe, title: "Uzaktan Çalışma", description: "Dünyanın her yerinden çalışabilirsiniz" },
    { icon: Clock, title: "Esnek Saatler", description: "Kendi çalışma saatlerinizi belirleyin" },
    { icon: Rocket, title: "Hızlı Büyüme", description: "Startup dinamizmi ile kariyer gelişimi" },
    { icon: Brain, title: "Sürekli Öğrenme", description: "AI ve fintech alanında gelişim fırsatları" },
    { icon: Heart, title: "Sağlık Sigortası", description: "Kapsamlı özel sağlık sigortası" },
    { icon: Coffee, title: "Ekipman Desteği", description: "Çalışma ekipmanı ve home office desteği" },
];

const openPositions = [
    {
        title: "Senior Full-Stack Developer",
        department: "Engineering",
        location: "Remote (Turkey)",
        type: "Full-time",
        icon: Code,
        color: "cyan",
        description: "Next.js, Python ve AI entegrasyonları konusunda deneyimli full-stack geliştirici arıyoruz.",
        requirements: [
            "5+ yıl full-stack geliştirme deneyimi",
            "React/Next.js ve Python (FastAPI) uzmanlığı",
            "PostgreSQL ve NoSQL veritabanları deneyimi",
            "CI/CD ve cloud platformları (AWS/GCP) bilgisi"
        ]
    },
    {
        title: "Machine Learning Engineer",
        department: "AI & Data",
        location: "Remote (Turkey)",
        type: "Full-time",
        icon: Brain,
        color: "purple",
        description: "Finansal tahmin modelleri geliştirmek için ML mühendisi arıyoruz.",
        requirements: [
            "3+ yıl ML/DL deneyimi",
            "Python, TensorFlow/PyTorch uzmanlığı",
            "Zaman serisi analizi ve tahmin modelleri",
            "Finans/trading bilgisi tercih sebebi"
        ]
    },
    {
        title: "Quantitative Analyst",
        department: "Research",
        location: "Remote (Turkey)",
        type: "Full-time",
        icon: BarChart3,
        color: "emerald",
        description: "Trading stratejileri geliştirmek ve backtest yapmak için quant analist arıyoruz.",
        requirements: [
            "Finans, Matematik veya ilgili alanda lisans",
            "Python ile istatistiksel analiz deneyimi",
            "Teknik analiz ve algoritmik trading bilgisi",
            "Finansal piyasalara güçlü ilgi"
        ]
    }
];

const colorClasses = {
    cyan: {
        bg: "from-cyan-500/20 to-blue-500/20",
        border: "border-cyan-500/30",
        text: "text-cyan-400",
        badge: "bg-cyan-500/20 text-cyan-400"
    },
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
    }
};

export default function CareersPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto z-10">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 mb-6">
                        <Users className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Kariyer</h1>
                    <p className="text-lg text-[#E5E7EB]/60 max-w-2xl mx-auto">
                        AI destekli finansal analiz platformunun geleceğini birlikte inşa edelim
                    </p>
                </div>

                {/* Mission Statement */}
                <div className="glass-premium p-8 rounded-3xl mb-16 text-center">
                    <h2 className="text-2xl font-bold text-white mb-4">Misyonumuz</h2>
                    <p className="text-lg text-[#E5E7EB]/70 max-w-3xl mx-auto leading-relaxed">
                        ForexsAi olarak, yapay zeka ve makine öğrenmesi teknolojilerini kullanarak bireysel yatırımcılara 
                        kurumsal düzeyde analiz araçları sunmayı hedefliyoruz. Ekibimize katılarak fintech sektörünün 
                        geleceğini şekillendirmeye katkıda bulunun.
                    </p>
                </div>

                {/* Benefits */}
                <div className="mb-16">
                    <h2 className="text-2xl font-bold text-white text-center mb-8">Neden ForexsAi?</h2>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {benefits.map((benefit, idx) => (
                            <div key={idx} className="glass-premium p-6 rounded-2xl flex items-start gap-4">
                                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex-shrink-0">
                                    <benefit.icon className="w-6 h-6 text-indigo-400" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-1">{benefit.title}</h3>
                                    <p className="text-sm text-[#E5E7EB]/60">{benefit.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Open Positions */}
                <div className="mb-16">
                    <h2 className="text-2xl font-bold text-white text-center mb-8">Açık Pozisyonlar</h2>
                    <div className="space-y-6">
                        {openPositions.map((position, idx) => {
                            const colors = colorClasses[position.color as keyof typeof colorClasses];
                            return (
                                <div key={idx} className="glass-premium p-8 rounded-3xl hover:border-white/20 transition-all">
                                    <div className="flex flex-col lg:flex-row lg:items-start gap-6">
                                        <div className={`flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br ${colors.bg} border ${colors.border} flex-shrink-0`}>
                                            <position.icon className={`w-8 h-8 ${colors.text}`} />
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex flex-wrap items-center gap-3 mb-3">
                                                <h3 className="text-xl font-bold text-white">{position.title}</h3>
                                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colors.badge}`}>
                                                    {position.department}
                                                </span>
                                            </div>
                                            <div className="flex flex-wrap items-center gap-4 text-sm text-[#E5E7EB]/60 mb-4">
                                                <span className="flex items-center gap-1">
                                                    <MapPin className="w-4 h-4" />
                                                    {position.location}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <Briefcase className="w-4 h-4" />
                                                    {position.type}
                                                </span>
                                            </div>
                                            <p className="text-[#E5E7EB]/70 mb-4">{position.description}</p>
                                            <div className="space-y-2">
                                                <p className="text-sm font-semibold text-white">Gereksinimler:</p>
                                                <ul className="grid md:grid-cols-2 gap-2">
                                                    {position.requirements.map((req, reqIdx) => (
                                                        <li key={reqIdx} className="flex items-start gap-2 text-sm text-[#E5E7EB]/60">
                                                            <Zap className={`w-4 h-4 ${colors.text} flex-shrink-0 mt-0.5`} />
                                                            {req}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                        <div className="lg:flex-shrink-0">
                                            <a
                                                href="mailto:careers@forexsai.com"
                                                className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r ${colors.bg} border ${colors.border} ${colors.text} font-semibold hover:opacity-80 transition-opacity`}
                                            >
                                                Başvur
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* No Matching Position */}
                <div className="glass-premium p-8 rounded-3xl text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">Aradığınız Pozisyon Yok mu?</h2>
                    <p className="text-[#E5E7EB]/60 mb-6 max-w-lg mx-auto">
                        Yetenekli profesyonellerle her zaman tanışmak isteriz. CV'nizi bize gönderin, 
                        uygun bir pozisyon açıldığında sizinle iletişime geçelim.
                    </p>
                    <a
                        href="mailto:careers@forexsai.com"
                        className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold hover:opacity-90 transition-opacity"
                    >
                        <Briefcase className="w-5 h-5" />
                        CV Gönder
                    </a>
                    <p className="text-sm text-[#E5E7EB]/40 mt-4">careers@forexsai.com</p>
                </div>
            </div>
            <Footer />
        </main>
    );
}
