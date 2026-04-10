"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useI18nStore } from "./i18n/store";

const translations = {
  en: () => import("@/messages/en.json").then((m) => m.default),
  tr: () => import("@/messages/tr.json").then((m) => m.default),
};

type Locale = "en" | "tr";

interface I18nContextType {
  locale: Locale;
  messages: any;
  setLocale: (locale: Locale) => void;
  t: (key: string) => any;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [messages, setMessages] = useState<any>({});

  // Subscribe to Zustand store so LanguageSwitcher changes propagate here
  const storeLocale = useI18nStore((s) => s.locale);

  useEffect(() => {
    const saved = localStorage.getItem("locale") as Locale;
    if (saved && (saved === "en" || saved === "tr")) {
      setLocaleState(saved);
    }
  }, []);

  // Sync when Zustand store locale changes (e.g. LanguageSwitcher)
  useEffect(() => {
    if (storeLocale && storeLocale !== locale) {
      setLocaleState(storeLocale);
    }
  }, [storeLocale]);

  useEffect(() => {
    translations[locale]().then((msgs) => setMessages(msgs));
    localStorage.setItem("locale", locale);
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    // Also sync to Zustand store
    useI18nStore.getState().setLocale(newLocale);
  };

  const t = (key: string): any => {
    const keys = key.split(".");
    let value = messages;
    for (const k of keys) {
      value = value?.[k];
    }
    // Return arrays and objects as-is, strings as-is, fallback to key
    if (value === undefined || value === null) return key;
    return value;
  };

  return (
    <I18nContext.Provider value={{ locale, messages, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used within I18nProvider");
  return context;
}
