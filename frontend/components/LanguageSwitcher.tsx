"use client";

import { Globe } from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18nStore();

  return (
    <button
      onClick={() => setLocale(locale === "en" ? "tr" : "en")}
      className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-textSecondary transition hover:border-white/30"
      title={locale === "en" ? "Türkçe'ye geç" : "Switch to English"}
    >
      <Globe className="h-3.5 w-3.5" />
      {locale === "en" ? "EN" : "TR"}
    </button>
  );
}





