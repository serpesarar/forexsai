"use client";

import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  TrendingUp,
  CircleDollarSign,
  Building2,
  Fuel,
  Menu,
} from "lucide-react";
import { useNavigationStore } from "@/lib/store/navigation";

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
    },
  },
] as const;

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

function SymbolTab({
  symbol,
  isActive,
  price,
  onClick,
}: {
  symbol: (typeof SYMBOLS)[number];
  isActive: boolean;
  price?: SymbolTopNavPrice;
  onClick: () => void;
}) {
  const Icon = symbol.icon;
  const isPriceReady = price && price.price !== "--" && price.price !== "-";
  const formattedPrice = !isPriceReady
    ? "---"
    : typeof price?.price === "number"
      ? `$${price.price}`
      : `$${price?.price}`;
  const isUp =
    price?.trend === "up" || (price?.change || "").startsWith("+");

  return (
    <button
      onClick={onClick}
      type="button"
      className={`
        relative flex flex-1 flex-col items-center justify-center gap-1
        rounded-xl border px-3 py-2
        transition-all duration-200 ease-out
        pointer-events-auto cursor-pointer
        hover:scale-[1.02] hover:-translate-y-0.5
        active:scale-[0.98]
        ${isActive ? symbol.accent.bg : "bg-slate-900/60 hover:bg-slate-800/80"}
        ${isActive ? symbol.accent.border : "border-slate-700 hover:border-slate-600"}
        ${isActive ? symbol.accent.glow : ""}
        ${isActive ? "shadow-lg" : "shadow-none hover:shadow-md"}
      `}
    >
      {isActive && (
        <div
          className={`absolute inset-0 rounded-xl opacity-40 blur-lg pointer-events-none ${symbol.accent.bg}`}
        />
      )}

      <div className="relative z-10 flex flex-col items-center gap-0.5">
        <div
          className={`flex h-7 w-7 items-center justify-center rounded-lg transition-colors duration-200 ${
            isActive ? symbol.accent.bg : "bg-slate-800/60"
          }`}
        >
          <Icon
            className={`h-4 w-4 transition-colors duration-200 ${
              isActive ? symbol.accent.text : "text-slate-400"
            }`}
          />
        </div>

        <span
          className={`text-sm font-bold tracking-wide transition-colors duration-200 ${
            isActive ? "text-white" : "text-slate-400"
          }`}
        >
          {symbol.label}
        </span>

        <div className="flex items-center gap-1 text-[10px] font-medium">
          <span className={isPriceReady ? "text-slate-300" : "text-slate-500"}>
            {formattedPrice}
          </span>
          {isPriceReady && price?.change && (
            <span className={isUp ? "text-emerald-400" : "text-rose-400"}>
              {price.change}
            </span>
          )}
        </div>
      </div>

      {isActive && (
        <div
          className={`absolute -bottom-px left-3 right-3 h-0.5 rounded-full ${symbol.accent.text.replace("text-", "bg-")}`}
        />
      )}
    </button>
  );
}

export default function SymbolTopNav({
  prices = [],
  rightSlot,
}: SymbolTopNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const toggleMobileSidebar = useNavigationStore((s) => s.toggleMobileSidebar);

  return (
    <nav
      className="sticky top-0 z-[100] w-full border-b border-slate-800/50 bg-slate-950/90 backdrop-blur-xl"
      style={{ paddingTop: "env(safe-area-inset-top, 0px)" }}
    >
      <div className="mx-auto flex max-w-[1680px] items-center gap-2 px-3 py-2 sm:px-4 md:px-6 lg:px-8 pointer-events-auto">
        {/* Mobile hamburger — opens the Sidebar drawer. Hidden on tablet+. */}
        <button
          type="button"
          aria-label="Open navigation menu"
          onClick={toggleMobileSidebar}
          className="fsai-tap-sm md:hidden flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-900/60 text-slate-200 transition-colors hover:bg-slate-800/80 active:scale-95"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Brand — hidden on mobile (logo lives in sidebar), visible from tablet */}
        <div className="mr-2 hidden shrink-0 items-center gap-2 md:flex">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500">
            <TrendingUp className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-bold text-white">ForexSAI</span>
        </div>

        {/* Symbol tabs — horizontally scrollable on narrow phones, flex-equal
            on tablet+ so the whole row fills the available width cleanly. */}
        <div className="flex flex-1 min-w-0 gap-2 sm:gap-3 pointer-events-auto overflow-x-auto md:overflow-visible [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          {SYMBOLS.map((symbol) => (
            <div key={symbol.id} className="flex-none basis-[26%] min-w-[96px] md:flex-1 md:basis-auto md:min-w-0">
              <SymbolTab
                symbol={symbol}
                isActive={pathname === symbol.path}
                price={prices.find((item) => item.label === symbol.label)}
                onClick={() => {
                  try {
                    router.push(symbol.path);
                  } catch (e) {
                    console.error("Navigation failed, falling back:", e);
                    window.location.href = symbol.path;
                  }
                }}
              />
            </div>
          ))}
        </div>

        {rightSlot ? (
          <div className="ml-2 hidden shrink-0 items-center gap-2 md:flex md:gap-3 pointer-events-auto">
            {rightSlot}
          </div>
        ) : (
          <div className="ml-2 hidden shrink-0 items-center gap-3 md:flex pointer-events-auto">
            <div className="h-6 w-px bg-slate-800" />
            <span className="text-xs text-slate-500">Live Market</span>
            <div className="flex h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
          </div>
        )}
      </div>
    </nav>
  );
}
