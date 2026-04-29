"use client";

import dynamic from "next/dynamic";
import { Sparkles } from "lucide-react";

const MetaEnginePanel = dynamic(() => import("../panels/MetaEnginePanel"), { ssr: false });

interface Props {
  symbol: string;
}

export function MetaSignalCard({ symbol }: Props) {
  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-fuchsia-500/20 bg-slate-950/70 backdrop-blur-sm">
      <div className="flex items-center gap-2 border-b border-fuchsia-500/20 bg-fuchsia-500/5 px-3 py-2">
        <Sparkles className="h-4 w-4 text-fuchsia-400" />
        <span className="text-sm font-bold text-fuchsia-300">Meta Signal — 6-Model Fusion</span>
      </div>
      <div className="flex-1">
        <MetaEnginePanel symbol={symbol} />
      </div>
    </div>
  );
}

export default MetaSignalCard;
