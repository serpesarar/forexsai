"use client";

import dynamic from "next/dynamic";
import { Fish, Brain } from "lucide-react";

const COTWhalePanel = dynamic(() => import("../panels/COTWhalePanel"), { ssr: false });
const ClaudeAnalysisPanelV2 = dynamic(() => import("../ClaudeAnalysisPanelV2"), { ssr: false });

interface Props {
  symbol: string;
  symbolLabel: string;
}

function Shell({
  title,
  accent,
  icon,
  children,
}: {
  title: string;
  accent: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex flex-col overflow-hidden rounded-2xl border bg-slate-950/70 backdrop-blur-sm ${accent}`}>
      <div className="flex items-center gap-2 border-b border-inherit px-3 py-2">
        {icon}
        <span className="text-sm font-bold text-slate-200">{title}</span>
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );
}

export function ContextCards({ symbol, symbolLabel }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Shell
        title="COT + Whale Intelligence"
        accent="border-sky-500/20"
        icon={<Fish className="h-4 w-4 text-sky-400" />}
      >
        <COTWhalePanel symbol={symbol} />
      </Shell>
      <Shell
        title="AI Panel — Hourly Analysis"
        accent="border-amber-500/20"
        icon={<Brain className="h-4 w-4 text-amber-400" />}
      >
        <ClaudeAnalysisPanelV2 symbol={symbol} symbolLabel={symbolLabel} />
      </Shell>
    </div>
  );
}

export default ContextCards;
