"use client";

import { useEffect, useState } from "react";
import { Trophy } from "lucide-react";
import { fetcher } from "../../lib/api";
import { MODEL_COLORS, type ModelKey } from "../../lib/symbolConfig";

interface ModelRow {
  model_type: string;
  total: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor?: number;
  target_hit_rate?: number;
}

interface AccuracyResponse {
  success?: boolean;
  data?: { models?: ModelRow[] };
  models?: ModelRow[];
}

interface Props {
  symbol: string;
  days?: number;
}

const MODEL_ORDER: Array<{ key: ModelKey; match: (m: string) => boolean; label: string }> = [
  { key: "ml", match: (m) => typeof m === "string" && m.startsWith("ml"), label: "ML" },
  { key: "emel", match: (m) => m === "emel" || m === "emel_inverse", label: "EMEL" },
  { key: "pulse1", match: (m) => m === "pulse1", label: "Pulse 1" },
  { key: "pulse2", match: (m) => m === "pulse2", label: "Pulse 2" },
  { key: "pulse3", match: (m) => m === "pulse3", label: "Pulse 3" },
  { key: "smc", match: (m) => m === "smc", label: "SMC" },
  { key: "ai", match: (m) => m === "ai_panel" || m === "meta", label: "AI / Meta" },
];

function winRateColor(wr: number): string {
  if (wr >= 0.6) return "text-emerald-400";
  if (wr >= 0.5) return "text-amber-400";
  return "text-rose-400";
}

export function PerformanceScoreboard({ symbol, days = 30 }: Props) {
  const [rows, setRows] = useState<ModelRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetcher<AccuracyResponse>(`/api/learning/accuracy-by-model?days=${days}&symbol=${encodeURIComponent(symbol)}`)
      .then((res) => {
        if (cancelled) return;
        const models = res?.data?.models ?? res?.models ?? [];
        setRows(models);
        setLoading(false);
      })
      .catch((e) => {
        if (cancelled) return;
        setErr(e?.message || "load failed");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, days]);

  // Aggregate ML variants into a single row per MODEL_ORDER entry
  const aggregated = MODEL_ORDER.map((def) => {
    const matching = rows.filter((r) => def.match(r.model_type));
    if (matching.length === 0) return { ...def, total: 0, wins: 0, losses: 0, win_rate: 0 };
    const total = matching.reduce((a, m) => a + (m.total || 0), 0);
    const wins = matching.reduce((a, m) => a + (m.wins || 0), 0);
    const losses = matching.reduce((a, m) => a + (m.losses || 0), 0);
    const wr = total > 0 ? wins / (wins + losses || 1) : 0;
    return { ...def, total, wins, losses, win_rate: wr };
  });

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="mb-3 flex items-center gap-2">
        <Trophy className="h-4 w-4 text-amber-400" />
        <h3 className="text-sm font-bold text-slate-100">Model Performance · {days}d</h3>
        {loading && <span className="text-[11px] text-slate-500">loading…</span>}
        {err && <span className="text-[11px] text-rose-400">{err}</span>}
      </div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {aggregated.map((m) => {
          const c = MODEL_COLORS[m.key];
          const wrPct = (m.win_rate * 100).toFixed(1);
          return (
            <div
              key={m.key}
              className={`min-w-[160px] flex-shrink-0 rounded-xl border ${c.border} ${c.bg} p-3`}
            >
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${c.dot}`} />
                <span className={`text-xs font-bold ${c.text}`}>{m.label}</span>
              </div>
              <div className={`mt-2 font-mono text-2xl font-black ${winRateColor(m.win_rate)}`}>
                {m.total === 0 ? "—" : `${wrPct}%`}
              </div>
              <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                <span>{m.total} signals</span>
                <span>
                  <span className="text-emerald-400">{m.wins}W</span> ·{" "}
                  <span className="text-rose-400">{m.losses}L</span>
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default PerformanceScoreboard;
