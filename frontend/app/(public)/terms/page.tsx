"use client";

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";

export default function TermsPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto z-10">
                <h1 className="text-4xl font-bold text-white mb-8">Kullanım Koşulları</h1>
                <div className="prose prose-invert max-w-none text-[#E5E7EB]/80 leading-relaxed bg-white/5 border border-white/10 p-8 rounded-3xl backdrop-blur-md">
                    <p>Lütfen hizmetlerimizi kullanmadan önce bu koşulları dikkatlice okuyunuz.</p>
                    <h3>1. Kabul</h3>
                    <p>ForexsAi'ye üye olarak bu kullanım koşullarını kabul etmiş sayılırsınız.</p>
                    <h3>2. Hizmet Kullanımı</h3>
                    <p>Hizmetlerimiz yalnızca kişisel kullanım içindir. Otomatik botlar veya scraping yöntemleri ile veri çekmek yasaktır.</p>
                    <h3>3. Sorumluluk Reddi</h3>
                    <p>ForexsAi, sunduğu analizlerin doğruluğunu garanti etmez. Ticaret kararlarınızdan doğacak zararlardan platform sorumlu tutulamaz.</p>
                </div>
            </div>
            <Footer />
        </main>
    );
}
