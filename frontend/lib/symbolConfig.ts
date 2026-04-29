export type SymbolSlug = "nasdaq" | "xauusd" | "dax" | "oil";

export interface SymbolTheme {
  accent: string;
  accentBg: string;
  accentBorder: string;
  accentText: string;
  gradient: string;
}

export interface SymbolConfig {
  slug: SymbolSlug;
  symbol: string;
  label: string;
  storageKey: string;
  theme: SymbolTheme;
}

export const SYMBOL_CONFIGS: Record<SymbolSlug, SymbolConfig> = {
  nasdaq: {
    slug: "nasdaq",
    symbol: "NDX.INDX",
    label: "NASDAQ",
    storageKey: "nasdaq-dashboard-layout-v5",
    theme: {
      accent: "emerald",
      accentBg: "bg-emerald-500/10",
      accentBorder: "border-emerald-500/20",
      accentText: "text-emerald-400",
      gradient: "from-emerald-500/20 to-cyan-500/10",
    },
  },
  xauusd: {
    slug: "xauusd",
    symbol: "XAUUSD",
    label: "XAU/USD",
    storageKey: "xauusd-dashboard-layout-v5",
    theme: {
      accent: "amber",
      accentBg: "bg-amber-500/10",
      accentBorder: "border-amber-500/20",
      accentText: "text-amber-400",
      gradient: "from-amber-500/20 to-orange-500/10",
    },
  },
  dax: {
    slug: "dax",
    symbol: "GDAXI.INDX",
    label: "DAX",
    storageKey: "dax-dashboard-layout-v5",
    theme: {
      accent: "blue",
      accentBg: "bg-blue-500/10",
      accentBorder: "border-blue-500/20",
      accentText: "text-blue-400",
      gradient: "from-blue-500/20 to-indigo-500/10",
    },
  },
  oil: {
    slug: "oil",
    symbol: "USOIL.FOREX",
    label: "US OIL",
    storageKey: "oil-dashboard-layout-v5",
    theme: {
      accent: "orange",
      accentBg: "bg-orange-500/10",
      accentBorder: "border-orange-500/20",
      accentText: "text-orange-400",
      gradient: "from-orange-500/20 to-red-500/10",
    },
  },
};

export function getSymbolBySlug(slug: string): SymbolConfig | null {
  return SYMBOL_CONFIGS[slug as SymbolSlug] ?? null;
}

export const MODEL_COLORS = {
  ml: { text: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/30", dot: "bg-blue-500" },
  emel: { text: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500/30", dot: "bg-purple-500" },
  pulse1: { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30", dot: "bg-orange-500" },
  pulse2: { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30", dot: "bg-orange-500" },
  pulse3: { text: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/30", dot: "bg-orange-500" },
  smc: { text: "text-teal-400", bg: "bg-teal-500/10", border: "border-teal-500/30", dot: "bg-teal-500" },
  ai: { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", dot: "bg-amber-500" },
} as const;

export type ModelKey = keyof typeof MODEL_COLORS;
