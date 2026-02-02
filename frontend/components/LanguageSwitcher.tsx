"use client";

import { motion } from "framer-motion";
import { useI18nStore } from "@/lib/i18n/store";

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18nStore();

  return (
    <div className="flex items-center p-1 rounded-full bg-white/[0.06] border border-white/[0.08] backdrop-blur-md">
      {["en", "tr"].map((lang) => (
        <button
          key={lang}
          onClick={() => setLocale(lang as "en" | "tr")}
          className={`relative px-3.5 py-1.5 text-sm font-medium rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#00E0C6]/50 ${locale === lang
              ? "text-[#0B1220]"
              : "text-[#E5E7EB]/60 hover:text-[#E5E7EB]"
            }`}
          aria-label={`Switch to ${lang === "en" ? "English" : "Turkish"}`}
        >
          {locale === lang && (
            <motion.div
              layoutId="langPillSwitcher"
              className="absolute inset-0 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-full"
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
            />
          )}
          <span className="relative z-10 uppercase">{lang}</span>
        </button>
      ))}
    </div>
  );
}
