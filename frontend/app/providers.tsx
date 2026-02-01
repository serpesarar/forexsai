"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { I18nProvider } from "../lib/i18n";
import { DashboardEditProvider } from "../contexts/DashboardEditContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());

  return (
    <I18nProvider>
      <QueryClientProvider client={client}>
        <DashboardEditProvider>{children}</DashboardEditProvider>
      </QueryClientProvider>
    </I18nProvider>
  );
}
