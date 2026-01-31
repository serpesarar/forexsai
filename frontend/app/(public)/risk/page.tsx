"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AlertTriangle, TrendingDown, Zap, Brain, BarChart3, Shield, XCircle, AlertOctagon } from "lucide-react";

export default function RiskPage() {
    const { t } = useI18n();

    const riskSections = [
        {
            icon: TrendingDown,
            title: "1. Genel Risk Uyarısı",
            color: "red",
            content: [
                {
                    subtitle: "1.1 Sermaye Kaybı Riski",
                    text: "Finansal piyasalarda (Forex, Emtia, Hisse Senedi Endeksleri vb.) işlem yapmak, yatırdığınız sermayenin TAMAMINI veya önemli bir kısmını kaybetme riski taşır. Asla kaybetmeyi göze alamayacağınız parayla işlem yapmayınız."
                },
                {
                    subtitle: "1.2 Kaldıraç Riski",
                    text: "Kaldıraçlı ürünler (CFD, Forex vb.) hem kazançları hem de kayıpları katlar. Küçük fiyat hareketleri bile hesap bakiyenizi önemli ölçüde etkileyebilir. Kaldıraç, yatırdığınız tutardan fazlasını kaybetmenize neden olabilir."
                },
                {
                    subtitle: "1.3 Piyasa Volatilitesi",
                    text: "Finansal piyasalar, ekonomik olaylar, jeopolitik gelişmeler, merkez bankası kararları ve beklenmedik haberler nedeniyle ani ve şiddetli fiyat hareketlerine maruz kalabilir. Bu volatilite, stop-loss emirlerinin beklenen fiyattan farklı seviyelerde gerçekleşmesine (slippage) neden olabilir."
                }
            ]
        },
        {
            icon: Brain,
            title: "2. Yapay Zeka ve Model Riskleri",
            color: "purple",
            content: [
                {
                    subtitle: "2.1 Model Hataları",
                    text: "ForexsAi tarafından kullanılan makine öğrenmesi modelleri, geçmiş veriler üzerinde eğitilmiştir. Bu modeller hatalı tahminler üretebilir ve piyasa koşulları değiştiğinde performansları düşebilir."
                },
                {
                    subtitle: "2.2 Geçmiş Performans Garantisi Değildir",
                    text: "Backtest sonuçları ve geçmiş doğruluk oranları, gelecekteki performansın garantisi veya göstergesi DEĞİLDİR. Piyasa dinamikleri sürekli değişir ve geçmişte çalışan stratejiler gelecekte başarısız olabilir."
                },
                {
                    subtitle: "2.3 Teknik Hatalar",
                    text: "Yazılım hataları, sunucu kesintileri, veri gecikmesi veya yanlış veri akışı nedeniyle analizler hatalı olabilir. Sistemin 7/24 kesintisiz çalışacağı garanti edilmemektedir."
                }
            ]
        },
        {
            icon: XCircle,
            title: "3. Yatırım Tavsiyesi Değildir",
            color: "amber",
            content: [
                {
                    subtitle: "3.1 Bilgilendirme Amaçlı",
                    text: "ForexsAi platformu tarafından sunulan TÜM analizler, tahminler, sinyaller, grafikler ve AI yorumları YALNIZCA bilgilendirme ve eğitim amaçlıdır. Bu içerikler hiçbir şekilde yatırım tavsiyesi, finansal danışmanlık veya alım-satım önerisi olarak yorumlanamaz."
                },
                {
                    subtitle: "3.2 Lisanslı Danışmanlık Değildir",
                    text: "ForexsAi, SPK (Sermaye Piyasası Kurulu) veya benzeri düzenleyici kurumlar tarafından lisanslı bir yatırım danışmanlığı şirketi DEĞİLDİR. Profesyonel yatırım kararları için lisanslı bir yatırım danışmanına başvurmanız önerilir."
                },
                {
                    subtitle: "3.3 Kişisel Sorumluluk",
                    text: "Platform üzerindeki verilere dayanarak aldığınız tüm yatırım kararları ve bunların sonuçları tamamen sizin sorumluluğunuzdadır. ForexsAi, kullanıcıların işlemlerinden kaynaklanan hiçbir kayıp veya zarardan sorumlu tutulamaz."
                }
            ]
        },
        {
            icon: BarChart3,
            title: "4. Piyasa Spesifik Riskler",
            color: "cyan",
            content: [
                {
                    subtitle: "4.1 NASDAQ-100 Riskleri",
                    text: "Teknoloji ağırlıklı bu endeks, sektörel konsantrasyon riski taşır. Teknoloji sektöründeki olumsuz gelişmeler endeksi orantısız şekilde etkileyebilir. ABD piyasa saatleri dışında likidite azalabilir."
                },
                {
                    subtitle: "4.2 Altın (XAU/USD) Riskleri",
                    text: "Altın fiyatları; dolar endeksi, faiz oranları, enflasyon beklentileri ve jeopolitik risklerden etkilenir. Kısa vadede yüksek volatilite gösterebilir. Spread'ler haber saatlerinde genişleyebilir."
                },
                {
                    subtitle: "4.3 Likidite Riski",
                    text: "Piyasa saatleri dışında, önemli haberler öncesinde/sonrasında veya tatil dönemlerinde likidite düşebilir. Bu durum, emirlerin istenilen fiyattan gerçekleşmemesine neden olabilir."
                }
            ]
        },
        {
            icon: Shield,
            title: "5. Kendinizi Koruma Yöntemleri",
            color: "emerald",
            content: [
                {
                    subtitle: "5.1 Eğitim",
                    text: "İşlem yapmadan önce finansal piyasalar, teknik analiz ve risk yönetimi hakkında yeterli bilgi edininiz. Demo hesaplarda pratik yapınız."
                },
                {
                    subtitle: "5.2 Risk Yönetimi",
                    text: "Her işlemde sermayenizin yalnızca küçük bir yüzdesini riske atınız (%1-2 önerilir). Stop-loss emirleri kullanınız. Portföyünüzü çeşitlendiriniz."
                },
                {
                    subtitle: "5.3 Duygusal Kontrol",
                    text: "Kayıpların peşinden koşmayınız. FOMO (kaçırma korkusu) ile işlem açmayınız. İşlem planınıza sadık kalınız."
                },
                {
                    subtitle: "5.4 Profesyonel Destek",
                    text: "Önemli yatırım kararları almadan önce lisanslı bir finansal danışmana danışmanız şiddetle tavsiye edilir."
                }
            ]
        }
    ];

    const colorClasses = {
        red: {
            bg: "from-red-500/20 to-rose-500/20",
            border: "border-red-500/30",
            icon: "text-red-400",
            subtitle: "text-red-400"
        },
        purple: {
            bg: "from-purple-500/20 to-indigo-500/20",
            border: "border-purple-500/30",
            icon: "text-purple-400",
            subtitle: "text-purple-400"
        },
        amber: {
            bg: "from-amber-500/20 to-orange-500/20",
            border: "border-amber-500/30",
            icon: "text-amber-400",
            subtitle: "text-amber-400"
        },
        cyan: {
            bg: "from-cyan-500/20 to-blue-500/20",
            border: "border-cyan-500/30",
            icon: "text-cyan-400",
            subtitle: "text-cyan-400"
        },
        emerald: {
            bg: "from-emerald-500/20 to-teal-500/20",
            border: "border-emerald-500/30",
            icon: "text-emerald-400",
            subtitle: "text-emerald-400"
        }
    };

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto z-10">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-red-500/20 to-rose-500/20 border border-red-500/30 mb-6 animate-pulse">
                        <AlertTriangle className="w-10 h-10 text-red-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Risk Uyarısı</h1>
                    <p className="text-lg text-[#E5E7EB]/60">Lütfen işlem yapmadan önce dikkatlice okuyunuz</p>
                </div>

                {/* Critical Warning Banner */}
                <div className="glass-premium p-6 rounded-3xl mb-8 bg-gradient-to-r from-red-500/20 to-rose-500/20 border-2 border-red-500/40">
                    <div className="flex items-center gap-4">
                        <AlertOctagon className="w-12 h-12 text-red-400 flex-shrink-0" />
                        <div>
                            <h2 className="text-xl font-bold text-red-400 mb-2">⚠️ KRİTİK UYARI</h2>
                            <p className="text-white/90 leading-relaxed">
                                Finansal piyasalarda işlem yapmak yüksek risk içerir ve yatırılan sermayenin tamamının kaybedilmesine neden olabilir. 
                                ForexsAi tarafından sunulan içerikler <strong>YATIRIM TAVSİYESİ DEĞİLDİR</strong>. 
                                Tüm işlemler tamamen kendi sorumluluğunuzdadır.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Risk Sections */}
                <div className="space-y-6">
                    {riskSections.map((section, idx) => {
                        const colors = colorClasses[section.color as keyof typeof colorClasses];
                        return (
                            <div key={idx} className="glass-premium p-8 rounded-3xl">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className={`flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${colors.bg} border ${colors.border}`}>
                                        <section.icon className={`w-6 h-6 ${colors.icon}`} />
                                    </div>
                                    <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                                </div>
                                <div className="space-y-6 pl-16">
                                    {section.content.map((item, itemIdx) => (
                                        <div key={itemIdx}>
                                            <h3 className={`text-lg font-semibold ${colors.subtitle} mb-2`}>{item.subtitle}</h3>
                                            <p className="text-[#E5E7EB]/70 leading-relaxed">{item.text}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Acknowledgment Box */}
                <div className="mt-8 glass-premium p-8 rounded-3xl bg-gradient-to-r from-red-500/10 to-amber-500/10 border-2 border-red-500/30">
                    <div className="flex items-start gap-4">
                        <AlertTriangle className="w-8 h-8 text-red-400 flex-shrink-0 mt-1" />
                        <div>
                            <h2 className="text-xl font-bold text-white mb-4">Kabul Beyanı</h2>
                            <p className="text-[#E5E7EB]/80 leading-relaxed mb-4">
                                ForexsAi platformunu kullanarak aşağıdaki hususları <strong className="text-white">OKUDUĞUNUZU, ANLADIĞINIZI VE KABUL ETTİĞİNİZİ</strong> beyan etmiş olursunuz:
                            </p>
                            <ul className="space-y-2 text-[#E5E7EB]/70">
                                <li className="flex items-start gap-2">
                                    <span className="text-red-400">•</span>
                                    Finansal piyasalarda işlem yapmanın yüksek risk içerdiğini ve sermayemizin tamamını kaybedebileceğimi biliyorum.
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-red-400">•</span>
                                    Platform tarafından sunulan içeriklerin yatırım tavsiyesi olmadığını anlıyorum.
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-red-400">•</span>
                                    Tüm yatırım kararlarımın ve sonuçlarının sorumluluğunun bana ait olduğunu kabul ediyorum.
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-red-400">•</span>
                                    Kaybetmeyi göze alamayacağım parayla işlem yapmayacağımı taahhüt ediyorum.
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-red-400">•</span>
                                    AI tahminlerinin hatalı olabileceğini ve geçmiş performansın gelecek garantisi olmadığını anlıyorum.
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
