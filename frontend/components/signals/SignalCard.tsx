"use client";

import type { ReactNode } from "react";
import { MODEL_COLORS, type ModelKey } from "../../lib/symbolConfig";

interface Props {
  modelKey: ModelKey;
  title: string;
  subtitle?: string;
  weight?: number;
  children: ReactNode;
}

/**
 * SignalCard — wraps an existing panel component as-is (adapter pattern).
 * The card provides only a thin colored title strip; the wrapped panel
 * renders at its native height with no scroll clipping.
 */
export function SignalCard({ modelKey, title, subtitle, weight, children }: Props) {
  const c = MODEL_COLORS[modelKey];

  return (
    <div className={`flex flex-col overflow-hidden rounded-2xl border ${c.border} bg-slate-950/70 backdrop-blur-sm shadow-lg`}>
      <div className={`flex items-center justify-between gap-2 border-b ${c.border} ${c.bg} px-3 py-2`}>
        <div className="flex min-w-0 items-center gap-2">
          <span className={`h-2 w-2 flex-shrink-0 rounded-full ${c.dot}`} />
          <div className="min-w-0">
            <div className={`truncate text-sm font-bold ${c.text}`}>{title}</div>
            {subtitle && <div className="truncate text-[11px] text-slate-500">{subtitle}</div>}
          </div>
        </div>
        {typeof weight === "number" && (
          <span className="flex-shrink-0 rounded-full border border-slate-700/60 bg-slate-900/60 px-2 py-0.5 text-[10px] font-mono text-slate-400">
            w {weight.toFixed(2)}
          </span>
        )}
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );
}

export default SignalCard;
