import { create } from "zustand";
import enTranslations from "./translations/en.json";
import trTranslations from "./translations/tr.json";

export type Locale = "en" | "tr";

const translations = {
  en: enTranslations,
  tr: trTranslations,
};

interface I18nState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

// Simple localStorage persistence
export const getStoredLocale = (): Locale => {
  if (typeof window === "undefined") return "en";
  const stored = localStorage.getItem("i18n-locale");
  return (stored === "en" || stored === "tr") ? stored : "en";
};

const setStoredLocale = (locale: Locale) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("i18n-locale", locale);
  }
};

export const useI18nStore = create<I18nState>((set, get) => ({
  // IMPORTANT: start with deterministic locale during SSR to avoid hydration mismatch.
  // We'll hydrate from localStorage on the client after mount.
  locale: "en",
  setLocale: (locale) => {
    set({ locale });
    setStoredLocale(locale);
  },
  t: (key: string) => {
    const { locale } = get();
    const keys = key.split(".");
    let value: any = translations[locale];
    for (const k of keys) {
      value = value?.[k];
    }
    return value || key;
  },
}));

