"use client";

/**
 * NeuralNav — the app-wide tab bar of the new Neural design.
 * One row: brand · main tabs (Panel, 4 symbols, Ship Map, Evolution) ·
 * language toggle · user menu. Active tab glows cyan; tabs scroll
 * horizontally on mobile. Used by the home dashboard, /neural/[symbol]
 * and the ship-map page so navigation feels like one system.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { BrainCircuit } from "lucide-react";
import { LangToggle, useNeuralLocale } from "./i18n";
import { useIsOwner } from "./OwnerGuard";
import UserMenu from "@/components/UserMenu";

export default function NeuralNav() {
  const { L } = useNeuralLocale();
  const pathname = usePathname() ?? "/";
  const isOwner = useIsOwner();

  const tabs = [
    { href: "/", label: L("PANEL", "PANEL"), match: (p: string) => p === "/" },
    { href: "/neural/ndx", label: "NASDAQ", match: (p: string) => p.startsWith("/neural/ndx") },
    { href: "/neural/dax", label: "DAX", match: (p: string) => p.startsWith("/neural/dax") },
    { href: "/neural/xauusd", label: L("ALTIN", "GOLD"), match: (p: string) => p.startsWith("/neural/xauusd") },
    { href: "/neural/usoil", label: L("PETROL", "OIL"), match: (p: string) => p.startsWith("/neural/usoil") },
    { href: "/oil", label: L("GEMİ HARİTASI", "SHIP MAP"), match: (p: string) => p.startsWith("/oil") },
    // EVRİM sekmesi yalnızca panel sahibine görünür (OwnerGuard e-postası)
    ...(isOwner
      ? [{ href: "/evolution", label: L("EVRİM", "EVOLUTION"), match: (p: string) => p.startsWith("/evolution") }]
      : []),
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#05070d]/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1500px] items-center gap-3 px-4 py-2.5 md:px-8">
        {/* brand */}
        <Link href="/" className="flex shrink-0 items-center gap-2 group">
          <motion.span
            animate={{ opacity: [1, 0.7, 1] }}
            transition={{ repeat: Infinity, duration: 4 }}
            className="text-cyan-400"
          >
            <BrainCircuit size={18} />
          </motion.span>
          <span className="hidden sm:inline-flex items-baseline gap-0.5">
            <span className="text-sm font-bold tracking-[0.12em] bg-gradient-to-r from-cyan-300 via-white to-purple-300 bg-clip-text text-transparent">
              FOREXS
            </span>
            <span className="text-sm font-light tracking-[0.12em] text-white/90">AI</span>
          </span>
        </Link>

        {/* tabs */}
        <div className="flex flex-1 items-center gap-1.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {tabs.map((t) => {
            const active = t.match(pathname);
            return (
              <Link
                key={t.href}
                href={t.href}
                className={`relative shrink-0 rounded-lg px-3.5 py-2 font-mono text-[10px] tracking-[0.2em] transition-all ${
                  active
                    ? "border border-cyan-400/40 bg-cyan-500/10 text-cyan-300 shadow-[0_0_16px_rgba(34,211,238,0.15)]"
                    : "border border-white/[0.06] text-gray-500 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                {t.label}
                {active && (
                  <motion.span
                    layoutId="neural-nav-glow"
                    className="pointer-events-none absolute inset-0 rounded-lg"
                    aria-hidden
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* right cluster */}
        <div className="flex shrink-0 items-center gap-2.5">
          <LangToggle />
          <UserMenu />
        </div>
      </div>
    </nav>
  );
}
