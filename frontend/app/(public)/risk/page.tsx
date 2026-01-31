"use client";

export const dynamic = 'force-dynamic';

import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { TopNav } from "@/components/welcome/TopNav";
import { Footer } from "@/components/welcome/Footer";
import { AlertTriangle } from "lucide-react";

export default function RiskPage() {
    const { t } = useI18n();

    return (
        <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB] font-sans">
            <TopNav />
            <AnimatedBackground />

            <div className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto z-10">
                <div className="p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md">
                    <div className="flex items-center gap-4 mb-8 text-red-400">
                        <AlertTriangle className="w-10 h-10" />
                        <h1 className="text-3xl font-bold text-white">{t("legal.risk.title")}</h1>
                    </div>

                    <div className="prose prose-invert max-w-none text-[#E5E7EB]/80 leading-relaxed space-y-6">
                        <p className="text-lg font-medium">{t("legal.risk.content")}</p>

                        <hr className="border-white/10" />

                        <h3 className="text-xl font-semibold text-white">1. Genel Risk Uyarısı</h3>
                        <p>
                            Finansal piyasalarda (Forex, Emtia, Kripto Para vb.) işlem yapmak, yatırdığınız sermayenin tamamını veya bir kısmını kaybetme riski taşır. Kaldıraçlı işlemler bu riski daha da artırır. Bu nedenle, kaybetmeyi göze alamayacağınız bir sermaye ile işlem yapmamanız tavsiye edilir.
                        </p>

                        <h3 className="text-xl font-semibold text-white">2. Yatırım Tavsiyesi Değildir</h3>
                        <p>
                            ForexsAi platformu tarafından sunulan analizler, grafikler, sinyaller ve yapay zeka verileri; yalnızca istatistiksel veri işleme ve eğitim amaçlıdır. Bu veriler "Yatırım Tavsiyesi" (Investment Advice) kapsamında değildir ve herhangi bir getiri garantisi sunmaz.
                        </p>

                        <h3 className="text-xl font-semibold text-white">3. Geçmiş Performans</h3>
                        <p>
                            Uygulamada sunulan backtest (geçmişe dönük test) sonuçları, gelecekteki performansın garantisi veya göstergesi değildir. Piyasa koşulları sürekli değişkenlik gösterir.
                        </p>

                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl mt-8">
                            Bu platformu kullanarak, ticaret yapmanın risklerini tamamen anladığınızı ve aldığınız kararlardan yalnızca kendinizin sorumlu olduğunuzu kabul etmiş olursunuz.
                        </div>
                    </div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
