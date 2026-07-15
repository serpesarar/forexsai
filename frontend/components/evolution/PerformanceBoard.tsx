"use client";

/**
 * Performans Panosu — model başarı oranları (dürüst lifecycle) + ajan bias karnesi.
 * Sol: en iyi modeller gradyan çubuklarla. Sağ: ajan karnesi büyük gauge halkasıyla.
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Users } from "lucide-react";

import type { Overview } from "@/lib/api/evolution";
import { Badge, EmptyState, GlassCard, ProgressBar, Ring, Section, modelColor, stagger } from "./ui";

const MIN_RESOLVED = 10;

function biasColor(pct: number | null): string {
  if (pct === null) return "#64748B";
  if (pct >= 65) return "#34D399";
  if (pct >= 55) return "#FBBF24";
  return "#FB7185";
}

export default function PerformanceBoard({ overview }: { overview: Overview | undefined }) {
  const models = useMemo(() => {
    const rows = overview?.models?.models ?? [];
    return rows
      .filter((m) => m.with_outcome >= MIN_RESOLVED && m.ml_accuracy !== null)
      .sort((a, b) => (b.ml_accuracy ?? 0) - (a.ml_accuracy ?? 0))
      .slice(0, 12);
  }, [overview]);

  const bias = overview?.bias ?? null;
  const overallPct = bias?.overall.accuracy_pct ?? null;

  return (
    <Section
      id="performans"
      title="Model & Ajan Performansı"
      subtitle={`Son ${overview?.days ?? 30} gün — dürüst lifecycle sonuçları`}
      accent="#5EEAD4"
      icon={<TrendingUp size={22} />}
    >
      <div className="grid gap-5 lg:grid-cols-5">
        {/* Model çubukları */}
        <GlassCard className="lg:col-span-3">
          <h3 className="mb-4 text-sm font-semibold text-slate-300">Model Kazanma Oranları</h3>
          {models.length === 0 && <EmptyState text="Yeterli çözülmüş sinyal yok — veritabanı erişimini kontrol et." />}
          <div className="space-y-3.5">
            {models.map((m, i) => {
              const pct = Math.round((m.ml_accuracy ?? 0) * 100);
              const color = modelColor(m.strategy);
              return (
                <motion.div key={m.strategy} {...stagger(i)}>
                  <div className="mb-1.5 flex items-baseline justify-between">
                    <span className="text-[13px] font-medium text-slate-200">{m.strategy}</span>
                    <span className="text-xs tabular-nums text-slate-500">
                      <span className="text-base font-bold" style={{ color }}>
                        %{pct}
                      </span>{" "}
                      <span className="ml-1">{m.with_outcome} sinyal</span>
                    </span>
                  </div>
                  <ProgressBar pct={pct} color={color} delay={i * 0.04} />
                </motion.div>
              );
            })}
          </div>
        </GlassCard>

        {/* Ajan bias karnesi */}
        <GlassCard className="lg:col-span-2" glow={biasColor(overallPct)}>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Users size={15} /> Ajan Tartışması Karnesi
          </h3>
          {!bias ? (
            <EmptyState text="Henüz notlanmış tahmin yok." />
          ) : (
            <div className="flex flex-col items-center">
              <Ring pct={overallPct ?? 0} color={biasColor(overallPct)} size={150}>
                <span className="text-4xl font-bold tabular-nums text-white">
                  {overallPct !== null ? `%${overallPct}` : "—"}
                </span>
                <span className="mt-1 text-[11px] text-slate-500">{bias.total_graded} tahmin</span>
              </Ring>

              <div className="mt-2 flex justify-center">
                {overallPct !== null && overallPct >= 65 && <Badge tone="green">hedefin üstünde</Badge>}
                {overallPct !== null && overallPct >= 55 && overallPct < 65 && <Badge tone="amber">sınırda</Badge>}
                {overallPct !== null && overallPct < 55 && <Badge tone="red">alt sınırın altında</Badge>}
              </div>

              <div className="mt-5 w-full space-y-2.5">
                {Object.entries(bias.by_symbol ?? {}).map(([sym, r], i) => (
                  <motion.div key={sym} {...stagger(i)} className="flex items-center gap-2.5 text-xs">
                    <span className="w-24 shrink-0 truncate font-medium text-slate-300">{sym}</span>
                    <div className="flex-1">
                      <ProgressBar pct={r.accuracy_pct ?? 0} color={biasColor(r.accuracy_pct)} delay={i * 0.05} />
                    </div>
                    <span className="w-16 shrink-0 text-right tabular-nums text-slate-500">
                      {r.accuracy_pct !== null ? `%${r.accuracy_pct}` : "—"}
                    </span>
                  </motion.div>
                ))}
              </div>
              <p className="mt-4 text-center text-[11px] text-slate-500">Hedef: ≥%65 iyi · ≥%55 canlıya alma alt sınırı</p>
            </div>
          )}
        </GlassCard>
      </div>
    </Section>
  );
}
