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
            staleTime: 30_000,
            gcTime: 10 * 60_000,
            // 2026-08-26: ikisi de `false` idi. Sonuç: bir panel bir kez
            // yüklendikten sonra HİÇBİR ŞEY yeniden çekmiyordu — sekmeye geri
            // dönmek, ağın kopup gelmesi, hiçbiri tetiklemiyordu. Kullanıcı
            // günlerce eski veriye bakıyordu (Evrim Paneli'ndeki decider
            // geçmişi vakası). staleTime zaten gereksiz isteği önlüyor;
            // odak/yeniden-bağlanma tetiklerinin kapalı olması için sebep yok.
            refetchOnWindowFocus: true,
            refetchOnReconnect: true,
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
