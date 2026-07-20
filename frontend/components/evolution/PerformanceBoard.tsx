"use client";

/**
 * Performans Panosu — model başarı oranları (dürüst lifecycle) + ajan bias karnesi.
 * Sol: en iyi modeller gradyan çubuklarla — TIKLA → sembol/yön detay çekmecesi.
 * Sağ: ajan karnesi büyük gauge halkasıyla — sembole tıkla → etiket/güven kırılımı.
 */

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight, MoveRight, TrendingDown, TrendingUp, Users, X } from "lucide-react";

import type { BiasReport, BiasTimelineCell, Overview } from "@/lib/api/evolution";
import ModelDetailDrawer from "./ModelDetailDrawer";
import { Badge, EmptyState, GlassCard, ProgressBar, Ring, Section, Skeleton, cx, modelColor, stagger } from "./ui";

const MIN_RESOLVED = 10;

function biasColor(pct: number | null): string {
  if (pct === null) return "#64748B";
  if (pct >= 65) return "#34D399";
  if (pct >= 55) return "#FBBF24";
  if (pct >= 45) return "#FB923C";
  return "#FB7185";
}

// ── Zaman-duyarlı trend: son dönem vs önceki dönem ────────────────────────

interface TrendInfo {
  recentPct: number | null; // son yarının isabeti (renk bundan gelir)
  olderPct: number | null;
  delta: number | null; // + iyileşiyor, − kötüleşiyor
  dirCount: number;
}

/** Yönlü hücreleri ikiye böl: eski yarı vs yeni yarı — başarı zamanla nereye gidiyor? */
function timelineTrend(timeline: BiasTimelineCell[] | undefined): TrendInfo {
  const dir = (timeline ?? []).filter((c) => c.ok !== null);
  if (dir.length < 2) return { recentPct: null, olderPct: null, delta: null, dirCount: dir.length };
  const half = Math.floor(dir.length / 2);
  const older = dir.slice(0, half);
  const recent = dir.slice(half);
  const pct = (arr: BiasTimelineCell[]) =>
    arr.length ? Math.round((arr.filter((c) => c.ok).length / arr.length) * 100) : null;
  const olderPct = pct(older);
  const recentPct = pct(recent);
  return {
    recentPct,
    olderPct,
    delta: recentPct !== null && olderPct !== null ? recentPct - olderPct : null,
    dirCount: dir.length,
  };
}

function TrendArrow({ delta }: { delta: number | null }) {
  if (delta === null) return null;
  if (delta > 5) return <TrendingUp size={13} className="text-emerald-400" />;
  if (delta < -5) return <TrendingDown size={13} className="text-rose-400" />;
  return <MoveRight size={13} className="text-slate-500" />;
}

// ── Karar dayanıklılık ısı haritası ──────────────────────────────────────
// Satır = sembol, sütun = karardan sonra geçen süre (10dk → 6s).
// Hücre rengi o ufuktaki yönlü isabet — karar zamanla bozuluyorsa satır
// soldan sağa yeşilden kırmızıya söner.

const HORIZON_ORDER = ["10m", "30m", "60m", "90m", "120m", "180m", "240m", "300m", "360m"];
const HORIZON_LABELS: Record<string, string> = {
  "10m": "10dk", "30m": "30dk", "60m": "1s", "90m": "1.5s", "120m": "2s",
  "180m": "3s", "240m": "4s", "300m": "5s", "360m": "6s",
};

function heatCellStyle(pct: number | null, n: number): React.CSSProperties {
  if (pct === null || n === 0) return { background: "rgba(148,163,184,0.06)", color: "#475569" };
  const c = biasColor(pct);
  const alpha = n < 3 ? "22" : "40"; // az veri → soluk
  return { background: `${c}${alpha}`, color: c, boxShadow: `inset 0 0 0 1px ${c}33` };
}

function DurabilityHeatmap({
  bias,
  onSymbolClick,
}: {
  bias: BiasReport;
  onSymbolClick: (sym: string) => void;
}) {
  const bySym = bias.by_symbol_horizon ?? {};
  const overall = bias.by_horizon ?? {};
  const symbols = Object.keys(bySym).sort();
  if (symbols.length === 0 && Object.keys(overall).length === 0) return null;

  const rows: { key: string; label: string; data: Record<string, { n: number; accuracy_pct: number | null }>; clickable: boolean }[] = [
    { key: "__all__", label: "TÜMÜ", data: overall, clickable: false },
    ...symbols.map((s) => ({
      key: s,
      label: s.replace(".INDX", "").replace(".FOREX", ""),
      data: bySym[s],
      clickable: true,
    })),
  ];

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full border-separate" style={{ borderSpacing: "3px" }}>
        <thead>
          <tr>
            <th className="w-16 text-left text-[9px] font-medium text-slate-600">karardan sonra →</th>
            {HORIZON_ORDER.map((h) => (
              <th key={h} className="min-w-[34px] text-center text-[9px] font-semibold text-slate-500">
                +{HORIZON_LABELS[h]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <motion.tr
              key={row.key}
              initial={{ opacity: 0, y: 6 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: ri * 0.06 }}
            >
              <td
                onClick={row.clickable ? () => onSymbolClick(row.key) : undefined}
                title={row.clickable ? "Detay panelini aç" : undefined}
                className={cx(
                  "pr-1 text-[11px] font-medium",
                  row.key === "__all__" ? "font-bold text-slate-200" : "text-slate-300",
                  row.clickable && "cursor-pointer hover:text-white"
                )}
              >
                {row.label}
              </td>
              {HORIZON_ORDER.map((h) => {
                const cell = row.data?.[h];
                const pct = cell?.accuracy_pct ?? null;
                const n = cell?.n ?? 0;
                return (
                  <td
                    key={h}
                    onClick={row.clickable ? () => onSymbolClick(row.key) : undefined}
                    title={`+${HORIZON_LABELS[h]}: ${pct !== null ? `%${pct} isabet` : "veri yok"} (${n} çağrı)`}
                    className={cx(
                      "h-[30px] rounded-lg text-center align-middle text-[10px] font-bold tabular-nums transition-transform",
                      row.clickable && "cursor-pointer hover:scale-110"
                    )}
                    style={heatCellStyle(pct, n)}
                  >
                    {pct !== null ? Math.round(pct) : "·"}
                  </td>
                );
              })}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Isı şeridi — kronolojik kararlar (eski→yeni): yeşil isabet, kırmızı ıska, gri çekimser. */
function HeatStrip({ timeline, tall = false }: { timeline: BiasTimelineCell[] | undefined; tall?: boolean }) {
  const cells = timeline ?? [];
  if (cells.length === 0)
    return <span className="text-[10px] text-slate-600">veri yok</span>;
  return (
    <div className="flex items-end gap-[3px]" aria-label="Kronolojik karar şeridi (eski→yeni)">
      {cells.map((c, i) => {
        const isLast = i === cells.length - 1;
        const color = c.ok === null ? "#475569" : c.ok ? "#34D399" : "#FB7185";
        const title = `${c.d} · ${c.label ?? ""} · ${c.bias}${c.ok === null ? " (çekimser)" : c.ok ? " ✓ isabet" : " ✗ ıska"}`;
        return (
          <motion.span
            key={`${c.d}-${i}`}
            initial={{ scaleY: 0, opacity: 0 }}
            whileInView={{ scaleY: 1, opacity: c.ok === null ? 0.45 : 1 }}
            viewport={{ once: true }}
            transition={{ delay: Math.min(i * 0.02, 0.4), duration: 0.25 }}
            title={title}
            className={cx("origin-bottom rounded-[2px]", tall ? "w-3" : "w-[7px]")}
            style={{
              height: tall ? (c.ok === null ? 12 : 22) : c.ok === null ? 8 : 14,
              background: color,
              boxShadow: c.ok !== null ? `0 0 6px ${color}66` : undefined,
              outline: isLast ? "1px solid rgba(255,255,255,0.35)" : undefined,
              outlineOffset: 1,
            }}
          />
        );
      })}
    </div>
  );
}

/** Bias karnesi sembol detayı — etiket (çalıştırma saati) + güven kovası kırılımı. */
function BiasDetailSheet({ bias, symbol, onClose }: { bias: BiasReport; symbol: string; onClose: () => void }) {
  const symRate = bias.by_symbol?.[symbol];
  const primaryStat = bias.primary_intraday?.per_symbol?.[symbol];
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
          {primaryStat ? (
            <p className="mb-4 text-center text-sm text-slate-300">
              <span className="text-2xl font-bold" style={{ color: biasColor(primaryStat.accuracy_pct) }}>
                {primaryStat.accuracy_pct !== null ? `%${primaryStat.accuracy_pct}` : "—"}
              </span>{" "}
              isabet · {primaryStat.correct}/{primaryStat.n} yönlü çağrı ({primaryStat.horizon_min}dk ufuk)
              {symRate && (
                <span className="mt-0.5 block text-[10px] text-slate-600">
                  gün-kapanışı (eski metrik): %{symRate.accuracy_pct ?? "—"} · {symRate.n} tahmin
                </span>
              )}
            </p>
          ) : symRate ? (
            <p className="mb-4 text-center text-sm text-slate-300">
              <span className="text-2xl font-bold" style={{ color: biasColor(symRate.accuracy_pct) }}>
                {symRate.accuracy_pct !== null ? `%${symRate.accuracy_pct}` : "—"}
              </span>{" "}
              isabet · {symRate.correct}/{symRate.n} tahmin
            </p>
          ) : null}
          {bias.primary_intraday?.per_symbol?.[symbol]?.timeline && (
            <>
              <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Zaman çizgisi — eski → yeni ({symbol})
              </h4>
              <div className="mb-1.5 overflow-x-auto pb-1">
                <HeatStrip timeline={bias.primary_intraday.per_symbol[symbol].timeline} tall />
              </div>
              <p className="mb-4 text-[9px] text-slate-600">
                Her sütun bir karar günü — üzerine gel: tarih, saat etiketi ve sonuç.
              </p>
            </>
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

  // Genel trend: tüm sembollerin şeritleri tarih sırasında birleştirilir —
  // gösterge rengi ve "son dönem vs önceki" çipi buradan.
  const overallTrend = useMemo(() => {
    const merged = Object.values(primary?.per_symbol ?? {})
      .flatMap((s) => s.timeline ?? [])
      .sort((a, b) => a.d.localeCompare(b.d));
    return timelineTrend(merged);
  }, [primary]);

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
              {/* Gösterge rengi SON DÖNEM isabetinden gelir — başarı zamanla
                  düşüyorsa halka yeşilden turuncu/kırmızıya kayar. */}
              <Ring
                pct={overallPct ?? 0}
                color={biasColor(overallTrend.recentPct ?? overallPct)}
                size={150}
              >
                <span className="text-4xl font-bold tabular-nums text-white">
                  {overallPct !== null ? `%${overallPct}` : "—"}
                </span>
                <span className="mt-1 text-[11px] text-slate-500">
                  {overallN} yönlü çağrı
                </span>
              </Ring>

              {/* Trend çipi: son dönem vs önceki dönem */}
              {overallTrend.delta !== null && (
                <div className="mt-2 flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px]">
                  <TrendArrow delta={overallTrend.delta} />
                  <span className="text-slate-300">
                    son dönem <span className="font-bold" style={{ color: biasColor(overallTrend.recentPct) }}>%{overallTrend.recentPct}</span>
                  </span>
                  <span className="text-slate-600">·</span>
                  <span className="text-slate-500">önceki %{overallTrend.olderPct}</span>
                </div>
              )}
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

              {/* Karar dayanıklılık ısı haritası: karardan +10dk → +6s isabet seyri */}
              <div className="mt-5 w-full">
                <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Karar dayanıklılığı — karardan sonra isabet nasıl seyrediyor?
                </h4>
                <DurabilityHeatmap bias={bias} onSymbolClick={setOpenBiasSymbol} />
              </div>
              <p className="mt-3 text-center text-[10px] text-slate-600">
                hücre = o ufuktaki yönlü isabet %'si · <span className="text-emerald-400">yeşil</span> tutuyor ·{" "}
                <span className="text-amber-400">sarı</span> zayıflıyor · <span className="text-rose-400">kırmızı</span> bozuluyor
                · soluk = az veri · satıra tıkla → detay
              </p>
              <p className="mt-2 text-center text-[11px] text-slate-500">Hedef: ≥%65 iyi · ≥%55 canlıya alma alt sınırı</p>
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
