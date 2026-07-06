"use client";

import { useState } from "react";
import { ChevronDown, ShieldAlert } from "lucide-react";
import { useDailyBias, type DailyBiasDirection } from "../../lib/api/dailyBias";

/**
 * DailyBiasCard — MiroShark's once-a-day NASDAQ macro bias, shown as a slim
 * top-bar badge. NASDAQ-only: renders nothing for other symbols. Click to
 * expand reason_summary + invalid_if.
 */

const NASDAQ_SYMBOL = "NDX.INDX";

const BIAS_STYLES: Record<DailyBiasDirection, { label: string; chip: string; dot: string }> = {
  bullish: { label: "BULLISH", chip: "border-green-500/40 bg-green-500/10 text-green-300", dot: "bg-green-400" },
  bearish: { label: "BEARISH", chip: "border-red-500/40 bg-red-500/10 text-red-300", dot: "bg-red-400" },
  neutral: { label: "NÖTR", chip: "border-slate-500/40 bg-slate-500/10 text-slate-300", dot: "bg-slate-400" },
  choppy: { label: "CHOPPY", chip: "border-amber-500/40 bg-amber-500/10 text-amber-300", dot: "bg-amber-400" },
};

const TRADE_MODE_LABELS: Record<string, string> = {
  buy_dips_only: "Sadece dip alımı",
  sell_rallies_only: "Sadece ralli satışı",
  range_scalp: "Range scalp",
  wait_and_see: "Bekle-gör",
};

interface Props {
  symbol: string;
}

export default function DailyBiasCard({ symbol }: Props) {
  const [expanded, setExpanded] = useState(false);
  const isNasdaq = symbol === NASDAQ_SYMBOL;
  const { data, isLoading } = useDailyBias(symbol, isNasdaq);

  // Scope guard + hide until there is something meaningful to show.
  if (!isNasdaq) return null;
  if (isLoading) {
    return (
      <div className="h-9 animate-pulse rounded-xl border border-slate-800 bg-slate-900/50" />
    );
  }
  if (!data || data.status !== "ok" || !data.bias) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-500">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
        Günlük NASDAQ bias yok (MiroShark)
      </div>
    );
  }

  const bias = data.bias;
  const style = BIAS_STYLES[bias.nasdaq_daily_bias] ?? BIAS_STYLES.neutral;
  const invalidated = Boolean(bias.is_invalidated);
  const tradeMode = bias.trade_mode ? TRADE_MODE_LABELS[bias.trade_mode] ?? bias.trade_mode : null;
  const hasDetail = Boolean(bias.reason_summary || bias.invalid_if);

  return (
    <div className={`rounded-xl border bg-slate-950/60 ${invalidated ? "border-slate-700" : style.chip.split(" ")[0]}`}>
      <button
        type="button"
        onClick={() => hasDetail && setExpanded((v) => !v)}
        className="flex w-full items-center gap-3 px-3 py-2 text-left"
      >
        <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">
          Günlük Bias
        </span>

        <span
          className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold ${
            invalidated ? "border-slate-600 bg-slate-800/60 text-slate-400 line-through" : style.chip
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${invalidated ? "bg-slate-500" : style.dot}`} />
          {style.label}
        </span>

        <span className="text-xs text-slate-400">%{Math.round(bias.confidence)}</span>

        {tradeMode && !invalidated && (
          <span className="hidden text-xs text-slate-500 sm:inline">· {tradeMode}</span>
        )}

        {invalidated && (
          <span className="inline-flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-red-300">
            <ShieldAlert className="h-3 w-3" /> GEÇERSİZ
          </span>
        )}

        {hasDetail && (
          <ChevronDown
            className={`ml-auto h-4 w-4 shrink-0 text-slate-500 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        )}
      </button>

      {expanded && hasDetail && (
        <div className="space-y-2 border-t border-slate-800 px-3 py-2 text-xs">
          {bias.reason_summary && (
            <p className="text-slate-300">{bias.reason_summary}</p>
          )}
          {bias.invalid_if && (
            <p className="text-slate-500">
              <span className="font-medium text-slate-400">Geçersiz olursa:</span> {bias.invalid_if}
            </p>
          )}
          {(bias.main_support != null || bias.main_resistance != null) && (
            <p className="text-slate-500">
              {bias.main_support != null && <>Destek {bias.main_support} </>}
              {bias.main_resistance != null && <>· Direnç {bias.main_resistance}</>}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
