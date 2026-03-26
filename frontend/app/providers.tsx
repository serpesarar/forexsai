"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { I18nProvider } from "../lib/i18n";
import { DashboardEditProvider } from "../contexts/DashboardEditContext";
import { WebSocketProvider } from "../contexts/WebSocketContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            gcTime: 10 * 60_000,
            refetchOnWindowFocus: false,
            refetchOnReconnect: false,
            retry: 1,
            retryDelay: 3000,
          },
        },
      })
  );

  return (
    <I18nProvider>
      <QueryClientProvider client={client}>
        <WebSocketProvider>
          <DashboardEditProvider>{children}</DashboardEditProvider>
        </WebSocketProvider>
      </QueryClientProvider>
    </I18nProvider>
  );
}
