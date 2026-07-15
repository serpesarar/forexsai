"use client";

// Gemi haritası — Neural tasarım kabuğunda.
// Eski çok panelli /oil sayfası kaldırıldı (yedek: .backup/legacy_panels_20260715/app/oil/);
// kanallardan geçen tankerleri izleyen harita uygulaması (OilBalticPanel) korundu.

import { lazy, Suspense } from "react";
import { motion } from "framer-motion";

import AuthGuard from "@/components/AuthGuard";
import NeuralNav from "@/components/neural/NeuralNav";
import { useNeuralLocale } from "@/components/neural/i18n";

const OilBalticPanel = lazy(() => import("@/components/panels/OilBalticPanel"));

function OilMapInner() {
  const { L } = useNeuralLocale();
  return (
    <div className="min-h-screen bg-[#05070d] font-sans text-white">
      <NeuralNav />
      <main className="relative mx-auto max-w-[1500px] px-4 pb-16 md:px-8">
        <div className="pb-6 pt-10 text-center">
          <motion.p
            initial={{ opacity: 0, letterSpacing: "0.8em" }}
            animate={{ opacity: 1, letterSpacing: "0.45em" }}
            transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
            className="font-mono text-[10px] uppercase text-cyan-500/70"
          >
            {L("Tanker Takibi", "Tanker Tracking")}
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.8 }}
            className="mt-3 text-2xl font-light text-gray-300 md:text-3xl"
          >
            {L("Kanallardan geçen gemiler — ", "Ships passing the chokepoints — ")}
            <span className="font-bold text-white">{L("fiziksel piyasa canlı", "physical market live")}</span>
          </motion.h1>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="rounded-2xl border border-white/[0.07] bg-[#0a0f1c]/80 p-3 backdrop-blur-md md:p-5"
        >
          <Suspense
            fallback={
              <div className="flex h-[420px] items-center justify-center font-mono text-[10px] tracking-[0.3em] text-gray-600">
                {L("HARİTA YÜKLENİYOR…", "LOADING MAP…")}
              </div>
            }
          >
            <OilBalticPanel />
          </Suspense>
        </motion.div>
      </main>
    </div>
  );
}

export default function OilMapPage() {
  return (
    <AuthGuard>
      <OilMapInner />
    </AuthGuard>
  );
}
