"use client";

/**
 * Decider İşlem Defteri — "hangi gün, hangi işlemde, ne kadar TP/SL yaptı".
 *
 * Karar listesi eskiden yalnız yön + gerekçe gösteriyordu; işlemin GEOMETRİSİ
 * (giriş, hedef, stop, gerçekleşen çıkış) ve YOL İZİ (nereye kadar gitti, ne
 * kadar geri çekildi) görünmüyordu. Bu bileşen kararları güne göre gruplar,
 * her günün net R'ını başlıkta verir ve satır açıldığında işlemin tam
 * dökümünü gösterir.
 *
 * Okuma kuralı: **brüt R değil net R** karar metriğidir (spread düşülmüş).
 * MFE/MAE ikilisi "kazandı/kaybetti" ikiliğinin arkasını anlatır: MAE'si
 * yüksek bir kazanç şanslı, MFE'si yüksek bir kayıp ise kaçırılmış kârdır.
 */

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, TrendingDown, TrendingUp } from "lucide-react";

import type { DeciderDecision } from "@/lib/api/evolution";
import { Badge, cx } from "./ui";

function rColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return "#64748B";
  if (v > 0.05) return "#34D399";
  if (v < -0.05) return "#FB7185";
  return "#94A3B8";
}

function fmtR(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(digits)}R`;
}

function fmtPrice(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("tr-TR", { maximumFractionDigits: 2 });
}

function hhmm(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

function dayLabel(day: string): string {
  const d = new Date(`${day}T12:00:00Z`);
  return d.toLocaleDateString("tr-TR", {
    day: "numeric", month: "long", weekday: "short", timeZone: "UTC",
  });
}

/** Girişten TP ve SL'e uzaklığı ölçekli gösteren minik şerit. */
function GeometryBar({ d }: { d: DeciderDecision }) {
  const tp = d.tp_distance;
  const sl = d.sl_distance;
  if (!tp || !sl) return null;
  const total = tp + sl;
  const tpPct = (tp / total) * 100;
  const won = d.outcome === "WIN";
  const lost = d.outcome === "LOSS";
  return (
    <div className="mt-2">
      <div className="flex h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className={cx("transition-opacity", lost ? "opacity-100" : "opacity-40")}
          style={{ width: `${100 - tpPct}%`, background: "#FB7185" }}
          title={`SL mesafesi ${sl} puan`}
        />
        <div
          className={cx("transition-opacity", won ? "opacity-100" : "opacity-40")}
          style={{ width: `${tpPct}%`, background: "#34D399" }}
          title={`TP mesafesi ${tp} puan`}
        />
      </div>
      <div className="mt-0.5 flex justify-between text-[9.5px] tabular-nums text-slate-600">
        <span>SL {sl} puan</span>
        <span className={cx(d.rr && d.rr < 1 ? "text-amber-500/80" : "text-slate-600")}>
          RR {d.rr?.toFixed(2) ?? "—"}
        </span>
        <span>TP {tp} puan</span>
      </div>
    </div>
  );
}

/** Yol izi: lehte en uzak (MFE) ve aleyhte en dip (MAE) nokta. */
function PathTrace({ d }: { d: DeciderDecision }) {
  if (d.mfe_r === null && d.mae_r === null) return null;
  const note =
    d.outcome === "WIN" && (d.mae_r ?? 0) >= 0.7
      ? "Kazandı ama stopun dibine kadar gitti — şanslı kazanç."
      : d.outcome === "LOSS" && (d.mfe_r ?? 0) >= 0.5
        ? "Hedefin yarısını geçmişti, sonra dönüp stop oldu — kaçırılmış kâr."
        : null;
  return (
    <div className="mt-2 rounded-lg bg-white/[0.03] px-2 py-1.5">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10.5px] tabular-nums">
        <span className="flex items-center gap-1 text-emerald-300/90">
          <TrendingUp size={11} /> en iyi {fmtR(d.mfe_r, 2)}
        </span>
        <span className="flex items-center gap-1 text-rose-300/90">
          <TrendingDown size={11} /> en kötü −{Math.abs(d.mae_r ?? 0).toFixed(2)}R
        </span>
        {d.tp_progress !== null && (
          <span className="text-slate-500">hedefe %{Math.round(d.tp_progress * 100)}</span>
        )}
        {d.bars_to_outcome !== null && (
          <span className="text-slate-500">{d.bars_to_outcome} barda bitti</span>
        )}
      </div>
      {note && <p className="mt-1 leading-snug text-[10.5px] text-amber-200/70">{note}</p>}
    </div>
  );
}

function TradeRow({ d }: { d: DeciderDecision }) {
  const [open, setOpen] = useState(false);
  const isOpen = d.action === "OPEN";
  const shownR = d.r_net ?? d.r;

  return (
    <div className="rounded-xl odd:bg-white/[0.02]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left text-[11px] transition hover:bg-white/[0.03]"
      >
        <span className="w-[38px] shrink-0 tabular-nums text-slate-500">{hhmm(d.ts)}</span>
        <span
          className={cx(
            "w-[38px] shrink-0 font-semibold",
            d.direction === "BUY" ? "text-emerald-300"
              : d.direction === "SELL" ? "text-rose-300" : "text-slate-500",
          )}
        >
          {d.direction ?? "bekle"}
        </span>
        {isOpen && d.entry !== null ? (
          <span className="shrink-0 tabular-nums text-slate-500">
            {fmtPrice(d.entry)}
            {d.exit_price !== null && (
              <>
                <span className="mx-1 text-slate-700">→</span>
                <span className={d.outcome === "WIN" ? "text-emerald-300/80" : "text-rose-300/80"}>
                  {fmtPrice(d.exit_price)}
                </span>
              </>
            )}
          </span>
        ) : (
          <span className="truncate text-slate-600">{d.session}</span>
        )}
        <span className="ml-auto flex shrink-0 items-center gap-2">
          {shownR !== null && (
            <span className="font-semibold tabular-nums" style={{ color: rColor(shownR) }}>
              {fmtR(shownR)}
            </span>
          )}
          {d.outcome ? (
            <Badge tone={d.outcome === "WIN" ? "green" : "red"}>
              {d.outcome === "WIN" ? "TP" : "SL"}
            </Badge>
          ) : isOpen ? (
            <Badge tone="blue">açık</Badge>
          ) : d.cf_r !== null ? (
            <span
              className="tabular-nums text-slate-600"
              title="beklemenin karşı-olgusu: açsaydı ne olurdu"
            >
              cf {fmtR(d.cf_r, 1)}
            </span>
          ) : null}
          <ChevronDown
            size={12}
            className={cx("text-slate-600 transition-transform", open && "rotate-180")}
          />
        </span>
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
            <div className="px-2.5 pb-2.5 pt-0.5">
              {isOpen && (
                <>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10.5px] tabular-nums sm:grid-cols-4">
                    <Field label="giriş" value={fmtPrice(d.entry)} />
                    <Field label="hedef (TP)" value={fmtPrice(d.tp)} tone="green" />
                    <Field label="stop (SL)" value={fmtPrice(d.sl)} tone="red" />
                    <Field
                      label="çıkış"
                      value={fmtPrice(d.exit_price)}
                      tone={d.outcome === "WIN" ? "green" : d.outcome === "LOSS" ? "red" : undefined}
                    />
                    <Field label="brüt" value={fmtR(d.r)} />
                    <Field label="net (spread'li)" value={fmtR(d.r_net)} strong />
                    <Field label="spread" value={d.spread !== null ? `${d.spread}` : "—"} />
                    <Field label="ATR" value={d.atr !== null ? `${d.atr}` : "—"} />
                    <Field label="boyut" value={d.size_factor !== null ? `×${d.size_factor}` : "—"} />
                    <Field label="seans" value={d.session} />
                    <Field label="kapanış" value={hhmm(d.outcome_at)} />
                    <Field
                      label="LLM maliyeti"
                      value={d.cost_usd !== null ? `$${d.cost_usd.toFixed(2)}` : "—"}
                    />
                  </div>
                  <GeometryBar d={d} />
                  <PathTrace d={d} />
                </>
              )}
              {d.reason && (
                <p className="mt-2 leading-snug text-[10.5px] text-slate-400">
                  <span className="text-slate-600">gerekçe · </span>
                  {d.reason}
                </p>
              )}
              {d.management && (
                <p className="mt-1.5 leading-snug text-[10.5px] text-slate-500">
                  <span className="text-slate-600">yönetim planı · </span>
                  {d.management}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Field({
  label, value, tone, strong,
}: {
  label: string; value: string; tone?: "green" | "red"; strong?: boolean;
}) {
  return (
    <div>
      <div className="text-[9.5px] text-slate-600">{label}</div>
      <div
        className={cx(
          strong ? "font-semibold text-slate-200" : "text-slate-300",
          tone === "green" && "text-emerald-300",
          tone === "red" && "text-rose-300",
        )}
      >
        {value}
      </div>
    </div>
  );
}

/** Bir günün başlığı: kaç işlem, kaç TP/SL, günün net R'ı. */
function DayHeader({
  day, rows, expanded, onToggle,
}: {
  day: string; rows: DeciderDecision[]; expanded: boolean; onToggle: () => void;
}) {
  const opens = rows.filter((r) => r.action === "OPEN");
  const wins = opens.filter((r) => r.outcome === "WIN").length;
  const losses = opens.filter((r) => r.outcome === "LOSS").length;
  const netR = opens.reduce((a, r) => a + (r.r_net ?? r.r ?? 0), 0);
  const waits = rows.length - opens.length;

  return (
    <button
      onClick={onToggle}
      className="sticky top-0 z-10 flex w-full items-center gap-2 rounded-lg bg-[#0B0F17]/95 px-2.5 py-1.5 text-left backdrop-blur transition hover:bg-white/[0.04]"
    >
      <ChevronDown
        size={13}
        className={cx("shrink-0 text-slate-600 transition-transform", !expanded && "-rotate-90")}
      />
      <span className="text-[11.5px] font-semibold text-slate-300">{dayLabel(day)}</span>
      <span className="text-[10.5px] text-slate-600">
        {opens.length} işlem{waits > 0 && ` · ${waits} bekle`}
      </span>
      <span className="ml-auto flex items-center gap-2 text-[10.5px] tabular-nums">
        {(wins > 0 || losses > 0) && (
          <span>
            <span className="text-emerald-400">{wins} TP</span>
            <span className="mx-1 text-slate-700">/</span>
            <span className="text-rose-400">{losses} SL</span>
          </span>
        )}
        <span className="font-semibold" style={{ color: rColor(netR) }}>
          {fmtR(netR, 2)}
        </span>
      </span>
    </button>
  );
}

export default function DeciderTradeLog({ decisions }: { decisions: DeciderDecision[] }) {
  const [only, setOnly] = useState<"OPEN" | "WAIT" | "all">("OPEN");
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());

  const byDay = useMemo(() => {
    const rows = decisions.filter((d) => (only === "all" ? true : d.action === only));
    const map = new Map<string, DeciderDecision[]>();
    for (const r of rows) {
      const list = map.get(r.day);
      if (list) list.push(r);
      else map.set(r.day, [r]);
    }
    // Gün içi kronoloji: en yeni işlem üstte (liste zaten ts desc gelir).
    return Array.from(map.entries()).sort((a, b) => b[0].localeCompare(a[0]));
  }, [decisions, only]);

  const toggle = (day: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });

  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5">
        {([["OPEN", "işlemler"], ["WAIT", "bekle"], ["all", "hepsi"]] as const).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setOnly(k)}
            className={cx(
              "rounded-full px-2.5 py-0.5 text-[11px] transition",
              only === k
                ? "bg-white/10 text-slate-200 ring-1 ring-white/20"
                : "text-slate-500 hover:text-slate-300",
            )}
          >
            {label}
          </button>
        ))}
        <span className="ml-auto text-[10px] text-slate-600">
          satıra tıkla → giriş / TP / SL / yol izi
        </span>
      </div>

      {byDay.length === 0 && (
        <p className="py-6 text-center text-[12px] text-slate-500">Bu filtrede karar yok.</p>
      )}

      <div className="space-y-2">
        {byDay.map(([day, rows]) => {
          const expanded = !collapsed.has(day);
          return (
            <div key={day}>
              <DayHeader day={day} rows={rows} expanded={expanded} onToggle={() => toggle(day)} />
              {expanded && (
                <div className="mt-0.5 space-y-0.5">
                  {rows.map((r, i) => (
                    <TradeRow key={`${r.ts}-${i}`} d={r} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
