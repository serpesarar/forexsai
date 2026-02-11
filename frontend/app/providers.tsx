"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { I18nProvider } from "../lib/i18n";
import { DashboardEditProvider } from "../contexts/DashboardEditContext";
import { WebSocketProvider } from "../contexts/WebSocketContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());

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
