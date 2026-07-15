"use client";

/**
 * Neural panel i18n — rides the app-wide I18nProvider (root providers.tsx)
 * so the panel follows the same language selection as the rest of the app.
 * `L(tr, en)` picks by the provider locale; `LangToggle` flips it through
 * the provider (which also syncs the zustand store + localStorage).
 */

import { useI18n } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n/store";

export type LFn = (tr: string, en: string) => string;

export function useNeuralLocale(): { locale: Locale; L: LFn } {
  const { locale } = useI18n();
  const L: LFn = (tr, en) => (locale === "tr" ? tr : en);
  return { locale: locale as Locale, L };
}

/** Kept for API compatibility — the root I18nProvider already hydrates from localStorage. */
export function useHydrateLocale() {}

export function LangToggle() {
  const { locale, setLocale } = useI18n();
  return (
    <div className="flex rounded-lg border border-white/[0.08] overflow-hidden">
      {(["tr", "en"] as Locale[]).map((l) => (
        <button
          key={l}
          onClick={() => setLocale(l)}
          className={`px-3 py-1.5 font-mono text-[10px] tracking-[0.2em] transition-colors ${
            locale === l ? "bg-cyan-500/15 text-cyan-300" : "text-gray-600 hover:text-gray-300"
          }`}
          aria-pressed={locale === l}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
