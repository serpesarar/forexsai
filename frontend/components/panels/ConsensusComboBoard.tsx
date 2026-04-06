"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export interface ConsensusComboRow {
  symbol: string;
  direction: "BUY" | "SELL";
  combination: string;
  model_count: number;
  occurrences: number;
  wins: number;
  losses: number;
  expired: number;
  resolved_count: number;
  win_rate: number;
  completion_rate: number;
  profit_factor: number;
  expectancy: number;
  stability_score: number;
  quality: string;
}

export interface ConsensusDirectionSection {
  total_rows: number;
  most_frequent: ConsensusComboRow[];
  best_stable: ConsensusComboRow[];
  top_quality_counts: {
    strong: number;
    usable: number;
    weak: number;
    weak_sample: number;
  };
}

export interface ConsensusSymbolView {
  symbol: string;
  report_generated_at?: string;
  report_path?: string;
  parameters?: {
    lookback_days?: number;
    bucket_minutes?: number;
    min_occurrences?: number;
    target_level?: string;
    price_timeframe?: string;
  };
  buy: ConsensusDirectionSection;
  sell: ConsensusDirectionSection;
}

interface ConsensusComboBoardProps {
  data: ConsensusSymbolView;
  compact?: boolean;
  maxRows?: number;
}

function formatPercent(value: number | undefined): string {
  return `${Math.round((value || 0) * 100)}%`;
}

function formatFactor(value: number | undefined): string {
  const numeric = value || 0;
  if (!numeric || numeric === 999) return "∞";
  return `${numeric.toFixed(2)}x`;
}

function metricTone(value: number, positiveThreshold: number, neutralThreshold: number) {
  if (value >= positiveThreshold) return "text-[#16C784]";
  if (value >= neutralThreshold) return "text-[#F5A623]";
  return "text-[#EA3943]";
}

function QualityPill({ value }: { value: string }) {
  const normalized = String(value || "weak").toLowerCase();
  const tone = normalized === "strong"
    ? "bg-[#16C784]/12 text-[#16C784] border-[#16C784]/20"
    : normalized === "usable"
      ? "bg-[#4F8CFF]/12 text-[#4F8CFF] border-[#4F8CFF]/20"
      : normalized === "weak_sample"
        ? "bg-[#F5A623]/12 text-[#F5A623] border-[#F5A623]/20"
        : "bg-white/[0.04] text-[#9AA4B2] border-white/[0.08]";
  return <span className={`px-2 py-0.5 rounded-md border text-[10px] font-semibold uppercase tracking-wide ${tone}`}>{normalized}</span>;
}

function ComboChips({ combination, direction }: { combination: string; direction: "BUY" | "SELL" }) {
  const tone = direction === "BUY"
    ? "bg-[#16C784]/10 text-[#16C784] border-[#16C784]/20"
    : "bg-[#EA3943]/10 text-[#EA3943] border-[#EA3943]/20";

  return (
    <div className="flex flex-wrap gap-1.5">
      {String(combination || "").split("+").filter(Boolean).map((item) => (
        <span key={`${combination}-${item}`} className={`px-2 py-0.5 rounded-md border text-[10px] font-semibold uppercase tracking-wide ${tone}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

function ComboRowCard({ row, compact = false, emphasis = "stable" }: { row: ConsensusComboRow; compact?: boolean; emphasis?: "stable" | "frequent" }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-black/20 p-3">
      <div className="flex items-start justify-between gap-3">
        <ComboChips combination={row.combination} direction={row.direction} />
        <QualityPill value={row.quality} />
      </div>
      <div className={`grid ${compact ? "grid-cols-2" : "grid-cols-4"} gap-2 mt-3 text-[11px]`}>
        <div>
          <div className="text-[#6B7280] uppercase tracking-wide">Occ</div>
          <div className="text-[#E6EDF3] font-semibold">{row.occurrences}</div>
        </div>
        <div>
          <div className="text-[#6B7280] uppercase tracking-wide">WR</div>
          <div className={`font-semibold ${metricTone(row.win_rate || 0, 0.6, 0.5)}`}>{formatPercent(row.win_rate)}</div>
        </div>
        <div>
          <div className="text-[#6B7280] uppercase tracking-wide">Comp</div>
          <div className={`font-semibold ${metricTone(row.completion_rate || 0, 0.6, 0.4)}`}>{formatPercent(row.completion_rate)}</div>
        </div>
        <div>
          <div className="text-[#6B7280] uppercase tracking-wide">{emphasis === "stable" ? "Stable" : "PF"}</div>
          <div className={`font-semibold ${emphasis === "stable" ? metricTone(row.stability_score || 0, 1, 0.5) : metricTone(row.profit_factor || 0, 1, 0.8)}`}>
            {emphasis === "stable" ? (row.stability_score || 0).toFixed(2) : formatFactor(row.profit_factor)}
          </div>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-[11px] text-[#6B7280]">
        <span>{row.wins}/{row.resolved_count} resolved</span>
        <span>{row.expired} expired</span>
      </div>
    </div>
  );
}

function DirectionColumn({
  direction,
  section,
  compact,
  maxRows,
}: {
  direction: "BUY" | "SELL";
  section: ConsensusDirectionSection;
  compact?: boolean;
  maxRows: number;
}) {
  const isBuy = direction === "BUY";
  const tone = isBuy
    ? "from-[#16C784]/20 to-[#16C784]/5 border-[#16C784]/15"
    : "from-[#EA3943]/20 to-[#EA3943]/5 border-[#EA3943]/15";
  const labelTone = isBuy ? "text-[#16C784]" : "text-[#EA3943]";

  return (
    <div className={`rounded-2xl border bg-gradient-to-b ${tone} p-4`}>
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          {isBuy ? <ArrowUpRight className={`w-4 h-4 ${labelTone}`} /> : <ArrowDownRight className={`w-4 h-4 ${labelTone}`} />}
          <span className={`text-sm font-semibold ${labelTone}`}>{direction} yönü için önemli kombinasyonlar</span>
        </div>
        <span className="text-[11px] text-[#9AA4B2]">{section.total_rows} combo</span>
      </div>
      <div className={`grid ${compact ? "grid-cols-1" : "grid-cols-1 xl:grid-cols-2"} gap-3`}>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[#E6EDF3]">Best Stable</span>
            <span className="text-[10px] text-[#6B7280]">strong {section.top_quality_counts.strong} • usable {section.top_quality_counts.usable}</span>
          </div>
          <div className="space-y-2.5">
            {section.best_stable.slice(0, maxRows).map((row) => (
              <ComboRowCard key={`${direction}-stable-${row.combination}`} row={row} compact={compact} emphasis="stable" />
            ))}
            {section.best_stable.length === 0 && <div className="text-[12px] text-[#6B7280]">Yeterli stable kombinasyon yok.</div>}
          </div>
        </div>
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[#E6EDF3]">Most Frequent</span>
            <span className="text-[10px] text-[#6B7280]">en çok tekrar edenler</span>
          </div>
          <div className="space-y-2.5">
            {section.most_frequent.slice(0, maxRows).map((row) => (
              <ComboRowCard key={`${direction}-frequent-${row.combination}`} row={row} compact={compact} emphasis="frequent" />
            ))}
            {section.most_frequent.length === 0 && <div className="text-[12px] text-[#6B7280]">Yeterli frequent kombinasyon yok.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ConsensusComboBoard({ data, compact = false, maxRows = 4 }: ConsensusComboBoardProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#6B7280]">
        <span>{data.symbol}</span>
        <span>•</span>
        <span>{data.parameters?.lookback_days || 0}D</span>
        <span>•</span>
        <span>{data.parameters?.bucket_minutes || 0}m bucket</span>
        <span>•</span>
        <span>{data.parameters?.target_level || "TP1"}</span>
      </div>
      <div className={`grid ${compact ? "grid-cols-1" : "grid-cols-1 2xl:grid-cols-2"} gap-4`}>
        <DirectionColumn direction="BUY" section={data.buy} compact={compact} maxRows={maxRows} />
        <DirectionColumn direction="SELL" section={data.sell} compact={compact} maxRows={maxRows} />
      </div>
    </div>
  );
}
