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
            title: "1. Hizmet Tanımı ve Kabul",
            content: [
                {
                    subtitle: "1.1 Hizmetlerimiz",
                    text: "ForexsAi, yapay zeka destekli finansal piyasa analiz platformudur. NASDAQ-100 ve XAU/USD (Altın) enstrümanları için teknik analiz, ML tabanlı tahminler, formasyon tespiti ve sentiment analizi hizmetleri sunmaktadır."
                },
                {
                    subtitle: "1.2 Kabul",
                    text: "Platformumuza kayıt olarak veya hizmetlerimizi kullanarak bu Kullanım Koşulları'nı, Gizlilik Politikası'nı ve Risk Uyarısı'nı okuduğunuzu, anladığınızı ve kabul ettiğinizi beyan edersiniz."
                },
                {
                    subtitle: "1.3 Yaş Sınırı",
                    text: "Hizmetlerimizi kullanabilmek için en az 18 yaşında olmanız gerekmektedir. 18 yaşından küçükseniz platformumuzu kullanamazsınız."
                }
            ]
        },
        {
            icon: Scale,
            title: "2. Sorumluluk Reddi",
            content: [
                {
                    subtitle: "2.1 Yatırım Tavsiyesi Değildir",
                    text: "ForexsAi tarafından sunulan tüm analizler, tahminler, sinyaller ve veriler YALNIZCA bilgilendirme ve eğitim amaçlıdır. Bu içerikler herhangi bir şekilde yatırım tavsiyesi, finansal danışmanlık veya alım-satım önerisi olarak yorumlanamaz."
                },
                {
                    subtitle: "2.2 Garanti Yokluğu",
                    text: "Platform 'olduğu gibi' ve 'mevcut olduğu şekliyle' sunulmaktadır. Analizlerin doğruluğu, tahminlerin gerçekleşmesi veya herhangi bir getiri garantisi verilmemektedir. Geçmiş performans, gelecekteki sonuçların göstergesi değildir."
                },
                {
                    subtitle: "2.3 Kayıp Sorumluluğu",
                    text: "Platformumuzun kullanımından kaynaklanan doğrudan, dolaylı, arızi, özel veya sonuç olarak ortaya çıkan herhangi bir kayıp veya zarardan ForexsAi sorumlu tutulamaz. Tüm yatırım kararları ve bunların sonuçları tamamen kullanıcının sorumluluğundadır."
                }
            ]
        },
        {
            icon: Ban,
            title: "3. Yasaklı Kullanımlar",
            content: [
                {
                    subtitle: "3.1 Otomatik Erişim",
                    text: "Bot, scraper, crawler veya benzeri otomatik araçlarla platforma erişim kesinlikle yasaktır. API limitleri ve kullanım kurallarına uyulması zorunludur."
                },
                {
                    subtitle: "3.2 İçerik Paylaşımı",
                    text: "Premium içeriklerin, analizlerin veya tahminlerin izinsiz olarak kopyalanması, dağıtılması veya yeniden yayınlanması yasaktır."
                },
                {
                    subtitle: "3.3 Kötüye Kullanım",
                    text: "Platformun güvenliğini tehlikeye atacak eylemler, diğer kullanıcıların hizmetlerini engelleyecek davranışlar, yanlış veya yanıltıcı bilgi paylaşımı, sahte hesap oluşturma kesinlikle yasaktır."
                },
                {
                    subtitle: "3.4 Ticari Kullanım",
                    text: "Bireysel lisans ile elde edilen verilerin ticari amaçlarla kullanılması, satılması veya yeniden lisanslanması yasaktır."
                }
            ]
        },
        {
            icon: CreditCard,
            title: "4. Ücretler ve Ödemeler",
            content: [
                {
                    subtitle: "4.1 Ücretsiz Plan",
                    text: "Early Access döneminde tüm özellikler ücretsiz olarak sunulmaktadır. Bu durum değişebilir ve değişiklikler önceden duyurulacaktır."
                },
                {
                    subtitle: "4.2 Premium Planlar",
                    text: "Gelecekte sunulacak premium planların ücretleri, fiyatlandırma sayfasında açıkça belirtilecektir. Abonelik ücretleri peşin olarak tahsil edilir."
                },
                {
                    subtitle: "4.3 İade Politikası",
                    text: "Dijital hizmet niteliği gereği, satın alma işleminden sonra iade yapılmamaktadır. Ancak teknik sorunlardan kaynaklanan durumlarda değerlendirme yapılabilir."
                }
            ]
        },
        {
            icon: RefreshCw,
            title: "5. Hesap Yönetimi",
            content: [
                {
                    subtitle: "5.1 Hesap Güvenliği",
                    text: "Hesap bilgilerinizin güvenliğinden siz sorumlusunuz. Güçlü parola kullanmanız ve hesap bilgilerinizi kimseyle paylaşmamanız önerilir."
                },
                {
                    subtitle: "5.2 Hesap Askıya Alma",
                    text: "Kullanım koşullarının ihlali durumunda hesabınız geçici veya kalıcı olarak askıya alınabilir. Bu durum önceden bildirilmeden uygulanabilir."
                },
                {
                    subtitle: "5.3 Hesap Silme",
                    text: "Hesabınızı istediğiniz zaman silebilirsiniz. Hesap silme işlemi 30 gün içinde tamamlanır ve tüm verileriniz kalıcı olarak silinir."
                }
            ]
        },
        {
            icon: FileText,
            title: "6. Fikri Mülkiyet",
            content: [
                {
                    subtitle: "6.1 Platform İçeriği",
                    text: "ForexsAi platformu, logosu, tasarımları, yazılımı, algoritmaları ve tüm içerikleri fikri mülkiyet hakları kapsamında korunmaktadır."
                },
                {
                    subtitle: "6.2 Kullanım Lisansı",
                    text: "Size kişisel, devredilemeyen, münhasır olmayan ve sınırlı bir kullanım lisansı verilmektedir. Bu lisans, hizmetlerimizi yalnızca belirlenen amaçlar doğrultusunda kullanmanızı kapsar."
                },
                {
                    subtitle: "6.3 Geri Bildirim",
                    text: "Platforma ilişkin sağladığınız geri bildirimler, öneriler veya fikirler üzerinde herhangi bir hak talep edemezsiniz ve bunlar ForexsAi'ye devredilmiş sayılır."
                }
            ]
        },
        {
            icon: Gavel,
            title: "7. Uyuşmazlık Çözümü",
            content: [
                {
                    subtitle: "7.1 Geçerli Hukuk",
                    text: "Bu sözleşme Türkiye Cumhuriyeti hukukuna tabidir ve bu hukuka göre yorumlanacaktır."
                },
                {
                    subtitle: "7.2 Yargı Yetkisi",
                    text: "Bu sözleşmeden doğabilecek uyuşmazlıklarda İstanbul Mahkemeleri ve İcra Daireleri yetkilidir."
                },
                {
                    subtitle: "7.3 Arabuluculuk",
                    text: "Taraflar, uyuşmazlıkların çözümünde öncelikle arabuluculuk yoluna başvurmayı kabul ederler."
                }
            ]
        },
        {
            icon: Globe,
            title: "8. Değişiklikler",
            content: [
                {
                    subtitle: "8.1 Koşul Değişiklikleri",
                    text: "Bu Kullanım Koşulları herhangi bir zamanda değiştirilebilir. Önemli değişiklikler e-posta ile bildirilecektir."
                },
                {
                    subtitle: "8.2 Devam Eden Kullanım",
                    text: "Değişikliklerden sonra platformu kullanmaya devam etmeniz, güncellenmiş koşulları kabul ettiğiniz anlamına gelir."
                },
                {
                    subtitle: "8.3 Geçerlilik",
                    text: "Bu koşulların herhangi bir hükmünün geçersiz veya uygulanamaz bulunması, diğer hükümlerin geçerliliğini etkilemez."
                }
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
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Kullanım Koşulları</h1>
                    <p className="text-lg text-[#E5E7EB]/60">Son Güncelleme: 31 Ocak 2025</p>
                </div>

                {/* Important Notice */}
                <div className="glass-premium p-8 rounded-3xl mb-8 border-l-4 border-amber-500">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                            <Scale className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-amber-400 mb-2">Önemli Uyarı</h3>
                            <p className="text-[#E5E7EB]/70 leading-relaxed">
                                Lütfen bu koşulları dikkatlice okuyunuz. Platformumuzu kullanarak bu koşulları kabul etmiş sayılırsınız. 
                                Ayrıca Risk Uyarısı sayfamızı da okumanızı şiddetle tavsiye ederiz.
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
                        <h2 className="text-xl font-bold text-white">Kabul Beyanı</h2>
                    </div>
                    <p className="text-[#E5E7EB]/70 leading-relaxed">
                        ForexsAi platformuna kayıt olarak veya hizmetlerimizi kullanarak yukarıdaki tüm koşulları okuduğunuzu, 
                        anladığınızı ve kabul ettiğinizi beyan edersiniz. Bu koşulları kabul etmiyorsanız, lütfen platformumuzu kullanmayınız.
                    </p>
                </div>
            </div>
            <Footer />
        </main>
    );
}
