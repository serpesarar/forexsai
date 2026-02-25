"use client";

import { I18nProvider } from "@/lib/i18n";
import { StarfieldBackground } from "@/components/welcome/StarfieldBackground";

export default function PublicLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <I18nProvider>
            <div className="relative min-h-screen bg-black">
                {/* Tüm public sayfaların arkasında, tıklanamaz, fixed bir katman olarak yıldızlar */}
                <StarfieldBackground />

                {/* İçeriğin yıldızların üzerinde görünmesi için relative ve z-10 kullanıyoruz */}
                <div className="relative z-10 w-full">
                    {children}
                </div>
            </div>
        </I18nProvider>
    );
}
