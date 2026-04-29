"use client";

import { useMemo } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { useLivePrices } from "../../hooks/useLivePrices";
import type { SymbolConfig } from "../../lib/symbolConfig";

interface Props {
  config: SymbolConfig;
}

export function LivePriceBar({ config }: Props) {
  const { tickers, isLoading } = useLivePrices();
  const ticker = useMemo(() => tickers.find((t) => t.label === config.label), [tickers, config.label]);
  const isPositive = (ticker?.change || "").startsWith("+");

  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 rounded-2xl border ${config.theme.accentBorder} bg-slate-950/70 px-4 py-3 backdrop-blur-sm`}>
      <div className="flex items-center gap-3 min-w-0">
        <div className={`rounded-full ${config.theme.accentBg} ${config.theme.accentText} px-2.5 py-1 text-xs font-bold uppercase tracking-wider`}>
          {config.label}
        </div>
        <div className="min-w-0">
          <div className="font-mono text-xl font-black text-white sm:text-2xl">
            {isLoading || !ticker ? "--" : ticker.price}
          </div>
          <div className="text-[11px] text-slate-500">{config.symbol}</div>
        </div>
      </div>
      {!isLoading && ticker?.change && ticker.change !== "--%" && (
        <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-bold ${isPositive ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
          {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
          {ticker.change}
        </span>
      )}
    </div>
  );
}

export default LivePriceBar;
