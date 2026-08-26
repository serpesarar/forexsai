"use client";

/**
 * GÖLGE MODU — sistemde gölge çalışan her şeyin tek karnesi.
 *
 * "Gölge" = karar üretiliyor, kaydediliyor, ama canlı akışa DOKUNMUYOR.
 * Üç aile tek yerde toplanır:
 *   1. Gölge kapılar   — "bloklardım" diyen ama bloklamayan filtreler
 *   2. Gölge modeller  — ters sinyaller + kapatılmış deneyler
 *   3. Gölge işlemler  — dedektörlerin sızıntısız kâğıt-işlemleri
 *
 * OKUMA KURALI (panelin her yerinde aynı): çıplak isabet oranı hiçbir şey
 * söylemez. RR 0,67 geometride %60 isabet BAŞABAŞtır. Bu yüzden her satırda
 * WR'ın yanında **beklenti (R)** ve **başabaş çıtası** durur; renk kodu
 * beklentiye göre verilir, WR'a göre değil.
 */

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  ChevronDown,
  Eye,
  FlaskConical,
  Ghost,
  Shield,
  ShieldOff,
} from "lucide-react";

import {
  type CanonMetrics,
  type ShadowGate,
  type ShadowModelFamily,
  type ShadowTradeBucket,
  useShadowOverview,
} from "@/lib/api/evolution";
import { Badge, GlassCard, Section, Skeleton, cx, timeAgo } from "./ui";

// ── Ortak yardımcılar ───────────────────────────────────────────────────────

/** Renk KAYNAĞI beklentidir — WR değil. Bilerek böyle. */
function rColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return "#64748B";
  if (v > 0.05) return "#34D399";
  if (v < -0.05) return "#FB7185";
  return "#94A3B8";
}

function fmtR(v: number | null | undefined, digits = 3): string {
  if (v === null || v === undefined) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(digits)}R`;
}

function pct(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : `%${v.toFixed(1)}`;
}

/**
 * WR + başabaş + beklenti üçlüsü — panelde çıplak WR'ın tek başına
 * görünmesini yapısal olarak imkânsız kılan bileşen.
 */
function MetricTriad({
  wr, breakeven, expectancy, n, totalR,
}: {
  wr: number | null; breakeven: number | null; expectancy: number | null;
  n: number; totalR?: number;
}) {
  const above = wr !== null && breakeven !== null && wr >= breakeven;
  return (
    <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-[11.5px] tabular-nums">
      <span>
        <span className="text-slate-600">isabet </span>
        <span className={cx("font-semibold", above ? "text-slate-200" : "text-slate-400")}>
          {pct(wr)}
        </span>
        {breakeven !== null && (
          <span className={cx("ml-1", above ? "text-emerald-500/70" : "text-amber-500/80")}>
            (başabaş {pct(breakeven)})
          </span>
        )}
      </span>
      <span>
        <span className="text-slate-600">beklenti </span>
        <span className="font-semibold" style={{ color: rColor(expectancy) }}>
          {fmtR(expectancy)}
        </span>
      </span>
      {totalR !== undefined && (
        <span>
          <span className="text-slate-600">toplam </span>
          <span className="font-semibold" style={{ color: rColor(totalR) }}>
            {totalR > 0 ? "+" : ""}{totalR.toFixed(1)}R
          </span>
        </span>
      )}
      <span className="text-slate-600">n={n}</span>
    </div>
  );
}

function WarnList({ items }: { items: string[] }) {
  if (!items?.length) return null;
  return (
    <ul className="mt-2 space-y-1">
      {items.map((w, i) => (
        <li key={i} className="flex gap-1.5 text-[10.5px] leading-snug text-amber-200/70">
          <AlertTriangle size={11} className="mt-0.5 shrink-0" />
          <span>{w}</span>
        </li>
      ))}
    </ul>
  );
}

function Collapsible({
  title, children, defaultOpen = false,
}: {
  title: React.ReactNode; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-1.5 py-1 text-left text-[11px] text-slate-500 transition hover:text-slate-300"
      >
        <ChevronDown size={12} className={cx("transition-transform", !open && "-rotate-90")} />
        {title}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="pt-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── 1) Gölge kapılar ────────────────────────────────────────────────────────

const VERDICT_TONE: Record<string, "green" | "red" | "slate" | "amber"> = {
  ac: "green",
  acma: "red",
  notr: "slate",
  veri_yok: "slate",
};

function GateCard({ gate }: { gate: ShadowGate }) {
  const m = gate.metrics;
  const v = gate.verdict;
  return (
    <GlassCard hover className="p-4">
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0">
          {gate.blocking ? (
            <Shield size={15} className="text-emerald-400" />
          ) : (
            <ShieldOff size={15} className="text-slate-500" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[13px] font-semibold text-slate-200">{gate.label}</span>
            <Badge tone={gate.blocking ? "green" : "slate"}>{gate.mode}</Badge>
            {!gate.enabled && <Badge tone="red">kapalı</Badge>}
          </div>
          <p className="mt-1 text-[10.5px] leading-snug text-slate-500">{gate.note}</p>
        </div>
      </div>

      <div className="mt-3 rounded-xl bg-white/[0.03] px-3 py-2">
        <div className="text-[10px] text-slate-600">
          {gate.blocking ? "Bu kapı bloklamış" : "Bloklayacağı"} sinyaller — {gate.would_block_total} adet
        </div>
        <div className="mt-1">
          <MetricTriad
            wr={m.win_rate}
            breakeven={m.breakeven_wr}
            expectancy={m.expectancy_r}
            n={m.n}
            totalR={m.total_r}
          />
        </div>
        {m.mixed_epochs && (
          <p className="mt-1.5 text-[10px] text-amber-200/60">
            ⚠ Farklı geometri dönemleri karışık — epoch kırılımına bak.
          </p>
        )}
        <WarnList items={m.warnings ?? []} />
      </div>

      <div className="mt-2.5 flex items-start gap-2 rounded-xl px-3 py-2 ring-1 ring-inset ring-white/[0.07]">
        <Badge tone={VERDICT_TONE[v.code] ?? "slate"}>{v.label}</Badge>
        <p className="flex-1 text-[10.5px] leading-snug text-slate-400">{v.detail}</p>
      </div>

      {v.code !== "veri_yok" && (
        <p className="mt-2 text-[10px] leading-snug text-slate-600">
          Açmak için: <code className="text-slate-400">{gate.flag}=1</code>
        </p>
      )}

      {gate.recent.length > 0 && (
        <div className="mt-2">
          <Collapsible title={`son ${gate.recent.length} verdikt`}>
            <div className="space-y-1">
              {gate.recent.map((r) => (
                <div key={r.id} className="rounded-lg px-2 py-1 text-[10.5px] odd:bg-white/[0.02]">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">{r.symbol}</span>
                    <span
                      className={cx(
                        "font-semibold",
                        r.direction === "BUY" ? "text-emerald-300" : "text-rose-300",
                      )}
                    >
                      {r.direction}
                    </span>
                    <span className="text-slate-600">{r.model}</span>
                    <span className="ml-auto text-slate-600">{timeAgo(r.at)}</span>
                  </div>
                  {r.reason && (
                    <p className="mt-0.5 leading-snug text-slate-600">{r.reason}</p>
                  )}
                </div>
              ))}
            </div>
          </Collapsible>
        </div>
      )}
    </GlassCard>
  );
}

// ── 2) Gölge modeller ───────────────────────────────────────────────────────

function ModelFamilyCard({ fam }: { fam: ShadowModelFamily }) {
  const m = fam.metrics;
  return (
    <GlassCard hover className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <FlaskConical size={15} className="text-violet-400" />
        <span className="text-[13px] font-semibold text-slate-200">{fam.label}</span>
        <span className="text-[10.5px] text-slate-600">{fam.total} sinyal</span>
      </div>
      <p className="mt-1 text-[10.5px] leading-snug text-slate-500">{fam.note}</p>

      <div className="mt-3 rounded-xl bg-white/[0.03] px-3 py-2">
        <MetricTriad
          wr={m.win_rate}
          breakeven={m.breakeven_wr}
          expectancy={m.expectancy_r}
          n={m.n}
          totalR={m.total_r}
        />
        {m.mixed_epochs && (
          <p className="mt-1.5 text-[10px] text-amber-200/60">
            ⚠ Geometri dönemleri karışık — aile toplamı yanıltıcı olabilir.
          </p>
        )}
      </div>

      {fam.models.length > 0 && (
        <div className="mt-2">
          <Collapsible title={`${fam.models.length} model kırılımı`} defaultOpen>
            <div className="space-y-1">
              {fam.models.map((mm) => (
                <div
                  key={mm.model_type}
                  className="rounded-lg px-2 py-1.5 odd:bg-white/[0.02]"
                >
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="font-medium text-slate-300">{mm.model_type}</span>
                    <span className="ml-auto text-[10px] text-slate-600">{mm.total} sinyal</span>
                  </div>
                  <div className="mt-0.5">
                    <MetricTriad
                      wr={mm.metrics.win_rate}
                      breakeven={mm.metrics.breakeven_wr}
                      expectancy={mm.metrics.expectancy_r}
                      n={mm.metrics.n}
                      totalR={mm.metrics.total_r}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Collapsible>
        </div>
      )}
    </GlassCard>
  );
}

// ── 3) Gölge işlemler ───────────────────────────────────────────────────────

function TradeSourceCard({ src }: { src: ShadowTradeBucket }) {
  return (
    <GlassCard hover className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Eye size={15} className="text-teal-400" />
        <span className="text-[13px] font-semibold text-slate-200">{src.label}</span>
        <span className="text-[10.5px] text-slate-600">
          {src.total} kâğıt-işlem · {src.open} açık
        </span>
      </div>

      <div className="mt-2.5 rounded-xl bg-white/[0.03] px-3 py-2">
        <MetricTriad
          wr={src.win_rate}
          breakeven={src.breakeven_wr}
          expectancy={src.expectancy_r}
          n={src.resolved}
          totalR={src.total_r}
        />
        <div className="mt-1 text-[10px] text-slate-600 tabular-nums">
          {src.wins} kazanç / {src.losses} kayıp
          {src.expired > 0 && ` · ${src.expired} süresi doldu`}
          {src.median_rr !== null && ` · medyan RR ${src.median_rr}`}
        </div>
        <WarnList items={src.warnings ?? []} />
      </div>

      {(src.by_direction?.length ?? 0) > 0 && (
        <div className="mt-2">
          <Collapsible title="yön kırılımı">
            <div className="space-y-1">
              {src.by_direction!.map((d) => (
                <div key={d.key} className="rounded-lg px-2 py-1 odd:bg-white/[0.02]">
                  <div className="flex items-center gap-2 text-[11px]">
                    <span
                      className={cx(
                        "font-semibold",
                        d.key === "BUY" ? "text-emerald-300" : "text-rose-300",
                      )}
                    >
                      {d.key}
                    </span>
                    <span className="ml-auto text-[10px] text-slate-600">{d.total}</span>
                  </div>
                  <MetricTriad
                    wr={d.win_rate}
                    breakeven={d.breakeven_wr}
                    expectancy={d.expectancy_r}
                    n={d.resolved}
                    totalR={d.total_r}
                  />
                </div>
              ))}
            </div>
          </Collapsible>
        </div>
      )}

      {(src.by_symbol?.length ?? 0) > 0 && (
        <div className="mt-1">
          <Collapsible title="sembol kırılımı">
            <div className="space-y-1">
              {src.by_symbol!.map((d) => (
                <div key={d.key} className="rounded-lg px-2 py-1 odd:bg-white/[0.02]">
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="font-medium text-slate-300">{d.key}</span>
                    <span className="ml-auto text-[10px] text-slate-600">{d.total}</span>
                  </div>
                  <MetricTriad
                    wr={d.win_rate}
                    breakeven={d.breakeven_wr}
                    expectancy={d.expectancy_r}
                    n={d.resolved}
                    totalR={d.total_r}
                  />
                </div>
              ))}
            </div>
          </Collapsible>
        </div>
      )}
    </GlassCard>
  );
}

// ── Ana panel ───────────────────────────────────────────────────────────────

export default function ShadowBoard({ days }: { days: number }) {
  const { data, isLoading, isError } = useShadowOverview(days);

  if (isLoading && !data) {
    return (
      <div className="grid gap-3 lg:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-44 rounded-3xl" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <GlassCard>
        <p className="text-sm text-slate-400">
          Gölge verisi alınamadı — backend çalışıyor mu?
        </p>
      </GlassCard>
    );
  }

  const gates = data.gates;
  const models = data.models;
  const trades = data.trades;
  const flags = data.flags;

  const shadowGateCount = flags?.gates.filter((g) => g.mode === "GÖLGE").length ?? 0;
  const liveGateCount = flags?.gates.filter((g) => g.mode === "BLOK").length ?? 0;

  return (
    <div className="space-y-6">
      {/* Üst şerit: gölgede ne var, ne kadar */}
      <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="gölge kapı"
          value={shadowGateCount}
          sub={`${liveGateCount} kapı gerçekten blokluyor`}
          color="#8B7CF6"
        />
        <StatTile
          label="ölçülmüş kapı"
          value={gates?.measured_gates ?? 0}
          sub={`${gates?.signals_with_shadow_verdict ?? 0} sinyalde verdikt var`}
          color="#38BDF8"
        />
        <StatTile
          label="gölge sinyal"
          value={models?.families.reduce((a, f) => a + f.total, 0) ?? 0}
          sub="ters + deney modelleri"
          color="#A78BFA"
        />
        <StatTile
          label="kâğıt-işlem"
          value={trades?.total ?? 0}
          sub={trades?.last_at ? `son: ${timeAgo(trades.last_at)}` : "—"}
          color="#2DD4BF"
        />
      </div>

      {data.errors?.length > 0 && (
        <GlassCard className="border-amber-400/20 p-4">
          {data.errors.map((e) => (
            <p key={e.block} className="text-[11.5px] text-amber-200/80">
              <span className="font-semibold">{e.block}</span> bloğu yüklenemedi: {e.error}
            </p>
          ))}
        </GlassCard>
      )}

      {models?.alerts?.map((a, i) => (
        <GlassCard key={i} className="border-amber-400/20 p-4">
          <p className="flex gap-2 text-[11.5px] leading-snug text-amber-200/80">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            {a.text}
          </p>
        </GlassCard>
      ))}

      {/* 1 — Gölge kapılar */}
      <div>
        <SubHeader
          title="Gölge Kapılar"
          desc={
            gates?.signals_with_shadow_verdict === 0
              ? `Verdikt kaydı ${gates?.since_instrumented} tarihinde başladı — sinyaller biriktikçe burası dolacak.`
              : "Her kapı için: bloklayacağı sinyaller ne yapmış? Beklenti NEGATİFSE kapı değerlidir."
          }
        />
        <div className="grid gap-3 lg:grid-cols-2">
          {gates?.gates.map((g) => (
            <GateCard key={g.id} gate={g} />
          ))}
        </div>
      </div>

      {/* 2 — Gölge modeller */}
      <div>
        <SubHeader
          title="Gölge Modeller"
          desc="prediction_logs'a yazılan ama işleme dönüşmeyen sinyal aileleri."
        />
        <div className="grid gap-3 lg:grid-cols-2">
          {models?.families.map((f) => (
            <ModelFamilyCard key={f.id} fam={f} />
          ))}
        </div>
      </div>

      {/* 3 — Gölge işlemler */}
      <div>
        <SubHeader
          title="Gölge İşlemler"
          desc="Dedektörlerin sızıntısız kâğıt-işlemleri — giriş kapanmış bardan, çözüm yalnız sonraki barlardan."
        />
        <div className="grid gap-3 lg:grid-cols-2">
          {trades?.sources.map((s) => (
            <TradeSourceCard key={s.key} src={s} />
          ))}
        </div>
      </div>

      {/* 4 — Bayrak künyesi */}
      {flags && (
        <div>
          <SubHeader title="Bayraklar" desc="Ne gölgede, ne canlıda — env durumu." />
          <GlassCard className="p-4">
            <div className="grid gap-1.5 sm:grid-cols-2">
              {flags.gates.map((g) => (
                <div
                  key={g.id}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] odd:bg-white/[0.02]"
                >
                  <span className="text-slate-300">{g.label}</span>
                  <code className="text-[9.5px] text-slate-600">{g.block_flag}</code>
                  <span className="ml-auto">
                    <Badge
                      tone={g.mode === "BLOK" ? "green" : g.mode === "GÖLGE" ? "purple" : "red"}
                    >
                      {g.mode}
                    </Badge>
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-3 border-t border-white/[0.06] pt-2.5">
              <div className="grid gap-1.5 sm:grid-cols-2">
                {flags.experiments.map((e) => (
                  <div key={e.flag} className="flex items-center gap-2 text-[11px]">
                    <span className="text-slate-400">{e.label}</span>
                    <span className="ml-auto">
                      <Badge tone={e.on ? "blue" : "slate"}>{e.on ? "açık" : "kapalı"}</Badge>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}

function StatTile({
  label, value, sub, color,
}: {
  label: string; value: number; sub: string; color: string;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] px-4 py-3">
      <div className="text-2xl font-bold tabular-nums" style={{ color }}>
        {value}
      </div>
      <div className="text-[11px] font-medium text-slate-400">{label}</div>
      <div className="mt-0.5 text-[10px] text-slate-600">{sub}</div>
    </div>
  );
}

function SubHeader({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="mb-3">
      <h3 className="text-[15px] font-semibold text-slate-200">{title}</h3>
      <p className="mt-0.5 text-[11.5px] leading-snug text-slate-500">{desc}</p>
    </div>
  );
}

/** Sayfada bölüm olarak kullanmak için sarmalayıcı. */
export function ShadowSection({ days }: { days: number }) {
  return (
    <Section
      id="golge"
      title="Gölge Modu"
      icon={<Ghost size={22} />}
      accent="#8B7CF6"
      subtitle="Karar veren ama canlıya dokunmayan her şeyin karnesi — kapılar, ters modeller, kâğıt-işlemler."
    >
      <ShadowBoard days={days} />
    </Section>
  );
}
