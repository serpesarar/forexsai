"use client";

/**
 * Performans Panosu — model başarı oranları (dürüst lifecycle verisi) +
 * ajan tartışması (bias) karnesi. Tek bakışta "kim iyi, kim kötü".
 */

import { useMemo } from "react";
import { TrendingUp, Users } from "lucide-react";

import type { Overview } from "@/lib/api/evolution";
import { Badge, Card, EmptyState, RateBar, Section, modelColor } from "./ui";

const MIN_RESOLVED = 10; // gürültü eşiği: 10'dan az çözülmüş sinyali olanı gösterme

export default function PerformanceBoard({
  overview,
  loading,
}: {
  overview: Overview | undefined;
  loading: boolean;
}) {
  const models = useMemo(() => {
    const rows = overview?.models?.models ?? [];
    return rows
      .filter((m) => m.with_outcome >= MIN_RESOLVED && m.ml_accuracy !== null)
      .sort((a, b) => (b.ml_accuracy ?? 0) - (a.ml_accuracy ?? 0))
      .slice(0, 14);
  }, [overview]);

  const bias = overview?.bias ?? null;

  return (
    <Section
      id="performans"
      title="Model & Ajan Performansı"
      icon={<TrendingUp size={18} />}
      subtitle={`Son ${overview?.days ?? 30} gün — dürüst lifecycle sonuçları (completed vs stopped)`}
    >
      <div className="grid gap-4 lg:grid-cols-5">
        {/* Model WR çubukları */}
        <Card className="lg:col-span-3">
          <h3 className="mb-3 text-sm font-semibold text-slate-300">
            Model Kazanma Oranları
          </h3>
          {loading && <EmptyState text="Yükleniyor…" />}
          {!loading && models.length === 0 && (
            <EmptyState text="Yeterli çözülmüş sinyal yok (veritabanı erişimini kontrol et)." />
          )}
          <div className="space-y-3">
            {models.map((m) => {
              const pct = Math.round((m.ml_accuracy ?? 0) * 100);
              const color = modelColor(m.strategy);
              return (
                <div key={m.strategy}>
                  <div className="mb-1 flex items-baseline justify-between text-xs">
                    <span className="font-medium text-slate-200">{m.strategy}</span>
                    <span className="tabular-nums text-slate-400">
                      <span className="font-semibold" style={{ color }}>
                        %{pct}
                      </span>{" "}
                      · {m.with_outcome} çözülmüş
                    </span>
                  </div>
                  <RateBar pct={pct} color={color} />
                </div>
              );
            })}
          </div>
        </Card>

        {/* Bias (ajan tartışması) karnesi */}
        <Card className="lg:col-span-2">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Users size={14} /> Ajan Tartışması (Günlük Bias) Karnesi
          </h3>
          {!bias && <EmptyState text="Bias verisi yok — henüz notlanmış tahmin bulunmuyor." />}
          {bias && (
            <div className="space-y-4">
              <div className="flex items-end gap-3">
                <span className="text-4xl font-bold tabular-nums text-slate-100">
                  {bias.overall.accuracy_pct !== null ? `%${bias.overall.accuracy_pct}` : "—"}
                </span>
                <span className="pb-1 text-xs text-slate-400">
                  genel isabet · {bias.total_graded} notlanmış tahmin
                </span>
              </div>
              <div className="space-y-2">
                {Object.entries(bias.by_symbol ?? {}).map(([sym, r]) => (
                  <div key={sym} className="flex items-center gap-2 text-xs">
                    <span className="w-20 shrink-0 font-medium text-slate-300">{sym}</span>
                    <div className="flex-1">
                      <RateBar pct={r.accuracy_pct ?? 0} color="#4F8CFF" />
                    </div>
                    <span className="w-20 shrink-0 text-right tabular-nums text-slate-400">
                      {r.accuracy_pct !== null ? `%${r.accuracy_pct}` : "—"} (n={r.n})
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-[11px] leading-relaxed text-slate-500">
                Hedef: ≥%65 iyi, ≥%55 canlıya bağlama alt sınırı.{" "}
                {bias.overall.accuracy_pct !== null && bias.overall.accuracy_pct >= 65 && (
                  <Badge tone="green">hedefin üstünde</Badge>
                )}
                {bias.overall.accuracy_pct !== null && bias.overall.accuracy_pct < 55 && (
                  <Badge tone="red">alt sınırın altında</Badge>
                )}
              </p>
            </div>
          )}
        </Card>
      </div>
    </Section>
  );
}
