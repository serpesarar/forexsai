"use client";

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

export default function PrivacyPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto z-10">
                <h1 className="text-4xl font-bold text-white mb-8">Gizlilik Politikası</h1>
                <div className="prose prose-invert max-w-none text-[#E5E7EB]/80 leading-relaxed bg-white/5 border border-white/10 p-8 rounded-3xl backdrop-blur-md">
                    <p>Son Güncelleme: 31.01.2025</p>
                    <p>ForexsAi olarak gizliliğinize önem veriyoruz. Bu politika, verilerinizin nasıl toplandığını ve işlendiğini açıklar.</p>
                    <h3>1. Toplanan Veriler</h3>
                    <p>Hesap oluştururken e-posta adresinizi ve temel profil bilgilerinizi topluyoruz. Ödeme bilgileri, güvenli ödeme sağlayıcıları tarafından işlenir ve sunucularımızda saklanmaz.</p>
                    <h3>2. Veri Kullanımı</h3>
                    <p>Verilerinizi yalnızca hizmet kalitesini artırmak ve size daha iyi bir deneyim sunmak için kullanıyoruz. Verileriniz asla üçüncü taraflara satılmaz.</p>
                    <h3>3. Güvenlik</h3>
                    <p>Endüstri standardı şifreleme yöntemleri (SSL/TLS) kullanarak verilerinizi koruyoruz.</p>
                </div>
            </div>
            <Footer />
        </main>
    );
}
