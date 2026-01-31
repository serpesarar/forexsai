"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

const translations = {
  en: () => import("@/messages/en.json").then((m) => m.default),
  tr: () => import("@/messages/tr.json").then((m) => m.default),
};

type Locale = "en" | "tr";

interface I18nContextType {
  locale: Locale;
  messages: any;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [messages, setMessages] = useState<any>({});

  useEffect(() => {
    const saved = localStorage.getItem("locale") as Locale;
    if (saved && (saved === "en" || saved === "tr")) {
      setLocaleState(saved);
    }
  }, []);

  useEffect(() => {
    translations[locale]().then((msgs) => setMessages(msgs));
    localStorage.setItem("locale", locale);
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
  };

  const t = (key: string): string => {
    const keys = key.split(".");
    let value = messages;
    for (const k of keys) {
      value = value?.[k];
    }
    return typeof value === "string" ? value : key;
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
