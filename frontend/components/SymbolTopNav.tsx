"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  TrendingUp,
  CircleDollarSign,
  Building2,
  Fuel,
} from "lucide-react";

// Sembol konfigürasyonu
const SYMBOLS = [
  {
    id: "nasdaq",
    label: "NASDAQ",
    path: "/nasdaq",
    icon: TrendingUp,
    accent: {
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
      text: "text-emerald-400",
      glow: "shadow-emerald-500/30",
      borderHover: "hover:border-emerald-500/50",
      bgHover: "hover:bg-emerald-500/20",
    },
  },
  {
    id: "xauusd",
    label: "XAU/USD",
    path: "/xauusd",
    icon: CircleDollarSign,
    accent: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      text: "text-amber-400",
      glow: "shadow-amber-400/30",
      borderHover: "hover:border-amber-500/50",
      bgHover: "hover:bg-amber-500/20",
    },
  },
  {
    id: "dax",
    label: "DAX",
    path: "/dax",
    icon: Building2,
    accent: {
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
      text: "text-blue-400",
      glow: "shadow-blue-500/30",
      borderHover: "hover:border-blue-500/50",
      bgHover: "hover:bg-blue-500/20",
    },
  },
  {
    id: "oil",
    label: "US OIL",
    path: "/oil",
    icon: Fuel,
    accent: {
      bg: "bg-orange-500/10",
      border: "border-orange-500/20",
      text: "text-orange-400",
      glow: "shadow-orange-500/30",
      borderHover: "hover:border-orange-500/50",
      bgHover: "hover:bg-orange-500/20",
    },
  },
] as const;

interface SymbolTabProps {
  symbol: (typeof SYMBOLS)[number];
  isActive: boolean;
  price?: SymbolTopNavPrice;
}

type SymbolTopNavPrice = {
  label: string;
  price: string | number;
  change?: string;
  trend?: "up" | "down";
};

interface SymbolTopNavProps {
  prices?: SymbolTopNavPrice[];
  rightSlot?: ReactNode;
}

function SymbolTab({ symbol, isActive, price }: SymbolTabProps) {
  const Icon = symbol.icon;
  const isPriceReady = price && price.price !== "--" && price.price !== "-";
  const formattedPrice = !isPriceReady ? "---" : typeof price?.price === "number" ? `$${price.price}` : `$${price?.price}`;
  const isUp = price?.trend === "up" || (price?.change || "").startsWith("+");

  return (
    <Link href={symbol.path} className="relative flex-1">
      <motion.div
        whileHover={{ y: -3, scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className={`
          group relative flex flex-col items-center justify-center gap-1.5
          rounded-2xl border px-4 py-3
          transition-all duration-200
          backdrop-blur-sm
          ${isActive ? symbol.accent.bg : "bg-slate-900/60"}
          ${isActive ? symbol.accent.border : "border-slate-800"}
          ${symbol.accent.borderHover}
          ${symbol.accent.bgHover}
          ${isActive ? symbol.accent.glow : ""}
          ${isActive ? "shadow-lg" : "shadow-none hover:shadow-md"}
        `}
      >
        {/* Glow efekti aktif sayfa için */}
        {isActive && (
          <motion.div
            layoutId="activeGlow"
            className={`
              absolute inset-0 rounded-2xl opacity-50 blur-xl
              ${symbol.accent.bg}
            `}
            transition={{ duration: 0.3 }}
          />
        )}

        {/* İkon ve içerik */}
        <div className="relative z-10 flex flex-col items-center gap-1">
          <div
            className={`
              flex h-8 w-8 items-center justify-center rounded-xl
              transition-colors duration-200
              ${isActive ? symbol.accent.bg : "bg-slate-800/50 group-hover:bg-slate-800"}
            `}
          >
            <Icon
              className={`
                h-4 w-4 transition-colors duration-200
                ${isActive ? symbol.accent.text : "text-slate-400"}
                group-hover:text-white
              `}
            />
          </div>

          <span
            className={`
              text-sm font-bold tracking-wide transition-colors duration-200
              ${isActive ? "text-white" : "text-slate-400"}
              group-hover:text-white
            `}
          >
            {symbol.label}
          </span>

          {/* Opsiyonal fiyat gösterimi - şu an placeholder */}
          <div className="flex items-center gap-1 text-[10px] font-medium">
            <span className={`${isPriceReady ? "text-slate-300" : "text-slate-500"}`}>{formattedPrice}</span>
            {isPriceReady && price?.change && (
              <span className={isUp ? "text-emerald-400" : "text-rose-400"}>{price.change}</span>
            )}
          </div>
        </div>

        {/* Aktif gösterge çizgisi (bottom border) */}
        {isActive && (
          <motion.div
            layoutId="activeIndicator"
            className={`
              absolute -bottom-px left-4 right-4 h-0.5 rounded-full
              ${symbol.accent.bg.replace("/10", "")}
            `}
            transition={{ duration: 0.3 }}
          />
        )}
      </motion.div>
    </Link>
  );
}

export default function SymbolTopNav({ prices = [], rightSlot }: SymbolTopNavProps) {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-[100] w-full border-b border-slate-800/50 bg-slate-950/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1680px] items-center gap-2 px-4 py-2 sm:px-6 lg:px-8">
        {/* Logo/Brand - Opsiyonel */}
        <div className="mr-4 hidden shrink-0 items-center gap-2 md:flex">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500">
            <TrendingUp className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-bold text-white">ForexSAI</span>
        </div>

        {/* Sembol sekmeleri */}
        <div className="flex flex-1 gap-2 sm:gap-3">
          {SYMBOLS.map((symbol) => (
            <SymbolTab
              key={symbol.id}
              symbol={symbol}
              isActive={pathname === symbol.path}
              price={prices.find((item) => item.label === symbol.label)}
            />
          ))}
        </div>

        {/* Sağ taraf opsiyonel alan */}
        {rightSlot ? (
          <div className="ml-4 hidden shrink-0 items-center gap-3 lg:flex">{rightSlot}</div>
        ) : (
          <div className="ml-4 hidden shrink-0 items-center gap-3 lg:flex">
            <div className="h-6 w-px bg-slate-800" />
            <span className="text-xs text-slate-500">Live Market</span>
            <div className="flex h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
          </div>
        )}
      </div>
    </nav>
  );
}
