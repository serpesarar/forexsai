"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { Shield, Lock, Eye, Database, Globe, Mail, FileText } from "lucide-react";

export default function PrivacyPage() {
    const { t } = useI18n();

    const sections = [
        {
            icon: Database,
            title: "1. Toplanan Veriler",
            content: [
                {
                    subtitle: "1.1 Hesap Bilgileri",
                    text: "Platformumuza kayıt olduğunuzda aşağıdaki bilgileri topluyoruz: E-posta adresi, şifrelenmiş parola (hash), ad-soyad (isteğe bağlı), profil fotoğrafı (isteğe bağlı)."
                },
                {
                    subtitle: "1.2 Kullanım Verileri",
                    text: "Hizmetlerimizi kullandığınızda otomatik olarak toplanan veriler: IP adresi, tarayıcı türü ve sürümü, cihaz bilgileri, sayfa görüntüleme istatistikleri, oturum süreleri, tercih edilen dil ayarları."
                },
                {
                    subtitle: "1.3 Analitik Veriler",
                    text: "Platform performansını iyileştirmek için: Hangi özelliklerin kullanıldığı, hata raporları, performans metrikleri. Bu veriler anonim olarak toplanır ve kişisel kimliğinizle ilişkilendirilmez."
                }
            ]
        },
        {
            icon: Eye,
            title: "2. Verilerin Kullanım Amacı",
            content: [
                {
                    subtitle: "2.1 Hizmet Sunumu",
                    text: "Hesabınızı oluşturmak ve yönetmek, AI destekli piyasa analizleri sunmak, kişiselleştirilmiş deneyim sağlamak, teknik destek vermek."
                },
                {
                    subtitle: "2.2 İletişim",
                    text: "Önemli güncellemeler ve duyurular, güvenlik bildirimleri, hesap aktivitesi uyarıları, pazarlama iletişimleri (onayınız dahilinde)."
                },
                {
                    subtitle: "2.3 Geliştirme",
                    text: "Hizmet kalitesini artırmak, yeni özellikler geliştirmek, kullanıcı deneyimini optimize etmek, hataları tespit ve düzeltmek."
                }
            ]
        },
        {
            icon: Lock,
            title: "3. Veri Güvenliği",
            content: [
                {
                    subtitle: "3.1 Şifreleme",
                    text: "Tüm veri transferleri 256-bit SSL/TLS şifreleme ile korunmaktadır. Parolalar bcrypt algoritması ile hash'lenerek saklanır. Hassas veriler AES-256 şifreleme standardı ile korunur."
                },
                {
                    subtitle: "3.2 Altyapı Güvenliği",
                    text: "Verileriniz güvenli bulut altyapısında (Railway, Supabase) barındırılmaktadır. Düzenli güvenlik denetimleri ve penetrasyon testleri yapılmaktadır. 7/24 izleme ve tehdit tespiti aktiftir."
                },
                {
                    subtitle: "3.3 Erişim Kontrolü",
                    text: "Verilerinize erişim, yalnızca görev tanımı gereği erişmesi gereken yetkili personel ile sınırlıdır. Tüm erişimler loglanır ve denetlenir."
                }
            ]
        },
        {
            icon: Globe,
            title: "4. Üçüncü Taraf Paylaşımları",
            content: [
                {
                    subtitle: "4.1 Hizmet Sağlayıcılar",
                    text: "Aşağıdaki güvenilir hizmet sağlayıcılarla veri paylaşımı yapılmaktadır: Supabase (veritabanı ve kimlik doğrulama), Railway (uygulama barındırma), Resend (e-posta hizmetleri). Bu sağlayıcılar GDPR ve endüstri standartlarına uygundur."
                },
                {
                    subtitle: "4.2 Yasal Zorunluluklar",
                    text: "Yasal bir zorunluluk halinde (mahkeme kararı, resmi talep vb.) verileriniz yetkili makamlarla paylaşılabilir. Bu durumda, yasaların izin verdiği ölçüde sizi bilgilendireceğiz."
                },
                {
                    subtitle: "4.3 Satış veya Transfer",
                    text: "Kişisel verileriniz hiçbir koşulda üçüncü taraflara satılmaz veya pazarlama amacıyla paylaşılmaz."
                }
            ]
        },
        {
            icon: FileText,
            title: "5. Kullanıcı Hakları",
            content: [
                {
                    subtitle: "5.1 Erişim Hakkı",
                    text: "Hakkınızda sakladığımız tüm verilerin bir kopyasını talep edebilirsiniz."
                },
                {
                    subtitle: "5.2 Düzeltme Hakkı",
                    text: "Yanlış veya eksik verilerinizin düzeltilmesini isteyebilirsiniz."
                },
                {
                    subtitle: "5.3 Silme Hakkı",
                    text: "Hesabınızı ve ilişkili tüm verilerinizi kalıcı olarak sildirebilirsiniz. Silme işlemi 30 gün içinde tamamlanır."
                },
                {
                    subtitle: "5.4 Veri Taşınabilirliği",
                    text: "Verilerinizi yaygın kullanılan, makine tarafından okunabilir bir formatta (JSON) talep edebilirsiniz."
                },
                {
                    subtitle: "5.5 İtiraz Hakkı",
                    text: "Verilerinizin işlenmesine itiraz edebilir veya pazarlama iletişimlerinden çıkabilirsiniz."
                }
            ]
        },
        {
            icon: Shield,
            title: "6. Çerezler (Cookies)",
            content: [
                {
                    subtitle: "6.1 Zorunlu Çerezler",
                    text: "Oturum yönetimi ve güvenlik için gerekli çerezler kullanılmaktadır. Bu çerezler olmadan hizmet verilemez."
                },
                {
                    subtitle: "6.2 Analitik Çerezler",
                    text: "Hizmet kullanımını analiz etmek için anonim çerezler kullanılabilir. Bu çerezleri tarayıcı ayarlarınızdan devre dışı bırakabilirsiniz."
                },
                {
                    subtitle: "6.3 Tercih Çerezleri",
                    text: "Dil tercihi, tema seçimi gibi ayarlarınızı hatırlamak için çerezler kullanılır."
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
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 mb-6">
                        <Shield className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Gizlilik Politikası</h1>
                    <p className="text-lg text-[#E5E7EB]/60">Son Güncelleme: 31 Ocak 2025</p>
                </div>

                {/* Intro */}
                <div className="glass-premium p-8 rounded-3xl mb-8">
                    <p className="text-lg text-[#E5E7EB]/80 leading-relaxed">
                        ForexsAi olarak gizliliğinize büyük önem veriyoruz. Bu Gizlilik Politikası, kişisel verilerinizin nasıl toplandığını, 
                        kullanıldığını, korunduğunu ve haklarınızın neler olduğunu açıklamaktadır. Platformumuzu kullanarak bu politikayı 
                        kabul etmiş sayılırsınız.
                    </p>
                </div>

                {/* Sections */}
                <div className="space-y-6">
                    {sections.map((section, idx) => (
                        <div key={idx} className="glass-premium p-8 rounded-3xl">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 border border-purple-500/30">
                                    <section.icon className="w-6 h-6 text-purple-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                            </div>
                            <div className="space-y-6 pl-16">
                                {section.content.map((item, itemIdx) => (
                                    <div key={itemIdx}>
                                        <h3 className="text-lg font-semibold text-emerald-400 mb-2">{item.subtitle}</h3>
                                        <p className="text-[#E5E7EB]/70 leading-relaxed">{item.text}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Contact */}
                <div className="mt-8 glass-premium p-8 rounded-3xl">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
                            <Mail className="w-6 h-6 text-cyan-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white">7. İletişim</h2>
                    </div>
                    <div className="pl-16">
                        <p className="text-[#E5E7EB]/70 leading-relaxed mb-4">
                            Gizlilik politikamız veya kişisel verilerinizle ilgili sorularınız için bizimle iletişime geçebilirsiniz:
                        </p>
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <p className="text-white font-medium">E-posta: privacy@forexsai.com</p>
                            <p className="text-[#E5E7EB]/60 text-sm mt-2">Taleplerinize 30 gün içinde yanıt verilecektir.</p>
                        </div>
                    </div>
                </div>
            </div>
            <Footer />
        </main>
    );
}
