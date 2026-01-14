"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { getStoredLocale, useI18nStore } from "../lib/i18n/store";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());
  const setLocale = useI18nStore((s) => s.setLocale);

  useEffect(() => {
    // Hydrate locale from localStorage after mount to avoid SSR hydration mismatch.
    setLocale(getStoredLocale());
  }, [setLocale]);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
