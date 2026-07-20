"use client";

/**
 * Performans Panosu — model başarı oranları (dürüst lifecycle) + ajan bias karnesi.
 * Sol: en iyi modeller gradyan çubuklarla — TIKLA → sembol/yön detay çekmecesi.
 * Sağ: ajan karnesi büyük gauge halkasıyla — sembole tıkla → etiket/güven kırılımı.
 */

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight, TrendingUp, Users, X } from "lucide-react";

import type { BiasReport, Overview } from "@/lib/api/evolution";
import ModelDetailDrawer from "./ModelDetailDrawer";
import { Badge, EmptyState, GlassCard, ProgressBar, Ring, Section, Skeleton, modelColor, stagger } from "./ui";

const MIN_RESOLVED = 10;

function biasColor(pct: number | null): string {
  if (pct === null) return "#64748B";
  if (pct >= 65) return "#34D399";
  if (pct >= 55) return "#FBBF24";
  return "#FB7185";
}

/** Bias karnesi sembol detayı — etiket (çalıştırma saati) + güven kovası kırılımı. */
function BiasDetailSheet({ bias, symbol, onClose }: { bias: BiasReport; symbol: string; onClose: () => void }) {
  const symRate = bias.by_symbol?.[symbol];
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-3 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 40, opacity: 0, scale: 0.98 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: 40, opacity: 0, scale: 0.98 }}
        transition={{ type: "spring", damping: 28, stiffness: 320 }}
        className="w-full max-w-lg overflow-hidden rounded-3xl border border-white/10 bg-[#0B0F17] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3.5">
          <span className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <Users size={15} className="text-violet-300" /> {symbol} — ajan karnesi
          </span>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
          {symRate && (
            <p className="mb-4 text-center text-sm text-slate-300">
              <span className="text-2xl font-bold" style={{ color: biasColor(symRate.accuracy_pct) }}>
                {symRate.accuracy_pct !== null ? `%${symRate.accuracy_pct}` : "—"}
              </span>{" "}
              isabet · {symRate.correct}/{symRate.n} tahmin
            </p>
          )}
          {bias.by_symbol_horizon?.[symbol] && (
            <>
              <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Ufka göre isabet ({symbol})
              </h4>
              <div className="mb-4 space-y-2">
                {Object.entries(bias.by_symbol_horizon[symbol]).map(([h, r]) => (
                  <div key={h} className="flex items-center gap-2.5 text-xs">
                    <span className="w-32 shrink-0 truncate font-medium text-slate-300">+{h.replace("m", " dk")}</span>
                    <div className="flex-1">
                      <ProgressBar pct={r.accuracy_pct ?? 0} color={biasColor(r.accuracy_pct)} />
                    </div>
                    <span className="w-20 shrink-0 text-right tabular-nums text-slate-500">
                      {r.accuracy_pct !== null ? `%${r.accuracy_pct}` : "—"} · {r.n}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
          <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Çalıştırma etiketine göre (tüm semboller)
          </h4>
          <div className="mb-4 space-y-2">
            {Object.entries(bias.by_run_label ?? {}).map(([label, r]) => (
              <div key={label} className="flex items-center gap-2.5 text-xs">
                <span className="w-32 shrink-0 truncate font-medium text-slate-300">{label}</span>
                <div className="flex-1">
                  <ProgressBar pct={r.accuracy_pct ?? 0} color={biasColor(r.accuracy_pct)} />
                </div>
                <span className="w-20 shrink-0 text-right tabular-nums text-slate-500">
                  {r.accuracy_pct !== null ? `%${r.accuracy_pct}` : "—"} · {r.n}
                </span>
              </div>
            ))}
          </div>
          <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Güven kovasına göre (tüm semboller)
          </h4>
          <div className="space-y-2">
            {Object.entries(bias.by_confidence_bucket ?? {}).map(([bucket, r]) => (
              <div key={bucket} className="flex items-center gap-2.5 text-xs">
                <span className="w-32 shrink-0 truncate font-medium text-slate-300">{bucket}</span>
                <div className="flex-1">
                  <ProgressBar pct={r.accuracy_pct ?? 0} color={biasColor(r.accuracy_pct)} />
                </div>
                <span className="w-20 shrink-0 text-right tabular-nums text-slate-500">
                  {r.accuracy_pct !== null ? `%${r.accuracy_pct}` : "—"} · {r.n}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-center text-[10px] text-slate-600">
            Etiket ve güven kırılımları tüm sembollerin toplamıdır — hangi saat/etiket en isabetli görülür.
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function PerformanceBoard({ overview }: { overview: Overview | undefined }) {
  const [openModel, setOpenModel] = useState<string | null>(null);
  const [openBiasSymbol, setOpenBiasSymbol] = useState<string | null>(null);
  const models = useMemo(() => {
    const rows = overview?.models?.models ?? [];
    return rows
      .filter((m) => m.with_outcome >= MIN_RESOLVED && m.ml_accuracy !== null)
      .sort((a, b) => (b.ml_accuracy ?? 0) - (a.ml_accuracy ?? 0))
      .slice(0, 12);
  }, [overview]);

  const bias = overview?.bias ?? null;
  // ANA METRİK: birincil ufukta yönlü isabet (çekimserler hariç). LEGACY
  // gün-kapanışı overall'ı yalnız primary yoksa (eski backend) kullanılır.
  const primary = bias?.primary_intraday ?? null;
  const overallPct = primary?.overall?.accuracy_pct ?? bias?.overall.accuracy_pct ?? null;
  const overallN = primary?.overall?.n ?? bias?.total_graded ?? 0;

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
          {(!overview || (models.length === 0 && overview.models_warming)) && (
            <div className="space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-11/12" />
              <Skeleton className="h-8 w-4/5" />
              <Skeleton className="h-8 w-3/4" />
              {overview?.models_warming && (
                <p className="text-center text-[11px] text-slate-500">
                  Veriler ısınıyor — birazdan otomatik gelecek…
                </p>
              )}
            </div>
          )}
          {overview && !overview.models_warming && models.length === 0 && (
            <EmptyState text="Yeterli çözülmüş sinyal yok — veritabanı erişimini kontrol et." />
          )}
          <div className="space-y-1.5">
            {models.map((m, i) => {
              const pct = Math.round((m.ml_accuracy ?? 0) * 100);
              const color = modelColor(m.strategy);
              return (
                <motion.button
                  key={m.strategy}
                  {...stagger(i)}
                  onClick={() => setOpenModel(m.strategy)}
                  className="group/row block w-full rounded-xl px-2 py-2 text-left transition hover:bg-white/[0.04]"
                  title="Sembol bazlı detayı aç"
                >
                  <div className="mb-1.5 flex items-baseline justify-between">
                    <span className="flex items-center gap-1 text-[13px] font-medium text-slate-200">
                      {m.strategy}
                      <ChevronRight size={12} className="text-slate-600 opacity-0 transition group-hover/row:translate-x-0.5 group-hover/row:opacity-100" />
                    </span>
                    <span className="text-xs tabular-nums text-slate-500">
                      <span className="text-base font-bold" style={{ color }}>
                        %{pct}
                      </span>{" "}
                      <span className="ml-1">{m.with_outcome} sinyal</span>
                    </span>
                  </div>
                  <ProgressBar pct={pct} color={color} delay={i * 0.04} />
                </motion.button>
              );
            })}
          </div>
          {models.length > 0 && (
            <p className="mt-3 text-center text-[10px] text-slate-600">Bir modele tıkla → sembol & yön kırılımı</p>
          )}
        </GlassCard>

        {/* Ajan bias karnesi */}
        <GlassCard className="lg:col-span-2" glow={biasColor(overallPct)}>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Users size={15} /> Ajan Tartışması Karnesi
          </h3>
          {!overview || (bias === null && overview.bias_warming) ? (
            <div className="space-y-4">
              <div className="flex justify-center">
                <Skeleton className="h-[150px] w-[150px] rounded-full" />
              </div>
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-5 w-4/5" />
              {overview?.bias_warming && (
                <p className="text-center text-[11px] text-slate-500">
                  Veriler ısınıyor — birazdan otomatik gelecek…
                </p>
              )}
            </div>
          ) : !bias ? (
            <EmptyState text="Henüz notlanmış tahmin yok." />
          ) : (
            <div className="flex flex-col items-center">
              <Ring pct={overallPct ?? 0} color={biasColor(overallPct)} size={150}>
                <span className="text-4xl font-bold tabular-nums text-white">
                  {overallPct !== null ? `%${overallPct}` : "—"}
                </span>
                <span className="mt-1 text-[11px] text-slate-500">
                  {overallN} yönlü çağrı
                </span>
              </Ring>
              {primary && (
                <p className="mt-1.5 text-center text-[10px] text-slate-500">
                  birincil ufukta yönlü isabet — çekimserler (nötr) hariç
                </p>
              )}

              <div className="mt-2 flex justify-center">
                {overallPct !== null && overallPct >= 65 && <Badge tone="green">hedefin üstünde</Badge>}
                {overallPct !== null && overallPct >= 55 && overallPct < 65 && <Badge tone="amber">sınırda</Badge>}
                {overallPct !== null && overallPct < 55 && <Badge tone="red">alt sınırın altında</Badge>}
              </div>

              <div className="mt-5 w-full space-y-1">
                {(primary
                  ? Object.entries(primary.per_symbol).map(([sym, s]) => ({
                      sym,
                      pct: s.accuracy_pct,
                      sub: `${s.horizon_min}dk · ${s.n} çağrı${s.abstain_n ? ` · ${s.abstain_n} çekimser` : ""}`,
                    }))
                  : Object.entries(bias.by_symbol ?? {}).map(([sym, r]) => ({
                      sym,
                      pct: r.accuracy_pct,
                      sub: `${r.n} tahmin`,
                    }))
                ).map((row, i) => (
                  <motion.button
                    key={row.sym}
                    {...stagger(i)}
                    onClick={() => setOpenBiasSymbol(row.sym)}
                    className="flex w-full items-center gap-2.5 rounded-lg px-1.5 py-1.5 text-xs transition hover:bg-white/[0.04]"
                    title="Saat/etiket & ufuk kırılımını aç"
                  >
                    <span className="w-24 shrink-0 truncate text-left">
                      <span className="block font-medium text-slate-300">{row.sym}</span>
                      <span className="block text-[9px] text-slate-600">{row.sub}</span>
                    </span>
                    <div className="flex-1">
                      <ProgressBar pct={row.pct ?? 0} color={biasColor(row.pct)} delay={i * 0.05} />
                    </div>
                    <span className="w-16 shrink-0 text-right tabular-nums text-slate-500">
                      {row.pct !== null ? `%${row.pct}` : "—"}
                    </span>
                  </motion.button>
                ))}
              </div>
              <p className="mt-4 text-center text-[11px] text-slate-500">Hedef: ≥%65 iyi · ≥%55 canlıya alma alt sınırı</p>
            </div>
          )}
        </GlassCard>
      </div>

      <AnimatePresence>
        {openModel && (
          <ModelDetailDrawer
            strategy={openModel}
            days={overview?.days ?? 30}
            onClose={() => setOpenModel(null)}
          />
        )}
        {openBiasSymbol && bias && (
          <BiasDetailSheet bias={bias} symbol={openBiasSymbol} onClose={() => setOpenBiasSymbol(null)} />
        )}
      </AnimatePresence>
    </Section>
  );
}
